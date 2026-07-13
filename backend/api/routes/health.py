"""Health check endpoints."""

from fastapi import APIRouter, Depends

from backend.api.deps import get_llm_client, get_qdrant_store
from backend.services.llm import VLLMClient
from retriever.client import QdrantStore

router = APIRouter()


@router.get("/health")
async def health_check(
    store: QdrantStore = Depends(get_qdrant_store),
    llm: VLLMClient = Depends(get_llm_client),
) -> dict:
    qdrant_ok = False
    try:
        store.health_check()
        qdrant_ok = True
    except Exception:
        pass

    vllm_ok = await llm.health_check()

    return {
        "status": "ok" if qdrant_ok else "degraded",
        "qdrant": qdrant_ok,
        "vllm": vllm_ok,
    }
