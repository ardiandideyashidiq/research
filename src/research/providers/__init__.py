from __future__ import annotations

from research.providers.arxiv import ArxivProvider
from research.providers.base import BaseProvider
from research.providers.crossref import CrossrefProvider
from research.providers.doaj import DOAJProvider
from research.providers.openaire import OpenAIREProvider
from research.providers.openalex import OpenAlexProvider
from research.providers.registry import ProviderRegistry

__all__ = [
    "ArxivProvider",
    "BaseProvider",
    "CrossrefProvider",
    "DOAJProvider",
    "OpenAIREProvider",
    "OpenAlexProvider",
    "ProviderRegistry",
]
