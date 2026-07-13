"""Stage 1: Extract structured content from raw HTML files."""

import json
from pathlib import Path

from bs4 import BeautifulSoup

from crawler.config import SOURCES
from processing.models import ExtractedDocument


def extract_from_html(
    html: str,
    source: str,
    url: str,
    raw_file: str,
    selectors: list[str],
) -> ExtractedDocument:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    content_root = None
    for selector in selectors:
        content_root = soup.select_one(selector)
        if content_root:
            break
    if content_root is None:
        content_root = soup.body or soup

    headings = [
        h.get_text(" ", strip=True)
        for h in content_root.find_all(["h1", "h2", "h3"])
        if h.get_text(" ", strip=True)
    ]

    blocks: list[str] = []
    for element in content_root.find_all(["h1", "h2", "h3", "p", "li", "pre"]):
        text = element.get_text(" ", strip=True)
        if not text:
            continue
        if element.name in {"h1", "h2", "h3"}:
            level = element.name[1]
            blocks.append(f"{'#' * int(level)} {text}")
        else:
            blocks.append(text)

    body = "\n\n".join(blocks)

    return ExtractedDocument(
        source=source,
        url=url,
        title=title,
        headings=headings,
        body=body,
        raw_file=raw_file,
    )


def extract_source(source_name: str, raw_dir: Path, output_dir: Path) -> list[ExtractedDocument]:
    source = SOURCES[source_name]
    manifest_path = raw_dir.parent / f"{source_name}_manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Missing manifest: {manifest_path}. Run the crawler first: "
            f"python -m scripts.crawl_docs --source {source_name}"
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)

    documents: list[ExtractedDocument] = []
    for page in manifest["pages"]:
        html_path = raw_dir.parent / page["file"]
        html = html_path.read_text(encoding="utf-8")
        doc = extract_from_html(
            html=html,
            source=source_name,
            url=page["url"],
            raw_file=str(html_path),
            selectors=source.content_selectors,
        )
        documents.append(doc)

        out_file = output_dir / f"{html_path.stem}.json"
        out_file.write_text(json.dumps(doc.to_dict(), indent=2), encoding="utf-8")

    return documents
