"""Order endpoints: create / list / get / cancel.

A consumer places an order by clicking a product card in the chat. The order
is bound to the chat session (if any) and snapshots product info at order time.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_db
from app.rag.product_indexer import parse_price_value
from app.schemas.order import OrderCreate, OrderOut, OrderListOut, CartCheckout
from app.storage.models import Order, OrderItem, Product

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/orders", response_model=OrderOut)
def create_order(payload: OrderCreate, db: DBSession = Depends(get_db)):
    p = db.get(Product, payload.product_id)
    if not p:
        raise HTTPException(status_code=404, detail="商品不存在")

    qty = max(1, int(payload.quantity or 1))
    unit_price = parse_price_value(p.price or "")
    total = unit_price * qty

    order = Order(
        session_id=payload.session_id or None,
        merchant_id=p.merchant_id,
        status="pending",
        total_amount=f"{total:.2f}",
        remark=payload.remark or "",
    )
    db.add(order)
    db.flush()  # to get order.id

    item = OrderItem(
        order_id=order.id,
        product_id=p.id,
        product_name=p.name,
        price=p.price or "",
        quantity=qty,
        image_url=p.image_url or "",
    )
    db.add(item)
    db.commit()
    db.refresh(order)
    return order


@router.post("/orders/checkout", response_model=list[OrderOut])
def checkout_cart(payload: CartCheckout, db: DBSession = Depends(get_db)):
    """Batch checkout: create one order per merchant (since orders are scoped to a merchant).

    Splits the cart items by merchant, creates one Order per merchant with all
    that merchant's items as OrderItem rows. Returns the list of created orders.
    """
    if not payload.items:
        raise HTTPException(status_code=400, detail="购物车为空")

    # Group items by merchant_id
    by_merchant: dict[str, list[tuple[Product, int]]] = {}
    for ci in payload.items:
        p = db.get(Product, ci.product_id)
        if not p:
            raise HTTPException(status_code=404, detail=f"商品 {ci.product_id} 不存在")
        qty = max(1, int(ci.quantity or 1))
        by_merchant.setdefault(p.merchant_id, []).append((p, qty))

    created_orders: list[Order] = []
    for merchant_id, items in by_merchant.items():
        total = sum(parse_price_value(p.price or "") * qty for p, qty in items)
        order = Order(
            session_id=payload.session_id or None,
            merchant_id=merchant_id,
            status="pending",
            total_amount=f"{total:.2f}",
            remark=payload.remark or "",
        )
        db.add(order)
        db.flush()

        for p, qty in items:
            db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=p.id,
                    product_name=p.name,
                    price=p.price or "",
                    quantity=qty,
                    image_url=p.image_url or "",
                )
            )
        created_orders.append(order)

    db.commit()
    for o in created_orders:
        db.refresh(o)
    return created_orders


@router.get("/orders", response_model=OrderListOut)
def list_orders(
    session_id: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: DBSession = Depends(get_db),
):
    q = select(Order)
    if session_id:
        q = q.where(Order.session_id == session_id)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = (
        db.execute(
            q.order_by(Order.created_at.desc()).offset((page - 1) * size).limit(size)
        )
        .scalars()
        .all()
    )
    return OrderListOut(items=list(rows), total=total)


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: str, db: DBSession = Depends(get_db)):
    o = db.get(Order, order_id)
    if not o:
        raise HTTPException(status_code=404, detail="订单不存在")
    return o


@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
def cancel_order(order_id: str, db: DBSession = Depends(get_db)):
    o = db.get(Order, order_id)
    if not o:
        raise HTTPException(status_code=404, detail="订单不存在")
    if o.status == "paid":
        raise HTTPException(status_code=400, detail="订单已支付,无法取消")
    if o.status == "cancelled":
        raise HTTPException(status_code=400, detail="订单已取消")
    o.status = "cancelled"
    db.commit()
    db.refresh(o)
    return o


@router.post("/orders/{order_id}/pay", response_model=OrderOut)
def pay_order(order_id: str, db: DBSession = Depends(get_db)):
    """Mark an order as paid (demo: no real payment gateway)."""
    o = db.get(Order, order_id)
    if not o:
        raise HTTPException(status_code=404, detail="订单不存在")
    if o.status == "paid":
        raise HTTPException(status_code=400, detail="订单已支付,请勿重复支付")
    if o.status == "cancelled":
        raise HTTPException(status_code=400, detail="订单已取消,无法支付")
    o.status = "paid"
    db.commit()
    db.refresh(o)
    return o
