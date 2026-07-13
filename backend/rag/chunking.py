"""Text chunking utilities."""

from dataclasses import dataclass


@dataclass
class TextChunk:
    text: str
    source: str
    chunk_index: int


def chunk_text(
    text: str,
    source: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    start = 0
    index = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(TextChunk(text=chunk, source=source, chunk_index=index))
            index += 1
        start = end - chunk_overlap

    return chunks
