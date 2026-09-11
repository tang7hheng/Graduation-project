"""Conversation memory: load context from SQLite and persist new messages.

We do NOT use LangChain's Memory classes; SQLite is the single source of truth.
Each request rebuilds context from `session.summary` + recent N messages.
When message count exceeds threshold, oldest chunks are summarized by LLM.
"""
from typing import Optional

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)
from sqlalchemy.orm import Session as DBSession

from app.config import settings
from app.storage import session_store
from app.storage.models import Session as SessionModel


def _role_to_message(role: str, content: str) -> BaseMessage:
    if role == "user":
        return HumanMessage(content=content)
    if role == "assistant":
        return AIMessage(content=content)
    return SystemMessage(content=content)


def load_context_messages(db: DBSession, session_id: str) -> list[BaseMessage]:
    """Build the conversation context as a list of LangChain messages.

    Order: [summary_system_msg?] + recent N [Human, AI, ...]
    """
    s: Optional[SessionModel] = session_store.get_session(db, session_id)
    if not s:
        return []

    msgs: list[BaseMessage] = []
    if s.summary:
        msgs.append(
            SystemMessage(content=f"以下是之前对话的摘要,作为上下文参考:\n{s.summary}")
        )

    recent = session_store.get_recent_messages(db, session_id, limit=settings.memory_buffer_size)
    for m in recent:
        msgs.append(_role_to_message(m.role, m.content))
    return msgs


def maybe_summarize(db: DBSession, session_id: str):
    """If message count exceeds threshold, summarize the oldest chunks and update session.summary.

    Called after each assistant reply.
    """
    count = session_store.count_messages(db, session_id)
    if count < settings.memory_summary_trigger:
        return

    # Take the oldest N-2 messages to summarize; keep the latest 2 intact
    summarize_count = count - 2
    if summarize_count < 2:
        return

    from app.storage.models import Message
    from sqlalchemy import select

    old_msgs = (
        db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
            .limit(summarize_count)
        )
        .scalars()
        .all()
    )
    if not old_msgs:
        return

    history_text = "\n".join(
        f"{'用户' if m.role == 'user' else '客服'}:{m.content}" for m in old_msgs
    )

    # Include existing summary so we re-summarize it together (prevents unbounded growth)
    s = session_store.get_session(db, session_id)
    if not s:
        return
    existing_summary = (s.summary or "").strip()
    if existing_summary:
        history_text = f"之前的对话摘要:\n{existing_summary}\n\n最近对话:\n{history_text}"

    try:
        from app.core.llm import get_llm
        from app.core.prompts import summarize_prompt

        llm = get_llm()
        prompt = summarize_prompt(history_text)
        result = llm.invoke(prompt)
        new_summary = (result.content if hasattr(result, "content") else str(result)).strip()
    except Exception as e:
        # Non-fatal: skip summarization on error
        import logging

        logging.getLogger(__name__).warning("Summarization failed: %s", e)
        return

    # Persist: replace summary (not append), then delete old msgs
    s.summary = new_summary

    for m in old_msgs:
        db.delete(m)
    db.commit()
