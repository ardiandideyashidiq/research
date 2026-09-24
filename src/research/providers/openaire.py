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


class OpenAIREProvider(BaseProvider):
    """Provider for OpenAIRE Graph scientific publications."""

    name: str = "openaire"
    BASE_URL: str = "https://api.openaire.eu/search/publications"

    def __init__(self, *, timeout: float = 12.0) -> None:
        self.timeout = timeout
        self._async_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            headers = {"User-Agent": "research-openaire/0.1 (mailto:rdndds@gmail.com)"}
            self._async_client = httpx.AsyncClient(headers=headers, timeout=self.timeout, follow_redirects=True)
        return self._async_client

    async def close(self) -> None:
        if self._async_client is not None and not self._async_client.is_closed:
            await self._async_client.aclose()
            self._async_client = None

    def _parse_item(self, item: dict[str, Any]) -> PublicationRecord | None:
        metadata = item.get("metadata", {}).get("oaf:entity", {}).get("oaf:result", {})
        if not metadata:
            return None

        # Title
        raw_title = metadata.get("title", {})
        title_str = ""
        if isinstance(raw_title, list) and raw_title:
            title_str = raw_title[0].get("$", "")
        elif isinstance(raw_title, dict):
            title_str = raw_title.get("$", "")
        title = normalize_title(title_str)
        if not title:
            return None

        # Authors
        creator_data = metadata.get("creator", [])
        if isinstance(creator_data, dict):
            creator_data = [creator_data]
        raw_authors = [c.get("$", "") for c in creator_data if c.get("$")]
        authors = normalize_authors(raw_authors)

        # Date / Year
        date_data = metadata.get("dateofacceptance", {})
        pub_date = date_data.get("$") if isinstance(date_data, dict) else str(date_data)
        year: int | None = None
        if pub_date:
            m = re.match(r"^(\d{4})", pub_date)
            if m:
                year = int(m.group(1))

        # Journal / Source
        journal_data = metadata.get("journal", {})
        journal = journal_data.get("$") if isinstance(journal_data, dict) else None

        # DOI & PID
        doi = None
        pid_data = metadata.get("pid", [])
        if isinstance(pid_data, dict):
            pid_data = [pid_data]
        for p in pid_data:
            classid = p.get("@classid", "").lower()
            if classid == "doi":
                doi = normalize_doi(p.get("$"))
                break

        # Abstract / Description
        desc_data = metadata.get("description", {})
        desc_str = desc_data.get("$") if isinstance(desc_data, dict) else (desc_data[0].get("$") if isinstance(desc_data, list) and desc_data else None)
        abstract = normalize_abstract(desc_str)

        # Fulltext / OA links
        pdf_url = None
        url = f"https://doi.org/{doi}" if doi else None

        first_author = authors[0].split()[-1] if authors else "Unknown"
        clean_word = re.sub(r"\W+", "", title.split()[0] if title else "Paper")
        header = item.get("header", {})
        dri_obj = header.get("dri:objIdentifier", {})
        short_id = (dri_obj.get("$", "") if isinstance(dri_obj, dict) else str(dri_obj))[-5:] or "openaire"
        cite_key = f"{first_author}{year or 2026}{clean_word}_{short_id}"

        return PublicationRecord(
            cite_key=cite_key,
            entry_type="article",
            title=title,
            authors=authors,
            journal=journal,
            year=year,
            doi=doi,
            url=url,
            abstract=abstract,
            sources=["provider:openaire"],
            pdf_url=pdf_url,
            is_ojs=False,
            download_status="pending",
            full_metadata={
                "openaire": {
                    "header": header,
                },
                "normalized_at": datetime.now(UTC).isoformat(),
            },
        )

    async def search(self, query: str, *, limit: int = 10, **kwargs: Any) -> list[PublicationRecord]:
        """Search OpenAIRE Graph publications by title or keywords."""
        client = await self._get_client()
        params = {"title": query, "format": "json", "size": min(limit, 50)}

        try:
            resp = await client.get(self.BASE_URL, params=params)
            if resp.status_code == 200:
                data = resp.json()
                raw_results = data.get("response", {}).get("results", {}).get("result", [])
                records = []
                for item in raw_results:
                    rec = self._parse_item(item)
                    if rec:
                        records.append(rec)
                return records
            logger.warning(f"OpenAIRE HTTP {resp.status_code} for query '{query}'")
        except httpx.HTTPError as e:
            logger.warning(f"OpenAIRE search error for '{query}': {e}")

        return []

    async def get_by_doi(self, doi: str, **kwargs: Any) -> PublicationRecord | None:
        """Fetch OpenAIRE publication by DOI."""
        norm = normalize_doi(doi)
        if not norm:
            return None
        client = await self._get_client()
        params = {"doi": norm, "format": "json", "size": 1}
        try:
            resp = await client.get(self.BASE_URL, params=params)
            if resp.status_code == 200:
                data = resp.json()
                raw_results = data.get("response", {}).get("results", {}).get("result", [])
                if raw_results:
                    return self._parse_item(raw_results[0])
        except httpx.HTTPError as e:
            logger.warning(f"OpenAIRE DOI lookup error for {norm}: {e}")
        return None
