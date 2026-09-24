from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from loguru import logger

from research.app import ResearchApp
from research.cli.parser import build_parser
from research.pipeline.models import PipelineConfig


def _setup_logging(verbose: bool) -> None:
    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )


async def _async_main(args: Any) -> int:
    app = ResearchApp(db_path=args.db, download_dir=args.downloads)
    cmd = args.command

    try:
        if cmd == "stats":
            stats = app.db.get_stats()
            statuses = app.db.get_status_summary()
            print("\n=== Research Database Status ===")
            print(f"  Database path:       {args.db}")
            print(f"  Total Publications:  {stats['total_publications']}")
            print(f"  Downloaded PDFs:     {stats['downloaded']}")
            print(f"  Converted Documents: {stats['converted']}")
            print(f"  RAG Semantic Chunks: {stats['total_chunks']}")
            print(f"  Dense Embeddings:    {stats.get('total_embeddings', 0)}")
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
                print("\n[-] Error: Please specify a search query or a --bib seed file.\n")
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
                download=not args.no_download,
                convert=not args.no_convert,
                index_rag=not args.no_rag,
            )
            desc = f"query='{args.query}'" if args.query else ""
            if args.bib:
                desc += f" (bib seed='{args.bib}')" if desc else f"bib seed='{args.bib}'"
            print(f"\n[+] Executing end-to-end research pipeline for: {desc}...")
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
            print("\n[+] Concurrently downloading open-access papers...")
            stats = await app.download_papers(cite_keys=c_keys)
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

            print(f"\n[+] Converting {len(files)} PDF document(s) to normalized Markdown...")
            out_dir = Path(args.output_dir) if args.output_dir else None

            converted_count = 0
            chunks_count = 0
            for pdf_file in files:
                out_md = (out_dir / pdf_file.with_suffix(".md").name) if out_dir else pdf_file.with_suffix(".md")
                conv_doc = app.convert_pdf(pdf_file, output_md=out_md)
                converted_count += 1
                cite_key = pdf_file.stem
                if args.index_rag:
                    chunks = app.retriever.index_document(conv_doc, cite_key=cite_key)
                    chunks_count += len(chunks)
                print(f"  - Converted {pdf_file.name} -> {out_md.name} ({conv_doc.total_pages} pages)")

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

    finally:
        await app.close()

    return 0


def main() -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()
    _setup_logging(args.verbose)
    code = asyncio.run(_async_main(args))
    sys.exit(code)


if __name__ == "__main__":
    main()
