from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any, Self

from research.db.models import PublicationRecord


class BaseProvider(ABC):
    """Abstract base class for all academic literature search and metadata providers."""

    name: str = "base"

    @abstractmethod
    async def search(self, query: str, *, limit: int = 10, **kwargs: Any) -> list[PublicationRecord]:
        """Search the provider for publications matching a query string."""

    @abstractmethod
    async def get_by_doi(self, doi: str, **kwargs: Any) -> PublicationRecord | None:
        """Fetch a specific publication by its Digital Object Identifier (DOI)."""

    def search_sync(self, query: str, *, limit: int = 10, **kwargs: Any) -> list[PublicationRecord]:
        """Synchronous wrapper for search."""
        return asyncio.run(self.search(query, limit=limit, **kwargs))

    def get_by_doi_sync(self, doi: str, **kwargs: Any) -> PublicationRecord | None:
        """Synchronous wrapper for get_by_doi."""
        return asyncio.run(self.get_by_doi(doi, **kwargs))

    async def close(self) -> None:
        """Release any underlying client sessions."""

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        asyncio.run(self.close())
