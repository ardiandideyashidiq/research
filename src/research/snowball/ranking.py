"""Relevance ranking for snowball results.

Scores raw OpenAlex work dicts against a free-text query so that wide snowball
fetches can be capped to a small, high-signal shortlist before any download,
conversion, or review work is spent on them.

Scoring is intentionally simple and deterministic: weighted term overlap over
title, concepts, and reconstructed abstract, with small tie-breakers for
open-access availability, work type, recency, and citation impact.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

from research.snowball.openalex import reconstruct_abstract

# Field weights: a query term in the title is the strongest signal, an OpenAlex
# concept is a curated topical label (next strongest), the abstract is prose.
_TITLE_WEIGHT = 3.0
_CONCEPT_WEIGHT = 2.0
_ABSTRACT_WEIGHT = 1.0

# Tie-breaker contributions are small so they can order a shortlist but can
# never outrank a real term-overlap difference.
_OA_BONUS = 0.15
_ARTICLE_BONUS = 0.10
_RECENCY_BONUS = 0.15
_CITATION_BONUS = 0.20

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Very common words add noise rather than signal in a topical query.
_STOPWORDS = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "by", "dalam", "dan",
        "for", "from", "in", "is", "it", "of", "on", "or", "the", "to",
        "yang", "dengan", "untuk", "pada", "adalah",
    }
)


@dataclass(frozen=True)
class RelevanceScore:
    """Relevance of one OpenAlex work to a query."""

    score: float
    matched_terms: list[str] = field(default_factory=list)
    title: str = ""
    doi: str | None = None
    year: int | None = None
    cited_by_count: int = 0
    has_oa_pdf: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "matched_terms": self.matched_terms,
            "title": self.title,
            "doi": self.doi,
            "year": self.year,
            "cited_by_count": self.cited_by_count,
            "has_oa_pdf": self.has_oa_pdf,
        }


def tokenize(text: str | None) -> set[str]:
    """Lowercase alphanumeric token set with stopwords removed."""
    if not text:
        return set()
    return {t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS and len(t) > 1}


def _score_text(text: str | None, terms: set[str], weight: float) -> tuple[float, set[str]]:
    tokens = tokenize(text)
    matched = tokens & terms
    if not tokens or not matched:
        return 0.0, set()
    # Normalize by the smaller side so a long abstract cannot outweigh a
    # precise title match purely through repetition.
    return weight * (len(matched) / max(len(terms), 1)), matched


def score_work(work: dict[str, Any], query_terms: set[str]) -> RelevanceScore:
    """Score one raw OpenAlex work dict against pre-tokenized query terms."""
    if not query_terms:
        return RelevanceScore(score=0.0)

    title = work.get("title") or work.get("display_name") or ""
    year = work.get("publication_year")
    cited = work.get("cited_by_count")
    concepts = " ".join(
        c.get("display_name", "") for c in (work.get("concepts") or []) if c.get("display_name")
    )
    abstract = reconstruct_abstract(work.get("abstract_inverted_index")) or ""

    title_score, matched = _score_text(title, query_terms, _TITLE_WEIGHT)
    concept_score, concept_matched = _score_text(concepts, query_terms, _CONCEPT_WEIGHT)
    abstract_score, abstract_matched = _score_text(abstract, query_terms, _ABSTRACT_WEIGHT)

    matched_terms = sorted(matched | concept_matched | abstract_matched)

    # A paper that matches none of the query terms is irrelevant regardless of
    # how well-cited or recent it is, so it must not collect tie-breaker
    # bonuses. Otherwise min_score filtering silently lets unrelated work
    # through on citation count alone.
    if not matched_terms:
        return RelevanceScore(
            score=0.0,
            matched_terms=[],
            title=title,
            doi=work.get("doi"),
            year=year if isinstance(year, int) else None,
            cited_by_count=cited if isinstance(cited, int) else 0,
            has_oa_pdf=bool((work.get("best_oa_location") or {}).get("pdf_url")),
        )

    # Coverage of the query: the single most important signal. A paper matching
    # every query term outranks one matching a single term five times.
    coverage = len(matched_terms) / len(query_terms)
    total = (0.6 * coverage) + (title_score + concept_score + abstract_score) * 0.2

    best_oa = work.get("best_oa_location") or {}
    primary = work.get("primary_location") or {}
    has_oa_pdf = bool(
        best_oa.get("pdf_url") or primary.get("pdf_url") or best_oa.get("is_oa")
    )
    if has_oa_pdf:
        total += _OA_BONUS
    if work.get("type") == "article":
        total += _ARTICLE_BONUS

    if isinstance(year, int):
        # 0 at 2000, ramping to the bonus by 2025, so recent work is preferred
        # without erasing older foundational papers.
        recency = min(max((year - 2000) / 25.0, 0.0), 1.0)
        total += _RECENCY_BONUS * recency

    if isinstance(cited, int) and cited > 0:
        # Log damping: 1 citation is worth little, 1000 is worth little more.
        total += _CITATION_BONUS * (math.log10(cited) / 4.0)

    return RelevanceScore(
        score=total,
        matched_terms=matched_terms,
        title=title,
        doi=work.get("doi"),
        year=year if isinstance(year, int) else None,
        cited_by_count=cited if isinstance(cited, int) else 0,
        has_oa_pdf=has_oa_pdf,
    )


def rank_works(
    works: list[dict[str, Any]],
    *,
    query: str,
    top_k: int = 10,
    min_score: float = 0.0,
) -> tuple[list[RelevanceScore], int, int]:
    """Score, filter, and cap a list of raw OpenAlex works.

    Returns ``(kept, ranked_out_count, dropped_irrelevant_count)`` where
    ``kept`` is sorted by descending score and capped at ``top_k``; the two
    counts report how many were excluded by the cap and by ``min_score``.
    """
    if not query.strip():
        return ([RelevanceScore(score=0.0) for _ in works], 0, 0)

    terms = tokenize(query)
    if not terms:
        return ([RelevanceScore(score=0.0) for _ in works], 0, 0)

    scored = [score_work(w, terms) for w in works]
    # Deterministic ordering: score desc, then more citations, then title.
    scored.sort(key=lambda s: (-s.score, -s.cited_by_count, s.title))

    passing = [s for s in scored if s.score >= min_score]
    dropped_irrelevant = len(scored) - len(passing)
    kept = passing[:top_k]
    ranked_out = len(passing) - len(kept)
    return kept, ranked_out, dropped_irrelevant
