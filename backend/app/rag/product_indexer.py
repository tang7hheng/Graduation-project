"""Index a Product as a retrieval unit in the vector store.

Each product becomes one Document whose page_content is a structured text block
combining name / brand / category / description / detail_content / specs / price,
and whose metadata carries product_id / merchant_id / name / price / price_value /
brand / category / in_stock / type:"product" so the chat chain can:
  - aggregate sources by product
  - render product info (name, price) in citations
  - structurally filter by category / brand / price range / stock
  - delete/update a single product's vector without touching others
"""
import logging
import re

from langchain_core.documents import Document
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.core.vector_store import add_documents, delete_by_product_id
from app.storage.models import Merchant, Product

log = logging.getLogger(__name__)

_PRICE_NUM_RE = re.compile(r"\d+(?:\.\d+)?")


def parse_price_value(price_str: str) -> float:
    """Extract the first numeric value from a price string.

    '¥88.33' -> 88.33; '199-299' -> 199.0; '面议' -> 0.0 (no number found).
    Used for price-range filtering and sorting.
    """
    if not price_str:
        return 0.0
    m = _PRICE_NUM_RE.search(price_str)
    return float(m.group()) if m else 0.0


def product_to_document(p: Product, merchant_name: str = "") -> Document:
    """Build the retrievable text for a product."""
    brand = getattr(p, "brand", "") or ""
    category = getattr(p, "category", "") or ""
    parts = [f"商品名称:{p.name}"]
    if brand:
        parts.append(f"品牌:{brand}")
    if category:
        parts.append(f"品类:{category}")
    if p.description:
        parts.append(f"商品描述:{p.description}")
    if p.detail_content:
        parts.append(f"功能介绍与使用说明:{p.detail_content}")
    if p.specs:
        parts.append(f"规格参数:{p.specs}")
    if p.price:
        parts.append(f"价格:{p.price}")
    if p.stock is not None:
        parts.append(f"库存:{p.stock}")
    if merchant_name:
        parts.append(f"商家:{merchant_name}")
    content = "\n".join(parts)

    price_value = float(getattr(p, "price_value", 0.0) or 0.0)
    if price_value <= 0.0:
        price_value = parse_price_value(p.price or "")

    return Document(
        page_content=content,
        metadata={
            "product_id": p.id,
            "merchant_id": p.merchant_id or "",
            "name": p.name,
            "price": p.price or "",
            "price_value": price_value,
            "brand": brand,
            "category": category,
            "in_stock": bool((p.stock or 0) > 0),
            "type": "product",
            "source": f"商品:{p.name}",
        },
    )


def index_product(p: Product, merchant_name: str = "") -> int:
    """Add (or replace) a product's vector. Returns number of vectors added."""
    # Remove existing vector for this product first (idempotent re-index)
    delete_by_product_id(p.id)
    doc = product_to_document(p, merchant_name=merchant_name)
    return add_documents([doc])


def remove_product(product_id: str) -> int:
    """Delete a product's vector entry."""
    return delete_by_product_id(product_id)


def index_all_products(db: DBSession) -> int:
    """Re-index every product in the DB into the vector store.

    Used by /kb/rebuild: reset_collection() wipes the whole Chroma collection
    (including product vectors), so products must be rebuilt afterwards or
    product search would silently break. Per-product errors are tolerated so a
    single bad row cannot abort the whole re-index. Returns count of indexed products.
    """
    products = db.execute(select(Product)).scalars().all()
    count = 0
    for p in products:
        try:
            merchant_name = ""
            if p.merchant_id:
                m = db.get(Merchant, p.merchant_id)
                if m:
                    merchant_name = m.name
            index_product(p, merchant_name=merchant_name)
            count += 1
        except Exception as e:
            log.warning("Re-index product %s failed: %s", p.id, e)
    return count
