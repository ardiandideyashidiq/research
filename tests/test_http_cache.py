from __future__ import annotations

import asyncio
import tempfile
import time
from pathlib import Path

from research.cache.manager import HttpCache
from research.cache.models import CachePolicy


def test_http_cache_basic_and_ttl() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_cache.sqlite"
        cache = HttpCache(db_path=db_path)

        # 1. Set and Get
        url = "https://example.com/api/test"
        cache.set(url, 200, b"Hello World", content_type="text/plain")

        cached = cache.get(url)
        assert cached is not None
        assert cached.status_code == 200
        assert cached.content == b"Hello World"
        assert cached.text == "Hello World"
        assert cached.from_cache is True

        # 2. Cache miss
        assert cache.get("https://example.com/notfound") is None

        # 3. TTL Expiration
        expiring_url = "https://example.com/expiring"
        cache.set(expiring_url, 200, b"short lived", ttl=0.2)
        assert cache.get(expiring_url) is not None
        time.sleep(0.3)
        assert cache.get(expiring_url) is None  # Should be expired and removed

        # 4. Stats
        stats = cache.stats()
        assert stats["total_cached"] >= 1
        assert stats["total_bytes"] > 0

        # 5. Clear
        deleted = cache.clear()
        assert deleted >= 1
        assert cache.stats()["total_cached"] == 0

        cache.close()
    print("test_http_cache_basic_and_ttl passed!")


def test_http_cache_in_flight_coalescing() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_coalesce.sqlite"
        cache = HttpCache(db_path=db_path)

        network_call_count = 0

        async def _mock_network_fetch() -> str:
            nonlocal network_call_count
            network_call_count += 1
            await asyncio.sleep(0.1)
            return "network_response"

        async def _run() -> None:
            # Launch 10 simultaneous requests for the exact same key
            tasks = [
                cache.coalesce_async("https://api.test/resource", _mock_network_fetch)
                for _ in range(10)
            ]
            results = await asyncio.gather(*tasks)
            assert len(results) == 10
            for r in results:
                assert r == "network_response"
            # Exactly 1 actual network call should have occurred!
            assert network_call_count == 1

        asyncio.run(_run())
        cache.close()
    print("test_http_cache_in_flight_coalescing passed!")


def test_http_cache_disabled_policy() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_disabled.sqlite"
        cache = HttpCache(db_path=db_path, policy=CachePolicy(enabled=False))

        cache.set("https://test.com", 200, b"content")
        assert cache.get("https://test.com") is None
        assert cache.stats()["total_cached"] == 0
        cache.close()
    print("test_http_cache_disabled_policy passed!")


if __name__ == "__main__":
    test_http_cache_basic_and_ttl()
    test_http_cache_in_flight_coalescing()
    test_http_cache_disabled_policy()
