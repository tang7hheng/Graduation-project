"""Local BGE embedding (HuggingFace sentence-transformers)."""
import os
from functools import lru_cache

from langchain_community.embeddings import HuggingFaceEmbeddings

from app.config import settings


@lru_cache(maxsize=1)
def get_embedding() -> HuggingFaceEmbeddings:
    # Use mirror endpoint to accelerate first-time download
    os.environ.setdefault("HF_ENDPOINT", settings.hf_endpoint)

    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        encode_kwargs={"normalize_embeddings": True},
    )
