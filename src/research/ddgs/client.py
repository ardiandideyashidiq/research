from __future__ import annotations

import asyncio
import time
from typing import Any

from ddgs import DDGS
from loguru import logger

from research.ddgs.models import DDGSSearchResponse, DDGSSearchResult, DDGSTopic


class DDGSClient:
    """DuckDuckGo search client for text and news queries with async support."""

    def __init__(self, *, timeout: float = 15.0) -> None:
        self.timeout = timeout

    def _sync_search_text(self, query: str, max_results: int) -> list[dict[str, Any]]:
        with DDGS(timeout=self.timeout) as ddgs:
            return list(ddgs.text(query, max_results=max_results))

    def _sync_search_news(self, query: str, max_results: int) -> list[dict[str, Any]]:
        with DDGS(timeout=self.timeout) as ddgs:
            return list(ddgs.news(query, max_results=max_results))

    async def search(
        self,
        query: str,
        *,
        topic: DDGSTopic = "general",
        max_results: int = 5,
    ) -> DDGSSearchResponse:
        """Execute async DuckDuckGo search."""
        t0 = time.time()
        logger.debug(f"Executing DDGS {topic} search for '{query}' (limit={max_results})...")

        try:
            if topic == "news":
                raw_items = await asyncio.to_thread(self._sync_search_news, query, max_results)
            else:
                raw_items = await asyncio.to_thread(self._sync_search_text, query, max_results)

            results: list[DDGSSearchResult] = []
            for item in raw_items:
                title = item.get("title") or ""
                url = item.get("href") or item.get("url") or ""
                body = item.get("body") or ""
                date = item.get("date")
                source = item.get("source")

                if title and url:
                    results.append(
                        DDGSSearchResult(
                            title=title,
                            url=url,
                            body=body,
                            date=date,
                            source=source,
                        )
                    )

            elapsed = round(time.time() - t0, 3)
            logger.info(f"DDGS search yielded {len(results)} results in {elapsed}s")
            return DDGSSearchResponse(
                query=query,
                topic=topic,
                results=results,
                response_time=elapsed,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"DDGS search failed for '{query}': {e}")
            elapsed = round(time.time() - t0, 3)
            return DDGSSearchResponse(
                query=query,
                topic=topic,
                results=[],
                response_time=elapsed,
            )
