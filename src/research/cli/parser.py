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
    p_pipe = subparsers.add_parser("pipeline", help="Run end-to-end research lifecycle (search -> snowball -> download -> convert -> RAG)")
    p_pipe.add_argument("query", help="Research topic or search query")
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
    p_query = subparsers.add_parser("query", help="Query full-text indexed literature chunks using FTS5 BM25")
    p_query.add_argument("query", help="Question or topic keywords to search")
    p_query.add_argument("--limit", type=int, default=5, help="Number of excerpts to return (default: 5)")
    p_query.add_argument("--cite-key", help="Filter search to a specific paper cite_key")
    p_query.add_argument("--format-context", action="store_true", help="Output as LLM-ready markdown prompt block")

    # 7. export
    p_exp = subparsers.add_parser("export", help="Export publications database to BibTeX, JSON, or SQLite")
    p_exp.add_argument("--format", choices=["bibtex", "json"], default="bibtex", help="Export format (default: bibtex)")
    p_exp.add_argument("--output", help="Output file path (default: stdout or tmp/export.<ext>)")

    # 8. stats
    subparsers.add_parser("stats", help="Show database metrics (publications, downloads, conversions, RAG chunks)")

    return parser
