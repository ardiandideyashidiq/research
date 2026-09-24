from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any

from curl_cffi.requests import AsyncSession, Session
from loguru import logger

from research.db.models import PublicationRecord
from research.normalizer.crossref import normalize_doi
from research.normalizer.normalizer import normalize_authors, normalize_title
from research.providers.base import BaseProvider


class ArxivProvider(BaseProvider):
    """Provider for searching arXiv preprints with browser TLS impersonation via curl-cffi."""

    name: str = "arxiv"
    BASE_URL: str = "https://export.arxiv.org/api/query"

    def __init__(self, *, timeout: float = 15.0) -> None:
        self.timeout = timeout
        self._async_session: AsyncSession | None = None
        self._sync_session: Session | None = None

    def _get_async_session(self) -> AsyncSession:
        if self._async_session is None:
            self._async_session = AsyncSession(impersonate="chrome", timeout=self.timeout)
        return self._async_session

    def _get_sync_session(self) -> Session:
        if self._sync_session is None:
            self._sync_session = Session(impersonate="chrome", timeout=self.timeout)
        return self._sync_session

    async def close(self) -> None:
        if self._async_session is not None:
            await self._async_session.close()
            self._async_session = None
        if self._sync_session is not None:
            self._sync_session.close()
            self._sync_session = None

    def _parse_atom_xml(self, xml_text: str) -> list[PublicationRecord]:
        records: list[PublicationRecord] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.warning(f"Failed to parse arXiv Atom XML: {e}")
            return records

        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/xmlns/arxiv",
        }

        for entry in root.findall("atom:entry", ns):
            id_elem = entry.find("atom:id", ns)
            id_url = id_elem.text.strip() if id_elem is not None and id_elem.text else ""
            arxiv_id = id_url.split("/abs/")[-1].split("v")[0] if "/abs/" in id_url else id_url

            title_elem = entry.find("atom:title", ns)
            raw_title = title_elem.text if title_elem is not None and title_elem.text else ""
            title = normalize_title(raw_title)

            summary_elem = entry.find("atom:summary", ns)
            abstract = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None and summary_elem.text else None

            authors_list = [
                a.find("atom:name", ns).text
                for a in entry.findall("atom:author", ns)
                if a.find("atom:name", ns) is not None and a.find("atom:name", ns).text
            ]
            authors = normalize_authors(authors_list)

            published_elem = entry.find("atom:published", ns)
            year: int | None = None
            if published_elem is not None and published_elem.text:
                m = re.match(r"^(\d{4})", published_elem.text.strip())
                if m:
                    year = int(m.group(1))

            doi_elem = entry.find("arxiv:doi", ns)
            doi = normalize_doi(doi_elem.text) if doi_elem is not None and doi_elem.text else None

            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else None

            first_author = authors[0].split()[-1] if authors else "Unknown"
            clean_word = re.sub(r"\W+", "", title.split()[0] if title else "Paper")
            short_id = arxiv_id.replace(".", "_")[-6:]
            cite_key = f"{first_author}{year or 2026}{clean_word}_{short_id}"

            rec = PublicationRecord(
                cite_key=cite_key,
                entry_type="article",
                title=title,
                authors=authors,
                journal="arXiv",
                year=year,
                doi=doi,
                url=id_url,
                abstract=abstract,
                sources=["provider:arxiv"],
                pdf_url=pdf_url,
                is_ojs=False,
                download_status="pending",
                full_metadata={
                    "arxiv": {
                        "id": arxiv_id,
                        "url": id_url,
                        "pdf_url": pdf_url,
                    },
                    "normalized_at": datetime.now(UTC).isoformat(),
                },
            )
            records.append(rec)

        return records

    async def search(self, query: str, *, limit: int = 10, **kwargs: Any) -> list[PublicationRecord]:
        """Search arXiv by keywords."""
        session = self._get_async_session()
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": limit,
        }
        try:
            resp = await session.get(self.BASE_URL, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                return self._parse_atom_xml(resp.text)
            logger.warning(f"arXiv search HTTP {resp.status_code} for '{query}'")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"arXiv search error for '{query}': {e}")
        return []

    async def get_by_doi(self, doi: str, **kwargs: Any) -> PublicationRecord | None:
        """Search arXiv by DOI."""
        norm = normalize_doi(doi)
        if not norm:
            return None
        session = self._get_async_session()
        params = {
            "search_query": f"doi:{norm}",
            "max_results": 1,
        }
        try:
            resp = await session.get(self.BASE_URL, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                records = self._parse_atom_xml(resp.text)
                return records[0] if records else None
        except Exception as e:  # noqa: BLE001
            logger.warning(f"arXiv DOI search error for {norm}: {e}")
        return None
