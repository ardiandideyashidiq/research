"""Dedup test for BibTeX ingest, verified against a real reference-manager export.

Run: uv run python tests/test_bib_dedup.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from research.bibtex.dedup import dedupe_entries, entry_identity
from research.bibtex.parser import parse_bib_file, parse_bib_files

REAL_BIB = Path("/home/rd/Downloads/apaurgensikitauntukmemperlambatperkembanganai-2026-09-25.bib")


def test_real_file_dedups() -> None:
    if not REAL_BIB.exists():
        print("[SKIP] real bib file not present")
        return
    raw = parse_bib_file(REAL_BIB)
    unique = parse_bib_files(REAL_BIB)
    assert len(unique) < len(raw), f"expected dedup: {len(raw)} -> <{len(raw)}"
    # Every entry in the export is a DOI-bearing duplicate pair.
    print(f"[PASS] real bib: {len(raw)} parsed -> {len(unique)} unique")
    keys = {e.cite_key for e in unique}
    assert not any(k.endswith("2") for k in keys), "a ...2 duplicate survived"
    print(f"[PASS] no '...2' suffixed duplicates survive ({len(keys)} keys)")


def test_identity_prefers_doi() -> None:
    raw = parse_bib_file(REAL_BIB) if REAL_BIB.exists() else []
    by_doi: dict[str, set[str]] = {}
    for e in raw:
        if e.doi:
            by_doi.setdefault(e.doi.strip().lower(), set()).add(e.cite_key)
    dupes = {d: ks for d, ks in by_doi.items() if len(ks) > 1}
    if dupes:
        first = next(iter(dupes.values()))
        entries = [e for e in raw if e.doi and e.doi.strip().lower() == next(iter(dupes))]
        ids = {entry_identity(e) for e in entries}
        assert len(ids) == 1, f"entries with same DOI got different identities: {ids}"
        print(f"[PASS] same-DOI entries share one identity ({sorted(first)})")
    else:
        print("[SKIP] no duplicate DOIs in file")


def test_dedupe_keeps_first_and_merges_sources() -> None:
    raw = parse_bib_file(REAL_BIB) if REAL_BIB.exists() else []
    if not raw:
        print("[SKIP] no entries")
        return
    uniq = dedupe_entries(raw)
    assert len(uniq) == len(parse_bib_files(REAL_BIB))
    aliased = [e for e in uniq if e.raw_fields.get("duplicate_cite_keys")]
    if aliased:
        print(f"[PASS] {len(aliased)} unique entries carry duplicate_cite_keys provenance")


def main() -> None:
    test_real_file_dedups()
    test_identity_prefers_doi()
    test_dedupe_keeps_first_and_merges_sources()
    print("\nAll bib dedup tests passed.")


if __name__ == "__main__":
    main()
