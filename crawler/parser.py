"""Extract links and main content from documentation HTML."""

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag


def is_valid_doc_url(url: str, base_url: str, allowed_prefixes: list[str]) -> bool:
    """Keep only same-site documentation URLs."""
    parsed = urlparse(url)
    base = urlparse(base_url)

    if parsed.netloc and parsed.netloc != base.netloc:
        return False

    path = parsed.path or "/"
    if not any(path.startswith(prefix) for prefix in allowed_prefixes):
        return False

    # Skip assets and non-page resources
    if re.search(r"\.(png|jpg|jpeg|gif|svg|pdf|zip|css|js)$", path, re.I):
        return False

    return True


def extract_links(html: str, page_url: str, base_url: str, allowed_prefixes: list[str]) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links: list[str] = []

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href.startswith("#") or href.startswith("mailto:"):
            continue
        absolute = urljoin(page_url, href)
        absolute = absolute.split("#")[0].rstrip("/") + "/"
        if is_valid_doc_url(absolute, base_url, allowed_prefixes):
            links.append(absolute)

    return list(dict.fromkeys(links))


def extract_page_content(
    html: str,
    page_url: str,
    selectors: list[str],
) -> dict[str, str | list[str]]:
    """Pull title, headings, and body text from a docs page."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    content_root: Tag | None = None
    for selector in selectors:
        content_root = soup.select_one(selector)
        if content_root:
            break
    if content_root is None:
        content_root = soup.body or soup

    headings: list[str] = []
    for level in ("h1", "h2", "h3"):
        for heading in content_root.find_all(level):
            text = heading.get_text(" ", strip=True)
            if text:
                headings.append(text)

    paragraphs: list[str] = []
    for element in content_root.find_all(["p", "li", "pre", "code", "td"]):
        text = element.get_text(" ", strip=True)
        if text and len(text) > 20:
            paragraphs.append(text)

    body = "\n\n".join(paragraphs)

    return {
        "url": page_url,
        "title": title,
        "headings": headings,
        "body": body,
    }
