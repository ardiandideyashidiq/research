"""Test DatabaseManager under concurrent multi-threaded read/write load."""

from __future__ import annotations

import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from research.db.manager import DatabaseManager
from research.db.models import PublicationRecord


def test_concurrent_db_operations() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_concurrent.sqlite"
        db = DatabaseManager(db_path)

        num_threads = 16
        records_per_thread = 20

        def _worker(worker_id: int) -> list[str]:
            created_keys = []
            for i in range(records_per_thread):
                key = f"pub_{worker_id}_{i}"
                rec = PublicationRecord(
                    cite_key=key,
                    title=f"Parallel Paper {worker_id}-{i}",
                    authors=[f"Author {worker_id}", "Coauthor"],
                    year=2025,
                    journal="Journal of Concurrent Systems",
                    abstract=f"This is abstract for publication {worker_id} number {i}.",
                    sources=["test"],
                )
                db.create(rec)
                created_keys.append(key)

                # Test immediate read
                fetched = db.get(key)
                assert fetched is not None
                assert fetched.title == rec.title

                # Test update
                db.update(key, download_status="downloaded", file_size=1024 * (i + 1))

                # Test chunk insertion
                chunk = {
                    "chunk_id": f"chunk_{key}_1",
                    "cite_key": key,
                    "paper_title": rec.title,
                    "section_title": "Introduction",
                    "section_level": 1,
                    "page_start": 1,
                    "page_end": 2,
                    "content": f"Content for chunk {worker_id}-{i}",
                    "corpus": "literature",
                }
                db.insert_chunks([chunk])

            return created_keys

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(_worker, w) for w in range(num_threads)]
            results = [f.result() for f in futures]

        total_created = sum(len(r) for r in results)
        assert total_created == num_threads * records_per_thread

        stats = db.get_stats()
        assert stats["total_publications"] == total_created
        assert stats["total_chunks"] == total_created
        assert stats["downloaded"] == total_created

        # Test concurrent search
        def _search_worker(term: str) -> int:
            results = db.search(term, limit=100)
            return len(results)

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            s_futures = [
                executor.submit(_search_worker, "Concurrent")
                for _ in range(num_threads)
            ]
            s_results = [f.result() for f in s_futures]
            for count in s_results:
                assert count > 0

        db.close()
        print(
            f"Successfully verified concurrent DB operations with {total_created} records across {num_threads} threads!"
        )


if __name__ == "__main__":
    test_concurrent_db_operations()
