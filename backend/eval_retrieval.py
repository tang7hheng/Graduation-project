# -*- coding: utf-8 -*-
"""检索质量评估脚本(不依赖具体商品 ID,重导数据后依然有效)。

它度量 search_products_by_keyword 在两种模式下的表现:
  - baseline  : 只传 keyword(相当于结构化过滤上线前的行为)
  - structured: 传 keyword + 品类/品牌/价格等结构化参数(新能力)

评分维度(客观、可自动计算,无需人工标注):
  1. 约束纯度 purity: 返回的商品中,满足全部硬约束(品类严格相等、价格落在区间)的比例
  2. 召回非空率     : 是否真的返回了商品(0 条视为失败)
  3. 价格合规率     : 指定了预算时,返回商品价格落在区间内的比例

用法(务必先导入数据):
    python seed_csv.py            # 或 python seed_csv.py --enrich
    python eval_retrieval.py              # 完整链路(含 reranker,首次会下载模型)
    python eval_retrieval.py --no-rerank  # 跳过 reranker,评估过滤+向量排序(快,无大下载)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.rag.tools import search_products_by_keyword
from app.rag.product_indexer import parse_price_value

TOP_K = 8

# 每个用例: query 文本 + 正确 agent 应传的结构化参数 + 用于评分的硬约束
CASES = [
    {
        "name": "预算内指定品牌品类",
        "keyword": "蓝牙耳机",
        "facets": {"category": "蓝牙耳机", "brand": "小米", "max_price": 300},
        "expect": {"category": "蓝牙耳机", "max_price": 300},
    },
    {
        "name": "充电宝价格区间",
        "keyword": "充电宝 大容量 便携",
        "facets": {"category": "充电宝", "min_price": 50, "max_price": 150},
        "expect": {"category": "充电宝", "min_price": 50, "max_price": 150},
    },
    {
        "name": "护眼台灯",
        "keyword": "台灯 护眼 学生学习",
        "facets": {"category": "台灯"},
        "expect": {"category": "台灯"},
    },
    {
        "name": "智能手表预算内",
        "keyword": "智能手表 运动 心率监测",
        "facets": {"category": "智能手表", "max_price": 500},
        "expect": {"category": "智能手表", "max_price": 500},
    },
    {
        "name": "鼠标品类",
        "keyword": "鼠标 办公",
        "facets": {"category": "鼠标"},
        "expect": {"category": "鼠标"},
    },
    {
        "name": "数据线品类",
        "keyword": "数据线 快充 Type-C",
        "facets": {"category": "数据线"},
        "expect": {"category": "数据线"},
    },
]


def _violations(product: dict, expect: dict) -> list[str]:
    """返回单个商品违反硬约束的说明列表(空=完全合规)。"""
    v = []
    price = parse_price_value(product.get("price", ""))
    # 品类: 严格相等(空品类视为不合规 —— 说明数据未重建或字段缺失)
    if "category" in expect:
        if product.get("category") != expect["category"]:
            v.append(f"品类={product.get('category') or '空'}≠{expect['category']}")
    # 品牌: 尽力而为字段,仅当商品有品牌且不符时才算违规
    if "brand" in expect:
        pb = product.get("brand") or ""
        if pb and pb != expect["brand"]:
            v.append(f"品牌={pb}≠{expect['brand']}")
    # 价格区间: 仅对能解析出数值(price>0)的商品判定
    if price > 0:
        if "max_price" in expect and price > expect["max_price"]:
            v.append(f"价格{price}>{expect['max_price']}")
        if "min_price" in expect and price < expect["min_price"]:
            v.append(f"价格{price}<{expect['min_price']}")
    return v


def _run(keyword: str, facets: dict | None) -> list[dict]:
    args = {"keyword": keyword, "top_k": TOP_K}
    if facets:
        args.update(facets)
    try:
        raw = search_products_by_keyword.invoke(args)
        return json.loads(raw).get("products", [])
    except Exception as e:  # noqa: BLE001
        print(f"    [ERROR] 检索失败: {e}")
        return []


def _grade(products: list[dict], expect: dict) -> dict:
    if not products:
        return {"returned": 0, "pure": 0, "purity": 0.0}
    pure = sum(1 for p in products if not _violations(p, expect))
    return {"returned": len(products), "pure": pure, "purity": pure / len(products)}


def main():
    if "--no-rerank" in sys.argv:
        from app.config import settings
        settings.enable_reranker = False
        print("[mode] reranker 已禁用(仅评估 结构化过滤 + 向量排序)\n")

    print("=" * 78)
    print("检索质量评估:baseline(仅关键词) vs structured(结构化过滤)")
    print("=" * 78)

    base_p, struct_p = [], []
    for case in CASES:
        expect = case["expect"]
        b = _grade(_run(case["keyword"], None), expect)
        s_products = _run(case["keyword"], case["facets"])
        s = _grade(s_products, expect)
        base_p.append(b["purity"])
        struct_p.append(s["purity"])

        print(f"\n[{case['name']}] keyword={case['keyword']!r} facets={case['facets']}")
        print(f"  baseline  : 返回 {b['returned']:2d} 条, 合规 {b['pure']:2d}, 纯度 {b['purity']:6.1%}")
        print(f"  structured: 返回 {s['returned']:2d} 条, 合规 {s['pure']:2d}, 纯度 {s['purity']:6.1%}")
        for p in s_products[:3]:
            vs = _violations(p, expect)
            tag = "OK" if not vs else "X " + "; ".join(vs)
            name = (p.get("name", "") or "")[:32]
            print(f"      - {name:34} {p.get('price',''):9} 品牌:{p.get('brand') or '-':6} [{tag}]")

    n = len(CASES)
    print("\n" + "=" * 78)
    print(f"平均约束纯度   baseline = {sum(base_p)/n:6.1%}    structured = {sum(struct_p)/n:6.1%}")
    print(f"纯度提升       +{(sum(struct_p)-sum(base_p))/n*100:.1f} 个百分点")
    print("=" * 78)
    print("说明: structured 纯度接近 100% 表示结构化过滤生效; baseline 纯度低属正常")
    print("      (仅靠关键词无法保证品类/价格约束)。若 structured 返回 0 条或品类为'空',")
    print("      说明向量库尚未按新字段重建,请先运行 seed_csv.py 重新导入。")


if __name__ == "__main__":
    main()
