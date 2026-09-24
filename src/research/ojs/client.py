from __future__ import annotations

import asyncio
from types import TracebackType
from typing import Any, Literal, Self

import httpx
from curl_cffi.requests import AsyncSession, Session
from loguru import logger

from research.cache.manager import HttpCache
from research.ojs.extractor import extract_ojs_metadata
from research.ojs.models import OJSMetadata

EngineType = Literal["curl_cffi", "httpx"]


class OJSClient:
    """Client for fetching and extracting Open Journal Systems (OJS) metadata supporting both curl-cffi and httpx."""

    def __init__(
        self,
        *,
        engine: EngineType = "curl_cffi",
        impersonate: str = "chrome",
        timeout: float = 8.0,
        verify_ssl: bool = False,
        cache: HttpCache | None = None,
    ) -> None:
        self.engine = engine
        self.impersonate = impersonate
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.cache = cache

        # curl-cffi sessions
        self._async_session: AsyncSession | None = None
        self._sync_session: Session | None = None

        # httpx clients
        self._httpx_async: httpx.AsyncClient | None = None
        self._httpx_sync: httpx.Client | None = None

    def _get_sync_session(self) -> Session | httpx.Client:
        if self.engine == "httpx":
            if self._httpx_sync is None:
                self._httpx_sync = httpx.Client(
                    verify=self.verify_ssl,
                    timeout=self.timeout,
                    follow_redirects=True,
                )
            return self._httpx_sync

        if self._sync_session is None:
            self._sync_session = Session(
                impersonate=self.impersonate,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
        return self._sync_session

    async def _get_async_session(self) -> AsyncSession | httpx.AsyncClient:
        if self.engine == "httpx":
            if self._httpx_async is None:
                self._httpx_async = httpx.AsyncClient(
                    verify=self.verify_ssl,
                    timeout=self.timeout,
                    follow_redirects=True,
                )
            return self._httpx_async

        if self._async_session is None:
            self._async_session = AsyncSession(
                impersonate=self.impersonate,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
        return self._async_session

    async def close(self) -> None:
        if self._async_session is not None:
            await self._async_session.close()
            self._async_session = None
        if self._sync_session is not None:
            self._sync_session.close()
            self._sync_session = None
        if self._httpx_async is not None:
            await self._httpx_async.aclose()
            self._httpx_async = None
        if self._httpx_sync is not None:
            self._httpx_sync.close()
            self._httpx_sync = None

    async def __aenter__(self) -> Self:
        await self._get_async_session()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    def __enter__(self) -> Self:
        self._get_sync_session()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._sync_session is not None:
            self._sync_session.close()
            self._sync_session = None
        if self._httpx_sync is not None:
            self._httpx_sync.close()
            self._httpx_sync = None

    async def fetch_metadata(
        self,
        url: str,
        *,
        timeout: float | None = None,
        retries: int = 1,
    ) -> OJSMetadata:
        """Fetch article page and extract OJS metadata asynchronously."""
        if self.cache is not None:
            cached = self.cache.get(url)
            if cached is not None:
                logger.debug(f"OJS metadata cache hit for {url}")
                if cached.status_code >= 400:
                    return OJSMetadata(url=url, is_ojs=False)
                return extract_ojs_metadata(cached.text, url)

        session = await self._get_async_session()
        to = timeout or self.timeout
        timeout_val: Any = (min(float(to), 5.0), float(to)) if self.engine == "curl_cffi" else to
        last_err: Exception | None = None

        for attempt in range(retries + 1):
            try:
                if isinstance(session, httpx.AsyncClient):
                    resp = await session.get(url, timeout=to)
                else:
                    resp = await session.get(url, timeout=timeout_val, allow_redirects=True)

                final_url = str(resp.url)
                if resp.status_code >= 400:
                    if self.cache is not None:
                        self.cache.set(url, resp.status_code, b"", content_type="text/html")
                    logger.debug(f"HTTP {resp.status_code} for {url}")
                    return OJSMetadata(url=final_url, is_ojs=False)

                html = resp.text
                if self.cache is not None:
                    self.cache.set(url, resp.status_code, html, content_type="text/html")
                return extract_ojs_metadata(html, final_url)
            except Exception as e:  # noqa: BLE001 - network/ssl/timeout errors
                last_err = e
                logger.debug(f"Attempt {attempt + 1}/{retries + 1} failed for {url}: {e}")
                if attempt < retries:
                    await asyncio.sleep(1.0 * (attempt + 1))

        logger.warning(f"Failed to fetch OJS page {url}: {last_err}")
        if self.cache is not None:
            self.cache.set(url, 504, b"", content_type="text/html")
        return OJSMetadata(url=url, is_ojs=False)

    def fetch_metadata_sync(
        self,
        url: str,
        *,
        timeout: float | None = None,
        retries: int = 1,
    ) -> OJSMetadata:
        """Fetch article page and extract OJS metadata synchronously."""
        if self.cache is not None:
            cached = self.cache.get(url)
            if cached is not None:
                logger.debug(f"OJS metadata cache hit for {url}")
                if cached.status_code >= 400:
                    return OJSMetadata(url=url, is_ojs=False)
                return extract_ojs_metadata(cached.text, url)

        session = self._get_sync_session()
        to = timeout or self.timeout
        timeout_val: Any = (min(float(to), 5.0), float(to)) if self.engine == "curl_cffi" else to
        last_err: Exception | None = None

        for attempt in range(retries + 1):
            try:
                if isinstance(session, httpx.Client):
                    resp = session.get(url, timeout=to)
                else:
                    resp = session.get(url, timeout=timeout_val, allow_redirects=True)

                final_url = str(resp.url)
                if resp.status_code >= 400:
                    if self.cache is not None:
                        self.cache.set(url, resp.status_code, b"", content_type="text/html")
                    logger.debug(f"HTTP {resp.status_code} for {url}")
                    return OJSMetadata(url=final_url, is_ojs=False)

                html = resp.text
                if self.cache is not None:
                    self.cache.set(url, resp.status_code, html, content_type="text/html")
                return extract_ojs_metadata(html, final_url)
            except Exception as e:  # noqa: BLE001 - network/ssl/timeout errors
                last_err = e
                logger.debug(f"Attempt {attempt + 1}/{retries + 1} failed for {url}: {e}")
                if attempt < retries:
                    import time
                    time.sleep(1.0 * (attempt + 1))

        logger.warning(f"Failed to fetch OJS page {url}: {last_err}")
        if self.cache is not None:
            self.cache.set(url, 504, b"", content_type="text/html")
        return OJSMetadata(url=url, is_ojs=False)
