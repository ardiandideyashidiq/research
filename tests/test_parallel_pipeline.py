"""Test parallel PDF conversion, download streaming, and pipeline execution."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pymupdf

from research.app import ResearchApp
from research.db.models import PublicationRecord
from research.pdf.converter import PDFConverter
from research.pipeline.models import PipelineConfig


def _create_sample_pdf(path: Path, title: str, content: str) -> Path:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), f"# {title}\n\n{content}")
    doc.save(str(path))
    doc.close()
    return path


def test_parallel_pdf_conversion() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        pdf_files = []
        for i in range(8):
            pdf_path = tmp_path / f"test_paper_{i}.pdf"
            _create_sample_pdf(
                pdf_path,
                f"Paper Title {i}",
                f"Abstract: This is parallel paper {i} testing high-performance layout normalization.",
            )
            pdf_files.append(pdf_path)

        converter = PDFConverter()

        async def _run() -> None:
            results = await converter.convert_batch(pdf_files, concurrency=4)
            assert len(results) == 8
            for i, r in enumerate(results):
                assert (
                    f"Paper Title {i}" in r.markdown
                    or f"paper_{i}" in r.markdown.lower()
                )

        asyncio.run(_run())
        print("Successfully verified parallel batch PDF conversion across 8 documents!")


def test_card_manager_parallel_batch_extract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "test_cards.sqlite"
        app = ResearchApp(db_path=db_path)

        for i in range(12):
            rec = PublicationRecord(
                cite_key=f"cite_key_{i}",
                title=f"Legal Analysis on AI Liability Vol. {i}",
                authors=["Test Author"],
                year=2024,
                journal="Journal of Cyber Law",
                abstract=f"Issue: criminal liability of AI. Theory: strict liability. Method: normative. Findings: AI agent #{i} holds partial liability.",
                sources=["test"],
            )
            app.db.create(rec)

        cards = app.cards.batch_extract(concurrency=4)
        assert len(cards) == 12
        for c in cards:
            assert "Liability" in c.title or "AI" in c.title

        app.db.close()
        print(
            "Successfully verified parallel CardManager batch extraction across 12 records!"
        )


def test_pipeline_streaming_execution() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "test_pipe.sqlite"
        dl_dir = tmp_path / "downloads"
        dl_dir.mkdir(parents=True, exist_ok=True)

        # Create 3 pre-downloaded PDFs to test streaming conversion and chunking
        app = ResearchApp(db_path=db_path, download_dir=dl_dir)

        for i in range(4):
            pdf_file = dl_dir / f"test_pub_{i}.pdf"
            _create_sample_pdf(
                pdf_file,
                f"Autonomous Research Paper {i}",
                f"Section 1: Introduction to Parallel Streaming {i}.\n\nSection 2: Empirical Results.",
            )
            rec = PublicationRecord(
                cite_key=f"test_pub_{i}",
                title=f"Autonomous Research Paper {i}",
                authors=["Researcher A", "Researcher B"],
                year=2025,
                download_status="downloaded",
                download_path=str(pdf_file),
                sources=["test"],
            )
            app.db.create(rec)

        # Run pipeline with staged execution and search/snowball disabled
        cfg = PipelineConfig(
            query="",
            download=False,
            convert=True,
            convert_concurrency=2,
            index_rag=True,
            streaming=False,
        )

        async def _run() -> None:
            res = await app.pipeline.run(cfg)
            assert res.converted_count == 4
            assert res.indexed_chunks_count > 0

        asyncio.run(_run())
        app.db.close()
        print("Successfully verified staged parallel conversion and RAG chunking!")


def test_pipeline_full_streaming_run() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "test_stream_pipe.sqlite"
        dl_dir = tmp_path / "downloads"
        dl_dir.mkdir(parents=True, exist_ok=True)

        app = ResearchApp(db_path=db_path, download_dir=dl_dir)

        # Create 3 sample PDFs
        bib_lines = []
        for i in range(3):
            pdf_file = dl_dir / f"stream_paper_{i}.pdf"
            _create_sample_pdf(
                pdf_file,
                f"Streaming Paper Title {i}",
                f"Section: Streaming test for parallel worker {i}.",
            )
            cite_key = f"stream_key_{i}"
            rec = PublicationRecord(
                cite_key=cite_key,
                title=f"Streaming Paper Title {i}",
                authors=["Researcher Streaming"],
                year=2025,
                download_status="downloaded",
                download_path=str(pdf_file),
                sources=["bib"],
            )
            app.db.create(rec)
            bib_lines.append(
                f"@article{{{cite_key},\n  title={{Streaming Paper Title {i}}},\n  author={{Researcher Streaming}},\n  year={{2025}}\n}}\n"
            )

        bib_file = tmp_path / "test_seed.bib"
        bib_file.write_text("\n".join(bib_lines), encoding="utf-8")

        cfg = PipelineConfig(
            query="",
            bib_path=bib_file,
            snowball=False,
            download=False,
            convert=True,
            convert_concurrency=3,
            index_rag=True,
            streaming=True,
        )

        async def _run() -> None:
            res = await app.pipeline.run(cfg)
            assert res.bib_count == 3
            assert res.converted_count == 3
            assert res.indexed_chunks_count >= 3

        asyncio.run(_run())
        app.db.close()
        print("Successfully verified full streaming parallel pipeline run!")


if __name__ == "__main__":
    test_parallel_pdf_conversion()
    test_card_manager_parallel_batch_extract()
    test_pipeline_streaming_execution()
    test_pipeline_full_streaming_run()
