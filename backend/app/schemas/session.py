"""Pydantic schemas for session endpoints."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    title: Optional[str] = None


class SessionOut(BaseModel):
    id: str
    title: str
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    sources_json: list = Field(default_factory=list)
    product_cards_json: list = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class SessionDetail(BaseModel):
    session: SessionOut
    messages: list[MessageOut]


class SessionListOut(BaseModel):
    items: list[SessionOut]
    total: int
