from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PublicationRecord:
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
    pdf_url: str | None = None
    is_ojs: bool | None = None
    download_status: str = "pending"
    download_path: str | None = None
    download_error: str | None = None
    downloaded_at: str | None = None
    file_size: int | None = None
    file_hash: str | None = None
    content_type: str | None = None
    full_metadata: dict[str, Any] = field(default_factory=dict)
    raw_fields: dict[str, str] = field(default_factory=dict)
    markdown_path: str | None = None
    is_chunked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> PublicationRecord:
        """Construct record from a database row dictionary."""
        authors = row.get("authors")
        if isinstance(authors, str):
            try:
                authors = json.loads(authors)
            except (json.JSONDecodeError, TypeError):
                authors = [authors] if authors else []
        elif authors is None:
            authors = []

        sources = row.get("sources")
        if isinstance(sources, str):
            try:
                sources = json.loads(sources)
            except (json.JSONDecodeError, TypeError):
                sources = [sources] if sources else []
        elif sources is None:
            sources = []

        full_meta = row.get("full_metadata")
        if isinstance(full_meta, str):
            try:
                full_meta = json.loads(full_meta)
            except (json.JSONDecodeError, TypeError):
                full_meta = {}
        elif full_meta is None:
            full_meta = {}

        raw_f = row.get("raw_fields")
        if isinstance(raw_f, str):
            try:
                raw_f = json.loads(raw_f)
            except (json.JSONDecodeError, TypeError):
                raw_f = {}
        elif raw_f is None:
            raw_f = {}

        is_ojs_val = row.get("is_ojs")
        if is_ojs_val is not None:
            is_ojs_val = bool(is_ojs_val)

        return cls(
            cite_key=row["cite_key"],
            entry_type=row.get("entry_type", "article"),
            title=row.get("title", ""),
            authors=authors,
            journal=row.get("journal"),
            year=row.get("year"),
            volume=row.get("volume"),
            number=row.get("number"),
            pages=row.get("pages"),
            doi=row.get("doi"),
            url=row.get("url"),
            abstract=row.get("abstract"),
            sources=sources,
            pdf_url=row.get("pdf_url"),
            is_ojs=is_ojs_val,
            download_status=row.get("download_status", "pending"),
            download_path=row.get("download_path"),
            download_error=row.get("download_error"),
            downloaded_at=row.get("downloaded_at"),
            file_size=row.get("file_size"),
            file_hash=row.get("file_hash"),
            content_type=row.get("content_type"),
            full_metadata=full_meta,
            raw_fields=raw_f,
            markdown_path=row.get("markdown_path"),
            is_chunked=bool(row.get("is_chunked", 0)),
        )
