"""Index authority chunks into Qdrant (local fastembed)."""

from __future__ import annotations

from pathlib import Path

from authority.ingest import build_chunks, write_chunks_jsonl
from authority.manifest import resolve_bot_root
from backend.core.config import Settings
from backend.services.embeddings import EmbeddingService
from retriever.client import QdrantStore


def index_authority(
    bot_root: str | Path | None = None,
    *,
    recreate: bool = True,
    batch_size: int = 32,
) -> dict:
    bot = resolve_bot_root(bot_root)
    settings = Settings()
    chunks = build_chunks(bot)

    out_path = Path("data/authority/chunks.jsonl")
    write_chunks_jsonl(chunks, out_path)

    store = QdrantStore(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection=settings.qdrant_collection,
    )
    embeddings = EmbeddingService(settings)

    if not chunks:
        return {"indexed": 0, "bot_root": str(bot)}

    probe = embeddings.embed_query("dimension probe")
    if recreate:
        store.recreate_collection(vector_size=len(probe))
    else:
        store.ensure_collection(vector_size=len(probe))

    total = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        vectors = embeddings.embed([c.text for c in batch])
        store.upsert(
            ids=[c.chunk_id for c in batch],
            vectors=vectors,
            payloads=[c.to_payload() for c in batch],
        )
        total += len(batch)
        print(f"  indexed batch {i // batch_size + 1}: {len(batch)}")

    by_ns: dict[str, int] = {}
    for c in chunks:
        by_ns[c.namespace] = by_ns.get(c.namespace, 0) + 1

    return {
        "indexed": total,
        "bot_root": str(bot),
        "collection": settings.qdrant_collection,
        "by_namespace": by_ns,
        "chunks_path": str(out_path),
    }
