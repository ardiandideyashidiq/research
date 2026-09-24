from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger

from research.app import ResearchApp
from research.cache.models import CachePolicy
from research.cli.parser import build_parser
from research.db.models import PublicationRecord
from research.pipeline.models import PipelineConfig


def setup_logging(
    verbose: bool = False,
    *,
    log_dir: str | Path = "logs",
    enable_file_logging: bool = True,
) -> Path | None:
    """Configure console and file logging.

    Args:
        verbose: Set console level to DEBUG if True, else INFO.
        log_dir: Path to directory for auto-generated run log files.
        enable_file_logging: Whether to automatically write logs to a file.

    Returns:
        The Path to the created log file, or None if file logging is disabled.
    """
    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )

    if not enable_file_logging:
        return None

    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)

    now = datetime.now(tz=UTC).astimezone()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    log_file = path / f"research_{timestamp}.log"
    if log_file.exists():
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S_%f")
        log_file = path / f"research_{timestamp}.log"

    logger.add(
        str(log_file),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8",
        enqueue=True,
    )
    logger.debug("Run log started: {}", log_file)
    return log_file


_setup_logging = setup_logging


async def _async_main(args: Any) -> int:
    policy = CachePolicy(enabled=not getattr(args, "no_cache", False))
    app = ResearchApp(db_path=args.db, download_dir=args.downloads, cache_policy=policy)
    cmd = args.command

    if getattr(args, "clear_cache", False):
        cleared = app.cache.clear()
        print(f"[*] Cleared {cleared} entries from HTTP cache.\n")

    try:
        if cmd == "stats":
            stats = app.get_stats()
            statuses = app.db.get_status_summary()
            print("\n=== Research Database Status ===")
            print(f"  Database path:       {args.db}")
            print(f"  Total Publications:  {stats['total_publications']}")
            print(f"  Downloaded PDFs:     {stats['downloaded']}")
            print(f"  Converted Documents: {stats['converted']}")
            print(f"  RAG Semantic Chunks: {stats['total_chunks']}")
            print(f"  Dense Embeddings:    {stats.get('total_embeddings', 0)}")
            cards_stats = app.cards.count_cards()
            print(f"  Review Cards:        {cards_stats['total_cards']}")
            cache_info = stats.get("cache", {})
            if cache_info:
                print(
                    f"  HTTP Cached Entries: {cache_info.get('total_cached', 0)} "
                    f"({cache_info.get('active_cached', 0)} active)"
                )
                print(f"  HTTP Cache Storage:  {cache_info.get('total_bytes', 0) / 1024:.1f} KB")
            corpus_b = stats.get("corpus_breakdown", {})
            if corpus_b:
                print("  Corpus breakdown:")
                for c_name, c_cnt in sorted(corpus_b.items()):
                    print(f"    - {c_name: <16}: {c_cnt}")
            if statuses:
                print("  Status breakdown:")
                for st, cnt in sorted(statuses.items()):
                    print(f"    - {st: <16}: {cnt}")
            print("================================\n")
            return 0

        if cmd == "pipeline":
            if not args.query and not args.bib:
                print("\n[-] Error: Please specify a search query or a --bib seed file/directory.\n")
                return 1

            if args.bib:
                raw_paths = [p.strip() for p in args.bib.split(",") if p.strip()] if "," in args.bib else [args.bib]
                for bp in raw_paths:
                    if not Path(bp).exists():
                        print(f"\n[-] Error: Specified --bib path does not exist: '{bp}'\n", file=sys.stderr)
                        return 1

            provs = [p.strip() for p in args.providers.split(",")] if args.providers else None
            cfg = PipelineConfig(
                query=args.query or "",
                bib_path=args.bib,
                providers=provs,
                search_limit=args.limit,
                include_scholar=not args.no_scholar,
                snowball=not args.no_snowball,
                snowball_seeds=args.snowball_seeds,
                snowball_concurrency=getattr(args, "snowball_concurrency", 4),
                download=not args.no_download,
                download_concurrency=getattr(args, "download_concurrency", 6),
                download_timeout=getattr(args, "download_timeout", 10.0),
                convert=not args.no_convert,
                convert_concurrency=getattr(args, "convert_concurrency", 4),
                index_rag=not args.no_rag,
                streaming=not getattr(args, "no_streaming", False),
                force=getattr(args, "force_download", False),
            )
            desc = f"query='{args.query}'" if args.query else ""
            if args.bib:
                bib_type = "dir" if Path(args.bib).is_dir() else "seed"
                desc += f" (bib {bib_type}='{args.bib}')" if desc else f"bib {bib_type}='{args.bib}'"
            mode_desc = "streaming parallel" if cfg.streaming else "staged parallel"
            print(f"\n[+] Executing end-to-end research pipeline [{mode_desc}] for: {desc}...")
            res = await app.pipeline.run(cfg)
            print("\n" + res.summary() + "\n")
            return 0

        if cmd == "search":
            provs = [p.strip() for p in args.providers.split(",")] if args.providers else None
            print(f"\n[+] Searching for: '{args.query}' (limit={args.limit})...")
            results = []

            if not provs or "scholar" not in provs:
                academic_res = await app.search_academic(
                    args.query,
                    providers=provs,
                    limit_per_provider=args.limit,
                    auto_index=not args.no_index,
                )
                results.extend(academic_res)

            if not provs or "scholar" in provs:
                scholar_res = await app.search_scholar(
                    args.query,
                    limit=args.limit,
                    auto_index=not args.no_index,
                )
                results.extend(scholar_res)

            print(f"[+] Found {len(results)} publications:\n")
            for i, r in enumerate(results[:args.limit], start=1):
                authors_str = ", ".join(r.authors[:3]) + (" et al." if len(r.authors) > 3 else "")
                year_str = f"({r.year})" if r.year else ""
                print(f"  [{i}] {r.title} {year_str}")
                print(f"      Cite Key: {r.cite_key} | Authors: {authors_str}")
                print(f"      Venue:    {r.journal or 'N/A'}")
                if r.pdf_url:
                    print(f"      PDF:      {r.pdf_url}")
                print()
            return 0

        if cmd == "snowball":
            print(f"\n[+] Snowballing citations for: '{args.cite_key}' (direction={args.direction})...")
            res = await app.run_snowball(
                args.cite_key,
                direction=args.direction,
                limit_forward=args.limit,
                limit_backward=args.limit,
            )
            print(f"\nSnowballing Complete for {res.seed_cite_key} ('{res.seed_title}'):")
            print(f"  - Forward (Citing):      {res.forward_count} papers")
            print(f"  - Backward (References):  {res.backward_count} papers")
            print(f"  - Newly Indexed to DB:    {res.newly_indexed_count} records\n")
            return 0

        if cmd == "download":
            c_keys = [k.strip() for k in args.cite_keys.split(",")] if args.cite_keys else None
            app.downloader.concurrency = args.concurrency
            if hasattr(args, "timeout") and args.timeout is not None:
                app.downloader.timeout = args.timeout
            force = getattr(args, "force", False)
            print("\n[+] Concurrently downloading open-access papers...")
            stats = await app.download_papers(cite_keys=c_keys, force=force)
            print("\nDownload Results:")
            for k, v in stats.items():
                print(f"  - {k: <16}: {v}")
            print()
            return 0

        if cmd == "convert":
            in_path = Path(args.path)
            if in_path.is_file():
                files = [in_path]
            elif in_path.is_dir():
                files = sorted(in_path.glob("*.pdf"))
            else:
                print(f"Error: Path '{args.path}' does not exist.", file=sys.stderr)
                return 1

            concurrency = getattr(args, "concurrency", 4)
            print(f"\n[+] Concurrently converting {len(files)} PDF document(s) to normalized Markdown (workers={concurrency})...")
            out_dir = Path(args.output_dir) if args.output_dir else None

            sem = asyncio.Semaphore(concurrency)

            async def _worker(pdf_file: Path) -> tuple[bool, int, str]:
                out_md = (out_dir / pdf_file.with_suffix(".md").name) if out_dir else pdf_file.with_suffix(".md")
                async with sem:
                    try:
                        _, conv_doc = await app.pdf.convert_file_async(pdf_file, out_md)
                        c_count = 0
                        if args.index_rag:
                            chunks = await asyncio.to_thread(
                                app.retriever.index_document,
                                conv_doc,
                                cite_key=pdf_file.stem,
                            )
                            c_count = len(chunks)
                        msg = f"  - Converted {pdf_file.name} -> {out_md.name} ({conv_doc.total_pages} pages)"
                        return True, c_count, msg
                    except Exception as e:  # noqa: BLE001
                        return False, 0, f"  - Failed {pdf_file.name}: {e}"

            tasks = [asyncio.create_task(_worker(f)) for f in files]
            try:
                results = await asyncio.gather(*tasks)
            except (asyncio.CancelledError, KeyboardInterrupt):
                for t in tasks:
                    if not t.done():
                        t.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                raise

            converted_count = 0
            chunks_count = 0
            for success, c_count, msg in results:
                print(msg)
                if success:
                    converted_count += 1
                    chunks_count += c_count

            print(f"\n[+] Successfully converted {converted_count} files ({chunks_count} RAG chunks indexed).\n")
            return 0

        if cmd == "query":
            if getattr(args, "embed", False):
                print("\n[+] Checking and generating missing dense vector embeddings...")
                app.retriever.embed_all_chunks()

            corpus_str = f" [corpus: {args.corpus}]" if args.corpus != "all" else ""
            mode_str = f" [mode: {args.mode}]"
            print(f"\n[+] Searching indexed database for: '{args.query}'{mode_str}{corpus_str}...")
            results = await app.query_rag(
                args.query,
                limit=args.limit,
                cite_key=args.cite_key,
                mode=args.mode,
                corpus=args.corpus,
            )

            if not results:
                print("\n  No matching chunks found in database.\n")
                return 0

            if args.format_context:
                print("\n" + app.retriever.format_context(results) + "\n")
            else:
                print(f"\n[+] Top {len(results)} Ranked Excerpts:\n")
                for i, r in enumerate(results, start=1):
                    citation = r.formatted_citation()
                    print(f"--- [{i}] {citation} (Match: {r.retrieval_mode}, Score: {r.score:.4f}) ---")
                    print(r.chunk.content.strip())
                    print()
            return 0

        if cmd == "export":
            records = app.db.list(limit=1000)
            out_format = args.format
            out_path = args.output

            if out_format == "json":
                data = [r.to_dict() for r in records]
                content = json.dumps(data, indent=2, ensure_ascii=False)
                default_file = "tmp/publications_export.json"
            else:
                # BibTeX export
                from research.bibtex.export import export_to_bibtex_str
                content = export_to_bibtex_str(records)
                default_file = "tmp/publications_export.bib"

            target = Path(out_path or default_file)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print(f"\n[+] Exported {len(records)} records ({out_format}) -> {target}\n")
            return 0

        if cmd == "putusan":
            import glob

            from research.putusan import PutusanConverter

            in_path = Path(args.path)
            out_dir = Path(args.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            converter = PutusanConverter(
                max_chunk_chars=args.max_chunk_chars,
            )

            if in_path.is_file():
                doc = converter.convert_pdf(in_path)
                md_path = out_dir / f"{doc.doc_id}.md"
                json_path = out_dir / f"{doc.doc_id}_chunks.json"
                converter.export_markdown(doc, md_path)
                converter.export_chunks_json(doc.chunks, json_path)
                if getattr(args, "index_rag", False):
                    app.retriever.index_putusan_document(
                        doc,
                        markdown_path=str(md_path),
                        embed=getattr(args, "embed", False),
                    )
                print(f"\n[+] Converted Putusan: {doc.metadata.nomor_putusan}")
                print(f"  Pengadilan:  {doc.metadata.pengadilan}")
                print(f"  Tingkat:     {doc.metadata.tingkat_peradilan}")
                print(f"  Klasifikasi: {doc.metadata.klasifikasi}")
                print(f"  Pihak:       {doc.metadata.pihak_utama}")
                print(f"  Halaman:     {doc.metadata.total_halaman}")
                print(f"  Bagian:      {len(doc.sections)} sections")
                print(f"  Chunks:      {len(doc.chunks)} context-preserving chunks")
                print(f"  Output MD:   {md_path}")
                print(f"  Output JSON: {json_path}")
                if getattr(args, "index_rag", False):
                    print("  RAG Status:  Indexed into unified SQLite chunks table")
                print()
                return 0

            # Directory batch processing
            pdf_files = sorted(glob.glob(f"{in_path}/**/*.pdf", recursive=True))
            if not pdf_files:
                print(f"\n[-] No PDF files found in: {in_path}\n")
                return 1

            if args.sample and args.sample > 0:
                pdf_files = pdf_files[: args.sample]

            print(f"\n[+] Processing {len(pdf_files)} Putusan PDF documents (workers={args.concurrency})...")
            results = converter.batch_convert(pdf_files, max_workers=args.concurrency)

            total_chunks = sum(len(d.chunks) for d in results)
            total_pages = sum(d.metadata.total_halaman for d in results)

            # Export individual files and consolidated index
            all_chunks = []
            for d in results:
                m_path = out_dir / f"{d.doc_id}.md"
                j_path = out_dir / f"{d.doc_id}_chunks.json"
                converter.export_markdown(d, m_path)
                converter.export_chunks_json(d.chunks, j_path)
                all_chunks.extend(d.chunks)
                if getattr(args, "index_rag", False):
                    app.retriever.index_putusan_document(
                        d,
                        markdown_path=str(m_path),
                        embed=getattr(args, "embed", False),
                    )

            all_chunks_path = out_dir / "all_chunks.json"
            converter.export_chunks_json(all_chunks, all_chunks_path)

            print("\n[+] Batch Putusan Processing Completed:")
            print(f"  - Successfully processed: {len(results)} / {len(pdf_files)} documents")
            print(f"  - Total Pages parsed:    {total_pages:,}")
            print(f"  - Total Semantic Chunks: {total_chunks:,}")
            print(f"  - Output directory:      {out_dir}")
            print(f"  - Consolidated Chunks:   {all_chunks_path}")
            if getattr(args, "index_rag", False):
                print(f"  - RAG Indexing:          {total_chunks:,} chunks indexed into SQLite")
            print()
            return 0

        if cmd == "embed":
            print("\n[+] Generating dense vector embeddings for unembedded chunks...")
            count = app.retriever.embed_all_chunks(batch_size=getattr(args, "batch_size", 64))
            print(f"\n[+] Finished! Generated and stored {count} chunk embeddings.\n")
            return 0

        if cmd == "web-search":
            print(
                f"\n[+] Searching web for: '{args.query}' "
                f"(provider={args.provider}, topic={args.topic}, limit={args.limit})..."
            )
            app.web_search.output_dir = Path(args.output_dir)
            resp = await app.search_web(
                args.query,
                provider=args.provider,
                topic=args.topic,
                limit=args.limit,
                auto_index=not args.no_index,
            )
            print(f"\n[+] Found {len(resp.results)} web results ({resp.response_time}s):")
            for i, r in enumerate(resp.results):
                print(f"\n  [{i + 1}] ({r.provider}) {r.title}")
                print(f"      URL:      {r.url}")
                print(f"      Cite Key: {r.cite_key}")
                snippet = r.content[:150].replace("\n", " ")
                print(f"      Snippet:  {snippet}...")

            if not args.no_index and resp.results:
                print(
                    f"\n[+] Automatically indexed {resp.indexed_documents} documents and "
                    f"{resp.indexed_chunks} semantic chunks into SQLite RAG."
                )
                print(f"    Markdown files saved to: {args.output_dir}/\n")
            else:
                print()
            return 0

        if cmd == "cards":
            sub = getattr(args, "cards_action", None)
            if not sub:
                counts = app.cards.count_cards()
                print("\n=== Literature Review Cards ===")
                print(f"  Total Cards: {counts['total_cards']}")
                for c_name, c_cnt in counts.get("corpus_breakdown", {}).items():
                    print(f"    - {c_name:<12}: {c_cnt}")
                print("\nRun 'research cards --help' to view actions: extract, list, show, edit, export.\n")
                return 0

            if sub == "extract":
                if args.cite_key:
                    print(f"\n[+] Extracting literature review card for: '{args.cite_key}'...")
                    card = app.cards.extract_and_save(args.cite_key, force=args.force)
                    if not card:
                        print(f"[-] Publication '{args.cite_key}' not found in database.\n")
                        return 1
                    print(f"\n[+] Successfully extracted card: [{card.corpus.upper()}] {card.title}")
                    print(f"  Isu Hukum:   {card.legal_issue[:100]}...")
                    print(f"  Dasar/Teori: {card.theory[:100]}...")
                    print(f"  Temuan:      {card.findings[:100]}...")
                    print(f"  Gap:         {card.gap[:100]}...")
                    print(f"  Positioning: {card.positioning[:100]}...\n")
                    return 0

                concurrency = getattr(args, "concurrency", 4)
                print(
                    f"\n[+] Batch extracting literature review cards (corpus={args.corpus}, limit={args.limit}, workers={concurrency})..."
                )
                cards = app.cards.batch_extract(
                    corpus=args.corpus,
                    force=args.force,
                    limit=args.limit,
                    concurrency=concurrency,
                )
                print(f"\n[+] Batch extraction finished: {len(cards)} review cards processed and saved into SQLite.\n")
                return 0

            if sub == "list":
                cards = app.cards.list_cards(corpus=args.corpus, tag=args.tag, query=args.query, limit=args.limit)
                if not cards:
                    print("\n  No matching review cards found in database.\n")
                    return 0

                print(f"\n[+] Found {len(cards)} Literature Review Cards:\n")
                print(f"{'No':<3} | {'Corpus':<10} | {'Tahun':<5} | {'Cite Key':<35} | {'Judul'}")
                print("-" * 90)
                for i, c in enumerate(cards, start=1):
                    yr = str(c.year) if c.year else "—"
                    t = c.title[:38] + ".." if len(c.title) > 40 else c.title
                    ck = c.cite_key[:33] + ".." if len(c.cite_key) > 35 else c.cite_key
                    print(f"{i:<3} | {c.corpus:<10} | {yr:<5} | {ck:<35} | {t}")
                print()
                return 0

            if sub == "show":
                card = app.cards.get_card(args.cite_key)
                if not card:
                    print(
                        f"\n[-] Review card for '{args.cite_key}' not found. "
                        f"Try 'research cards extract --cite-key {args.cite_key}'\n"
                    )
                    return 1
                print("\n" + card.to_markdown_card() + "\n")
                return 0

            if sub == "edit":
                card = app.cards.update_card(
                    args.cite_key,
                    legal_issue=args.issue,
                    theory=args.theory,
                    methodology=args.methodology,
                    findings=args.findings,
                    gap=args.gap,
                    positioning=args.positioning,
                    tags=args.tags,
                    notes=args.notes,
                )
                if not card:
                    print(f"[-] Could not find or create review card for '{args.cite_key}'.\n")
                    return 1
                print(f"\n[+] Review card for '{card.cite_key}' updated successfully.\n")
                return 0

            if sub == "export":
                out_ext = "md" if args.format == "markdown" else args.format
                default_file = f"data/literature_matrix.{out_ext}"
                out_path = Path(args.output or default_file)

                print(f"\n[+] Exporting literature review matrix (format={args.format}, corpus={args.corpus})...")
                content = app.cards.export_matrix(
                    format=args.format,
                    output_path=out_path,
                    corpus=args.corpus,
                    tag=args.tag,
                    include_details=not args.no_details,
                )
                cards_count = len(app.cards.list_cards(corpus=args.corpus, tag=args.tag))
                print(f"[+] Exported {cards_count} review cards -> {out_path} ({len(content):,} bytes)\n")
                return 0

        if cmd == "bib":
            sub = getattr(args, "bib_action", None)
            if not sub:
                print("\n[-] Error: Please specify a bib action: list, show, add, update, delete, import, export.")
                print("    Run 'research bib --help' for details.\n")
                return 1

            if sub == "list":
                records = app.bib.list(
                    corpus=args.corpus,
                    year=args.year,
                    author=args.author,
                    journal=args.journal,
                    query=args.query,
                    limit=args.limit,
                    offset=args.offset,
                )
                if not records:
                    print(f"\n[-] No publications found matching criteria (corpus={args.corpus}, query={args.query or 'none'}).\n")
                    return 0

                print(f"\n[+] Bibliography ({len(records)} entries, style={args.style.upper()}):\n")
                for i, r in enumerate(records, 1):
                    citation = app.bib.format_citation(r, style=args.style, index=i)
                    print(f"[{i}] [{r.cite_key}] ({r.entry_type})")
                    print(f"    {citation}")
                    if args.style not in ("bibtex", "ris", "csl-json"):
                        in_text = app.bib.format_in_text(r, style=args.style, index=i)
                        print(f"    In-text: {in_text}")
                    print()
                return 0

            if sub == "show":
                rec = app.bib.get(args.cite_key)
                if not rec:
                    print(f"\n[-] Publication '{args.cite_key}' not found in database.\n")
                    return 1

                print(f"\n=== Reference: {rec.cite_key} ===")
                print(f"Title:       {rec.title}")
                print(f"Authors:     {', '.join(rec.authors) if rec.authors else 'Anonymous'}")
                print(f"Year:        {rec.year or 'n.d.'}")
                print(f"Type:        {rec.entry_type}")
                print(f"Journal:     {rec.journal or 'N/A'}")
                if rec.volume or rec.number or rec.pages:
                    print(f"Details:     Vol. {rec.volume or '-'}, No. {rec.number or '-'}, pp. {rec.pages or '-'}")
                if rec.doi:
                    print(f"DOI:         {rec.doi}")
                if rec.url:
                    print(f"URL:         {rec.url}")
                print("==================================\n")

                if args.style == "all":
                    styles = ["apa", "ieee", "harvard", "chicago", "chicago-note", "mla", "vancouver", "oscola", "indonesia"]
                    print("--- Formatted Citations (Multi-CSL) ---")
                    for st in styles:
                        cite_str = app.bib.format_citation(rec, style=st)
                        in_text = app.bib.format_in_text(rec, style=st)
                        print(f"[{st.upper(): <12}] {cite_str}")
                        print(f"  └ In-text:   {in_text}\n")

                    print("--- Raw BibTeX ---")
                    print(app.bib.format_citation(rec, style="bibtex"))
                    print()
                else:
                    cite_str = app.bib.format_citation(rec, style=args.style)
                    print(f"[{args.style.upper()}] {cite_str}")
                    if args.in_text:
                        in_text = app.bib.format_in_text(rec, style=args.style)
                        print(f"In-text:     {in_text}")
                    print()
                return 0

            if sub == "add":
                authors_list: list[str] = []
                if args.author:
                    for a_arg in args.author:
                        for a_item in a_arg.split(";"):
                            if a_item.strip():
                                authors_list.append(a_item.strip())

                rec = PublicationRecord(
                    cite_key=args.cite_key or "",
                    entry_type=args.entry_type,
                    title=args.title,
                    authors=authors_list,
                    journal=args.journal,
                    year=args.year,
                    volume=args.volume,
                    number=args.issue,
                    pages=args.pages,
                    doi=args.doi,
                    url=args.url,
                    abstract=args.abstract,
                    sources=["manual_cli_add"],
                )
                saved = app.bib.create(rec)
                print(f"\n[+] Successfully added reference: `{saved.cite_key}`")
                print(f"    APA: {app.bib.format_citation(saved, style='apa')}\n")
                return 0

            if sub == "update":
                updates: dict[str, Any] = {}
                if args.title:
                    updates["title"] = args.title
                if args.year:
                    updates["year"] = args.year
                if args.journal:
                    updates["journal"] = args.journal
                if args.volume:
                    updates["volume"] = args.volume
                if args.issue:
                    updates["number"] = args.issue
                if args.pages:
                    updates["pages"] = args.pages
                if args.doi:
                    updates["doi"] = args.doi
                if args.url:
                    updates["url"] = args.url
                if args.abstract:
                    updates["abstract"] = args.abstract
                if args.author:
                    authors_list = []
                    for a_arg in args.author:
                        for a_item in a_arg.split(";"):
                            if a_item.strip():
                                authors_list.append(a_item.strip())
                    updates["authors"] = authors_list

                if not updates:
                    print("\n[-] Error: No fields specified to update.\n")
                    return 1

                updated = app.bib.update(args.cite_key, **updates)
                if not updated:
                    print(f"\n[-] Error: Reference '{args.cite_key}' not found in database.\n")
                    return 1

                print(f"\n[+] Reference '{args.cite_key}' updated successfully:")
                print(f"    APA: {app.bib.format_citation(updated, style='apa')}\n")
                return 0

            if sub == "delete":
                existing = app.bib.get(args.cite_key)
                if not existing:
                    print(f"\n[-] Error: Reference '{args.cite_key}' not found in database.\n")
                    return 1

                if not args.yes:
                    confirm = input(f"Are you sure you want to delete '{args.cite_key}'? [y/N]: ").strip().lower()
                    if confirm not in ("y", "yes"):
                        print("[*] Aborted.")
                        return 0

                deleted = app.bib.delete(args.cite_key)
                if deleted:
                    print(f"\n[+] Reference '{args.cite_key}' deleted from database and FTS indexes.\n")
                else:
                    print(f"\n[-] Failed to delete '{args.cite_key}'.\n")
                return 0

            if sub == "import":
                src = args.source.strip()
                fmt = args.format

                # Auto-detect format if requested
                if fmt == "auto":
                    if src.startswith("10.") or "doi.org/" in src:
                        fmt = "doi"
                    elif src.endswith(".ris"):
                        fmt = "ris"
                    elif src.endswith(".json"):
                        fmt = "csl-json"
                    elif src.endswith(".bib") or "@" in src:
                        fmt = "bibtex"
                    else:
                        fmt = "bibtex"

                print(f"\n[+] Importing references (format={fmt}, source={src})...")
                if fmt == "doi":
                    rec = app.bib.import_doi(src)
                    if rec:
                        print(f"[+] Successfully imported DOI: `{rec.cite_key}` - {rec.title}")
                    else:
                        print(f"[-] Failed to import DOI '{src}'.")
                elif fmt == "bibtex":
                    imported = app.bib.import_bibtex(src)
                    print(f"[+] Successfully imported {len(imported)} references from BibTeX.")
                elif fmt == "csl-json":
                    imported = app.bib.import_csl_json(src)
                    print(f"[+] Successfully imported {len(imported)} references from CSL-JSON.")
                elif fmt == "ris":
                    imported = app.bib.import_ris(src)
                    print(f"[+] Successfully imported {len(imported)} references from RIS.")
                print()
                return 0

            if sub == "export":
                print(f"\n[+] Exporting bibliography (style={args.style}, format={args.format}, corpus={args.corpus})...")
                out_path = app.bib.export_bibliography(
                    args.output,
                    style=args.style,
                    output_format=args.format,
                    corpus=args.corpus,
                    query=args.query,
                    limit=args.limit,
                )
                print(f"[+] Export complete -> {out_path}\n")
                return 0

    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.warning("\n[!] Execution interrupted by user (Ctrl+C). Performing graceful cleanup...")
        return 130
    finally:
        try:
            await asyncio.shield(app.close())
        except Exception as exc:  # noqa: BLE001
            logger.debug("Error during app cleanup: {}", exc)

    return 0


def main() -> None:
    """CLI entry point with robust keyboard interrupt and termination handling."""
    parser = build_parser()
    args = parser.parse_args()
    log_file = setup_logging(
        verbose=args.verbose,
        log_dir=getattr(args, "log_dir", "logs"),
        enable_file_logging=not getattr(args, "no_log_file", False),
    )
    cmd_args = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    logger.debug("Executing CLI command: research {}", cmd_args)
    if log_file:
        logger.debug("Run log path: {}", log_file)

    try:
        code = asyncio.run(_async_main(args))
    except KeyboardInterrupt:
        logger.warning("\n[!] Process terminated by user.")
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Fatal error during execution: {}", exc)
        sys.exit(1)
    else:
        sys.exit(code)


if __name__ == "__main__":
    main()
