"""Crawler configuration — all free, no paid APIs."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DocSource:
    """A documentation site to crawl."""

    name: str
    base_url: str
    seed_urls: list[str]
    url_prefixes: list[str]
    content_selectors: list[str]
    max_pages: int = 100
    request_delay_seconds: float = 1.0


# Curated seeds include pages that answer your example questions:
# - ENTRYPOINT vs CMD → Docker Dockerfile reference
# - Docker networking → engine/network
# - Multi-stage builds → build/building/multi-stage
KUBERNETES = DocSource(
    name="kubernetes",
    base_url="https://kubernetes.io",
    seed_urls=[
        "https://kubernetes.io/docs/home/",
        "https://kubernetes.io/docs/concepts/overview/",
        "https://kubernetes.io/docs/concepts/workloads/",
        "https://kubernetes.io/docs/concepts/services-networking/",
        "https://kubernetes.io/docs/tasks/",
    ],
    url_prefixes=["/docs/"],
    content_selectors=["main", "#main-content", ".docs-content", "article"],
    max_pages=100,
)

DOCKER = DocSource(
    name="docker",
    base_url="https://docs.docker.com",
    seed_urls=[
        "https://docs.docker.com/",
        "https://docs.docker.com/reference/dockerfile/",
        "https://docs.docker.com/engine/network/",
        "https://docs.docker.com/build/building/multi-stage/",
        "https://docs.docker.com/get-started/",
    ],
    url_prefixes=[
        "/reference/",
        "/engine/",
        "/build/",
        "/get-started/",
        "/guides/",
        "/manuals/",
        "/desktop/",
    ],
    content_selectors=["article", "main", ".docs-content", "#docsContent"],
    max_pages=100,
)

SOURCES: dict[str, DocSource] = {
    "kubernetes": KUBERNETES,
    "docker": DOCKER,
}


@dataclass
class CrawlSettings:
    """Runtime settings loaded from env or defaults."""

    raw_dir: str = "data/raw/html"
    manifest_path: str = "data/raw/manifest.json"
    user_agent: str = "RAG-Learning-Crawler/0.1 (+local; respectful; no-cost)"
    timeout_seconds: float = 30.0
    sources: dict[str, DocSource] = field(default_factory=lambda: SOURCES.copy())
