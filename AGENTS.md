# AGENTS.md

## Project Overview

`research` is a modular Python package for automated academic research, publication discovery, citation graph snowballing, and open-access paper downloading.

Key capabilities:
- **Federated Academic Search**: Multi-provider parallel querying across **arXiv**, **OpenAlex**, **Crossref**, **DOAJ**, and **OpenAIRE**.
- **BibTeX Processing**: High-performance parsing, deduplication, and export to JSON and SQLite with **FTS5 full-text search**.
- **Open Journal Systems (OJS)**: Automated discovery of Highwire Press and Dublin Core metadata with galley-to-download link resolution.
- **Open Access Retrieval**: Direct open-access PDF resolution via **Unpaywall** and OpenAlex metadata.
- **Citation Graph Snowballing**: Automated forward (citing) and backward (referenced) graph traversal starting from `.bib` seed files or database records.
- **Idempotent Parallel Downloader**: Queued concurrent downloading with content inspection (`%PDF` magic byte verification) and granular error auditing (preventing false positives for dead links).
- **Web Search Integration & Auto-Indexing**: Multi-API-key load balancing and automatic failover for **Tavily Search** and **DuckDuckGo (ddgs)** with automatic sanitization into clean Markdown documents (YAML frontmatter) and instant semantic chunking into SQLite FTS5 RAG.
- **Anti-Bot Scraping Engine**: `curl-cffi` browser TLS impersonation (`impersonate="chrome"`) for Google Scholar, arXiv, and Cloudflare-protected academic repositories.
- **PDF to Markdown & Layout Normalization**: High-performance conversion with **PyMuPDF** & **PyMuPDF4LLM**, dehyphenation, heading normalization, running header/footer removal, prose reflow, and YAML frontmatter metadata.
- **Semantic Chunking & SQLite FTS5 BM25 RAG**: Heading- and page-aware chunking preserving academic citation context, with zero-dependency SQLite BM25 ranking and LLM prompt context formatting.
- **Dense Multilingual Vector Embeddings & RRF**: Local ONNX-powered embeddings with `fastembed` (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) stored as compact float32 binary blobs in SQLite, fused with BM25 using Reciprocal Rank Fusion ($k=60$).
- **Cross-Corpus Unified Retrieval**: Simultaneous semantic search across academic papers (`literature`), court decisions (`putusan`), and web findings (`web`) with explicit corpus tags and legal context headers.
- **End-to-End Autonomous Pipeline**: One-command complete lifecycle orchestration (`search -> snowball -> download -> convert -> RAG chunking`).
- **Indonesian Court Judgment Engine (Putusan)**: Context-preserving conversion and chunking for court decisions across all jurisdictions (MA, MK, MKMK, PN, PT, PA, PM, PTUN, DKPP, KIP) with legal typography unspacing, watermark/disclaimer stripping, section segmentation (`KEPALA`, `IDENTITAS`, `DUDUK_PERKARA`, `PERTIMBANGAN_HUKUM`, `AMAR_PUTUSAN`, `PENUTUP`), context header injection, and direct SQLite RAG indexing.
- **Production CLI Suite**: Ergonomic subcommands (`pipeline`, `search`, `snowball`, `download`, `convert`, `query`, `export`, `stats`, `putusan`, `web-search`, `embed`).

## Commands

