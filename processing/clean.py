"""Stage 2: Clean and normalize extracted text."""

import json
import re
from pathlib import Path

from processing.models import CleanedDocument, ExtractedDocument


def clean_text(text: str) -> str:
    """Remove noise while keeping technical content readable."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            lines.append("")
        elif len(stripped) >= 3 or stripped.startswith("#"):
            lines.append(stripped)

    # Keep paragraph breaks, drop triple+ blank lines
    result: list[str] = []
    blank_run = 0
    for line in lines:
        if line == "":
            blank_run += 1
            if blank_run == 1:
                result.append("")
        else:
            blank_run = 0
            result.append(line)

    return "\n".join(result).strip()


def clean_document(doc: ExtractedDocument) -> CleanedDocument:
    header = f"# {doc.title}\n\nSource: {doc.url}\n\n" if doc.title else f"Source: {doc.url}\n\n"
    cleaned = clean_text(header + doc.body)
    word_count = len(cleaned.split())

    return CleanedDocument(
        source=doc.source,
        url=doc.url,
        title=doc.title,
        text=cleaned,
        word_count=word_count,
    )


def clean_extracted_files(extracted_dir: Path, output_dir: Path) -> list[CleanedDocument]:
    output_dir.mkdir(parents=True, exist_ok=True)
    documents: list[CleanedDocument] = []

    for path in sorted(extracted_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        extracted = ExtractedDocument(**raw)
        cleaned = clean_document(extracted)
        documents.append(cleaned)

        out_path = output_dir / path.name
        out_path.write_text(json.dumps(cleaned.to_dict(), indent=2), encoding="utf-8")

    return documents
