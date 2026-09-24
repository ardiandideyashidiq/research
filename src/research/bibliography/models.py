from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from research.db.models import PublicationRecord

ACADEMIC_TITLES = {
    "dr.", "prof.", "ph.d.", "phd", "ll.m.", "llm", "s.h.", "sh", "m.h.", "mh",
    "m.si.", "msi", "s.sos.", "ssos", "m.hum.", "mhum", "s.pd.", "spd", "m.pd.", "mpd",
    "s.kom.", "skom", "m.kom.", "mkom", "b.a.", "ba", "m.a.", "ma", "b.sc.", "bsc", "m.sc.", "msc",
}


@dataclass
class Author:
    """Structured representation of a person/author."""

    family: str
    given: str = ""
    dropping_particle: str = ""
    non_dropping_particle: str = ""
    suffix: str = ""

    @property
    def full_name(self) -> str:
        parts = [p for p in [self.given, self.non_dropping_particle, self.family, self.suffix] if p]
        return " ".join(parts)

    @property
    def initials(self) -> str:
        """Return initials for given name(s), e.g. 'John Arthur' -> 'J. A.'."""
        if not self.given:
            return ""
        tokens = re.split(r"[\s.-]+", self.given.strip())
        inits = [f"{t[0].upper()}." for t in tokens if t]
        return " ".join(inits)

    @classmethod
    def parse(cls, raw: str) -> Author:
        """Parse raw author string into structured Author with titles stripped."""
        text = raw.strip()
        if not text:
            return cls(family="")

        # Remove academic titles
        tokens = [t for t in text.split() if t.lower().rstrip(".,") not in ACADEMIC_TITLES]
        cleaned = " ".join(tokens)
        cleaned = re.sub(r",\s*,+", ",", cleaned).strip(", ")

        if "," in cleaned:
            parts = [p.strip() for p in cleaned.split(",", 1)]
            family = parts[0]
            given = parts[1] if len(parts) > 1 else ""
            return cls(family=family, given=given)

        parts = cleaned.split()
        if len(parts) == 1:
            return cls(family=parts[0])

        return cls(family=parts[-1], given=" ".join(parts[:-1]))

    def to_csl_dict(self) -> dict[str, str]:
        """Export to standard CSL-JSON author object."""
        d = {"family": self.family}
        if self.given:
            d["given"] = self.given
        if self.dropping_particle:
            d["dropping-particle"] = self.dropping_particle
        if self.non_dropping_particle:
            d["non-dropping-particle"] = self.non_dropping_particle
        if self.suffix:
            d["suffix"] = self.suffix
        return d


