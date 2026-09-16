"""RAG chain: streaming generator that ties together retrieval, memory, tools, and LLM.

Architecture (per user requirements):
- The LLM does NOT touch the database. It can only call the provided tools.
- The tools (search_products_by_keyword / get_product_detail) are strictly query-only
  and use their own short-lived DB sessions.
- The guide does NOT place orders. It can only recommend products. The frontend
  renders clickable product cards so the user places the order themselves.
- This module orchestrates: load memory -> LLM (with tools) streams tokens ->
  if tool calls happen, execute them, feed results back, continue streaming ->
  build product_cards_payload from the tool results -> persist message.
"""
import json
import logging
import re
import time
from typing import Generator

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from sqlalchemy.orm import Session as DBSession

from app.core.llm import get_llm
from app.core.prompts import SYSTEM_PROMPT
from app.rag.memory import load_context_messages, maybe_summarize
from app.rag.tools import (
    SHOPPING_TOOLS,
    search_products_by_keyword,
    get_product_detail,
    search_knowledge_base,
)
from app.storage import session_store

log = logging.getLogger(__name__)

# Frontend "thinking" hints per tool name
_TOOL_THINKING_HINT = {
    "search_products_by_keyword": "正在查询商品信息...",
    "get_product_detail": "正在查询商品详情...",
    "search_knowledge_base": "正在查询知识库...",
}

# Strip whitespace + common CJK/ASCII punctuation before substring matching,
# so formatting differences (e.g. "小米手环 10" vs "小米手环10") don't cause
# a recommended product's card to be dropped.
_MATCH_STRIP_RE = re.compile(r"[\s,\.。、!！?？;；:：~～\-—_/\\()（）\[\]【】\"'’‘]+")


def _normalize_for_match(s: str) -> str:
    return _MATCH_STRIP_RE.sub("", s or "")


def _extract_exclusions(context_msgs: list[BaseMessage], current_msg: str) -> str:
    """Scan conversation history for user exclusion patterns like '不要华为' and
    inject them as an explicit system reminder so the LLM doesn't forget.

    Only extracts from HumanMessage (user) content. Returns empty string if none found.
    """
    # Pattern: 不要/排除/不含 + brand/keyword
    pattern = re.compile(r'(?:不要|不想|排除|不含|别给我|不喜欢|不要推荐)([a-zA-Z\u4e00-\u9fff]{1,8})')

    exclusions: list[str] = []
    for msg in context_msgs:
        if not isinstance(msg, HumanMessage):
            continue
        matches = pattern.findall(msg.content or "")
        for m in matches:
            m = m.strip()
            if m and m not in exclusions:
                exclusions.append(m)

    # Also check current message
    matches = pattern.findall(current_msg or "")
    for m in matches:
        m = m.strip()
        if m and m not in exclusions:
            exclusions.append(m)

    # Filter out generic words that aren't brand/category names
    stop_words = {"的", "了", "太", "贵", "便宜", "其他", "这个", "那个", "这些", "那些"}
    exclusions = [e for e in exclusions if e not in stop_words]

    if not exclusions:
        return ""

    return (
        f"【用户排除条件提醒】根据之前的对话,用户明确表示不要以下品牌/商品:"
        f"{'、'.join(exclusions)}。"
        f"在本次推荐中,必须排除包含以上关键词的商品,绝对不能推荐。"
    )


def _sse(event: dict) -> str:
    """Serialize a dict to an SSE `data:` frame (terminated by \\n\\n)."""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def _execute_tool(tool_name: str, args: dict) -> str:
    """Dispatch a tool call to the right tool function and return its string result."""
    if tool_name == "search_products_by_keyword":
        return search_products_by_keyword.invoke(args)
    if tool_name == "get_product_detail":
        return get_product_detail.invoke(args)
    if tool_name == "search_knowledge_base":
        return search_knowledge_base.invoke(args)
    return json.dumps({"error": f"未知工具: {tool_name}"}, ensure_ascii=False)


def _name_in_answer(name: str, answer: str, window: int = 6) -> bool:
    """Check if a product name is referenced in the LLM's answer text.

    Uses a sliding window approach: if any `window`-char substring of the
    product name appears in the answer, it's considered a match.
    This handles cases where the DB name is very long but the LLM only
    mentioned a short version (e.g., DB: "小米手环10 NFC陶瓷版血氧心率睡眠监测...",
    answer: "小米手环10 NFC陶瓷版 — ¥309").
    """
    if not name or not answer:
        return False
    # Normalize away spacing/punctuation differences before matching
    name = _normalize_for_match(name)
    answer = _normalize_for_match(answer)
    if not name or not answer:
        return False
    if len(name) <= window:
        return name in answer
    for i in range(len(name) - window + 1):
        sub = name[i : i + window]
        if sub in answer:
            return True
    return False


