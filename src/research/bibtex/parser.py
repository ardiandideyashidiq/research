from __future__ import annotations

import re
from pathlib import Path

from research.bibtex.models import BibEntry


def _clean_field_value(value: str) -> str:
    cleaned = value.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def _parse_authors(authors_str: str) -> list[str]:
    raw_authors = re.split(r"\s+and\s+", authors_str.strip(), flags=re.IGNORECASE)
    authors = []
    for a in raw_authors:
        name = a.strip().strip("{}").strip()
        if name:
            authors.append(name)
    return authors


def parse_bib_str(text: str, *, source: str | None = None) -> list[BibEntry]:
    """Parse BibTeX entries from a string."""
    pos = 0
    length = len(text)
    entries: list[BibEntry] = []

    while pos < length:
        at_pos = text.find("@", pos)
        if at_pos == -1:
            break

        brace_pos = text.find("{", at_pos)
        if brace_pos == -1:
            break

        entry_type = text[at_pos + 1 : brace_pos].strip().lower()
        comma_pos = text.find(",", brace_pos)
        if comma_pos == -1:
            break

        cite_key = text[brace_pos + 1 : comma_pos].strip()

        # Find matching closing brace for this entry
        curr = comma_pos + 1
        depth = 1
        fields_str_start = curr

        while curr < length and depth > 0:
            ch = text[curr]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            curr += 1

        fields_str = text[fields_str_start : curr - 1]
        pos = curr

        # Parse key-value fields inside the entry
        raw_fields: dict[str, str] = {}
        f_idx = 0
        f_len = len(fields_str)

        while f_idx < f_len:
            while f_idx < f_len and fields_str[f_idx] in " \t\r\n,":
                f_idx += 1
            if f_idx >= f_len:
                break

            eq_idx = fields_str.find("=", f_idx)
            if eq_idx == -1:
                break

            field_name = fields_str[f_idx:eq_idx].strip().lower()

            val_start = eq_idx + 1
            while val_start < f_len and fields_str[val_start] in " \t\r\n":
                val_start += 1
            if val_start >= f_len:
                break

            val = ""
            if fields_str[val_start] == "{":
                brace_depth = 1
                v_curr = val_start + 1
                while v_curr < f_len and brace_depth > 0:
                    if fields_str[v_curr] == "{":
                        brace_depth += 1
                    elif fields_str[v_curr] == "}":
                        brace_depth -= 1
                    v_curr += 1
                val = fields_str[val_start + 1 : v_curr - 1]
                f_idx = v_curr
            elif fields_str[val_start] == '"':
                v_curr = val_start + 1
                while v_curr < f_len and fields_str[v_curr] != '"':
                    v_curr += 1
                val = fields_str[val_start + 1 : v_curr]
                f_idx = v_curr + 1
            else:
                v_curr = val_start
                while v_curr < f_len and fields_str[v_curr] not in ",\r\n}":
                    v_curr += 1
                val = fields_str[val_start:v_curr]
                f_idx = v_curr

            if field_name:
                raw_fields[field_name] = _clean_field_value(val)

        # Parse year
        year: int | None = None
        if "year" in raw_fields:
            try:
                year = int(raw_fields["year"])
            except ValueError:
                year = None

        # Parse authors
        authors = _parse_authors(raw_fields.get("author", ""))

        sources = [source] if source else []

        entry = BibEntry(
            cite_key=cite_key,
            entry_type=entry_type,
            title=raw_fields.get("title", ""),
            authors=authors,
            journal=raw_fields.get("journal"),
            year=year,
            volume=raw_fields.get("volume"),
            number=raw_fields.get("number"),
            pages=raw_fields.get("pages"),
            doi=raw_fields.get("doi"),
            url=raw_fields.get("url"),
            abstract=raw_fields.get("abstract"),
            sources=sources,
            raw_fields=raw_fields,
        )
        entries.append(entry)

    return entries


def parse_bib_file(path: str | Path) -> list[BibEntry]:
    """Parse a single BibTeX file."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    return parse_bib_str(text, source=str(p))


def expand_bib_paths(
    paths: list[str | Path] | list[str] | list[Path] | str | Path,
    *,
    recursive: bool = True,
) -> list[Path]:
    """Expand a path or collection of file and directory paths into a sorted list of unique .bib file paths.

    If a path is a directory, searches for all *.bib files (recursively if recursive=True).
    If a path is an existing file, it is included directly.
    """
    raw_paths: list[str | Path]
    if isinstance(paths, (str, Path)):
        if isinstance(paths, str) and "," in paths:
            raw_paths = [p.strip() for p in paths.split(",") if p.strip()]
        else:
            raw_paths = [paths]
    else:
        raw_paths = list(paths)

    bib_files: list[Path] = []
    seen: set[Path] = set()

    for p in raw_paths:
        path_obj = Path(p)
        if path_obj.is_dir():
            pattern = "**/*.bib" if recursive else "*.bib"
            for f in sorted(path_obj.glob(pattern)):
                if f.is_file():
                    resolved = f.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        bib_files.append(f)
        elif path_obj.is_file():
            resolved = path_obj.resolve()
            if resolved not in seen:
                seen.add(resolved)
                bib_files.append(path_obj)
        elif path_obj.exists():
            continue
        else:
            bib_files.append(path_obj)

    return bib_files


def parse_bib_files(
    paths: list[str | Path] | list[str] | list[Path] | str | Path,
    *,
    deduplicate: bool = True,
    recursive: bool = True,
) -> list[BibEntry]:
    """Parse multiple BibTeX files or directories, optionally deduplicating entries by cite_key."""
    file_paths = expand_bib_paths(paths, recursive=recursive)
    parsed: list[BibEntry] = []
    for path in file_paths:
        parsed.extend(parse_bib_file(path))

    if not deduplicate:
        return parsed

    from research.bibtex.dedup import entry_identity

    # DOI/title-aware dedup. Reference-manager exports commonly re-import the
    # same work under a "...2" cite key, which cite_key-only dedup misses.
    seen: dict[str, BibEntry] = {}
    result: list[BibEntry] = []
    for entry in parsed:
        identity = entry_identity(entry)
        if identity in seen:
            existing = seen[identity]
            for src in entry.sources:
                if src not in existing.sources:
                    existing.sources.append(src)
            aliases = existing.raw_fields.get("duplicate_cite_keys", "")
            if entry.cite_key != existing.cite_key:
                existing.raw_fields["duplicate_cite_keys"] = (
                    f"{aliases},{entry.cite_key}" if aliases else entry.cite_key
                )
        else:
            seen[identity] = entry
            result.append(entry)
    return result

