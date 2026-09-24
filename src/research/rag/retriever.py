from __future__ import annotations

import re

from loguru import logger

from research.db.manager import DatabaseManager
from research.pdf.models import ConvertedDocument
from research.rag.chunker import SemanticChunker
from research.rag.models import DocumentChunk, RetrievalResult


class RAGRetriever:
    """Hybrid/BM25 retrieval engine querying full document chunks via SQLite FTS5."""

    def __init__(
        self,
        db: DatabaseManager,
        *,
        chunker: SemanticChunker | None = None,
    ) -> None:
        self.db = db
        self.chunker = chunker or SemanticChunker()

    def index_document(
        self,
        doc: ConvertedDocument,
        *,
        cite_key: str,
    ) -> list[DocumentChunk]:
        """Semantically chunk and index a ConvertedDocument into SQLite FTS5."""
        # Clean existing chunks for this cite_key
        self.db.delete_chunks(cite_key)

        chunks = self.chunker.chunk_document(doc, cite_key=cite_key)
        if chunks:
            chunk_dicts = [c.to_dict() for c in chunks]
            inserted = self.db.insert_chunks(chunk_dicts)
            self.db.update(cite_key, is_chunked=True)
            logger.info("Indexed {} chunks for paper '{}' ({})", inserted, cite_key, doc.metadata.title[:40])
        return chunks

    def index_markdown(
        self,
        markdown: str,
        *,
        cite_key: str,
        paper_title: str,
    ) -> list[DocumentChunk]:
        """Semantically chunk and index raw Markdown text into SQLite FTS5."""
        self.db.delete_chunks(cite_key)

        chunks = self.chunker.chunk_markdown(markdown, cite_key=cite_key, paper_title=paper_title)
        if chunks:
            chunk_dicts = [c.to_dict() for c in chunks]
            inserted = self.db.insert_chunks(chunk_dicts)
            self.db.update(cite_key, is_chunked=True)
            logger.info("Indexed {} chunks for paper '{}'", inserted, cite_key)
        return chunks

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        cite_key: str | None = None,
    ) -> list[RetrievalResult]:
        """Search across all indexed document chunks using FTS5 BM25 ranking."""
        clean_q = self._sanitize_fts_query(query)
        if not clean_q:
            return []

        rows = self.db.search_chunks(clean_q, limit=limit, cite_key=cite_key)
        results: list[RetrievalResult] = []

        for row in rows:
            chunk = DocumentChunk.from_dict(row)
            score = float(row.get("rank", 0.0))
            # Generate snippet from content
            snippet = chunk.content[:300].strip() + ("..." if len(chunk.content) > 300 else "")
            results.append(RetrievalResult(chunk=chunk, score=score, snippet=snippet))

        return results

    def _sanitize_fts_query(self, query: str) -> str:
        """Sanitize query string for safe SQLite FTS5 MATCH execution."""
        # Strip FTS5 operators and special punctuation
        words = re.findall(r"\b[A-Za-z0-9_-]+\b", query)
        if not words:
            return ""
        # Match any of the key terms or match phrase
        return " OR ".join(f'"{w}"' for w in words[:12])

    def format_context(
        self,
        results: list[RetrievalResult],
        *,
        max_chars: int = 4000,
    ) -> str:
        """Format ranked retrieval results into clean markdown context for LLM prompts."""
        if not results:
            return "No relevant literature excerpts found."

        parts: list[str] = ["## Relevant Academic & Legal Literature Excerpts\n"]
        current_len = 0

        for i, res in enumerate(results, start=1):
            citation = res.formatted_citation()
            content = res.chunk.content.strip()
            block = f"### [{i}] {citation}\n\n{content}\n"

            if current_len + len(block) > max_chars and i > 1:
                break

            parts.append(block)
            current_len += len(block)

        return "\n".join(parts)
