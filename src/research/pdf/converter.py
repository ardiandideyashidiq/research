from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

import pymupdf
import pymupdf4llm
from loguru import logger

from research.pdf.models import (
    ConversionOptions,
    ConvertedDocument,
    PageChunk,
    PDFMetadata,
    TableOfContentsItem,
)
from research.pdf.normalizer import (
    build_yaml_frontmatter,
    normalize_markdown_layout,
    strip_repeating_headers_footers,
)


class PDFConverter:
    """High-performance PDF to Markdown converter with layout normalization."""

    def __init__(self, default_options: ConversionOptions | None = None) -> None:
        self.default_options = default_options or ConversionOptions()

    def _extract_metadata(self, doc: pymupdf.Document, source: str | Path | bytes) -> PDFMetadata:
        raw_meta = doc.metadata or {}
        file_path = str(source) if isinstance(source, (str, Path)) else None
        file_size = Path(file_path).stat().st_size if file_path and Path(file_path).exists() else None

        title = (raw_meta.get("title") or "").strip()
        # If title is empty, placeholder, or an arXiv stamp, derive fallback from filename
        if (
            not title
            or title.lower().startswith(("arxiv:", "untitled", "template", "draft"))
            or len(title) < 4
        ) and file_path:
            title = Path(file_path).stem.replace("_", " ").replace("-", " ").title()

        return PDFMetadata(
            title=title.strip(),
            author=(raw_meta.get("author") or "").strip(),
            subject=(raw_meta.get("subject") or "").strip(),
            keywords=(raw_meta.get("keywords") or "").strip(),
            creator=(raw_meta.get("creator") or "").strip(),
            producer=(raw_meta.get("producer") or "").strip(),
            creation_date=(raw_meta.get("creationDate") or "").strip(),
            page_count=len(doc),
            file_size=file_size,
            file_path=file_path,
        )

    def _extract_toc(self, doc: pymupdf.Document) -> list[TableOfContentsItem]:
        raw_toc = doc.get_toc() or []
        items: list[TableOfContentsItem] = []
        for entry in raw_toc:
            if len(entry) >= 3:
                items.append(
                    TableOfContentsItem(
                        level=int(entry[0]),
                        title=str(entry[1]).strip(),
                        page=int(entry[2]),
                    )
                )
        return items

    def _refine_title_from_text(self, text: str, current_title: str) -> str:
        """If metadata title is generic or filename-derived, extract genuine title from first blocks or heading."""
        if (
            current_title
            and not current_title.lower().startswith(("arxiv:", "untitled", "template"))
            and len(current_title.split()) >= 3
            and not current_title.endswith((".pdf", ".tex"))
            and not re.search(r"^[A-Z][a-z]+[0-9]{4}", current_title)  # Not cite-key-like
        ):
            return current_title

        blocks = re.split(r"\n\s*\n", text.strip())

        # 1. Search first 4 blocks for title-like block before Abstract / Sections
        for block in blocks[:5]:
            s = block.strip()
            if not s:
                continue
            if re.search(r"\b(preprint of|to appear in|accepted for publication|arxiv:)\b", s, re.IGNORECASE):
                continue
            if re.match(
                r"^#{1,3}\s+(?:[0-9IVXLCDM\.]*\s*)?(?:introduction|abstract|contents|overview)\b",
                s,
                re.IGNORECASE,
            ):
                continue
            if re.search(r"(@|university|department|school of|institute|laboratory|corporation|inc\.)", s, re.IGNORECASE):
                continue

            clean = re.sub(r"^(#{1,3}\s+|\*\*|__)", "", s)
            clean = re.sub(r"(\*\*|__)$", "", clean)
            clean = re.sub(r"<sup>.*?</sup>", "", clean)
            clean = re.sub(r"[*†‡§¶⋆]+$", "", clean).strip()
            clean = re.sub(r"\s+", " ", clean)

            words = clean.split()
            if 3 <= len(words) <= 30 and not clean.startswith(("-", "*", ">", "|", "http")):
                return clean

        return current_title

    def convert(
        self,
        source: str | Path | bytes,
        *,
        options: ConversionOptions | None = None,
    ) -> ConvertedDocument:
        """Convert a PDF document into normalized Markdown and structured page chunks."""
        opts = options or self.default_options
        doc = pymupdf.open(stream=source, filetype="pdf") if isinstance(source, bytes) else pymupdf.open(source)

        try:
            metadata = self._extract_metadata(doc, source)
            toc = self._extract_toc(doc)
            total_pages = len(doc)

            # Determine pages to convert safely
            pages_arg: list[int] | None = None
            if opts.pages is not None:
                if isinstance(opts.pages, int):
                    raw_pages = [opts.pages]
                else:
                    raw_pages = list(opts.pages)
                # Clamp within valid range [0, total_pages - 1]
                filtered = [p for p in raw_pages if 0 <= p < total_pages]
                pages_arg = filtered if filtered else None

            # Prepare extraction kwargs
            kwargs: dict[str, Any] = {
                "pages": pages_arg,
                "dpi": opts.dpi,
                "page_chunks": True,
                "table_output": opts.table_output,
                "use_ocr": opts.use_ocr,
                "show_progress": False,
            }

            if opts.embed_images:
                kwargs["embed_images"] = True
            elif opts.extract_images and opts.image_dir:
                img_dir = Path(opts.image_dir)
                img_dir.mkdir(parents=True, exist_ok=True)
                kwargs["write_images"] = True
                kwargs["image_path"] = str(img_dir)
                kwargs["image_format"] = opts.image_format

            # Extract raw page chunks using PyMuPDF4LLM
            raw_chunks = pymupdf4llm.to_markdown(doc, **kwargs)

            chunks: list[PageChunk] = []
            for i, chunk in enumerate(raw_chunks):
                pg_num = chunk.get("metadata", {}).get("page_number", (pages_arg[i] + 1 if pages_arg else i + 1))
                chunk_text = chunk.get("text", "")
                chunks.append(
                    PageChunk(
                        page_number=pg_num,
                        text=chunk_text,
                        raw_text=chunk_text,
                        metadata=chunk.get("metadata", {}),
                    )
                )

            # Detect and remove running headers/footers across chunks
            if opts.strip_headers_footers:
                strip_repeating_headers_footers(chunks)

            # Normalize layout per chunk
            for chunk in chunks:
                chunk.text = normalize_markdown_layout(chunk.text, options=opts)

            # Assemble full document markdown
            body_parts: list[str] = []
            for chunk in chunks:
                if opts.page_separators:
                    body_parts.append(f"\n\n---\n<!-- Page {chunk.page_number} -->\n\n{chunk.text}")
                else:
                    body_parts.append(chunk.text)

            body_markdown = "\n\n".join(body_parts)
            full_markdown = normalize_markdown_layout(body_markdown, options=opts)

            # Refine title if needed from body text
            metadata.title = self._refine_title_from_text(full_markdown, metadata.title)

            # Build Table of Contents block if requested
            toc_markdown = ""
            if opts.include_toc and toc:
                toc_lines = ["## Table of Contents\n"]
                for item in toc:
                    indent = "  " * (item.level - 1)
                    toc_lines.append(f"{indent}- [{item.title}](#page-{item.page})")
                toc_markdown = "\n".join(toc_lines) + "\n\n"

            # Build YAML frontmatter if requested
            frontmatter = ""
            if opts.include_frontmatter:
                frontmatter = build_yaml_frontmatter(metadata)

            final_markdown = f"{frontmatter}{toc_markdown}{full_markdown}".strip()

            return ConvertedDocument(
                markdown=final_markdown,
                metadata=metadata,
                toc=toc,
                chunks=chunks,
                total_pages=total_pages,
            )
        finally:
            doc.close()

    def convert_to_markdown(
        self,
        source: str | Path | bytes,
        *,
        options: ConversionOptions | None = None,
    ) -> str:
        """Directly convert PDF source to normalized markdown string."""
        return self.convert(source, options=options).markdown

    def convert_to_chunks(
        self,
        source: str | Path | bytes,
        *,
        options: ConversionOptions | None = None,
    ) -> list[PageChunk]:
        """Convert PDF source to normalized per-page chunks."""
        return self.convert(source, options=options).chunks

    def convert_file(
        self,
        input_pdf: str | Path,
        output_md: str | Path | None = None,
        *,
        options: ConversionOptions | None = None,
    ) -> Path:
        """Convert PDF file to a Markdown file on disk."""
        in_path = Path(input_pdf)
        if not in_path.exists():
            raise FileNotFoundError(f"Input PDF not found: {in_path}")

        out_path = Path(output_md) if output_md else in_path.with_suffix(".md")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        converted = self.convert(in_path, options=options)
        out_path.write_text(converted.markdown, encoding="utf-8")
        logger.info("Successfully converted {} to {} ({} pages)", in_path.name, out_path.name, converted.total_pages)
        return out_path

    async def convert_async(
        self,
        source: str | Path | bytes,
        *,
        options: ConversionOptions | None = None,
    ) -> ConvertedDocument:
        """Asynchronously convert a PDF document in a background thread."""
        return await asyncio.to_thread(self.convert, source, options=options)

    async def convert_file_async(
        self,
        input_pdf: str | Path,
        output_md: str | Path | None = None,
        *,
        options: ConversionOptions | None = None,
    ) -> tuple[Path, ConvertedDocument]:
        """Asynchronously convert PDF file to a Markdown file on disk in a worker thread."""

        def _task() -> tuple[Path, ConvertedDocument]:
            in_path = Path(input_pdf)
            if not in_path.exists():
                raise FileNotFoundError(f"Input PDF not found: {in_path}")
            out_path = Path(output_md) if output_md else in_path.with_suffix(".md")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            conv = self.convert(in_path, options=options)
            out_path.write_text(conv.markdown, encoding="utf-8")
            return out_path, conv

        return await asyncio.to_thread(_task)

    async def convert_batch(
        self,
        sources: list[str | Path],
        *,
        options: ConversionOptions | None = None,
        concurrency: int = 4,
    ) -> list[ConvertedDocument]:
        """Convert multiple PDF documents in parallel with bounded concurrency."""
        sem = asyncio.Semaphore(concurrency)

        async def _worker(src: str | Path) -> ConvertedDocument:
            async with sem:
                return await self.convert_async(src, options=options)

        return await asyncio.gather(*[_worker(s) for s in sources])
