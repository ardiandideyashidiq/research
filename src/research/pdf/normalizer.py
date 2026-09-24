from __future__ import annotations

import re
from collections import Counter
from typing import Any

from research.pdf.models import ConversionOptions, PageChunk, PDFMetadata


def normalize_unicode(text: str) -> str:
    """Normalize non-breaking spaces, zero-width characters, and non-standard hyphens."""
    # Convert non-breaking spaces to standard space
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    # Remove soft hyphens and zero-width markers
    text = re.sub(r"[\xad\u200b\u200c\u200d\ufeff]", "", text)
    # Normalize non-standard hyphens/dashes to standard hyphen
    text = text.replace("\u2010", "-").replace("\u2011", "-")
    return text


def fix_latex_accents(text: str) -> str:
    """Normalize decomposed and legacy LaTeX TeX accents into standard Unicode characters."""
    replacements = [
        (r"´e", "é"), (r"´a", "á"), (r"´o", "ó"), (r"´i", "í"), (r"´u", "ú"), (r"´y", "ý"),
        (r"´E", "É"), (r"´A", "Á"), (r"´O", "Ó"), (r"´I", "Í"), (r"´U", "Ú"),
        (r"`e", "è"), (r"`a", "à"), (r"`o", "ò"), (r"`u", "ù"), (r"`i", "ì"),
        (r"`E", "È"), (r"`A", "À"), (r"`O", "Ò"), (r"`U", "Ù"),
        (r"\\`e", "è"), (r"\\`a", "à"), (r"\\´e", "é"),
        (r"¨a", "ä"), (r"¨o", "ö"), (r"¨u", "ü"), (r"¨ı", "ï"), (r"¨i", "ï"),
        (r"¨A", "Ä"), (r"¨O", "Ö"), (r"¨U", "Ü"),
        (r'\\"a', "ä"), (r'\\"o', "ö"), (r'\\"u', "ü"),
        (r"\^e", "ê"), (r"\^a", "â"), (r"\^o", "ô"), (r"\^i", "î"), (r"\^u", "û"),
        (r"\^E", "Ê"), (r"\^A", "Â"), (r"\^O", "Ô"), (r"\^U", "Û"),
        (r"˜n", "ñ"), (r"\\~n", "ñ"), (r"˜N", "Ñ"),
        (r"\\c\{c\}", "ç"), (r"¸c", "ç"), (r"¸C", "Ç"),
        (r"˚a", "å"), (r"˚A", "Å"),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)
    return text


def clean_headings(text: str) -> str:
    """Normalize markdown headings by stripping redundant bold/italic wrappers and trailing symbols."""
    lines = text.splitlines()
    cleaned_lines: list[str] = []

    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level, content = m.group(1), m.group(2).strip()
            # Strip redundant bold or italic tags: **Heading** or _Heading_
            content = re.sub(r"^\*\*(.*?)\*\*$", r"\1", content)
            content = re.sub(r"^_(.*?)_$", r"\1", content)
            content = re.sub(r"^\*(.*?)\*$", r"\1", content)
            # Normalize spacing after numbering, e.g. ## 1Introduction -> ## 1 Introduction
            content = re.sub(
                r"^((?:[0-9]+(?:\.[0-9]+)*\.?|[IVXLCDM]+\.))([A-Za-z])",
                r"\1 \2",
                content,
            )
            # Strip trailing colons or trailing hash tags from heading
            content = re.sub(r"\s*[:#]+\s*$", "", content).strip()
            cleaned_lines.append(f"{level} {content}")
        else:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def fix_hyphenation(text: str) -> str:
    """Merge hyphenated words split across line breaks."""
    # Match word characters with a hyphen at line end followed by word characters on next line
    return re.sub(r"(\b[a-zA-Z]{2,})[-–—]\n[ \t]*([a-zA-Z]{2,}\b)", r"\1\2", text)


