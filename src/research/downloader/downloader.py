from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import httpx
from curl_cffi.requests import AsyncSession
from loguru import logger

from research.cache.manager import HttpCache
from research.db.manager import DatabaseManager
from research.db.models import PublicationRecord
from research.downloader.verifier import (
    classify_error,
    compute_file_hash,
    inspect_content,
)
from research.ojs.client import OJSClient

EngineType = Literal["curl_cffi", "httpx"]


class DownloadManager:
    """Parallel publication downloader with multi-tier deduplication and caching."""

    def __init__(
        self,
        db: DatabaseManager,
        *,
        download_dir: str | Path = "data/downloads",
        concurrency: int = 4,
        timeout: float = 10.0,
        retries: int = 1,
        engine: EngineType = "curl_cffi",
        cache: HttpCache | None = None,
    ) -> None:
        self.db = db
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.concurrency = concurrency
        self.timeout = timeout
        self.retries = retries
        self.engine = engine
        self.cache = cache
        self._in_flight: dict[str, asyncio.Future[PublicationRecord]] = {}
        self._download_lock: asyncio.Lock | None = None

    async def _execute_download(
        self,
        record: PublicationRecord,
        target_url: str,
        *,
        session: Any,
        ojs_client: OJSClient | None = None,
    ) -> PublicationRecord:
        """Internal worker executing HTTP request and verifying PDF magic bytes."""
        last_status_code: int | None = None
        last_exc: Exception | None = None
        content_bytes: bytes | None = None
        current_url = target_url

        # Execute download with retries and fallback checks
        for attempt in range(self.retries + 1):
            try:
                if isinstance(session, httpx.AsyncClient):
                    resp = await session.get(current_url, timeout=self.timeout)
                else:
                    resp = await session.get(
                        current_url,
                        timeout=self.timeout,
                        allow_redirects=True,
                    )
                last_status_code = resp.status_code

                if resp.status_code == 200:
                    content_bytes = resp.content
                    break

                # If 404, check if landing page has alternative galley before giving up
                if resp.status_code == 404 and record.url and current_url != record.url and attempt == 0:
                    client = ojs_client or OJSClient(engine=self.engine, cache=self.cache)
                    meta = await client.fetch_metadata(record.url, timeout=min(self.timeout, 8.0))
                    if meta.pdf_url and meta.pdf_url != current_url:
                        logger.info(f"Retrying {record.cite_key} with alternative galley: {meta.pdf_url}")
                        current_url = meta.pdf_url
                        continue

            except Exception as exc:  # noqa: BLE001 - capture all connection/curl errors
                last_exc = exc
                if attempt < self.retries:
                    await asyncio.sleep(1.0 * (attempt + 1))

        # Handle failure cases
        if content_bytes is None or last_status_code != 200:
            if self.cache is not None:
                self.cache.set(
                    target_url,
                    last_status_code or 500,
                    b"",
                    content_type="text/plain",
                    ttl=self.cache.policy.negative_ttl,
                )

            status_name, diagnostic = classify_error(last_status_code, last_exc, current_url)
            logger.warning(f"Download failed for {record.cite_key} -> {status_name}: {diagnostic}")
            updated = self.db.update_status(
                record.cite_key,
                status_name,
                error=diagnostic,
            )
            return updated or record

        # Inspect content to prevent false positives (e.g. 200 OK returning HTML error page)
        is_pdf, content_type = inspect_content(content_bytes)

        if not is_pdf:
            if "word" in content_type:
                # Microsoft Word document
                ext = ".docx" if "openxml" in content_type else ".doc"
                dest_path = self.download_dir / f"{record.cite_key}{ext}"
                dest_path.write_bytes(content_bytes)
                file_hash = compute_file_hash(content_bytes)
                now_str = datetime.now(UTC).isoformat()

                logger.info(f"{record.cite_key}: Word document saved to {dest_path}")
                updated = self.db.update_status(
                    record.cite_key,
                    "unsupported_format",
                    path=str(dest_path),
                    size=len(content_bytes),
                    file_hash=file_hash,
                    content_type=content_type,
                    downloaded_at=now_str,
                    error=f"Downloaded file is {content_type}, not PDF",
                )
                return updated or record

            # HTML returned instead of PDF (paywall or captcha)
            if self.cache is not None:
                self.cache.set(
                    target_url,
                    200,
                    content_bytes[:2048],
                    content_type=content_type,
                    ttl=self.cache.policy.negative_ttl,
                )

            err_msg = f"Server returned {content_type} (likely a paywall, captcha, or soft-error page) instead of PDF"
            logger.warning(f"{record.cite_key}: {err_msg}")
            updated = self.db.update_status(
                record.cite_key,
                "failed_not_pdf",
                error=err_msg,
                content_type=content_type,
                size=len(content_bytes),
            )
            return updated or record

        # Verified valid PDF! Compute content hash
        file_hash = compute_file_hash(content_bytes)
        now_str = datetime.now(UTC).isoformat()

        # Tier 7: Content Hash Deduplication
        existing_hash_rec = self.db.get_by_file_hash(file_hash)
        if existing_hash_rec and existing_hash_rec.download_path and Path(existing_hash_rec.download_path).is_file():
            dest_path = Path(existing_hash_rec.download_path)
            logger.info(
                f"{record.cite_key}: Content hash matches existing file from {existing_hash_rec.cite_key}: {dest_path}"
            )
        else:
            dest_path = self.download_dir / f"{record.cite_key}.pdf"
            dest_path.write_bytes(content_bytes)

        if self.cache is not None:
            self.cache.set(
                target_url,
                200,
                content_bytes[:2048],
                content_type="application/pdf",
            )

        logger.success(f"{record.cite_key}: Downloaded PDF ({len(content_bytes):,} bytes) -> {dest_path}")
        updated = self.db.update_status(
            record.cite_key,
            "downloaded",
            path=str(dest_path),
            size=len(content_bytes),
            file_hash=file_hash,
            content_type="application/pdf",
            downloaded_at=now_str,
            error=None,
        )
        return updated or record

    async def download_record(
        self,
        record: PublicationRecord,
        *,
        session: Any,
        ojs_client: OJSClient | None = None,
        force: bool = False,
    ) -> PublicationRecord:
        """Download and verify a single publication record with multi-tier deduplication."""
        # Tier 0: Database check for existing state (already downloaded or known failure)
        if not force:
            db_rec = self.db.get(record.cite_key)
            if db_rec:
                if db_rec.download_status == "downloaded" and db_rec.download_path:
                    local_path = Path(db_rec.download_path)
                    if local_path.is_file() and local_path.stat().st_size > 0:
                        logger.debug(f"Paper {record.cite_key} already downloaded at {local_path}. Skipping.")
                        return db_rec
                elif db_rec.download_status in (
                    "no_pdf_found",
                    "failed_not_pdf",
                    "failed_blocked",
                    "unsupported_format",
                    "dead_link",
                ):
                    logger.info(
                        f"Paper {record.cite_key}: Skipping previously verified unavailable PDF (status: {db_rec.download_status})"
                    )
                    return db_rec

        # Tier 1: Check if this record is already downloaded on disk
        if not force and record.download_status == "downloaded" and record.download_path:
            local_path = Path(record.download_path)
            if local_path.is_file() and local_path.stat().st_size > 0:
                logger.debug(f"Paper {record.cite_key} already downloaded at {local_path}. Skipping.")
                return record

        # Tier 2: Cross-record DOI lookup - check if ANY record with this DOI is downloaded
        if not force and record.doi:
            existing_doi_rec = self.db.get_by_doi(record.doi)
            if (
                existing_doi_rec
                and existing_doi_rec.cite_key != record.cite_key
                and existing_doi_rec.download_status == "downloaded"
                and existing_doi_rec.download_path
            ):
                local_path = Path(existing_doi_rec.download_path)
                if local_path.is_file() and local_path.stat().st_size > 0:
                    logger.info(
                        f"Paper {record.cite_key}: Reusing already downloaded file from {existing_doi_rec.cite_key} (DOI {record.doi}): {local_path}"
                    )
                    updated = self.db.update_status(
                        record.cite_key,
                        "downloaded",
                        path=str(local_path),
                        size=existing_doi_rec.file_size or local_path.stat().st_size,
                        file_hash=existing_doi_rec.file_hash,
                        content_type=existing_doi_rec.content_type or "application/pdf",
                        downloaded_at=existing_doi_rec.downloaded_at or datetime.now(UTC).isoformat(),
                    )
                    return updated or record

        # Tier 3: Pre-existing valid file on disk by cite_key
        if not force:
            candidate_file = self.download_dir / f"{record.cite_key}.pdf"
            if candidate_file.is_file() and candidate_file.stat().st_size > 0:
                content_bytes = candidate_file.read_bytes()
                is_pdf, content_type = inspect_content(content_bytes)
                if is_pdf:
                    file_hash = compute_file_hash(content_bytes)
                    logger.info(f"Paper {record.cite_key}: Found existing valid PDF file on disk: {candidate_file}")
                    updated = self.db.update_status(
                        record.cite_key,
                        "downloaded",
                        path=str(candidate_file),
                        size=len(content_bytes),
                        file_hash=file_hash,
                        content_type=content_type,
                        downloaded_at=datetime.now(UTC).isoformat(),
                    )
                    return updated or record

        # Determine target PDF URL
        pdf_url = record.pdf_url

        # If pdf_url is missing, attempt to extract via OJS client if URL exists
        if not pdf_url and record.url:
            client = ojs_client or OJSClient(engine=self.engine, cache=self.cache)
            try:
                ojs_meta = await client.fetch_metadata(record.url, timeout=min(self.timeout, 8.0))
                if ojs_meta.is_ojs:
                    self.db.update(record.cite_key, is_ojs=True)
                    record.is_ojs = True
                if ojs_meta.pdf_url:
                    pdf_url = ojs_meta.pdf_url
                    self.db.update(record.cite_key, pdf_url=pdf_url)
                    record.pdf_url = pdf_url
            except Exception as e:  # noqa: BLE001 - catch all network/extraction errors
                logger.debug(f"Could not extract OJS metadata for {record.cite_key}: {e}")

        if not pdf_url:
            err_msg = "No direct PDF download URL available on record or landing page"
            logger.info(f"{record.cite_key}: {err_msg}")
            updated = self.db.update_status(record.cite_key, "no_pdf_found", error=err_msg)
            return updated or record

        target_url = pdf_url

        # Tier 4: Cross-record Target URL lookup - check if ANY record with this URL is downloaded
        if not force:
            existing_url_rec = self.db.get_by_pdf_url(target_url)
            if (
                existing_url_rec
                and existing_url_rec.cite_key != record.cite_key
                and existing_url_rec.download_status == "downloaded"
                and existing_url_rec.download_path
            ):
                local_path = Path(existing_url_rec.download_path)
                if local_path.is_file() and local_path.stat().st_size > 0:
                    logger.info(
                        f"Paper {record.cite_key}: Reusing already downloaded file from {existing_url_rec.cite_key} (URL {target_url})"
                    )
                    updated = self.db.update_status(
                        record.cite_key,
                        "downloaded",
                        path=str(local_path),
                        size=existing_url_rec.file_size or local_path.stat().st_size,
                        file_hash=existing_url_rec.file_hash,
                        content_type=existing_url_rec.content_type or "application/pdf",
                        downloaded_at=existing_url_rec.downloaded_at or datetime.now(UTC).isoformat(),
                    )
                    return updated or record

        # Tier 5: Negative cache check
        if not force and self.cache is not None:
            cached_err = self.cache.get(target_url)
            if cached_err is not None and cached_err.status_code >= 400:
                err_msg = f"Skipping known dead URL (cached HTTP {cached_err.status_code}): {target_url}"
                logger.info(f"{record.cite_key}: {err_msg}")
                updated = self.db.update_status(record.cite_key, "dead_link", error=err_msg)
                return updated or record

        # Tier 6: In-Flight download coalescing
        if self._download_lock is None:
            self._download_lock = asyncio.Lock()

        async with self._download_lock:
            if target_url in self._in_flight:
                peer_future = self._in_flight[target_url]
                logger.info(f"{record.cite_key}: Awaiting concurrent in-flight download for {target_url}")
                peer_rec = await peer_future
                if peer_rec.download_status == "downloaded" and peer_rec.download_path:
                    updated = self.db.update_status(
                        record.cite_key,
                        "downloaded",
                        path=peer_rec.download_path,
                        size=peer_rec.file_size,
                        file_hash=peer_rec.file_hash,
                        content_type=peer_rec.content_type,
                        downloaded_at=peer_rec.downloaded_at or datetime.now(UTC).isoformat(),
                    )
                    return updated or record
                return self.db.get(record.cite_key) or record

            loop = asyncio.get_running_loop()
            future = loop.create_future()
            self._in_flight[target_url] = future

        # Mark in-progress
        self.db.update_status(record.cite_key, "downloading")

        try:
            result = await self._execute_download(
                record=record,
                target_url=target_url,
                session=session,
                ojs_client=ojs_client,
            )
            future.set_result(result)
            return result
        except BaseException as exc:
            future.set_exception(exc)
            raise
        finally:
            async with self._download_lock:
                self._in_flight.pop(target_url, None)

    async def download_stream(
        self,
        in_queue: asyncio.Queue[PublicationRecord | None],
        out_queue: asyncio.Queue[PublicationRecord | None] | None = None,
        *,
        concurrency: int | None = None,
        on_downloaded: Any | None = None,
        force: bool = False,
    ) -> dict[str, int]:
        """Process incoming publication download requests from an async queue with parallel workers."""
        worker_count = concurrency or self.concurrency
        stats: dict[str, int] = {}
        seen_keys: set[str] = set()

        if self.engine == "httpx":
            session_ctx = httpx.AsyncClient(verify=False, timeout=self.timeout, follow_redirects=True)
        else:
            session_ctx = AsyncSession(impersonate="chrome", verify=False, timeout=self.timeout)

        async with (
            session_ctx as session,
            OJSClient(engine=self.engine, verify_ssl=False, timeout=min(self.timeout, 8.0), cache=self.cache) as ojs_client,
        ):

            async def _worker() -> None:
                while True:
                    try:
                        rec = await in_queue.get()
                    except (asyncio.CancelledError, KeyboardInterrupt):
                        break

                    if rec is None:
                        in_queue.task_done()
                        break

                    if rec.cite_key in seen_keys:
                        in_queue.task_done()
                        continue
                    seen_keys.add(rec.cite_key)

                    try:
                        result = await self.download_record(
                            rec,
                            session=session,
                            ojs_client=ojs_client,
                            force=force,
                        )
                        status = result.download_status
                        stats[status] = stats.get(status, 0) + 1
                        if status == "downloaded":
                            if on_downloaded:
                                if asyncio.iscoroutinefunction(on_downloaded):
                                    await on_downloaded(result)
                                else:
                                    on_downloaded(result)
                            if out_queue is not None:
                                await out_queue.put(result)
                    except (asyncio.CancelledError, KeyboardInterrupt):
                        raise
                    except Exception as e:  # noqa: BLE001
                        logger.error(f"Worker error downloading {rec.cite_key}: {e}")
                        stats["failed_unexpected"] = stats.get("failed_unexpected", 0) + 1
                    finally:
                        in_queue.task_done()

            workers = [asyncio.create_task(_worker()) for _ in range(worker_count)]
            try:
                await asyncio.gather(*workers)
            except (asyncio.CancelledError, KeyboardInterrupt):
                for w in workers:
                    if not w.done():
                        w.cancel()
                await asyncio.gather(*workers, return_exceptions=True)
                raise

        return stats

    async def download_all(
        self,
        cite_keys: list[str] | None = None,
        *,
        skip_already_downloaded: bool = True,
        concurrency: int | None = None,
        force: bool = False,
    ) -> dict[str, int]:
        """Download papers in parallel using an async queue and worker pool."""
        if cite_keys is not None:
            records = [self.db.get(k) for k in cite_keys]
            records = [r for r in records if r is not None]
        else:
            records = self.db.list()

        if not force and skip_already_downloaded:
            filtered_records = []
            for r in records:
                if r.download_status == "downloaded" and r.download_path and Path(r.download_path).is_file():
                    continue
                # Also skip if another record with same DOI is already downloaded on disk
                if r.doi:
                    existing = self.db.get_by_doi(r.doi)
                    if (
                        existing
                        and existing.cite_key != r.cite_key
                        and existing.download_status == "downloaded"
                        and existing.download_path
                        and Path(existing.download_path).is_file()
                    ):
                        # Link now
                        self.db.update_status(
                            r.cite_key,
                            "downloaded",
                            path=existing.download_path,
                            size=existing.file_size,
                            file_hash=existing.file_hash,
                            content_type=existing.content_type or "application/pdf",
                            downloaded_at=existing.downloaded_at or datetime.now(UTC).isoformat(),
                        )
                        continue
                filtered_records.append(r)
            records = filtered_records

        worker_count = concurrency or self.concurrency
        queue: asyncio.Queue[PublicationRecord | None] = asyncio.Queue()
        for r in records:
            await queue.put(r)
        for _ in range(worker_count):
            await queue.put(None)

        return await self.download_stream(queue, concurrency=worker_count, force=force)

    def download_all_sync(
        self,
        cite_keys: list[str] | None = None,
        *,
        skip_already_downloaded: bool = True,
        concurrency: int | None = None,
        force: bool = False,
    ) -> dict[str, int]:
        """Synchronous wrapper for download_all."""
        return asyncio.run(
            self.download_all(
                cite_keys=cite_keys,
                skip_already_downloaded=skip_already_downloaded,
                concurrency=concurrency,
                force=force,
            )
        )
