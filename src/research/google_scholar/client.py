from __future__ import annotations

import asyncio
import re
from html import unescape
from types import TracebackType
from typing import Self

from curl_cffi.requests import AsyncSession
from curl_cffi.requests.exceptions import RequestException
from loguru import logger

from research.google_scholar.models import Publication, SearchResult
from research.proxy.models import Proxy
from research.proxy.pool import ProxyPool


class GoogleScholarClient:
    BASE_URL = "https://scholar.google.com/scholar"

    def __init__(
        self,
        *,
        timeout: float = 30.0,
        proxy: str | Proxy | None = None,
        proxy_pool: ProxyPool | None = None,
        max_retries: int = 3,
    ) -> None:
        self.timeout = timeout
        self.proxy = proxy
        self.proxy_pool = proxy_pool
        self.max_retries = max_retries
        self._session: AsyncSession | None = None

    async def _get_session(self) -> AsyncSession:
        if self._session is None:
            self._session = AsyncSession(impersonate="chrome", timeout=self.timeout)
        return self._session

    async def _resolve_current_proxy(self) -> str | None:
        if self.proxy_pool is not None:
            return await self.proxy_pool.resolve_proxy_url()
        if self.proxy is not None:
            if isinstance(self.proxy, Proxy):
                if self.proxy.protocol in ("http", "https", "socks4", "socks5", "socks5h"):
                    return self.proxy.url
                pool = ProxyPool()
                return await pool.resolve_proxy_url(self.proxy)
            return str(self.proxy)
        return None

    def _parse_html_results(self, html: str, query: str, limit: int) -> SearchResult:
        # 1. Total results count
        total_results: int | None = None
        total_m = re.search(
            r"""(?:About|Sekitar)\s+([\d.,]+)\s+results""",
            html,
            re.IGNORECASE,
        )
        if total_m:
            raw_num = total_m.group(1).replace(".", "").replace(",", "")
            try:
                total_results = int(raw_num)
            except ValueError:
                total_results = None

        # 2. Extract article blocks (<div class="gs_ri">...</div>)
        blocks = re.findall(
            r"""(<div class=["']gs_ri["']>.*?)(?=<div class=["']gs_ri["']|</div>\s*</div>\s*<div id=["']gs_res_ccl_bot["']|$)""",
            html,
            re.DOTALL | re.IGNORECASE,
        )

        publications: list[Publication] = []
        for block in blocks:
            # Title & Link
            t_match = re.search(
                r"""<h3[^>]*class=["']gs_rt["'][^>]*>(.*?)</h3>""",
                block,
                re.DOTALL | re.IGNORECASE,
            )
            url: str | None = None
            title = ""
            if t_match:
                t_raw = t_match.group(1)
                link_m = re.search(r"""<a[^>]*href=["']([^"']+)["']""", t_raw)
                if link_m:
                    url = unescape(link_m.group(1))
                # Strip HTML tags
                title = re.sub(r"""<[^>]+>""", "", t_raw)
                # Strip leading tags like [PDF], [HTML], [BOOK], [CITATION]
                title = re.sub(r"""^(?:\[[A-Za-z]+\]\s*)+""", "", title).strip()
                title = unescape(title)

            if not title:
                continue

            # Authors, Venue, Year
            authors: list[str] = []
            year: int | None = None
            venue: str | None = None
            a_match = re.search(
                r"""<div class=["']gs_a["']>(.*?)</div>""",
                block,
                re.DOTALL | re.IGNORECASE,
            )
            if a_match:
                meta_str = re.sub(r"""<[^>]+>""", "", a_match.group(1))
                parts = [p.strip() for p in re.split(r"""\s+[-–—]\s+""", meta_str) if p.strip()]
                if parts:
                    authors = [
                        unescape(a.rstrip("….").strip())
                        for a in parts[0].split(",")
                        if a.strip()
                    ]
                if len(parts) > 1:
                    venue_part = parts[1]
                    y_m = re.search(r"""\b(19\d\d|20\d\d)\b""", venue_part)
                    if y_m:
                        year = int(y_m.group(1))
                    cleaned_v = re.sub(
                        r""",?\s*\b(19\d\d|20\d\d)\b""",
                        "",
                        venue_part,
                    ).strip().rstrip(",….").strip()
                    if cleaned_v:
                        venue = unescape(cleaned_v)

            # Abstract snippet
            snippet: str | None = None
            s_match = re.search(
                r"""<div class=["']gs_rs["']>(.*?)</div>""",
                block,
                re.DOTALL | re.IGNORECASE,
            )
            if s_match:
                snip = re.sub(r"""<[^>]+>""", "", s_match.group(1))
                snippet = unescape(re.sub(r"""\s+""", " ", snip)).strip()

            # Citation count
            citation_count: int | None = None
            c_match = re.search(r"""(?:Cited by|Dirujuk)\s+(\d+)""", block, re.IGNORECASE)
            if c_match:
                citation_count = int(c_match.group(1))

            publications.append(
                Publication(
                    title=title,
                    url=url,
                    authors=authors,
                    year=year,
                    venue=venue,
                    citation_count=citation_count,
                    abstract=snippet,
                )
            )

        return SearchResult(
            query=query,
            total_results=total_results,
            publications=publications[:limit],
        )

    async def search(self, query: str, *, limit: int = 10, page: int = 1) -> SearchResult:
        """Search Google Scholar for publications matching query."""
        start = max(0, (page - 1) * 10)
        params = {
            "q": query,
            "hl": "en",
            "start": str(start),
        }
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        attempts = 0
        last_error: Exception | None = None

        while attempts < self.max_retries:
            attempts += 1
            proxy_url = await self._resolve_current_proxy()
            session = await self._get_session()

            try:
                logger.debug(
                    "Google Scholar search attempt {}/{} for '{}' (proxy={})",
                    attempts,
                    self.max_retries,
                    query,
                    proxy_url,
                )
                resp = await session.get(
                    self.BASE_URL,
                    params=params,
                    headers=headers,
                    proxy=proxy_url,
                )

                if resp.status_code == 200:
                    # Detect soft block / CAPTCHA page
                    if "gs_captcha" in resp.text or "/sorry/" in str(resp.url):
                        logger.warning("Google Scholar CAPTCHA encountered on attempt {}", attempts)
                        if self.proxy_pool is not None and attempts < self.max_retries:
                            continue
                        raise RuntimeError("Google Scholar CAPTCHA / rate-limit encountered.")

                    return self._parse_html_results(resp.text, query, limit)

                if resp.status_code in (429, 403):
                    logger.warning("Google Scholar HTTP {} on attempt {}", resp.status_code, attempts)
                    if self.proxy_pool is not None and attempts < self.max_retries:
                        continue
                    raise RuntimeError(f"Google Scholar HTTP {resp.status_code} rate limit.")

                resp.raise_for_status()

            except (TimeoutError, RequestException, RuntimeError, OSError) as exc:
                last_error = exc
                logger.warning(
                    "Google Scholar search error on attempt {}: {}",
                    attempts,
                    exc,
                )
                if attempts < self.max_retries:
                    await asyncio.sleep(1.0)
                else:
                    break

        raise RuntimeError(
            f"Google Scholar search failed after {attempts} attempts: {last_error}"
        ) from last_error

    def search_sync(self, query: str, *, limit: int = 10, page: int = 1) -> SearchResult:
        """Synchronous wrapper for search."""
        return asyncio.run(self.search(query, limit=limit, page=page))

    async def publication(self, url: str) -> Publication:
        """Fetch details for a single publication directly from its landing page."""
        session = await self._get_session()
        proxy_url = await self._resolve_current_proxy()

        resp = await session.get(url, proxy=proxy_url)
        resp.raise_for_status()
        html = resp.text

        # Extract title
        title = ""
        t_meta = re.search(
            r"""<meta\s+[^>]*?(?:name|property)=['"](?:citation_title|dc\.title)['"][^>]*?content=['"]([^'"]+)['"]""",
            html,
            re.IGNORECASE,
        )
        if t_meta:
            title = unescape(t_meta.group(1).strip())
        else:
            title_m = re.search(r"""<title>(.*?)</title>""", html, re.IGNORECASE | re.DOTALL)
            if title_m:
                title = re.sub(r"""\s+""", " ", unescape(title_m.group(1))).strip()

        # Extract authors
        authors = re.findall(
            r"""<meta\s+[^>]*?(?:name|property)=['"](?:citation_author|dc\.creator)['"][^>]*?content=['"]([^'"]+)['"]""",
            html,
            re.IGNORECASE,
        )
        authors = [unescape(a.strip()) for a in authors if a.strip()]

        # Extract year
        year: int | None = None
        date_meta = re.search(
            r"""<meta\s+[^>]*?(?:name|property)=['"](?:citation_publication_date|citation_date|dc\.date\.issued)['"][^>]*?content=['"]([^'"]+)['"]""",
            html,
            re.IGNORECASE,
        )
        if date_meta:
            y_m = re.search(r"""\b(19\d\d|20\d\d)\b""", date_meta.group(1))
            if y_m:
                year = int(y_m.group(1))

        # Extract venue
        venue: str | None = None
        v_meta = re.search(
            r"""<meta\s+[^>]*?(?:name|property)=['"](?:citation_journal_title|dc\.source)['"][^>]*?content=['"]([^'"]+)['"]""",
            html,
            re.IGNORECASE,
        )
        if v_meta:
            venue = unescape(v_meta.group(1).strip())

        # Extract abstract
        abstract: str | None = None
        abs_meta = re.search(
            r"""<meta\s+[^>]*?(?:name|property)=['"](?:citation_abstract|dc\.description|description)['"][^>]*?content=['"]([^'"]+)['"]""",
            html,
            re.IGNORECASE,
        )
        if abs_meta:
            abstract = unescape(abs_meta.group(1).strip())

        return Publication(
            title=title or "Untitled",
            url=url,
            authors=authors,
            year=year,
            venue=venue,
            abstract=abstract,
        )

    def publication_sync(self, url: str) -> Publication:
        """Synchronous wrapper for publication."""
        return asyncio.run(self.publication(url))

    async def close(self) -> None:
        """Close HTTP session and background proxy bridges."""
        if self._session is not None:
            await self._session.close()
            self._session = None
        if self.proxy_pool is not None:
            await self.proxy_pool.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()
