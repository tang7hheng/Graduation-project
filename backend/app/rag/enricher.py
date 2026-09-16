"""Offline product-text enrichment via LLM.

Problem: the seed data (goods_info.csv) only provides a title plus a templated
description ("蓝牙耳机类商品。月销量: 5人付款") and an empty detail_content, so
each product vector carries very little discriminative signal — retrieval then
degenerates into title keyword matching.

This module asks the LLM to generate a richer Chinese text block (核心卖点 /
适用场景人群 / 关键规格功能词 / 搜索关键词) for a product. The result is stored
in Product.detail_content and embedded, improving recall quality at the source.

Used by seed_csv.py --enrich. Degrades to a lightweight template when the LLM is
unavailable, so detail_content is never left empty.
"""
import logging

from app.core.llm import get_llm

log = logging.getLogger(__name__)

_ENRICH_PROMPT = """你是电商商品资料整理专家。请根据下面的商品信息,生成一段用于语义检索的中文富文本。
需包含:核心卖点、适用场景或人群、关键规格/功能词、以及用户可能使用的搜索关键词。
要求:
- 只依据给定信息做合理扩写,不要编造具体参数数值(如续航小时数、屏幕尺寸、功率),信息里没有的就不写;
- 语言精炼,120-200字,可用逗号或分号分隔的短语;
- 直接输出富文本内容,不要复述商品标题,不要加"卖点:"之类的多余前后缀。

商品信息:
名称:{name}
品类:{category}
价格:{price}
销量:{sales}
店铺:{shop}
已有描述:{description}
"""


def enrich_product_text(
    name: str,
    category: str = "",
    price: str = "",
    sales: str = "",
    shop: str = "",
    description: str = "",
) -> str:
    """Return an LLM-generated enriched text for a product; template fallback on failure."""
    prompt = _ENRICH_PROMPT.format(
        name=name,
        category=category or "",
        price=price or "",
        sales=sales or "",
        shop=shop or "",
        description=description or "",
    )
    try:
        llm = get_llm()
        resp = llm.invoke(prompt)
        text = (getattr(resp, "content", "") or "").strip()
        if text:
            return text
    except Exception as e:  # noqa: BLE001 - enrichment is best-effort, must not abort seeding
        log.warning("Enrich failed for %s: %s", (name or "")[:30], e)

    # Fallback template so detail_content is never empty
    parts = [f"{category}类商品" if category else "商品", f"关键词:{name}"]
    if shop:
        parts.append(f"店铺:{shop}")
    return ";".join(parts)
