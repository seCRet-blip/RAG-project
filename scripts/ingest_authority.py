"""CLI: ingest sniper-bot authority sources into Qdrant (local fastembed)."""

from __future__ import annotations

import argparse
import json

from retriever.authority_loader import index_authority


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest AI Sniper Bot authority docs/config/code into Qdrant"
    )
    parser.add_argument(
        "--bot-repo",
        default=None,
        help="Absolute path to AI_sniper_bot_sol_base (or set BOT_REPO_ROOT)",
    )
    parser.add_argument(
        "--no-recreate",
        action="store_true",
        help="Upsert without recreating the collection",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build chunks only — do not write to Qdrant",
    )
    args = parser.parse_args()

    if args.dry_run:
        from authority.ingest import build_chunks, write_chunks_jsonl
        from authority.manifest import resolve_bot_root
        from pathlib import Path

        bot = resolve_bot_root(args.bot_repo)
        chunks = build_chunks(bot)
        path = write_chunks_jsonl(chunks, Path("data/authority/chunks.jsonl"))
        by_ns: dict[str, int] = {}
        for c in chunks:
            by_ns[c.namespace] = by_ns.get(c.namespace, 0) + 1
        print(json.dumps({"dry_run": True, "chunks": len(chunks), "by_namespace": by_ns, "path": str(path)}, indent=2))
        return

    result = index_authority(args.bot_repo, recreate=not args.no_recreate)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
