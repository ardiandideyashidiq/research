from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import numpy as np
from loguru import logger

from research.db.manager import DatabaseManager
from research.pdf.models import ConvertedDocument
from research.rag.chunker import SemanticChunker
from research.rag.embeddings import EmbeddingEngine
from research.rag.models import DocumentChunk, RetrievalResult

if TYPE_CHECKING:
    from research.putusan.models import PutusanDocument


class RAGRetriever:
    """Unified hybrid retrieval engine combining SQLite FTS5 BM25 and dense vector search via RRF."""

    def __init__(
        self,
        db: DatabaseManager,
        *,
        chunker: SemanticChunker | None = None,
        embeddings: EmbeddingEngine | None = None,
    ) -> None:
        self.db = db
        self.chunker = chunker or SemanticChunker()
        self.embeddings = embeddings or EmbeddingEngine()

    def index_document(
        self,
        doc: ConvertedDocument,
        *,
        cite_key: str,
        corpus: str = "literature",
        embed: bool = False,
    ) -> list[DocumentChunk]:
        """Semantically chunk and index a ConvertedDocument into SQLite FTS5."""
        self.db.delete_chunks(cite_key)

        chunks = self.chunker.chunk_document(doc, cite_key=cite_key, corpus=corpus)
        if chunks:
            chunk_dicts = [c.to_dict() for c in chunks]
            inserted = self.db.insert_chunks(chunk_dicts)
            self.db.update(cite_key, is_chunked=True)
            logger.info(
                "Indexed {} chunks for paper '{}' ({})",
                inserted,
                cite_key,
                doc.metadata.title[:40],
            )
            if embed:
                emb_map = self.embeddings.embed_chunks(chunk_dicts)
                self.db.save_chunk_embeddings(emb_map)
        return chunks

    def index_markdown(
        self,
        markdown: str,
        *,
        cite_key: str,
        paper_title: str,
        corpus: str = "literature",
        embed: bool = False,
    ) -> list[DocumentChunk]:
        """Semantically chunk and index raw Markdown text into SQLite FTS5."""
        self.db.delete_chunks(cite_key)

        chunks = self.chunker.chunk_markdown(
            markdown,
            cite_key=cite_key,
            paper_title=paper_title,
            corpus=corpus,
        )
        if chunks:
            chunk_dicts = [c.to_dict() for c in chunks]
            inserted = self.db.insert_chunks(chunk_dicts)
            self.db.update(cite_key, is_chunked=True)
            logger.info("Indexed {} chunks for '{}'", inserted, cite_key)
            if embed:
                emb_map = self.embeddings.embed_chunks(chunk_dicts)
                self.db.save_chunk_embeddings(emb_map)
        return chunks

    def index_putusan_document(
        self,
        doc: PutusanDocument,
        *,
        markdown_path: str | None = None,
        embed: bool = False,
    ) -> list[DocumentChunk]:
        """Index an Indonesian Putusan court decision into the unified RAG database."""
        from research.putusan.converter import PutusanConverter

        chunks = PutusanConverter.index_document_to_db(doc, self.db, markdown_path=markdown_path)
        if embed and chunks:
            chunk_dicts = [c.to_dict() for c in chunks]
            emb_map = self.embeddings.embed_chunks(chunk_dicts)
            self.db.save_chunk_embeddings(emb_map)
        return chunks

    def embed_all_chunks(self, *, batch_size: int = 64) -> int:
        """Compute and persist embeddings for all chunks lacking dense vectors."""
        unembedded = self.db.get_unembedded_chunks()
        if not unembedded:
            logger.info("All chunks already have vector embeddings.")
            return 0

        logger.info(
            "Generating dense embeddings for {} chunks using model '{}'...",
            len(unembedded),
            self.embeddings.model_name,
        )

        total_embedded = 0
        try:
            for i in range(0, len(unembedded), batch_size):
                batch = unembedded[i : i + batch_size]
                emb_map = self.embeddings.embed_chunks(batch)
                saved = self.db.save_chunk_embeddings(emb_map)
                total_embedded += saved
                logger.debug(
                    "Embedded chunks {}/{} (saved {})",
                    min(i + batch_size, len(unembedded)),
                    len(unembedded),
                    saved,
                )
        except KeyboardInterrupt:
            logger.warning(
                "Embedding generation interrupted by user. Saved {} chunk embeddings so far.",
                total_embedded,
            )
            raise

        logger.info("Successfully generated and saved {} chunk embeddings.", total_embedded)
        return total_embedded

    def search_bm25(
        self,
        query: str,
        *,
        limit: int = 5,
        cite_key: str | None = None,
        corpus: str | None = None,
    ) -> list[RetrievalResult]:
        """Search across indexed document chunks using SQLite FTS5 BM25."""
        clean_q = self._sanitize_fts_query(query)
        if not clean_q:
            return []

        rows = self.db.search_chunks(clean_q, limit=limit, cite_key=cite_key, corpus=corpus)
        results: list[RetrievalResult] = []

        for row in rows:
            chunk = DocumentChunk.from_dict(row)
            score = float(row.get("rank", 0.0))
            snippet = chunk.content[:300].strip() + ("..." if len(chunk.content) > 300 else "")
            results.append(
                RetrievalResult(chunk=chunk, score=score, snippet=snippet, retrieval_mode="bm25")
            )

        return results

    def search_dense(
        self,
        query: str,
        *,
        limit: int = 5,
        cite_key: str | None = None,
        corpus: str | None = None,
    ) -> list[RetrievalResult]:
        """Search across indexed chunks using dense semantic cosine similarity."""
        chunk_ids, matrix = self.db.get_all_embeddings(corpus=corpus, cite_key=cite_key)
        if matrix.shape[0] == 0:
            logger.debug("No dense embeddings found in database for search_dense.")
            return []

        query_vec = self.embeddings.embed_query(query)
        # Both vectors and matrix are L2-normalized; dot product equals cosine similarity
        scores = np.dot(matrix, query_vec)

        top_k = min(limit, len(chunk_ids))
        top_indices = np.argsort(scores)[::-1][:top_k]

        top_cids = [chunk_ids[idx] for idx in top_indices]
        chunks_map = self.db.get_chunks_by_ids(top_cids)

        results: list[RetrievalResult] = []
        for idx in top_indices:
            cid = chunk_ids[idx]
            row = chunks_map.get(cid)
            if not row:
                continue
            chunk = DocumentChunk.from_dict(row)
            sim_score = float(scores[idx])
            snippet = chunk.content[:300].strip() + ("..." if len(chunk.content) > 300 else "")
            results.append(
                RetrievalResult(
                    chunk=chunk,
                    score=sim_score,
                    snippet=snippet,
                    retrieval_mode="dense",
                )
            )

        return results

    def search_hybrid(
        self,
        query: str,
        *,
        limit: int = 5,
        cite_key: str | None = None,
        corpus: str | None = None,
        weight_bm25: float = 0.5,
        weight_dense: float = 0.5,
        k: int = 60,
    ) -> list[RetrievalResult]:
        """Hybrid search combining BM25 and Dense retrieval via Reciprocal Rank Fusion (RRF)."""
        candidate_limit = max(limit * 4, 30)

        bm25_results = self.search_bm25(
            query,
            limit=candidate_limit,
            cite_key=cite_key,
            corpus=corpus,
        )
        dense_results = self.search_dense(
            query,
            limit=candidate_limit,
            cite_key=cite_key,
            corpus=corpus,
        )

        if not dense_results:
            # Fall back to BM25 if no embeddings have been computed
            return bm25_results[:limit]
        if not bm25_results:
            return dense_results[:limit]

        # Reciprocal Rank Fusion
        rrf_scores: dict[str, float] = {}
        chunk_map: dict[str, DocumentChunk] = {}

        for rank, res in enumerate(bm25_results, start=1):
            cid = res.chunk.chunk_id
            chunk_map[cid] = res.chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + weight_bm25 * (1.0 / (k + rank))

        for rank, res in enumerate(dense_results, start=1):
            cid = res.chunk.chunk_id
            chunk_map[cid] = res.chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + weight_dense * (1.0 / (k + rank))

        # Sort chunk IDs by combined RRF score descending
        sorted_cids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:limit]

        fused_results: list[RetrievalResult] = []
        for cid in sorted_cids:
            chunk = chunk_map[cid]
            fused_score = float(rrf_scores[cid])
            snippet = chunk.content[:300].strip() + ("..." if len(chunk.content) > 300 else "")
            fused_results.append(
                RetrievalResult(
                    chunk=chunk,
                    score=fused_score,
                    snippet=snippet,
                    retrieval_mode="hybrid",
                )
            )

        return fused_results

    def search(
        self,
        query: str,
        *,
        mode: str = "hybrid",
        limit: int = 5,
        cite_key: str | None = None,
        corpus: str | None = None,
        **kwargs: Any,
    ) -> list[RetrievalResult]:
        """Unified search across indexed document chunks using hybrid, bm25, or dense mode."""
        if mode == "dense":
            return self.search_dense(query, limit=limit, cite_key=cite_key, corpus=corpus)
        if mode == "bm25":
            return self.search_bm25(query, limit=limit, cite_key=cite_key, corpus=corpus)
        # Default to hybrid
        return self.search_hybrid(
            query,
            limit=limit,
            cite_key=cite_key,
            corpus=corpus,
            **kwargs,
        )

    def _sanitize_fts_query(self, query: str) -> str:
        """Sanitize query string for safe SQLite FTS5 MATCH execution."""
        words = re.findall(r"\b[A-Za-z0-9_-]+\b", query)
        if not words:
            return ""
        return " OR ".join(f'"{w}"' for w in words[:12])

    def format_context(
        self,
        results: list[RetrievalResult],
        *,
        max_chars: int = 4500,
    ) -> str:
        """Format ranked retrieval results into clean markdown context for LLM prompts."""
        if not results:
            return "No relevant literature or legal excerpts found."

        parts: list[str] = ["## Relevant Academic & Legal Literature Excerpts\n"]
        current_len = 0

        for i, res in enumerate(results, start=1):
            citation = res.formatted_citation()
            mode_badge = f"*(match: {res.retrieval_mode}, score: {res.score:.4f})*"
            content = res.chunk.content.strip()
            block = f"### [{i}] {citation}\n{mode_badge}\n\n{content}\n"

            if current_len + len(block) > max_chars and i > 1:
                break

            parts.append(block)
            current_len += len(block)

        return "\n".join(parts)
