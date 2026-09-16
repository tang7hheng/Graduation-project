"""Seed real product data from goods_info.csv into the database + vector store.

Usage:
    python seed_csv.py               # clear and import ~200 sampled products
    python seed_csv.py --all         # import ALL products from CSV (slow!)
    python seed_csv.py --keep        # keep existing, only append
"""
import argparse
import csv
import random
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from app.storage.database import Base, SessionLocal, engine, init_db
from app.storage.models import Merchant, Product
from app.rag.product_indexer import index_product, parse_price_value
from app.rag.enricher import enrich_product_text
from app.core.vector_store import reset_collection

CSV_PATH = Path(__file__).parent.parent / "goods_info.csv"
IMAGES_DIR = Path(__file__).parent.parent / "images"
SAMPLE_PER_CATEGORY = 25  # ~200 total across 9 categories

# Brand dictionary for lightweight brand extraction from the goods title.
# Titles usually start with the brand, so we take the earliest match.
BRANDS = [
    "漫步者", "Edifier", "小米", "米家", "Redmi", "红米", "Xiaomi", "华为", "HUAWEI", "荣耀", "Honor",
    "苹果", "Apple", "三星", "Samsung", "索尼", "Sony", "JBL", "Bose", "Beats", "森海塞尔",
    "铁三角", "拜亚动力", "AKG", "万魔", "1MORE", "QCY", "声阔", "soundcore", "安克", "Anker",
    "倍思", "Baseus", "绿联", "UGREEN", "品胜", "罗马仕", "紫米", "ZMI", "台电", "爱国者", "aigo", "南孚",
    "罗技", "Logitech", "雷蛇", "Razer", "雷柏", "双飞燕", "海盗船", "微软", "Microsoft", "戴尔", "Dell",
    "惠普", "HP", "联想", "Lenovo", "华硕", "ASUS", "飞利浦", "Philips", "松下", "明基", "欧普", "雷士",
    "得力", "公牛", "几光", "大疆", "DJI", "魅族", "OPPO", "vivo", "iQOO", "一加", "realme", "努比亚",
    "中兴", "诺基亚", "摩托罗拉", "小度", "天猫精灵", "膳魔师", "象印", "虎牌", "哈尔斯", "富光", "乐扣",
    "希诺", "金士顿", "闪迪", "西部数据", "希捷", "惠威", "猫王", "先科", "山水", "金正", "德生",
]


def _extract_brand(title: str) -> str:
    """Return the brand appearing earliest in the title, or '' if none is recognized."""
    if not title:
        return ""
    best, best_pos = "", len(title) + 1
    for b in BRANDS:
        pos = title.find(b)
        if pos != -1 and pos < best_pos:
            best, best_pos = b, pos
    return best


def _local_image_for_category(category: str) -> str:
    """Pick a random local image path for a category."""
    cat_dir = IMAGES_DIR / category
    if not cat_dir.is_dir():
        return ""
    files = [f for f in cat_dir.iterdir() if f.suffix.lower() in (".jpg", ".png", ".jpeg")]
    if not files:
        return ""
    picked = random.choice(files)
    return f"/images/{category}/{picked.name}"


def read_csv():
    """Read CSV and return list of dicts."""
    rows = []
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def sample_products(rows, per_category=SAMPLE_PER_CATEGORY):
    """Sample N products per category for balanced representation."""
    by_cat = defaultdict(list)
    for r in rows:
        cat = r.get("category", "其他").strip()
        by_cat[cat].append(r)

    sampled = []
    for cat, items in sorted(by_cat.items()):
        # Sort by sales descending (extract number) for better products
        def sales_num(r):
            s = r.get("sales", "")
            num = ""
            for ch in s:
                if ch.isdigit():
                    num += ch
                elif num:
                    break
            return int(num) if num else 0

        items_sorted = sorted(items, key=sales_num, reverse=True)
        take = min(per_category, len(items_sorted))
        sampled.extend(items_sorted[:take])

    return sampled


def run(keep=False, all_products=False, enrich=False):
    if enrich:
        print("[enrich] LLM 富化已开启:每个商品会调用一次大模型生成 detail_content,速度较慢且消耗 API 额度。")
    if not keep:
        print("Clearing existing data...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        reset_collection()

    rows = read_csv()
    print(f"CSV total rows: {len(rows)}")

    if all_products:
        sampled = rows
    else:
        sampled = sample_products(rows)
    print(f"Sampled products to import: {len(sampled)}")

    # Group by shop_name to create merchants
    shop_map = {}  # shop_name -> merchant_id
    for r in sampled:
        shop = r.get("shop_name", "默认商户").strip()
        if shop not in shop_map:
            shop_map[shop] = None

    print(f"Unique merchants: {len(shop_map)}")

    db = SessionLocal()
    try:
        # Create merchants
        for shop_name in shop_map:
            m = Merchant(name=shop_name[:128], description=f"淘宝商户 · {shop_name}")
            db.add(m)
            db.flush()
            shop_map[shop_name] = m.id

        # Create products
        imported = 0
        for r in sampled:
            shop = r.get("shop_name", "默认商户").strip()
            merchant_id = shop_map.get(shop)
            title = r.get("goods_title", "").strip()
            price = r.get("price", "0").strip()
            category = r.get("category", "").strip()
            sales = r.get("sales", "").strip()
            image_url = r.get("image_url", "").strip()
            goods_id = r.get("goods_id", "").strip()

            # Use local image if CSV has no image_url
            if not image_url:
                image_url = _local_image_for_category(category)

            # Extract structured facets used for filtered retrieval
            brand = _extract_brand(title)

            # Build description and specs
            description = f"{category}类商品。月销量: {sales}"
            specs = f"品类:{category};品牌:{brand};商品ID:{goods_id};店铺:{shop}"

            # Optional LLM enrichment fills detail_content (improves vector quality)
            detail_content = ""
            if enrich:
                try:
                    detail_content = enrich_product_text(
                        name=title,
                        category=category,
                        price=f"¥{price}",
                        sales=sales,
                        shop=shop,
                        description=description,
                    )
                except Exception as e:
                    print(f"  [WARN] enrich failed for {title[:30]}...: {e}")

            p = Product(
                merchant_id=merchant_id,
                name=title[:256],
                description=description,
                detail_content=detail_content,
                price=f"¥{price}",
                price_value=parse_price_value(price),
                specs=specs,
                brand=brand,
                category=category,
                stock=random.randint(20, 500),
                image_url=image_url,
            )
            db.add(p)
            db.flush()

            # Index into vector DB
            try:
                index_product(p, merchant_name=shop)
                p.status = "indexed"
            except Exception as e:
                print(f"  [WARN] vector index failed for {title[:30]}...: {e}")
                p.status = "failed"

            db.commit()
            imported += 1
            if imported % 50 == 0:
                print(f"  Imported {imported}/{len(sampled)}...")

        print(f"\nDone! Imported {imported} products from {len(shop_map)} merchants.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep", action="store_true", help="Keep existing data")
    parser.add_argument("--all", action="store_true", help="Import ALL CSV rows (slow)")
    parser.add_argument("--enrich", action="store_true", help="Use LLM to enrich detail_content (slow, costs API calls)")
    args = parser.parse_args()
    run(keep=args.keep, all_products=args.all, enrich=args.enrich)
