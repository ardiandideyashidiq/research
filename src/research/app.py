from __future__ import annotations

import asyncio
from pathlib import Path
from types import TracebackType
from typing import Any, Self

from loguru import logger

from research.bibliography.manager import BibliographyManager
from research.bibtex.parser import expand_bib_paths, parse_bib_files
from research.cache.manager import HttpCache
from research.cache.models import CachePolicy
from research.cards.manager import CardManager
from research.db.manager import DatabaseManager
from research.db.models import PublicationRecord
from research.downloader.downloader import DownloadManager
from research.google_scholar.client import GoogleScholarClient
from research.normalizer.normalizer import normalize_record
from research.normative.irac import IRACManager
from research.normative.scaffold import ThesisScaffolder
from research.normative.traceability import TraceabilityAuditor
from research.normative.workflow import WorkflowManager
from research.pdf.converter import PDFConverter
from research.pdf.models import ConversionOptions, ConvertedDocument
from research.pipeline.models import PipelineConfig, PipelineResult
from research.pipeline.orchestrator import ResearchPipeline
from research.providers.registry import ProviderRegistry
from research.proxy.models import Proxy
from research.proxy.pool import ProxyPool
from research.rag.models import RetrievalResult
from research.rag.retriever import RAGRetriever
from research.snowball.models import SnowballConfig, SnowballResult
from research.snowball.orchestrator import SnowballOrchestrator
from research.tavily.client import TavilyClient
from research.web_search.client import WebSearchEngine
from research.web_search.models import WebSearchProvider, WebSearchResponse


