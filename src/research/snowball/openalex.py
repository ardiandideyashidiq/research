from __future__ import annotations

import re
from datetime import UTC, datetime
from types import TracebackType
from typing import Any, Self

import httpx
from loguru import logger

from research.db.models import PublicationRecord
from research.normalizer.crossref import normalize_doi
from research.normalizer.normalizer import (
    normalize_abstract,
    normalize_authors,
    normalize_title,
)


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    """Reconstruct plain-text abstract from OpenAlex inverted index."""
    if not inverted_index:
        return None
    word_positions: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort(key=lambda x: x[0])
    text = " ".join(word for _, word in word_positions)
    return normalize_abstract(text)


def generate_cite_key(authors: list[str], year: int | None, title: str, openalex_id: str) -> str:
    """Generate a clean, readable, unique BibTeX-style cite_key."""
    first_author = "Unknown"
    if authors:
        last_name_match = re.search(r"(\w+)$", authors[0].strip())
        if last_name_match:
            first_author = last_name_match.group(1).capitalize()

    yr = str(year) if year else "2026"

    words = re.findall(r"[A-Za-z]+", title)
    title_word = words[0].capitalize() if words else "Work"

    # Short suffix from OpenAlex ID (e.g. W4416998586 -> 98586)
    short_id = openalex_id.split("/")[-1].replace("W", "")[-5:]
    return f"{first_author}{yr}{title_word}_{short_id}"


HARDCODED_EMAIL = "rdndds@gmail.com"


class OpenAlexClient:
    """HTTPX-based client for OpenAlex literature graph and citation network."""

    def __init__(self, *, email: str = HARDCODED_EMAIL, timeout: float = 15.0) -> None:
        self.email = email
        self.timeout = timeout
        self.base_url = "https://api.openalex.org"
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {"User-Agent": f"research-snowball/0.1 (mailto:{self.email})"}
            self._client = httpx.AsyncClient(headers=headers, timeout=self.timeout, follow_redirects=True)
        return self._client

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> Self:
        await self.get_client()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def find_work(
        self,
        *,
        doi: str | None = None,
        title: str | None = None,
    ) -> dict[str, Any] | None:
        """Find an OpenAlex work by DOI or title search."""
        client = await self.get_client()

        # 1. Direct lookup by DOI
        if doi:
            norm_doi = normalize_doi(doi)
            if norm_doi:
                try:
                    resp = await client.get(f"{self.base_url}/works/doi:{norm_doi}")
                    if resp.status_code == 200:
                        return resp.json()
                except httpx.HTTPError as e:
                    logger.debug(f"OpenAlex DOI lookup failed for {norm_doi}: {e}")

        # 2. Search by title
        if title:
            clean_t = normalize_title(title)
            if len(clean_t) > 10:
                try:
                    resp = await client.get(f"{self.base_url}/works", params={"search": clean_t, "per_page": 1})
                    if resp.status_code == 200:
                        results = resp.json().get("results", [])
                        if results:
                            return results[0]
                except httpx.HTTPError as e:
                    logger.debug(f"OpenAlex title search failed: {e}")

        return None

    async def fetch_citing_works(
        self,
        openalex_id: str,
        *,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        """Forward snowballing: fetch papers that cite the specified work."""
        client = await self.get_client()
        work_id = openalex_id.split("/")[-1]
        try:
            resp = await client.get(
                f"{self.base_url}/works",
                params={"filter": f"cites:{work_id}", "per_page": min(limit, 100), "sort": "-publication_date"},
            )
            if resp.status_code == 200:
                return resp.json().get("results", [])
        except httpx.HTTPError as e:
            logger.warning(f"Error fetching citing works for {openalex_id}: {e}")
        return []

    async def fetch_referenced_works(
        self,
        referenced_ids: list[str],
        *,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        """Backward snowballing: batch-fetch works referenced in the bibliography."""
        if not referenced_ids:
            return []

        client = await self.get_client()
        clean_ids = [ref.split("/")[-1] for ref in referenced_ids[:limit]]
        filter_str = "openalex:" + "|".join(clean_ids)

        try:
            resp = await client.get(
                f"{self.base_url}/works",
                params={"filter": filter_str, "per_page": len(clean_ids)},
            )
            if resp.status_code == 200:
                return resp.json().get("results", [])
        except httpx.HTTPError as e:
            logger.warning(f"Error batch-fetching referenced works: {e}")
        return []

    def work_to_record(
        self,
        work: dict[str, Any],
        *,
        seed_cite_key: str,
        relation: str,
    ) -> PublicationRecord:
        """Transform an OpenAlex work entity into an enriched PublicationRecord."""
        raw_authors = [
            a["author"]["display_name"]
            for a in work.get("authorships", [])
            if a.get("author", {}).get("display_name")
        ]
        authors = normalize_authors(raw_authors)
        title = normalize_title(work.get("title", ""))
        year = work.get("publication_year")

        # Journal / Venue
        primary_loc = work.get("primary_location") or {}
        source = primary_loc.get("source") or {}
        journal = source.get("display_name")

        # DOI & URL
        doi = normalize_doi(work.get("doi"))
        url = work.get("doi") or primary_loc.get("landing_page_url") or work.get("id")

        # Direct PDF link from OpenAlex Open-Access metadata
        best_oa = work.get("best_oa_location") or {}
        pdf_url = best_oa.get("pdf_url") or primary_loc.get("pdf_url")

        # Abstract
        abstract = reconstruct_abstract(work.get("abstract_inverted_index"))

        # OJS detection from URL structure
        is_ojs = None
        if url and any(m in url for m in ["/article/view/", "/article/download/", "index.php"]):
            is_ojs = True

        cite_key = generate_cite_key(authors, year, title, work.get("id", ""))

        now_str = datetime.now(UTC).isoformat()
        full_metadata = {
            "openalex": {
                "id": work.get("id"),
                "cited_by_count": work.get("cited_by_count"),
                "referenced_works_count": len(work.get("referenced_works", [])),
                "is_oa": work.get("open_access", {}).get("is_oa"),
                "oa_status": work.get("open_access", {}).get("oa_status"),
                "concepts": [c.get("display_name") for c in work.get("concepts", [])[:5]],
            },
            "snowball": {
                "seed_cite_key": seed_cite_key,
                "relation": relation,
                "discovered_at": now_str,
            },
            "normalized_at": now_str,
        }

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
            sources=[f"snowball:{relation}:{seed_cite_key}"],
            pdf_url=pdf_url,
            is_ojs=is_ojs,
            download_status="pending",
            full_metadata=full_metadata,
        )
