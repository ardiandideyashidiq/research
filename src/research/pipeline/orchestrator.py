from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from research.pipeline.models import PipelineConfig, PipelineResult

if TYPE_CHECKING:
    from research.app import ResearchApp
    from research.db.models import PublicationRecord


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

        if cfg.streaming:
            return await self._run_streaming(cfg)
        return await self._run_staged(cfg)

    async def _run_streaming(self, cfg: PipelineConfig) -> PipelineResult:
        """Execute fully parallel streaming pipeline with producer-consumer queues."""
        t0 = time.time()
        logger.info(
            "Starting Research Pipeline [STREAMING PARALLEL] (query='{}', bib_path={})",
            cfg.query,
            cfg.bib_path,
        )

        download_queue: asyncio.Queue[PublicationRecord | None] = asyncio.Queue()
        convert_queue: asyncio.Queue[PublicationRecord | None] = asyncio.Queue()
        queued_cite_keys: set[str] = set()

        stats = {
            "bib_count": 0,
            "discovered_count": 0,
            "snowballed_count": 0,
            "downloaded_count": 0,
            "converted_count": 0,
            "indexed_chunks_count": 0,
        }

        async def _enqueue_download(rec: PublicationRecord) -> None:
            if not cfg.download:
                return
            if rec.cite_key in queued_cite_keys:
                return
            queued_cite_keys.add(rec.cite_key)
            await download_queue.put(rec)

        # Worker for CPU-bound conversion and semantic chunking
        async def _convert_worker() -> None:
            while True:
                pub = await convert_queue.get()
                if pub is None:
                    convert_queue.task_done()
                    break

                try:
                    if not pub.download_path:
                        continue
                    pdf_path = Path(pub.download_path)
                    if not pdf_path.exists():
                        continue

                    md_path = pdf_path.with_suffix(".md")
                    out_path, conv_doc = await self.app.pdf.convert_file_async(pdf_path, md_path)
                    self.app.db.update(pub.cite_key, markdown_path=str(out_path))
                    stats["converted_count"] += 1

                    if cfg.index_rag:
                        chunks = await asyncio.to_thread(
                            self.app.retriever.index_document,
                            conv_doc,
                            cite_key=pub.cite_key,
                        )
                        stats["indexed_chunks_count"] += len(chunks)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Streaming conversion/chunking failed for {}: {}", pub.cite_key, exc)
                finally:
                    convert_queue.task_done()

        # Start conversion workers if convert enabled
        convert_workers: list[asyncio.Task] = []
        if cfg.convert:
            convert_workers = [
                asyncio.create_task(_convert_worker())
                for _ in range(max(1, cfg.convert_concurrency))
            ]

        # Start download workers if download enabled
        download_task: asyncio.Task | None = None
        if cfg.download:

            async def _run_downloads() -> None:
                dl_stats = await self.app.downloader.download_stream(
                    download_queue,
                    out_queue=convert_queue if cfg.convert else None,
                    concurrency=cfg.download_concurrency,
                )
                stats["downloaded_count"] = dl_stats.get("downloaded", 0)

            download_task = asyncio.create_task(_run_downloads())

        # Step 0: BibTeX Seed Ingestion
        bib_records: list[PublicationRecord] = []
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
                stats["bib_count"] = bib_count

                parsed_entries = parse_bib_files(path_list)
                for e in parsed_entries:
                    rec = self.app.db.get(e.cite_key)
                    if rec:
                        bib_records.append(rec)
                        if rec.download_status == "downloaded" and rec.download_path and cfg.convert:
                            if not Path(rec.download_path).with_suffix(".md").exists():
                                await convert_queue.put(rec)
                        elif rec.download_status != "downloaded":
                            await _enqueue_download(rec)

                logger.info("Pipeline Step 0: Ingested and enriched {} BibTeX seed papers", len(bib_records))
            except Exception as exc:  # noqa: BLE001
                logger.warning("BibTeX seed ingestion issue: {}", exc)

        # Step 1: Federated Discovery (academic providers + Google Scholar in parallel)
        discovered: list[PublicationRecord] = []
        if cfg.query:
            logger.info("Pipeline Step 1: Launching concurrent academic and Scholar discovery...")

            async def _search_academic() -> list[PublicationRecord]:
                try:
                    return await self.app.providers.search_all(
                        cfg.query,
                        providers=cfg.providers,
                        limit_per_provider=max(3, cfg.search_limit // 2),
                        auto_index=True,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Academic providers search issue: {}", exc)
                    return []

            async def _search_scholar() -> list[PublicationRecord]:
                if not cfg.include_scholar:
                    return []
                try:
                    return await self.app.search_scholar(
                        cfg.query,
                        limit=cfg.search_limit,
                        auto_index=True,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Google Scholar search issue: {}", exc)
                    return []

            search_results = await asyncio.gather(_search_academic(), _search_scholar())
            for res_list in search_results:
                for rec in res_list:
                    discovered.append(rec)
                    await _enqueue_download(rec)

            stats["discovered_count"] = len(discovered)
            logger.info("Pipeline Step 1: Discovered and indexed {} papers", len(discovered))

        # Step 2: Parallel Citation Graph Snowballing
        if cfg.snowball:
            candidate_seeds = bib_records + [r for r in discovered if r.doi or r.title]
            seeds = candidate_seeds[: cfg.snowball_seeds]
            if seeds:
                logger.info(
                    "Pipeline Step 2: Snowballing {} seed papers in parallel (concurrency={})...",
                    len(seeds),
                    cfg.snowball_concurrency,
                )
                self.app.snowball.config.limit_forward = cfg.snowball_limit
                self.app.snowball.config.limit_backward = cfg.snowball_limit
                self.app.snowball.config.concurrency = cfg.snowball_concurrency

                snowball_results = await self.app.snowball.snowball_records(seeds)
                for s_res in snowball_results:
                    stats["snowballed_count"] += s_res.forward_count + s_res.backward_count
                    for rec in s_res.discovered_records:
                        await _enqueue_download(rec)

                logger.info("Pipeline Step 2: Snowballed {} citation nodes", stats["snowballed_count"])

        # Discovery & Snowballing are complete -> close download queue
        if cfg.download:
            for _ in range(cfg.download_concurrency):
                await download_queue.put(None)
            if download_task:
                await download_task

        # Downloads are complete -> close convert queue
        if cfg.convert:
            for _ in range(max(1, cfg.convert_concurrency)):
                await convert_queue.put(None)
            if convert_workers:
                await asyncio.gather(*convert_workers)

        duration = time.time() - t0
        all_records = self.app.db.list(limit=200)

        result = PipelineResult(
            query=cfg.query,
            bib_count=stats["bib_count"],
            discovered_count=stats["discovered_count"],
            snowballed_count=stats["snowballed_count"],
            downloaded_count=stats["downloaded_count"],
            converted_count=stats["converted_count"],
            indexed_chunks_count=stats["indexed_chunks_count"],
            records=all_records,
            duration_seconds=duration,
        )
        logger.info("Streaming Pipeline completed successfully in {:.2f}s", duration)
        return result

    async def _run_staged(self, cfg: PipelineConfig) -> PipelineResult:
        """Execute parallel staged pipeline with explicit phase barriers."""
        t0 = time.time()
        logger.info(
            "Starting Research Pipeline [STAGED PARALLEL] (query='{}', bib_path={})",
            cfg.query,
            cfg.bib_path,
        )

        # 0. BibTeX Seed Ingestion & Enrichment (.bib)
        bib_records: list[PublicationRecord] = []
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

        # 1. Federated Literature Discovery (parallel providers + scholar)
        discovered: list[PublicationRecord] = []
        if cfg.query:

            async def _search_academic() -> list[PublicationRecord]:
                try:
                    return await self.app.providers.search_all(
                        cfg.query,
                        providers=cfg.providers,
                        limit_per_provider=max(3, cfg.search_limit // 2),
                        auto_index=True,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Academic providers search issue: {}", exc)
                    return []

            async def _search_scholar() -> list[PublicationRecord]:
                if not cfg.include_scholar:
                    return []
                try:
                    return await self.app.search_scholar(
                        cfg.query,
                        limit=cfg.search_limit,
                        auto_index=True,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Google Scholar search issue: {}", exc)
                    return []

            search_results = await asyncio.gather(_search_academic(), _search_scholar())
            for res_list in search_results:
                discovered.extend(res_list)

        discovered_count = len(discovered)
        logger.info("Pipeline Step 1: Discovered and indexed {} papers", discovered_count)

        # 2. Parallel Citation Graph Snowballing
        snowballed_count = 0
        if cfg.snowball:
            candidate_seeds = bib_records + [r for r in discovered if r.doi or r.title]
            seeds = candidate_seeds[: cfg.snowball_seeds]
            if seeds:
                self.app.snowball.config.limit_forward = cfg.snowball_limit
                self.app.snowball.config.limit_backward = cfg.snowball_limit
                self.app.snowball.config.concurrency = cfg.snowball_concurrency

                results = await self.app.snowball.snowball_records(seeds)
                for res in results:
                    snowballed_count += res.forward_count + res.backward_count

        logger.info("Pipeline Step 2: Snowballed {} citation nodes", snowballed_count)

        # 3. Open-Access Paper Downloading (download)
        downloaded_count = 0
        if cfg.download:
            dl_res = await self.app.downloader.download_all(concurrency=cfg.download_concurrency)
            downloaded_count = dl_res.get("downloaded", 0)

        logger.info("Pipeline Step 3: Verified and downloaded {} PDFs", downloaded_count)

        # 4. Parallel PDF to Markdown Conversion & RAG Indexing
        converted_count = 0
        indexed_chunks_count = 0

        if cfg.convert:
            downloaded_pubs = self.app.db.list(status="downloaded", limit=200)
            valid_pubs = [
                p for p in downloaded_pubs
                if p.download_path and Path(p.download_path).exists()
            ]

            sem = asyncio.Semaphore(cfg.convert_concurrency)

            async def _process_pub(pub: PublicationRecord) -> tuple[bool, int]:
                pdf_path = Path(pub.download_path)  # type: ignore[arg-type]
                md_path = pdf_path.with_suffix(".md")
                async with sem:
                    try:
                        out_path, conv_doc = await self.app.pdf.convert_file_async(pdf_path, md_path)
                        self.app.db.update(pub.cite_key, markdown_path=str(out_path))

                        chunks_len = 0
                        if cfg.index_rag:
                            chunks = await asyncio.to_thread(
                                self.app.retriever.index_document,
                                conv_doc,
                                cite_key=pub.cite_key,
                            )
                            chunks_len = len(chunks)
                        return True, chunks_len
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Conversion failed for {}: {}", pub.cite_key, exc)
                        return False, 0

            tasks = [_process_pub(p) for p in valid_pubs]
            processed = await asyncio.gather(*tasks)
            for ok, c_cnt in processed:
                if ok:
                    converted_count += 1
                indexed_chunks_count += c_cnt

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
