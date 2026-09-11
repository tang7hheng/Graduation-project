"""Merchant endpoints: create / list / get."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_db
from app.schemas.merchant import MerchantCreate, MerchantOut, ProductOut
from app.storage.models import Merchant, Product

router = APIRouter()


@router.post("/merchants", response_model=MerchantOut)
def create_merchant(payload: MerchantCreate, db: DBSession = Depends(get_db)):
    m = Merchant(name=payload.name, description=payload.description or "")
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.get("/merchants", response_model=list[MerchantOut])
def list_merchants(db: DBSession = Depends(get_db)):
    rows = db.execute(select(Merchant).order_by(Merchant.created_at.desc())).scalars().all()
    return list(rows)


@router.get("/merchants/{merchant_id}", response_model=MerchantOut)
def get_merchant(merchant_id: str, db: DBSession = Depends(get_db)):
    m = db.get(Merchant, merchant_id)
    if not m:
        raise HTTPException(status_code=404, detail="商户不存在")
    return m


@router.get("/merchants/{merchant_id}/products", response_model=list[ProductOut])
def list_merchant_products(merchant_id: str, db: DBSession = Depends(get_db)):
    rows = (
        db.execute(
            select(Product)
            .where(Product.merchant_id == merchant_id)
            .order_by(Product.created_at.desc())
        )
        .scalars()
        .all()
    )
    return list(rows)
