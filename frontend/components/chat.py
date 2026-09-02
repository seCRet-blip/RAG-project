"""Chat UI components."""

import os

from fasthtml.common import A, Button, Div, Form, H2, H3, Hr, Input, P, Strong

from frontend.components.formatting import answer_lines, line_kind, plain_text_answer

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def page_style() -> str:
    return """
    body { font-family: system-ui, sans-serif; max-width: 820px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }
    .answer-box { background: #f0f4f8; padding: 1.25rem 1.35rem; border-radius: 8px; margin: 1rem 0; }
    .answer-text { margin: 0.75rem 0 0; }
    .answer-section {
      font-weight: 700;
      font-size: 0.95rem;
      letter-spacing: 0.02em;
      margin: 1.1rem 0 0.35rem;
      color: #0f172a;
    }
    .answer-section:first-child { margin-top: 0; }
    .answer-body {
      margin: 0.2rem 0 0.55rem;
      line-height: 1.55;
      color: #334155;
    }
    .answer-bullet {
      margin: 0.15rem 0 0.15rem 0.1rem;
      padding-left: 1rem;
      line-height: 1.5;
      color: #334155;
    }
    .answer-spacer { height: 0.55rem; }
    .source-card { border-left: 3px solid #3b82f6; padding: 0.65rem 1rem; margin: 0.65rem 0; background: #fafafa; }
    .preview { color: #555; font-size: 0.9rem; margin: 0.25rem 0; }
    input[type=text] { width: 70%; padding: 0.5rem; }
    button { padding: 0.5rem 1rem; }
    .error { color: #b91c1c; }
    .loading { color: #666; font-style: italic; }
    """


def chat_ui():
    return Form(
        Input(
            name="message",
            placeholder="e.g. What's the difference between ENTRYPOINT and CMD?",
            required=True,
        ),
        Button("Ask", type="submit"),
        method="post",
        action="/ask",
        enctype="application/x-www-form-urlencoded",
        hx_post="/ask",
        hx_target="#chat-results",
        hx_swap="innerHTML",
        hx_indicator="#loading",
        id="chat-form",
    )


def answer_block(answer: str) -> Div:
    lines = answer_lines(answer)
    if not lines:
        return Div(P("—", cls="answer-body"))

    children = []
    for line in lines:
        kind = line_kind(line)
        if kind == "spacer":
            children.append(Div(cls="answer-spacer"))
        elif kind == "section":
            children.append(P(line.strip(), cls="answer-section"))
        elif kind == "bullet":
            children.append(P(line.strip(), cls="answer-bullet"))
        else:
            children.append(P(line.strip(), cls="answer-body"))
    return Div(*children, cls="answer-text")


def source_card(source: dict) -> Div:
    title = source.get("title") or source.get("source") or "documentation"
    url = source.get("url")
    preview = plain_text_answer(source.get("preview", ""))
    link = A("View doc", href=url, target="_blank") if url else ""
    return Div(
        P(Strong(title)),
        P(link),
        P(f"Score: {source.get('score', 0)} | Section: {source.get('section') or 'n/a'}", cls="preview"),
        P(preview, cls="preview"),
        cls="source-card",
    )


def chat_results(question: str, answer: str, sources: list[dict], error: str | None = None) -> Div:
    """Answer fragment swapped into #chat-results via HTMX."""
    if error:
        return Div(P(error, cls="error"), id="chat-results")

    if not question.strip():
        return Div(P("Please enter a question.", cls="error"), id="chat-results")

    return Div(
        Div(
            P(Strong("Question: "), question),
            P(Strong("Answer:")),
            answer_block(answer),
            cls="answer-box",
        ),
        H3("Sources from Qdrant"),
        *[source_card(s) for s in sources],
        id="chat-results",
    )


def chat_page(question: str = "", answer: str = "", sources: list[dict] | None = None, error: str | None = None) -> Div:
    sources = sources or []
    return Div(
        H2("RAG Chat"),
        P("Ask questions about Docker & Kubernetes docs (local Qdrant + vLLM)"),
        P("Searching docs and generating answer…", id="loading", cls="loading", style="display:none"),
        chat_results(question, answer, sources, error) if (question or error) else Div(id="chat-results"),
        Hr(),
        chat_ui(),
        cls="container",
    )
