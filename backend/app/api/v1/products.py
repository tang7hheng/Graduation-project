"""Product endpoints: create / list / update / delete.

A product is both persisted in SQLite and indexed as one retrieval unit in the
vector store, so the chat chain can recall product information when answering
consumer questions.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_db
from app.rag.product_indexer import index_product, remove_product
from app.schemas.merchant import ProductCreate, ProductOut, ProductUpdate
from app.storage.models import Merchant, Product

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/merchants/{merchant_id}/products", response_model=ProductOut)
def create_product(
    merchant_id: str,
    payload: ProductCreate,
    db: DBSession = Depends(get_db),
):
    m = db.get(Merchant, merchant_id)
    if not m:
        raise HTTPException(status_code=404, detail="商户不存在")

    p = Product(
        merchant_id=merchant_id,
        name=payload.name,
        description=payload.description or "",
        detail_content=payload.detail_content or "",
        price=payload.price or "",
        specs=payload.specs or "",
        stock=payload.stock or 0,
        image_url=payload.image_url or "",
        status="indexed",
    )
    db.add(p)

    # Commit to DB first, then index into vector store
    db.commit()
    db.refresh(p)

    try:
        index_product(p, merchant_name=m.name)
    except Exception as e:
        log.exception("Product index failed: %s", e)
        p.status = "failed"
        db.commit()
        db.refresh(p)
    return p


@router.get("/products", response_model=list[ProductOut])
def list_all_products(db: DBSession = Depends(get_db)):
    rows = db.execute(select(Product).order_by(Product.created_at.desc())).scalars().all()
    return list(rows)


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: str, db: DBSession = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="商品不存在")
    return p


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: str,
    payload: ProductUpdate,
    db: DBSession = Depends(get_db),
):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="商品不存在")

    changed = False
    for field in ("name", "description", "detail_content", "price", "specs", "stock", "image_url"):
        val = getattr(payload, field, None)
        if val is not None and val != getattr(p, field):
            setattr(p, field, val)
            changed = True

    if changed:
        db.commit()
        db.refresh(p)
        m = db.get(Merchant, p.merchant_id)
        try:
            index_product(p, merchant_name=m.name if m else "")
            p.status = "indexed"
            db.commit()
            db.refresh(p)
        except Exception as e:
            log.exception("Product re-index failed: %s", e)
            p.status = "failed"
            db.commit()
            db.refresh(p)
    else:
        db.commit()
        db.refresh(p)
    return p


@router.delete("/products/{product_id}")
def delete_product(product_id: str, db: DBSession = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="商品不存在")

    # Delete from DB first, then remove from vector store (best-effort)
    db.delete(p)
    db.commit()

    try:
        remove_product(product_id)
    except Exception as e:
        log.warning("Remove product vector failed (non-fatal): %s", e)
    return {"ok": True}
