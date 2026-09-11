"""Pydantic schemas for knowledge base endpoints."""
from datetime import datetime
from pydantic import BaseModel


class DocOut(BaseModel):
    id: str
    filename: str
    doc_type: str
    chunk_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class UploadResp(BaseModel):
    doc_id: str
    filename: str
    chunks: int


class RebuildResp(BaseModel):
    reindexed: int
