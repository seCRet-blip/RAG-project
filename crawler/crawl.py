"""BFS crawler — discovers docs by following links from seed pages."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from crawler.config import CrawlSettings, DocSource
from crawler.fetcher import PoliteFetcher
from crawler.parser import extract_links, extract_page_content, is_valid_doc_url


def url_to_filename(url: str) -> str:
    """Turn a URL into a safe filesystem name."""
    slug = re.sub(r"^https?://", "", url)
    slug = slug.strip("/").replace("/", "__")
    slug = re.sub(r"[^a-zA-Z0-9._-]", "_", slug)
    return slug or "index"


def crawl_source(source: DocSource, settings: CrawlSettings) -> dict:
    """
    Crawl one documentation source.

    Stage output: HTML files in data/raw/html/{source}/
    Plus a manifest describing every page fetched.
    """
    output_dir = Path(settings.raw_dir) / source.name
    output_dir.mkdir(parents=True, exist_ok=True)

    fetcher = PoliteFetcher(
        user_agent=settings.user_agent,
        delay_seconds=source.request_delay_seconds,
        timeout_seconds=settings.timeout_seconds,
    )

    visited: set[str] = set()
    queue: list[str] = list(source.seed_urls)
    pages: list[dict] = []

    try:
        while queue and len(visited) < source.max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            if not is_valid_doc_url(url, source.base_url, source.url_prefixes):
                continue

            result = fetcher.fetch(url)
            if result is None:
                visited.add(url)
                continue

            final_url, html = result
            visited.add(final_url)

            filename = url_to_filename(final_url)
            html_path = output_dir / f"{filename}.html"
            html_path.write_text(html, encoding="utf-8")

            extracted = extract_page_content(html, final_url, source.content_selectors)
            pages.append(
                {
                    "url": final_url,
                    "title": extracted["title"],
                    "file": str(html_path.relative_to(Path(settings.raw_dir).parent)),
                    "char_count": len(extracted["body"]),
                    "heading_count": len(extracted["headings"]),
                }
            )

            for link in extract_links(html, final_url, source.base_url, source.url_prefixes):
                if link not in visited and link not in queue:
                    queue.append(link)
    finally:
        fetcher.close()

    manifest = {
        "source": source.name,
        "base_url": source.base_url,
        "crawled_at": datetime.now(UTC).isoformat(),
        "page_count": len(pages),
        "max_pages": source.max_pages,
        "pages": pages,
    }

    manifest_dir = Path(settings.manifest_path).parent
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_file = manifest_dir / f"{source.name}_manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return manifest
