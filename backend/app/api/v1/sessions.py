"""Session CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_db
from app.schemas.session import (
    SessionCreate,
    SessionOut,
    SessionDetail,
    SessionListOut,
    MessageOut,
)
from app.storage import session_store

router = APIRouter()


@router.post("/sessions", response_model=SessionOut)
def create_session(payload: SessionCreate, db: DBSession = Depends(get_db)):
    s = session_store.create_session(db, title=payload.title)
    return s


@router.get("/sessions", response_model=SessionListOut)
def list_sessions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: DBSession = Depends(get_db),
):
    items, total = session_store.list_sessions(db, page=page, size=size)
    return SessionListOut(items=items, total=total)


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    s = session_store.get_session(db, session_id)
    if not s:
        raise HTTPException(status_code=404, detail="会话不存在")
    msgs = session_store.get_session_messages(db, session_id)
    return SessionDetail(session=s, messages=msgs)


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: DBSession = Depends(get_db)):
    ok = session_store.delete_session(db, session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"ok": True}