Environment is managed strictly by [uv](https://docs.astral.sh/uv/); never use pip or create a venv manually.

```bash
uv sync                 # install deps including dev group
uv run research --help  # view all CLI subcommands
uv run research stats   # show database publications, downloads, RAG chunks, embeddings
uv run research pipeline "artificial intelligence copyright" --limit 10
uv run research search "quantum computing" --providers arxiv,openalex --limit 5
uv run research web-search "pertanggungjawaban pidana kecerdasan buatan" --provider all --limit 5
uv run research snowball <cite_key> --direction both --limit 10
uv run research download --concurrency 4
uv run research convert data/downloads/paper.pdf --index-rag
uv run research embed --batch-size 64 # generate vector embeddings for all pending chunks
uv run research query "criminal liability deepfake" --mode hybrid --corpus all --format-context
uv run research query "pertimbangan hukum" --mode hybrid --corpus putusan --limit 3
uv run research putusan /path/to/putusan.pdf --output-dir data/putusan_processed --index-rag
uv run research putusan /path/to/putusan_dir/ --sample 50 --concurrency 6 --index-rag
uv run research export --format bibtex --output tmp/export.bib
uv run ruff check .     # lint
uv run ruff check --fix .
uv build                # build distributions with uv_build backend
```

## Code Organization

```
src/research/
├── __init__.py           # Lazy app loader (get_app) & CLI entry point (research:main)
├── app.py                # ResearchApp unified application facade
├── cli/                  # Production CLI subcommands and runner
│   ├── parser.py         # Argument parser specification with 8 subcommands
│   └── main.py           # Async CLI execution handlers
├── bibtex/               # BibTeX parser, normalizer, and SQLite/JSON exporter
│   ├── models.py         # BibEntry dataclass with .to_publication() mapping
│   ├── parser.py         # parse_bib_file, parse_bib_files, parse_bib_str
│   └── export.py         # export_to_json, export_to_sqlite, export_to_bibtex_str
├── db/                   # SQLite storage & full CRUD
│   ├── models.py         # PublicationRecord dataclass
│   └── manager.py        # DatabaseManager (CRUD, auto-migrations, FTS5 sync, chunks table)
├── providers/            # Federated academic literature search engines
│   ├── base.py           # BaseProvider abstract base class
│   ├── arxiv.py          # arXiv client (curl-cffi Chrome impersonation)
│   ├── openaire.py       # OpenAIRE Graph client
│   ├── doaj.py           # Directory of Open Access Journals client
│   ├── crossref.py       # Crossref REST API client
│   ├── openalex.py       # OpenAlex catalog client
│   └── registry.py       # ProviderRegistry (parallel federated search & deduplication)
├── normalizer/           # Metadata normalizer & multi-source enricher
│   ├── normalizer.py     # normalize_record, normalize_records_async
│   └── crossref.py       # Crossref DOI resolver
├── unpaywall/            # Unpaywall open-access PDF resolver
│   ├── models.py         # UnpaywallRecord, UnpaywallLocation
│   └── client.py         # UnpaywallClient (hardcoded rdndds@gmail.com)
├── ojs/                  # Open Journal Systems (PKP OJS) scraper
│   ├── models.py         # OJSMetadata dataclass
│   ├── extractor.py      # Highwire & Dublin Core HTML meta tag parser
│   └── client.py         # OJSClient (dual-engine: curl-cffi & httpx)
├── snowball/             # Citation graph traversal (forward citing & backward references)
│   ├── models.py         # SnowballConfig, SnowballResult
│   ├── openalex.py       # OpenAlexClient (abstract reconstruction, cite key generator)
│   └── orchestrator.py   # SnowballOrchestrator (.bib orchestration & auto-indexing)
├── downloader/           # Parallel paper downloader
│   ├── verifier.py       # inspect_content (%PDF magic bytes), classify_error
│   └── downloader.py     # DownloadManager (queue/semaphore concurrency, DB auto-indexing)
├── tavily/               # Multi-key load-balanced web search engine
│   ├── models.py         # TavilySearchResponse, APIKeyStatus
│   └── pool.py           # APIKeyPool (round-robin / least-used, auto-failover)
├── ddgs/                 # DuckDuckGo search client (text and news async scraper)
│   ├── models.py         # DDGSSearchResult, DDGSSearchResponse
│   └── client.py         # DDGSClient (text and news async execution)
├── web_search/           # Unified Tavily & DDGS search with Markdown extraction & auto-indexing
│   ├── models.py         # WebSearchResult, WebSearchResponse
│   ├── normalizer.py     # HTML/web content cleaner, YAML frontmatter Markdown formatter
│   ├── indexer.py        # WebSearchIndexer (Markdown disk export, SQLite CRUD, RAG FTS5 sync)
│   └── client.py         # WebSearchEngine (dual-engine orchestrator with auto-failover)
├── google_scholar/       # Google Scholar client (TLS impersonation, metadata & citations extraction)
│   ├── models.py         # Publication, SearchResult (.to_publication_record())
│   └── client.py         # GoogleScholarClient (search, publication landing resolver)
├── proxy/                # Rotating proxy pool & V2Ray VLESS bridge
│   ├── models.py         # Proxy dataclass (.from_url() parser for http, socks5, vless)
│   └── pool.py           # ProxyPool (round-robin rotation, V2Ray socks5 bridge, validation)
├── pdf/                  # PDF to Markdown converter & layout normalizer
│   ├── models.py         # PDFMetadata, PageChunk, ConvertedDocument, ConversionOptions
│   ├── normalizer.py     # Dehyphenation, heading cleanup, reflow, header/footer removal
│   └── converter.py      # PDFConverter (PyMuPDF & PyMuPDF4LLM extraction, async batching)
├── rag/                  # Semantic chunking & local FTS5 BM25 retrieval
│   ├── models.py         # DocumentChunk, RetrievalResult
│   ├── chunker.py        # SemanticChunker (heading/page boundary-aware chunking)
│   ├── embeddings.py     # EmbeddingEngine (fast ONNX multilingual dense embeddings)
│   └── retriever.py      # RAGRetriever (Hybrid BM25 + Dense RRF ranking, context builder)
├── pipeline/             # Autonomous end-to-end research orchestration
│   ├── models.py         # PipelineConfig, PipelineResult
│   └── orchestrator.py   # ResearchPipeline (search -> snowball -> download -> convert -> RAG)
└── putusan/              # Indonesian Court Judgment conversion & context-preserving chunking
    ├── models.py         # PutusanMetadata, PutusanSection, PutusanChunk, PutusanDocument
    ├── normalizer.py     # Watermark/disclaimer stripping, spaced typography unspacing, table reflow
    ├── extractor.py      # Regex & heuristic metadata extraction (case number, court, parties, dates)
    ├── segmenter.py      # Legal milestones segmenter (Kepala, Identitas, Duduk Perkara, Pertimbangan, Amar, Penutup)
    ├── chunker.py        # Context-preserving semantic chunker with injected legal context banners
    └── converter.py      # PutusanConverter (batch processing, Tesseract OCR fallback, JSON/MD export)
```

Import packages using absolute `src/` layout: `from research.db import DatabaseManager`, never relative imports.

## Conventions

- **Python 3.13+**: PEP 604 unions (`str | None`, `list[str]`), `X | None` return types — no `Optional`/`List` from typing. Use `from typing import Self` and `from types import TracebackType` for context managers.
- **Dataclasses** for all domain models; mutable fields use `field(default_factory=list)` or `field(default_factory=dict)`.
- **Keyword-only args** after `*` in public APIs (e.g. `search(query, *, limit=10)`).
- **Async-first**: Networking methods are `async def` with convenient synchronous wrappers (`_sync`) for scripts and CLI.
- **Logging**: Use `loguru.logger` — do not use stdlib `logging`.
- **Hardcoded Email**: Academic API polite pools (Crossref, OpenAlex, Unpaywall, OpenAIRE) use `rdndds@gmail.com`.
- **Ruff defaults**: Keep code 100% ruff-compliant without line-length overrides.

## Gotchas

- **Dual HTTP Architecture**:
  - `curl-cffi` (with `impersonate="chrome"`) is mandatory for Google Scholar, arXiv, and bot/Cloudflare-protected journal sites. Python's standard `ssl` stack in `httpx`/`requests` gets blocked by these platforms.
  - `httpx` is used for standard REST APIs (Crossref, OpenAlex, Unpaywall, DOAJ, OpenAIRE, Tavily).
- **Zero False-Positive Error Auditing**:
  - Never classify a paper as a `dead_link` on transient timeouts or server-side 5xx errors.
  - Verify `%PDF` magic bytes upon HTTP 200 to prevent marking soft paywalls or HTML login portals as successfully downloaded papers.
- **Idempotent Operations**:
  - `DownloadManager` skips papers already marked `downloaded` with verified files on disk to prevent hitting publishers twice.
  - `SnowballOrchestrator` deduplicates discovered works by canonical DOI before inserting into SQLite.
- `main()` in `__init__.py` is the lightweight console script entry point — keep imports light there using lazy loading (`get_app()`).
- `sessions/` holds auto-generated agent session logs — do not edit or commit meaningful code into it.