from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from research.google_scholar.models import Publication


@dataclass
class BibEntry:
    cite_key: str
    entry_type: str = "article"
    title: str = ""
    authors: list[str] = field(default_factory=list)
    journal: str | None = None
    year: int | None = None
    volume: str | None = None
    number: str | None = None
    pages: str | None = None
    doi: str | None = None
    url: str | None = None
    abstract: str | None = None
    sources: list[str] = field(default_factory=list)
    raw_fields: dict[str, str] = field(default_factory=dict)

    def to_publication(self) -> Publication:
        from research.google_scholar.models import Publication

        return Publication(
            title=self.title,
            url=self.url,
            authors=list(self.authors),
            year=self.year,
            venue=self.journal,
            citation_count=None,
            abstract=self.abstract,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "cite_key": self.cite_key,
            "entry_type": self.entry_type,
            "title": self.title,
            "authors": self.authors,
            "journal": self.journal,
            "year": self.year,
            "volume": self.volume,
            "number": self.number,
            "pages": self.pages,
            "doi": self.doi,
            "url": self.url,
            "abstract": self.abstract,
            "sources": self.sources,
            "raw_fields": self.raw_fields,
        }
