from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class ReviewCard:
    """Literature Review Matrix Card for a single paper, court ruling, or web article."""

    card_id: str
    cite_key: str
    corpus: str = "literature"  # 'literature', 'putusan', 'web'
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str | None = None  # Journal name or Court name
    legal_issue: str = ""  # Isu hukum / Rumusan masalah
    theory: str = ""  # Teori / Landasan konseptual / Dasar hukum
    methodology: str = ""  # Metode penelitian / Pendekatan yuridis
    findings: str = ""  # Temuan utama / Argumen / Pertimbangan hukum & amar
    gap: str = ""  # Research gap / Kekurangan regulasi / Kelemahan argumen
    positioning: str = ""  # Positioning penelitian / Kontribusi / Kebaruan
    tags: list[str] = field(default_factory=list)
    notes: str = ""  # Catatan bebas peneliti
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> ReviewCard:
        """Construct ReviewCard from a SQLite row dictionary."""
        authors = row.get("authors")
        if isinstance(authors, str):
            try:
                authors = json.loads(authors)
            except (json.JSONDecodeError, TypeError):
                authors = [authors] if authors else []
        elif authors is None:
            authors = []

        tags = row.get("tags")
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except (json.JSONDecodeError, TypeError):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
        elif tags is None:
            tags = []

        return cls(
            card_id=row["card_id"],
            cite_key=row["cite_key"],
            corpus=row.get("corpus", "literature"),
            title=row.get("title", ""),
            authors=authors,
            year=row.get("year"),
            venue=row.get("venue"),
            legal_issue=row.get("legal_issue") or "",
            theory=row.get("theory") or "",
            methodology=row.get("methodology") or "",
            findings=row.get("findings") or "",
            gap=row.get("gap") or "",
            positioning=row.get("positioning") or "",
            tags=tags,
            notes=row.get("notes") or "",
            created_at=row.get("created_at") or datetime.now(UTC).isoformat(),
            updated_at=row.get("updated_at") or datetime.now(UTC).isoformat(),
        )

    def to_markdown_card(self) -> str:
        """Format review card as an individual rich markdown card."""
        authors_str = ", ".join(self.authors) if self.authors else "Anonim"
        year_str = f"({self.year})" if self.year else ""
        venue_str = f"*{self.venue}*" if self.venue else ""
        tags_str = " ".join(f"`#{t}`" for t in self.tags) if self.tags else "—"

        lines = [
            f"## [{self.corpus.upper()}] {self.title} {year_str}",
            f"**Cite Key**: `{self.cite_key}` | **Penulis**: {authors_str} | **Venue**: {venue_str}",
            f"**Tags**: {tags_str}",
            "",
            "### 1. Isu Hukum / Masalah Penelitian",
            self.legal_issue or "*(Belum diisi)*",
            "",
            "### 2. Teori / Landasan Konseptual / Dasar Hukum",
            self.theory or "*(Belum diisi)*",
            "",
            "### 3. Metode Penelitian / Pendekatan",
            self.methodology or "*(Belum diisi)*",
            "",
            "### 4. Temuan Utama / Pertimbangan Hukum & Amar",
            self.findings or "*(Belum diisi)*",
            "",
            "### 5. Research Gap / Kekurangan Regulasi",
            self.gap or "*(Belum diisi)*",
            "",
            "### 6. Positioning & Kontribusi",
            self.positioning or "*(Belum diisi)*",
            "",
        ]
        if self.notes:
            lines.extend(["### 7. Catatan Peneliti", self.notes, ""])

        lines.append("---")
        return "\n".join(lines)
