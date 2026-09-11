"""Index a Product as a retrieval unit in the vector store.

Each product becomes one Document whose page_content is a structured text block
combining name / description / specs / price, and whose metadata carries
product_id / merchant_id / name / type:"product" so the chat chain can:
  - aggregate sources by product
  - render product info (name, price) in citations
  - delete/update a single product's vector without touching others
"""
from langchain_core.documents import Document

from app.core.vector_store import add_documents, delete_by_product_id
from app.storage.models import Product


def product_to_document(p: Product, merchant_name: str = "") -> Document:
    """Build the retrievable text for a product."""
    parts = [f"商品名称:{p.name}"]
    if p.description:
        parts.append(f"商品描述:{p.description}")
    if p.specs:
        parts.append(f"规格参数:{p.specs}")
    if p.price:
        parts.append(f"价格:{p.price}")
    if p.stock is not None:
        parts.append(f"库存:{p.stock}")
    if merchant_name:
        parts.append(f"商家:{merchant_name}")
    content = "\n".join(parts)

    return Document(
        page_content=content,
        metadata={
            "product_id": p.id,
            "merchant_id": p.merchant_id,
            "name": p.name,
            "price": p.price or "",
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
