"""Literature review run orchestration.

Takes a .bib export, deduplicates it, expands it through a relevance-capped
snowball, resolves open-access PDF links via Unpaywall, and writes a manifest
plus one review packet per paper.

The packets are deterministic inputs for per-paper subagent reviews — this
module never writes the reviews itself; it only prepares what they need.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger

from research.app import ResearchApp
from research.snowball.ranking import score_work, tokenize
from research.unpaywall.client import UnpaywallClient


@dataclass
class ReviewPaper:
    """One paper queued for review, with everything a subagent needs."""

    cite_key: str
    title: str
    doi: str | None
    year: int | None
    venue: str | None
    label: str  # FULL-TEXT | ABSTRACT | METADATA
    origin: str  # seed | snowball
    relevance_score: float = 0.0
    matched_terms: list[str] = field(default_factory=list)
    pdf_url: str | None = None
    pdf_path: str | None = None
    md_path: str | None = None
    abstract: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewRunResult:
    out_dir: str
    seed_count: int
    seeds_expanded: int = 0
    papers: list[ReviewPaper] = field(default_factory=list)
    ranked_out: int = 0
    dropped_irrelevant: int = 0
    unpaywall_resolved: int = 0

    @property
    def full_text_count(self) -> int:
        return sum(1 for p in self.papers if p.label == "FULL-TEXT")

    def summary(self) -> str:
        return "\n".join(
            [
                f"Review run written to {self.out_dir}",
                f"  Unique seeds:         {self.seed_count}",
                f"  Seeds expanded:       {self.seeds_expanded}",
                f"  Papers queued:        {len(self.papers)}",
                f"  Full-text available:  {self.full_text_count}",
                (
                    "  Abstract-only:        "
                    f"{sum(1 for p in self.papers if p.label == 'ABSTRACT')}"
                ),
                (
                    "  Metadata-only:        "
                    f"{sum(1 for p in self.papers if p.label == 'METADATA')}"
                ),
                f"  Unpaywall resolved:   {self.unpaywall_resolved}",
                f"  Ranked out over cap:  {self.ranked_out}",
                f"  Dropped irrelevant:   {self.dropped_irrelevant}",
            ]
        )


def _classify(rec: Any, markdown_dir: Path) -> tuple[str, str | None, str | None]:
    """Return (label, markdown_path, pdf_path) for a record from disk state."""
    pdf_path = None
    if rec.download_status == "downloaded" and rec.download_path:
        candidate = Path(rec.download_path)
        if candidate.exists():
            pdf_path = str(candidate)
            md = markdown_dir / f"{rec.cite_key}.md"
            if md.exists():
                return "FULL-TEXT", str(md), pdf_path
    if (rec.abstract or "").strip():
        return "ABSTRACT", None, pdf_path
    return "METADATA", None, pdf_path


async def run_review(
    app: ResearchApp,
    *,
    bib_path: str | Path,
    out_dir: str | Path,
    relevance_query: str,
    relevance_top_k: int = 10,
    seeds: int = 3,
    snowball_limit: int = 20,
    direction: str = "both",
    resolve_unpaywall: bool = True,
    markdown_dir: str | Path = "data/markdown",
) -> ReviewRunResult:
    """Run bib -> dedup -> ranked snowball -> unpaywall -> manifest.

    ``seeds`` controls how many of the ingested seeds are expanded through the
    citation graph (the strongest by relevance first); every seed is still
    queued for review, but only ``seeds`` of them cost snowball calls.
    """
    out = Path(out_dir)
    (out / "packets").mkdir(parents=True, exist_ok=True)
    md_dir = Path(markdown_dir)

    # 1. Ingest + dedup (app.load_bib_files uses parse_bib_files(deduplicate=True)).
    indexed = app.load_bib_files(bib_path, deduplicate=True)
    if indexed == 0:
        msg = f"No BibTeX entries ingested from {bib_path}"
        raise ValueError(msg)

    result = ReviewRunResult(out_dir=str(out), seed_count=indexed)
    terms = tokenize(relevance_query)

    # 2. Queue the records that came from THIS bib run. Reading the whole
    #    database here would sweep in unrelated prior literature.
    from research.bibtex.parser import parse_bib_files as _parse

    seed_keys: list[str] = []
    for entry in _parse(bib_path, deduplicate=True):
        # find_existing resolves by cite_key, then DOI, then URL/title, so a
        # record ingested under a regenerated key is still matched.
        rec = app.db.find_existing({"cite_key": entry.cite_key, "doi": entry.doi})
        if rec is not None:
            seed_keys.append(rec.cite_key)

    seed_papers: list[ReviewPaper] = []
    for rec in [app.db.get(k) for k in seed_keys]:
        if rec is None:
            continue
        score = score_work(
            {
                "title": rec.title,
                "type": rec.entry_type,
                "publication_year": rec.year,
                "cited_by_count": 0,
                "concepts": [],
            },
            terms,
        )
        label, md, pdf = _classify(rec, md_dir)
        seed_papers.append(
            ReviewPaper(
                cite_key=rec.cite_key,
                title=rec.title,
                doi=rec.doi,
                year=rec.year,
                venue=rec.journal,
                label=label,
                origin="seed",
                relevance_score=score.score,
                matched_terms=score.matched_terms,
                pdf_url=rec.pdf_url,
                pdf_path=pdf,
                md_path=md,
                abstract=rec.abstract,
            )
        )

    # 3. Relevance-capped snowball over the strongest seeds.
    ranked_seeds = sorted(seed_papers, key=lambda p: -p.relevance_score)[:seeds]
    result.seeds_expanded = len(ranked_seeds)
    seen_keys = {p.cite_key for p in seed_papers}
    seen_dois = {p.doi.lower() for p in seed_papers if p.doi}
    snowball_papers: list[ReviewPaper] = []

    for seed in ranked_seeds:
        if not app.db.get(seed.cite_key):
            continue
        try:
            res = await app.run_snowball(
                seed.cite_key,
                direction=direction,
                limit_forward=snowball_limit,
                limit_backward=snowball_limit,
                relevance_query=relevance_query,
                relevance_top_k=relevance_top_k,
            )
        except Exception as e:  # noqa: BLE001 - one bad seed must not kill the run
            logger.warning("Snowball failed for seed {}: {}", seed.cite_key, e)
            continue
        result.ranked_out += res.ranked_out_count
        result.dropped_irrelevant += res.dropped_irrelevant_count
        for rec in res.discovered_records:
            doi_key = (rec.doi or "").lower()
            if rec.cite_key in seen_keys or (doi_key and doi_key in seen_dois):
                continue
            seen_keys.add(rec.cite_key)
            if doi_key:
                seen_dois.add(doi_key)
            label, md, pdf = _classify(rec, md_dir)
            snowball_papers.append(
                ReviewPaper(
                    cite_key=rec.cite_key,
                    title=rec.title,
                    doi=rec.doi,
                    year=rec.year,
                    venue=rec.journal,
                    label=label,
                    origin="snowball",
                    pdf_url=rec.pdf_url,
                    pdf_path=pdf,
                    md_path=md,
                    abstract=rec.abstract,
                )
            )

    result.papers = seed_papers + snowball_papers

    # 4. Unpaywall resolve for papers that still lack a PDF link.
    if resolve_unpaywall:
        client = UnpaywallClient(timeout=12.0, cache=app.cache)
        try:
            for paper in result.papers:
                if paper.pdf_url or not paper.doi:
                    continue
                try:
                    url = await client.get_best_pdf_url(paper.doi)
                except Exception as e:  # noqa: BLE001
                    logger.debug("Unpaywall failed for {}: {}", paper.doi, e)
                    continue
                if url:
                    paper.pdf_url = url
                    result.unpaywall_resolved += 1
                    rec = app.db.get(paper.cite_key)
                    if rec is not None:
                        app.db.update(rec.cite_key, pdf_url=url)
        finally:
            await client.close()

    # 5. Write per-paper packets + manifest for subagent review.
    manifest: list[dict[str, Any]] = []
    for paper in result.papers:
        packet = {
            "instructions": (
                "Write a comprehensive literature review card following "
                "template-analisis-paper.md sections I-X, including the required "
                "enrichment blocks: 2b the author's analytical technique, 2c the "
                "statutes analysed with [VERBATIM]/[RUJUKAN]/[TAK DISEBUT] status, "
                "and 2d critical analysis. When label is FULL-TEXT, read the "
                "markdown at md_path. Never fabricate: anything not verifiable in "
                "the provided source must be written as '—'."
            ),
            "paper": paper.to_dict(),
        }
        (out / "packets" / f"{paper.cite_key}.json").write_text(
            json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        manifest.append(paper.to_dict())

    (out / "manifest.json").write_text(
        json.dumps(
            {
                "relevance_query": relevance_query,
                "relevance_top_k": relevance_top_k,
                "seeds_expanded": result.seeds_expanded,
                "paper_count": len(manifest),
                "papers": manifest,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return result
