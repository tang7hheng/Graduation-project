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
from app.rag.tools import SHOPPING_TOOLS, search_products_by_keyword, get_product_detail
from app.storage import session_store

log = logging.getLogger(__name__)


def _sse(event: dict) -> str:
    """Serialize a dict to an SSE `data:` frame (terminated by \\n\\n)."""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def _execute_tool(tool_name: str, args: dict) -> str:
    """Dispatch a tool call to the right tool function and return its string result."""
    if tool_name == "search_products_by_keyword":
        return search_products_by_keyword.invoke(args)
    if tool_name == "get_product_detail":
        return get_product_detail.invoke(args)
    return json.dumps({"error": f"未知工具: {tool_name}"}, ensure_ascii=False)


def _extract_product_cards_from_tool_history(messages: list[BaseMessage]) -> list[dict]:
    """Parse tool-call history to collect product cards to show in the UI.

    Scans ToolMessages for search_products_by_keyword / get_product_detail results,
    extracts product info, and de-dupes by product_id.
    """
    cards: list[dict] = []
    seen_pids: set[str] = set()

    for msg in messages:
        if not isinstance(msg, ToolMessage):
            continue
        try:
            payload = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
        except Exception:
            continue

        # search result: {"products": [{product_id, name, price, snippet, ...}]}
        if isinstance(payload, dict) and "products" in payload:
            for p in payload["products"]:
                pid = p.get("product_id") or ""
                if not pid or pid in seen_pids:
                    continue
                seen_pids.add(pid)
                cards.append(
                    {
                        "id": pid,
                        "name": p.get("name", "未知商品"),
                        "price": p.get("price", ""),
                        "description": "",
                        "specs": "",
                        "image_url": "",
                        # enrich below if a get_product_detail call exists
                    }
                )

        # detail result: {product_id, name, description, price, specs, ...}
        if isinstance(payload, dict) and "product_id" in payload and "products" not in payload:
            pid = payload.get("product_id") or ""
            # Enrich existing card if present, else add
            for c in cards:
                if c["id"] == pid:
                    c["description"] = payload.get("description", c["description"])
                    c["specs"] = payload.get("specs", c["specs"])
                    c["price"] = payload.get("price", c["price"]) or c["price"]
                    break
            else:
                if pid and pid not in seen_pids:
                    seen_pids.add(pid)
                    cards.append(
                        {
                            "id": pid,
                            "name": payload.get("name", "未知商品"),
                            "price": payload.get("price", ""),
                            "description": payload.get("description", ""),
                            "specs": payload.get("specs", ""),
                            "image_url": "",
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

    # 2. Build message sequence: system + memory + question
    #    No pre-retrieved context — LLM uses tools to query instead.
    messages: list[BaseMessage] = [
        SystemMessage(content=SYSTEM_PROMPT),
    ]
    messages.extend(load_context_messages(db, session_id))
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
                if now - last_ping > 15:
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
    product_cards_payload = _extract_product_cards_from_tool_history(messages)
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
