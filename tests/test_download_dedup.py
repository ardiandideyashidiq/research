from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pymupdf

from research.cache.manager import HttpCache
from research.db.manager import DatabaseManager
from research.db.models import PublicationRecord
from research.downloader.downloader import DownloadManager
from research.downloader.verifier import compute_file_hash


def _create_sample_pdf(path: Path, title: str, text: str) -> Path:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), f"# {title}\n\n{text}")
    doc.save(str(path))
    doc.close()
    return path


class MockResponse:
    def __init__(self, content: bytes, status_code: int = 200) -> None:
        self.content = content
        self.status_code = status_code


class MockSession:
    def __init__(self, content: bytes) -> None:
        self.content = content
        self.calls: list[str] = []

    async def get(self, url: str, **kwargs) -> MockResponse:
        self.calls.append(url)
        await asyncio.sleep(0.05)
        return MockResponse(self.content, 200)


def test_cross_record_doi_deduplication() -> None:
    """When Paper B shares the same DOI as already-downloaded Paper A, it should reuse Paper A's PDF without network fetch."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "test.sqlite"
        dl_dir = tmp_path / "downloads"
        dl_dir.mkdir()

        db = DatabaseManager(db_path)
        cache = HttpCache(db_path=db_path)
        downloader = DownloadManager(db, download_dir=dl_dir, cache=cache)

        # 1. Create sample PDF on disk
        pdf_file = dl_dir / "smith2024.pdf"
        _create_sample_pdf(pdf_file, "Deep Learning AI", "Sample publication content.")
        file_bytes = pdf_file.read_bytes()
        file_hash = compute_file_hash(file_bytes)

        # 2. Insert record A (downloaded)
        rec_a = PublicationRecord(
            cite_key="smith2024",
            title="Deep Learning AI",
            doi="10.1234/test.doi.1",
            pdf_url="https://example.com/smith.pdf",
            download_status="downloaded",
            download_path=str(pdf_file),
            file_size=len(file_bytes),
            file_hash=file_hash,
        )
        db.create(rec_a)

        # 3. Insert record B (pending, different cite_key, same DOI)
        rec_b = PublicationRecord(
            cite_key="smith_2024_openalex",
            title="Deep Learning AI (OpenAlex version)",
            doi="10.1234/test.doi.1",
            pdf_url="https://other-publisher.com/alt_smith.pdf",
            download_status="pending",
        )
        db.create(rec_b)

        # 4. Attempt download of record B
        session = MockSession(b"dummy")

        async def _run() -> None:
            res = await downloader.download_record(rec_b, session=session)
            assert res.download_status == "downloaded"
            assert res.download_path == str(pdf_file)
            assert res.file_hash == file_hash
            # Session should NOT have been called because Tier 2 DOI matched!
            assert len(session.calls) == 0

        asyncio.run(_run())
        cache.close()
        db.close()
    print("test_cross_record_doi_deduplication passed!")


def test_preexisting_file_on_disk_check() -> None:
    """If a valid PDF file already exists on disk for cite_key, it should be adopted without downloading."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "test.sqlite"
        dl_dir = tmp_path / "downloads"
        dl_dir.mkdir()

        db = DatabaseManager(db_path)
        cache = HttpCache(db_path=db_path)
        downloader = DownloadManager(db, download_dir=dl_dir, cache=cache)

        # Pre-place file on disk
        pdf_file = dl_dir / "paper_on_disk.pdf"
        _create_sample_pdf(pdf_file, "On Disk Paper", "Content present before download.")
        file_bytes = pdf_file.read_bytes()

        rec = PublicationRecord(
            cite_key="paper_on_disk",
            title="On Disk Paper",
            pdf_url="https://example.com/paper.pdf",
            download_status="pending",
        )
        db.create(rec)

        session = MockSession(b"network_bytes")

        async def _run() -> None:
            res = await downloader.download_record(rec, session=session)
            assert res.download_status == "downloaded"
            assert res.download_path == str(pdf_file)
            assert res.file_size == len(file_bytes)
            # No network call
            assert len(session.calls) == 0

        asyncio.run(_run())
        cache.close()
        db.close()
    print("test_preexisting_file_on_disk_check passed!")


def test_in_flight_download_coalescing() -> None:
    """When two concurrent workers download records pointing to the same PDF URL, only 1 network fetch runs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "test.sqlite"
        dl_dir = tmp_path / "downloads"
        dl_dir.mkdir()

        db = DatabaseManager(db_path)
        cache = HttpCache(db_path=db_path)
        downloader = DownloadManager(db, download_dir=dl_dir, cache=cache)

        # Sample PDF bytes
        sample_pdf = tmp_path / "dummy.pdf"
        _create_sample_pdf(sample_pdf, "Coalesced Paper", "Same URL shared between 2 records.")
        pdf_bytes = sample_pdf.read_bytes()

        rec1 = PublicationRecord(
            cite_key="worker_1_rec",
            title="Shared URL Paper 1",
            pdf_url="https://shared-host.com/paper.pdf",
            download_status="pending",
        )
        rec2 = PublicationRecord(
            cite_key="worker_2_rec",
            title="Shared URL Paper 2",
            pdf_url="https://shared-host.com/paper.pdf",
            download_status="pending",
        )
        db.create(rec1)
        db.create(rec2)

        session = MockSession(pdf_bytes)

        async def _run() -> None:
            t1 = downloader.download_record(rec1, session=session)
            t2 = downloader.download_record(rec2, session=session)
            r1, r2 = await asyncio.gather(t1, t2)

            assert r1.download_status == "downloaded"
            assert r2.download_status == "downloaded"
            # Exactly 1 network fetch should have executed!
            assert len(session.calls) == 1

        asyncio.run(_run())
        cache.close()
        db.close()
    print("test_in_flight_download_coalescing passed!")


def test_content_hash_deduplication() -> None:
    """If network returns bytes matching an already stored PDF's SHA-256, it reuses the existing file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "test.sqlite"
        dl_dir = tmp_path / "downloads"
        dl_dir.mkdir()

        db = DatabaseManager(db_path)
        cache = HttpCache(db_path=db_path)
        downloader = DownloadManager(db, download_dir=dl_dir, cache=cache)

        # Create original file
        orig_file = dl_dir / "original.pdf"
        _create_sample_pdf(orig_file, "Identical Content", "Identical bytes across publishers.")
        pdf_bytes = orig_file.read_bytes()
        file_hash = compute_file_hash(pdf_bytes)

        # Record 1 downloaded
        rec1 = PublicationRecord(
            cite_key="original",
            title="Identical Content",
            download_status="downloaded",
            download_path=str(orig_file),
            file_hash=file_hash,
            file_size=len(pdf_bytes),
        )
        db.create(rec1)

        # Record 2 pending from different URL, no DOI
        rec2 = PublicationRecord(
            cite_key="mirror_copy",
            title="Mirror Copy",
            pdf_url="https://mirror.org/mirror.pdf",
            download_status="pending",
        )
        db.create(rec2)

        session = MockSession(pdf_bytes)

        async def _run() -> None:
            res = await downloader.download_record(rec2, session=session)
            assert res.download_status == "downloaded"
            # Reused the original path because content hash matched!
            assert res.download_path == str(orig_file)
            assert res.file_hash == file_hash

        asyncio.run(_run())
        cache.close()
        db.close()
    print("test_content_hash_deduplication passed!")


if __name__ == "__main__":
    test_cross_record_doi_deduplication()
    test_preexisting_file_on_disk_check()
    test_in_flight_download_coalescing()
    test_content_hash_deduplication()
