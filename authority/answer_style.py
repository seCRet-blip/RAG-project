"""Retrieval helpers — topic routing only, no answer-schema overfitting."""

from __future__ import annotations

import re

# Prefer high-signal lines when packing small-model context
PRIORITY_TERMS = (
    "CANONICAL_BTC_REGIME",
    "encode_btc_regime",
    "direction_correct_close",
    "filter_post_deploy",
    "prediction_id",
    "GARBAGE",
    "ranging",
    "unknown",
    "SNIPER_",
    "footing",
    "last_deployed_at",
)


def prioritize_chunk_text(text: str, max_chars: int) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text

    lines = [ln for ln in text.splitlines() if ln.strip()]
    scored: list[tuple[int, int, str]] = []
    for i, ln in enumerate(lines):
        score = sum(1 for t in PRIORITY_TERMS if t.lower() in ln.lower())
        scored.append((score, -i, ln))

    scored.sort(reverse=True)
    chosen: list[str] = []
    used = 0
    for score, _neg_i, ln in scored:
        if score == 0 and chosen:
            continue
        add = len(ln) + 1
        if used + add > max_chars:
            continue
        chosen.append(ln)
        used += add

    if not chosen:
        return text[: max_chars - 20].rstrip() + "\n...[truncated]..."

    order = {ln: i for i, ln in enumerate(lines)}
    chosen.sort(key=lambda ln: order.get(ln, 0))
    out = "\n".join(chosen)
    if len(out) > max_chars:
        out = out[: max_chars - 20].rstrip() + "\n...[truncated]..."
    return out


def query_priority_keys(query: str) -> tuple[str, ...]:
    """Keys to re-rank retrieved chunks for this query (retrieval only)."""
    q = query.lower()
    if re.search(r"btc|regime|encode|codebook|ranging|canonical", q):
        return (
            "CANONICAL_BTC_REGIME",
            "encode_btc_regime",
            "btc_regime_encoding",
            "03_FEATURE_CONTRACTS",
            "ranging",
            "unknown",
        )
    if re.search(r"accurac|direction_correct|measure|garbage|prediction_id|filter_post", q):
        return (
            "direction_correct_close",
            "filter_post_deploy",
            "deploy_boundary",
            "GARBAGE",
            "08_EVAL",
            "I7",
            "I8",
            "I12",
        )
    if re.search(r"footing|stationar", q):
        return ("footing", "stationar", "SNIPER_SOL_STATIONARIZE", "sol_footing")
    return ()
