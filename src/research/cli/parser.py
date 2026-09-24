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
    parser.add_argument("--log-dir", default="logs", help="Directory for auto-generated run log files (default: logs)")
    parser.add_argument("--no-log-file", action="store_true", help="Disable auto-generating log file under logs directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debug logging")
    parser.add_argument("--no-cache", action="store_true", help="Disable persistent HTTP/page caching")
    parser.add_argument("--clear-cache", action="store_true", help="Clear cached HTTP responses")

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
    p_pipe.add_argument("--download-concurrency", type=int, default=6, help="Concurrent download workers (default: 6)")
    p_pipe.add_argument("--no-convert", action="store_true", help="Skip converting PDFs to Markdown")
    p_pipe.add_argument("--convert-concurrency", type=int, default=4, help="Concurrent conversion workers (default: 4)")
    p_pipe.add_argument("--snowball-concurrency", type=int, default=4, help="Concurrent snowball workers (default: 4)")
    p_pipe.add_argument("--no-rag", action="store_true", help="Skip semantic chunking and RAG indexing")
    p_pipe.add_argument(
        "--no-streaming",
        action="store_true",
        help="Disable streaming producer-consumer mode and use staged execution",
    )
    p_pipe.add_argument(
        "--force-download",
        action="store_true",
        help="Force redownloading papers even if already downloaded or cached",
    )

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
    p_dl.add_argument("--force", action="store_true", help="Force redownloading papers even if already downloaded or cached")

    # 5. convert
    p_conv = subparsers.add_parser("convert", help="Convert PDF(s) to normalized Markdown with layout cleaning")
    p_conv.add_argument("path", help="Path to PDF file or directory containing PDFs")
    p_conv.add_argument("--output-dir", help="Directory to save converted .md files")
    p_conv.add_argument("--concurrency", type=int, default=4, help="Concurrent conversion workers (default: 4)")
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

    # 12. cards / matrix
    p_cards = subparsers.add_parser(
        "cards",
        help="Card System & Literature Review Matrix: extraction (isu, teori, temuan, gap, positioning) and exports",
    )
    cards_subs = p_cards.add_subparsers(dest="cards_action", help="Cards action")

    # cards extract
    p_cextract = cards_subs.add_parser(
        "extract",
        help="Extract literature review cards from papers or court decisions",
    )
    p_cextract.add_argument("--cite-key", help="Extract specific publication by cite_key")
    p_cextract.add_argument("--all", action="store_true", help="Extract cards for all publications in database")
    p_cextract.add_argument(
        "--corpus",
        choices=["all", "literature", "putusan", "web"],
        default="all",
        help="Filter extraction by corpus (default: all)",
    )
    p_cextract.add_argument("--force", action="store_true", help="Re-extract and overwrite existing cards")
    p_cextract.add_argument("--concurrency", type=int, default=4, help="Concurrent worker threads (default: 4)")
    p_cextract.add_argument("--limit", type=int, default=200, help="Maximum publications to process (default: 200)")

    # cards list
    p_clist = cards_subs.add_parser("list", help="List literature review cards in database")
    p_clist.add_argument(
        "--corpus",
        choices=["all", "literature", "putusan", "web"],
        default="all",
        help="Filter by corpus (default: all)",
    )
    p_clist.add_argument("--tag", help="Filter by tag (e.g. pidana, ai, deepfake)")
    p_clist.add_argument("--query", help="Keyword search across card fields using FTS5")
    p_clist.add_argument("--limit", type=int, default=50, help="Max cards to list (default: 50)")

    # cards show
    p_cshow = cards_subs.add_parser("show", help="Show full literature review card details for a paper/putusan")
    p_cshow.add_argument("cite_key", help="Citation key or case identifier")

    # cards edit
    p_cedit = cards_subs.add_parser("edit", help="Update annotations on a literature review card")
    p_cedit.add_argument("cite_key", help="Citation key or case identifier")
    p_cedit.add_argument("--issue", help="Update legal issue / research problem")
    p_cedit.add_argument("--theory", help="Update theory / legal basis")
    p_cedit.add_argument("--methodology", help="Update research methodology")
    p_cedit.add_argument("--findings", help="Update key findings / ratio decidendi / verdict")
    p_cedit.add_argument("--gap", help="Update research gap / limitations")
    p_cedit.add_argument("--positioning", help="Update research positioning / novelty")
    p_cedit.add_argument("--tags", help="Update tags (comma-separated)")
    p_cedit.add_argument("--notes", help="Update researcher personal notes")

    # cards export
    p_cexport = cards_subs.add_parser("export", help="Export literature review matrix table and cards")
    p_cexport.add_argument(
        "--format",
        choices=["markdown", "csv", "json"],
        default="markdown",
        help="Export format (default: markdown)",
    )
    p_cexport.add_argument("--output", help="Output file path (default: data/literature_matrix.<ext>)")
    p_cexport.add_argument(
        "--corpus",
        choices=["all", "literature", "putusan", "web"],
        default="all",
        help="Filter by corpus (default: all)",
    )
    p_cexport.add_argument("--tag", help="Filter by tag")
    p_cexport.add_argument(
        "--no-details",
        action="store_true",
        help="Exclude detail cards (table only in markdown)",
    )

    # bib (Full CRUD Bibliography & Multi-CSL Manager)
    p_bib = subparsers.add_parser("bib", help="Full CRUD bibliography manager with multi-CSL citation styling")
    bib_subs = p_bib.add_subparsers(dest="bib_action", help="Bibliography action")

    # bib list
    p_blist = bib_subs.add_parser("list", help="List and format bibliography entries in CSL style")
    p_blist.add_argument(
        "--style",
        choices=["apa", "ieee", "harvard", "chicago", "chicago-note", "mla", "vancouver", "oscola", "indonesia", "bibtex", "ris", "csl-json"],
        default="apa",
        help="Citation Style Language (default: apa)",
    )
    p_blist.add_argument(
        "--corpus",
        choices=["all", "literature", "putusan", "web"],
        default="all",
        help="Filter by corpus (default: all)",
    )
    p_blist.add_argument("--query", help="Full-text search query across bibliography")
    p_blist.add_argument("--author", help="Filter by author name substring")
    p_blist.add_argument("--journal", help="Filter by journal / venue substring")
    p_blist.add_argument("--year", type=int, help="Filter by publication year")
    p_blist.add_argument("--limit", type=int, default=20, help="Maximum entries to list (default: 20)")
    p_blist.add_argument("--offset", type=int, default=0, help="Offset for pagination (default: 0)")

    # bib show
    p_bshow = bib_subs.add_parser("show", help="Show reference formatted in one or all CSL styles")
    p_bshow.add_argument("cite_key", help="Citation key of the publication")
    p_bshow.add_argument(
        "--style",
        choices=["all", "apa", "ieee", "harvard", "chicago", "chicago-note", "mla", "vancouver", "oscola", "indonesia", "bibtex", "ris", "csl-json"],
        default="all",
        help="CSL style to format (default: all)",
    )
    p_bshow.add_argument("--in-text", action="store_true", help="Also display in-text citation format")

    # bib add
    p_badd = bib_subs.add_parser("add", help="Manually add a new reference to the bibliography")
    p_badd.add_argument("--title", required=True, help="Publication title")
    p_badd.add_argument("--author", action="append", help="Author name (can be repeated or comma-separated)")
    p_badd.add_argument("--year", type=int, help="Publication year")
    p_badd.add_argument("--journal", help="Journal, book, or venue name")
    p_badd.add_argument("--volume", help="Volume number")
    p_badd.add_argument("--issue", help="Issue / number")
    p_badd.add_argument("--pages", help="Page range (e.g. 100-125)")
    p_badd.add_argument("--doi", help="Digital Object Identifier (DOI)")
    p_badd.add_argument("--url", help="URL / Link to paper")
    p_badd.add_argument("--abstract", help="Abstract text")
    p_badd.add_argument("--entry-type", default="article", help="Entry type: article, book, inproceedings, putusan, etc. (default: article)")
    p_badd.add_argument("--cite-key", help="Custom citation key (auto-generated if omitted)")

    # bib update
    p_bupdate = bib_subs.add_parser("update", help="Update fields of an existing bibliography entry")
    p_bupdate.add_argument("cite_key", help="Citation key of reference to update")
    p_bupdate.add_argument("--title", help="New title")
    p_bupdate.add_argument("--author", action="append", help="New author name(s)")
    p_bupdate.add_argument("--year", type=int, help="New publication year")
    p_bupdate.add_argument("--journal", help="New journal/venue name")
    p_bupdate.add_argument("--volume", help="New volume")
    p_bupdate.add_argument("--issue", help="New issue/number")
    p_bupdate.add_argument("--pages", help="New pages")
    p_bupdate.add_argument("--doi", help="New DOI")
    p_bupdate.add_argument("--url", help="New URL")
    p_bupdate.add_argument("--abstract", help="New abstract")

    # bib delete
    p_bdel = bib_subs.add_parser("delete", help="Delete a reference from the bibliography")
    p_bdel.add_argument("cite_key", help="Citation key of reference to delete")
    p_bdel.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

    # bib import
    p_bimp = bib_subs.add_parser("import", help="Import references from BibTeX, CSL-JSON, RIS, or DOI")
    p_bimp.add_argument("source", help="File path, DOI string, or raw content")
    p_bimp.add_argument(
        "--format",
        choices=["auto", "bibtex", "csl-json", "ris", "doi"],
        default="auto",
        help="Format of source (default: auto)",
    )

    # bib export
    p_bexp = bib_subs.add_parser("export", help="Export bibliography formatted in selected CSL style and format")
    p_bexp.add_argument("--output", required=True, help="Destination output file path")
    p_bexp.add_argument(
        "--style",
        choices=["apa", "ieee", "harvard", "chicago", "chicago-note", "mla", "vancouver", "oscola", "indonesia", "bibtex", "ris", "csl-json"],
        default="apa",
        help="Citation style (default: apa)",
    )
    p_bexp.add_argument(
        "--format",
        choices=["markdown", "text", "html", "json", "bibtex", "ris"],
        default="markdown",
        help="Output document format (default: markdown)",
    )
    p_bexp.add_argument(
        "--corpus",
        choices=["all", "literature", "putusan", "web"],
        default="all",
        help="Filter by corpus (default: all)",
    )
    p_bexp.add_argument("--query", help="Filter by search query")
    p_bexp.add_argument("--limit", type=int, default=500, help="Maximum entries to export (default: 500)")

    return parser

