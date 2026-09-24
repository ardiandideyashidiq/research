from __future__ import annotations

import asyncio
import tempfile
import time
from pathlib import Path

from research.cache.manager import HttpCache
from research.db.manager import DatabaseManager
from research.db.models import PublicationRecord
from research.downloader.downloader import DownloadManager
from research.google_scholar.client import GoogleScholarClient
from research.ojs.client import OJSClient
from research.pipeline.models import PipelineConfig


def test_client_defaults() -> None:
    db = DatabaseManager(":memory:")
    dl = DownloadManager(db)
    assert dl.timeout == 10.0
    assert dl.retries == 1

    ojs = OJSClient()
    assert ojs.timeout == 8.0

    scholar = GoogleScholarClient()
    assert scholar.timeout == 12.0
    assert scholar.max_retries == 2

    cfg = PipelineConfig()
    assert cfg.download_timeout == 10.0


def test_ojs_negative_cache_on_unresponsive() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_cache.sqlite"
        cache = HttpCache(db_path=db_path)
        # Point to a non-routable address to simulate timeout
        client = OJSClient(cache=cache, timeout=0.5)

        start = time.perf_counter()
        meta1 = client.fetch_metadata_sync("http://10.255.255.1/slow_paper", timeout=0.5, retries=0)
        elapsed1 = time.perf_counter() - start

        assert meta1.is_ojs is False
        assert elapsed1 < 2.0

        # Second request must hit negative cache immediately (< 0.05s)
        start2 = time.perf_counter()
        meta2 = client.fetch_metadata_sync("http://10.255.255.1/slow_paper", timeout=0.5, retries=0)
        elapsed2 = time.perf_counter() - start2

        assert meta2.is_ojs is False
        assert elapsed2 < 0.1, f"Expected cache hit to be fast, took {elapsed2}s"

        cached = cache.get("http://10.255.255.1/slow_paper")
        assert cached is not None
        assert cached.status_code == 504


async def test_downloader_fast_fail_and_cache() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test.sqlite"
        dl_dir = Path(tmp_dir) / "downloads"
        cache = HttpCache(db_path=db_path)
        db = DatabaseManager(db_path)
        dl = DownloadManager(db, download_dir=dl_dir, cache=cache, timeout=0.5, retries=0)

        record = PublicationRecord(
            cite_key="hung_host_2026",
            title="Hung Server Paper",
            pdf_url="http://10.255.255.1/paper.pdf",
        )
        db.create(record)

        start = time.perf_counter()
        await dl.download_all([record.cite_key])
        elapsed = time.perf_counter() - start

        updated = db.get("hung_host_2026")
        assert updated is not None
        assert updated.download_status in ("failed", "failed_timeout", "network_error", "dead_link")
        assert elapsed < 2.5, f"Download took too long: {elapsed}s"


if __name__ == "__main__":
    test_client_defaults()
    print("test_client_defaults passed!")
    test_ojs_negative_cache_on_unresponsive()
    print("test_ojs_negative_cache_on_unresponsive passed!")
    asyncio.run(test_downloader_fast_fail_and_cache())
    print("test_downloader_fast_fail_and_cache passed!")
