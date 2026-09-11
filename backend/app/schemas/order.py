"""Pydantic schemas for order endpoints."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class OrderItemOut(BaseModel):
    id: int
    product_id: str
    product_name: str
    price: str
    quantity: int
    image_url: str

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    session_id: Optional[str] = None
    product_id: str
    quantity: int = 1
    remark: Optional[str] = ""


class CheckoutItem(BaseModel):
    product_id: str
    quantity: int = 1


class CartCheckout(BaseModel):
    """Batch checkout: create one order containing multiple product line items."""

    session_id: Optional[str] = None
    items: list[CheckoutItem]
    remark: Optional[str] = ""


class OrderOut(BaseModel):
    id: str
    session_id: Optional[str] = None
    merchant_id: str
    status: str
    total_amount: str
    remark: str
    created_at: datetime
    items: list[OrderItemOut] = []

    class Config:
        from_attributes = True


class OrderListOut(BaseModel):
    items: list[OrderOut]
    total: int
