from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

import httpx
from loguru import logger

from research.db.models import PublicationRecord
from research.normalizer.crossref import normalize_doi
from research.normalizer.normalizer import (
    normalize_abstract,
    normalize_authors,
    normalize_title,
)
from research.providers.base import BaseProvider


class DOAJProvider(BaseProvider):
    """Provider for Directory of Open Access Journals (DOAJ) articles."""

    name: str = "doaj"
    BASE_URL: str = "https://doaj.org/api/search/articles"

    def __init__(self, *, timeout: float = 12.0) -> None:
        self.timeout = timeout
        self._async_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            headers = {"User-Agent": "research-doaj/0.1 (mailto:rdndds@gmail.com)"}
            self._async_client = httpx.AsyncClient(headers=headers, timeout=self.timeout, follow_redirects=True)
        return self._async_client

    async def close(self) -> None:
        if self._async_client is not None and not self._async_client.is_closed:
            await self._async_client.aclose()
            self._async_client = None

    def _parse_item(self, item: dict[str, Any]) -> PublicationRecord | None:
        bib = item.get("bibjson", {})
        title = normalize_title(bib.get("title", ""))
        if not title:
            return None

        authors_list = [a.get("name", "") for a in bib.get("author", []) if a.get("name")]
        authors = normalize_authors(authors_list)

        journal_data = bib.get("journal") or {}
        journal = journal_data.get("title")

        year: int | None = None
        if bib.get("year"):
            try:
                year = int(bib["year"])
            except ValueError:
                year = None

        # Identifiers (DOI)
        doi = None
        for ident in bib.get("identifier", []):
            if ident.get("type", "").lower() == "doi":
                doi = normalize_doi(ident.get("id"))
                break

        abstract = normalize_abstract(bib.get("abstract"))

        # Links (Full text / PDF)
        pdf_url = None
        landing_url = None
        for link in bib.get("link", []):
            content_type = link.get("content_type", "").lower()
            url_str = link.get("url", "")
            if "pdf" in content_type or url_str.endswith(".pdf") or "/article/download/" in url_str:
                pdf_url = url_str
            elif not landing_url:
                landing_url = url_str

        # OJS detection
        target_url = pdf_url or landing_url
        is_ojs = None
        if target_url and any(p in target_url for p in ["/article/view/", "/article/download/", "index.php"]):
            is_ojs = True

        first_author = authors[0].split()[-1] if authors else "Unknown"
        clean_word = re.sub(r"\W+", "", title.split()[0] if title else "Paper")
        short_id = item.get("id", "doaj")[-5:]
        cite_key = f"{first_author}{year or 2026}{clean_word}_{short_id}"

        return PublicationRecord(
            cite_key=cite_key,
            entry_type="article",
            title=title,
            authors=authors,
            journal=journal,
            year=year,
            doi=doi,
            url=landing_url or (f"https://doi.org/{doi}" if doi else None),
            abstract=abstract,
            sources=["provider:doaj"],
            pdf_url=pdf_url,
            is_ojs=is_ojs,
            download_status="pending",
            full_metadata={
                "doaj": {
                    "id": item.get("id"),
                    "created_date": item.get("created_date"),
                    "journal": journal_data,
                },
                "normalized_at": datetime.now(UTC).isoformat(),
            },
        )

    async def search(self, query: str, *, limit: int = 10, **kwargs: Any) -> list[PublicationRecord]:
        """Search DOAJ articles by query string."""
        client = await self._get_client()
        url = f"{self.BASE_URL}/{query}"
        params = {"pageSize": min(limit, 50)}

        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in data.get("results", []):
                    rec = self._parse_item(item)
                    if rec:
                        results.append(rec)
                return results
            logger.warning(f"DOAJ HTTP {resp.status_code} for query '{query}'")
        except httpx.HTTPError as e:
            logger.warning(f"DOAJ search error for '{query}': {e}")

        return []

    async def get_by_doi(self, doi: str, **kwargs: Any) -> PublicationRecord | None:
        """Search DOAJ for an article by DOI."""
        norm = normalize_doi(doi)
        if not norm:
            return None
        records = await self.search(f'doi:"{norm}"', limit=1)
        return records[0] if records else None
