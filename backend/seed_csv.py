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
from app.rag.product_indexer import index_product
from app.core.vector_store import reset_collection

CSV_PATH = Path(__file__).parent.parent / "goods_info.csv"
IMAGES_DIR = Path(__file__).parent.parent / "images"
SAMPLE_PER_CATEGORY = 25  # ~200 total across 9 categories


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


def run(keep=False, all_products=False):
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

            # Build description and specs
            description = f"{category}类商品。月销量: {sales}"
            specs = f"品类:{category};商品ID:{goods_id};店铺:{shop}"

            p = Product(
                merchant_id=merchant_id,
                name=title[:256],
                description=description,
                price=f"¥{price}",
                specs=specs,
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
    args = parser.parse_args()
    run(keep=args.keep, all_products=args.all)