def _extract_product_cards_from_tool_history(
    db: DBSession, messages: list[BaseMessage], answer_text: str = ""
) -> list[dict]:
    """Parse tool-call history to collect product cards to show in the UI.

    Only shows products that the LLM actually referenced in its answer text.
    This prevents showing products that were in search results but filtered out
    by the LLM (e.g., user said "不要华为" → LLM excludes Huawei in text,
    but search results still contain Huawei products).
    """
    from app.storage.models import Product, Merchant

    # Step 1: Collect all product IDs from tool messages
    all_pids: set[str] = set()
    for msg in messages:
        if not isinstance(msg, ToolMessage):
            continue
        try:
            payload = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
        except Exception:
            continue
        if isinstance(payload, dict) and "products" in payload:
            for p in payload["products"]:
                pid = p.get("product_id") or ""
                if pid:
                    all_pids.add(pid)
        if isinstance(payload, dict) and "product_id" in payload:
            pid = payload.get("product_id") or ""
            if pid:
                all_pids.add(pid)

    if not all_pids:
        return []

    # Step 2: If we have answer text, only include products mentioned in it
    answer_lower = (answer_text or "").lower()
    cards: list[dict] = []
    for pid in all_pids:
        p = db.get(Product, pid)
        if not p:
            continue

        # Check if product name appears in the LLM's answer using sliding window
        if answer_text:
            name_lower = (p.name or "").lower()
            if not _name_in_answer(name_lower, answer_lower):
                continue

        merchant_name = ""
        if p.merchant_id:
            m = db.get(Merchant, p.merchant_id)
            if m:
                merchant_name = m.name
        cards.append(
            {
                "id": p.id,
                "merchant_id": p.merchant_id or "",
                "merchant_name": merchant_name,
                "name": p.name,
                "price": p.price or "",
                "description": p.description or "",
                "specs": p.specs or "",
                "image_url": p.image_url or "",
                "stock_status": "充足" if (p.stock or 0) > 0 else "缺货",
            }
        )

    return cards


