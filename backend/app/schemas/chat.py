"""Pydantic schemas for chat endpoints."""
from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatSource(BaseModel):
    title: str
    snippet: str = ""
    score: float = 0.0
    page: Optional[int] = None
