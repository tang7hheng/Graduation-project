"""DeepSeek LLM client (OpenAI-compatible)."""
import os
from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.config import settings


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    # Set HF_ENDPOINT early so sentence-transformers uses mirror when later loaded
    os.environ.setdefault("HF_ENDPOINT", settings.hf_endpoint)

    if not settings.deepseek_api_key or settings.deepseek_api_key.startswith("sk-xxx"):
        # Allow import-time load; will raise on actual call if not configured
        pass

    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        streaming=True,
    )
