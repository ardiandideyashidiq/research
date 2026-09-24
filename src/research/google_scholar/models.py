from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from research.db.models import PublicationRecord


@dataclass
class Publication:
    title: str
    url: str | None = None
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str | None = None
    citation_count: int | None = None
    abstract: str | None = None

    def to_publication_record(self) -> PublicationRecord:
        from research.db.models import PublicationRecord

        first_author = "Unknown"
        if self.authors:
            parts = re.findall(r"\b[A-Za-z]+\b", self.authors[0])
            if parts:
                first_author = parts[-1].capitalize()
        yr = str(self.year) if self.year else "2026"
        words = re.findall(r"[A-Za-z]+", self.title)
        title_word = words[0].capitalize() if words else "Scholar"
        hash_suffix = hashlib.md5((self.title + (self.url or "")).encode()).hexdigest()[:6]
        cite_key = f"{first_author}{yr}{title_word}_{hash_suffix}"

        return PublicationRecord(
            cite_key=cite_key,
            title=self.title,
            authors=self.authors,
            year=self.year,
            journal=self.venue,
            url=self.url,
            abstract=self.abstract,
            sources=["google_scholar"],
            full_metadata={
                "citation_count": self.citation_count,
                "venue": self.venue,
            },
        )


@dataclass
class SearchResult:
    query: str
    total_results: int | None = None
    publications: list[Publication] = field(default_factory=list)