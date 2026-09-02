"""Processing pipeline tests."""

from processing.chunk import chunk_document, split_into_sections
from processing.clean import clean_document, clean_text
from processing.models import CleanedDocument, ExtractedDocument


def test_clean_text_collapses_whitespace():
    raw = "Hello   world\n\n\n\nFoo   bar"
    assert clean_text(raw) == "Hello world\n\nFoo bar"


def test_split_into_sections():
    text = "# Title\n\nIntro\n\n## Section A\n\nBody A\n\n## Section B\n\nBody B"
    sections = split_into_sections(text)
    assert sections[0][0] == "Title"
    assert any(s[0] == "Section A" for s in sections)


def test_chunk_document_preserves_metadata():
    doc = CleanedDocument(
        source="docs-ai",
        url="docs/ai/10_INVARIANTS.md",
        title="Invariants",
        text="SOL train and serve footing must match. " * 30,
        word_count=150,
    )
    chunks = chunk_document(doc, chunk_size=200, chunk_overlap=40)
    assert len(chunks) >= 1
    assert chunks[0].source == "docs-ai"
    assert "footing" in chunks[0].text


def test_clean_document_adds_source_url():
    extracted = ExtractedDocument(
        source="docs-ai",
        url="docs/ai/08_EVAL_AND_MEASUREMENT.md",
        title="Eval",
        headings=["Overview"],
        body="Use direction_correct_close and exclude GARBAGE rows.",
        raw_file="docs/ai/08_EVAL_AND_MEASUREMENT.md",
    )
    cleaned = clean_document(extracted)
    assert "direction_correct_close" in cleaned.text
    assert "GARBAGE" in cleaned.text
