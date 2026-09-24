from __future__ import annotations

import re
from types import TracebackType
from typing import Self

import httpx
from loguru import logger

from research.unpaywall.models import HARDCODED_EMAIL, UnpaywallRecord


def _normalize_doi(raw_doi: str | None) -> str | None:
    if not raw_doi:
        return None
    cleaned = raw_doi.strip()
    cleaned = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^doi:\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip("/ .;")
    match = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", cleaned)
    if match:
        return match.group(0).lower()
    return cleaned.lower() if cleaned.startswith("10.") else None


class UnpaywallClient:
    """Client for Unpaywall API v2 with hardcoded researcher email."""

    EMAIL = HARDCODED_EMAIL
    BASE_URL = "https://api.unpaywall.org/v2"

    def __init__(self, *, timeout: float = 12.0) -> None:
        self.email = self.EMAIL
        self.timeout = timeout
        self._async_client: httpx.AsyncClient | None = None
        self._sync_client: httpx.Client | None = None

    def _get_sync_client(self) -> httpx.Client:
        if self._sync_client is None or self._sync_client.is_closed:
            headers = {"User-Agent": f"research-unpaywall/0.1 (mailto:{self.email})"}
            self._sync_client = httpx.Client(headers=headers, timeout=self.timeout, follow_redirects=True)
        return self._sync_client

    async def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            headers = {"User-Agent": f"research-unpaywall/0.1 (mailto:{self.email})"}
            self._async_client = httpx.AsyncClient(headers=headers, timeout=self.timeout, follow_redirects=True)
        return self._async_client

    async def close(self) -> None:
        if self._async_client is not None and not self._async_client.is_closed:
            await self._async_client.aclose()
            self._async_client = None
        if self._sync_client is not None and not self._sync_client.is_closed:
            self._sync_client.close()
            self._sync_client = None

    async def __aenter__(self) -> Self:
        await self._get_async_client()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    def __enter__(self) -> Self:
        self._get_sync_client()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._sync_client is not None:
            self._sync_client.close()
            self._sync_client = None

    async def get_record(self, doi: str) -> UnpaywallRecord | None:
        """Fetch Unpaywall open-access metadata for a DOI asynchronously."""
        norm_doi = _normalize_doi(doi)
        if not norm_doi:
            return None

        client = await self._get_async_client()
        url = f"{self.BASE_URL}/{norm_doi}"
        params = {"email": self.email}

        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                return UnpaywallRecord.from_api_response(resp.json())
            if resp.status_code == 404:
                logger.debug(f"Unpaywall: DOI not found {norm_doi}")
                return None
            logger.debug(f"Unpaywall HTTP {resp.status_code} for {norm_doi}")
        except httpx.HTTPError as e:
            logger.debug(f"Unpaywall error for {norm_doi}: {e}")
        return None

    def get_record_sync(self, doi: str) -> UnpaywallRecord | None:
        """Fetch Unpaywall open-access metadata for a DOI synchronously."""
        norm_doi = _normalize_doi(doi)
        if not norm_doi:
            return None

        client = self._get_sync_client()
        url = f"{self.BASE_URL}/{norm_doi}"
        params = {"email": self.email}

        try:
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                return UnpaywallRecord.from_api_response(resp.json())
            if resp.status_code == 404:
                logger.debug(f"Unpaywall: DOI not found {norm_doi}")
                return None
            logger.debug(f"Unpaywall HTTP {resp.status_code} for {norm_doi}")
        except httpx.HTTPError as e:
            logger.debug(f"Unpaywall error for {norm_doi}: {e}")
        return None

    async def get_best_pdf_url(self, doi: str) -> str | None:
        """Convenience method to retrieve the direct PDF download URL if open-access."""
        record = await self.get_record(doi)
        return record.best_pdf_url if record else None

    def get_best_pdf_url_sync(self, doi: str) -> str | None:
        """Convenience synchronous method to retrieve the direct PDF download URL."""
        record = self.get_record_sync(doi)
        return record.best_pdf_url if record else None


# Top-level module helper functions
def get_unpaywall_record(doi: str, *, timeout: float = 12.0) -> UnpaywallRecord | None:
    """Fetch Unpaywall record synchronously using hardcoded email."""
    client = UnpaywallClient(timeout=timeout)
    return client.get_record_sync(doi)


def get_best_pdf_url(doi: str, *, timeout: float = 12.0) -> str | None:
    """Retrieve direct open-access PDF link from Unpaywall."""
    client = UnpaywallClient(timeout=timeout)
    return client.get_best_pdf_url_sync(doi)
