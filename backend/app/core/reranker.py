"""Cross-encoder reranker for product/knowledge search results.

Why: pure vector recall (bi-encoder) is fast but coarse — it encodes query and
document independently, so precise needs (品牌/型号/规格/预算) often rank poorly.
A cross-encoder reads (query, document) together and produces a much more
accurate relevance score, so re-scoring the top-N vector candidates and
re-sorting them significantly improves recommendation precision.

Robustness: the model is lazily loaded and cached. If it cannot be loaded
(no network / missing weights) or prediction fails, rerank_scores() returns
None and the caller degrades gracefully to the original vector ordering.
"""
import logging
import os
from functools import lru_cache
from typing import Optional

from app.config import settings

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_cross_encoder():
    """Lazily load the cross-encoder once per process. Returns None if disabled/unavailable."""
    if not settings.enable_reranker:
        return None
    try:
        # Use mirror endpoint to accelerate first-time download (same as embedding)
        os.environ.setdefault("HF_ENDPOINT", settings.hf_endpoint)
        from sentence_transformers import CrossEncoder

        model = CrossEncoder(settings.reranker_model, max_length=512)
        log.info("Reranker loaded: %s", settings.reranker_model)
        return model
    except Exception as e:  # noqa: BLE001 - any load failure must not break search
        log.warning("Reranker load failed; degrading to vector ordering: %s", e)
        return None


def rerank_scores(query: str, documents: list[str]) -> Optional[list[float]]:
    """Score each document against the query.

    Returns a list of relevance scores (same order as `documents`), or None if
    the reranker is unavailable — in which case the caller keeps vector ordering.
    """
    if not documents or not query:
        return None
    model = _get_cross_encoder()
    if model is None:
        return None
    try:
        pairs = [[query, d] for d in documents]
        scores = model.predict(pairs)
        return [float(s) for s in scores]
    except Exception as e:  # noqa: BLE001 - prediction failure must not break search
        log.warning("Rerank prediction failed; degrading to vector ordering: %s", e)
        return None


def preload() -> None:
    """Eagerly load the cross-encoder (called at app startup to avoid first-request
    download latency). No-ops safely when the reranker is disabled."""
    _get_cross_encoder()
