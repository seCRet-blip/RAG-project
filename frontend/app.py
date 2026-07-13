"""FastHTML frontend — port 8788 (not 8787 dashboard)."""

from dataclasses import dataclass

import httpx
from fasthtml.common import FastHTML, Style, Title

from frontend.components.chat import API_BASE_URL, chat_page, chat_results, page_style

app = FastHTML(hdrs=(Title("RAG Chat"), Style(page_style())))


@dataclass
class AskResult:
    question: str
    answer: str
    sources: list[dict]
    error: str | None = None


@app.get("/")
def home():
    return chat_page()


async def _fetch_answer(message: str) -> AskResult:
    question = (message or "").strip()
    if not question:
        return AskResult(question="", answer="", sources=[], error="Please enter a question.")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/chat/",
                json={"message": question, "top_k": 5},
            )
            response.raise_for_status()
            data = response.json()
    except httpx.ConnectError:
        return AskResult(
            question=question,
            answer="",
            sources=[],
            error=f"Cannot reach API at {API_BASE_URL}. Start: py -m uvicorn backend.main:app --port 8000",
        )
    except httpx.HTTPStatusError as exc:
        return AskResult(
            question=question,
            answer="",
            sources=[],
            error=f"API error ({exc.response.status_code}): {exc.response.text[:200]}",
        )
    except Exception as exc:
        return AskResult(question=question, answer="", sources=[], error=str(exc))

    return AskResult(
        question=question,
        answer=data.get("answer", ""),
        sources=data.get("sources", []),
    )


@app.post("/ask")
async def ask(message: str = ""):
    result = await _fetch_answer(message)
    return chat_results(result.question, result.answer, result.sources, error=result.error)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("frontend.app:app", host="127.0.0.1", port=8788, reload=True)
