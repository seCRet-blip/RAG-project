"""Retriever unit tests."""

from retriever.search import SearchResult


def test_search_result_dataclass():
    result = SearchResult(text="hello", score=0.95, source="doc.txt")
    assert result.text == "hello"
    assert result.score == 0.95
