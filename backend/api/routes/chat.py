"""RAG chat endpoints."""

from fastapi import APIRouter, Depends

from backend.api.deps import get_llm_client, get_retriever
from backend.models.schemas import ChatRequest, ChatResponse, SourceChunk
from backend.rag.pipeline import RAGPipeline
from backend.services.llm import VLLMClient
from retriever.search import Retriever

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    retriever: Retriever = Depends(get_retriever),
    llm: VLLMClient = Depends(get_llm_client),
) -> ChatResponse:
    pipeline = RAGPipeline(retriever=retriever, llm=llm)
    result = await pipeline.run(query=request.message, top_k=request.top_k)

    sources = [
        SourceChunk(
            source=chunk.source,
            title=chunk.title,
            url=chunk.url,
            section=chunk.section,
            score=round(chunk.score, 3),
            preview=chunk.text[:200] + ("..." if len(chunk.text) > 200 else ""),
        )
        for chunk in result.chunks
    ]

    return ChatResponse(answer=result.answer, sources=sources)
