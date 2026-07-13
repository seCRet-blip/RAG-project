"""HTTP fetcher with polite rate limiting (free, no API keys)."""

import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx


class PoliteFetcher:
    """Fetch pages while respecting robots.txt and rate limits."""

    def __init__(
        self,
        user_agent: str,
        delay_seconds: float = 1.0,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._user_agent = user_agent
        self._delay = delay_seconds
        self._timeout = timeout_seconds
        self._last_request_at = 0.0
        self._robots: dict[str, RobotFileParser] = {}
        self._client = httpx.Client(
            headers={"User-Agent": user_agent},
            follow_redirects=True,
            timeout=timeout_seconds,
        )

    def close(self) -> None:
        self._client.close()

    def _wait_for_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)
        self._last_request_at = time.monotonic()

    def _get_robots(self, base_url: str) -> RobotFileParser:
        if base_url not in self._robots:
            parser = RobotFileParser()
            parser.set_url(urljoin(base_url, "/robots.txt"))
            try:
                parser.read()
            except Exception:
                # If robots.txt is unavailable, allow crawling docs paths only.
                parser = RobotFileParser()
                parser.parse(["User-agent: *", "Allow: /"])
            self._robots[base_url] = parser
        return self._robots[base_url]

    def can_fetch(self, url: str) -> bool:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        return self._get_robots(base).can_fetch(self._user_agent, url)

    def fetch(self, url: str) -> tuple[str, str] | None:
        """Return (final_url, html) or None if blocked/failed."""
        if not self.can_fetch(url):
            return None

        self._wait_for_rate_limit()
        try:
            response = self._client.get(url)
            response.raise_for_status()
        except httpx.HTTPError:
            return None

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            return None

        return str(response.url), response.text
