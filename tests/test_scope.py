"""General abstain / support checks."""

from authority.scope import retrieval_supports_query
from retriever.search import SearchResult


def _c(text: str, score: float = 0.5, path: str = "docs/ai/x.md") -> SearchResult:
    return SearchResult(text=text, score=score, namespace="docs-ai", source_path=path)


def test_unrelated_ops_query_not_supported():
    chunks = [
        _c("CANONICAL_BTC_REGIME unknown=3 ranging=0", 0.55),
        _c("SOL footing must match train and serve", 0.5),
    ]
    q = "How do I fix a CrashLoopBackOff on my sniper pod with a Helm chart?"
    assert not retrieval_supports_query(q, chunks)


def test_encode_query_supported_by_codebook_chunk():
    chunks = [_c("CANONICAL_BTC_REGIME: ranging=0 unknown=3 encode_btc_regime", 0.7)]
    q = "Should ranging encode as 1?"
    assert retrieval_supports_query(q, chunks)


def test_low_score_not_supported():
    chunks = [_c("ranging encode codebook", 0.1)]
    assert not retrieval_supports_query("Should ranging encode as 1?", chunks)
