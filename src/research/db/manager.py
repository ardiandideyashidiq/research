from __future__ import annotations

import json
import sqlite3
import threading
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
        self._local = threading.local()
        self._connections: list[sqlite3.Connection] = []
        self._lock = threading.Lock()
        self.init_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=60.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA busy_timeout = 60000")
            conn.execute("PRAGMA cache_size = -64000")
            self._local.conn = conn
            with self._lock:
                self._connections.append(conn)
        return conn

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
        with self._lock:
            for conn in self._connections:
                try:
                    conn.close()
                except sqlite3.Error as e:
                    logger.debug(f"Error closing DB connection: {e}")
            self._connections.clear()
        self._local = threading.local()

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
                raw_fields TEXT,
                markdown_path TEXT,
                is_chunked INTEGER NOT NULL DEFAULT 0
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
            "markdown_path": "TEXT",
            "is_chunked": "INTEGER NOT NULL DEFAULT 0",
        }
        for col_name, col_def in col_defs.items():
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE publications ADD COLUMN {col_name} {col_def}")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_year ON publications(year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_journal ON publications(journal)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_doi ON publications(doi)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_status ON publications(download_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_is_ojs ON publications(is_ojs)")

        # Create FTS5 virtual table for publications
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

        # Create chunks table and chunks_fts
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                cite_key TEXT NOT NULL,
                paper_title TEXT NOT NULL,
                section_title TEXT,
                section_level INTEGER,
                page_start INTEGER,
                page_end INTEGER,
                content TEXT NOT NULL,
                corpus TEXT NOT NULL DEFAULT 'literature',
                FOREIGN KEY (cite_key) REFERENCES publications(cite_key) ON DELETE CASCADE
            )
            """
        )
        # Auto-migrate corpus in chunks if missing
        chunk_cols = {row[1] for row in cursor.execute("PRAGMA table_info(chunks)").fetchall()}
        if "corpus" not in chunk_cols:
            cursor.execute("ALTER TABLE chunks ADD COLUMN corpus TEXT NOT NULL DEFAULT 'literature'")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_cite_key ON chunks(cite_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_corpus ON chunks(corpus)")

        # Create chunk_embeddings table for dense vectors
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chunk_embeddings (
                chunk_id TEXT PRIMARY KEY,
                embedding BLOB NOT NULL,
                FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id) ON DELETE CASCADE
            )
            """
        )

        try:
            cursor.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                    chunk_id UNINDEXED,
                    cite_key UNINDEXED,
                    paper_title,
                    section_title,
                    content
                )
                """
            )
        except sqlite3.OperationalError as e:
            logger.debug(f"chunks_fts already initialized or FTS5 error: {e}")

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
                file_size, file_hash, content_type, full_metadata, raw_fields,
                markdown_path, is_chunked
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                rec.markdown_path,
                1 if rec.is_chunked else 0,
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
            "full_metadata", "raw_fields", "markdown_path", "is_chunked",
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

    def insert_chunks(self, chunks: list[dict[str, Any]]) -> int:
        """Insert a batch of document chunks and sync to FTS5."""
        if not chunks:
            return 0
        conn = self.get_connection()
        cursor = conn.cursor()
        count = 0
        for c in chunks:
            corpus_val = c.get("corpus", "literature")
            cursor.execute(
                """
                INSERT OR REPLACE INTO chunks (
                    chunk_id, cite_key, paper_title, section_title,
                    section_level, page_start, page_end, content, corpus
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    c["chunk_id"],
                    c["cite_key"],
                    c["paper_title"],
                    c.get("section_title"),
                    c.get("section_level"),
                    c.get("page_start"),
                    c.get("page_end"),
                    c["content"],
                    corpus_val,
                ),
            )
            # Sync to chunks_fts
            cursor.execute(
                """
                INSERT OR REPLACE INTO chunks_fts(chunk_id, cite_key, paper_title, section_title, content)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    c["chunk_id"],
                    c["cite_key"],
                    c["paper_title"],
                    c.get("section_title") or "",
                    c["content"],
                ),
            )
            count += 1
        conn.commit()
        return count

    def delete_chunks(self, cite_key: str) -> int:
        """Delete all chunks and their embeddings for a publication."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM chunk_embeddings WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE cite_key = ?)",
            (cite_key,),
        )
        cursor.execute("DELETE FROM chunks WHERE cite_key = ?", (cite_key,))
        deleted = cursor.rowcount
        try:
            cursor.execute("DELETE FROM chunks_fts WHERE cite_key = ?", (cite_key,))
        except sqlite3.OperationalError:
            pass
        conn.commit()
        return deleted

    def save_chunk_embeddings(self, embeddings: dict[str, Any]) -> int:
        """Save binary float32 embeddings for chunks."""
        import array

        conn = self.get_connection()
        cursor = conn.cursor()
        count = 0
        for chunk_id, emb in embeddings.items():
            if hasattr(emb, "tobytes"):
                emb_bytes = emb.tobytes()
            elif isinstance(emb, (list, tuple)):
                emb_bytes = array.array("f", emb).tobytes()
            else:
                emb_bytes = bytes(emb)

            cursor.execute(
                "INSERT OR REPLACE INTO chunk_embeddings (chunk_id, embedding) VALUES (?, ?)",
                (chunk_id, emb_bytes),
            )
            count += 1
        conn.commit()
        return count

    def get_unembedded_chunks(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Return chunks that do not yet have an embedding in chunk_embeddings."""
        conn = self.get_connection()
        cursor = conn.cursor()
        sql = """
            SELECT c.chunk_id, c.content, c.paper_title, c.section_title
            FROM chunks c
            LEFT JOIN chunk_embeddings e ON c.chunk_id = e.chunk_id
            WHERE e.chunk_id IS NULL
        """
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        rows = cursor.execute(sql).fetchall()
        return [dict(r) for r in rows]

    def get_all_embeddings(
        self,
        *,
        corpus: str | None = None,
        cite_key: str | None = None,
    ) -> tuple[list[str], Any]:
        """Fetch all chunk IDs and their vector embeddings as a 2D float32 numpy array."""
        import numpy as np

        conn = self.get_connection()
        cursor = conn.cursor()

        conditions = []
        params = []
        if corpus and corpus != "all":
            conditions.append("c.corpus = ?")
            params.append(corpus)
        if cite_key:
            conditions.append("c.cite_key = ?")
            params.append(cite_key)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        sql = f"""
            SELECT e.chunk_id, e.embedding
            FROM chunk_embeddings e
            JOIN chunks c ON e.chunk_id = c.chunk_id
            {where_clause}
        """
        rows = cursor.execute(sql, params).fetchall()
        if not rows:
            return [], np.empty((0, 0), dtype=np.float32)

        chunk_ids = [r[0] for r in rows]
        all_bytes = b"".join(r[1] for r in rows)
        dim = len(rows[0][1]) // 4
        matrix = np.frombuffer(all_bytes, dtype=np.float32).reshape(len(rows), dim)
        return chunk_ids, matrix

    def get_chunks_by_ids(self, chunk_ids: list[str]) -> dict[str, dict[str, Any]]:
        """Fetch chunk metadata and content for a list of chunk IDs."""
        if not chunk_ids:
            return {}
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in chunk_ids)
        rows = cursor.execute(
            f"SELECT * FROM chunks WHERE chunk_id IN ({placeholders})",
            chunk_ids,
        ).fetchall()
        return {r["chunk_id"]: dict(r) for r in rows}

    def search_chunks(
        self,
        query: str,
        *,
        limit: int = 10,
        cite_key: str | None = None,
        corpus: str | None = None,
    ) -> list[dict[str, Any]]:
        """Full-text search across all indexed chunks using FTS5 BM25 ranking with optional corpus filter."""
        conn = self.get_connection()
        cursor = conn.cursor()

        conditions = []
        params: list[Any] = [query]
        if cite_key:
            conditions.append("c.cite_key = ?")
            params.append(cite_key)
        if corpus and corpus != "all":
            conditions.append("c.corpus = ?")
            params.append(corpus)

        where_extra = f"AND {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        try:
            sql = f"""
                SELECT c.*, bm25(chunks_fts) as rank
                FROM chunks c
                JOIN chunks_fts f ON c.chunk_id = f.chunk_id
                WHERE chunks_fts MATCH ? {where_extra}
                ORDER BY rank
                LIMIT ?
            """
            rows = cursor.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.OperationalError:
            pattern = f"%{query}%"
            fallback_conditions = ["(c.content LIKE ? OR c.section_title LIKE ? OR c.paper_title LIKE ?)"]
            fallback_params: list[Any] = [pattern, pattern, pattern]
            if cite_key:
                fallback_conditions.append("c.cite_key = ?")
                fallback_params.append(cite_key)
            if corpus and corpus != "all":
                fallback_conditions.append("c.corpus = ?")
                fallback_params.append(corpus)
            fallback_params.append(limit)

            sql = f"""
                SELECT c.*, 0.0 as rank FROM chunks c
                WHERE {' AND '.join(fallback_conditions)}
                LIMIT ?
            """
            cursor.execute(sql, fallback_params)
            return [dict(r) for r in cursor.fetchall()]

    def get_stats(self) -> dict[str, Any]:
        """Return high-level summary counts of database contents."""
        conn = self.get_connection()
        cursor = conn.cursor()
        total_pubs = cursor.execute("SELECT COUNT(*) FROM publications").fetchone()[0]
        downloaded = cursor.execute(
            "SELECT COUNT(*) FROM publications WHERE download_status = 'downloaded'"
        ).fetchone()[0]
        converted = cursor.execute(
            "SELECT COUNT(*) FROM publications WHERE markdown_path IS NOT NULL"
        ).fetchone()[0]
        total_chunks = cursor.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        total_embeddings = 0
        try:
            total_embeddings = cursor.execute("SELECT COUNT(*) FROM chunk_embeddings").fetchone()[0]
        except sqlite3.OperationalError:
            pass

        corpus_breakdown = {}
        try:
            c_rows = cursor.execute("SELECT corpus, COUNT(*) FROM chunks GROUP BY corpus").fetchall()
            corpus_breakdown = {r[0]: r[1] for r in c_rows}
        except sqlite3.OperationalError:
            pass

        return {
            "total_publications": total_pubs,
            "downloaded": downloaded,
            "converted": converted,
            "total_chunks": total_chunks,
            "total_embeddings": total_embeddings,
            "corpus_breakdown": corpus_breakdown,
        }
