"""Session / Message CRUD operations."""
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session as DBSession

from app.storage.models import Session, Message
from app.config import settings


def create_session(db: DBSession, title: Optional[str] = None) -> Session:
    s = Session(title=title or "新会话", summary="")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def list_sessions(db: DBSession, page: int = 1, size: int = 20):
    total = db.scalar(select(func.count(Session.id)))
    rows = (
        db.execute(
            select(Session).order_by(Session.updated_at.desc()).offset((page - 1) * size).limit(size)
        )
        .scalars()
        .all()
    )
    return rows, total or 0


def get_session(db: DBSession, session_id: str) -> Optional[Session]:
    return db.get(Session, session_id)


def get_session_messages(db: DBSession, session_id: str, limit: int = 50):
    return (
        db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        .scalars()
        .all()
    )


def delete_session(db: DBSession, session_id: str) -> bool:
    s = db.get(Session, session_id)
    if not s:
        return False
    db.delete(s)
    db.commit()
    return True


def add_message(
    db: DBSession,
    session_id: str,
    role: str,
    content: str,
    sources: Optional[list[dict]] = None,
    product_cards: Optional[list[dict]] = None,
) -> Message:
    m = Message(
        session_id=session_id,
        role=role,
        content=content,
        sources_json=sources or [],
        product_cards_json=product_cards or [],
    )
    db.add(m)
    # Auto-update session title using first user message
    s = db.get(Session, session_id)
    if s and role == "user" and (not s.title or s.title == "新会话"):
        s.title = content[:20] + ("..." if len(content) > 20 else "")
    # Touch updated_at so the session sorts to the top of the list
    if s:
        from app.storage.models import _now
        s.updated_at = _now()
    db.commit()
    db.refresh(m)
    return m


def count_messages(db: DBSession, session_id: str) -> int:
    return db.scalar(
        select(func.count(Message.id)).where(Message.session_id == session_id)
    ) or 0


def get_recent_messages(db: DBSession, session_id: str, limit: int = None) -> list[Message]:
    if limit is None:
        limit = settings.memory_buffer_size
    return list(
        db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )[::-1]  # reverse to chronological


def update_session_summary(db: DBSession, session_id: str, summary: str):
    s = db.get(Session, session_id)
    if s:
        s.summary = summary
        db.commit()
