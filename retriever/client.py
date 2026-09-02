"""Qdrant vector store client with namespace filtering."""

import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchAny, PointStruct, VectorParams


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

    def search(
        self,
        vector: list[float],
        top_k: int,
        namespaces: list[str] | None = None,
    ) -> list[dict]:
        query_filter = None
        if namespaces:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="namespace",
                        match=MatchAny(any=namespaces),
                    )
                ]
            )

        results = self._client.search(
            collection_name=self._collection,
            query_vector=vector,
            limit=top_k,
            query_filter=query_filter,
        )
        return [
            {
                "text": hit.payload.get("text", "") if hit.payload else "",
                "score": hit.score,
                "source": (hit.payload or {}).get("source"),
                "namespace": (hit.payload or {}).get("namespace"),
                "source_path": (hit.payload or {}).get("source_path"),
                "freshness": (hit.payload or {}).get("freshness"),
                "asset": (hit.payload or {}).get("asset"),
                "url": (hit.payload or {}).get("url") or (hit.payload or {}).get("source_path"),
                "title": (hit.payload or {}).get("title"),
                "section": (hit.payload or {}).get("section"),
            }
            for hit in results
        ]


def _to_point_id(point_id: str) -> str:
    try:
        uuid.UUID(point_id)
        return point_id
    except ValueError:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, point_id))
