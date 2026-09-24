from __future__ import annotations

import re

from research.pdf.models import ConvertedDocument
from research.rag.models import DocumentChunk


class SemanticChunker:
    """Structure-aware chunker for academic and legal papers, preserving section hierarchy."""

    def __init__(
        self,
        *,
        max_chunk_chars: int = 1800,
        min_chunk_chars: int = 250,
        chunk_overlap_chars: int = 200,
    ) -> None:
        self.max_chunk_chars = max_chunk_chars
        self.min_chunk_chars = min_chunk_chars
        self.chunk_overlap_chars = chunk_overlap_chars

    def chunk_document(
        self,
        doc: ConvertedDocument,
        *,
        cite_key: str,
        corpus: str = "literature",
    ) -> list[DocumentChunk]:
        """Chunk a ConvertedDocument using per-page and section structural boundaries."""
        paper_title = doc.metadata.title or cite_key
        chunks: list[DocumentChunk] = []

        current_section = "Introduction"
        current_level = 1
        current_page = 1

        accumulated_text: list[str] = []
        page_start = 1
        chunk_index = 0

        def _flush(page_end: int) -> None:
            nonlocal accumulated_text, chunk_index, page_start
            text = "\n\n".join(accumulated_text).strip()
            if not text:
                return

            # If text exceeds max_chunk_chars, split on paragraph boundaries
            if len(text) > self.max_chunk_chars:
                paras = text.split("\n\n")
                sub_buf: list[str] = []
                sub_len = 0
                for p in paras:
                    if sub_len + len(p) > self.max_chunk_chars and sub_buf:
                        sub_text = "\n\n".join(sub_buf).strip()
                        if len(sub_text) >= self.min_chunk_chars or not chunks:
                            chunk_index += 1
                            chunks.append(
                                DocumentChunk(
                                    chunk_id=f"{cite_key}_c{chunk_index:03d}",
                                    cite_key=cite_key,
                                    paper_title=paper_title,
                                    section_title=current_section,
                                    section_level=current_level,
                                    page_start=page_start,
                                    page_end=page_end,
                                    content=sub_text,
                                    token_estimate=max(1, len(sub_text) // 4),
                                    corpus=corpus,
                                )
                            )
                        sub_buf = [p]
                        sub_len = len(p)
                    else:
                        sub_buf.append(p)
                        sub_len += len(p)

                if sub_buf:
                    sub_text = "\n\n".join(sub_buf).strip()
                    if sub_text:
                        chunk_index += 1
                        chunks.append(
                            DocumentChunk(
                                chunk_id=f"{cite_key}_c{chunk_index:03d}",
                                cite_key=cite_key,
                                paper_title=paper_title,
                                section_title=current_section,
                                section_level=current_level,
                                page_start=page_start,
                                page_end=page_end,
                                content=sub_text,
                                token_estimate=max(1, len(sub_text) // 4),
                                corpus=corpus,
                            )
                        )
            else:
                chunk_index += 1
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{cite_key}_c{chunk_index:03d}",
                        cite_key=cite_key,
                        paper_title=paper_title,
                        section_title=current_section,
                        section_level=current_level,
                        page_start=page_start,
                        page_end=page_end,
                        content=text,
                        token_estimate=max(1, len(text) // 4),
                        corpus=corpus,
                    )
                )

            accumulated_text = []
            page_start = page_end

        # Iterate through per-page chunks
        for page_chunk in doc.chunks:
            current_page = page_chunk.page_number
            # Check for section headings within the page text
            paragraphs = page_chunk.text.split("\n\n")

            for para in paragraphs:
                para_s = para.strip()
                if not para_s:
                    continue

                # Check if paragraph is a heading
                heading_match = re.match(r"^(#{1,3})\s+(.*)$", para_s)
                if heading_match:
                    h_level = len(heading_match.group(1))
                    h_text = heading_match.group(2).strip()

                    # If we have accumulated text and hit a major heading (H1 or H2), flush chunk
                    if accumulated_text and (h_level <= 2 or len("\n\n".join(accumulated_text)) > self.max_chunk_chars // 2):
                        _flush(page_end=current_page)

                    current_section = h_text
                    current_level = h_level
                    accumulated_text.append(para_s)
                else:
                    accumulated_text.append(para_s)
                    if len("\n\n".join(accumulated_text)) >= self.max_chunk_chars:
                        _flush(page_end=current_page)

        # Flush any remaining text
        if accumulated_text:
            _flush(page_end=current_page)

        return chunks

    def chunk_markdown(
        self,
        markdown: str,
        *,
        cite_key: str,
        paper_title: str,
        corpus: str = "literature",
    ) -> list[DocumentChunk]:
        """Chunk a raw Markdown string using headings and paragraphs."""
        chunks: list[DocumentChunk] = []
        paragraphs = markdown.split("\n\n")

        current_section = "Introduction"
        current_level = 1
        current_page = 1
        accumulated_text: list[str] = []
        chunk_index = 0

        for para in paragraphs:
            s = para.strip()
            if not s:
                continue

            # Detect page comment markers e.g. <!-- Page 2 -->
            pg_match = re.search(r"<!--\s*Page\s+(\d+)\s*-->", s)
            if pg_match:
                current_page = int(pg_match.group(1))

            heading_match = re.match(r"^(#{1,3})\s+(.*)$", s)
            if heading_match:
                if accumulated_text:
                    chunk_text = "\n\n".join(accumulated_text).strip()
                    if chunk_text:
                        chunk_index += 1
                        chunks.append(
                            DocumentChunk(
                                chunk_id=f"{cite_key}_c{chunk_index:03d}",
                                cite_key=cite_key,
                                paper_title=paper_title,
                                section_title=current_section,
                                section_level=current_level,
                                page_start=current_page,
                                page_end=current_page,
                                content=chunk_text,
                                token_estimate=max(1, len(chunk_text) // 4),
                                corpus=corpus,
                            )
                        )
                    accumulated_text = []

                current_section = heading_match.group(2).strip()
                current_level = len(heading_match.group(1))
                accumulated_text.append(s)
            else:
                accumulated_text.append(s)
                if len("\n\n".join(accumulated_text)) >= self.max_chunk_chars:
                    chunk_text = "\n\n".join(accumulated_text).strip()
                    if chunk_text:
                        chunk_index += 1
                        chunks.append(
                            DocumentChunk(
                                chunk_id=f"{cite_key}_c{chunk_index:03d}",
                                cite_key=cite_key,
                                paper_title=paper_title,
                                section_title=current_section,
                                section_level=current_level,
                                page_start=current_page,
                                page_end=current_page,
                                content=chunk_text,
                                token_estimate=max(1, len(chunk_text) // 4),
                                corpus=corpus,
                            )
                        )
                    accumulated_text = []

        if accumulated_text:
            chunk_text = "\n\n".join(accumulated_text).strip()
            if chunk_text:
                chunk_index += 1
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{cite_key}_c{chunk_index:03d}",
                        cite_key=cite_key,
                        paper_title=paper_title,
                        section_title=current_section,
                        section_level=current_level,
                        page_start=current_page,
                        page_end=current_page,
                        content=chunk_text,
                        token_estimate=max(1, len(chunk_text) // 4),
                        corpus=corpus,
                    )
                )

        return chunks
