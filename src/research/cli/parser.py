from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="research",
        description="Automated Academic Research, Citation Graph Snowballing, and Literature Discovery Platform.",
    )
    parser.add_argument("--db", default="tmp/publications.sqlite", help="Path to SQLite database (default: tmp/publications.sqlite)")
    parser.add_argument("--downloads", default="data/downloads", help="Path to PDF downloads directory (default: data/downloads)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debug logging")

    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommand to execute")

    # 1. pipeline
    p_pipe = subparsers.add_parser(
        "pipeline",
        help="Run end-to-end research lifecycle (.bib -> search -> snowball -> download -> convert -> RAG)",
    )
    p_pipe.add_argument(
        "query",
        nargs="?",
        default="",
        help="Research topic or search query (optional if --bib is specified)",
    )
    p_pipe.add_argument("--bib", help="Path to seed .bib file or directory with .bib files")
    p_pipe.add_argument("--limit", type=int, default=15, help="Search limit per provider (default: 15)")
    p_pipe.add_argument("--providers", help="Comma-separated providers (e.g. arxiv,openalex,crossref,doaj,openaire)")
    p_pipe.add_argument("--no-scholar", action="store_true", help="Exclude Google Scholar")
    p_pipe.add_argument("--no-snowball", action="store_true", help="Skip citation graph snowballing")
    p_pipe.add_argument("--snowball-seeds", type=int, default=2, help="Number of top seed papers to snowball (default: 2)")
    p_pipe.add_argument("--no-download", action="store_true", help="Skip downloading PDFs")
    p_pipe.add_argument("--no-convert", action="store_true", help="Skip converting PDFs to Markdown")
    p_pipe.add_argument("--no-rag", action="store_true", help="Skip semantic chunking and RAG indexing")

    # 2. search
    p_search = subparsers.add_parser("search", help="Search academic literature across federated providers and Google Scholar")
    p_search.add_argument("query", help="Search query string")
    p_search.add_argument("--providers", help="Comma-separated providers (arxiv, openalex, crossref, doaj, openaire, scholar)")
    p_search.add_argument("--limit", type=int, default=10, help="Max results to fetch (default: 10)")
    p_search.add_argument("--no-index", action="store_true", help="Do not save results into SQLite database")

    # 3. snowball
    p_snow = subparsers.add_parser("snowball", help="Expand citation network (citing and referenced papers)")
    p_snow.add_argument("cite_key", help="Seed paper cite_key in the database")
    p_snow.add_argument("--direction", choices=["forward", "backward", "both"], default="both", help="Traversal direction (default: both)")
    p_snow.add_argument("--limit", type=int, default=10, help="Max forward/backward citations to fetch (default: 10)")

    # 4. download
    p_dl = subparsers.add_parser("download", help="Concurrently download open-access PDFs with %%PDF magic byte verification")
    p_dl.add_argument("--cite-keys", help="Comma-separated cite_keys to download (default: all pending)")
    p_dl.add_argument("--concurrency", type=int, default=4, help="Concurrent download workers (default: 4)")

    # 5. convert
    p_conv = subparsers.add_parser("convert", help="Convert PDF(s) to normalized Markdown with layout cleaning")
    p_conv.add_argument("path", help="Path to PDF file or directory containing PDFs")
    p_conv.add_argument("--output-dir", help="Directory to save converted .md files")
    p_conv.add_argument("--index-rag", action="store_true", help="Also chunk and index into RAG database")

    # 6. query (RAG)
    p_query = subparsers.add_parser(
        "query",
        help="Query cross-corpus indexed literature & putusan using Hybrid (BM25 + Dense RRF), BM25, or Dense RAG",
    )
    p_query.add_argument("query", help="Question or topic keywords to search")
    p_query.add_argument(
        "--mode",
        choices=["hybrid", "bm25", "dense"],
        default="hybrid",
        help="Search mode: hybrid (BM25 + Dense RRF), bm25, or dense (default: hybrid)",
    )
    p_query.add_argument(
        "--corpus",
        choices=["all", "literature", "putusan", "web"],
        default="all",
        help="Corpus to search: all, literature, putusan, or web (default: all)",
    )
    p_query.add_argument("--limit", type=int, default=5, help="Number of excerpts to return (default: 5)")
    p_query.add_argument("--cite-key", help="Filter search to a specific paper cite_key")
    p_query.add_argument("--format-context", action="store_true", help="Output as LLM-ready markdown prompt block")
    p_query.add_argument(
        "--embed",
        action="store_true",
        help="Generate missing dense vector embeddings for all chunks before searching",
    )

    # 7. export
    p_exp = subparsers.add_parser("export", help="Export publications database to BibTeX, JSON, or SQLite")
    p_exp.add_argument("--format", choices=["bibtex", "json"], default="bibtex", help="Export format (default: bibtex)")
    p_exp.add_argument("--output", help="Output file path (default: stdout or tmp/export.<ext>)")

    # 8. stats
    subparsers.add_parser("stats", help="Show database metrics (publications, downloads, conversions, RAG chunks)")

    # 9. putusan
    p_putusan = subparsers.add_parser(
        "putusan",
        help="Convert and chunk Indonesian court decisions (Putusan) preserving legal context",
    )
    p_putusan.add_argument("path", help="Path to Putusan PDF or directory containing Putusan PDFs")
    p_putusan.add_argument(
        "--output-dir",
        default="data/putusan_processed",
        help="Directory to save converted markdown and chunks JSON (default: data/putusan_processed)",
    )
    p_putusan.add_argument("--sample", type=int, default=None, help="Process only N sample PDFs if path is a directory")
    p_putusan.add_argument("--concurrency", type=int, default=4, help="Concurrent workers for batch conversion (default: 4)")
    p_putusan.add_argument(
        "--max-chunk-chars",
        type=int,
        default=1500,
        help="Target max characters per chunk (default: 1500)",
    )
    p_putusan.add_argument(
        "--index-rag",
        action="store_true",
        help="Index converted Putusan chunks into SQLite unified RAG database",
    )
    p_putusan.add_argument(
        "--embed",
        action="store_true",
        help="Compute dense vector embeddings for newly indexed chunks",
    )

    # 10. embed
    p_embed = subparsers.add_parser(
        "embed",
        help="Generate and persist dense vector embeddings for all unembedded chunks",
    )
    p_embed.add_argument("--batch-size", type=int, default=64, help="Embedding batch size (default: 64)")

    # 11. web-search
    p_web = subparsers.add_parser(
        "web-search",
        help="Search web via Tavily and/or DuckDuckGo (ddgs), extract to clean Markdown, and auto-index into RAG",
    )
    p_web.add_argument("query", help="Web search query string")
    p_web.add_argument(
        "--provider",
        choices=["all", "tavily", "ddgs"],
        default="all",
        help="Search provider to use (default: all)",
    )
    p_web.add_argument(
        "--topic",
        choices=["general", "news"],
        default="general",
        help="Search topic: general web or news (default: general)",
    )
    p_web.add_argument("--limit", type=int, default=5, help="Number of results to retrieve (default: 5)")
    p_web.add_argument("--no-index", action="store_true", help="Do not save and index into SQLite RAG database")
    p_web.add_argument(
        "--output-dir",
        default="data/web_searches",
        help="Directory to save extracted markdown files (default: data/web_searches)",
    )

    return parser

