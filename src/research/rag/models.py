from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class DocumentChunk:
    chunk_id: str
    cite_key: str
    paper_title: str
    section_title: str | None = None
    section_level: int | None = None
    page_start: int | None = None
    page_end: int | None = None
    content: str = ""
    token_estimate: int = 0
    corpus: str = "literature"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentChunk:
        return cls(
            chunk_id=data["chunk_id"],
            cite_key=data["cite_key"],
            paper_title=data["paper_title"],
            section_title=data.get("section_title"),
            section_level=data.get("section_level"),
            page_start=data.get("page_start"),
            page_end=data.get("page_end"),
            content=data.get("content", ""),
            token_estimate=data.get("token_estimate", max(1, len(data.get("content", "")) // 4)),
            corpus=data.get("corpus", "literature"),
        )


@dataclass
class RetrievalResult:
    chunk: DocumentChunk
    score: float
    snippet: str = ""
    retrieval_mode: str = "bm25"

    def formatted_citation(self) -> str:
        badge = ""
        if self.chunk.corpus == "putusan":
            badge = "[PUTUSAN] "
        elif self.chunk.corpus == "web":
            badge = "[WEB] "
        elif self.chunk.corpus == "literature":
            badge = "[ACADEMIC] "

        sec = f" > {self.chunk.section_title}" if self.chunk.section_title else ""
        pg = f" (p. {self.chunk.page_start})" if self.chunk.page_start else ""
        return f"{badge}[{self.chunk.cite_key}] {self.chunk.paper_title}{sec}{pg}"
