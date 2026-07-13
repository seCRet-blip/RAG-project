"""Shared FastAPI dependencies."""

from functools import lru_cache

from backend.core.config import Settings
from backend.services.llm import VLLMClient
from retriever.client import QdrantStore
from retriever.search import Retriever


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_qdrant_store() -> QdrantStore:
    settings = get_settings()
    return QdrantStore(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection=settings.qdrant_collection,
    )


def get_retriever() -> Retriever:
    return Retriever(store=get_qdrant_store())


def get_llm_client() -> VLLMClient:
    settings = get_settings()
    return VLLMClient(
        base_url=settings.vllm_base_url,
        model=settings.vllm_model,
    )
