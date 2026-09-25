# AGENTS.md

## Project Overview

`research` is an autonomous, modular Python 3.13+ platform for academic literature discovery, Indonesian court judgment analysis, citation graph snowballing, open-access paper downloading, and cross-corpus Retrieval-Augmented Generation (RAG).

### Core Capabilities
- **Federated Academic Search**: Parallel querying across **arXiv**, **OpenAlex**, **Crossref**, **DOAJ**, and **OpenAIRE** with automatic canonical DOI deduplication.
- **BibTeX Processing & Ingestion**: High-performance parsing of single `.bib` files or entire recursive directory trees, with normalization and export to JSON, SQLite, and BibTeX.
- **Open Journal Systems (OJS) Discovery**: Automated discovery of Highwire Press and Dublin Core HTML metadata with multi-galley download link resolution.
- **Open Access Retrieval (`fulltext`)**: Unpaywall API integration, OpenAlex metadata inspection, direct `--pdf-url` support, and OJS/Highwire galley extraction in one CLI command (`research fulltext`) turning a DOI/URL into full-text Markdown.
- **Citation Graph Snowballing**: Automated forward (citing) and backward (referenced) graph traversal starting from database records or seed `.bib` collections.
- **Idempotent Parallel Downloader**: Queued concurrent downloading with content inspection (`%PDF` magic byte verification) and granular error auditing (preventing false-positive dead link tags on soft paywalls or transient timeouts).
- **Web Search Integration & Auto-Indexing**: Load-balanced multi-key **Tavily** and zero-config **DuckDuckGo (ddgs)** search engines, automatic sanitization into clean Markdown documents with YAML frontmatter, and instant semantic chunking into SQLite FTS5 RAG.
- **Anti-Bot Scraping Engine**: `curl-cffi` browser TLS impersonation (`impersonate="chrome"`) for Google Scholar, arXiv, and Cloudflare-protected academic repositories.
- **PDF to Markdown & Layout Normalization**: Multi-threaded extraction via **PyMuPDF** & **PyMuPDF4LLM**, prose reflow, dehyphenation, heading normalization, and running header/footer stripping.
- **Indonesian Court Judgment Engine (`putusan`)**: Context-preserving conversion and chunking for court decisions across all jurisdictions (MA, MK, MKMK, PN, PT, PA, PM, PTUN, DKPP, KIP) with legal typography unspacing, watermark/disclaimer stripping, section segmentation (`KEPALA`, `IDENTITAS`, `DUDUK_PERKARA`, `PERTIMBANGAN_HUKUM`, `AMAR_PUTUSAN`, `PENUTUP`), and injected legal context banners.
- **Cross-Corpus Unified Retrieval & Hybrid RRF**: Simultaneous semantic search across academic literature (`literature`), court decisions (`putusan`), and web findings (`web`) fusing SQLite FTS5 BM25 and ONNX dense multilingual embeddings (`paraphrase-multilingual-MiniLM-L12-v2`) via Reciprocal Rank Fusion ($k=60$).
- **Literature Review Card System & Matrix Synthesis**: Heuristic & milestone-aware extraction across papers and court rulings into structured research cards (*Isu Hukum*, *Teori/Dasar Hukum*, *Metodologi*, *Temuan Utama/Amar*, *Research Gap*, *Positioning*), researcher tagging/annotations, and multi-format matrix export (GFM table + detailed cards in Markdown, UTF-8 BOM CSV for Excel, and JSON).
- **Full CRUD Bibliography Manager & Multi-CSL Engine**: Comprehensive reference CRUD (create, import from BibTeX/CSL-JSON/RIS/DOI, update, delete, FTS search), with instant citation generation across 12 CSL & data formats (APA 7th, IEEE, Harvard, Chicago Author-Date & Note, MLA 9th, Vancouver, OSCOLA, Indonesian Legal, BibTeX, RIS, CSL-JSON) for in-text and bibliography lists.
- **Normative Legal Research Toolkit (`workflow`, `irac`, `scaffold`, `audit-traceability`)**: End-to-end operationalization of the 20-stage normative legal research methodology (`workflow.md`) with 7-phase gate-check tracking, formal deductive syllogism (IRAC) building with criminal law analogy guards, automated 5-chapter thesis scaffolding, and citation traceability auditing.
- **Doctrinal Knowledge Base (`knowledge/`)**: Modular, traceable doctrine library for normative analysis — `analisis-status-hukum/kerangka-teori.md` (three-tier legal science + 5 theory groups), `framework-operasional.md` (6-stage analysis + worksheet template), `dekonstruksi-unsur-pasal.md` (4-stage article/ayat dissection: bestanddelen vs elementen, actus reus vs mens rea, monisme-dualisme, antar-ayat), `dekonstruksi-isu-hukum.md` (6-stage legal-issue decomposition: faktual skematisasi, kualifikasi, anatomi norma + 3 sub-isu pidana, tipologi cacat norma, 3-lapis ilmu hukum, IRAC per sub-isu), and `review-kualitas/` (review-epistemologis.md + review-framework-7dimensi.md: 5-criteria evaluation, 7-dimension framework + 35-point audit scorecard, reviewer form). Subagents MUST ground doctrinal reasoning, issue-decomposition, and quality-review in this library (index: `knowledge/README.md`).
- **End-to-End Autonomous Pipeline**: One-command streaming or staged pipeline orchestrating discovery, snowballing, downloading, conversion, and RAG indexing.

---

## Development Guide

