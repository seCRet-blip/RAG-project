"""Chunk strategies for sniper-bot authority sources."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from authority.models import AuthorityChunk


def _cid(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode()).hexdigest()[:16]
    return digest


def chunk_markdown_sections(
    text: str,
    *,
    namespace: str,
    source_path: str,
    freshness: str,
    asset: str | None = None,
) -> list[AuthorityChunk]:
    """Split on ## headings; keep tables and lists with their section."""
    parts = re.split(r"(?m)^(#{1,3})\s+(.+)$", text)
    chunks: list[AuthorityChunk] = []

    if len(parts) <= 1:
        body = text.strip()
        if body:
            chunks.append(
                AuthorityChunk(
                    chunk_id=_cid(namespace, source_path, "whole"),
                    text=body,
                    namespace=namespace,
                    source_path=source_path,
                    freshness=freshness,
                    title=Path(source_path).name,
                    section="document",
                    asset=asset,  # type: ignore[arg-type]
                )
            )
        return chunks

    preamble = parts[0].strip()
    if preamble:
        chunks.append(
            AuthorityChunk(
                chunk_id=_cid(namespace, source_path, "preamble"),
                text=preamble,
                namespace=namespace,
                source_path=source_path,
                freshness=freshness,
                title=Path(source_path).name,
                section="Introduction",
                asset=asset,  # type: ignore[arg-type]
            )
        )

    i = 1
    while i < len(parts):
        level, title = parts[i], parts[i + 1].strip()
        body = parts[i + 2].strip() if i + 2 < len(parts) else ""
        content = f"{'#' * len(level)} {title}\n\n{body}".strip()
        if content:
            chunks.append(
                AuthorityChunk(
                    chunk_id=_cid(namespace, source_path, title),
                    text=content,
                    namespace=namespace,
                    source_path=source_path,
                    freshness=freshness,
                    title=Path(source_path).name,
                    section=title,
                    asset=asset,  # type: ignore[arg-type]
                )
            )
        i += 3
    return chunks


def chunk_compose_services(
    text: str,
    *,
    namespace: str,
    source_path: str,
    freshness: str,
) -> list[AuthorityChunk]:
    """One chunk per top-level service under services:."""
    chunks: list[AuthorityChunk] = []
    # Keep header / networks / volumes as overview
    header_match = re.split(r"(?m)^services:\s*$", text, maxsplit=1)
    if header_match:
        preamble = header_match[0].strip()
        if preamble:
            chunks.append(
                AuthorityChunk(
                    chunk_id=_cid(namespace, source_path, "preamble"),
                    text=preamble,
                    namespace=namespace,
                    source_path=source_path,
                    freshness=freshness,
                    title="compose-live",
                    section="compose-preamble",
                )
            )

    services_body = header_match[1] if len(header_match) > 1 else text
    # Split on lines starting with two-space service name (compose indent)
    service_pattern = re.compile(r"(?m)^  ([a-zA-Z0-9_-]+):\s*$")
    matches = list(service_pattern.finditer(services_body))
    for idx, match in enumerate(matches):
        name = match.group(1)
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(services_body)
        block = services_body[start:end].strip()
        if name in {"networks", "volumes"}:
            continue
        chunks.append(
            AuthorityChunk(
                chunk_id=_cid(namespace, source_path, name),
                text=f"Service `{name}` (compose-live):\n\n{block}",
                namespace=namespace,
                source_path=source_path,
                freshness=freshness,
                title=f"compose:{name}",
                section=name,
            )
        )
    return chunks


def chunk_yaml_sections(
    text: str,
    *,
    namespace: str,
    source_path: str,
    freshness: str,
) -> list[AuthorityChunk]:
    """Split YAML on top-level keys."""
    chunks: list[AuthorityChunk] = []
    pattern = re.compile(r"(?m)^([A-Za-z0-9_]+):\s*")
    matches = list(pattern.finditer(text))
    if not matches:
        return [
            AuthorityChunk(
                chunk_id=_cid(namespace, source_path, "whole"),
                text=text,
                namespace=namespace,
                source_path=source_path,
                freshness=freshness,
                title=Path(source_path).stem,
                section="document",
            )
        ]

    for idx, match in enumerate(matches):
        key = match.group(1)
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        chunks.append(
            AuthorityChunk(
                chunk_id=_cid(namespace, source_path, key),
                text=block,
                namespace=namespace,
                source_path=source_path,
                freshness=freshness,
                title=Path(source_path).name,
                section=key,
            )
        )
    return chunks


def chunk_whole_file(
    text: str,
    *,
    namespace: str,
    source_path: str,
    freshness: str,
    asset: str | None = None,
    title: str | None = None,
) -> list[AuthorityChunk]:
    body = text.strip()
    if not body:
        return []
    return [
        AuthorityChunk(
            chunk_id=_cid(namespace, source_path, "whole"),
            text=body,
            namespace=namespace,
            source_path=source_path,
            freshness=freshness,
            title=title or Path(source_path).name,
            section="document",
            asset=asset,  # type: ignore[arg-type]
        )
    ]


def infer_asset(path: str) -> str | None:
    lower = path.lower().replace("\\", "/")
    if "/sol/" in lower or "_sol." in lower or "sol_" in Path(lower).name:
        return "SOL"
    if "/ltc/" in lower or "_ltc." in lower or "ltc_" in Path(lower).name:
        return "LTC"
    return None
