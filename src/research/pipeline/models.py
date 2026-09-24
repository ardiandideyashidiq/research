from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from research.db.models import PublicationRecord


@dataclass
class PipelineConfig:
    query: str = ""
    bib_path: str | Path | list[str | Path] | None = None
    providers: list[str] | None = None
    search_limit: int = 15
    include_scholar: bool = True
    snowball: bool = True
    snowball_seeds: int = 2
    snowball_limit: int = 8
    download: bool = True
    download_concurrency: int = 4
    convert: bool = True
    index_rag: bool = True


@dataclass
class PipelineResult:
    query: str = ""
    bib_count: int = 0
    discovered_count: int = 0
    snowballed_count: int = 0
    downloaded_count: int = 0
    converted_count: int = 0
    indexed_chunks_count: int = 0
    records: list[PublicationRecord] = field(default_factory=list)
    duration_seconds: float = 0.0

    def summary(self) -> str:
        target_name = self.query or "BibTeX Seed Corpus"
        lines = [f"Pipeline Summary for '{target_name}':"]
        if self.bib_count > 0:
            lines.append(f"  - BibTeX Seeds: {self.bib_count} papers loaded & enriched")
        lines.extend([
            f"  - Discovered:   {self.discovered_count} papers",
            f"  - Snowballed:   {self.snowballed_count} citations",
            f"  - Downloaded:   {self.downloaded_count} PDFs",
            f"  - Converted:    {self.converted_count} Markdown documents",
            f"  - RAG Chunks:   {self.indexed_chunks_count} indexed chunks",
            f"  - Duration:     {self.duration_seconds:.2f}s",
        ])
        return "\n".join(lines)
