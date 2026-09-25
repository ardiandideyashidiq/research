"""Deduplication for parsed BibTeX entries.

Exports downloaded from reference managers routinely contain the same work
twice — once under its original cite key and once under a ``...2`` suffixed
key when a manager re-imported a PDF. Reviewing both wastes the full-text
download and the analysis pass, so ingest deduplicates before doing any work.

Identity is resolved in priority order:

1. normalized DOI (``https://doi.org/`` prefix and case differences removed),
2. otherwise a normalized ``title + year`` key,
3. otherwise the cite key itself.
"""

from __future__ import annotations

import re
from typing import Any

from research.bibtex.models import BibEntry
from research.normalizer.crossref import normalize_doi

_WS_RE = re.compile(r"\s+")


def normalize_title(raw: str | None) -> str:
    """Collapse whitespace and case for fuzzy title identity."""
    if not raw:
        return ""
    return _WS_RE.sub(" ", raw).strip().lower()


def _fallback_key(entry: BibEntry) -> str:
    return f"{normalize_title(entry.title)}|{entry.year or ''}"


def entry_identity(entry: BibEntry) -> str:
    """Stable identity key for a BibTeX entry (DOI, else title+year, else key)."""
    doi = normalize_doi(entry.doi)
    if doi:
        return f"doi:{doi}"
    if normalize_title(entry.title):
        return f"title:{_fallback_key(entry)}"
    return f"key:{entry.cite_key}"


def dedupe_entries(entries: list[BibEntry]) -> list[BibEntry]:
    """Return entries in first-seen order with duplicate works removed.

    The first occurrence wins, so an unsuffixed original cite key is kept over a
    later ``...2`` duplicate.
    """
    seen: dict[str, str] = {}
    unique: list[BibEntry] = []
    for entry in entries:
        identity = entry_identity(entry)
        if identity in seen:
            # Record the alias on the surviving entry so provenance survives.
            alias = seen[identity]
            if entry.cite_key != alias and entry.cite_key not in entry.raw_fields.get(
                "duplicate_cite_keys", ""
            ).split(","):
                existing = next((e for e in unique if e.cite_key == alias), None)
                if existing is not None:
                    merged = existing.raw_fields.get("duplicate_cite_keys", "")
                    existing.raw_fields["duplicate_cite_keys"] = (
                        f"{merged},{entry.cite_key}" if merged else entry.cite_key
                    )
            continue
        seen[identity] = entry.cite_key
        unique.append(entry)
    return unique


def dedupe_dicts(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Same as :func:`dedupe_entries` but for raw dict records (e.g. CSL-JSON)."""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for raw in entries:
        doi = normalize_doi(raw.get("DOI") or raw.get("doi"))
        title = normalize_title(raw.get("title"))
        year = raw.get("issued", {}).get("date-parts", [[None]])[0][0] if raw.get("issued") else raw.get("year")
        key = f"doi:{doi}" if doi else f"title:{title}|{year or ''}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(raw)
    return unique
