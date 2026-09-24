from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from research.db.models import PublicationRecord
from research.rag.chunker import SemanticChunker
from research.web_search.normalizer import format_web_markdown

if TYPE_CHECKING:
    from research.db.manager import DatabaseManager
    from research.web_search.models import WebSearchResult


class WebSearchIndexer:
    """Extracts web search results into clean Markdown documents and indexes them into SQLite FTS5."""

    def __init__(
        self,
        db: DatabaseManager,
        *,
        output_dir: str | Path = "data/web_searches",
        max_chunk_chars: int = 1500,
    ) -> None:
        self.db = db
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chunker = SemanticChunker(max_chunk_chars=max_chunk_chars)

    def index_result(
        self,
        result: WebSearchResult,
        *,
        chunk_rag: bool = True,
    ) -> tuple[Path, int]:
        """Convert a single web search result into Markdown and index into database."""
        # 1. Format clean Markdown with YAML frontmatter
        md_content = format_web_markdown(result)
        result.markdown_content = md_content

        # 2. Write Markdown to disk
        md_file = self.output_dir / f"{result.cite_key}.md"
        md_file.write_text(md_content, encoding="utf-8")

        # 3. Create or update PublicationRecord in SQLite
        record = PublicationRecord(
            cite_key=result.cite_key,
            entry_type="online",
            title=result.title,
            authors=[result.source_domain] if result.source_domain else [],
            journal=result.source_domain,
            url=result.url,
            abstract=result.content,
            sources=[result.provider],
            download_status="downloaded",
            download_path=str(md_file),
            markdown_path=str(md_file),
            is_chunked=chunk_rag,
            raw_fields={
                "provider": result.provider,
                "query": result.query,
                "published_date": result.published_date or "",
            },
        )
        self.db.create(record)

        # 4. Semantic chunking and RAG indexing
        chunk_count = 0
        if chunk_rag:
            chunks = self.chunker.chunk_markdown(
                md_content,
                cite_key=result.cite_key,
                paper_title=result.title,
                corpus="web",
            )
            if chunks:
                self.db.insert_chunks([c.to_dict() for c in chunks])
                chunk_count = len(chunks)

        logger.debug(
            f"Indexed web result '{result.cite_key}': saved MD ({md_file.name}), "
            f"indexed {chunk_count} RAG chunks."
        )
        return md_file, chunk_count

    def index_results(
        self,
        results: list[WebSearchResult],
        *,
        chunk_rag: bool = True,
    ) -> dict[str, int]:
        """Batch index multiple web search results."""
        total_docs = 0
        total_chunks = 0

        for r in results:
            try:
                _, chunks_cnt = self.index_result(r, chunk_rag=chunk_rag)
                total_docs += 1
                total_chunks += chunks_cnt
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed indexing result '{r.url}': {e}")

        logger.info(
            f"Web search indexer: {total_docs} documents saved & {total_chunks} chunks indexed into SQLite RAG."
        )
        return {
            "indexed_documents": total_docs,
            "indexed_chunks": total_chunks,
        }
