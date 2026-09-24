from __future__ import annotations

import html
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from research.web_search.models import WebSearchResult


def clean_web_text(text: str) -> str:
    """Sanitize raw web snippets/HTML into clean prose."""
    if not text:
        return ""

    # Decode HTML entities
    s = html.unescape(text)

    # Strip script and style tags completely
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", s, flags=re.DOTALL | re.IGNORECASE)

    # Convert common HTML tags to markdown
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</p>", "\n\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<li>", "- ", s, flags=re.IGNORECASE)
    s = re.sub(r"</li>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<(b|strong)>", "**", s, flags=re.IGNORECASE)
    s = re.sub(r"</(b|strong)>", "**", s, flags=re.IGNORECASE)
    s = re.sub(r"<(i|em)>", "*", s, flags=re.IGNORECASE)
    s = re.sub(r"</(i|em)>", "*", s, flags=re.IGNORECASE)

    # Strip all remaining tags
    s = re.sub(r"<[^>]+>", "", s)

    # Normalize excessive newlines and spaces
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def format_web_markdown(result: WebSearchResult) -> str:
    """Format a WebSearchResult into a publication-grade Markdown document with YAML frontmatter."""
    clean_title = clean_web_text(result.title)
    clean_summary = clean_web_text(result.content)
    clean_raw = clean_web_text(result.raw_content) if result.raw_content else ""

    timestamp = datetime.now(UTC).isoformat()
    pub_date = result.published_date or "N/A"

    # YAML Frontmatter
    lines: list[str] = [
        "---",
        f"title: {clean_title!r}",
        f"url: {result.url!r}",
        f"provider: {result.provider!r}",
        f"source_domain: {result.source_domain!r}",
        f"query: {result.query!r}",
        f"published_date: {pub_date!r}",
        f"indexed_at: {timestamp!r}",
        f"cite_key: {result.cite_key!r}",
        "---",
        "",
        f"# {clean_title}",
        "",
        f"- **Source**: [{result.source_domain}]({result.url})",
        f"- **Search Provider**: `{result.provider}`",
        f"- **Search Query**: `{result.query}`",
        f"- **Published Date**: {pub_date}",
        "",
        "---",
        "",
        "## Summary",
        "",
        clean_summary,
    ]

    if clean_raw and clean_raw != clean_summary:
        lines.extend([
            "",
            "## Detailed Content",
            "",
            clean_raw,
        ])

    lines.append("")
    return "\n".join(lines)
