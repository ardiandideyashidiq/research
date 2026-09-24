from __future__ import annotations

import asyncio
import time
from types import TracebackType
from typing import TYPE_CHECKING, Literal, Self

from loguru import logger

from research.ddgs.client import DDGSClient
from research.tavily.client import TavilyClient
from research.web_search.indexer import WebSearchIndexer
from research.web_search.models import (
    WebSearchProvider,
    WebSearchResponse,
    WebSearchResult,
)

if TYPE_CHECKING:
    from pathlib import Path

    from research.db.manager import DatabaseManager

SearchTopic = Literal["general", "news"]


class WebSearchEngine:
    """Unified web search engine orchestrating Tavily and DuckDuckGo (ddgs) with auto-indexing."""

    def __init__(
        self,
        db: DatabaseManager | None = None,
        *,
        tavily_keys: list[str] | str | None = None,
        output_dir: str | Path = "data/web_searches",
        timeout: float = 15.0,
    ) -> None:
        self.tavily = TavilyClient(api_keys=tavily_keys, timeout=timeout)
        self.ddgs = DDGSClient(timeout=timeout)
        self._db = db
        self.output_dir = output_dir
        self._indexer: WebSearchIndexer | None = None
        if self._db is not None:
            self._indexer = WebSearchIndexer(self._db, output_dir=output_dir)

    def set_db(self, db: DatabaseManager) -> None:
        """Set or update DatabaseManager instance for auto-indexing."""
        self._db = db
        self._indexer = WebSearchIndexer(db, output_dir=self.output_dir)

    async def close(self) -> None:
        """Close underlying HTTP clients."""
        await self.tavily.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def _search_tavily(
        self,
        query: str,
        *,
        topic: SearchTopic = "general",
        limit: int = 5,
    ) -> list[WebSearchResult]:
        try:
            t_topic = "news" if topic == "news" else "general"
            resp = await self.tavily.search(query, topic=t_topic, max_results=limit)
            results: list[WebSearchResult] = []
            for r in resp.results:
                results.append(
                    WebSearchResult(
                        title=r.title,
                        url=r.url,
                        content=r.content,
                        provider="tavily",
                        query=query,
                        score=r.score,
                        raw_content=r.raw_content,
                    )
                )
            return results
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Tavily search failed for '{query}': {e}")
            return []

    async def _search_ddgs(
        self,
        query: str,
        *,
        topic: SearchTopic = "general",
        limit: int = 5,
    ) -> list[WebSearchResult]:
        try:
            d_topic = "news" if topic == "news" else "general"
            resp = await self.ddgs.search(query, topic=d_topic, max_results=limit)
            results: list[WebSearchResult] = []
            for r in resp.results:
                results.append(
                    WebSearchResult(
                        title=r.title,
                        url=r.url,
                        content=r.body,
                        provider="ddgs",
                        query=query,
                        published_date=r.date,
                    )
                )
            return results
        except Exception as e:  # noqa: BLE001
            logger.warning(f"DDGS search failed for '{query}': {e}")
            return []

    async def search(
        self,
        query: str,
        *,
        provider: WebSearchProvider = "all",
        topic: SearchTopic = "general",
        limit: int = 5,
        auto_index: bool = True,
    ) -> WebSearchResponse:
        """Search across Tavily and/or DuckDuckGo, clean markdown, and automatically index into SQLite RAG."""
        t0 = time.time()
        logger.info(f"Initiating web search '{query}' (provider={provider}, topic={topic}, limit={limit})...")

        results: list[WebSearchResult] = []

        if provider == "tavily":
            results = await self._search_tavily(query, topic=topic, limit=limit)
            if not results:
                logger.info("Tavily yielded 0 results, attempting fallback to DDGS...")
                results = await self._search_ddgs(query, topic=topic, limit=limit)
        elif provider == "ddgs":
            results = await self._search_ddgs(query, topic=topic, limit=limit)
        else:
            # provider == 'all': search concurrently
            t_task = asyncio.create_task(self._search_tavily(query, topic=topic, limit=limit))
            d_task = asyncio.create_task(self._search_ddgs(query, topic=topic, limit=limit))
            try:
                t_res, d_res = await asyncio.gather(t_task, d_task)
            except (asyncio.CancelledError, KeyboardInterrupt):
                for t in [t_task, d_task]:
                    if not t.done():
                        t.cancel()
                await asyncio.gather(t_task, d_task, return_exceptions=True)
                raise

            # Deduplicate by canonical URL
            seen_urls: set[str] = set()
            combined: list[WebSearchResult] = []
            for r in t_res + d_res:
                norm_url = r.url.rstrip("/")
                if norm_url not in seen_urls:
                    seen_urls.add(norm_url)
                    combined.append(r)
            results = combined[:limit]

        elapsed = round(time.time() - t0, 3)

        # Automatic Markdown extraction and SQLite RAG indexing
        indexed_docs = 0
        indexed_chunks = 0
        if auto_index and self._indexer is not None and results:
            index_stats = self._indexer.index_results(results, chunk_rag=True)
            indexed_docs = index_stats["indexed_documents"]
            indexed_chunks = index_stats["indexed_chunks"]

        return WebSearchResponse(
            query=query,
            provider=provider,
            total_results=len(results),
            results=results,
            response_time=elapsed,
            indexed_documents=indexed_docs,
            indexed_chunks=indexed_chunks,
        )
