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


_CLIENT: Any = None


async def _get_unpaywall_client(timeout: float) -> Any:
    """Return a run-scoped Unpaywall client, creating it on first use."""
    global _CLIENT
    if _CLIENT is None:
        from research.unpaywall.client import UnpaywallClient

        _CLIENT = UnpaywallClient(timeout=timeout, cache=_CACHE)
    return _CLIENT


async def _close_unpaywall_client() -> None:
    global _CLIENT
    if _CLIENT is not None:
        try:
            await _CLIENT.close()
        except Exception as e:  # noqa: BLE001 - teardown is best-effort
            logger.debug("Unpaywall client close failed: {}", e)
        _CLIENT = None


async def _resolve_unpaywall(doi: str, timeout: float) -> str | None:
    """Look up an open-access PDF URL for a DOI, tolerating network failure.

    Unpaywall is a best-effort enrichment: a miss must never abort the run, and
    a per-DOI failure is logged and skipped rather than raised.
    """
    try:
        client = await _get_unpaywall_client(timeout)
        return await client.get_best_pdf_url(doi)
    except Exception as e:  # noqa: BLE001 - enrichment is best-effort
        logger.debug("Unpaywall lookup failed for {}: {}", doi, e)
        return None


_CACHE: Any = None


class ResearchPipeline:
    """Automated orchestrator coordinating discovery, snowballing, downloading, normalization, and RAG indexing."""

    def __init__(self, app: ResearchApp) -> None:
        self.app = app
        global _CACHE
        if _CACHE is None:
            _CACHE = app.cache

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

        try:
            if cfg.streaming:
                return await self._run_streaming(cfg)
            return await self._run_staged(cfg)
        finally:
            # The Unpaywall client is run-scoped; never leak its session.
            await _close_unpaywall_client()

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
            "unpaywall_resolved_count": 0,
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
            # Resolve an open-access PDF before downloading: a record discovered
            # through search/snowball often has a DOI but no direct link, and the
            # downloader has nothing to fetch without one.
            if cfg.unpaywall and not rec.pdf_url and rec.doi:
                rec.pdf_url = await _resolve_unpaywall(rec.doi, cfg.unpaywall_timeout)
                if rec.pdf_url:
                    stats["unpaywall_resolved_count"] += 1
                    self.app.db.update(rec.cite_key, pdf_url=rec.pdf_url)
            await download_queue.put(rec)

        # Worker for CPU-bound conversion and semantic chunking
        async def _convert_worker() -> None:
            while True:
                try:
                    pub = await convert_queue.get()
                except (asyncio.CancelledError, KeyboardInterrupt):
                    break
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
                    is_already_converted = md_path.is_file() and md_path.stat().st_size > 0
                    has_db_chunks = self.app.db.has_chunks(pub.cite_key)
                    is_already_chunked = pub.is_chunked or has_db_chunks

                    # Ensure DB tracks markdown_path and is_chunked
                    if is_already_converted and not pub.markdown_path:
                        self.app.db.update(pub.cite_key, markdown_path=str(md_path))
                        pub.markdown_path = str(md_path)
                    if has_db_chunks and not pub.is_chunked:
                        self.app.db.update(pub.cite_key, is_chunked=True)
                        pub.is_chunked = True

                    # 1. Fast-path: already converted and already indexed in RAG
                    if not cfg.force and is_already_converted and (not cfg.index_rag or is_already_chunked):
                        c_cnt = self.app.db.count_chunks_for(pub.cite_key) if cfg.index_rag and is_already_chunked else 0
                        logger.info(
                            "Paper '{}': Reusing existing Markdown and {} indexed RAG chunks",
                            pub.cite_key,
                            c_cnt,
                        )
                        stats["converted_count"] += 1
                        if cfg.index_rag and is_already_chunked:
                            stats["indexed_chunks_count"] += c_cnt
                        continue

                    # 2. Markdown exists, but not yet indexed in RAG: index directly without PyMuPDF re-conversion
                    if not cfg.force and is_already_converted and cfg.index_rag and not is_already_chunked:
                        logger.info(
                            "Paper '{}': Reusing existing Markdown, indexing RAG chunks directly...",
                            pub.cite_key,
                        )
                        md_text = md_path.read_text(encoding="utf-8")
                        chunks = await asyncio.to_thread(
                            self.app.retriever.index_markdown,
                            md_text,
                            cite_key=pub.cite_key,
                            paper_title=pub.title,
                        )
                        stats["converted_count"] += 1
                        stats["indexed_chunks_count"] += len(chunks)
                        continue

                    # 3. Full conversion & RAG chunking
                    logger.info("Paper '{}': Converting PDF to Markdown ({})...", pub.cite_key, pdf_path.name)
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
                except (asyncio.CancelledError, KeyboardInterrupt):
                    raise
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Streaming conversion/chunking failed for {}: {}", pub.cite_key, exc)
                finally:
                    convert_queue.task_done()

        # Start conversion workers if convert enabled
        convert_workers: list[asyncio.Task[None]] = []
        download_task: asyncio.Task[None] | None = None

        try:
            if cfg.convert:
                convert_workers = [
                    asyncio.create_task(_convert_worker())
                    for _ in range(max(1, cfg.convert_concurrency))
                ]

            # Start download workers if download enabled
            if cfg.download:
                self.app.downloader.timeout = cfg.download_timeout

                async def _run_downloads() -> None:
                    dl_stats = await self.app.downloader.download_stream(
                        download_queue,
                        out_queue=convert_queue if cfg.convert else None,
                        concurrency=cfg.download_concurrency,
                        force=cfg.force,
                    )
                    stats["downloaded_count"] = dl_stats.get("downloaded", 0)

                download_task = asyncio.create_task(_run_downloads())

            # Step 0: BibTeX Seed Ingestion
            bib_records: list[PublicationRecord] = []
            if cfg.bib_path:
                try:
                    from research.bibtex.parser import expand_bib_paths, parse_bib_files

                    bib_files = expand_bib_paths(cfg.bib_path)
                    if not bib_files:
                        logger.warning("Pipeline Step 0: No .bib files found at {}", cfg.bib_path)
                    else:
                        if len(bib_files) == 1 and Path(cfg.bib_path).is_file():
                            logger.info("Pipeline Step 0: Ingesting BibTeX seed from {}", cfg.bib_path)
                        else:
                            logger.info(
                                "Pipeline Step 0: Ingesting BibTeX seeds from {} ({} .bib files found)",
                                cfg.bib_path,
                                len(bib_files),
                            )

                        bib_count = self.app.load_bib_files(bib_files, auto_normalize=False)
                        stats["bib_count"] = bib_count

                        parsed_entries = parse_bib_files(bib_files)
                        already_dl = 0
                        already_unavail = 0
                        pending_dl = 0
                        for e in parsed_entries:
                            rec = self.app.db.get(e.cite_key)
                            if rec:
                                bib_records.append(rec)
                                if rec.download_status == "downloaded":
                                    already_dl += 1
                                    md_exists = (
                                        Path(rec.download_path).with_suffix(".md").exists()
                                        if rec.download_path
                                        else False
                                    )
                                    has_chunks = rec.is_chunked or self.app.db.has_chunks(rec.cite_key)
                                    if cfg.force or not md_exists or (cfg.index_rag and not has_chunks):
                                        await convert_queue.put(rec)
                                elif rec.download_status in (
                                    "no_pdf_found",
                                    "failed_not_pdf",
                                    "dead_link",
                                    "failed_blocked",
                                ):
                                    already_unavail += 1
                                    if cfg.force:
                                        await _enqueue_download(rec)
                                else:
                                    pending_dl += 1
                                    await _enqueue_download(rec)

                        logger.info(
                            "Pipeline Step 0: Ingested {} BibTeX seed papers from {} file(s) ({} downloaded, {} unavailable, {} pending download)",
                            len(bib_records),
                            len(bib_files),
                            already_dl,
                            already_unavail,
                            pending_dl,
                        )
                except (asyncio.CancelledError, KeyboardInterrupt):
                    raise
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
                    except (asyncio.CancelledError, KeyboardInterrupt):
                        raise
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
                    except (asyncio.CancelledError, KeyboardInterrupt):
                        raise
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Google Scholar search issue: {}", exc)
                        return []

                search_tasks = [
                    asyncio.create_task(_search_academic()),
                    asyncio.create_task(_search_scholar()),
                ]
                try:
                    search_results = await asyncio.gather(*search_tasks)
                except (asyncio.CancelledError, KeyboardInterrupt):
                    for t in search_tasks:
                        if not t.done():
                            t.cancel()
                    await asyncio.gather(*search_tasks, return_exceptions=True)
                    raise

                for res_list in search_results:
                    for rec in res_list:
                        discovered.append(rec)
                        await _enqueue_download(rec)

                stats["discovered_count"] = len(discovered)
                already_in_db = sum(1 for r in discovered if r.download_status == "downloaded")
                logger.info(
                    "Pipeline Step 1: Discovered and indexed {} papers ({} already downloaded, {} queued)",
                    len(discovered),
                    already_in_db,
                    len(discovered) - already_in_db,
                )

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
                logger.info(
                    "Pipeline Step 3: Paper download phase finished ({} PDFs downloaded/verified)",
                    stats["downloaded_count"],
                )

            # Downloads are complete -> close convert queue
            if cfg.convert:
                for _ in range(max(1, cfg.convert_concurrency)):
                    await convert_queue.put(None)
                if convert_workers:
                    await asyncio.gather(*convert_workers)
                logger.info(
                    "Pipeline Step 4 & 5: Converted/verified {} documents and indexed {} total semantic chunks",
                    stats["converted_count"],
                    stats["indexed_chunks_count"],
                )

        except (asyncio.CancelledError, KeyboardInterrupt):
            logger.warning("Pipeline streaming execution interrupted. Cancelling worker tasks...")
            raise
        finally:
            if download_task and not download_task.done():
                download_task.cancel()
            for w in convert_workers:
                if not w.done():
                    w.cancel()
            all_to_cancel = [t for t in [download_task, *convert_workers] if t and not t.done()]
            if all_to_cancel:
                await asyncio.gather(*all_to_cancel, return_exceptions=True)

        duration = time.time() - t0
        all_records = self.app.db.list(limit=200)

        result = PipelineResult(
            query=cfg.query,
            bib_count=stats["bib_count"],
            discovered_count=stats["discovered_count"],
            snowballed_count=stats["snowballed_count"],
            unpaywall_resolved_count=stats["unpaywall_resolved_count"],
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
            try:
                from research.bibtex.parser import expand_bib_paths, parse_bib_files

                bib_files = expand_bib_paths(cfg.bib_path)
                if not bib_files:
                    logger.warning("Pipeline Step 0: No .bib files found at {}", cfg.bib_path)
                else:
                    if len(bib_files) == 1 and Path(cfg.bib_path).is_file():
                        logger.info("Pipeline Step 0: Ingesting BibTeX seed from {}", cfg.bib_path)
                    else:
                        logger.info(
                            "Pipeline Step 0: Ingesting BibTeX seeds from {} ({} .bib files found)",
                            cfg.bib_path,
                            len(bib_files),
                        )

                    bib_count = self.app.load_bib_files(bib_files, auto_normalize=False)
                    parsed_entries = parse_bib_files(bib_files)
                    for e in parsed_entries:
                        rec = self.app.db.get(e.cite_key)
                        if rec:
                            bib_records.append(rec)
                    logger.info(
                        "Pipeline Step 0: Ingested and enriched {} BibTeX seed papers from {} file(s)",
                        len(bib_records),
                        len(bib_files),
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

            search_tasks = [
                asyncio.create_task(_search_academic()),
                asyncio.create_task(_search_scholar()),
            ]
            try:
                search_results = await asyncio.gather(*search_tasks)
            except (asyncio.CancelledError, KeyboardInterrupt):
                for t in search_tasks:
                    if not t.done():
                        t.cancel()
                await asyncio.gather(*search_tasks, return_exceptions=True)
                raise

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
        unpaywall_resolved_count = 0
        if cfg.download:
            # Resolve open-access links first: records discovered through
            # search/snowball frequently carry a DOI but no direct PDF URL, and
            # the downloader has nothing to fetch without one.
            if cfg.unpaywall:
                for rec in self.app.db.list(limit=200):
                    if rec.pdf_url or not rec.doi:
                        continue
                    url = await _resolve_unpaywall(rec.doi, cfg.unpaywall_timeout)
                    if url:
                        rec.pdf_url = url
                        unpaywall_resolved_count += 1
                        self.app.db.update(rec.cite_key, pdf_url=url)
                if unpaywall_resolved_count:
                    logger.info(
                        "Pipeline Step 2.5: Unpaywall resolved {} open-access links",
                        unpaywall_resolved_count,
                    )
            self.app.downloader.timeout = cfg.download_timeout
            dl_res = await self.app.downloader.download_all(
                concurrency=cfg.download_concurrency,
                force=cfg.force,
            )
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
                is_already_converted = md_path.is_file() and md_path.stat().st_size > 0
                has_db_chunks = self.app.db.has_chunks(pub.cite_key)
                is_already_chunked = pub.is_chunked or has_db_chunks

                # Ensure DB tracks markdown_path and is_chunked
                if is_already_converted and not pub.markdown_path:
                    self.app.db.update(pub.cite_key, markdown_path=str(md_path))
                    pub.markdown_path = str(md_path)
                if has_db_chunks and not pub.is_chunked:
                    self.app.db.update(pub.cite_key, is_chunked=True)
                    pub.is_chunked = True

                # 1. Fast-path: already converted and already indexed in RAG
                if not cfg.force and is_already_converted and (not cfg.index_rag or is_already_chunked):
                    logger.debug("Paper '{}' already converted and indexed in RAG. Skipping.", pub.cite_key)
                    c_count = self.app.db.count_chunks_for(pub.cite_key) if cfg.index_rag and is_already_chunked else 0
                    return True, c_count

                async with sem:
                    try:
                        # 2. Markdown exists, but not yet indexed in RAG: index directly without PyMuPDF
                        if not cfg.force and is_already_converted and cfg.index_rag and not is_already_chunked:
                            md_text = md_path.read_text(encoding="utf-8")
                            chunks = await asyncio.to_thread(
                                self.app.retriever.index_markdown,
                                md_text,
                                cite_key=pub.cite_key,
                                paper_title=pub.title,
                            )
                            return True, len(chunks)

                        # 3. Full conversion & RAG chunking
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
                    except (asyncio.CancelledError, KeyboardInterrupt):
                        raise
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Conversion failed for {}: {}", pub.cite_key, exc)
                        return False, 0

            tasks = [asyncio.create_task(_process_pub(p)) for p in valid_pubs]
            try:
                processed = await asyncio.gather(*tasks)
            except (asyncio.CancelledError, KeyboardInterrupt):
                for t in tasks:
                    if not t.done():
                        t.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                raise

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
            unpaywall_resolved_count=unpaywall_resolved_count,
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
