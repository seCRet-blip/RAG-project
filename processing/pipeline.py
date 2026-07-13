"""Orchestrate the full data processing pipeline."""

from dataclasses import dataclass
from pathlib import Path

from processing.chunk import chunk_cleaned_files
from processing.clean import clean_extracted_files
from processing.extract import extract_source
from processing.models import CleanedDocument, ExtractedDocument, ProcessedChunk


@dataclass
class PipelineResult:
    source: str
    extracted_count: int
    cleaned_count: int
    chunk_count: int


class DataPipeline:
    """
    Three-stage local pipeline (100% free — runs on your machine):

      1. extract  — HTML → structured JSON (title, headings, body)
      2. clean    — normalize whitespace, add source context
      3. chunk    — split into retrieval-sized pieces with metadata
    """

    def __init__(
        self,
        raw_dir: Path = Path("data/raw/html"),
        processed_dir: Path = Path("data/processed"),
        chunk_size: int = 800,
        chunk_overlap: int = 120,
    ) -> None:
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def run(self, source_name: str, stage: str = "all") -> PipelineResult:
        extracted_dir = self.processed_dir / "extracted" / source_name
        cleaned_dir = self.processed_dir / "cleaned" / source_name
        chunks_dir = self.processed_dir / "chunks" / source_name

        extracted_count = 0
        cleaned_count = 0
        chunk_count = 0

        if stage in {"all", "extract"}:
            extracted = extract_source(source_name, self.raw_dir, extracted_dir)
            extracted_count = len(extracted)

        if stage in {"all", "clean"}:
            cleaned = clean_extracted_files(extracted_dir, cleaned_dir)
            cleaned_count = len(cleaned)

        if stage in {"all", "chunk"}:
            chunks = chunk_cleaned_files(
                cleaned_dir,
                chunks_dir,
                self.chunk_size,
                self.chunk_overlap,
            )
            chunk_count = len(chunks)

        return PipelineResult(
            source=source_name,
            extracted_count=extracted_count,
            cleaned_count=cleaned_count,
            chunk_count=chunk_count,
        )
