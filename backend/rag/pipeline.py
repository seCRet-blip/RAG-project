"""RAG orchestration: retrieve context, then generate with vLLM."""

from dataclasses import dataclass

from backend.core.config import Settings
from backend.services.llm import VLLMClient
from retriever.search import Retriever, SearchResult

RAG_PROMPT = """You are a helpful assistant answering questions about Docker and Kubernetes documentation.
Use ONLY the context below. If the context does not contain enough information, say so clearly.
Write in plain text only — no markdown, no bullet symbols, no bold.
Keep answers concise (2-4 sentences).

Context:
{context}

Question: {query}

Answer:"""


@dataclass
class RAGResult:
    answer: str
    chunks: list[SearchResult]


def _truncate(text: str, max_chars: int) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 20].rstrip() + "\n...[truncated]..."


def build_context(
    chunks: list[SearchResult],
    *,
    max_context_chars: int,
    max_chunk_chars: int,
) -> str:
    parts: list[str] = []
    used = 0
    for i, chunk in enumerate(chunks, start=1):
        header = chunk.title or chunk.source or "doc"
        body = _truncate(chunk.text, max_chunk_chars)
        block = f"[{i}] {header}\n{body}"
        if used + len(block) + 2 > max_context_chars:
            remaining = max_context_chars - used - 2
            if remaining < 80:
                break
            block = _truncate(block, remaining)
            parts.append(block)
            break
        parts.append(block)
        used += len(block) + 2
    return "\n\n".join(parts)


class RAGPipeline:
    def __init__(self, retriever: Retriever, llm: VLLMClient) -> None:
        self._retriever = retriever
        self._llm = llm
        self._settings = Settings()

    async def run(self, query: str, top_k: int = 5) -> RAGResult:
        fetch_k = min(top_k, self._settings.rag_top_k)
        chunks = self._retriever.search(query=query, top_k=fetch_k)

        if not chunks:
            return RAGResult(
                answer="No relevant documentation found in the index. Try running: py scripts/sync_docs.py",
                chunks=[],
            )

        context = build_context(
            chunks,
            max_context_chars=self._settings.rag_max_context_chars,
            max_chunk_chars=self._settings.rag_max_chunk_chars,
        )
        prompt = RAG_PROMPT.format(context=context, query=query)
        answer = await self._llm.generate(
            prompt,
            max_tokens=self._settings.rag_max_output_tokens,
        )
        return RAGResult(answer=answer, chunks=chunks)
