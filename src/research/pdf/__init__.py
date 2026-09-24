from __future__ import annotations

from pathlib import Path

from research.pdf.converter import PDFConverter
from research.pdf.models import (
    ConversionOptions,
    ConvertedDocument,
    PageChunk,
    PDFMetadata,
    TableOfContentsItem,
)
from research.pdf.normalizer import (
    clean_headings,
    fix_hyphenation,
    fix_latex_accents,
    normalize_markdown_layout,
    normalize_unicode,
    reflow_paragraphs,
)


def convert_pdf_to_markdown(
    source: str | Path | bytes,
    *,
    pages: list[int] | int | None = None,
    reflow_paragraphs: bool = True,
    dehyphenate: bool = True,
    clean_headings: bool = True,
    normalize_accents: bool = True,
    include_frontmatter: bool = True,
    include_toc: bool = False,
    page_separators: bool = False,
) -> str:
    """Convenience function to convert a PDF into normalized markdown."""
    converter = PDFConverter()
    options = ConversionOptions(
        pages=pages,
        reflow_paragraphs=reflow_paragraphs,
        dehyphenate=dehyphenate,
        clean_headings=clean_headings,
        normalize_accents=normalize_accents,
        include_frontmatter=include_frontmatter,
        include_toc=include_toc,
        page_separators=page_separators,
    )
    return converter.convert_to_markdown(source, options=options)


__all__ = [
    "ConversionOptions",
    "ConvertedDocument",
    "PDFConverter",
    "PDFMetadata",
    "PageChunk",
    "TableOfContentsItem",
    "clean_headings",
    "convert_pdf_to_markdown",
    "fix_hyphenation",
    "fix_latex_accents",
    "normalize_markdown_layout",
    "normalize_unicode",
    "reflow_paragraphs",
]
