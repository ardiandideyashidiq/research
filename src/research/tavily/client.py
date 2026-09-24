from __future__ import annotations

import asyncio
from types import TracebackType
from typing import Any, Literal, Self

import httpx
from loguru import logger

from research.tavily.models import (
    DEFAULT_TAVILY_KEYS,
    TavilySearchResponse,
    TavilySearchResult,
)
from research.tavily.pool import APIKeyPool, LoadBalanceStrategy

SearchDepth = Literal["basic", "advanced"]
SearchTopic = Literal["general", "news"]


class TavilyClient:
    """Tavily search client with multi-key load balancing and automatic failover."""

    BASE_URL = "https://api.tavily.com/search"

    def __init__(
        self,
        api_keys: list[str] | str | None = None,
        *,
        strategy: LoadBalanceStrategy = "round_robin",
        timeout: float = 15.0,
    ) -> None:
        if api_keys is None:
            keys = list(DEFAULT_TAVILY_KEYS)
        elif isinstance(api_keys, str):
            keys = [k.strip() for k in api_keys.split(",") if k.strip()]
        else:
            keys = [k.strip() for k in api_keys if k.strip()]

        self.pool = APIKeyPool(keys, strategy=strategy)
        self.timeout = timeout
        self._async_client: httpx.AsyncClient | None = None
        self._sync_client: httpx.Client | None = None

    def _get_sync_client(self) -> httpx.Client:
        if self._sync_client is None or self._sync_client.is_closed:
            self._sync_client = httpx.Client(timeout=self.timeout, follow_redirects=True)
        return self._sync_client

    async def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)
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

    def get_pool_stats(self) -> list[dict[str, object]]:
        """Return statistics on API key usage and status."""
        return self.pool.get_stats()

    async def search(
        self,
        query: str,
        *,
        search_depth: SearchDepth = "basic",
        topic: SearchTopic = "general",
        max_results: int = 5,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        include_answer: bool = False,
        include_raw_content: bool = False,
    ) -> TavilySearchResponse:
        """Search Tavily asynchronously with automated key rotation and failover."""
        client = await self._get_async_client()
        max_attempts = self.pool.total_keys
        last_error: Exception | None = None

        payload_base: dict[str, Any] = {
            "query": query,
            "search_depth": search_depth,
            "topic": topic,
            "max_results": max_results,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
        }
        if include_domains:
            payload_base["include_domains"] = include_domains
        if exclude_domains:
            payload_base["exclude_domains"] = exclude_domains

        for attempt in range(max_attempts):
            key_status = self.pool.next_key()
            payload = {**payload_base, "api_key": key_status.key}

            try:
                resp = await client.post(self.BASE_URL, json=payload)

                if resp.status_code == 200:
                    data = resp.json()
                    results = [
                        TavilySearchResult(
                            url=r.get("url", ""),
                            title=r.get("title", ""),
                            content=r.get("content", ""),
                            score=float(r.get("score", 0.0)),
                            raw_content=r.get("raw_content"),
                        )
                        for r in data.get("results", [])
                    ]
                    return TavilySearchResponse(
                        query=query,
                        results=results,
                        response_time=float(data.get("response_time", 0.0)),
                        api_key_used=key_status.masked_key,
                        request_id=data.get("request_id"),
                    )

                if resp.status_code in (429, 401, 403):
                    reason = f"HTTP {resp.status_code}: {resp.text[:100]}"
                    self.pool.mark_exhausted(key_status.key, reason=reason)
                    continue

                logger.warning(f"Tavily returned unexpected HTTP {resp.status_code}: {resp.text[:100]}")
                self.pool.record_error(key_status.key)

            except httpx.HTTPError as e:
                last_error = e
                self.pool.record_error(key_status.key)
                logger.debug(f"HTTP error using key {key_status.masked_key}: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(0.5)

        msg = f"All {max_attempts} Tavily API keys failed for query '{query}': {last_error}"
        raise RuntimeError(msg)

    def search_sync(
        self,
        query: str,
        *,
        search_depth: SearchDepth = "basic",
        topic: SearchTopic = "general",
        max_results: int = 5,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        include_answer: bool = False,
        include_raw_content: bool = False,
    ) -> TavilySearchResponse:
        """Search Tavily synchronously with automated key rotation and failover."""
        client = self._get_sync_client()
        max_attempts = self.pool.total_keys
        last_error: Exception | None = None

        payload_base: dict[str, Any] = {
            "query": query,
            "search_depth": search_depth,
            "topic": topic,
            "max_results": max_results,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
        }
        if include_domains:
            payload_base["include_domains"] = include_domains
        if exclude_domains:
            payload_base["exclude_domains"] = exclude_domains

        for attempt in range(max_attempts):
            key_status = self.pool.next_key()
            payload = {**payload_base, "api_key": key_status.key}

            try:
                resp = client.post(self.BASE_URL, json=payload)

                if resp.status_code == 200:
                    data = resp.json()
                    results = [
                        TavilySearchResult(
                            url=r.get("url", ""),
                            title=r.get("title", ""),
                            content=r.get("content", ""),
                            score=float(r.get("score", 0.0)),
                            raw_content=r.get("raw_content"),
                        )
                        for r in data.get("results", [])
                    ]
                    return TavilySearchResponse(
                        query=query,
                        results=results,
                        response_time=float(data.get("response_time", 0.0)),
                        api_key_used=key_status.masked_key,
                        request_id=data.get("request_id"),
                    )

                if resp.status_code in (429, 401, 403):
                    reason = f"HTTP {resp.status_code}: {resp.text[:100]}"
                    self.pool.mark_exhausted(key_status.key, reason=reason)
                    continue

                logger.warning(f"Tavily returned unexpected HTTP {resp.status_code}: {resp.text[:100]}")
                self.pool.record_error(key_status.key)

            except httpx.HTTPError as e:
                last_error = e
                self.pool.record_error(key_status.key)
                logger.debug(f"HTTP error using key {key_status.masked_key}: {e}")
                if attempt < max_attempts - 1:
                    import time
                    time.sleep(0.5)

        msg = f"All {max_attempts} Tavily API keys failed for query '{query}': {last_error}"
        raise RuntimeError(msg)
