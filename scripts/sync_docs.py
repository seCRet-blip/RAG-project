"""Full doc sync: crawl → process → Qdrant (free, local)."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from crawler.config import SOURCES, CrawlSettings
from crawler.crawl import crawl_source
from processing.pipeline import DataPipeline
from retriever.chunk_loader import ingest_processed_chunks
from retriever.client import QdrantStore

from backend.core.config import Settings
from backend.services.embeddings import EmbeddingService


CHECKPOINT_PATH = Path("data/sync_checkpoint.json")


def qdrant_is_ready(settings: Settings) -> bool:
    try:
        store = QdrantStore(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            collection=settings.qdrant_collection,
        )
        store.health_check()
        return True
    except Exception as exc:
        print(f"Qdrant not reachable at {settings.qdrant_host}:{settings.qdrant_port} — {exc}")
        return False


def run_sync(
    max_pages: int | None = None,
    recreate_collection: bool = True,
    skip_crawl: bool = False,
) -> dict:
    """
    End-to-end sync pipeline (checkpoint).

    1. Crawl kubernetes + docker docs
    2. Extract → clean → chunk
    3. Index chunks into Qdrant
    """
    settings = Settings()
    crawl_settings = CrawlSettings()
    pipeline = DataPipeline(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    if not qdrant_is_ready(settings):
        raise RuntimeError(
            "Qdrant is not available. Use the existing rag-qdrant container "
            f"at {settings.qdrant_host}:{settings.qdrant_port}."
        )

    crawl_results: dict[str, int] = {}
    process_results: dict[str, dict] = {}

    if not skip_crawl:
        for name, source in SOURCES.items():
            if max_pages is not None:
                from dataclasses import replace
                source = replace(source, max_pages=max_pages)
            print(f"\n[1/3] Crawling {name}...")
            manifest = crawl_source(source, crawl_settings)
            crawl_results[name] = manifest["page_count"]

    for name in SOURCES:
        print(f"\n[2/3] Processing {name}...")
        result = pipeline.run(source_name=name, stage="all")
        process_results[name] = {
            "extracted": result.extracted_count,
            "cleaned": result.cleaned_count,
            "chunks": result.chunk_count,
        }

    if recreate_collection:
        print("\n[3/3] Recreating Qdrant collection for a fresh monthly index...")
        embeddings = EmbeddingService(settings)
        vector_size = len(embeddings.embed_query("dimension probe"))
        store = QdrantStore(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            collection=settings.qdrant_collection,
        )
        store.recreate_collection(vector_size=vector_size)
    else:
        print("\n[3/3] Upserting into existing Qdrant collection...")

    total_indexed = ingest_processed_chunks(source=None)

    checkpoint = {
        "status": "complete",
        "completed_at": datetime.now(UTC).isoformat(),
        "qdrant": {
            "host": settings.qdrant_host,
            "port": settings.qdrant_port,
            "collection": settings.qdrant_collection,
        },
        "crawl": crawl_results,
        "process": process_results,
        "indexed_chunks": total_indexed,
        "cost": "free — local crawl, local embeddings, local Qdrant",
    }

    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_PATH.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
    print(f"\nCheckpoint saved: {CHECKPOINT_PATH}")
    print(f"Indexed {total_indexed} chunks into Qdrant collection '{settings.qdrant_collection}'")

    return checkpoint


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync Kubernetes + Docker docs into Qdrant (free, local)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Limit pages per source (omit for default 100)",
    )
    parser.add_argument(
        "--skip-crawl",
        action="store_true",
        help="Reuse existing raw HTML; only process + index",
    )
    parser.add_argument(
        "--no-recreate",
        action="store_true",
        help="Upsert into existing collection instead of full refresh",
    )
    args = parser.parse_args()

    checkpoint = run_sync(
        max_pages=args.max_pages,
        recreate_collection=not args.no_recreate,
        skip_crawl=args.skip_crawl,
    )
    print(json.dumps(checkpoint, indent=2))


if __name__ == "__main__":
    main()
