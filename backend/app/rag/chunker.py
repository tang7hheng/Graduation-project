"""Text chunker: RecursiveCharacterTextSplitter with Chinese-aware separators."""
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


# Chinese + ASCII punctuation included for better boundary detection
# (original had "!"/"?" duplicated; use full-width ！？ alongside ASCII !?)
_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "!", "?", " ", ""]


def get_splitter(chunk_size: int = 500, chunk_overlap: int = 50) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=_SEPARATORS,
        keep_separator=True,
    )


def chunk_documents(docs: list[Document]) -> list[Document]:
    """Split documents into chunks. FAQ docs (is_faq=True) are not split."""
    splitter = get_splitter()
    out: list[Document] = []
    for doc in docs:
        if doc.metadata and doc.metadata.get("is_faq"):
            # Each FAQ QA is already atomic; keep as-is
            out.append(doc)
            continue
        out.extend(splitter.split_documents([doc]))
    return out
