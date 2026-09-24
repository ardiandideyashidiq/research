from __future__ import annotations

import asyncio
import json
from types import TracebackType
from typing import Self

from loguru import logger

from research.cache.manager import HttpCache
from research.db.manager import DatabaseManager
from research.db.models import PublicationRecord
from research.providers.arxiv import ArxivProvider
from research.providers.base import BaseProvider
from research.providers.crossref import CrossrefProvider
from research.providers.doaj import DOAJProvider
from research.providers.openaire import OpenAIREProvider
from research.providers.openalex import OpenAlexProvider


class ProviderRegistry:
    """Registry and federated search orchestrator across all academic providers."""

    def __init__(self, *, db: DatabaseManager | None = None, cache: HttpCache | None = None) -> None:
        self.db = db
        self.cache = cache
        self.providers: dict[str, BaseProvider] = {
            "arxiv": ArxivProvider(),
            "openalex": OpenAlexProvider(),
            "crossref": CrossrefProvider(),
            "doaj": DOAJProvider(),
            "openaire": OpenAIREProvider(),
        }

    def register(self, provider: BaseProvider) -> None:
        self.providers[provider.name] = provider

    def get(self, name: str) -> BaseProvider | None:
        return self.providers.get(name)

    async def close(self) -> None:
        for p in self.providers.values():
            await p.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def search_all(
        self,
        query: str,
        *,
        providers: list[str] | None = None,
        limit_per_provider: int = 5,
        auto_index: bool = True,
    ) -> list[PublicationRecord]:
        """Search across multiple academic providers in parallel, deduplicate, and auto-index into DB."""
        selected_names = providers or list(self.providers.keys())
        active_providers = [self.providers[name] for name in selected_names if name in self.providers]

        logger.info(f"Federated search for '{query}' across {len(active_providers)} providers: {[p.name for p in active_providers]}")

        async def _fetch_provider(provider: BaseProvider) -> list[PublicationRecord]:
            cache_key = f"academic_provider:{provider.name}:{query}:{limit_per_provider}"
            if self.cache is not None:
                cached = self.cache.get(cache_key)
                if cached is not None and cached.status_code == 200:
                    try:
                        cached_items = cached.json()
                        if isinstance(cached_items, list):
                            logger.debug(f"Provider {provider.name} cache hit ({len(cached_items)} items)")
                            return [PublicationRecord.from_row(d) for d in cached_items]
                    except (json.JSONDecodeError, TypeError, KeyError) as e:
                        logger.debug(f"Failed to decode cached provider records: {e}")

            records = await provider.search(query, limit=limit_per_provider)
            if self.cache is not None and records:
                try:
                    payload = json.dumps([r.to_dict() for r in records], ensure_ascii=False)
                    self.cache.set(
                        cache_key,
                        200,
                        payload,
                        content_type="application/json",
                        ttl=self.cache.policy.dynamic_ttl,
                    )
                except Exception as e:  # noqa: BLE001
                    logger.debug(f"Failed to cache provider records for {provider.name}: {e}")
            return records

        task_objs = [asyncio.create_task(_fetch_provider(p)) for p in active_providers]
        try:
            nested_results = await asyncio.gather(*task_objs, return_exceptions=True)
        except (asyncio.CancelledError, KeyboardInterrupt):
            for t in task_objs:
                if not t.done():
                    t.cancel()
            await asyncio.gather(*task_objs, return_exceptions=True)
            raise

        all_records: list[PublicationRecord] = []
        for i, res in enumerate(nested_results):
            p_name = active_providers[i].name
            if isinstance(res, list):
                logger.debug(f"Provider {p_name} returned {len(res)} results")
                all_records.extend(res)
            elif isinstance(res, Exception):
                logger.warning(f"Provider {p_name} error: {res}")

        # Deduplicate results by DOI or normalized title
        deduped: list[PublicationRecord] = []
        seen_dois: set[str] = set()
        seen_titles: set[str] = set()

        for rec in all_records:
            doi_key = rec.doi.lower() if rec.doi else None
            title_key = rec.title.lower().strip() if rec.title else None

            if doi_key and doi_key in seen_dois:
                continue
            if title_key and title_key in seen_titles:
                continue

            if doi_key:
                seen_dois.add(doi_key)
            if title_key:
                seen_titles.add(title_key)

            deduped.append(rec)

            # Auto-index into DatabaseManager if configured
            if auto_index and self.db is not None:
                existing = self.db.find_existing(rec)
                if existing:
                    updated_sources = list(dict.fromkeys(existing.sources + rec.sources))
                    self.db.update(existing.cite_key, sources=updated_sources)
                else:
                    self.db.create(rec)

        logger.success(f"Federated search yielded {len(deduped)} deduplicated publications.")
        return deduped

    def search_all_sync(
        self,
        query: str,
        *,
        providers: list[str] | None = None,
        limit_per_provider: int = 5,
        auto_index: bool = True,
    ) -> list[PublicationRecord]:
        """Synchronous wrapper for search_all."""
        return asyncio.run(
            self.search_all(
                query,
                providers=providers,
                limit_per_provider=limit_per_provider,
                auto_index=auto_index,
            )
        )
