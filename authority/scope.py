"""General abstain when retrieval does not support the question.

No hard-coded topic lists (Helm, CrashLoop, etc.). If the retrieved chunks
do not cover the question's content words or similarity is weak, refuse.
"""

from __future__ import annotations

import re

from retriever.search import SearchResult

# Weak / structural words — ignore for overlap checks
_STOP = frozenset(
    """
    a an the and or but if then else when how what which who why where
    is are was were be been being do does did doing can could should would
    will may might must have has had having of to for from with on in at by
    into onto over under about as it its my your our their this that these
    those i me we you they he she not no yes please help fix make get set
    """.split()
)

_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_./-]{1,}")


def content_terms(text: str) -> set[str]:
    terms: set[str] = set()
    for raw in _TOKEN_RE.findall(text.lower()):
        tok = raw.strip("./-")
        if len(tok) < 3 or tok in _STOP:
            continue
        terms.add(tok)
    return terms


def retrieval_supports_query(
    query: str,
    chunks: list[SearchResult],
    *,
    min_score: float = 0.35,
    min_overlap: float = 0.2,
) -> bool:
    """True if chunks look usable for answering this query."""
    if not chunks:
        return False

    best = max(c.score for c in chunks)
    if best < min_score:
        return False

    q_terms = content_terms(query)
    if not q_terms:
        return best >= min_score

    blob = " ".join(
        f"{c.source_path or ''} {c.title or ''} {c.section or ''} {c.text}"
        for c in chunks
    ).lower()

    hits = sum(1 for t in q_terms if t in blob)
    return (hits / len(q_terms)) >= min_overlap


REFUSAL = (
    "Unknown from sniper-bot authority — the retrieved context does not "
    "support this question. Ask about SOL/LTC train/serve, gates, flags, "
    "contracts, compose-live for this bot, or re-ingest if the source should exist."
)
