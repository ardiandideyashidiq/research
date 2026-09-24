from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class OJSMetadata:
    url: str
    is_ojs: bool = False
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    journal_title: str | None = None
    publication_date: str | None = None
    year: int | None = None
    doi: str | None = None
    volume: str | None = None
    issue: str | None = None
    firstpage: str | None = None
    lastpage: str | None = None
    abstract: str | None = None
    pdf_url: str | None = None
    galley_urls: list[str] = field(default_factory=list)
    raw_meta: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