class ResearchApp:
    """Unified application facade orchestrating storage, literature providers, OJS, snowballing, downloading, and web search."""

    def __init__(
        self,
        *,
        db_path: str | Path = "tmp/publications.sqlite",
        download_dir: str | Path = "data/downloads",
        web_search_dir: str | Path = "data/web_searches",
        tavily_keys: list[str] | None = None,
        scholar_proxy: str | Proxy | None = None,
        proxy_pool: ProxyPool | None = None,
        cache_policy: CachePolicy | None = None,
        cache_db_path: str | Path | None = None,
        log_dir: str | Path | None = None,
        auto_log: bool = False,
    ) -> None:
        if auto_log:
            from research.cli.main import setup_logging

            setup_logging(log_dir=log_dir or "logs")

        self.db = DatabaseManager(db_path)
        self.cache = HttpCache(db_path=cache_db_path or db_path, policy=cache_policy)
        self.providers = ProviderRegistry(db=self.db, cache=self.cache)
        self.downloader = DownloadManager(
            self.db, download_dir=download_dir, cache=self.cache
        )
        self.snowball = SnowballOrchestrator(
            self.db, config=SnowballConfig(), cache=self.cache
        )
        self.tavily = TavilyClient(api_keys=tavily_keys)
        self.web_search = WebSearchEngine(
            db=self.db,
            tavily_keys=tavily_keys,
            output_dir=web_search_dir,
        )
        self.scholar = GoogleScholarClient(
            proxy=scholar_proxy, proxy_pool=proxy_pool, cache=self.cache
        )
        self.pdf = PDFConverter()
        self.retriever = RAGRetriever(self.db)
        self.cards = CardManager(self.db)
        self.bib = BibliographyManager(self.db)
        self.workflow = WorkflowManager(self.db)
        self.irac = IRACManager(self.db)
        self.scaffolder = ThesisScaffolder(self.db, self.workflow, self.irac, self.bib)
        self.auditor = TraceabilityAuditor(self.db)
        self.pipeline = ResearchPipeline(app=self)

    async def close(self) -> None:
        """Gracefully close all network clients, background pools, and database connections."""
        closers = [
            ("providers", self.providers.close),
            ("tavily", self.tavily.close),
            ("web_search", self.web_search.close),
            ("scholar", self.scholar.close),
        ]
        for name, closer in closers:
            try:
                res = closer()
                if asyncio.iscoroutine(res):
                    await asyncio.shield(res)
            except (asyncio.CancelledError, KeyboardInterrupt):
                pass
            except Exception as e:  # noqa: BLE001
                logger.debug("Error closing {}: {}", name, e)

        try:
            self.db.close()
        except Exception as e:  # noqa: BLE001
            logger.debug("Error closing database: {}", e)

        try:
            self.cache.close()
        except Exception as e:  # noqa: BLE001
            logger.debug("Error closing cache: {}", e)

    def close_sync(self) -> None:
        """Synchronously close all network clients, background pools, and database connections."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            loop.create_task(self.close())
        else:
            asyncio.run(self.close())

    async def __aenter__(self) -> Self:

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    def load_bib_files(
        self,
        paths: list[str | Path] | list[str] | list[Path] | str | Path,
        *,
        deduplicate: bool = True,
        auto_normalize: bool = False,
    ) -> int:
        """Parse BibTeX files or whole directories and populate database."""
        file_paths = expand_bib_paths(paths)
        entries = parse_bib_files(file_paths, deduplicate=deduplicate)

        indexed = 0
        for e in entries:
            existing = self.db.get(e.cite_key)
            if existing:
                rec = PublicationRecord(
                    cite_key=e.cite_key,
                    entry_type=e.entry_type or existing.entry_type,
                    title=e.title or existing.title,
                    authors=e.authors if e.authors else existing.authors,
                    journal=e.journal or existing.journal,
                    year=e.year or existing.year,
                    volume=e.volume or existing.volume,
                    number=e.number or existing.number,
                    pages=e.pages or existing.pages,
                    doi=e.doi or existing.doi,
                    url=e.url or existing.url,
                    abstract=e.abstract or existing.abstract,
                    sources=list(dict.fromkeys(existing.sources + e.sources)),
                    raw_fields=e.raw_fields or existing.raw_fields,
                    download_status=existing.download_status,
                    download_path=existing.download_path,
                    markdown_path=existing.markdown_path,
                    is_chunked=existing.is_chunked,
                )
            else:
                rec = PublicationRecord(
                    cite_key=e.cite_key,
                    entry_type=e.entry_type,
                    title=e.title,
                    authors=e.authors,
                    journal=e.journal,
                    year=e.year,
                    volume=e.volume,
                    number=e.number,
                    pages=e.pages,
                    doi=e.doi,
                    url=e.url,
                    abstract=e.abstract,
                    sources=e.sources,
                    raw_fields=e.raw_fields,
                )
            if auto_normalize:
                rec = normalize_record(rec, cache=self.cache)
            self.db.create(rec)
            indexed += 1

        logger.info(
            f"Loaded and indexed {indexed} entries from {[p.name for p in file_paths]}"
        )
        return indexed

    async def search_academic(
        self,
        query: str,
        *,
        providers: list[str] | None = None,
        limit_per_provider: int = 5,
        auto_index: bool = True,
    ) -> list[PublicationRecord]:
        """Search across arXiv, OpenAlex, Crossref, DOAJ, and OpenAIRE."""
        return await self.providers.search_all(
            query,
            providers=providers,
            limit_per_provider=limit_per_provider,
            auto_index=auto_index,
        )

    async def search_scholar(
        self,
        query: str,
        *,
        limit: int = 10,
        page: int = 1,
        auto_index: bool = True,
    ) -> list[PublicationRecord]:
        """Search Google Scholar and optionally auto-index into SQLite database."""
        res = await self.scholar.search(query, limit=limit, page=page)
        raw_records = [pub.to_publication_record() for pub in res.publications]
        if not auto_index:
            return raw_records

        final_records: list[PublicationRecord] = []
        for rec in raw_records:
            existing = self.db.find_existing(rec)
            if existing:
                updated_sources = list(dict.fromkeys(existing.sources + rec.sources))
                self.db.update(existing.cite_key, sources=updated_sources)
                existing.sources = updated_sources
                final_records.append(existing)
            else:
                self.db.create(rec)
                final_records.append(rec)
        return final_records

    async def run_snowball(
        self,
        seed_cite_key: str,
        *,
        direction: str = "both",
        limit_forward: int = 15,
        limit_backward: int = 15,
        relevance_query: str = "",
        relevance_top_k: int = 10,
        relevance_min_score: float = 0.0,
    ) -> SnowballResult:
        """Traverse citation network for a seed paper in the database."""
        rec = self.db.get(seed_cite_key)
        if not rec:
            msg = f"Seed paper '{seed_cite_key}' not found in database."
            raise ValueError(msg)

        self.snowball.config.direction = direction  # type: ignore[assignment]
        self.snowball.config.limit_forward = limit_forward
        self.snowball.config.limit_backward = limit_backward
        self.snowball.config.relevance_query = relevance_query
        self.snowball.config.relevance_top_k = relevance_top_k
        self.snowball.config.relevance_min_score = relevance_min_score
        return await self.snowball.snowball_record(rec)

    async def download_papers(
        self,
        cite_keys: list[str] | None = None,
        *,
        skip_already_downloaded: bool = True,
        force: bool = False,
    ) -> dict[str, int]:
        """Download papers in parallel with content and magic byte verification."""
        return await self.downloader.download_all(
            cite_keys=cite_keys,
            skip_already_downloaded=skip_already_downloaded,
            force=force,
        )

    def convert_pdf(
        self,
        source: str | Path | bytes,
        *,
        output_md: str | Path | None = None,
        options: ConversionOptions | None = None,
    ) -> ConvertedDocument:
        """Convert a PDF document into normalized Markdown with layout cleaning."""
        if output_md and isinstance(source, (str, Path)):
            self.pdf.convert_file(source, output_md, options=options)
        return self.pdf.convert(source, options=options)

    async def run_pipeline(
        self,
        query: str = "",
        *,
        bib_path: str | Path | list[str | Path] | None = None,
        search_limit: int = 15,
        include_scholar: bool = True,
        snowball: bool = True,
        download: bool = True,
        download_concurrency: int = 6,
        convert: bool = True,
        convert_concurrency: int = 4,
        snowball_concurrency: int = 4,
        index_rag: bool = True,
        streaming: bool = True,
        **kwargs: Any,
    ) -> PipelineResult:
        """Execute the end-to-end research lifecycle for a query and/or seed .bib file."""
        config = PipelineConfig(
            query=query,
            bib_path=bib_path,
            search_limit=search_limit,
            include_scholar=include_scholar,
            snowball=snowball,
            download=download,
            download_concurrency=download_concurrency,
            convert=convert,
            convert_concurrency=convert_concurrency,
            snowball_concurrency=snowball_concurrency,
            index_rag=index_rag,
            streaming=streaming,
            **kwargs,
        )
        return await self.pipeline.run(config)

    async def query_rag(
        self,
        query: str,
        *,
        limit: int = 5,
        cite_key: str | None = None,
        mode: str = "hybrid",
        corpus: str | None = None,
        **kwargs: Any,
    ) -> list[RetrievalResult]:
        """Search full-text indexed document chunks via hybrid (BM25 + Dense RRF), BM25, or Dense."""
        return self.retriever.search(
            query,
            limit=limit,
            cite_key=cite_key,
            mode=mode,
            corpus=corpus,
            **kwargs,
        )

    def embed_chunks(self, *, batch_size: int = 64) -> int:
        """Compute and persist dense vector embeddings for all unembedded chunks."""
        return self.retriever.embed_all_chunks(batch_size=batch_size)

    async def search_web(
        self,
        query: str,
        *,
        provider: WebSearchProvider = "all",
        topic: str = "general",
        limit: int = 5,
        auto_index: bool = True,
    ) -> WebSearchResponse:
        """Search web via Tavily and/or DuckDuckGo (ddgs), extract to clean Markdown, and auto-index into SQLite RAG."""
        return await self.web_search.search(
            query,
            provider=provider,
            topic=topic,  # type: ignore[arg-type]
            limit=limit,
            auto_index=auto_index,
        )

    def get_stats(self) -> dict[str, Any]:
        """Return combined statistics from database, download directory, and HTTP cache."""
        db_stats = self.db.get_stats()
        cache_stats = self.cache.stats()
        db_stats["cache"] = cache_stats
        return db_stats
