"""Stage 3: Chunk cleaned documents for retrieval."""

import hashlib
import json
import re
from pathlib import Path

from processing.models import CleanedDocument, ProcessedChunk


def split_into_sections(text: str) -> list[tuple[str, str]]:
    """Split on markdown headings; returns (section_title, section_body)."""
    parts = re.split(r"(?m)^(#{1,3})\s+(.+)$", text)
    if len(parts) <= 1:
        return [("Introduction", text)]

    sections: list[tuple[str, str]] = []
    preamble = parts[0].strip()
    if preamble:
        sections.append(("Introduction", preamble))

    i = 1
    while i < len(parts):
        title = parts[i + 1].strip()
        body = parts[i + 2].strip() if i + 2 < len(parts) else ""
        sections.append((title, body))
        i += 3

    return sections


def chunk_section(
    section_text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    """Character-based chunking with overlap within a section."""
    if len(section_text) <= chunk_size:
        return [section_text]

    chunks: list[str] = []
    start = 0
    while start < len(section_text):
        end = start + chunk_size
        piece = section_text[start:end].strip()
        if piece:
            chunks.append(piece)
        start = end - chunk_overlap

    return chunks


def make_chunk_id(source: str, url: str, chunk_index: int) -> str:
    digest = hashlib.sha1(f"{source}:{url}:{chunk_index}".encode()).hexdigest()[:12]
    return f"{source}-{digest}"


def chunk_document(
    doc: CleanedDocument,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[ProcessedChunk]:
    chunks: list[ProcessedChunk] = []
    chunk_index = 0

    for section_title, section_body in split_into_sections(doc.text):
        for piece in chunk_section(section_body, chunk_size, chunk_overlap):
            if len(piece) < 80:
                continue

            chunk = ProcessedChunk(
                chunk_id=make_chunk_id(doc.source, doc.url, chunk_index),
                source=doc.source,
                url=doc.url,
                title=doc.title,
                section=section_title,
                text=piece,
                chunk_index=chunk_index,
                char_count=len(piece),
                metadata={
                    "word_count": len(piece.split()),
                    "section": section_title,
                },
            )
            chunks.append(chunk)
            chunk_index += 1

    return chunks


def chunk_cleaned_files(
    cleaned_dir: Path,
    output_dir: Path,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[ProcessedChunk]:
    output_dir.mkdir(parents=True, exist_ok=True)
    all_chunks: list[ProcessedChunk] = []

    for path in sorted(cleaned_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        cleaned = CleanedDocument(**raw)
        doc_chunks = chunk_document(cleaned, chunk_size, chunk_overlap)
        all_chunks.extend(doc_chunks)

    jsonl_path = output_dir / "chunks.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk.to_dict()) + "\n")

    summary = {
        "chunk_count": len(all_chunks),
        "sources": sorted({c.source for c in all_chunks}),
        "avg_char_count": round(sum(c.char_count for c in all_chunks) / max(len(all_chunks), 1), 1),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return all_chunks
