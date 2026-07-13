"""Semantic search over Qdrant."""

from dataclasses import dataclass

from backend.services.embeddings import EmbeddingService
from retriever.client import QdrantStore


@dataclass
class SearchResult:
    text: str
    score: float
    source: str | None = None
    url: str | None = None
    title: str | None = None
    section: str | None = None


class Retriever:
    def __init__(self, store: QdrantStore) -> None:
        self.store = store
        self._embeddings = EmbeddingService()

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        vector = self._embeddings.embed_query(query)
        hits = self.store.search(vector=vector, top_k=top_k)
        return [
            SearchResult(
                text=hit["text"],
                score=hit["score"],
                source=hit.get("source"),
                url=hit.get("url"),
                title=hit.get("title"),
                section=hit.get("section"),
            )
            for hit in hits
        ]
