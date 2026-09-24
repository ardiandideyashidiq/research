from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import httpx
from curl_cffi.requests import AsyncSession
from loguru import logger

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
    """Parallel & queued publication downloader supporting both curl-cffi and httpx engines."""

    def __init__(
        self,
        db: DatabaseManager,
        *,
        download_dir: str | Path = "data/downloads",
        concurrency: int = 4,
        timeout: float = 25.0,
        retries: int = 2,
        engine: EngineType = "curl_cffi",
    ) -> None:
        self.db = db
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.concurrency = concurrency
        self.timeout = timeout
        self.retries = retries
        self.engine = engine

    async def download_record(
        self,
        record: PublicationRecord,
        *,
        session: Any,
        ojs_client: OJSClient | None = None,
    ) -> PublicationRecord:
        """Download and verify a single publication record, recording progress in DB."""
        # Check if already downloaded on disk to prevent hitting the server twice
        if record.download_status == "downloaded" and record.download_path:
            local_path = Path(record.download_path)
            if local_path.is_file() and local_path.stat().st_size > 0:
                logger.debug(f"Paper {record.cite_key} already downloaded at {local_path}. Skipping.")
                return record

        pdf_url = record.pdf_url

        # If pdf_url is missing, attempt to extract via OJS client if URL exists
        if not pdf_url and record.url:
            client = ojs_client or OJSClient(engine=self.engine)
            try:
                ojs_meta = await client.fetch_metadata(record.url, timeout=self.timeout)
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

        # Mark in-progress
        self.db.update_status(record.cite_key, "downloading")

        target_url = pdf_url
        last_status_code: int | None = None
        last_exc: Exception | None = None
        content_bytes: bytes | None = None

        # Execute download with retries and fallback checks
        for attempt in range(self.retries + 1):
            try:
                if isinstance(session, httpx.AsyncClient):
                    resp = await session.get(target_url, timeout=self.timeout)
                else:
                    resp = await session.get(
                        target_url,
                        timeout=self.timeout,
                        allow_redirects=True,
                    )
                last_status_code = resp.status_code

                if resp.status_code == 200:
                    content_bytes = resp.content
                    break

                # If 404, check if landing page has alternative galley before giving up
                if resp.status_code == 404 and record.url and target_url != record.url and attempt == 0:
                    client = ojs_client or OJSClient(engine=self.engine)
                    meta = await client.fetch_metadata(record.url, timeout=self.timeout)
                    if meta.pdf_url and meta.pdf_url != target_url:
                        logger.info(f"Retrying {record.cite_key} with alternative galley: {meta.pdf_url}")
                        target_url = meta.pdf_url
                        continue

            except Exception as exc:  # noqa: BLE001 - capture all connection/curl errors
                last_exc = exc
                if attempt < self.retries:
                    await asyncio.sleep(1.0 * (attempt + 1))

        # Handle failure cases
        if content_bytes is None or last_status_code != 200:
            status_name, diagnostic = classify_error(last_status_code, last_exc, target_url)
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

            # HTML returned instead of PDF
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

        # Verified valid PDF!
        dest_path = self.download_dir / f"{record.cite_key}.pdf"
        dest_path.write_bytes(content_bytes)
        file_hash = compute_file_hash(content_bytes)
        now_str = datetime.now(UTC).isoformat()

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

    async def download_stream(
        self,
        in_queue: asyncio.Queue[PublicationRecord | None],
        out_queue: asyncio.Queue[PublicationRecord | None] | None = None,
        *,
        concurrency: int | None = None,
        on_downloaded: Any | None = None,
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
            OJSClient(engine=self.engine, verify_ssl=False, timeout=self.timeout) as ojs_client,
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
                        result = await self.download_record(rec, session=session, ojs_client=ojs_client)
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
    ) -> dict[str, int]:
        """Download papers in parallel using an async queue and worker pool."""
        if cite_keys is not None:
            records = [self.db.get(k) for k in cite_keys]
            records = [r for r in records if r is not None]
        else:
            records = self.db.list()

        if skip_already_downloaded:
            records = [
                r for r in records
                if not (r.download_status == "downloaded" and r.download_path and Path(r.download_path).is_file())
            ]

        worker_count = concurrency or self.concurrency
        queue: asyncio.Queue[PublicationRecord | None] = asyncio.Queue()
        for r in records:
            await queue.put(r)
        for _ in range(worker_count):
            await queue.put(None)

        return await self.download_stream(queue, concurrency=worker_count)

    def download_all_sync(
        self,
        cite_keys: list[str] | None = None,
        *,
        skip_already_downloaded: bool = True,
        concurrency: int | None = None,
    ) -> dict[str, int]:
        """Synchronous wrapper for download_all."""
        return asyncio.run(
            self.download_all(
                cite_keys=cite_keys,
                skip_already_downloaded=skip_already_downloaded,
                concurrency=concurrency,
            )
        )