### Environment & Tooling
The environment is strictly managed by [uv](https://docs.astral.sh/uv/). Never use raw `pip` or create virtual environments manually.

```bash
uv sync                 # Install all runtime and development dependencies
uv run ruff check .     # Lint entire codebase according to project rules
uv run ruff format .    # Auto-format codebase
uv build                # Build source distributions with uv_build backend
```

### Running Tests
The test suite consists of standalone integration and concurrency verification scripts located in `tests/`:

```bash
# Run all test scripts sequentially
for f in tests/test_*.py; do echo "=== Running $f ==="; uv run python "$f"; done

# Run specific subsystem tests
uv run python tests/test_parallel_pipeline.py   # Multi-worker pipeline & batch conversion
uv run python tests/test_interruption.py        # SIGINT/Ctrl+C graceful task cancellation
uv run python tests/test_db_concurrency.py      # SQLite WAL concurrency and lock safety
uv run python tests/test_db_lookups.py          # Hash, DOI, and URL indexing lookups
uv run python tests/test_download_dedup.py      # Magic byte and content deduplication
uv run python tests/test_http_cache.py          # SQLite HTTP cache TTL & negative caching
uv run python tests/test_bib_directory.py       # Recursive BibTeX directory ingestion
uv run python tests/test_timeouts.py            # Fast-fail timeouts on unresponsive hosts
```

### Architecture & Design Patterns
1. **Async-First Core with Sync Wrappers**:
   - All network I/O, scraping, and pipeline orchestrations are natively `async` (`asyncio`).
   - High-level classes expose synchronous companion methods with a `_sync` suffix for ergonomic scripting.
2. **Asyncio Task Cancellation & Shielding**:
   - `ResearchApp.close()` and database write transactions wrap critical teardown logic in `asyncio.shield()` to ensure DB connections and running workers terminate cleanly upon `KeyboardInterrupt` or cancellation.
3. **Database & Unified Storage**:
   - Primary storage is SQLite with WAL mode enabled (`PRAGMA journal_mode=WAL`).
   - Schema auto-migrates via `DatabaseManager.init_schema()`.
   - `publications`: Core metadata table with FTS5 virtual table `publications_fts`.
   - `chunks`: Stores semantic text chunks across all corpora (`literature`, `putusan`, `web`) with FTS5 virtual table `chunks_fts` and `embedding` (384-dim IEEE 754 float32 BLOB).
   - `review_cards`: Literature review synthesis cards with full-text search `review_cards_fts`.
   - `http_cache`: Persistent response caching with dynamic TTL and negative-result caching.
4. **Dual HTTP Network Engine**:
   - `curl-cffi` (`impersonate="chrome"`): Mandatory for scraping Google Scholar, arXiv, and bot-protected academic publisher websites.
   - `httpx`: High-throughput async client for standard REST endpoints (Crossref, OpenAlex, Unpaywall, DOAJ, OpenAIRE, Tavily).
5. **Zero False-Positive Download Auditing**:
   - An HTTP 200 response alone does not mean a download succeeded; servers often return HTML login portals or captcha challenges.
   - `inspect_content()` reads the first 1024 bytes and validates `%PDF-` magic bytes. If HTML or paywall headers are found, the status is categorized as `failed_not_pdf` rather than `dead_link`.
6. **Full-Text First (Literature Review)**:
   - When analyzing a paper with a DOI, subagents MUST obtain the full text via
     `uv run research fulltext "<DOI>"` (add `--index-rag` when RAG indexing is wanted)
     instead of settling for abstracts.
7. **Every Research Stage Uses a Subagent**:
   - Each of the 20 stages of the normative workflow (see `workflow.md` and the
     `riset/tahapN.md` trail) MUST be executed with a dedicated subagent (`Agent`,
     `general-purpose`) rather than the main agent doing the analysis inline.
   - The main agent prepares the doctrinally grounded materials (pasal [TERBACA]
     from the corpus, verified papers, `knowledge/`), writes a self-contained brief,
     spawns the subagent, and reviews/incorporates the returned stage file.
   - Subagents write the stage output to `riset/tahapN.md` (or the relevant file),
     follow the stage's gate check in `workflow.md`, and adhere to zero-hallucination
     rules ([FULL-TEXT]/[ABSTRACT]/[METADATA] labels; no invented pasal/paper).
   - This keeps analysis parallelizable, reviewable, and traceable.
8. **Manual `curl`/`httpx`/`wget` PDF retrieval is STRICTLY FORBIDDEN** for literature
     analysis. Every download goes through the CLI:
       - `uv run research fulltext "<DOI>"` → Unpaywall/OJS auto-resolve
       - `uv run research fulltext "<DOI>" --pdf-url "<direct PDF or OJS download URL>"`
         → when the PDF URL is already known (galley, repository link, OpenAlex OA URL)
       - `uv run research fulltext "<article landing URL>"` → OJS extractor finds the
         galley automatically
   - The dual-engine downloader (curl-cffi Chrome impersonation + OJS fallback)
     already handles anti-bot (Cloudflare/OJS) protection — never reimplement it.
   - An abstract-only analysis is a **degraded fallback** that must be flagged with the
     `[ABSTRACT]` / `[METADATA]` epistemic labels, never the target outcome. Only mark a
     paper `[FULL-TEXT]` after reading the Markdown produced by `fulltext` (or a
     previously converted local `.md`), never from a PDF you grabbed ad hoc.
9. **Pasal.id MCP for Statutory Verification**:
   - Any Indonesian regulation, pasal, or citation used in analysis MUST be verified
     against the Pasal.id MCP corpus (`resolve_law` → `get_law_context` → `read_law`)
     when available. Label verified text `[TERBACA]`; otherwise `[REFERENSI]` /
     `[PERLU VERIFIKASI]`.
   - Subagents verifying statutes MUST check `get_law_context(detail='relationships')`
     for amendments (e.g. UU 1/2026) and `court_reviews` (putusan MK uji materi) —
     a pasal may be modified or held inkonstitusional (e.g. MK 105/2024 limiting
     ITE 27A "orang lain"; MK 115/2024 "kerusuhan" = physical).
   - Never rely on a paper's quoted pasal number; confirm against the corpus before
     citing substantively (papers routinely quote outdated versions, e.g. UU ITE
     19/2016 or wrong PDP sanctions).
10. **Auto-Enrich Doctrine into `knowledge/`**:
    - Whenever a paper, web result, or doctrinal point (teori, tokoh, asas,
      definisi) is encountered that is NOT yet reflected in `knowledge/`
      (`analisis-status-hukum/*`, README index), subagents SHOULD capture it:
      run a quick web search (`uv run research web-search "--no-index"`) for
      the doctrine AND/OR read it from the paper's full text, then write a
      short knowledge file (or append to the existing one) with: doctrine
      name, tokoh/penggagas, sumber (DOI/URL/paper cite_key + label
      [FULL-TEXT]/[ABSTRACT]/[WEB]), fungsi bagi analisis status hukum.
    - Index new files in `knowledge/README.md`; keep naming modular &
      traceable. Do NOT duplicate an existing entry — update it instead.
    - This keeps the doctrinal grounding current and lets future stages &
      subagents inherit it (self-improving rule #10).
11. **Self-Improving Workflow & Tools**:
    - Whenever a task reveals a repeated manual step, a tool limit that forces a
      subagent to fall back to `curl`/ad-hoc scripts, or a workflow gap, the agent
      SHOULD fix it on the spot and commit: enhance the research CLI (new flag/
      subcommand), update `workflow.md`, `AGENTS.md`, `knowledge/`, or the
      subagent briefs.
    - Before enhancing a tool, read its current implementation and docs; keep changes
      minimal, lint-clean (`uv run ruff check .`), and backward-compatible.
    - Register any new CLI surface in `AGENTS.md` (Detailed CLI section) and, if it
      changes methodology, in `workflow.md` (Alat Operasional / gate checks).
    - If a subagent reports an anti-pattern (manual retrieval, unverified pasal,
      invented content), treat it as a tooling/instruction gap to close, not just an
      agent failure, and improve the instructions/tools to prevent recurrence.
    - Keep the `riset/` trail and `knowledge/` library consistent with tool changes so
      future sessions & subagents inherit the improvements.

---

## Detailed CLI & API Usage Guide

Every CLI command supports global flags:
- `--db DB_PATH`: Specify SQLite database file (default: `tmp/publications.sqlite`).
- `--downloads DIR`: Specify PDF download directory (default: `data/downloads`).
- `--log-dir DIR`: Directory for log files (default: `logs`).
- `--no-log-file`: Disable writing log files to disk.
- `-v`, `--verbose`: Enable debug logging.
- `--no-cache`: Bypass persistent HTTP cache.
- `--clear-cache`: Purge HTTP cache before execution.

---

### 1. Database & Cache Inspection (`stats`)

View database counts, download statistics, RAG semantic chunk breakdown by corpus, dense vector embedding progress, and HTTP cache utilization.

#### CLI Usage
```bash
# View default database stats
uv run research stats

# View stats for a custom database and clear expired cache entries
uv run research --db tmp/my_project.sqlite --clear-cache stats
```

#### Python API
```python
from research.app import ResearchApp

app = ResearchApp(db_path="tmp/publications.sqlite")
stats = app.get_stats()
print(f"Total Publications: {stats['total_publications']}")
print(f"Downloaded PDFs:    {stats['downloaded_pdfs']}")
print(f"RAG Chunks:         {stats['total_chunks']}")
print(f"Corpus Breakdown:   {stats.get('corpus_breakdown')}")
print(f"HTTP Cache Active:  {stats['cache']['active_entries']}")
app.close_sync()
```

---

### 2. Bibliography Manager (`bib`)

Comprehensive reference manager supporting full CRUD, BibTeX / CSL-JSON / RIS / DOI import, and multi-CSL formatting across 12 citation styles:
`apa`, `ieee`, `harvard`, `chicago`, `chicago-note`, `mla`, `vancouver`, `oscola`, `indonesia`, `bibtex`, `ris`, `csl-json`.

#### CLI Usage
```bash
# Add a new publication manually
uv run research bib add \
  --title "Pertanggungjawaban Pidana Kecerdasan Buatan di Indonesia" \
  --author "Budi Santoso, Siti Rahayu" \
  --year 2025 \
  --journal "Jurnal Hukum Bisnis" \
  --volume 12 --issue 3 --pages "45-60" \
  --doi "10.1234/jhb.2025.12.3" \
  --abstract "Penelitian ini mengkaji doktrin pertanggungjawaban pidana terhadap AI."

# List publications formatted in IEEE style
uv run research bib list --style ieee --limit 20

# Show a publication rendered in ALL 10+ CSL styles and raw BibTeX
uv run research bib show Budisantoso2025pertanggungjawabanpidana --style all

# Update metadata of an existing entry
uv run research bib update Budisantoso2025pertanggungjawabanpidana --pages "45-65" --volume 13

# Import references from a BibTeX file, CSL-JSON, RIS, or DOI
uv run research bib import tmp/seed.bib
uv run research bib import "10.48550/arXiv.1706.03762" --format doi

# Export bibliography to Markdown, BibTeX, or RIS
uv run research bib export --output data/daftar_pustaka.md --style apa --format markdown
uv run research bib export --output data/export.ris --format ris --corpus literature

# Delete an entry and its associated full-text index
uv run research bib delete Budisantoso2025pertanggungjawabanpidana --yes
```

#### Python API
```python
from research.app import ResearchApp
from research.db.models import PublicationRecord

app = ResearchApp()

# 1. Add record
rec = PublicationRecord(
    cite_key="Santoso2025AI",
    title="Pertanggungjawaban Pidana AI",
    authors=["Budi Santoso"],
    year=2025,
    journal="Jurnal Hukum",
    doi="10.1234/jh.2025.1",
)
app.db.create(rec)

# 2. Format citations
apa_citation = app.bib.format_citation(rec, style="apa")
ieee_in_text = app.bib.format_in_text(rec, style="ieee")
print("APA Citation:", apa_citation)
print("IEEE In-Text:", ieee_in_text)

# 3. Search and export
results = app.bib.search_references("Kecerdasan Buatan", limit=5)
app.bib.export_bibliography("tmp/bib_export.md", style="oscola", format="markdown")
app.close_sync()
```

---

### 3. Federated Academic Search (`search`)

Searches across academic providers in parallel with canonical deduplication.

#### CLI Usage
```bash
# Query arXiv and OpenAlex simultaneously
uv run research search "attention mechanism deep learning" --providers arxiv,openalex --limit 5

# Query all providers including Google Scholar (via TLS impersonation)
uv run research search "corporate criminal liability autonomous systems" \
  --providers arxiv,openalex,crossref,doaj,openaire,scholar \
  --limit 10

# Search without saving results to the database
uv run research search "quantum cryptography" --providers arxiv --limit 3 --no-index
```

#### Python API
```python
import asyncio
from research.app import ResearchApp

async def main():
    app = ResearchApp()
    # Search federated providers concurrently
    results = await app.search_literature(
        "machine learning intellectual property",
        providers=["arxiv", "openalex", "crossref"],
        limit=5,
    )
    for pub in results:
        print(f"[{pub.cite_key}] {pub.title} ({pub.year}) - PDF: {pub.pdf_url}")
    await app.close()

asyncio.run(main())
```

---

### 4. Web Search Integration & Auto-Indexing (`web-search`)

Combines Tavily Search (with API key pool failover) and DuckDuckGo (`ddgs`), cleans raw web content into Markdown with YAML frontmatter, and indexes chunks directly into SQLite RAG.

#### CLI Usage
```bash
# Search web via DuckDuckGo (zero configuration required)
uv run research web-search "pertanggungjawaban pidana deepfake" --provider ddgs --limit 5

# Search web news via all available providers and save markdown to custom folder
uv run research web-search "regulasi kecerdasan buatan uni eropa" \
  --provider all \
  --topic news \
  --limit 5 \
  --output-dir data/web_reports

# Perform search without inserting into SQLite RAG
uv run research web-search "AI governance framework" --provider ddgs --limit 3 --no-index
```

#### Python API
```python
import asyncio
from research.app import ResearchApp

async def main():
    app = ResearchApp()
    resp = await app.search_web(
        "perkembangan regulasi AI di Indonesia",
        provider="ddgs",
        limit=3,
        auto_index=True,
    )
    print(f"Retrieved {len(resp.results)} results in {resp.response_time}s")
    for r in resp.results:
        print(f"- {r.title} ({r.url}) -> Cite Key: {r.cite_key}")
    await app.close()

asyncio.run(main())
```

---

### 5. Citation Graph Snowballing (`snowball`)

Traverses forward (citing papers) and backward (referenced works) from any seed paper using the OpenAlex citation catalog.

#### CLI Usage
```bash
# Snowball both directions (forward and backward)
uv run research snowball Vaswani2017Attention --direction both --limit 10

# Snowball only backward references for foundational literature
uv run research snowball Devlin2018BERT --direction backward --limit 15

# Snowball forward citations to find recent follow-up research
uv run research snowball Vaswani2017Attention --direction forward --limit 20

# Snowball AND fetch full texts of newly discovered papers (anti-curl; optional RAG)
uv run research snowball Noerman2024kriminalisasideepfakeindonesia \
  --direction both --limit 6 --download --index-rag
```
`--download` automatically resolves (Unpaywall/OJS), downloads (dual-engine
anti-bot), and converts newly discovered papers to Markdown — no manual
`curl`/`httpx` needed. Use `--index-rag` to also chunk them into the RAG DB.

#### Python API
```python
import asyncio
from research.app import ResearchApp

async def main():
    app = ResearchApp()
    res = await app.snowball_citations(
        seed_cite_key="Vaswani2017Attention",
        direction="both",
        limit_forward=5,
        limit_backward=5,
    )
    print(f"Discovered: {len(res.citing_papers)} citing, {len(res.referenced_papers)} referenced.")
    await app.close()

asyncio.run(main())
```

---

### 6. Idempotent Parallel Downloader (`download`)

Concurrently downloads open-access PDFs, verifies `%PDF` magic bytes, retries alternative galleys, and classifies failures without false-positive dead links.

#### CLI Usage
```bash
# Download all pending papers using 4 workers
uv run research download --concurrency 4

# Download specific papers by cite_keys
uv run research download --cite-keys Vaswani2017Attention,Devlin2018BERT --concurrency 2

# Force re-download even if files already exist on disk
uv run research download --concurrency 4 --force --timeout 15.0
```

#### Python API
```python
import asyncio
from research.app import ResearchApp

async def main():
    app = ResearchApp(download_dir="data/downloads")
    stats = await app.download_papers(concurrency=4, skip_already_downloaded=True)
    print("Download Summary:", stats)
    await app.close()

asyncio.run(main())
```

---

### 7. PDF to Normalized Markdown Converter (`convert`)

Converts academic PDF documents to cleaned, heading-normalized Markdown and optionally chunks and indexes them into SQLite RAG.

#### CLI Usage
```bash
# Convert a single PDF to Markdown and index into RAG
uv run research convert data/downloads/paper.pdf --output-dir data/markdown --index-rag

# Batch convert an entire directory of PDFs with 6 workers
uv run research convert data/downloads/ --concurrency 6 --index-rag
```

#### Python API
```python
from pathlib import Path
from research.app import ResearchApp

app = ResearchApp()
# Single document conversion
converted_doc = app.pdf.convert_pdf(Path("data/downloads/paper.pdf"))
print(f"Converted {converted_doc.metadata.title}: {converted_doc.metadata.total_pages} pages")

# Save markdown and index chunks into RAG
app.retriever.index_document(
    cite_key="sample_paper",
    title=converted_doc.metadata.title,
    markdown_content=converted_doc.full_markdown,
    corpus="literature",
)
app.close_sync()
```

---

### 7b. Open-Access Full-Text Retrieval (`fulltext`)

Resolves a **DOI / doi.org URL / DB cite_key** directly to its **full-text Markdown**:
Unpaywall open-access resolve → PDF download (via the dual-engine downloader with
curl-cffi Chrome impersonation + OJS fallback, so anti-bot 403s are bypassed;
magic-byte verified) → PyMuPDF conversion → optional RAG indexing.

**This is the canonical "get the full text" one-shot command for agents.** Use it
instead of falling back to abstracts whenever a paper has a DOI.

#### CLI Usage
```bash
# Resolve a DOI to its full-text Markdown (saved under data/markdown/)
uv run research fulltext "10.15642/aj.2025.11.1.125-153"

# Also chunk & index the full text into the RAG database
uv run research fulltext "10.15642/aj.2025.11.1.125-153" --index-rag

# Pass a DIRECT PDF URL when Unpaywall has no OA match (OJS galley, repository, etc.)
uv run research fulltext "10.xxxx/paper" --pdf-url "https://jurnal.../article/download/123/456"

# Custom Markdown output directory, longer timeout, force re-download/re-convert
uv run research fulltext "10.21070/ups.11586" --output-dir data/markdown --timeout 25 --force
```

#### Output
Prints the resolved PDF path and the generated Markdown file path, e.g.:
```
[+] Full text Markdown: data/markdown/10_15642_aj_2025_11_1_125_153.md (29 pages)
```
The Markdown file is the **full text** — read it to extract findings (Tahap 6/17).

#### Resolution order & behavior
`fulltext` finds the PDF URL in this order, so agents never need to hand-roll downloads:
1. `--pdf-url <URL>` (explicit direct URL)
2. `target` itself is a bare `http(s)://...pdf` / OJS download endpoint → used directly
3. Unpaywall Open-Access resolve of a DOI
4. Stored `pdf_url` / landing `url` of a DB cite_key
5. If the resolved URL is an **article landing page** (contains `/article/`, not
   `/download/`), the project's OJS/Highwire extractor pulls the galley PDF URL
   automatically.
If the target/URL already has a verified local PDF in the DB (by DOI or by URL),
it is reused instead of re-downloaded.

#### Notes
- If Unpaywall finds no OA PDF and no DB/`--pdf-url` gives a URL, the command reports
  empty — supply `--pdf-url` or index the record via `research search` first.
- Bug-free guarantee: this command is the substitute for manual `curl`-based PDF
  retrieval; agents MUST use it rather than hand-rolling httpx/curl downloads.

---

### 8. Indonesian Court Judgment Engine (`putusan`)

Processes judicial rulings across MA, MK, MKMK, PN, PT, PA, PM, PTUN, DKPP, and KIP. Handles legal typography unspacing, watermark/disclaimer stripping, legal milestone segmentation (`DUDUK_PERKARA`, `PERTIMBANGAN_HUKUM`, `AMAR`), and context banner injection.

#### CLI Usage
```bash
# Process a single court decision PDF and index chunks into unified RAG
uv run research putusan data/putusan/123_Pid_Sus_2024.pdf \
  --output-dir data/putusan_processed \
  --index-rag

# Process a directory of court decisions with sampling and dense vector embeddings
uv run research putusan /path/to/putusan_archive/ \
  --sample 50 \
  --concurrency 6 \
  --max-chunk-chars 1500 \
  --index-rag \
  --embed
```

#### Python API
```python
from pathlib import Path
from research.putusan.converter import PutusanConverter
from research.db.manager import DatabaseManager

db = DatabaseManager()
converter = PutusanConverter(output_dir="data/putusan_processed", db=db)

# Convert and index putusan
doc = converter.convert_pdf(Path("putusan_sample.pdf"), index_rag=True)
print(f"Case: {doc.metadata.case_number} | Court: {doc.metadata.court_name}")
print(f"Sections detected: {list(doc.sections.keys())}")
print(f"Context chunks: {len(doc.chunks)}")
db.close()
```

---

### 9. Dense Multilingual Vector Embeddings (`embed`)

Computes local ONNX embeddings using `fastembed` (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) and persists 384-dimensional float32 binary blobs in the `chunks` SQLite table.

#### CLI Usage
```bash
# Compute embeddings for all pending chunks across literature, putusan, and web
uv run research embed --batch-size 64
```

#### Python API
```python
from research.app import ResearchApp

app = ResearchApp()
embedded_count = app.embed_chunks(batch_size=64)
print(f"Successfully generated embeddings for {embedded_count} chunks.")
app.close_sync()
```

---

### 10. Cross-Corpus Unified Retrieval & RAG (`query`)

Performs unified semantic search across `literature`, `putusan`, and `web`. Supports `hybrid` (Reciprocal Rank Fusion $k=60$), `bm25` (SQLite FTS5), and `dense` (dot product on normalized float32 vectors). Use `--with-source` to label each hit with its `corpus`/`cite_key`, and `--output FILE` to save the retrieved excerpts to Markdown (handy for riset pendahuluan notes).

#### CLI Usage
```bash
# Hybrid search across all corpora with LLM-ready prompt context formatting
uv run research query "pertanggungjawaban pidana korporasi kecerdasan buatan" \
  --mode hybrid \
  --corpus all \
  --limit 5 \
  --format-context

# Filter search specifically to court decisions (putusan)
uv run research query "unsur melawan hukum deepfake" \
  --mode hybrid \
  --corpus putusan \
  --limit 3

# BM25-only keyword search across academic literature
uv run research query "transformer attention mechanism" \
  --mode bm25 \
  --corpus literature \
  --limit 5

# Search within a single specific paper
uv run research query "positional encoding" \
  --cite-key Vaswani2017Attention \
  --mode dense

# Write results to a file for research notes (riset pendahuluan), with source labels
uv run research query "kekosongan hukum deepfake indonesia" \
  --mode bm25 --corpus all --limit 5 \
  --with-source --output riset/qa/db_query_kekosongan.md
```

#### Python API
```python
import asyncio
from research.app import ResearchApp

async def main():
    app = ResearchApp()
    # Hybrid query returning ranked excerpts
    results = await app.query_rag(
        "pertimbangan hakim mengenai alat bukti elektronik",
        mode="hybrid",
        corpus="putusan",
        limit=3,
    )
    for r in results:
        print(f"[{r.corpus.upper()}] [{r.cite_key}] (score={r.score:.4f}):\n{r.content}\n")

    # Generate prompt block formatted for LLMs
    prompt_context = app.retriever.format_context_for_prompt(results)
    print("Prompt Context:\n", prompt_context)
    await app.close()

asyncio.run(main())
```

---

### 11. Literature Review Card System & Matrix Synthesis (`cards`)

Extracts structured research cards (*Isu Hukum*, *Teori/Dasar Hukum*, *Metodologi*, *Temuan Utama/Amar*, *Research Gap*, *Positioning*), supports researcher tagging and notes, and exports synthesis matrices.

#### CLI Usage
```bash
# Extract card for a specific paper or court judgment
uv run research cards extract --cite-key Vaswani2017Attention
uv run research cards extract --cite-key Putusan_123_Pid_Sus_2024_PN_Jkt_Sel

# Batch extract review cards for all publications in the database
uv run research cards extract --all --limit 50 --concurrency 4

# List review cards in database
uv run research cards list --corpus all --limit 20

# View full review card synthesis
uv run research cards show Putusan_123_Pid_Sus_2024_PN_Jkt_Sel

# Edit researcher annotations and tags
uv run research cards edit Putusan_123_Pid_Sus_2024_PN_Jkt_Sel \
  --notes "Rujukan penting untuk Bab 4 pertanggungjawaban pidana" \
  --tags "ai-crime,uu-ite,pn-jkt-sel"

# Export literature review matrix to Markdown (table + full cards)
uv run research cards export --format markdown --output data/literature_matrix.md

# Export matrix to Excel-compatible UTF-8 BOM CSV
uv run research cards export --format csv --output data/literature_matrix.csv

# Export matrix to JSON
uv run research cards export --format json --output data/literature_matrix.json
```

#### Python API
```python
from research.app import ResearchApp

app = ResearchApp()

# Extract and save card
card = app.cards.extract_and_save("Vaswani2017Attention", force=True)
print("Isu:", card.legal_issue)
print("Teori:", card.theory)
print("Gap:", card.gap)

# Update notes and tags
app.cards.update_annotations(
    "Vaswani2017Attention",
    notes="Foundational paper for sequence-to-sequence transformers.",
    tags=["transformer", "foundational", "nips2017"],
)

# Export matrix
app.cards.export_matrix("tmp/synthesis.md", format="markdown")
app.close_sync()
```

---

### 12. Database Export (`export`)

Exports all indexed publications to standard academic interchange formats.

#### CLI Usage
```bash
# Export to BibTeX
uv run research export --format bibtex --output tmp/exported.bib

# Export to JSON
uv run research export --format json --output tmp/exported.json
```

#### Python API
```python
from research.app import ResearchApp

app = ResearchApp()
records = app.db.list(limit=500)

# Export to BibTeX string
from research.bibtex.export import export_to_bibtex_str
bib_str = export_to_bibtex_str(records)
with open("tmp/records.bib", "w", encoding="utf-8") as f:
    f.write(bib_str)

app.close_sync()
```

---

### 13. End-to-End Autonomous Pipeline (`pipeline`)

Executes the entire research lifecycle: query/seed ingestion $\rightarrow$ federated discovery $\rightarrow$ snowballing $\rightarrow$ parallel downloading $\rightarrow$ PDF conversion $\rightarrow$ RAG chunk indexing.

Supports both **streaming producer-consumer** execution (converts and chunks as PDFs finish downloading) and **staged** execution.

#### CLI Usage
```bash
# Run streaming parallel pipeline for a research query
uv run research pipeline "artificial intelligence copyright fair use" \
  --limit 10 \
  --download-concurrency 4 \
  --convert-concurrency 4

# Run pipeline seeded by a .bib file or directory of .bib files
uv run research pipeline --bib data/seeds/ai_law.bib \
  --no-scholar \
  --snowball-seeds 2 \
  --snowball-limit 8 \
  --download-concurrency 6

# Staged execution (downloads complete before conversion starts)
uv run research pipeline "criminal liability autonomous systems" \
  --no-streaming \
  --limit 5
```

#### Python API
```python
import asyncio
from research.app import ResearchApp

async def main():
    app = ResearchApp()
    res = await app.run_pipeline(
        query="intellectual property deepfake generation",
        search_limit=5,
        include_scholar=False,
        snowball=True,
        snowball_seeds=2,
        download=True,
        convert=True,
        index_rag=True,
        streaming=True,
    )
    print(f"Pipeline executed in {res.duration_seconds:.2f}s:")
    print(f"- Discovered: {res.discovered_count}")
    print(f"- Downloaded: {res.downloaded_count}")
    print(f"- Converted:  {res.converted_count}")
    print(f"- RAG Chunks: {res.chunks_indexed}")
    await app.close()

asyncio.run(main())
```

---

### 14. Normative Legal Research Workflow Tracker (`workflow`)

Operates the 20-stage, 7-phase methodology defined in `workflow.md`. Manages project state, gate-check validations, theoretical frameworks, and exports methodological audit trails.

#### CLI Usage
```bash
# Initialize a new normative thesis research project
uv run research workflow init "Pertanggungjawaban Pidana AI" \
  --author "Budi Santoso" \
  --typology wet_vacuum \
  --approaches "statute,conceptual,comparative" \
  --questions "Bagaimana kualifikasi perbuatan AI?;Bagaimana preskripsi de lege ferenda?"

# Display the 20-stage interactive progress dashboard
uv run research workflow status

# Update stage gate check and record notes / theoretical framework
uv run research workflow check 1 --pass --notes "Isu murni norma hukum mengenai ketiadaan subjek hukum AI"
uv run research workflow check 6 --grand "Keadilan Substantif" --middle "Kebijakan Kriminal" --applied "Strict Liability"

# Export complete methodological audit trail to Markdown
uv run research workflow export --output logs/metodologi_audit.md
```

#### Python API
```python
from research.app import ResearchApp

app = ResearchApp()
proj = app.workflow.init_project(
    title="Pertanggungjawaban Pidana AI",
    typology="wet_vacuum",
    approaches=["statute", "conceptual"],
)
app.workflow.check_stage(stage_num=1, passed=True, notes="Das sollen vs das sein valid.")
print(app.workflow.render_status_dashboard())
app.close_sync()
```

---

### 15. Deductive Legal Syllogism & IRAC Builder (`irac`)

Constructs formal legal syllogisms ($p$: Premis Mayor, $q$: Premis Minor, $r$: Konklusi) formatted in IRAC (*Issue, Rule, Analysis, Conclusion*) with automatic logic validation and criminal law analogy violation guard per Tahap 15.

#### CLI Usage
```bash
# Add a deductive legal syllogism
uv run research irac add \
  --issue "Apakah penyedia sistem AI dapat dipidana atas kelalaian algoritma?" \
  --rule "Pasal 359 KUHP jo. UU ITE" \
  --facts "Pengembang X lalai memvalidasi dataset kendali kemudi hingga menimbulkan kecelakaan" \
  --conclusion "Pengembang X memenuhi unsur kealpaan (culpa) yang mengakibatkan matinya orang" \
  --domain pidana \
  --method interpretasi_teleologis \
  --cite-keys "Santoso2025AI"

# List registered syllogisms
uv run research irac list

# Validate all syllogisms for logic fallacies & criminal analogy violations
uv run research irac validate

# Export IRAC blocks directly to Markdown for insertion into Bab III / Bab IV
uv run research irac export --output data/bab3_analisis.md
```

#### Python API
```python
from research.app import ResearchApp

app = ResearchApp()
syl = app.irac.add_syllogism(
    issue="Status hukum AI",
    rule_major="Pasal 362 KUHP",
    facts_minor="Terdakwa mengambil kode digital secara tanpa hak",
    conclusion="Kode digital terkualifikasi sebagai barang imateriel",
    legal_domain="pidana",
    method_type="interpretasi_teleologis",
)
warnings = syl.validate_logic()
print("Logic warnings:", warnings)
app.close_sync()
```

---

### 16. Skripsi 5-Chapter Thesis Scaffolder (`scaffold`)

Generates the standard 5-chapter thesis Markdown skeleton (`BAB_I_PENDAHULUAN.md`, `BAB_II_TINJAUAN_PUSTAKA.md`, `BAB_III_PEMBAHASAN_1.md`, `BAB_IV_PEMBAHASAN_2.md`, `BAB_V_PENUTUP.md`, `DAFTAR_PUSTAKA.md`) linked dynamically to the active project state, theoretical framework, and IRAC arguments.

#### CLI Usage
```bash
# Generate complete 5-chapter thesis draft directory
uv run research scaffold --output-dir draft_skripsi/ --style indonesia
```

#### Python API
```python
from research.app import ResearchApp

app = ResearchApp()
files = app.scaffolder.generate_draft(output_dir="draft_skripsi", style="indonesia")
for chapter, path in files.items():
    print(f"- {chapter.upper()}: {path}")
app.close_sync()
```

---

### 16b. Literature Review Run (`review-run`)

Turns a `.bib` export into subagent-ready review inputs: dedup by DOI →
relevance-capped snowball → Unpaywall resolve → per-paper packets + manifest.

#### CLI Usage
```bash
uv run research review-run \
  --bib /path/to/references.bib \
  --relevance-query "kecerdasan buatan martabat manusia" \
  --relevance-top-k 10 --relevance-min-score 0.3 \
  --seeds 3 --snowball-limit 20 \
  --out tmp/aiethics_review
```

Writes `manifest.json` plus one packet per paper under `<out>/packets/`.
A paper is labelled `FULL-TEXT` only when a converted Markdown file actually
exists on disk; otherwise `ABSTRACT` or `METADATA` — never optimistic. Follow
by spawning one subagent per manifest entry to write the review card (see the
`literature-review` skill).

#### Notes
- `--relevance-min-score` also filters the *seeds* and papers already in the
  database, not just freshly fetched snowball works; without it an off-topic
  seed drags in off-topic citations.
- Reference-manager exports commonly duplicate every entry under a `...2`
  cite key; ingest deduplicates by normalized DOI (title+year as fallback).

---

### 17. Citation Traceability Auditor (`audit-traceability`)

Scans thesis draft chapters, verifies in-text citations and statutory mentions against the database, catches ghost citations (*no fabrication* rule per Tahap 20), and builds an audit report.

#### CLI Usage
```bash
# Audit draft skripsi directory against database citations
uv run research audit-traceability --draft-dir draft_skripsi/ --output draft_skripsi/audit_report.md
```

#### Python API
```python
from research.app import ResearchApp

app = ResearchApp()
report = app.auditor.audit_drafts("draft_skripsi")
print(f"Verified keys: {len(report.verified_cite_keys)}, Ghost keys: {len(report.ghost_cite_keys)}")
print(report.to_markdown())
app.close_sync()
```

---

## Code Organization

```
src/research/
├── __init__.py           # Lazy app loader (get_app) & CLI entry point (research:main)
├── app.py                # ResearchApp unified application facade
├── cli/                  # Production CLI subcommands and runner
│   ├── parser.py         # Argument parser specification with 19 subcommands
│   └── main.py           # Async CLI execution handlers & signal management
├── normative/            # Normative legal research toolkit supporting workflow.md
│   ├── models.py         # NormativeProject, LegalSyllogism, AuditReport, STAGE_DEFINITIONS (1-20)
│   ├── workflow.py       # WorkflowManager (20-stage state tracker, gate-checks, audit export)
│   ├── irac.py           # IRACManager (deductive legal syllogisms, logic fallacies & analogy guard)
│   ├── scaffold.py       # ThesisScaffolder (5-chapter skripsi markdown generator linked to DB)
│   └── traceability.py   # TraceabilityAuditor (draft citation scanner, ghost detector, primary sources)
├── bibtex/               # BibTeX parser, normalizer, and SQLite/JSON exporter
│   ├── models.py         # BibEntry dataclass with .to_publication() mapping
│   ├── parser.py         # parse_bib_file, parse_bib_files, expand_bib_paths
│   └── export.py         # export_to_json, export_to_sqlite, export_to_bibtex_str
├── bibliography/         # Full CRUD bibliography manager & multi-CSL formatting engine
│   ├── models.py         # Author & CSLItem models, CSL-JSON & RIS converters
│   ├── csl.py            # CSLEngine (APA, IEEE, Harvard, Chicago, MLA, Vancouver, OSCOLA, Indonesian)
│   └── manager.py        # BibliographyManager (CRUD, multi-source import, export, FTS search)
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
│   └── client.py         # UnpaywallClient (polite pool)
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
├── cards/                # Literature review card system, researcher annotations & matrix export
│   ├── models.py         # ReviewCard dataclass (.to_dict(), .from_row(), .to_markdown_card())
│   ├── extractor.py      # CardExtractor (heuristic & milestone-aware literature & putusan extractor)
│   ├── export.py         # Matrix export (Markdown GFM table + cards, UTF-8 BOM CSV, JSON)
│   └── manager.py        # CardManager (SQLite review_cards & FTS5 CRUD, batch extraction, search)
├── review/               # Literature-review run orchestration (bib -> ranked snowball -> packets)
│   ├── models.py         # ReviewPaper, ReviewRunResult (label + relevance per queued paper)
│   └── review_run.py     # run_review(): dedup ingest, capped snowball, Unpaywall, packets
└── putusan/              # Indonesian Court Judgment conversion & context-preserving chunking
    ├── models.py         # PutusanMetadata, PutusanSection, PutusanChunk, PutusanDocument
    ├── normalizer.py     # Watermark/disclaimer stripping, spaced typography unspacing, table reflow
    ├── extractor.py      # Regex & heuristic metadata extraction (case number, court, parties, dates)
    ├── segmenter.py      # Legal milestones segmenter (Kepala, Identitas, Duduk Perkara, Pertimbangan, Amar, Penutup)
    ├── chunker.py        # Context-preserving semantic chunker with injected legal context banners
    └── converter.py      # PutusanConverter (batch processing, Tesseract OCR fallback, JSON/MD export)
```

Import packages strictly using absolute `src/` layout: `from research.db import DatabaseManager`, never relative imports.

---

## Skills — Creation Reference

When the user asks to **create, refactor, or fix a skill**, follow the official
best practices: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices>
(also `https://code.claude.com/docs/en/skills` for Claude Code specifics).

Project skills live in `.claude/skills/<skill-name>/SKILL.md`.

Required structure & rules:
- **File**: must be `SKILL.md` (exact name) inside `.claude/skills/<name>/`.
- **Frontmatter**: exactly `name` (≤64 chars, lowercase/numbers/hyphens, no
  XML, no reserved "anthropic"/"claude") and `description` (non-empty,
  ≤1024 chars, **third-person**, includes "what it does" + "when to use it"
  with trigger keywords). No XML tags.
- **Naming**: prefer gerund/noun-phrase (e.g. `processing-pdfs`,
  `writing-abstracts`); avoid vague names (`helper`, `utils`).
- **Body**: keep under 500 lines; use **progressive disclosure** — SKILL.md
  is an overview; put details in sibling files (`reference.md`, `FORMS.md`,
  `scripts/`) loaded on demand; keep references **one level deep**.
- **Content**: concise (Claude already knows basics); consistent terminology;
  concrete examples; workflows with checklists + feedback loops; no
  time-sensitive info outside an "old patterns" section; forward slashes.
- **Anti-patterns**: don't offer many tool options; don't assume packages
  installed; don't defer error handling in scripts.
- **Grounding**: when the skill wraps project doctrine, point it at
  `knowledge/` files (e.g. `knowledge/review-kualitas/`,
  `knowledge/penulisan/`) — keep references relative from SKILL.md.

Existing project skills: `reviewer` (legal-research quality review) and
`abstrak` (normative abstract writing/review) under `.claude/skills/`.

---

## Conventions & Rules

- **Python 3.13+**: PEP 604 unions (`str | None`, `list[str]`), `X | None` return types — no legacy `Optional` or `List` from `typing`. Use `from typing import Self` and `from types import TracebackType` for context managers.
- **Dataclasses**: Dataclasses for all domain models; mutable fields strictly use `field(default_factory=list)` or `field(default_factory=dict)`.
- **Keyword-Only Arguments**: Enforce `*` keyword-only arguments for optional and configurable parameters in public APIs (e.g. `search(query, *, limit=10)`).
- **Async-First**: All network and pipeline operations are `async def`. Provide synchronous wrappers (`_sync`) for CLI and standalone scripts.
- **Logging**: Use `loguru.logger` everywhere; do not use the standard library `logging`.
- **Polite Pools Email**: Academic API clients (Crossref, OpenAlex, Unpaywall, OpenAIRE) use `rdndds@gmail.com`.
- **Ruff Compliance**: The codebase must maintain 100% compliance with `uv run ruff check .` without ignoring errors.
- **Graceful Shutdown**: Always ensure background workers, database connections, and HTTP clients close properly via shielded teardown blocks.
- **Continuous Self-Improvement**: Treat every completed phase as a chance to harden the platform — if a step required manual work, boat-anchor it into the CLI/workflow/agent guidance (rule #10).