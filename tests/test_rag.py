"""RAG pipeline tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.rag.pipeline import RAGPipeline
from retriever.search import SearchResult


@pytest.mark.asyncio
async def test_pipeline_returns_answer_and_chunks():
    retriever = MagicMock()
    retriever.search.return_value = [
        SearchResult(
            text="ENTRYPOINT sets the default executable.",
            score=0.92,
            source="docker",
            url="https://docs.docker.com/reference/dockerfile/",
            title="Dockerfile reference",
            section="ENTRYPOINT",
        )
    ]

    llm = AsyncMock()
    llm.generate.return_value = "ENTRYPOINT defines the main process."

    pipeline = RAGPipeline(retriever=retriever, llm=llm)
    result = await pipeline.run("What is ENTRYPOINT?", top_k=3)

    assert "ENTRYPOINT" in result.answer
    assert len(result.chunks) == 1
    retriever.search.assert_called_once_with(query="What is ENTRYPOINT?", top_k=3)
    llm.generate.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_handles_no_chunks():
    retriever = MagicMock()
    retriever.search.return_value = []
    llm = AsyncMock()

    pipeline = RAGPipeline(retriever=retriever, llm=llm)
    result = await pipeline.run("unknown topic")

    assert "No relevant documentation" in result.answer
    llm.generate.assert_not_called()
