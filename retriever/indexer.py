"""Document indexing into Qdrant."""

import uuid

from fastapi import UploadFile
from pypdf import PdfReader

from backend.rag.chunking import chunk_text
from backend.services.embeddings import EmbeddingService
from retriever.client import QdrantStore


class DocumentIndexer:
    def __init__(self, store: QdrantStore) -> None:
        self._store = store
        self._embeddings = EmbeddingService()

    async def ingest_upload(self, file: UploadFile) -> None:
        content = await file.read()
        text = self._extract_text(file.filename or "document", content)
        chunks = chunk_text(text=text, source=file.filename or "document")
        vectors = self._embeddings.embed([c.text for c in chunks])

        self._store.ensure_collection(vector_size=len(vectors[0]))
        self._store.upsert(
            ids=[str(uuid.uuid4()) for _ in chunks],
            vectors=vectors,
            payloads=[
                {"text": c.text, "source": c.source, "chunk_index": c.chunk_index}
                for c in chunks
            ],
        )

    def _extract_text(self, filename: str, content: bytes) -> str:
        if filename.lower().endswith(".pdf"):
            reader = PdfReader(__import__("io").BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        return content.decode("utf-8", errors="ignore")
