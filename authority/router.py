"""Query-type retrieval router for sniper-bot authority RAG."""

from __future__ import annotations

import re

from authority.models import DEFAULT_NAMESPACES, EXCLUDED_BY_DEFAULT

# Order matters: encode/codebook before generic "live"/"filter" routes
ROUTES: list[tuple[re.Pattern[str], list[str]]] = [
    (
        re.compile(
            r"CANONICAL_BTC_REGIME|btc.?regime|encode|codebook|ranging\s*=|"
            r"trending_bear|trending_bull|unknown\s*=|real.?categor|"
            r"SNIPER_BTC_REAL|feature.?contract",
            re.I,
        ),
        ["code-critical", "contracts", "tests-parity", "docs-ai"],
    ),
    (
        re.compile(
            r"which\s+(column|metric|filter)|what\s+(column|metric|filter)|"
            r"how\s+(do\s+we|to)\s+(measure|eval)|"
            r"live\s+accurac|direction_correct_close|"
            r"post[- ]?deploy.*(accurac|measure|filter)|"
            r"GARBAGE.*(accurac|exclude|filter)",
            re.I,
        ),
        ["docs-ai", "code-critical", "state-live"],
    ),
    (
        re.compile(
            r"live|flag|deploy|compose|recreate|container|SNIPER_|what's live|what is live",
            re.I,
        ),
        ["state-live", "compose-live", "docs-ai"],
    ),
    (
        re.compile(
            r"feature|footing|stationar|train.?serve|contract|parity",
            re.I,
        ),
        ["code-critical", "contracts", "docs-ai", "tests-parity"],
    ),
    (
        re.compile(r"promot|gate|uplift|walk.?forward|force.?regime", re.I),
        ["config-train", "docs-ai", "state-live", "code-critical"],
    ),
    (
        re.compile(r"restart|recreate|gpu|compose|scheduler|multi-asset", re.I),
        ["compose-live", "docs-ai", "state-live"],
    ),
    (
        re.compile(r"xgboost|lightgbm|pandas|binance", re.I),
        ["docs-ai", "code-critical", "config-train"],
    ),
]


def namespaces_for_query(
    query: str,
    *,
    allow_opt_in: set[str] | None = None,
) -> list[str]:
    """Return preferred namespaces (ordered)."""
    allow = allow_opt_in or set()
    preferred: list[str] = []
    for pattern, nss in ROUTES:
        if pattern.search(query):
            preferred.extend(nss)
            break
    if not preferred:
        preferred = list(DEFAULT_NAMESPACES)

    if "handoff" in query.lower() and "handoff-secondary" in allow:
        preferred.append("handoff-secondary")

    out: list[str] = []
    seen: set[str] = set()
    for ns in preferred:
        if ns in EXCLUDED_BY_DEFAULT and ns not in allow:
            continue
        if ns not in seen:
            seen.add(ns)
            out.append(ns)
    return out or list(DEFAULT_NAMESPACES)
