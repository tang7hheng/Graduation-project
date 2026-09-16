"""ORM models: Session, Message, Document."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from app.storage.database import Base


def _new_uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=_new_uuid)
    title = Column(String(256), nullable=False, default="新会话")
    summary = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    sources_json = Column(JSON, default=list)  # list[{title, snippet, score, page?}]
    product_cards_json = Column(JSON, default=list)  # list[{id,name,price,image_url,description,specs}]
    created_at = Column(DateTime(timezone=True), default=_now, index=True)

    session = relationship("Session", back_populates="messages")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=_new_uuid)
    filename = Column(String(256), nullable=False)
    file_path = Column(String(512), nullable=False)
    doc_type = Column(String(16), nullable=False)  # pdf|docx|xlsx|json|md|txt
    chunk_count = Column(Integer, default=0)
    status = Column(String(16), default="indexed")  # indexed | failed
    created_at = Column(DateTime(timezone=True), default=_now)


class Merchant(Base):
    """A merchant who publishes products to the customer-service knowledge base."""

    __tablename__ = "merchants"

    id = Column(String, primary_key=True, default=_new_uuid)
    name = Column(String(128), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=_now)

    products = relationship(
        "Product",
        back_populates="merchant",
        cascade="all, delete-orphan",
    )


class Product(Base):
    """A merchant's product. Each product is indexed as a retrieval unit in the vector store."""

    __tablename__ = "products"

    id = Column(String, primary_key=True, default=_new_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(256), nullable=False)
    description = Column(Text, default="")
    detail_content = Column(Text, default="")  # 详细功能介绍与使用说明,构成知识库检索内容
    price = Column(String(64), default="")  # keep as string to support "99.00元"/"面议" etc.
    price_value = Column(Float, default=0.0)  # 从 price 解析出的数值,用于价格区间过滤与排序
    specs = Column(Text, default="")  # free-form text or JSON string
    brand = Column(String(128), default="", index=True)  # 品牌,用于结构化过滤
    category = Column(String(64), default="", index=True)  # 品类,用于结构化过滤
    stock = Column(Integer, default=0)
    image_url = Column(String(512), default="")
    status = Column(String(16), default="indexed")  # indexed | failed
    created_at = Column(DateTime(timezone=True), default=_now)

    merchant = relationship("Merchant", back_populates="products")


class Order(Base):
    """A consumer order. Bound to a chat session so we can attribute it to a conversation."""

    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=_new_uuid)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    merchant_id = Column(String, ForeignKey("merchants.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(16), default="pending")  # pending | paid | cancelled
    total_amount = Column(String(64), default="0")  # keep as string to match Product.price format
    remark = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=_now, index=True)

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderItem.id",
    )


class OrderItem(Base):
    """A line item in an order. Snapshot of product info at order time."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String, nullable=False)
    product_name = Column(String(256), nullable=False)
    price = Column(String(64), default="")
    quantity = Column(Integer, default=1)
    image_url = Column(String(512), default="")

    order = relationship("Order", back_populates="items")
