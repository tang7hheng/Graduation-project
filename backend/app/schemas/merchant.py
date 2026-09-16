"""Pydantic schemas for merchant & product endpoints."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# === Merchant ===
class MerchantCreate(BaseModel):
    name: str
    description: Optional[str] = None


class MerchantOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# === Product ===
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    detail_content: Optional[str] = ""
    price: Optional[str] = ""
    specs: Optional[str] = ""
    stock: Optional[int] = 0
    image_url: Optional[str] = ""


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    detail_content: Optional[str] = None
    price: Optional[str] = None
    specs: Optional[str] = None
    stock: Optional[int] = None
    image_url: Optional[str] = None


class ProductOut(BaseModel):
    id: str
    merchant_id: Optional[str] = None  # 商户被删除(SET NULL)后可能为 None
    name: str
    description: str
    detail_content: str = ""
    price: str
    specs: str
    stock: int
    image_url: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
