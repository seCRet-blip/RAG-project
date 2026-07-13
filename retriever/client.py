"""Qdrant vector store client."""

import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


class QdrantStore:
    def __init__(self, host: str, port: int, collection: str) -> None:
        self._client = QdrantClient(host=host, port=port)
        self._collection = collection

    def health_check(self) -> None:
        self._client.get_collections()

    def ensure_collection(self, vector_size: int) -> None:
        collections = [c.name for c in self._client.get_collections().collections]
        if self._collection not in collections:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def recreate_collection(self, vector_size: int) -> None:
        collections = [c.name for c in self._client.get_collections().collections]
        if self._collection in collections:
            self._client.delete_collection(collection_name=self._collection)
        self._client.create_collection(
            collection_name=self._collection,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict],
    ) -> None:
        points = [
            PointStruct(id=_to_point_id(point_id), vector=vector, payload=payload)
            for point_id, vector, payload in zip(ids, vectors, payloads)
        ]
        self._client.upsert(collection_name=self._collection, points=points)

    def search(self, vector: list[float], top_k: int) -> list[dict]:
        results = self._client.search(
            collection_name=self._collection,
            query_vector=vector,
            limit=top_k,
        )
        return [
            {
                "text": hit.payload.get("text", ""),
                "score": hit.score,
                "source": hit.payload.get("source"),
                "url": hit.payload.get("url"),
                "title": hit.payload.get("title"),
                "section": hit.payload.get("section"),
            }
            for hit in results
        ]


def _to_point_id(point_id: str) -> str:
    """Qdrant accepts UUID strings; hash non-UUID ids deterministically."""
    try:
        uuid.UUID(point_id)
        return point_id
    except ValueError:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, point_id))
