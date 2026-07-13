"""CLI: create Qdrant collection if it does not exist."""

from backend.core.config import Settings
from backend.services.embeddings import EmbeddingService
from retriever.client import QdrantStore


def main() -> None:
    settings = Settings()
    store = QdrantStore(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection=settings.qdrant_collection,
    )
    embeddings = EmbeddingService(settings)
    vector_size = len(embeddings.embed_query("test"))
    store.ensure_collection(vector_size=vector_size)
    print(f"Collection '{settings.qdrant_collection}' is ready (dim={vector_size}).")


if __name__ == "__main__":
    main()
