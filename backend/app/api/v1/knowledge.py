"""Knowledge base endpoints: upload, list, delete, rebuild."""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_db
from app.config import settings
from app.core import vector_store
from app.rag.chunker import chunk_documents
from app.rag.document_loader import SUPPORTED_EXT, detect_doc_type, load_file
from app.schemas.knowledge import DocOut, UploadResp, RebuildResp
from app.storage.models import Document

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/kb/upload", response_model=UploadResp)
async def upload_document(
    file: UploadFile = File(...),
    db: DBSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名为空")
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in SUPPORTED_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 {ext},支持:{' '.join(sorted(SUPPORTED_EXT))}",
        )

    doc_id = uuid.uuid4().hex
    doc_type = detect_doc_type(file.filename)
    save_path = settings.upload_dir_abs / f"{doc_id}_{file.filename}"

    # Save uploaded file
    content = await file.read()
    save_path.write_bytes(content)

    # Parse + chunk + index
    try:
        raw_docs = load_file(save_path, doc_id=doc_id)
        chunks = chunk_documents(raw_docs)
        if not chunks:
            raise HTTPException(status_code=400, detail="文件内容为空或无法解析")
        vector_store.add_documents(chunks)
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Indexing failed: %s", e)
        # Save record as failed for traceability
        doc = Document(
            id=doc_id,
            filename=file.filename,
            file_path=str(save_path),
            doc_type=doc_type,
            chunk_count=0,
            status="failed",
        )
        db.add(doc)
        db.commit()
        raise HTTPException(status_code=500, detail=f"索引失败: {e}")

    doc = Document(
        id=doc_id,
        filename=file.filename,
        file_path=str(save_path),
        doc_type=doc_type,
        chunk_count=len(chunks),
        status="indexed",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return UploadResp(doc_id=doc.id, filename=doc.filename, chunks=doc.chunk_count)


@router.get("/kb/documents", response_model=list[DocOut])
def list_documents(db: DBSession = Depends(get_db)):
    from sqlalchemy import select
    rows = db.execute(select(Document).order_by(Document.created_at.desc())).scalars().all()
    return list(rows)


@router.delete("/kb/documents/{doc_id}")
def delete_document(doc_id: str, db: DBSession = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    # Remove from vector store
    removed = vector_store.delete_by_doc_id(doc_id)
    # Remove file from disk
    try:
        from pathlib import Path
        p = Path(doc.file_path)
        if p.exists():
            p.unlink()
    except Exception as e:
        log.warning("Failed to remove file %s: %s", doc.file_path, e)

    db.delete(doc)
    db.commit()
    return {"ok": True, "removed_chunks": removed}


@router.post("/kb/rebuild", response_model=RebuildResp)
def rebuild_index(db: DBSession = Depends(get_db)):
    """Drop and re-index ALL vectors: knowledge documents AND products.

    reset_collection() wipes the entire Chroma collection, which also contains
    the product vectors. If we only re-indexed documents, product search would
    break permanently. So after the reset we rebuild both documents and products.
    """
    from sqlalchemy import select
    from app.rag.product_indexer import index_all_products

    docs = db.execute(select(Document).where(Document.status == "indexed")).scalars().all()

    # Reset collection (wipes documents AND product vectors)
    vector_store.reset_collection()

    reindexed = 0
    for doc in docs:
        try:
            raw_docs = load_file(doc.file_path, doc_id=doc.id)
            chunks = chunk_documents(raw_docs)
            if chunks:
                vector_store.add_documents(chunks)
                doc.chunk_count = len(chunks)
                doc.status = "indexed"
                reindexed += 1
            else:
                doc.status = "failed"
        except Exception as e:
            log.warning("Rebuild failed for %s: %s", doc.filename, e)
            doc.status = "failed"

    # Re-index all products so导购检索在 reset 之后依然可用
    products_reindexed = index_all_products(db)

    db.commit()
    return RebuildResp(reindexed=reindexed, products_reindexed=products_reindexed)
