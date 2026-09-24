from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from research.pipeline.models import PipelineConfig, PipelineResult

if TYPE_CHECKING:
    from research.app import ResearchApp


class ResearchPipeline:
    """Automated orchestrator coordinating discovery, snowballing, downloading, normalization, and RAG indexing."""

    def __init__(self, app: ResearchApp) -> None:
        self.app = app

    async def run(
        self,
        config: PipelineConfig | str,
        **kwargs: Any,
    ) -> PipelineResult:
        """Execute the end-to-end research lifecycle for a query."""
        if isinstance(config, str):
            cfg = PipelineConfig(query=config, **kwargs)
        else:
            cfg = config

        t0 = time.time()
        logger.info(
            "Starting Research Pipeline (query='{}', bib_path={})",
            cfg.query,
            cfg.bib_path,
        )

        # 0. BibTeX Seed Ingestion & Enrichment (.bib)
        bib_records: list[Any] = []
        bib_count = 0
        if cfg.bib_path:
            logger.info("Pipeline Step 0: Ingesting BibTeX seed from {}", cfg.bib_path)
            try:
                from research.bibtex.parser import parse_bib_files

                path_list = (
                    [Path(cfg.bib_path)]
                    if isinstance(cfg.bib_path, (str, Path))
                    else [Path(p) for p in cfg.bib_path]
                )
                bib_count = self.app.load_bib_files(path_list, auto_normalize=True)

                parsed_entries = parse_bib_files(path_list)
                for e in parsed_entries:
                    rec = self.app.db.get(e.cite_key)
                    if rec:
                        bib_records.append(rec)
                logger.info(
                    "Pipeline Step 0: Ingested and enriched {} BibTeX seed papers",
                    len(bib_records),
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("BibTeX seed ingestion issue: {}", exc)

        # 1. Federated Literature Discovery (search)
        discovered: list[Any] = []
        if cfg.query:
            try:
                academic_recs = await self.app.providers.search_all(
                    cfg.query,
                    providers=cfg.providers,
                    limit_per_provider=max(3, cfg.search_limit // 2),
                    auto_index=True,
                )
                discovered.extend(academic_recs)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Academic providers search issue: {}", exc)

            if cfg.include_scholar:
                try:
                    scholar_recs = await self.app.search_scholar(
                        cfg.query,
                        limit=cfg.search_limit,
                        auto_index=True,
                    )
                    discovered.extend(scholar_recs)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Google Scholar search issue: {}", exc)

        discovered_count = len(discovered)
        logger.info("Pipeline Step 1: Discovered and indexed {} papers", discovered_count)

        # 2. Citation Graph Snowballing (snowball)
        snowballed_count = 0
        if cfg.snowball:
            # Combine .bib seeds and search discovery seeds
            candidate_seeds = bib_records + [r for r in discovered if r.doi or r.title]
            seeds = candidate_seeds[: cfg.snowball_seeds]
            for seed in seeds:
                try:
                    self.app.snowball.config.limit_forward = cfg.snowball_limit
                    self.app.snowball.config.limit_backward = cfg.snowball_limit
                    res = await self.app.snowball.snowball_record(seed)
                    snowballed_count += res.forward_count + res.backward_count
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Snowballing skipped for {}: {}", seed.cite_key, exc)

        logger.info("Pipeline Step 2: Snowballed {} citation nodes", snowballed_count)

        # 3. Open-Access Paper Downloading (download)
        downloaded_count = 0
        if cfg.download:
            dl_res = await self.app.downloader.download_all()
            downloaded_count = dl_res.get("downloaded", 0)

        logger.info("Pipeline Step 3: Verified and downloaded {} PDFs", downloaded_count)

        # 4. PDF to Markdown Conversion & Layout Normalization (convert)
        converted_count = 0
        indexed_chunks_count = 0

        if cfg.convert:
            downloaded_pubs = self.app.db.list(status="downloaded", limit=200)
            for pub in downloaded_pubs:
                if not pub.download_path:
                    continue
                pdf_path = Path(pub.download_path)
                if not pdf_path.exists():
                    continue

                md_path = pdf_path.with_suffix(".md")
                try:
                    # Convert PDF with layout normalization
                    conv_doc = self.app.pdf.convert(pdf_path)
                    md_path.write_text(conv_doc.markdown, encoding="utf-8")
                    self.app.db.update(pub.cite_key, markdown_path=str(md_path))
                    converted_count += 1

                    # 5. Semantic Chunking & RAG FTS5 Indexing (semantic chunking & index)
                    if cfg.index_rag:
                        chunks = self.app.retriever.index_document(
                            conv_doc, cite_key=pub.cite_key
                        )
                        indexed_chunks_count += len(chunks)

                except Exception as exc:  # noqa: BLE001
                    logger.warning("Conversion failed for {}: {}", pub.cite_key, exc)

        logger.info(
            "Pipeline Step 4 & 5: Converted {} documents and indexed {} semantic chunks",
            converted_count,
            indexed_chunks_count,
        )

        duration = time.time() - t0
        all_records = self.app.db.list(limit=200)

        result = PipelineResult(
            query=cfg.query,
            bib_count=bib_count,
            discovered_count=discovered_count,
            snowballed_count=snowballed_count,
            downloaded_count=downloaded_count,
            converted_count=converted_count,
            indexed_chunks_count=indexed_chunks_count,
            records=all_records,
            duration_seconds=duration,
        )
        logger.info("Pipeline completed successfully in {:.2f}s", duration)
        return result

    def run_sync(
        self,
        config: PipelineConfig | str,
        **kwargs: Any,
    ) -> PipelineResult:
        """Synchronous wrapper for pipeline execution."""
        return asyncio.run(self.run(config, **kwargs))
