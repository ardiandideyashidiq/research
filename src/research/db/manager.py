from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from types import TracebackType
from typing import Any, Self

from loguru import logger

from research.db.models import PublicationRecord


class DatabaseManager:
    """Full CRUD manager for publication records in SQLite with full-text search."""

    def __init__(self, db_path: str | Path = "tmp/publications.sqlite") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self.init_schema()

    def get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def __enter__(self) -> Self:
        self.get_connection()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except sqlite3.Error as e:
                logger.debug(f"Error closing DB connection: {e}")
            finally:
                self._conn = None

    def init_schema(self) -> None:
        """Create tables and FTS virtual table if they don't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS publications (
                cite_key TEXT PRIMARY KEY,
                entry_type TEXT NOT NULL DEFAULT 'article',
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
                pdf_url TEXT,
                is_ojs INTEGER,
                download_status TEXT NOT NULL DEFAULT 'pending',
                download_path TEXT,
                download_error TEXT,
                downloaded_at TEXT,
                file_size INTEGER,
                file_hash TEXT,
                content_type TEXT,
                full_metadata TEXT,
                raw_fields TEXT
            )
            """
        )

        # Auto-migrate missing columns for existing tables
        existing_cols = {row[1] for row in cursor.execute("PRAGMA table_info(publications)").fetchall()}
        col_defs = {
            "entry_type": "TEXT NOT NULL DEFAULT 'article'",
            "title": "TEXT NOT NULL DEFAULT ''",
            "authors": "TEXT",
            "journal": "TEXT",
            "year": "INTEGER",
            "volume": "TEXT",
            "number": "TEXT",
            "pages": "TEXT",
            "doi": "TEXT",
            "url": "TEXT",
            "abstract": "TEXT",
            "sources": "TEXT",
            "pdf_url": "TEXT",
            "is_ojs": "INTEGER",
            "download_status": "TEXT NOT NULL DEFAULT 'pending'",
            "download_path": "TEXT",
            "download_error": "TEXT",
            "downloaded_at": "TEXT",
            "file_size": "INTEGER",
            "file_hash": "TEXT",
            "content_type": "TEXT",
            "full_metadata": "TEXT",
            "raw_fields": "TEXT",
        }
        for col_name, col_def in col_defs.items():
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE publications ADD COLUMN {col_name} {col_def}")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_year ON publications(year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_journal ON publications(journal)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_doi ON publications(doi)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_status ON publications(download_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_is_ojs ON publications(is_ojs)")

        # Create FTS5 virtual table
        try:
            cursor.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS publications_fts USING fts5(
                    cite_key UNINDEXED,
                    title,
                    authors,
                    journal,
                    abstract,
                    content='publications',
                    content_rowid='rowid'
                )
                """
            )
        except sqlite3.OperationalError as e:
            logger.debug(f"FTS5 not enabled or already initialized: {e}")

        conn.commit()

    def _sync_fts_entry(self, cite_key: str) -> None:
        """Sync a single entry to FTS5."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            row = cursor.execute(
                "SELECT rowid, cite_key, title, authors, journal, abstract FROM publications WHERE cite_key = ?",
                (cite_key,),
            ).fetchone()
            if row:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO publications_fts(rowid, cite_key, title, authors, journal, abstract)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (row["rowid"], row["cite_key"], row["title"], row["authors"], row["journal"] or "", row["abstract"] or ""),
                )
            else:
                cursor.execute("DELETE FROM publications_fts WHERE cite_key = ?", (cite_key,))
            conn.commit()
        except sqlite3.OperationalError:
            pass

    def create(self, record: PublicationRecord | dict[str, Any]) -> PublicationRecord:
        """Insert or replace a publication record (Create)."""
        if isinstance(record, dict):
            rec = PublicationRecord.from_row(record)
        else:
            rec = record

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO publications (
                cite_key, entry_type, title, authors, journal, year, volume,
                number, pages, doi, url, abstract, sources, pdf_url, is_ojs,
                download_status, download_path, download_error, downloaded_at,
                file_size, file_hash, content_type, full_metadata, raw_fields
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rec.cite_key,
                rec.entry_type,
                rec.title,
                json.dumps(rec.authors, ensure_ascii=False),
                rec.journal,
                rec.year,
                rec.volume,
                rec.number,
                rec.pages,
                rec.doi,
                rec.url,
                rec.abstract,
                json.dumps(rec.sources, ensure_ascii=False),
                rec.pdf_url,
                1 if rec.is_ojs else (0 if rec.is_ojs is False else None),
                rec.download_status,
                rec.download_path,
                rec.download_error,
                rec.downloaded_at,
                rec.file_size,
                rec.file_hash,
                rec.content_type,
                json.dumps(rec.full_metadata, ensure_ascii=False),
                json.dumps(rec.raw_fields, ensure_ascii=False),
            ),
        )
        conn.commit()
        self._sync_fts_entry(rec.cite_key)
        return rec

    def create_many(self, records: list[PublicationRecord | dict[str, Any]]) -> int:
        """Batch insert or replace records."""
        count = 0
        for r in records:
            self.create(r)
            count += 1
        return count

    def get(self, cite_key: str) -> PublicationRecord | None:
        """Fetch a single record by cite_key (Read)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM publications WHERE cite_key = ?", (cite_key,))
        row = cursor.fetchone()
        if not row:
            return None
        return PublicationRecord.from_row(dict(row))

    def list(
        self,
        *,
        status: str | None = None,
        is_ojs: bool | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[PublicationRecord]:
        """List records with optional filtering (Read)."""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM publications WHERE 1=1"
        params: list[Any] = []

        if status is not None:
            query += " AND download_status = ?"
            params.append(status)

        if is_ojs is not None:
            query += " AND is_ojs = ?"
            params.append(1 if is_ojs else 0)

        query += " ORDER BY year DESC, title ASC"

        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [PublicationRecord.from_row(dict(r)) for r in rows]

    def search(self, query: str, *, limit: int = 50) -> list[PublicationRecord]:
        """Search records using full-text search (Read)."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT p.* FROM publications p
                JOIN publications_fts f ON p.cite_key = f.cite_key
                WHERE publications_fts MATCH ?
                LIMIT ?
                """,
                (query, limit),
            )
            rows = cursor.fetchall()
            return [PublicationRecord.from_row(dict(r)) for r in rows]
        except sqlite3.OperationalError:
            # Fallback to LIKE if FTS is unavailable
            pattern = f"%{query}%"
            cursor.execute(
                """
                SELECT * FROM publications
                WHERE title LIKE ? OR abstract LIKE ? OR authors LIKE ?
                LIMIT ?
                """,
                (pattern, pattern, pattern, limit),
            )
            rows = cursor.fetchall()
            return [PublicationRecord.from_row(dict(r)) for r in rows]

    def update(self, cite_key: str, **fields: Any) -> PublicationRecord | None:
        """Update specific fields of an existing record (Update)."""
        record = self.get(cite_key)
        if not record:
            return None

        conn = self.get_connection()
        cursor = conn.cursor()

        allowed_fields = {
            "title", "authors", "journal", "year", "volume", "number",
            "pages", "doi", "url", "abstract", "sources", "pdf_url",
            "is_ojs", "download_status", "download_path", "download_error",
            "downloaded_at", "file_size", "file_hash", "content_type",
            "full_metadata", "raw_fields",
        }

        set_clauses: list[str] = []
        values: list[Any] = []

        for k, v in fields.items():
            if k not in allowed_fields:
                continue
            set_clauses.append(f"{k} = ?")
            if k in {"authors", "sources", "full_metadata", "raw_fields"} and not isinstance(v, str):
                values.append(json.dumps(v, ensure_ascii=False))
            elif k == "is_ojs" and v is not None:
                values.append(1 if v else 0)
            else:
                values.append(v)

        if not set_clauses:
            return record

        values.append(cite_key)
        sql = f"UPDATE publications SET {', '.join(set_clauses)} WHERE cite_key = ?"
        cursor.execute(sql, values)
        conn.commit()

        self._sync_fts_entry(cite_key)
        return self.get(cite_key)

    def update_status(
        self,
        cite_key: str,
        status: str,
        *,
        error: str | None = None,
        path: str | None = None,
        size: int | None = None,
        file_hash: str | None = None,
        content_type: str | None = None,
        downloaded_at: str | None = None,
    ) -> PublicationRecord | None:
        """Convenience method to update download state."""
        updates: dict[str, Any] = {"download_status": status}
        if error is not None:
            updates["download_error"] = error
        if path is not None:
            updates["download_path"] = path
        if size is not None:
            updates["file_size"] = size
        if file_hash is not None:
            updates["file_hash"] = file_hash
        if content_type is not None:
            updates["content_type"] = content_type
        if downloaded_at is not None:
            updates["downloaded_at"] = downloaded_at

        return self.update(cite_key, **updates)

    def delete(self, cite_key: str) -> bool:
        """Delete a record by cite_key (Delete)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM publications WHERE cite_key = ?", (cite_key,))
        deleted = cursor.rowcount > 0
        conn.commit()
        if deleted:
            try:
                cursor.execute("DELETE FROM publications_fts WHERE cite_key = ?", (cite_key,))
                conn.commit()
            except sqlite3.OperationalError:
                pass
        return deleted

    def delete_all(self) -> int:
        """Clear all records."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM publications")
        count = cursor.rowcount
        try:
            cursor.execute("DELETE FROM publications_fts")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        return count

    def count(self, *, status: str | None = None) -> int:
        """Count publications, optionally filtered by download_status."""
        conn = self.get_connection()
        cursor = conn.cursor()
        if status is not None:
            cursor.execute("SELECT COUNT(*) FROM publications WHERE download_status = ?", (status,))
        else:
            cursor.execute("SELECT COUNT(*) FROM publications")
        return cursor.fetchone()[0]

    def get_status_summary(self) -> dict[str, int]:
        """Return counts broken down by download_status."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT download_status, COUNT(*) FROM publications GROUP BY download_status")
        return dict(cursor.fetchall())
