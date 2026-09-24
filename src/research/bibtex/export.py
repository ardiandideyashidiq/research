from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from research.bibtex.models import BibEntry


def export_to_json(
    entries: list[BibEntry],
    output_path: str | Path,
    *,
    indent: int = 2,
) -> Path:
    """Export BibEntry list to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = [entry.to_dict() for entry in entries]
    path.write_text(json.dumps(data, indent=indent, ensure_ascii=False), encoding="utf-8")
    return path


def export_to_sqlite(
    entries: list[BibEntry],
    db_path: str | Path,
    *,
    table_name: str = "publications",
    if_exists: str = "replace",
) -> Path:
    """Export BibEntry list to a SQLite database with full-text search enabled."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()

        if if_exists == "replace":
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}_fts")
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                cite_key TEXT PRIMARY KEY,
                entry_type TEXT NOT NULL,
                title TEXT NOT NULL,
                authors TEXT,
                journal TEXT,
                year INTEGER,
                volume TEXT,
                number TEXT,
                pages TEXT,
                doi TEXT,
                url TEXT,
                abstract TEXT,
                sources TEXT,
                raw_fields TEXT
            )
            """
        )

        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_year ON {table_name}(year)"
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_journal ON {table_name}(journal)"
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_doi ON {table_name}(doi)"
        )

        rows = []
        for e in entries:
            rows.append(
                (
                    e.cite_key,
                    e.entry_type,
                    e.title,
                    json.dumps(e.authors, ensure_ascii=False),
                    e.journal,
                    e.year,
                    e.volume,
                    e.number,
                    e.pages,
                    e.doi,
                    e.url,
                    e.abstract,
                    json.dumps(e.sources, ensure_ascii=False),
                    json.dumps(e.raw_fields, ensure_ascii=False),
                )
            )

        cursor.executemany(
            f"""
            INSERT OR REPLACE INTO {table_name} (
                cite_key, entry_type, title, authors, journal, year,
                volume, number, pages, doi, url, abstract, sources, raw_fields
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

        # Build Full-Text Search (FTS5) virtual table
        try:
            cursor.execute(
                f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS {table_name}_fts USING fts5(
                    cite_key UNINDEXED,
                    title,
                    authors,
                    journal,
                    abstract
                )
                """
            )
            fts_rows = [
                (
                    e.cite_key,
                    e.title,
                    ", ".join(e.authors),
                    e.journal or "",
                    e.abstract or "",
                )
                for e in entries
            ]
            cursor.executemany(
                f"""
                INSERT INTO {table_name}_fts (
                    cite_key, title, authors, journal, abstract
                ) VALUES (?, ?, ?, ?, ?)
                """,
                fts_rows,
            )
        except sqlite3.OperationalError:
            # FTS5 might not be compiled in some minimal SQLite environments
            pass

        conn.commit()

    return path
