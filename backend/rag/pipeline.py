"""RAG orchestration: retrieve context, then generate with vLLM."""

from dataclasses import dataclass

from backend.services.llm import VLLMClient
from retriever.search import Retriever, SearchResult

RAG_PROMPT = """You are a helpful assistant answering questions about Docker and Kubernetes documentation.
Use ONLY the context below. If the context does not contain enough information, say so clearly.
Keep answers concise (2-4 sentences).

Context:
{context}

Question: {query}

Answer:"""


@dataclass
class RAGResult:
    answer: str
    chunks: list[SearchResult]


class RAGPipeline:
    def __init__(self, retriever: Retriever, llm: VLLMClient) -> None:
        self._retriever = retriever
        self._llm = llm

    async def run(self, query: str, top_k: int = 5) -> RAGResult:
        chunks = self._retriever.search(query=query, top_k=top_k)

        if not chunks:
            return RAGResult(
                answer="No relevant documentation found in the index. Try re-running sync_docs.",
                chunks=[],
            )

        context_parts = []
        for i, chunk in enumerate(chunks, start=1):
            header = chunk.title or chunk.source or "doc"
            context_parts.append(f"[{i}] {header}\n{chunk.text}")
        context = "\n\n".join(context_parts)

        prompt = RAG_PROMPT.format(context=context, query=query)
        answer = await self._llm.generate(prompt)
        return RAGResult(answer=answer, chunks=chunks)
