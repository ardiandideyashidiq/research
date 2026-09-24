from __future__ import annotations

from typing import Any

import httpx
from loguru import logger

from research.db.models import PublicationRecord
from research.normalizer.crossref import HARDCODED_EMAIL, normalize_doi
from research.providers.base import BaseProvider
from research.snowball.openalex import OpenAlexClient


class OpenAlexProvider(BaseProvider):
    """Provider for OpenAlex catalog search and work retrieval."""

    name: str = "openalex"

    def __init__(self, *, email: str = HARDCODED_EMAIL, timeout: float = 15.0) -> None:
        self.email = email
        self.timeout = timeout
        self.client = OpenAlexClient(email=self.email, timeout=self.timeout)

    async def close(self) -> None:
        await self.client.close()

    async def search(self, query: str, *, limit: int = 10, **kwargs: Any) -> list[PublicationRecord]:
        """Search OpenAlex works by query string."""
        http = await self.client.get_client()
        params = {"search": query, "per_page": min(limit, 50)}

        try:
            resp = await http.get(f"{self.client.base_url}/works", params=params)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                records = []
                for item in results:
                    rec = self.client.work_to_record(item, seed_cite_key="search", relation="direct")
                    rec.sources = ["provider:openalex"]
                    records.append(rec)
                return records
            logger.warning(f"OpenAlex search HTTP {resp.status_code} for '{query}'")
        except httpx.HTTPError as e:
            logger.warning(f"OpenAlex search error for '{query}': {e}")

        return []

    async def get_by_doi(self, doi: str, **kwargs: Any) -> PublicationRecord | None:
        """Fetch OpenAlex work by DOI."""
        norm = normalize_doi(doi)
        if not norm:
            return None

        work = await self.client.find_work(doi=norm)
        if work:
            rec = self.client.work_to_record(work, seed_cite_key="doi_lookup", relation="direct")
            rec.sources = ["provider:openalex"]
            return rec

        return None
