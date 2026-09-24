from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from loguru import logger

if TYPE_CHECKING:
    from fastembed import TextEmbedding

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class EmbeddingEngine:
    """Fast, local ONNX-powered multilingual text embedding engine using fastembed."""

    def __init__(
        self,
        *,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        batch_size: int = 32,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self._model: TextEmbedding | None = None

    def _get_model(self) -> TextEmbedding:
        """Lazily initialize the embedding model on first use."""
        if self._model is None:
            logger.info("Initializing embedding engine with model: {}", self.model_name)
            try:
                from fastembed import TextEmbedding

                self._model = TextEmbedding(model_name=self.model_name)
            except Exception as exc:
                logger.error("Failed to load fastembed model '{}': {}", self.model_name, exc)
                raise
        return self._model

    def embed_query(self, query: str) -> np.ndarray:
        """Compute an L2-normalized 1D float32 embedding for a search query."""
        model = self._get_model()
        # fastembed query embedding returns a generator of numpy arrays
        generator = model.embed([query])
        vec = next(generator).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def embed_documents(
        self,
        texts: list[str],
        *,
        batch_size: int | None = None,
    ) -> np.ndarray:
        """Compute L2-normalized 2D float32 embeddings for a batch of documents."""
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        model = self._get_model()
        bs = batch_size or self.batch_size
        raw_embs = list(model.embed(texts, batch_size=bs))
        matrix = np.vstack([e.astype(np.float32) for e in raw_embs])

        # L2-normalize each row so dot product equals cosine similarity
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms

    def embed_chunks(
        self,
        chunks: list[dict[str, Any]],
        *,
        batch_size: int | None = None,
    ) -> dict[str, np.ndarray]:
        """Compute embeddings for a list of chunk dictionaries, returning {chunk_id: vec}."""
        if not chunks:
            return {}

        texts: list[str] = []
        chunk_ids: list[str] = []

        for c in chunks:
            chunk_ids.append(c["chunk_id"])
            # Prefix with title and section if available for higher retrieval quality
            prefix_parts = []
            if c.get("paper_title"):
                prefix_parts.append(c["paper_title"])
            if c.get("section_title"):
                prefix_parts.append(c["section_title"])

            prefix = " | ".join(prefix_parts)
            content = c.get("content", "")
            full_text = f"{prefix}\n\n{content}" if prefix else content
            texts.append(full_text)

        matrix = self.embed_documents(texts, batch_size=batch_size)
        return {cid: matrix[idx] for idx, cid in enumerate(chunk_ids)}
