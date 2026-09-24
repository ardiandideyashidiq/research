"""Test robust handling of KeyboardInterrupt and asyncio cancellation."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pymupdf

from research.app import ResearchApp
from research.cli.main import _async_main
from research.db.models import PublicationRecord
from research.pipeline.models import PipelineConfig
from research.putusan.converter import PutusanConverter


def _create_sample_pdf(path: Path, title: str, content: str) -> Path:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), f"# {title}\n\n{content}")
    doc.save(str(path))
    doc.close()
    return path


def test_app_close_shielded_on_cancellation() -> None:
    """Verify ResearchApp.close() completes fully even when called in a cancelled task context."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_shield.sqlite"
        app = ResearchApp(db_path=db_path)

        # Populate a sample record to ensure DB connection is active
        rec = PublicationRecord(
            cite_key="test_key_1",
            title="Test Shield",
            authors=["Author 1"],
            year=2025,
            sources=["test"],
        )
        app.db.create(rec)
        assert app.db.get("test_key_1") is not None

        closed = False

        async def _cancelled_task() -> None:
            nonlocal closed
            try:
                # Sleep and wait to be cancelled
                await asyncio.sleep(10)
            finally:
                # Ensure close is shielded and succeeds
                await app.close()
                closed = True

        async def _runner() -> None:
            task = asyncio.create_task(_cancelled_task())
            await asyncio.sleep(0.01)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        asyncio.run(_runner())
        assert closed is True
        # Verify connections are cleared
        assert len(app.db._connections) == 0


def test_card_batch_extract_interruption() -> None:
    """Verify CardManager.batch_extract cancels remaining futures on KeyboardInterrupt."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_cards_interrupt.sqlite"
        app = ResearchApp(db_path=db_path)

        for i in range(10):
            app.db.create(
                PublicationRecord(
                    cite_key=f"card_rec_{i}",
                    title=f"Legal Review {i}",
                    authors=["Author"],
                    year=2024,
                    abstract=f"Issue: copyright. Method: normative. Amar: {i}",
                    sources=["test"],
                )
            )

        import time

        executed_count = 0
        original_extract = app.cards.extractor.extract_from_record

        def _mock_extract(rec: PublicationRecord):
            nonlocal executed_count
            time.sleep(0.03)
            executed_count += 1
            if executed_count >= 2:
                raise KeyboardInterrupt("Simulated user interrupt")
            return original_extract(rec)

        app.cards.extractor.extract_from_record = _mock_extract  # type: ignore[assignment]

        try:
            app.cards.batch_extract(concurrency=1)
            assert False, "Should have raised KeyboardInterrupt"
        except KeyboardInterrupt:
            pass

        # Since it raised on the 2nd record and cancelled pending futures immediately,
        # executed_count should not reach 10.
        assert executed_count < 10
        app.db.close()


def test_putusan_batch_convert_interruption() -> None:
    """Verify PutusanConverter.batch_convert cancels pending futures on KeyboardInterrupt."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        import time

        tmp_path = Path(tmp_dir)
        pdf_paths = []
        for i in range(8):
            p = tmp_path / f"putusan_{i}.pdf"
            _create_sample_pdf(
                p, f"Putusan No. {i}/Pdt.G/2024/PN Jkt", "MENGADILI: Menolak gugatan."
            )
            pdf_paths.append(p)

        converter = PutusanConverter()
        call_count = 0
        orig_convert = converter.convert_pdf

        def _mock_convert(path: Path):
            nonlocal call_count
            time.sleep(0.03)
            call_count += 1
            if call_count >= 2:
                raise KeyboardInterrupt("Simulated Ctrl+C")
            return orig_convert(path)

        converter.convert_pdf = _mock_convert  # type: ignore[assignment]

        try:
            converter.batch_convert(pdf_paths, max_workers=1)
            assert False, "Should have raised KeyboardInterrupt"
        except KeyboardInterrupt:
            pass

        assert call_count < 8


def test_pipeline_streaming_cancellation() -> None:
    """Verify ResearchPipeline._run_streaming cleans up worker tasks on cancellation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "test_pipe_cancel.sqlite"
        dl_dir = tmp_path / "downloads"
        dl_dir.mkdir(parents=True, exist_ok=True)

        app = ResearchApp(db_path=db_path, download_dir=dl_dir)

        # Create sample files
        for i in range(5):
            pdf_file = dl_dir / f"pipe_doc_{i}.pdf"
            _create_sample_pdf(pdf_file, f"Title {i}", "Sample content for test.")
            app.db.create(
                PublicationRecord(
                    cite_key=f"pipe_doc_{i}",
                    title=f"Title {i}",
                    authors=["Author"],
                    year=2025,
                    download_status="downloaded",
                    download_path=str(pdf_file),
                    sources=["test"],
                )
            )

        async def _slow_search(*args, **kwargs):
            await asyncio.sleep(5)
            return []

        app.providers.search_all = _slow_search  # type: ignore[assignment]

        cfg = PipelineConfig(
            query="quantum encryption",
            download=True,
            convert=True,
            convert_concurrency=2,
            index_rag=True,
            streaming=True,
        )

        pipeline_cancelled = False

        async def _run_and_cancel() -> None:
            nonlocal pipeline_cancelled
            pipe_task = asyncio.create_task(app.pipeline.run(cfg))
            # Let workers start and enter active execution
            await asyncio.sleep(0.05)
            pipe_task.cancel()
            try:
                await pipe_task
            except asyncio.CancelledError:
                pipeline_cancelled = True

        asyncio.run(_run_and_cancel())
        assert pipeline_cancelled is True
        app.db.close()


def test_cli_async_main_cancellation() -> None:
    """Verify _async_main intercepts CancelledError/KeyboardInterrupt and exits cleanly with 130."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_cli_cancel.sqlite"

        args = MagicMock()
        args.db = str(db_path)
        args.downloads = str(Path(tmp_dir) / "downloads")
        args.command = "convert"
        args.path = str(tmp_dir)
        args.output_dir = None
        args.concurrency = 2
        args.index_rag = False

        # Create dummy PDF
        p = Path(tmp_dir) / "sample.pdf"
        _create_sample_pdf(p, "Sample Title", "Sample PDF body.")

        async def _run() -> int:
            task = asyncio.create_task(_async_main(args))
            await asyncio.sleep(0.001)
            task.cancel()
            return await task

        exit_code = asyncio.run(_run())
        assert exit_code == 130


if __name__ == "__main__":
    test_app_close_shielded_on_cancellation()
    test_card_batch_extract_interruption()
    test_putusan_batch_convert_interruption()
    test_pipeline_streaming_cancellation()
    test_cli_async_main_cancellation()
    print("All interruption and cancellation tests passed successfully!")
