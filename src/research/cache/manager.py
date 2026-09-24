from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import threading
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import TracebackType
from typing import Any, Self, TypeVar

from loguru import logger

from research.cache.models import CachedResponse, CachePolicy

T = TypeVar("T")


def compute_url_hash(url: str, method: str = "GET") -> str:
    """Compute deterministic SHA-256 hash for a URL and method."""
    norm_url = url.strip()
    key = f"{method.upper()}:{norm_url}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


class HttpCache:
    """Persistent, thread-safe, and async-safe SQLite-backed HTTP & web page cache."""

    def __init__(
        self,
        db_path: str | Path = "tmp/publications.sqlite",
        *,
        policy: CachePolicy | None = None,
    ) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.policy = policy or CachePolicy()
        self._local = threading.local()
        self._connections: list[sqlite3.Connection] = []
        self._lock = threading.Lock()
        self._in_flight: dict[str, asyncio.Future[Any]] = {}
        self._in_flight_lock: asyncio.Lock | None = None
        self.init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=60.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA busy_timeout = 60000")
            self._local.conn = conn
            with self._lock:
                self._connections.append(conn)
        return conn

    def init_schema(self) -> None:
        """Create cache tables and indices if not present."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS http_cache (
                url_hash TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                method TEXT NOT NULL DEFAULT 'GET',
                status_code INTEGER NOT NULL,
                headers TEXT,
                content BLOB,
                content_type TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_url ON http_cache(url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON http_cache(expires_at)")
        conn.commit()

    def get(self, url: str, *, method: str = "GET") -> CachedResponse | None:
        """Retrieve a valid cached response by URL and method."""
        if not self.policy.enabled:
            return None

        url_hash = compute_url_hash(url, method=method)
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT url, status_code, content, content_type, headers, created_at, expires_at
            FROM http_cache WHERE url_hash = ?
            """,
            (url_hash,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        expires_at = row["expires_at"]
        if expires_at:
            try:
                exp_dt = datetime.fromisoformat(expires_at)
                if datetime.now(UTC) > exp_dt:
                    # Expired, clean up and return None
                    self.delete(url, method=method)
                    return None
            except (ValueError, TypeError) as exc:
                logger.debug(f"Failed to parse cache expires_at '{expires_at}': {exc}")

        headers_dict: dict[str, str] = {}
        if row["headers"]:
            try:
                headers_dict = json.loads(row["headers"])
            except (json.JSONDecodeError, TypeError) as exc:
                logger.debug(f"Failed to decode cached headers: {exc}")
                headers_dict = {}

        raw_content = row["content"]
        content_bytes = raw_content if isinstance(raw_content, bytes) else (raw_content or "").encode("utf-8")

        return CachedResponse(
            url=row["url"],
            status_code=row["status_code"],
            content=content_bytes,
            content_type=row["content_type"] or "text/html",
            headers=headers_dict,
            created_at=row["created_at"],
            expires_at=expires_at,
            from_cache=True,
        )

    def set(
        self,
        url: str,
        status_code: int,
        content: bytes | str,
        *,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        content_type: str = "text/html",
        ttl: float | None = None,
    ) -> CachedResponse:
        """Store a response in cache with optional TTL."""
        if not self.policy.enabled:
            content_bytes = content if isinstance(content, bytes) else content.encode("utf-8")
            return CachedResponse(
                url=url,
                status_code=status_code,
                content=content_bytes,
                content_type=content_type,
                headers=headers or {},
                from_cache=False,
            )

        url_hash = compute_url_hash(url, method=method)
        content_bytes = content if isinstance(content, bytes) else content.encode("utf-8")
        headers_json = json.dumps(headers or {}, ensure_ascii=False)
        now_dt = datetime.now(UTC)
        created_at = now_dt.isoformat()

        # Compute expiration time
        expires_at: str | None = None
        effective_ttl = ttl
        if effective_ttl is None:
            if status_code >= 400:
                effective_ttl = self.policy.negative_ttl
            else:
                effective_ttl = self.policy.default_ttl

        if effective_ttl is not None:
            expires_at = (now_dt + timedelta(seconds=effective_ttl)).isoformat()

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO http_cache (
                url_hash, url, method, status_code, headers, content, content_type, created_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                url_hash,
                url.strip(),
                method.upper(),
                status_code,
                headers_json,
                content_bytes,
                content_type,
                created_at,
                expires_at,
            ),
        )
        conn.commit()

        return CachedResponse(
            url=url,
            status_code=status_code,
            content=content_bytes,
            content_type=content_type,
            headers=headers or {},
            created_at=created_at,
            expires_at=expires_at,
            from_cache=False,
        )

    def delete(self, url: str, *, method: str = "GET") -> bool:
        """Remove a cached URL."""
        url_hash = compute_url_hash(url, method=method)
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM http_cache WHERE url_hash = ?", (url_hash,))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted

    def clear(self, *, expired_only: bool = False) -> int:
        """Purge cache entries. If expired_only is True, deletes only expired entries."""
        conn = self._get_connection()
        cursor = conn.cursor()
        if expired_only:
            now_str = datetime.now(UTC).isoformat()
            cursor.execute("DELETE FROM http_cache WHERE expires_at IS NOT NULL AND expires_at < ?", (now_str,))
        else:
            cursor.execute("DELETE FROM http_cache")
        count = cursor.rowcount
        conn.commit()
        return count

    def stats(self) -> dict[str, Any]:
        """Return cache health and storage statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now_str = datetime.now(UTC).isoformat()

        total = cursor.execute("SELECT COUNT(*) FROM http_cache").fetchone()[0]
        expired = cursor.execute(
            "SELECT COUNT(*) FROM http_cache WHERE expires_at IS NOT NULL AND expires_at < ?",
            (now_str,),
        ).fetchone()[0]
        active = total - expired
        total_bytes = cursor.execute("SELECT TOTAL(LENGTH(content)) FROM http_cache").fetchone()[0]

        return {
            "total_cached": total,
            "active_cached": active,
            "expired_cached": expired,
            "total_bytes": int(total_bytes or 0),
        }

    async def coalesce_async(
        self,
        key: str,
        fetch_coro: Callable[[], Coroutine[Any, Any, T]],
    ) -> T:
        """In-flight single-flight lock ensuring only one network request runs for key."""
        if self._in_flight_lock is None:
            self._in_flight_lock = asyncio.Lock()

        async with self._in_flight_lock:
            if key in self._in_flight:
                future = self._in_flight[key]
                # Await in-flight future outside the lock
                return await future

            loop = asyncio.get_running_loop()
            future = loop.create_future()
            self._in_flight[key] = future

        try:
            res = await fetch_coro()
            future.set_result(res)
            return res
        except BaseException as exc:
            future.set_exception(exc)
            raise
        finally:
            async with self._in_flight_lock:
                self._in_flight.pop(key, None)

    def close(self) -> None:
        """Close SQLite connections for current thread/manager."""
        with self._lock:
            for conn in self._connections:
                try:
                    conn.close()
                except sqlite3.Error as e:
                    logger.debug(f"Error closing cache DB: {e}")
            self._connections.clear()
        self._local = threading.local()

    def __enter__(self) -> Self:
        self._get_connection()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()
