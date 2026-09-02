"""CLI: clear local authority artifacts and recreate empty Qdrant collection."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from backend.core.config import Settings
from backend.services.embeddings import EmbeddingService
from retriever.client import QdrantStore

ROOT = Path(__file__).resolve().parents[1]


def wipe_local_data() -> list[str]:
    removed: list[str] = []
    targets = [
        ROOT / "data" / "raw",
        ROOT / "data" / "processed",
        ROOT / "data" / "sync_checkpoint.json",
        ROOT / "data" / "authority" / "chunks.jsonl",
        ROOT / "data" / "authority" / "summary.json",
    ]
    for path in targets:
        if path.is_file():
            path.unlink()
            removed.append(str(path))
        elif path.is_dir():
            shutil.rmtree(path)
            removed.append(str(path))

    for rel in [
        "data/raw/html",
        "data/processed/extracted",
        "data/processed/cleaned",
        "data/processed/chunks",
        "data/authority",
    ]:
        d = ROOT / rel
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

    return removed


def wipe_qdrant() -> str:
    settings = Settings()
    store = QdrantStore(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection=settings.qdrant_collection,
    )
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        existing = {c.name for c in client.get_collections().collections}
        for name in ("documents",):
            if name in existing and name != settings.qdrant_collection:
                client.delete_collection(name)
    except Exception as exc:
        print(f"warning: could not delete old collection: {exc}")

    emb = EmbeddingService(settings)
    dim = len(emb.embed_query("wipe"))
    store.recreate_collection(vector_size=dim)
    return f"recreated empty collection '{settings.qdrant_collection}' (dim={dim})"


def main() -> None:
    parser = argparse.ArgumentParser(description="Wipe local + Qdrant authority data")
    parser.add_argument("--skip-qdrant", action="store_true")
    args = parser.parse_args()

    removed = wipe_local_data()
    print("Removed:")
    for p in removed:
        print(f"  - {p}")
    if not args.skip_qdrant:
        print(wipe_qdrant())
    print("Next: python -m scripts.ingest_authority")


if __name__ == "__main__":
    main()
