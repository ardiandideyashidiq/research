from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from research.bibliography.csl import CSLEngine
from research.bibliography.models import Author, CSLItem
from research.bibtex.parser import parse_bib_str
from research.db.models import PublicationRecord
from research.normalizer.crossref import fetch_crossref_metadata, normalize_doi

if TYPE_CHECKING:
    from research.db.manager import DatabaseManager


def _read_source_content(source: str | Path) -> str:
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8", errors="ignore")
    if isinstance(source, str):
        if "\n" not in source and len(source) < 260:
            try:
                p = Path(source)
                if p.is_file():
                    return p.read_text(encoding="utf-8", errors="ignore")
            except (OSError, ValueError):
                pass
        return source
    return str(source)


class BibliographyManager:
    """Full CRUD Bibliography Manager with Multi-CSL formatting, import, and export."""

    def __init__(self, db: DatabaseManager, *, csl_engine: CSLEngine | None = None) -> None:
        self.db = db
        self.csl = csl_engine or CSLEngine()

    # =========================================================================
    # CREATE (Add / Import)
    # =========================================================================

    def create(self, record: PublicationRecord | dict[str, Any]) -> PublicationRecord:
        """Create or insert a publication/reference record in the database."""
        if isinstance(record, dict):
            rec = PublicationRecord.from_row(record)
        else:
            rec = record

        if not rec.cite_key:
            rec.cite_key = self._generate_cite_key(rec)

        return self.db.create(rec)

    def import_bibtex(self, source: str | Path) -> list[PublicationRecord]:
        """Import bibliographic entries from a BibTeX file or raw string."""
        bib_str = _read_source_content(source)
        entries = parse_bib_str(bib_str)
        created: list[PublicationRecord] = []
        for e in entries:
            pub = PublicationRecord(
                cite_key=e.cite_key,
                entry_type=e.entry_type or "article",
                title=e.title,
                authors=list(e.authors),
                journal=e.journal,
                year=e.year,
                volume=e.volume,
                number=e.number,
                pages=e.pages,
                doi=e.doi,
                url=e.url,
                abstract=e.abstract,
                sources=["bibtex_import"],
                raw_fields=e.raw_fields,
            )
            saved = self.db.create(pub)
            created.append(saved)

        logger.info("Imported {} entries from BibTeX.", len(created))
        return created

    def import_csl_json(self, source: str | Path | list[dict[str, Any]]) -> list[PublicationRecord]:
        """Import entries from standard CSL-JSON file, string, or list of dicts."""
        if isinstance(source, list):
            data = source
        else:
            raw = _read_source_content(source)
            data = json.loads(raw)

        if isinstance(data, dict):
            data = [data]

        created: list[PublicationRecord] = []
        for item_dict in data:
            csl_item = CSLItem.from_csl_dict(item_dict)
            if not csl_item.id:
                csl_item.id = self._generate_cite_key_for_csl(csl_item)
            rec = csl_item.to_publication_record()
            saved = self.db.create(rec)
            created.append(saved)

        logger.info("Imported {} entries from CSL-JSON.", len(created))
        return created

    def import_ris(self, source: str | Path) -> list[PublicationRecord]:
        """Import bibliographic entries from RIS format file or string."""
        content = _read_source_content(source)

        records_raw = content.split("ER  -")
        created: list[PublicationRecord] = []

        for chunk in records_raw:
            chunk = chunk.strip()
            if not chunk:
                continue

            lines = chunk.splitlines()
            current_tag = None
            data: dict[str, Any] = {"authors": []}

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                match = re.match(r"^([A-Z0-9]{2})\s*-\s*(.*)$", line)
                if match:
                    current_tag = match.group(1)
                    val = match.group(2).strip()
                    if current_tag == "AU":
                        data["authors"].append(val)
                    elif current_tag in ("TI", "T1"):
                        data["title"] = val
                    elif current_tag in ("JO", "JF", "T2"):
                        data["journal"] = val
                    elif current_tag == "PY":
                        year_m = re.search(r"\b(19\d\d|20\d\d)\b", val)
                        if year_m:
                            data["year"] = int(year_m.group(1))
                    elif current_tag == "VL":
                        data["volume"] = val
                    elif current_tag == "IS":
                        data["number"] = val
                    elif current_tag == "SP":
                        data["sp"] = val
                    elif current_tag == "EP":
                        data["ep"] = val
                    elif current_tag == "DO":
                        data["doi"] = val
                    elif current_tag == "UR":
                        data["url"] = val
                    elif current_tag in ("AB", "N2"):
                        data["abstract"] = val
                    elif current_tag == "ID":
                        data["cite_key"] = val
                    elif current_tag == "TY":
                        data["entry_type"] = val.lower()

            if not data.get("title") and not data.get("authors"):
                continue

            sp = data.get("sp")
            ep = data.get("ep")
            pages = f"{sp}-{ep}" if sp and ep else (sp or ep)

            rec = PublicationRecord(
                cite_key=data.get("cite_key") or "",
                entry_type="article",
                title=data.get("title", ""),
                authors=data.get("authors", []),
                journal=data.get("journal"),
                year=data.get("year"),
                volume=data.get("volume"),
                number=data.get("number"),
                pages=pages,
                doi=data.get("doi"),
                url=data.get("url"),
                abstract=data.get("abstract"),
                sources=["ris_import"],
            )
            if not rec.cite_key:
                rec.cite_key = self._generate_cite_key(rec)

            saved = self.db.create(rec)
            created.append(saved)

        logger.info("Imported {} entries from RIS.", len(created))
        return created

    def import_doi(self, raw_doi: str) -> PublicationRecord | None:
        """Resolve metadata for a DOI via Crossref and add to bibliography database."""
        doi = normalize_doi(raw_doi)
        if not doi:
            logger.warning("Invalid DOI string: '{}'", raw_doi)
            return None

        # Check if already present in DB
        existing = self.get_by_doi(doi)
        if existing:
            logger.info("Publication with DOI '{}' already exists (`{}`).", doi, existing.cite_key)
            return existing

        work = fetch_crossref_metadata(doi)
        if not work:
            logger.warning("Could not fetch Crossref metadata for DOI: '{}'", doi)
            return None

        title = ""
        titles = work.get("title", [])
        if titles and isinstance(titles, list):
            title = titles[0]

        authors = []
        for a in work.get("author", []):
            if isinstance(a, dict):
                given = a.get("given", "").strip()
                family = a.get("family", "").strip()
                name = f"{given} {family}".strip() if given else family
                if name:
                    authors.append(name)

        journal = None
        containers = work.get("container-title", [])
        if containers and isinstance(containers, list):
            journal = containers[0]

        year = None
        for date_field in ("published-print", "published-online", "created", "issued"):
            date_parts = work.get(date_field, {}).get("date-parts", [])
            if date_parts and date_parts[0]:
                year = date_parts[0][0]
                break

        rec = PublicationRecord(
            cite_key="",
            entry_type=work.get("type", "article"),
            title=title,
            authors=authors,
            journal=journal,
            year=year,
            volume=str(work.get("volume")) if work.get("volume") is not None else None,
            number=str(work.get("issue")) if work.get("issue") is not None else None,
            pages=str(work.get("page")) if work.get("page") is not None else None,
            doi=doi,
            url=work.get("URL") or f"https://doi.org/{doi}",
            abstract=work.get("abstract"),
            sources=["crossref_doi_import"],
            full_metadata=work,
        )
        rec.cite_key = self._generate_cite_key(rec)

        saved = self.db.create(rec)
        logger.info("Successfully imported DOI '{}' as `{}`.", doi, saved.cite_key)
        return saved

    # =========================================================================
    # READ (Get / List / Search / CSL Format)
    # =========================================================================

    def get(self, cite_key: str) -> PublicationRecord | None:
        """Fetch publication record by cite_key."""
        return self.db.get(cite_key)

    def get_csl(self, cite_key: str) -> CSLItem | None:
        """Fetch publication record as a standardized CSLItem."""
        rec = self.get(cite_key)
        if not rec:
            return None
        return CSLItem.from_publication_record(rec)

    def get_by_doi(self, doi: str) -> PublicationRecord | None:
        """Find publication record matching a canonical DOI."""
        norm = normalize_doi(doi)
        if not norm:
            return None
        conn = self.db.get_connection()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM publications WHERE LOWER(doi) = ? LIMIT 1", (norm.lower(),)).fetchone()
        if row:
            return PublicationRecord.from_row(dict(row))
        return None

    def list(
        self,
        *,
        corpus: str | None = None,
        year: int | None = None,
        author: str | None = None,
        journal: str | None = None,
        query: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PublicationRecord]:
        """Search and list publications with multi-criteria filtering."""
        if query:
            return self.db.search(query, limit=limit)

        conn = self.db.get_connection()
        cursor = conn.cursor()

        conditions = ["1=1"]
        params: list[Any] = []

        if corpus and corpus != "all":
            if corpus == "putusan":
                conditions.append("(entry_type = 'putusan' OR cite_key LIKE 'Putusan_%')")
            elif corpus == "literature":
                conditions.append("entry_type != 'putusan' AND entry_type != 'online' AND cite_key NOT LIKE 'Putusan_%'")
            elif corpus == "web":
                conditions.append("entry_type = 'online'")

        if year:
            conditions.append("year = ?")
            params.append(year)

        if author:
            conditions.append("authors LIKE ?")
            params.append(f"%{author}%")

        if journal:
            conditions.append("journal LIKE ?")
            params.append(f"%{journal}%")

        where_clause = " AND ".join(conditions)
        sql = f"SELECT * FROM publications WHERE {where_clause} ORDER BY year DESC, title ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = cursor.execute(sql, params).fetchall()
        return [PublicationRecord.from_row(dict(r)) for r in rows]

    def format_citation(
        self,
        record_or_key: str | PublicationRecord | CSLItem,
        style: str = "apa",
        *,
        citation_type: str = "bibliography",
        index: int = 1,
        page: str | None = None,
    ) -> str:
        """Format a single publication in any supported CSL style."""
        if isinstance(record_or_key, CSLItem):
            item = record_or_key
        elif isinstance(record_or_key, PublicationRecord):
            item = CSLItem.from_publication_record(record_or_key)
        else:
            rec = self.get(str(record_or_key))
            if not rec:
                return f"[Citation error: key '{record_or_key}' not found]"
            item = CSLItem.from_publication_record(rec)

        if citation_type == "in_text":
            return self.csl.format_in_text(item, style=style, index=index, page=page)
        return self.csl.format_entry(item, style=style, index=index)

    def format_in_text(
        self,
        record_or_key: str | PublicationRecord | CSLItem,
        style: str = "apa",
        *,
        index: int = 1,
        page: str | None = None,
    ) -> str:
        """Format an in-text citation for a publication in the given CSL style."""
        return self.format_citation(record_or_key, style=style, citation_type="in_text", index=index, page=page)

    def format_all_styles(self, record_or_key: str | PublicationRecord) -> dict[str, str]:
        """Format a publication in all supported CSL styles simultaneously."""
        if isinstance(record_or_key, PublicationRecord):
            item = CSLItem.from_publication_record(record_or_key)
        else:
            rec = self.get(str(record_or_key))
            if not rec:
                return {}
            item = CSLItem.from_publication_record(rec)

        return {
            style: self.csl.format_entry(item, style=style)
            for style in self.csl.SUPPORTED_STYLES
        }

    def format_bibliography(
        self,
        records: list[PublicationRecord],
        style: str = "apa",
        *,
        output_format: str = "text",
    ) -> str:
        """Format a collection of records into a compiled bibliography list."""
        items = [CSLItem.from_publication_record(r) for r in records]
        return self.csl.format_bibliography(items, style=style, output_format=output_format)

    # =========================================================================
    # UPDATE
    # =========================================================================

    def update(self, cite_key: str, **fields: Any) -> PublicationRecord | None:
        """Update bibliographic fields of an existing publication."""
        return self.db.update(cite_key, **fields)

    # =========================================================================
    # DELETE
    # =========================================================================

    def delete(self, cite_key: str) -> bool:
        """Delete publication by cite_key and synchronize SQLite indexes."""
        return self.db.delete(cite_key)

    # =========================================================================
    # EXPORT
    # =========================================================================

    def export_bibliography(
        self,
        output_path: str | Path,
        *,
        style: str = "apa",
        output_format: str = "markdown",
        corpus: str | None = None,
        query: str | None = None,
        limit: int = 500,
    ) -> Path:
        """Export bibliography to a file formatted in the requested CSL style and format."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        records = self.list(corpus=corpus, query=query, limit=limit)
        content = self.format_bibliography(records, style=style, output_format=output_format)

        out.write_text(content, encoding="utf-8")
        logger.info("Exported {} references ({}, style={}) -> {}", len(records), output_format, style, out)
        return out

    # =========================================================================
    # Helpers
    # =========================================================================

    def _generate_cite_key(self, rec: PublicationRecord) -> str:
        lead_author = "Unknown"
        if rec.authors:
            parsed = Author.parse(rec.authors[0])
            lead_author = parsed.family or parsed.given or "Unknown"

        lead_author = re.sub(r"[^A-Za-z0-9]", "", lead_author).capitalize()
        year = str(rec.year) if rec.year else "nd"

        title_slug = ""
        if rec.title:
            words = [w for w in re.split(r"\W+", rec.title.lower()) if w and w not in ("the", "a", "an", "on", "of", "in")]
            title_slug = "".join(words[:3])

        base_key = f"{lead_author}{year}{title_slug}"
        if not base_key:
            base_key = f"Ref{year}"

        key = base_key
        counter = 1
        while self.get(key) is not None:
            counter += 1
            key = f"{base_key}{counter}"

        return key

    def _generate_cite_key_for_csl(self, item: CSLItem) -> str:
        lead_author = "Unknown"
        if item.author:
            lead_author = item.author[0].family or item.author[0].given or "Unknown"
        lead_author = re.sub(r"[^A-Za-z0-9]", "", lead_author).capitalize()
        year = str(item.issued_year) if item.issued_year else "nd"
        title_slug = "".join([w for w in re.split(r"\W+", item.title.lower()) if w][:3])
        return f"{lead_author}{year}{title_slug}"
