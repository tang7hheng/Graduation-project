"""POST /chat — SSE streaming chat endpoint."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_db
from app.rag.chain import stream_chat
from app.schemas.chat import ChatRequest
from app.storage import session_store

router = APIRouter()


@router.post("/chat")
def chat(req: ChatRequest, db: DBSession = Depends(get_db)):
    # Validate session exists (auto-create if not, for resilience)
    s = session_store.get_session(db, req.session_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"会话不存在: {req.session_id}")

    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    # Build SSE generator. Use a fresh DB session bound to this request lifecycle.
    def event_stream():
        # The injected db is request-scoped; safe to use within this generator.
        try:
            for frame in stream_chat(db, req.session_id, req.message.strip()):
                yield frame
        except Exception as e:
            import json
            yield f"data: {json.dumps({'type': 'error', 'message': f'内部错误: {e}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable proxy buffering
            "Connection": "keep-alive",
        },
    )