def stream_chat(
    db: DBSession,
    session_id: str,
    user_message: str,
) -> Generator[str, None, None]:
    """Yield SSE strings. Persists user + assistant messages and triggers summarization."""
    # 1. Persist user message
    session_store.add_message(db, session_id, role="user", content=user_message)

    # 1b. Immediate feedback so the frontend can show a "thinking" indicator
    yield _sse({"type": "thinking", "message": "正在思考..."})

    # 2. Build message sequence: system + memory + question
    #    No pre-retrieved context — LLM uses tools to query instead.
    messages: list[BaseMessage] = [
        SystemMessage(content=SYSTEM_PROMPT),
    ]
    context_msgs = load_context_messages(db, session_id)
    messages.extend(context_msgs)

    # 2b. Extract user exclusion constraints from conversation history and inject as reminder
    exclusion_reminder = _extract_exclusions(context_msgs, user_message)
    if exclusion_reminder:
        messages.append(SystemMessage(content=exclusion_reminder))

    messages.append(HumanMessage(content=user_message))

    # 3. Get LLM and bind tools
    try:
        llm = get_llm()
        llm_with_tools = llm.bind_tools(SHOPPING_TOOLS)
    except Exception as e:
        log.exception("LLM init failed: %s", e)
        yield _sse({"type": "error", "message": f"LLM 初始化失败: {e}"})
        return

    # 4. Agent loop: stream tokens; if tool_calls appear, execute tools and continue.
    full_answer = ""
    last_ping = time.time()
    MAX_TOOL_ROUNDS = 3  # safety limit to avoid infinite loops

    try:
        for _round in range(MAX_TOOL_ROUNDS + 1):
            # Stream the LLM response for this round
            ai_chunk_content = ""
            collected_tool_calls: list[dict] = []

            for chunk in llm_with_tools.stream(messages):
                # Text content
                token = getattr(chunk, "content", "") or ""
                if token:
                    ai_chunk_content += token
                    full_answer += token
                    yield _sse({"type": "token", "content": token})

                # Tool calls (may arrive across chunks)
                tcs = getattr(chunk, "tool_call_chunks", None)
                if tcs:
                    for tc in tcs:
                        if tc.get("name") or tc.get("args"):
                            idx = tc.get("index", 0) or 0
                            while len(collected_tool_calls) <= idx:
                                collected_tool_calls.append({"name": "", "args": ""})
                            if tc.get("name"):
                                collected_tool_calls[idx]["name"] = tc["name"]
                            if tc.get("args"):
                                collected_tool_calls[idx]["args"] += tc["args"]

                # Keep-alive ping
                now = time.time()
                if now - last_ping > 5:
                    yield _sse({"type": "ping"})
                    last_ping = now

            # Build AIMessage with the content + tool_calls for the message history
            # Parse accumulated tool call args from streaming chunks
            parsed_tool_calls: list[dict] = []
            for tc in collected_tool_calls:
                if not tc.get("name"):
                    continue
                try:
                    args = json.loads(tc["args"]) if tc["args"] else {}
                except json.JSONDecodeError:
                    args = {}
                parsed_tool_calls.append({"name": tc["name"], "args": args})

            ai_msg = AIMessage(content=ai_chunk_content)
            if parsed_tool_calls:
                # LangChain expects tool_calls with id; generate ids
                ai_msg.tool_calls = [
                    {
                        "name": tc["name"],
                        "args": tc["args"],
                        "id": f"call_{_round}_{i}",
                        "type": "tool_call",
                    }
                    for i, tc in enumerate(parsed_tool_calls)
                ]
            messages.append(ai_msg)

            # If no tool calls this round, the agent is done
            if not parsed_tool_calls:
                break

            # Execute each tool call and append ToolMessage
            for i, tc in enumerate(parsed_tool_calls):
                tool_name = tc["name"]
                tool_args = tc["args"]
                # Tell the frontend what we're doing (reduces perceived lag)
                thinking_msg = _TOOL_THINKING_HINT.get(tool_name, "正在查询...")
                yield _sse({"type": "thinking", "message": thinking_msg})
                yield _sse({"type": "tool_call", "name": tool_name, "args": tool_args})
                try:
                    result = _execute_tool(tool_name, tool_args)
                except Exception as e:
                    log.exception("Tool %s failed: %s", tool_name, e)
                    result = json.dumps({"error": f"工具执行失败: {e}"}, ensure_ascii=False)
                messages.append(
                    ToolMessage(content=result, tool_call_id=f"call_{_round}_{i}")
                )

            # If this was the last allowed round, force one more LLM call without tools
            # so the LLM can produce a final user-facing answer from the tool results.
            if _round == MAX_TOOL_ROUNDS - 1:
                # Switch to LLM without tools for the final summary round
                for chunk in llm.stream(messages):
                    token = getattr(chunk, "content", "") or ""
                    if token:
                        full_answer += token
                        yield _sse({"type": "token", "content": token})
                break

        if not full_answer:
            # Edge case: tools were called but no final answer streamed
            full_answer = "（已检索商品信息,但未能生成回复,请重试。）"
            yield _sse({"type": "token", "content": full_answer})

    except Exception as e:
        log.exception("Streaming LLM failed: %s", e)
        if not full_answer:
            yield _sse({"type": "error", "message": f"模型调用失败: {e}"})
            return
        # partial answer - continue to persist

    # 5. Build product cards from tool-call history (LLM did NOT touch DB directly)
    sources_payload: list[dict] = []
    product_cards_payload = _extract_product_cards_from_tool_history(db, messages, full_answer)
    if product_cards_payload:
        for c in product_cards_payload:
            sources_payload.append(
                {
                    "kind": "product",
                    "product_id": c["id"],
                    "merchant_id": None,
                    "title": c["name"],
                    "price": c.get("price", ""),
                    "page": None,
                    "score": 0.0,
                    "snippet": c.get("description") or "",
                }
            )

    # 6. Persist assistant message
    msg = session_store.add_message(
        db,
        session_id,
        role="assistant",
        content=full_answer,
        sources=sources_payload,
        product_cards=product_cards_payload,
    )

    # 7. Send sources + product_cards + done events
    yield _sse({"type": "sources", "sources": sources_payload})
    if product_cards_payload:
        yield _sse({"type": "product_cards", "product_cards": product_cards_payload})
    yield _sse({"type": "done", "message_id": msg.id})

    # 8. Summarize if necessary
    try:
        maybe_summarize(db, session_id)
    except Exception as e:
        log.warning("Summarization failed (non-fatal): %s", e)