def strip_page_numbers_and_noise(text: str) -> str:
    """Remove standalone page numbers and common running header noise."""
    patterns = [
        # Page X of Y or Page X
        r"(?mi)^\s*Page\s+\d+(\s*(?:of|/)\s*\d+)?\s*$",
        # Standalone numbers like - 1 - or [ 1 ] or bare single/double digit numbers
        r"(?m)^\s*[-–—\[\(]?\s*\d+\s*[-–—\]\)]?\s*$",
        # arXiv running stamp
        r"(?mi)^\s*arXiv:\d+\.\d+v?\d*\s*\[[a-zA-Z0-9\.\-]+\]\s*\d+\s+[A-Za-z]+\s+\d{4}\s*$",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    return text


def strip_repeating_headers_footers(chunks: list[PageChunk]) -> None:
    """Detect and remove identical running headers and footers across pages."""
    if len(chunks) < 2:
        return

    top_lines: list[str] = []
    bottom_lines: list[str] = []

    for chunk in chunks:
        lines = [line.strip() for line in chunk.text.splitlines() if line.strip()]
        if lines:
            top_lines.append(lines[0])
            if len(lines) > 1:
                bottom_lines.append(lines[-1])

    threshold = max(2, int(len(chunks) * 0.4))
    top_counts = Counter(top_lines)
    bottom_counts = Counter(bottom_lines)

    repeating_top = {line for line, cnt in top_counts.items() if cnt >= threshold and len(line) < 120}
    repeating_bottom = {line for line, cnt in bottom_counts.items() if cnt >= threshold and len(line) < 120}

    for chunk in chunks:
        lines = chunk.text.splitlines()
        filtered: list[str] = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            # If line is first or last non-empty line and matches repeating candidate, omit it
            if i < 3 and stripped in repeating_top:
                continue
            if i >= len(lines) - 3 and stripped in repeating_bottom:
                continue
            filtered.append(line)
        chunk.text = "\n".join(filtered)


def reflow_paragraphs(text: str) -> str:
    """Join broken lines inside paragraphs while preserving markdown syntax (lists, tables, quotes, code, math)."""
    blocks = re.split(r"\n\s*\n", text)
    reflowed_blocks: list[str] = []

    in_code_block = False

    for block in blocks:
        lines = block.splitlines()
        if not lines:
            continue

        # Toggle or check code blocks
        if any(line.strip().startswith(("```", "~~~")) for line in lines):
            in_code_block = not in_code_block
            reflowed_blocks.append(block)
            continue

        if in_code_block:
            reflowed_blocks.append(block)
            continue

        # Check if block is a table, list item, heading, blockquote, math equation, or hr
        is_special = any(
            line.strip().startswith(("#", ">", "|", "---", "***", "___", "* ", "- ", "+ ", "$$", "\\begin", "\\end"))
            or re.match(r"^\d+[\.\)]\s+", line.strip())
            or re.match(r"^\([0-9a-zA-ZivxIVX]+\)\s+", line.strip())
            or re.match(r"^\[\d+\]\s+", line.strip())
            for line in lines
        )

        if is_special:
            reflowed_blocks.append(block)
            continue

        # Merge standard prose lines into a single coherent paragraph
        joined = " ".join(line.strip() for line in lines if line.strip())
        joined = re.sub(r"\s+", " ", joined)
        if joined:
            reflowed_blocks.append(joined)

    return "\n\n".join(reflowed_blocks)


def clean_whitespace(text: str) -> str:
    """Trim trailing spaces and collapse excess blank lines to standard markdown spacing."""
    # Strip trailing whitespace on each line
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    # Collapse 3 or more newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_yaml_frontmatter(metadata: PDFMetadata, extra: dict[str, Any] | None = None) -> str:
    """Generate YAML frontmatter block for markdown documents."""
    fields: dict[str, Any] = {}
    if metadata.title:
        fields["title"] = metadata.title
    if metadata.author:
        fields["author"] = metadata.author
    if metadata.subject:
        fields["subject"] = metadata.subject
    if metadata.keywords:
        fields["keywords"] = metadata.keywords
    if metadata.page_count:
        fields["pages"] = metadata.page_count
    if metadata.creation_date:
        fields["date"] = metadata.creation_date

    if extra:
        fields.update(extra)

    if not fields:
        return ""

    lines = ["---"]
    for k, v in fields.items():
        if isinstance(v, (int, float, bool)):
            lines.append(f"{k}: {v}")
        elif isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {item}")
        else:
            clean_str = str(v).replace('"', '\\"')
            lines.append(f'{k}: "{clean_str}"')
    lines.append("---\n\n")
    return "\n".join(lines)


def normalize_markdown_layout(
    markdown: str,
    *,
    options: ConversionOptions | None = None,
) -> str:
    """Execute complete layout normalization pipeline on raw markdown."""
    opts = options or ConversionOptions()
    text = markdown

    # 1. Unicode & special characters
    text = normalize_unicode(text)

    # 2. LaTeX accents
    if opts.normalize_accents:
        text = fix_latex_accents(text)

    # 3. Hyphenation
    if opts.dehyphenate:
        text = fix_hyphenation(text)

    # 4. Page numbers and noise
    if opts.strip_headers_footers:
        text = strip_page_numbers_and_noise(text)

    # 5. Headings
    if opts.clean_headings:
        text = clean_headings(text)

    # 6. Paragraph reflow
    if opts.reflow_paragraphs:
        text = reflow_paragraphs(text)

    # 7. Whitespace normalization
    return clean_whitespace(text)
