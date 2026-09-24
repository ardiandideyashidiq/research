from __future__ import annotations

from research.normalizer.crossref import (
    fetch_crossref_metadata,
    fetch_crossref_metadata_async,
    normalize_doi,
)
from research.normalizer.normalizer import (
    normalize_abstract,
    normalize_authors,
    normalize_record,
    normalize_record_async,
    normalize_records_async,
    normalize_title,
)

__all__ = [
    "fetch_crossref_metadata",
    "fetch_crossref_metadata_async",
    "normalize_abstract",
    "normalize_authors",
    "normalize_doi",
    "normalize_record",
    "normalize_record_async",
    "normalize_records_async",
    "normalize_title",
]
