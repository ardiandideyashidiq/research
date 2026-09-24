from __future__ import annotations

from pathlib import Path
from types import TracebackType
from typing import Any, Self

from loguru import logger

from research.bibtex.parser import parse_bib_files
from research.db.manager import DatabaseManager
from research.db.models import PublicationRecord
from research.downloader.downloader import DownloadManager
from research.google_scholar.client import GoogleScholarClient
from research.normalizer.normalizer import normalize_record
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


class ResearchApp:
    """Unified application facade orchestrating storage, literature providers, OJS, snowballing, downloading, and web search."""

    def __init__(
        self,
        *,
        db_path: str | Path = "tmp/publications.sqlite",
        download_dir: str | Path = "data/downloads",
        tavily_keys: list[str] | None = None,
        scholar_proxy: str | Proxy | None = None,
        proxy_pool: ProxyPool | None = None,
    ) -> None:
        self.db = DatabaseManager(db_path)
        self.providers = ProviderRegistry(db=self.db)
        self.downloader = DownloadManager(self.db, download_dir=download_dir)
        self.snowball = SnowballOrchestrator(self.db, config=SnowballConfig())
        self.tavily = TavilyClient(api_keys=tavily_keys)
        self.scholar = GoogleScholarClient(proxy=scholar_proxy, proxy_pool=proxy_pool)
        self.pdf = PDFConverter()
        self.retriever = RAGRetriever(self.db)
        self.pipeline = ResearchPipeline(app=self)

    async def close(self) -> None:
        await self.providers.close()
        await self.tavily.close()
        await self.scholar.close()
        self.db.close()

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
        """Parse BibTeX files and populate database."""
        path_list = [Path(paths)] if isinstance(paths, (str, Path)) else [Path(p) for p in paths]
        entries = parse_bib_files(path_list, deduplicate=deduplicate)

        indexed = 0
        for e in entries:
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
                rec = normalize_record(rec)
            self.db.create(rec)
            indexed += 1

        logger.info(f"Loaded and indexed {indexed} entries from {[p.name for p in path_list]}")
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
        records = [pub.to_publication_record() for pub in res.publications]
        if auto_index:
            for rec in records:
                self.db.create(rec)
        return records

    async def run_snowball(
        self,
        seed_cite_key: str,
        *,
        direction: str = "both",
        limit_forward: int = 15,
        limit_backward: int = 15,
    ) -> SnowballResult:
        """Traverse citation network for a seed paper in the database."""
        rec = self.db.get(seed_cite_key)
        if not rec:
            msg = f"Seed paper '{seed_cite_key}' not found in database."
            raise ValueError(msg)

        self.snowball.config.direction = direction  # type: ignore[assignment]
        self.snowball.config.limit_forward = limit_forward
        self.snowball.config.limit_backward = limit_backward
        return await self.snowball.snowball_record(rec)

    async def download_papers(
        self,
        cite_keys: list[str] | None = None,
        *,
        skip_already_downloaded: bool = True,
    ) -> dict[str, int]:
        """Download papers in parallel with content and magic byte verification."""
        return await self.downloader.download_all(
            cite_keys=cite_keys,
            skip_already_downloaded=skip_already_downloaded,
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
        query: str,
        *,
        search_limit: int = 15,
        include_scholar: bool = True,
        snowball: bool = True,
        download: bool = True,
        convert: bool = True,
        index_rag: bool = True,
        **kwargs: Any,
    ) -> PipelineResult:
        """Execute the end-to-end research lifecycle for a query."""
        config = PipelineConfig(
            query=query,
            search_limit=search_limit,
            include_scholar=include_scholar,
            snowball=snowball,
            download=download,
            convert=convert,
            index_rag=index_rag,
            **kwargs,
        )
        return await self.pipeline.run(config)

    async def query_rag(
        self,
        query: str,
        *,
        limit: int = 5,
        cite_key: str | None = None,
    ) -> list[RetrievalResult]:
        """Search full-text indexed document chunks via FTS5 BM25."""
        return self.retriever.search(query, limit=limit, cite_key=cite_key)
