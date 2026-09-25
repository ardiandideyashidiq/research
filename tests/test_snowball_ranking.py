"""Unit test for snowball relevance ranking.

Run: uv run python tests/test_snowball_ranking.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from research.snowball.ranking import rank_works, score_work, tokenize


def _work(
    title: str,
    *,
    year: int = 2023,
    concepts: list[str] | None = None,
    cited: int = 0,
    oa: bool = False,
    doi: str | None = None,
) -> dict:
    return {
        "title": title,
        "display_name": title,
        "publication_year": year,
        "type": "article",
        "cited_by_count": cited,
        "concepts": [{"display_name": c} for c in (concepts or [])],
        "best_oa_location": {"pdf_url": "http://x/y.pdf"} if oa else {},
        "doi": doi,
    }


def test_tokenize_drops_stopwords() -> None:
    tokens = tokenize("Kecerdasan Buatan dan Martabat Manusia yang di dalam")
    assert "kecerdasan" in tokens
    assert "martabat" in tokens
    assert "yang" not in tokens
    assert "dan" not in tokens
    print("[PASS] tokenize removes stopwords")


def test_relevant_beats_irrelevant() -> None:
    query = tokenize("kecerdasan buatan martabat manusia")
    relevant = score_work(
        _work("Kecerdasan Buatan dan Martabat Manusia dalam Etika", cited=5),
        query,
    )
    irrelevant = score_work(
        _work("Quantum Error Correcting Codes for beginners", year=2010, cited=900),
        query,
    )
    assert relevant.score > irrelevant.score
    assert "kecerdasan" in relevant.matched_terms
    print(f"[PASS] relevant {relevant.score:.3f} > irrelevant {irrelevant.score:.3f}")


def test_title_match_outranks_abstract_only() -> None:
    query = tokenize("kecerdasan buatan martabat")
    title_hit = score_work(_work("Martabat Manusia dan Kecerdasan Buatan"), query)
    abstract_only = score_work(_work("Etika burdensome technologies", year=2023), query)
    assert title_hit.score > abstract_only.score
    print("[PASS] title match outranks unrelated title")


def test_rank_caps_and_reports_counts() -> None:
    works = [_work(f"Article {i} tentang kecerdasan buatan dan martabat", doi=f"10.1/{i}") for i in range(15)]
    works.append(_work("Quantum computing hardware", doi="10.9/99", year=2010, cited=5000))
    kept, ranked_out, dropped = rank_works(
        works, query="kecerdasan buatan martabat manusia", top_k=10, min_score=0.05
    )
    assert len(kept) == 10, f"expected cap 10, got {len(kept)}"
    assert ranked_out > 0, "expected some works ranked out by the cap"
    assert dropped >= 1, "expected the clearly irrelevant work to be dropped"
    # Ordering must be descending by score.
    scores = [s.score for s in kept]
    assert scores == sorted(scores, reverse=True)
    print(f"[PASS] rank_works kept={len(kept)} ranked_out={ranked_out} dropped={dropped}")


def test_empty_query_is_pass_through() -> None:
    works = [_work("A"), _work("B")]
    kept, ranked_out, dropped = rank_works(works, query="", top_k=10)
    assert len(kept) == 2
    assert ranked_out == 0 and dropped == 0
    print("[PASS] empty query passes all works through")


def main() -> None:
    test_tokenize_drops_stopwords()
    test_relevant_beats_irrelevant()
    test_title_match_outranks_abstract_only()
    test_rank_caps_and_reports_counts()
    test_empty_query_is_pass_through()
    print("\nAll snowball ranking tests passed.")


if __name__ == "__main__":
    main()
