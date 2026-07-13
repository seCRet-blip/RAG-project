"""Data models for each processing stage.

Follow the data through these stages:

  raw HTML  →  ExtractedDocument  →  CleanedDocument  →  ProcessedChunk

Each stage writes JSON files so you can inspect what changed.
"""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ExtractedDocument:
    """Stage 1 output: structured text pulled from HTML."""

    source: str
    url: str
    title: str
    headings: list[str]
    body: str
    raw_file: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CleanedDocument:
    """Stage 2 output: normalized text ready for chunking."""

    source: str
    url: str
    title: str
    text: str
    word_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProcessedChunk:
    """Stage 3 output: retrieval-ready chunks with metadata."""

    chunk_id: str
    source: str
    url: str
    title: str
    section: str
    text: str
    chunk_index: int
    char_count: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
