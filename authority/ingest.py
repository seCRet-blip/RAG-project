"""Build authority chunks from bot repo per ingest_manifest.yaml."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from authority.chunkers import (
    chunk_compose_services,
    chunk_markdown_sections,
    chunk_whole_file,
    chunk_yaml_sections,
    infer_asset,
)
from authority.code_slices import extract_code_slices
from authority.live_card import write_live_card
from authority.manifest import load_manifest, resolve_bot_root
from authority.models import AuthorityChunk, EXCLUDED_BY_DEFAULT

RAG_ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _expand_globs(bot: Path, globs: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in globs:
        files.extend(sorted(bot.glob(pattern)))
    return [p for p in files if p.is_file()]


def build_chunks(
    bot_root: Path | None = None,
    manifest_path: Path | None = None,
    *,
    include_opt_in: bool = False,
) -> list[AuthorityChunk]:
    bot = resolve_bot_root(bot_root)
    manifest = load_manifest(manifest_path)
    chunks: list[AuthorityChunk] = []

    for source in manifest.get("sources", []):
        if not source.get("enabled", True):
            continue
        namespace = source["namespace"]
        if not include_opt_in and not source.get("default_retrieve", True):
            # Still ingest handoff if enabled+false? Spec says handoff enabled but opt-in retrieve.
            # Ingest opt-in namespaces when enabled=true so they can be queried explicitly.
            if namespace in EXCLUDED_BY_DEFAULT and not source.get("enabled", True):
                continue
        if namespace == "web-generic":
            continue
        if namespace == "footgun" and not source.get("enabled", False):
            continue

        freshness = str(source.get("freshness", "repo-file"))
        strategy = source.get("chunk_strategy", "whole_file")

        if source.get("generated"):
            out = RAG_ROOT / source.get("output", "data/authority/rag_live_card.md")
            write_live_card(bot, out)
            text = _read(out)
            chunks.extend(
                chunk_whole_file(
                    text,
                    namespace=namespace,
                    source_path=str(out.relative_to(RAG_ROOT)).replace("\\", "/"),
                    freshness="generated",
                    title="rag_live_card",
                )
            )
            continue

        if strategy == "code_slices":
            for slice_spec in source.get("slices", []):
                rel = slice_spec["path"]
                path = bot / rel
                chunks.extend(
                    extract_code_slices(
                        path,
                        relative=rel.replace("\\", "/"),
                        symbols=list(slice_spec.get("symbols", [])),
                        namespace=namespace,
                        freshness=freshness,
                        asset=slice_spec.get("asset", "BOTH"),
                        max_chars=int(slice_spec.get("max_chars", 20000)),
                    )
                )
            continue

        paths: list[Path] = []
        for rel in source.get("paths", []) or []:
            p = bot / rel
            if p.is_file():
                paths.append(p)
        if source.get("globs"):
            paths.extend(_expand_globs(bot, source["globs"]))

        # de-dupe
        seen: set[Path] = set()
        unique_paths = []
        for p in paths:
            if p not in seen:
                seen.add(p)
                unique_paths.append(p)

        for path in unique_paths:
            rel = path.relative_to(bot).as_posix()
            text = _read(path)
            asset = None
            if source.get("asset_from_filename") or source.get("asset_from_path"):
                asset = infer_asset(rel)

            if strategy == "markdown_sections":
                chunks.extend(
                    chunk_markdown_sections(
                        text,
                        namespace=namespace,
                        source_path=rel,
                        freshness=freshness,
                        asset=asset,
                    )
                )
            elif strategy == "compose_services":
                chunks.extend(
                    chunk_compose_services(
                        text,
                        namespace=namespace,
                        source_path=rel,
                        freshness=freshness,
                    )
                )
            elif strategy == "yaml_sections":
                chunks.extend(
                    chunk_yaml_sections(
                        text,
                        namespace=namespace,
                        source_path=rel,
                        freshness=freshness,
                    )
                )
            else:
                chunks.extend(
                    chunk_whole_file(
                        text,
                        namespace=namespace,
                        source_path=rel,
                        freshness=freshness,
                        asset=asset,
                    )
                )

    return chunks


def write_chunks_jsonl(chunks: list[AuthorityChunk], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")
    summary = {
        "chunk_count": len(chunks),
        "by_namespace": {},
    }
    for c in chunks:
        summary["by_namespace"][c.namespace] = summary["by_namespace"].get(c.namespace, 0) + 1
    (path.parent / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return path