@dataclass
class CSLItem:
    """Standard Citation Style Language (CSL-JSON) schema item."""

    id: str
    type: str = "article-journal"
    title: str = ""
    author: list[Author] = field(default_factory=list)
    issued_year: int | None = None
    issued_month: int | None = None
    issued_day: int | None = None
    container_title: str | None = None
    volume: str | None = None
    issue: str | None = None
    page: str | None = None
    doi: str | None = None
    url: str | None = None
    abstract: str | None = None
    publisher: str | None = None
    publisher_place: str | None = None
    edition: str | None = None
    isbn: str | None = None
    issn: str | None = None
    corpus: str = "literature"
    raw_extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_publication_record(cls, rec: PublicationRecord) -> CSLItem:
        """Convert a PublicationRecord into standard CSLItem."""
        authors = [Author.parse(a) for a in rec.authors if a]

        # Determine CSL type
        entry_type = (rec.entry_type or "article").lower()
        if entry_type in ("article", "journal_article", "article-journal"):
            csl_type = "article-journal"
            corpus = "literature"
        elif entry_type in ("putusan", "legal_case", "case"):
            csl_type = "legal_case"
            corpus = "putusan"
        elif entry_type in ("book",):
            csl_type = "book"
            corpus = "literature"
        elif entry_type in ("inproceedings", "conference", "paper-conference"):
            csl_type = "paper-conference"
            corpus = "literature"
        elif entry_type in ("online", "web", "webpage"):
            csl_type = "webpage"
            corpus = "web"
        else:
            csl_type = "article-journal"
            corpus = "literature"

        if rec.cite_key.startswith("Putusan_") or "putusan" in rec.sources:
            csl_type = "legal_case"
            corpus = "putusan"

        return cls(
            id=rec.cite_key,
            type=csl_type,
            title=rec.title,
            author=authors,
            issued_year=rec.year,
            container_title=rec.journal,
            volume=rec.volume,
            issue=rec.number,
            page=rec.pages,
            doi=rec.doi,
            url=rec.url or rec.pdf_url,
            abstract=rec.abstract,
            corpus=corpus,
            raw_extra=rec.full_metadata,
        )

    def to_publication_record(self) -> PublicationRecord:
        """Convert CSLItem into a PublicationRecord for SQLite storage."""
        authors_str = [a.full_name for a in self.author if a.family]

        # Map CSL type back to entry_type
        if self.type == "legal_case" or self.corpus == "putusan":
            entry_type = "putusan"
        elif self.type == "book":
            entry_type = "book"
        elif self.type == "paper-conference":
            entry_type = "inproceedings"
        elif self.type == "webpage":
            entry_type = "online"
        else:
            entry_type = "article"

        return PublicationRecord(
            cite_key=self.id,
            entry_type=entry_type,
            title=self.title,
            authors=authors_str,
            journal=self.container_title,
            year=self.issued_year,
            volume=self.volume,
            number=self.issue,
            pages=self.page,
            doi=self.doi,
            url=self.url,
            abstract=self.abstract,
            sources=[self.corpus],
            full_metadata=self.raw_extra,
        )

    @classmethod
    def from_csl_dict(cls, data: dict[str, Any]) -> CSLItem:
        """Construct CSLItem from standard CSL-JSON dictionary."""
        authors: list[Author] = []
        for a_data in data.get("author", []):
            if isinstance(a_data, dict):
                authors.append(
                    Author(
                        family=a_data.get("family", ""),
                        given=a_data.get("given", ""),
                        dropping_particle=a_data.get("dropping-particle", ""),
                        non_dropping_particle=a_data.get("non-dropping-particle", ""),
                        suffix=a_data.get("suffix", ""),
                    )
                )
            elif isinstance(a_data, str):
                authors.append(Author.parse(a_data))

        issued = data.get("issued", {})
        year = None
        month = None
        day = None
        if isinstance(issued, dict):
            date_parts = issued.get("date-parts", [])
            if date_parts and isinstance(date_parts[0], list) and date_parts[0]:
                year = date_parts[0][0]
                if len(date_parts[0]) > 1:
                    month = date_parts[0][1]
                if len(date_parts[0]) > 2:
                    day = date_parts[0][2]
        elif isinstance(issued, int):
            year = issued

        return cls(
            id=str(data.get("id") or ""),
            type=str(data.get("type") or "article-journal"),
            title=str(data.get("title") or ""),
            author=authors,
            issued_year=year,
            issued_month=month,
            issued_day=day,
            container_title=data.get("container-title") or data.get("journal"),
            volume=str(data.get("volume")) if data.get("volume") is not None else None,
            issue=str(data.get("issue") or data.get("number")) if (data.get("issue") or data.get("number")) is not None else None,
            page=str(data.get("page") or data.get("pages")) if (data.get("page") or data.get("pages")) is not None else None,
            doi=data.get("DOI") or data.get("doi"),
            url=data.get("URL") or data.get("url"),
            abstract=data.get("abstract"),
            publisher=data.get("publisher"),
            publisher_place=data.get("publisher-place"),
            edition=str(data.get("edition")) if data.get("edition") is not None else None,
            isbn=data.get("ISBN") or data.get("isbn"),
            issn=data.get("ISSN") or data.get("issn"),
            corpus="putusan" if data.get("type") == "legal_case" else "literature",
            raw_extra=data,
        )

    def to_csl_dict(self) -> dict[str, Any]:
        """Convert to official CSL-JSON dictionary format."""
        d: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "author": [a.to_csl_dict() for a in self.author],
        }
        if self.issued_year:
            parts = [self.issued_year]
            if self.issued_month:
                parts.append(self.issued_month)
                if self.issued_day:
                    parts.append(self.issued_day)
            d["issued"] = {"date-parts": [parts]}

        if self.container_title:
            d["container-title"] = self.container_title
        if self.volume:
            d["volume"] = self.volume
        if self.issue:
            d["issue"] = self.issue
        if self.page:
            d["page"] = self.page
        if self.doi:
            d["DOI"] = self.doi
        if self.url:
            d["URL"] = self.url
        if self.abstract:
            d["abstract"] = self.abstract
        if self.publisher:
            d["publisher"] = self.publisher
        if self.publisher_place:
            d["publisher-place"] = self.publisher_place
        if self.edition:
            d["edition"] = self.edition
        if self.isbn:
            d["ISBN"] = self.isbn
        if self.issn:
            d["ISSN"] = self.issn

        return d

    def to_ris(self) -> str:
        """Convert item to standard RIS format for Zotero/EndNote/Mendeley."""
        lines = []
        if self.type == "article-journal":
            lines.append("TY  - JOUR")
        elif self.type == "book":
            lines.append("TY  - BOOK")
        elif self.type == "paper-conference":
            lines.append("TY  - CONF")
        elif self.type == "legal_case":
            lines.append("TY  - CASE")
        elif self.type == "webpage":
            lines.append("TY  - ELEC")
        else:
            lines.append("TY  - GEN")

        lines.append(f"ID  - {self.id}")
        lines.append(f"TI  - {self.title}")

        for a in self.author:
            if a.family and a.given:
                lines.append(f"AU  - {a.family}, {a.given}")
            elif a.family:
                lines.append(f"AU  - {a.family}")

        if self.container_title:
            lines.append(f"JO  - {self.container_title}")
        if self.issued_year:
            lines.append(f"PY  - {self.issued_year}")
        if self.volume:
            lines.append(f"VL  - {self.volume}")
        if self.issue:
            lines.append(f"IS  - {self.issue}")
        if self.page:
            if "-" in self.page:
                sp, ep = self.page.split("-", 1)
                lines.append(f"SP  - {sp.strip()}")
                lines.append(f"EP  - {ep.strip()}")
            else:
                lines.append(f"SP  - {self.page.strip()}")
        if self.doi:
            lines.append(f"DO  - {self.doi}")
        if self.url:
            lines.append(f"UR  - {self.url}")
        if self.abstract:
            lines.append(f"AB  - {' '.join(self.abstract.split())}")
        if self.publisher:
            lines.append(f"PB  - {self.publisher}")

        lines.append("ER  - ")
        return "\n".join(lines)
