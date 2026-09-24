"""Test BibTeX directory ingestion and expansion across whole directories."""

from __future__ import annotations

import tempfile
from pathlib import Path

from research.app import ResearchApp
from research.bibtex.parser import expand_bib_paths, parse_bib_files
from research.pipeline.models import PipelineConfig


def test_expand_bib_paths_single_and_directory() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        sub = root / "subdir"
        sub.mkdir()

        f1 = root / "first.bib"
        f2 = root / "second.bib"
        f3 = sub / "nested.bib"
        txt = root / "notes.txt"

        f1.write_text("@article{key1, title={Paper One}}\n", encoding="utf-8")
        f2.write_text("@article{key2, title={Paper Two}}\n", encoding="utf-8")
        f3.write_text("@article{key3, title={Paper Three}}\n", encoding="utf-8")
        txt.write_text("Not a bib file", encoding="utf-8")

        # 1. Expand single file
        single = expand_bib_paths(f1)
        assert len(single) == 1
        assert single[0].resolve() == f1.resolve()

        # 2. Expand directory (recursive)
        expanded = expand_bib_paths(root, recursive=True)
        assert len(expanded) == 3
        expanded_names = {p.name for p in expanded}
        assert expanded_names == {"first.bib", "second.bib", "nested.bib"}

        # 3. Expand directory (non-recursive)
        non_rec = expand_bib_paths(root, recursive=False)
        assert len(non_rec) == 2
        assert {p.name for p in non_rec} == {"first.bib", "second.bib"}

        # 4. Mixed input (file + dir)
        mixed = expand_bib_paths([f1, sub])
        assert len(mixed) == 2
        assert {p.name for p in mixed} == {"first.bib", "nested.bib"}


def test_parse_bib_files_with_directory() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        f1 = root / "alpha.bib"
        f2 = root / "beta.bib"

        f1.write_text("@article{keyA, title={Title A}, year={2023}}\n", encoding="utf-8")
        f2.write_text("@article{keyB, title={Title B}, year={2024}}\n@article{keyA, title={Title A Dupe}, year={2023}}\n", encoding="utf-8")

        # Parse directory directly
        entries = parse_bib_files(root, deduplicate=True)
        assert len(entries) == 2
        keys = {e.cite_key for e in entries}
        assert keys == {"keyA", "keyB"}


def test_app_load_bib_directory_and_pipeline() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        db_path = root / "test.db"
        f1 = root / "a.bib"
        f2 = root / "b.bib"

        f1.write_text("@article{seed1, title={Seed One}, author={Author A}, year={2022}}\n", encoding="utf-8")
        f2.write_text("@article{seed2, title={Seed Two}, author={Author B}, year={2023}}\n", encoding="utf-8")

        app = ResearchApp(db_path=db_path)
        try:
            # Test app.load_bib_files with directory path
            count = app.load_bib_files(root, auto_normalize=False)
            assert count == 2
            assert app.db.get("seed1") is not None
            assert app.db.get("seed2") is not None

            # Test pipeline run with directory bib_path
            cfg = PipelineConfig(
                query="",
                bib_path=root,
                snowball=False,
                download=False,
                convert=False,
                index_rag=False,
            )
            res = app.pipeline.run_sync(cfg)
            assert res.bib_count == 2

            # Test staged pipeline run with directory bib_path
            cfg_staged = PipelineConfig(
                query="",
                bib_path=root,
                snowball=False,
                download=False,
                convert=False,
                index_rag=False,
                streaming=False,
            )
            res_staged = app.pipeline.run_sync(cfg_staged)
            assert res_staged.bib_count == 2
        finally:
            import asyncio
            asyncio.run(app.close())

