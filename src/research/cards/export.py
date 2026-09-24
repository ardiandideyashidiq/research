from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from research.cards.models import ReviewCard


def export_matrix_markdown(cards: list[ReviewCard], *, include_details: bool = True) -> str:
    """Format review cards as a comprehensive Markdown Literature Review Matrix table and cards."""
    if not cards:
        return "# Literature Review Matrix\n\n*Tidak ada data kartu review.*\n"

    lines = [
        "# Matriks Literature Review & Card System",
        "",
        f"Total entri: **{len(cards)}** dokumen  ",
        f"Tanggal ekspor: *{cards[0].updated_at[:10] if cards else 'N/A'}*",
        "",
        "## 1. Tabel Matriks Komparatif",
        "",
        "| No | Referensi / Kasus | Tahun | Isu Hukum / Masalah | Teori / Dasar Hukum | Temuan Utama | Research Gap | Positioning / Kontribusi |",
        "|:---|:---|:---:|:---|:---|:---|:---|:---|",
    ]

    def _sanitize(text: str, max_chars: int = 200) -> str:
        s = text.replace("\n", " ").replace("|", "\\|").strip()
        if len(s) > max_chars:
            return s[:max_chars].rstrip() + "..."
        return s or "—"

    for i, c in enumerate(cards, start=1):
        ref_title = f"**{c.title}**" if len(c.title) < 60 else f"**{c.title[:57]}...**"
        ref_str = f"[{c.corpus.upper()}]<br>`{c.cite_key}`<br>{ref_title}"
        yr = str(c.year) if c.year else "—"
        issue = _sanitize(c.legal_issue)
        theory = _sanitize(c.theory)
        findings = _sanitize(c.findings)
        gap = _sanitize(c.gap)
        pos = _sanitize(c.positioning)

        row = f"| {i} | {ref_str} | {yr} | {issue} | {theory} | {findings} | {gap} | {pos} |"
        lines.append(row)

    if include_details:
        lines.extend(["", "---", "", "## 2. Detail Kartu Penelitian Per Dokumen", ""])
        for c in cards:
            lines.append(c.to_markdown_card())
            lines.append("")

    return "\n".join(lines)


def export_matrix_csv(cards: list[ReviewCard]) -> str:
    """Export review cards to standard CSV string with UTF-8 BOM."""
    output = io.StringIO()
    # Write UTF-8 BOM so Excel opens the file correctly
    output.write("\ufeff")

    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    writer.writerow([
        "No",
        "Cite Key",
        "Corpus",
        "Judul",
        "Penulis",
        "Tahun",
        "Jurnal / Pengadilan",
        "Isu Hukum / Masalah",
        "Teori / Dasar Hukum",
        "Metode Penelitian",
        "Temuan Utama / Amar",
        "Research Gap",
        "Positioning / Kontribusi",
        "Tags",
        "Catatan",
        "Updated At",
    ])

    for i, c in enumerate(cards, start=1):
        writer.writerow([
            i,
            c.cite_key,
            c.corpus,
            c.title,
            ", ".join(c.authors),
            c.year or "",
            c.venue or "",
            c.legal_issue,
            c.theory,
            c.methodology,
            c.findings,
            c.gap,
            c.positioning,
            ", ".join(c.tags),
            c.notes,
            c.updated_at,
        ])

    return output.getvalue()


def export_matrix_json(cards: list[ReviewCard]) -> str:
    """Export review cards to formatted JSON string."""
    data = [c.to_dict() for c in cards]
    return json.dumps(data, indent=2, ensure_ascii=False)


def export_cards_matrix(
    cards: list[ReviewCard],
    *,
    format: str = "markdown",
    output_path: str | Path | None = None,
    include_details: bool = True,
) -> str:
    """Unified exporter for Literature Review Cards supporting markdown, csv, and json."""
    fmt = format.lower().strip()
    if fmt == "csv":
        content = export_matrix_csv(cards)
    elif fmt == "json":
        content = export_matrix_json(cards)
    else:
        content = export_matrix_markdown(cards, include_details=include_details)

    if output_path:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    return content
