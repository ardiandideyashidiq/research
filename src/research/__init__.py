from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from research.app import ResearchApp


def get_app(*args, **kwargs) -> ResearchApp:
    """Lazy loader for the unified ResearchApp instance."""
    from research.app import ResearchApp

    return ResearchApp(*args, **kwargs)


def main() -> None:
    """CLI entry point for research."""
    from research.db import DatabaseManager

    db = DatabaseManager("tmp/publications.sqlite")
    total = db.count()
    summary = db.get_status_summary()
    print("========================================")
    print("      RESEARCH KNOWLEDGE ENGINE         ")
    print("========================================")
    print(f"Total Publications in DB: {total}")
    print(f"Download Status Breakdown: {summary}")
    print("Providers Available: arxiv, openalex, crossref, doaj, openaire, unpaywall, ojs, tavily")
    print("Run research via Python SDK or CLI subcommands.")
