from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from research.db.models import PublicationRecord


@dataclass
class PipelineConfig:
    query: str
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
    query: str
    discovered_count: int = 0
    snowballed_count: int = 0
    downloaded_count: int = 0
    converted_count: int = 0
    indexed_chunks_count: int = 0
    records: list[PublicationRecord] = field(default_factory=list)
    duration_seconds: float = 0.0

    def summary(self) -> str:
        return (
            f"Pipeline Summary for '{self.query}':\n"
            f"  - Discovered: {self.discovered_count} papers\n"
            f"  - Snowballed: {self.snowballed_count} citations\n"
            f"  - Downloaded: {self.downloaded_count} PDFs\n"
            f"  - Converted:  {self.converted_count} Markdown documents\n"
            f"  - RAG Chunks: {self.indexed_chunks_count} indexed chunks\n"
            f"  - Duration:   {self.duration_seconds:.2f}s"
        )
