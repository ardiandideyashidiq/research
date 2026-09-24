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
    from research.cli.main import main as cli_main

    cli_main()
