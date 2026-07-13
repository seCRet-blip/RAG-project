"""Embedding generation service (free, local — no API keys)."""

from fastembed import TextEmbedding

from backend.core.config import Settings

# Maps settings name to fastembed model id
MODEL_MAP = {
    "sentence-transformers/all-MiniLM-L6-v2": "BAAI/bge-small-en-v1.5",
}


class EmbeddingService:
    def __init__(self, settings: Settings | None = None) -> None:
        settings = settings or Settings()
        model_name = MODEL_MAP.get(settings.embedding_model, "BAAI/bge-small-en-v1.5")
        self._model = TextEmbedding(model_name=model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._model.embed(texts)]

    def embed_query(self, query: str) -> list[float]:
        return self.embed([query])[0]
