"""Document ingestion endpoints."""

from fastapi import APIRouter, Depends, UploadFile

from backend.api.deps import get_retriever
from retriever.indexer import DocumentIndexer
from retriever.search import Retriever

router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile,
    retriever: Retriever = Depends(get_retriever),
) -> dict[str, str]:
    indexer = DocumentIndexer(store=retriever.store)
    await indexer.ingest_upload(file)
    return {"status": "indexed", "filename": file.filename or "unknown"}
