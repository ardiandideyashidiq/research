from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PDFMetadata:
    title: str = ""
    author: str = ""
    subject: str = ""
    keywords: str = ""
    creator: str = ""
    producer: str = ""
    creation_date: str = ""
    page_count: int = 0
    file_size: int | None = None
    file_path: str | None = None


@dataclass
class TableOfContentsItem:
    level: int
    title: str
    page: int


@dataclass
class PageChunk:
    page_number: int
    text: str
    raw_text: str = ""
    images: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversionOptions:
    pages: list[int] | int | None = None
    extract_images: bool = False
    embed_images: bool = False
    image_dir: str | Path | None = None
    image_format: str = "png"
    table_output: str = "markdown"
    reflow_paragraphs: bool = True
    dehyphenate: bool = True
    clean_headings: bool = True
    normalize_accents: bool = True
    strip_headers_footers: bool = True
    include_frontmatter: bool = True
    include_toc: bool = False
    page_separators: bool = False
    use_ocr: bool = False
    dpi: int = 150


@dataclass
class ConvertedDocument:
    markdown: str
    metadata: PDFMetadata
    toc: list[TableOfContentsItem] = field(default_factory=list)
    chunks: list[PageChunk] = field(default_factory=list)
    total_pages: int = 0
    image_paths: list[str] = field(default_factory=list)
