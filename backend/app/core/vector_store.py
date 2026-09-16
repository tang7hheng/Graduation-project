"""Chroma persistent vector store wrapper."""
import logging
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import settings
from app.core.embedding import get_embedding

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_vector_store() -> Chroma:
    return Chroma(
        collection_name=settings.chroma_collection,
        embedding_function=get_embedding(),
        persist_directory=str(settings.chroma_dir_abs),
    )


def add_documents(docs: list[Document]) -> int:
    if not docs:
        return 0
    vs = get_vector_store()
    vs.add_documents(docs)
    return len(docs)


def similarity_search_with_score(query: str, k: int = None) -> list[tuple[Document, float]]:
    k = k or settings.retrieval_top_k
    vs = get_vector_store()
    # Chroma returns (Document, distance); lower distance = more similar (cosine distance)
    return vs.similarity_search_with_score(query, k=k)


def delete_by_doc_id(doc_id: str) -> int:
    """Delete all chunks belonging to a document by metadata filter."""
    return _delete_by_metadata({"doc_id": doc_id})


def delete_by_product_id(product_id: str) -> int:
    """Delete the vector entry for a product (products are 1 vector per product)."""
    return _delete_by_metadata({"product_id": product_id})


def _delete_by_metadata(meta: dict) -> int:
    vs = get_vector_store()
    collection = vs._collection
    try:
        result = collection.get(where=meta)
        ids = result.get("ids", []) if result else []
        if ids:
            collection.delete(ids=ids)
        return len(ids)
    except Exception as e:
        log.warning("delete by metadata %s failed: %s", meta, e)
        return 0


def reset_collection():
    """Drop and recreate the collection (used by /kb/rebuild)."""
    vs = get_vector_store()
    client = vs._client
    try:
        client.delete_collection(name=settings.chroma_collection)
    except Exception:
        pass
    # Drop the cached Chroma instance so a fresh one (with a new collection) is built
    get_vector_store.cache_clear()
    # Force creation of the new collection
    _ = get_vector_store()._collection
