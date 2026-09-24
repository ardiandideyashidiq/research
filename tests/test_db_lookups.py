from __future__ import annotations

import tempfile
from pathlib import Path

from research.db.manager import DatabaseManager
from research.db.models import PublicationRecord


def test_db_indexed_lookups_and_find_existing() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_lookups.sqlite"
        db = DatabaseManager(db_path)

        rec = PublicationRecord(
            cite_key="vaswani2017attention",
            title="Attention Is All You Need",
            authors=["Vaswani, Ashish", "Shazeer, Noam"],
            year=2017,
            doi="10.5555/3295222.3295349",
            url="https://arxiv.org/abs/1706.03762",
            pdf_url="https://arxiv.org/pdf/1706.03762.pdf",
            file_hash="abc123hash",
        )
        db.create(rec)

        # 1. get_by_doi (case-insensitive)
        found_doi = db.get_by_doi("10.5555/3295222.3295349")
        assert found_doi is not None
        assert found_doi.cite_key == "vaswani2017attention"

        found_doi_upper = db.get_by_doi("10.5555/3295222.3295349".upper())
        assert found_doi_upper is not None
        assert found_doi_upper.cite_key == "vaswani2017attention"

        # 2. get_by_url
        found_url = db.get_by_url("https://arxiv.org/abs/1706.03762")
        assert found_url is not None
        assert found_url.cite_key == "vaswani2017attention"

        # 3. get_by_pdf_url
        found_pdf = db.get_by_pdf_url("https://arxiv.org/pdf/1706.03762.pdf")
        assert found_pdf is not None
        assert found_pdf.cite_key == "vaswani2017attention"

        # 4. get_by_file_hash
        found_hash = db.get_by_file_hash("abc123hash")
        assert found_hash is not None
        assert found_hash.cite_key == "vaswani2017attention"

        # 5. find_existing by cite_key
        assert db.find_existing({"cite_key": "vaswani2017attention"}) is not None

        # 6. find_existing by DOI under a different cite_key
        assert db.find_existing({
            "cite_key": "different_key_2017",
            "doi": "10.5555/3295222.3295349",
        }) is not None

        # 7. find_existing by title and year without cite_key or DOI
        assert db.find_existing({
            "title": "  Attention Is All You Need  ",
            "year": 2017,
        }) is not None

        # 8. Non-existent record
        assert db.find_existing({
            "title": "Unrelated Quantum Mechanics",
            "year": 1920,
        }) is None

        db.close()
    print("test_db_indexed_lookups_and_find_existing passed!")


if __name__ == "__main__":
    test_db_indexed_lookups_and_find_existing()
