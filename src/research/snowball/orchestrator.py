from __future__ import annotations

import asyncio
from pathlib import Path

from loguru import logger

from research.bibtex.parser import parse_bib_files
from research.db.manager import DatabaseManager
from research.db.models import PublicationRecord
from research.snowball.models import SnowballConfig, SnowballResult
from research.snowball.openalex import OpenAlexClient


class SnowballOrchestrator:
    """Orchestrates citation graph snowballing, automated metadata enrichment, and database indexing."""

    def __init__(
        self,
        db: DatabaseManager,
        *,
        config: SnowballConfig | None = None,
    ) -> None:
        self.db = db
        self.config = config or SnowballConfig()

    async def snowball_record(
        self,
        record: PublicationRecord,
        *,
        client: OpenAlexClient | None = None,
    ) -> SnowballResult:
        """Execute forward and/or backward snowballing for a single seed publication."""
        result = SnowballResult(
            seed_cite_key=record.cite_key,
            seed_title=record.title,
        )

        should_close = False
        oa_client = client
        if oa_client is None:
            oa_client = OpenAlexClient(email=self.config.email, timeout=self.config.timeout)
            should_close = True

        try:
            logger.info(f"Snowballing seed: {record.cite_key} - '{record.title[:45]}...'")

            # 1. Resolve seed work in OpenAlex
            seed_work = await oa_client.find_work(doi=record.doi, title=record.title)
            if not seed_work:
                logger.warning(f"Could not find seed in OpenAlex: {record.cite_key}")
                return result

            # Enrich seed record if OpenAlex provides direct OA PDF link
            best_oa_pdf = (seed_work.get("best_oa_location") or {}).get("pdf_url")
            if not record.pdf_url and best_oa_pdf:
                self.db.update(record.cite_key, pdf_url=best_oa_pdf)
                record.pdf_url = best_oa_pdf

            raw_discovered: list[tuple[dict, str]] = []

            # 2. Forward snowballing (papers citing this seed)
            if self.config.direction in ("both", "forward"):
                citing = await oa_client.fetch_citing_works(
                    seed_work["id"],
                    limit=self.config.limit_forward,
                )
                result.forward_count = len(citing)
                for w in citing:
                    raw_discovered.append((w, "forward"))

            # 3. Backward snowballing (references cited in seed's bibliography)
            if self.config.direction in ("both", "backward"):
                referenced_ids = seed_work.get("referenced_works", [])
                if referenced_ids:
                    referenced = await oa_client.fetch_referenced_works(
                        referenced_ids,
                        limit=self.config.limit_backward,
                    )
                    result.backward_count = len(referenced)
                    for w in referenced:
                        raw_discovered.append((w, "backward"))

            # 4. Transform, auto-enrich, and index into DB
            for work, relation in raw_discovered:
                discovered_rec = oa_client.work_to_record(
                    work,
                    seed_cite_key=record.cite_key,
                    relation=relation,
                )

                # Check if already present in DB by cite_key or DOI
                existing: PublicationRecord | None = self.db.get(discovered_rec.cite_key)
                if not existing and discovered_rec.doi:
                    # Look up by DOI
                    candidates = self.db.list(limit=500)
                    for c in candidates:
                        if c.doi and c.doi.lower() == discovered_rec.doi.lower():
                            existing = c
                            break

                source_tag = f"snowball:{relation}:{record.cite_key}"

                if existing:
                    # Update sources on existing record
                    if source_tag not in existing.sources:
                        new_sources = list(existing.sources) + [source_tag]
                        self.db.update(existing.cite_key, sources=new_sources)
                    result.discovered_records.append(existing)
                else:
                    # Index newly discovered publication record into database
                    self.db.create(discovered_rec)
                    result.discovered_records.append(discovered_rec)
                    result.newly_indexed_count += 1

            logger.success(
                f"Completed snowball for {record.cite_key}: "
                f"+{result.forward_count} citing, +{result.backward_count} referenced, "
                f"{result.newly_indexed_count} new papers indexed into DB."
            )

        finally:
            if should_close and oa_client is not None:
                await oa_client.close()

        return result

    async def snowball_records(
        self,
        records: list[PublicationRecord],
    ) -> list[SnowballResult]:
        """Execute snowballing across multiple seed records with concurrency control."""
        sem = asyncio.Semaphore(self.config.concurrency)
        results: list[SnowballResult] = []

        async with OpenAlexClient(email=self.config.email, timeout=self.config.timeout) as client:

            async def _worker(rec: PublicationRecord) -> SnowballResult:
                async with sem:
                    return await self.snowball_record(rec, client=client)

            tasks = [_worker(r) for r in records]
            gathered = await asyncio.gather(*tasks, return_exceptions=True)

            for item in gathered:
                if isinstance(item, SnowballResult):
                    results.append(item)
                elif isinstance(item, Exception):
                    logger.error(f"Snowball task failed: {item}")

        return results

    async def snowball_from_bib(
        self,
        bib_paths: list[str | Path] | list[str] | list[Path] | str | Path,
        *,
        deduplicate_seeds: bool = True,
        max_seeds: int | None = None,
    ) -> list[SnowballResult]:
        """Orchestrate end-to-end snowballing starting from .bib file(s)."""
        paths: list[Path]
        if isinstance(bib_paths, (str, Path)):
            paths = [Path(bib_paths)]
        else:
            paths = [Path(p) for p in bib_paths]

        # 1. Parse .bib files
        bib_entries = parse_bib_files(paths, deduplicate=deduplicate_seeds)
        logger.info(f"Loaded {len(bib_entries)} seed entries from {[p.name for p in paths]}")

        # 2. Index seeds into DB if not present
        seed_records: list[PublicationRecord] = []
        for e in bib_entries:
            rec = self.db.get(e.cite_key)
            if not rec:
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
                self.db.create(rec)
            seed_records.append(rec)

        if max_seeds is not None:
            seed_records = seed_records[:max_seeds]

        # 3. Execute snowballing
        return await self.snowball_records(seed_records)

    def snowball_from_bib_sync(
        self,
        bib_paths: list[str | Path] | list[str] | list[Path] | str | Path,
        *,
        deduplicate_seeds: bool = True,
        max_seeds: int | None = None,
    ) -> list[SnowballResult]:
        """Synchronous wrapper for snowball_from_bib."""
        return asyncio.run(
            self.snowball_from_bib(
                bib_paths=bib_paths,
                deduplicate_seeds=deduplicate_seeds,
                max_seeds=max_seeds,
            )
        )
