from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

import httpx
from loguru import logger

from research.db.models import PublicationRecord
from research.normalizer.crossref import HARDCODED_EMAIL, normalize_doi
from research.normalizer.normalizer import (
    normalize_abstract,
    normalize_authors,
    normalize_title,
)
from research.providers.base import BaseProvider


class CrossrefProvider(BaseProvider):
    """Provider for Crossref REST API search and work retrieval."""

    name: str = "crossref"
    BASE_URL: str = "https://api.crossref.org/works"

    def __init__(self, *, email: str = HARDCODED_EMAIL, timeout: float = 12.0) -> None:
        self.email = email
        self.timeout = timeout
        self._async_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            headers = {"User-Agent": f"research-crossref/0.1 (mailto:{self.email})"}
            self._async_client = httpx.AsyncClient(headers=headers, timeout=self.timeout, follow_redirects=True)
        return self._async_client

    async def close(self) -> None:
        if self._async_client is not None and not self._async_client.is_closed:
            await self._async_client.aclose()
            self._async_client = None

    def _parse_message(self, msg: dict[str, Any]) -> PublicationRecord | None:
        raw_titles = msg.get("title", [])
        title = normalize_title(raw_titles[0] if raw_titles else "")
        if not title:
            return None

        # Authors
        raw_authors = []
        for a in msg.get("author", []):
            given = a.get("given", "").strip()
            family = a.get("family", "").strip()
            name = f"{given} {family}".strip() if (given or family) else a.get("name", "")
            if name:
                raw_authors.append(name)
        authors = normalize_authors(raw_authors)

        # Journal / Container
        containers = msg.get("container-title", [])
        journal = containers[0] if containers else None

        # Year
        year: int | None = None
        date_parts = msg.get("published", {}).get("date-parts", [[]])[0]
        if date_parts:
            year = date_parts[0]

        doi = normalize_doi(msg.get("DOI"))
        url = msg.get("URL") or (f"https://doi.org/{doi}" if doi else None)
        abstract = normalize_abstract(msg.get("abstract"))

        first_author = authors[0].split()[-1] if authors else "Unknown"
        clean_word = re.sub(r"\W+", "", title.split()[0] if title else "Paper")
        short_id = (doi or "crossref")[-5:].replace("/", "_")
        cite_key = f"{first_author}{year or 2026}{clean_word}_{short_id}"

        return PublicationRecord(
            cite_key=cite_key,
            entry_type=msg.get("type", "article"),
            title=title,
            authors=authors,
            journal=journal,
            year=year,
            volume=msg.get("volume"),
            number=msg.get("issue"),
            pages=msg.get("page"),
            doi=doi,
            url=url,
            abstract=abstract,
            sources=["provider:crossref"],
            is_ojs=False,
            download_status="pending",
            full_metadata={
                "crossref": msg,
                "normalized_at": datetime.now(UTC).isoformat(),
            },
        )

    async def search(self, query: str, *, limit: int = 10, **kwargs: Any) -> list[PublicationRecord]:
        """Search Crossref works by free-text query."""
        client = await self._get_client()
        params = {"query": query, "rows": min(limit, 50)}

        try:
            resp = await client.get(self.BASE_URL, params=params)
            if resp.status_code == 200:
                items = resp.json().get("message", {}).get("items", [])
                records = []
                for item in items:
                    rec = self._parse_message(item)
                    if rec:
                        records.append(rec)
                return records
            logger.warning(f"Crossref HTTP {resp.status_code} for query '{query}'")
        except httpx.HTTPError as e:
            logger.warning(f"Crossref search error for '{query}': {e}")

        return []

    async def get_by_doi(self, doi: str, **kwargs: Any) -> PublicationRecord | None:
        """Fetch canonical Crossref record by DOI."""
        norm = normalize_doi(doi)
        if not norm:
            return None

        client = await self._get_client()
        url = f"{self.BASE_URL}/{norm}"

        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                msg = resp.json().get("message", {})
                return self._parse_message(msg)
            logger.debug(f"Crossref HTTP {resp.status_code} for {norm}")
        except httpx.HTTPError as e:
            logger.debug(f"Crossref error for {norm}: {e}")

        return None
