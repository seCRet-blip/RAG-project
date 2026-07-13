"""Load processed chunks from JSONL into Qdrant (free local vector DB)."""

import json
import uuid
from pathlib import Path

from backend.core.config import Settings
from backend.services.embeddings import EmbeddingService
from retriever.client import QdrantStore


def ingest_chunks_file(
    chunks_path: Path,
    store: QdrantStore,
    embeddings: EmbeddingService,
    batch_size: int = 32,
) -> int:
    chunks: list[dict] = []
    with chunks_path.open(encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))

    if not chunks:
        return 0

    total = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["text"] for c in batch]
        vectors = embeddings.embed(texts)
        store.ensure_collection(vector_size=len(vectors[0]))
        store.upsert(
            ids=[c.get("chunk_id", str(uuid.uuid4())) for c in batch],
            vectors=vectors,
            payloads=[
                {
                    "text": c["text"],
                    "source": c["source"],
                    "url": c["url"],
                    "title": c["title"],
                    "section": c["section"],
                    "chunk_index": c["chunk_index"],
                }
                for c in batch
            ],
        )
        total += len(batch)
        print(f"  batch {i // batch_size + 1}: {len(batch)} chunks")

    return total


def ingest_processed_chunks(source: str | None = None) -> int:
    settings = Settings()
    store = QdrantStore(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection=settings.qdrant_collection,
    )
    embeddings = EmbeddingService(settings)

    chunks_root = Path("data/processed/chunks")
    if source:
        files = [chunks_root / source / "chunks.jsonl"]
    else:
        files = list(chunks_root.glob("*/chunks.jsonl"))

    total = 0
    for path in files:
        if path.exists():
            count = ingest_chunks_file(path, store, embeddings)
            print(f"Indexed {count} chunks from {path}")
            total += count

    return total
