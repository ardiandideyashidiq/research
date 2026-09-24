from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from loguru import logger

from research.cards.export import export_cards_matrix
from research.cards.extractor import CardExtractor
from research.cards.models import ReviewCard
from research.db.models import PublicationRecord

if TYPE_CHECKING:
    from pathlib import Path

    from research.db.manager import DatabaseManager


class CardManager:
    """Manager for literature review cards, annotations, and matrix synthesis stored in SQLite."""

    def __init__(
        self,
        db: DatabaseManager,
        *,
        extractor: CardExtractor | None = None,
    ) -> None:
        self.db = db
        self.extractor = extractor or CardExtractor()
        self.init_cards_schema()

    def init_cards_schema(self) -> None:
        """Create review_cards table and full-text search virtual table if they don't exist."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS review_cards (
                card_id TEXT PRIMARY KEY,
                cite_key TEXT UNIQUE NOT NULL,
                corpus TEXT NOT NULL DEFAULT 'literature',
                title TEXT NOT NULL,
                authors TEXT,
                year INTEGER,
                venue TEXT,
                legal_issue TEXT,
                theory TEXT,
                methodology TEXT,
                findings TEXT,
                gap TEXT,
                positioning TEXT,
                tags TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (cite_key) REFERENCES publications(cite_key) ON DELETE CASCADE
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_cite_key ON review_cards(cite_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_corpus ON review_cards(corpus)")

        try:
            cursor.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS review_cards_fts USING fts5(
                    card_id UNINDEXED,
                    cite_key UNINDEXED,
                    title,
                    legal_issue,
                    theory,
                    findings,
                    gap,
                    positioning,
                    tags,
                    notes
                )
                """
            )
        except sqlite3.OperationalError:
            pass

        conn.commit()

    def save_card(self, card: ReviewCard) -> ReviewCard:
        """Insert or replace a literature review card into SQLite and sync to FTS5."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        now = datetime.now(UTC).isoformat()
        card.updated_at = now

        authors_json = json.dumps(card.authors, ensure_ascii=False)
        tags_json = json.dumps(card.tags, ensure_ascii=False)

        cursor.execute(
            """
            INSERT OR REPLACE INTO review_cards (
                card_id, cite_key, corpus, title, authors, year, venue,
                legal_issue, theory, methodology, findings, gap, positioning,
                tags, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                card.card_id,
                card.cite_key,
                card.corpus,
                card.title,
                authors_json,
                card.year,
                card.venue,
                card.legal_issue,
                card.theory,
                card.methodology,
                card.findings,
                card.gap,
                card.positioning,
                tags_json,
                card.notes,
                card.created_at,
                card.updated_at,
            ),
        )

        try:
            cursor.execute("DELETE FROM review_cards_fts WHERE cite_key = ?", (card.cite_key,))
            cursor.execute(
                """
                INSERT INTO review_cards_fts (
                    card_id, cite_key, title, legal_issue, theory,
                    findings, gap, positioning, tags, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card.card_id,
                    card.cite_key,
                    card.title,
                    card.legal_issue,
                    card.theory,
                    card.findings,
                    card.gap,
                    card.positioning,
                    " ".join(card.tags),
                    card.notes,
                ),
            )
        except sqlite3.OperationalError:
            pass

        conn.commit()
        logger.debug("Saved review card for '{}'", card.cite_key)
        return card

    def get_card(self, cite_key: str) -> ReviewCard | None:
        """Fetch a single review card by its cite_key."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM review_cards WHERE cite_key = ?", (cite_key,)).fetchone()
        if not row:
            return None
        return ReviewCard.from_row(dict(row))

    def update_card(self, cite_key: str, **fields: Any) -> ReviewCard | None:
        """Update specific fields of an existing review card."""
        card = self.get_card(cite_key)
        if not card:
            # Check if publication exists in DB to auto-initialize card
            pub = self.db.get(cite_key)
            if not pub:
                logger.warning("Cannot update card: publication '{}' not found in database.", cite_key)
                return None
            card = self.extractor.extract_from_record(pub)

        for k, v in fields.items():
            if hasattr(card, k) and v is not None:
                if k == "tags" and isinstance(v, str):
                    v = [t.strip() for t in v.split(",") if t.strip()]
                setattr(card, k, v)

        return self.save_card(card)

    def delete_card(self, cite_key: str) -> bool:
        """Delete a review card by cite_key."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM review_cards WHERE cite_key = ?", (cite_key,))
        deleted = cursor.rowcount > 0
        try:
            cursor.execute("DELETE FROM review_cards_fts WHERE cite_key = ?", (cite_key,))
        except sqlite3.OperationalError:
            pass
        conn.commit()
        return deleted

    def list_cards(
        self,
        *,
        corpus: str | None = None,
        tag: str | None = None,
        query: str | None = None,
        limit: int = 100,
    ) -> list[ReviewCard]:
        """List review cards with optional corpus, tag, or FTS keyword filtering."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        conditions = []
        params: list[Any] = []

        if corpus and corpus != "all":
            conditions.append("corpus = ?")
            params.append(corpus)

        if tag:
            conditions.append("tags LIKE ?")
            params.append(f"%{tag}%")

        if query:
            try:
                fts_sql = "SELECT cite_key FROM review_cards_fts WHERE review_cards_fts MATCH ?"
                matching_keys = [r[0] for r in cursor.execute(fts_sql, (f'"{query}"',)).fetchall()]
                if matching_keys:
                    placeholders = ",".join("?" for _ in matching_keys)
                    conditions.append(f"cite_key IN ({placeholders})")
                    params.extend(matching_keys)
                else:
                    conditions.append("(title LIKE ? OR legal_issue LIKE ? OR findings LIKE ?)")
                    patt = f"%{query}%"
                    params.extend([patt, patt, patt])
            except sqlite3.OperationalError:
                conditions.append("(title LIKE ? OR legal_issue LIKE ? OR findings LIKE ?)")
                patt = f"%{query}%"
                params.extend([patt, patt, patt])

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        sql = f"SELECT * FROM review_cards {where_clause} ORDER BY year DESC, updated_at DESC LIMIT ?"
        rows = cursor.execute(sql, params).fetchall()
        return [ReviewCard.from_row(dict(r)) for r in rows]

    def count_cards(self) -> dict[str, Any]:
        """Return count of review cards and breakdown by corpus."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        total = cursor.execute("SELECT COUNT(*) FROM review_cards").fetchone()[0]
        breakdown_rows = cursor.execute("SELECT corpus, COUNT(*) FROM review_cards GROUP BY corpus").fetchall()
        return {
            "total_cards": total,
            "corpus_breakdown": {r[0]: r[1] for r in breakdown_rows},
        }

    def extract_and_save(
        self,
        cite_key: str,
        *,
        force: bool = False,
    ) -> ReviewCard | None:
        """Extract and save literature review card for a specific publication."""
        if not force:
            existing = self.get_card(cite_key)
            if existing:
                return existing

        pub = self.db.get(cite_key)
        if not pub:
            logger.warning("Publication '{}' not found in database.", cite_key)
            return None

        card = self.extractor.extract_from_record(pub)
        return self.save_card(card)

    def batch_extract(
        self,
        *,
        corpus: str | None = None,
        force: bool = False,
        limit: int = 200,
        concurrency: int = 4,
    ) -> list[ReviewCard]:
        """Extract literature review cards for publications in the database using parallel workers."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Find existing card cite_keys
        existing_keys = set()
        if not force:
            rows = cursor.execute("SELECT cite_key FROM review_cards").fetchall()
            existing_keys = {r[0] for r in rows}

        conditions = ["1=1"]
        params: list[Any] = []

        if corpus and corpus != "all":
            if corpus == "putusan":
                conditions.append("(entry_type = 'putusan' OR cite_key LIKE 'Putusan_%')")
            elif corpus == "literature":
                conditions.append("entry_type != 'putusan' AND entry_type != 'online' AND cite_key NOT LIKE 'Putusan_%'")
            elif corpus == "web":
                conditions.append("entry_type = 'online'")

        where_clause = " AND ".join(conditions)
        sql = f"SELECT * FROM publications WHERE {where_clause} ORDER BY year DESC, title ASC LIMIT ?"
        params.append(limit)

        rows = cursor.execute(sql, params).fetchall()
        pubs = [PublicationRecord.from_row(dict(r)) for r in rows]
        results: list[ReviewCard] = []
        to_extract: list[PublicationRecord] = []

        for p in pubs:
            if not force and p.cite_key in existing_keys:
                card = self.get_card(p.cite_key)
                if card:
                    results.append(card)
            else:
                to_extract.append(p)

        if to_extract:
            def _worker(pub: PublicationRecord) -> ReviewCard | None:
                try:
                    c = self.extractor.extract_from_record(pub)
                    self.save_card(c)
                    return c
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed extracting review card for '{}': {}", pub.cite_key, exc)
                    return None

            with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
                futures = [executor.submit(_worker, pub) for pub in to_extract]
                for fut in as_completed(futures):
                    card_res = fut.result()
                    if card_res is not None:
                        results.append(card_res)

        logger.info("Batch extraction completed: processed {} review cards.", len(results))
        return results

    async def batch_extract_async(
        self,
        *,
        corpus: str | None = None,
        force: bool = False,
        limit: int = 200,
        concurrency: int = 4,
    ) -> list[ReviewCard]:
        """Asynchronously extract literature review cards using background thread pool."""
        import asyncio

        return await asyncio.to_thread(
            self.batch_extract,
            corpus=corpus,
            force=force,
            limit=limit,
            concurrency=concurrency,
        )

    def export_matrix(
        self,
        *,
        format: str = "markdown",
        output_path: str | Path | None = None,
        corpus: str | None = None,
        tag: str | None = None,
        limit: int = 500,
        include_details: bool = True,
    ) -> str:
        """Fetch matching cards and export as combined literature review matrix."""
        cards = self.list_cards(corpus=corpus, tag=tag, limit=limit)
        return export_cards_matrix(
            cards,
            format=format,
            output_path=output_path,
            include_details=include_details,
        )
