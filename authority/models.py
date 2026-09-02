"""Authority RAG models — chunk payload for sniper-bot domain."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Asset = Literal["SOL", "LTC", "BOTH"] | None

EXCLUDED_BY_DEFAULT = frozenset(
    {
        "handoff-secondary",
        "web-generic",
        "footgun",
    }
)

DEFAULT_NAMESPACES = frozenset(
    {
        "docs-ai",
        "compose-live",
        "config-train",
        "contracts",
        "code-critical",
        "state-live",
        "tests-parity",
    }
)


@dataclass
class AuthorityChunk:
    chunk_id: str
    text: str
    namespace: str
    source_path: str
    freshness: str
    title: str = ""
    section: str = ""
    asset: Asset = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "text": self.text,
            "namespace": self.namespace,
            "source_path": self.source_path,
            "freshness": self.freshness,
            "title": self.title,
            "section": self.section,
            "asset": self.asset,
            "source": self.namespace,
            "url": self.source_path,
        }
        payload.update(self.metadata)
        return payload

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
