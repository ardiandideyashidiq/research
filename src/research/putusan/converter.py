from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING

import pymupdf
from loguru import logger

from research.putusan.chunker import chunk_putusan_document
from research.putusan.extractor import extract_metadata
from research.putusan.models import PutusanChunk, PutusanDocument
from research.putusan.normalizer import normalize_putusan_text
from research.putusan.segmenter import segment_putusan

if TYPE_CHECKING:
    from research.db.manager import DatabaseManager
    from research.rag.models import DocumentChunk


class PutusanConverter:
    """End-to-end converter and context-preserving semantic chunker for Indonesian Putusan court documents."""

    def __init__(
        self,
        *,
        max_chunk_chars: int = 1500,
        overlap_chars: int = 150,
        enable_ocr: bool = True,
        ocr_language: str = "ind",
        ocr_dpi: int = 150,
    ) -> None:
        self.max_chunk_chars = max_chunk_chars
        self.overlap_chars = overlap_chars
        self.enable_ocr = enable_ocr
        self.ocr_language = ocr_language
        self.ocr_dpi = ocr_dpi

    def _extract_page_text(self, page: pymupdf.Page, page_num: int) -> str:
        """Extract text from page with automatic OCR fallback if page has no selectable text."""
        text = page.get_text()
        if text and len(text.strip()) > 30:
            return text

        # If page text is empty or nearly empty, try OCR if enabled
        if self.enable_ocr:
            try:
                logger.debug(f"Page {page_num} has no native text, running OCR ({self.ocr_language})...")
                tp = page.get_textpage_ocr(language=self.ocr_language, dpi=self.ocr_dpi)
                ocr_text = tp.extractText()
                if ocr_text and len(ocr_text.strip()) > 20:
                    return ocr_text
            except (RuntimeError, ValueError, OSError, AttributeError) as e:
                logger.warning(f"OCR failed on page {page_num}: {e}")

        return text or ""

    def convert_pdf(self, pdf_path: str | Path) -> PutusanDocument:
        """Convert and chunk a single Putusan court ruling PDF without losing context."""
        path = Path(pdf_path)
        if not path.is_file():
            msg = f"PDF file not found: {path}"
            raise FileNotFoundError(msg)

        doc_id = path.stem
        logger.info(f"Processing putusan PDF: {path.name}")

        with pymupdf.open(path) as doc:
            raw_pages: list[str] = []
            for pno in range(len(doc)):
                p_text = self._extract_page_text(doc[pno], pno + 1)
                raw_pages.append(p_text)

        # 1. Normalize typography, strip watermarks and disclaimers
        cleaned_pages = normalize_putusan_text(raw_pages)

        # 2. Extract rich metadata
        metadata = extract_metadata(cleaned_pages, file_path=str(path))

        # 3. Segment into canonical legal sections
        sections = segment_putusan(cleaned_pages, metadata=metadata)

        # 4. Construct normalized markdown document
        md_blocks: list[str] = [
            f"# PUTUSAN {metadata.nomor_putusan}",
            "",
            f"**Pengadilan**: {metadata.pengadilan}  ",
            f"**Tingkat Peradilan**: {metadata.tingkat_peradilan}  ",
            f"**Klasifikasi**: {metadata.klasifikasi}  ",
            f"**Pihak**: {metadata.pihak_utama}  " if metadata.pihak_utama else "",
            f"**Tanggal Putusan**: {metadata.tanggal_putusan or 'N/A'}  ",
            f"**Total Halaman**: {metadata.total_halaman}  ",
            "",
            "---",
            "",
        ]

        for s in sections:
            md_blocks.append(f"## {s.section_type.value} ({s.title})")
            md_blocks.append(f"*Halaman {s.page_start} - {s.page_end}*")
            md_blocks.append("")
            md_blocks.append(s.content)
            md_blocks.append("")

        normalized_md = "\n".join(b for b in md_blocks if b is not None)

        putusan_doc = PutusanDocument(
            doc_id=doc_id,
            file_path=str(path),
            metadata=metadata,
            normalized_markdown=normalized_md,
            sections=sections,
            chunks=[],
        )

        # 5. Semantic chunking with context injection
        chunks = chunk_putusan_document(
            putusan_doc,
            max_chunk_chars=self.max_chunk_chars,
            overlap_chars=self.overlap_chars,
        )
        putusan_doc.chunks = chunks

        logger.info(
            f"Converted {path.name}: {metadata.total_halaman} pages -> "
            f"{len(sections)} legal sections, {len(chunks)} context-preserving chunks."
        )
        return putusan_doc

    def batch_convert(
        self,
        pdf_paths: list[str | Path],
        *,
        max_workers: int = 4,
    ) -> list[PutusanDocument]:
        """Concurrently convert and chunk multiple putusan PDFs."""
        results: list[PutusanDocument] = []
        errors: dict[str, str] = {}

        logger.info(f"Starting batch conversion of {len(pdf_paths)} Putusan documents (workers={max_workers})...")

        executor = ThreadPoolExecutor(max_workers=max_workers)
        try:
            future_to_path = {executor.submit(self.convert_pdf, p): str(p) for p in pdf_paths}
            for future in as_completed(future_to_path):
                p_str = future_to_path[future]
                try:
                    res = future.result()
                    results.append(res)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception as e:  # noqa: BLE001
                    logger.error(f"Failed processing {p_str}: {e}")
                    errors[p_str] = str(e)
        except (KeyboardInterrupt, SystemExit):
            logger.warning("Batch Putusan conversion interrupted by user. Cancelling pending jobs...")
            executor.shutdown(wait=False, cancel_futures=True)
            raise
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        logger.info(
            f"Batch conversion completed: {len(results)} succeeded, {len(errors)} failed out of {len(pdf_paths)}."
        )
        return results

    @staticmethod
    def export_chunks_json(chunks: list[PutusanChunk], out_path: str | Path) -> Path:
        """Export chunks list to a JSON file."""
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        data = [c.to_dict() for c in chunks]
        target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return target

    @staticmethod
    def export_markdown(doc: PutusanDocument, out_path: str | Path) -> Path:
        """Save normalized document markdown to file."""
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(doc.normalized_markdown, encoding="utf-8")
        return target

    @staticmethod
    def index_document_to_db(
        doc: PutusanDocument,
        db: DatabaseManager,
        *,
        markdown_path: str | Path | None = None,
    ) -> list[DocumentChunk]:
        """Index a PutusanDocument and its context-preserving chunks into SQLite database."""
        import re

        from research.db.models import PublicationRecord
        from research.rag.models import DocumentChunk

        clean_nomor = doc.metadata.nomor_putusan
        if not clean_nomor or clean_nomor == "TIDAK_TERDETEKSI":
            cite_key = doc.doc_id
        else:
            safe_suffix = re.sub(r"[^a-zA-Z0-9]+", "_", clean_nomor).strip("_")
            cite_key = f"Putusan_{safe_suffix}"

        # Extract year if possible
        year = None
        if doc.metadata.tanggal_putusan:
            m = re.search(r"\b(19\d\d|20\d\d)\b", doc.metadata.tanggal_putusan)
            if m:
                year = int(m.group(1))
        if year is None:
            m = re.search(r"\b(19\d\d|20\d\d)\b", clean_nomor)
            if m:
                year = int(m.group(1))

        # Build PublicationRecord
        pub = PublicationRecord(
            cite_key=cite_key,
            entry_type="putusan",
            title=f"Putusan {doc.metadata.pengadilan} No. {doc.metadata.nomor_putusan}",
            authors=doc.metadata.majelis_hakim if doc.metadata.majelis_hakim else [doc.metadata.pengadilan],
            journal=doc.metadata.pengadilan,
            year=year,
            abstract=doc.metadata.amar_ringkas or (doc.sections[0].content[:600] if doc.sections else None),
            sources=["putusan", doc.metadata.tingkat_peradilan],
            download_status="downloaded",
            download_path=doc.file_path,
            markdown_path=str(markdown_path) if markdown_path else None,
            full_metadata=doc.metadata.to_dict(),
            is_chunked=True,
        )
        db.create(pub)

        # Delete existing chunks for this cite_key
        db.delete_chunks(cite_key)

        # Map PutusanChunk to DocumentChunk
        doc_chunks: list[DocumentChunk] = []
        for c in doc.chunks:
            sec_title = f"[{c.section}] {c.subsection}" if c.subsection else f"[{c.section}]"
            dc = DocumentChunk(
                chunk_id=f"putusan_{c.chunk_id}",
                cite_key=cite_key,
                paper_title=pub.title,
                section_title=sec_title,
                section_level=2,
                page_start=c.page_start,
                page_end=c.page_end,
                content=c.full_text,
                token_estimate=c.token_count,
                corpus="putusan",
            )
            doc_chunks.append(dc)

        if doc_chunks:
            db.insert_chunks([c.to_dict() for c in doc_chunks])
            logger.info(
                "Indexed {} Putusan chunks for '{}' into RAG database",
                len(doc_chunks),
                cite_key,
            )

        return doc_chunks
