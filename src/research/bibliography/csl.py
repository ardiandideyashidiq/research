from __future__ import annotations

import json
from typing import ClassVar

from research.bibliography.models import Author, CSLItem


class CSLEngine:
    """Multi-style Citation Style Language (CSL) formatting engine for academic and legal works."""

    SUPPORTED_STYLES: ClassVar[list[str]] = [
        "apa",           # APA 7th edition
        "ieee",          # IEEE numbered
        "harvard",       # Harvard author-date
        "chicago",       # Chicago 17th author-date
        "chicago-note",  # Chicago 17th notes-bibliography
        "mla",           # MLA 9th edition
        "vancouver",     # Vancouver numbered biomedical
        "oscola",        # Oxford Standard for Citation of Legal Authorities
        "indonesia",     # Standar Jurnal & Sitasi Hukum Indonesia
        "bibtex",        # BibTeX source string
        "ris",           # RIS format (Zotero/EndNote)
        "csl-json",      # Official CSL-JSON
    ]

    # -------------------------------------------------------------------------
    # Author Name Formatters
    # -------------------------------------------------------------------------

    @staticmethod
    def _author_apa(author: Author) -> str:
        """APA: Family, G. M."""
        if not author.family:
            return author.full_name
        return f"{author.family}, {author.initials}" if author.initials else author.family

    @staticmethod
    def _authors_apa(authors: list[Author]) -> str:
        if not authors:
            return "Anonymous"
        formatted = [CSLEngine._author_apa(a) for a in authors if a.family]
        if not formatted:
            return "Anonymous"
        if len(formatted) == 1:
            return formatted[0]
        if len(formatted) == 2:
            return f"{formatted[0]}, & {formatted[1]}"
        if len(formatted) <= 20:
            return f"{', '.join(formatted[:-1])}, & {formatted[-1]}"
        return f"{', '.join(formatted[:19])}, ... {formatted[-1]}"

    @staticmethod
    def _author_ieee(author: Author) -> str:
        """IEEE: G. M. Family"""
        if not author.family:
            return author.full_name
        return f"{author.initials} {author.family}" if author.initials else author.family

    @staticmethod
    def _authors_ieee(authors: list[Author]) -> str:
        if not authors:
            return "Anonymous"
        formatted = [CSLEngine._author_ieee(a) for a in authors if a.family]
        if not formatted:
            return "Anonymous"
        if len(formatted) == 1:
            return formatted[0]
        if len(formatted) == 2:
            return f"{formatted[0]} and {formatted[1]}"
        if len(formatted) <= 6:
            return f"{', '.join(formatted[:-1])}, and {formatted[-1]}"
        return f"{formatted[0]} et al."

    @staticmethod
    def _author_harvard(author: Author) -> str:
        """Harvard: Family, G."""
        if not author.family:
            return author.full_name
        inits = author.initials.replace(". ", ".").rstrip(".")
        return f"{author.family}, {inits}" if inits else author.family

    @staticmethod
    def _authors_harvard(authors: list[Author]) -> str:
        if not authors:
            return "Anon."
        formatted = [CSLEngine._author_harvard(a) for a in authors if a.family]
        if not formatted:
            return "Anon."
        if len(formatted) == 1:
            return formatted[0]
        if len(formatted) == 2:
            return f"{formatted[0]} and {formatted[1]}"
        return f"{', '.join(formatted[:-1])} and {formatted[-1]}"

    @staticmethod
    def _author_chicago(author: Author, *, invert: bool = True) -> str:
        """Chicago: Family, Given (first author) or Given Family (subsequent)."""
        if not author.family:
            return author.full_name
        if invert:
            return f"{author.family}, {author.given}" if author.given else author.family
        return f"{author.given} {author.family}" if author.given else author.family

    @staticmethod
    def _authors_chicago(authors: list[Author]) -> str:
        if not authors:
            return "Anonymous"
        if len(authors) == 1:
            return CSLEngine._author_chicago(authors[0], invert=True)
        if len(authors) == 2:
            return f"{CSLEngine._author_chicago(authors[0], invert=True)}, and {CSLEngine._author_chicago(authors[1], invert=False)}"
        if len(authors) <= 10:
            parts = [CSLEngine._author_chicago(authors[0], invert=True)]
            parts.extend([CSLEngine._author_chicago(a, invert=False) for a in authors[1:-1]])
            return f"{', '.join(parts)}, and {CSLEngine._author_chicago(authors[-1], invert=False)}"
        parts = [CSLEngine._author_chicago(authors[0], invert=True)]
        parts.extend([CSLEngine._author_chicago(a, invert=False) for a in authors[1:7]])
        return f"{', '.join(parts)}, et al."

    @staticmethod
    def _author_mla(author: Author, *, invert: bool = True) -> str:
        """MLA: Family, Given (first) and Given Family (second)."""
        return CSLEngine._author_chicago(author, invert=invert)

    @staticmethod
    def _authors_mla(authors: list[Author]) -> str:
        if not authors:
            return "Anonymous"
        if len(authors) == 1:
            return CSLEngine._author_mla(authors[0], invert=True)
        if len(authors) == 2:
            return f"{CSLEngine._author_mla(authors[0], invert=True)}, and {CSLEngine._author_mla(authors[1], invert=False)}"
        return f"{CSLEngine._author_mla(authors[0], invert=True)}, et al."

    @staticmethod
    def _author_vancouver(author: Author) -> str:
        """Vancouver: Family GM (no punctuation in initials)."""
        if not author.family:
            return author.full_name
        inits = author.initials.replace(".", "").replace(" ", "")
        return f"{author.family} {inits}" if inits else author.family

    @staticmethod
    def _authors_vancouver(authors: list[Author]) -> str:
        if not authors:
            return "Anonymous"
        formatted = [CSLEngine._author_vancouver(a) for a in authors if a.family]
        if not formatted:
            return "Anonymous"
        if len(formatted) <= 6:
            return ", ".join(formatted)
        return f"{', '.join(formatted[:6])}, et al."

    @staticmethod
    def _authors_oscola(authors: list[Author]) -> str:
        """OSCOLA: Given Family (no inverted names in footnotes, optional in table)."""
        if not authors:
            return ""
        formatted = [f"{a.given} {a.family}".strip() for a in authors if a.family]
        if not formatted:
            return ""
        if len(formatted) == 1:
            return formatted[0]
        if len(formatted) == 2:
            return f"{formatted[0]} and {formatted[1]}"
        return f"{formatted[0]} and others"

    @staticmethod
    def _authors_indonesia(authors: list[Author]) -> str:
        """Standar Penulisan Ilmiah Hukum Indonesia: Nama Lengkap Penulis."""
        if not authors:
            return "Anonim"
        formatted = [a.full_name for a in authors if a.family]
        if not formatted:
            return "Anonim"
        if len(formatted) == 1:
            return formatted[0]
        if len(formatted) == 2:
            return f"{formatted[0]} dan {formatted[1]}"
        if len(formatted) == 3:
            return f"{formatted[0]}, {formatted[1]}, dan {formatted[2]}"
        return f"{formatted[0]} dkk."

    # -------------------------------------------------------------------------
    # In-Text Citation Formatters
    # -------------------------------------------------------------------------

    @classmethod
    def format_in_text(
        cls,
        item: CSLItem,
        style: str = "apa",
        *,
        index: int = 1,
        page: str | None = None,
    ) -> str:
        """Generate in-text citation string according to the requested style."""
        style_norm = style.lower().strip()
        year = str(item.issued_year) if item.issued_year else "n.d."
        page_str = f", p. {page}" if page else ""

        # Special handling for court decisions (Putusan)
        if item.type == "legal_case" or item.corpus == "putusan":
            if style_norm == "oscola":
                return f"*{item.title}* ({year})"
            if style_norm == "indonesia":
                return f"({item.title})"
            return f"(*{item.title}*, {year})"

        authors = [a for a in item.author if a.family]

        if style_norm in ("ieee", "vancouver"):
            return f"[{index}]"

        if not authors:
            short_title = f'"{item.title[:25]}..."' if item.title else "Anon."
            return f"({short_title}, {year}{page_str})"

        f0 = authors[0].family
        if len(authors) == 1:
            lead = f0
        elif len(authors) == 2:
            sep = "&" if style_norm in ("apa",) else "and"
            if style_norm == "indonesia":
                sep = "dan"
            lead = f"{f0} {sep} {authors[1].family}"
        else:
            suffix = "dkk." if style_norm == "indonesia" else "et al."
            lead = f"{f0} {suffix}"

        if style_norm == "mla":
            p_mla = f" {page}" if page else ""
            return f"({lead}{p_mla})"

        if style_norm == "chicago":
            p_chi = f", {page}" if page else ""
            return f"({lead} {year}{p_chi})"

        return f"({lead}, {year}{page_str})"

    # -------------------------------------------------------------------------
    # Full Bibliography Entry Formatters
    # -------------------------------------------------------------------------

    @classmethod
    def format_entry(
        cls,
        item: CSLItem,
        style: str = "apa",
        *,
        index: int = 1,
    ) -> str:
        """Format a single CSLItem into a full reference list entry in the given style."""
        style_norm = style.lower().strip()

        # Raw data formats
        if style_norm == "bibtex":
            return cls._format_bibtex(item)
        if style_norm == "ris":
            return item.to_ris()
        if style_norm == "csl-json":
            return json.dumps(item.to_csl_dict(), indent=2, ensure_ascii=False)

        # Legal cases (Putusan) special handling across all styles
        if item.type == "legal_case" or item.corpus == "putusan":
            return cls._format_legal_case(item, style_norm, index=index)

        if style_norm == "apa":
            return cls._format_apa(item)
        if style_norm == "ieee":
            return cls._format_ieee(item, index=index)
        if style_norm == "harvard":
            return cls._format_harvard(item)
        if style_norm in ("chicago", "chicago-author-date"):
            return cls._format_chicago(item)
        if style_norm == "chicago-note":
            return cls._format_chicago_note(item)
        if style_norm == "mla":
            return cls._format_mla(item)
        if style_norm == "vancouver":
            return cls._format_vancouver(item, index=index)
        if style_norm == "oscola":
            return cls._format_oscola(item)
        if style_norm == "indonesia":
            return cls._format_indonesia(item)

        # Default fallback to APA
        return cls._format_apa(item)

    # -------------------------------------------------------------------------
    # Style-specific Implementations
    # -------------------------------------------------------------------------

    @classmethod
    def _format_apa(cls, item: CSLItem) -> str:
        """APA 7th Edition:
        Authors. (Year). Title. Journal Name, volume(issue), pages. https://doi.org/...
        """
        authors_str = cls._authors_apa(item.author)
        year_str = f"({item.issued_year})" if item.issued_year else "(n.d.)"
        title_str = item.title.rstrip(".") if item.title else "Untitled"

        parts = [f"{authors_str} {year_str}. {title_str}."]

        if item.container_title:
            journal_part = f"*{item.container_title}*"
            if item.volume:
                journal_part += f", *{item.volume}*"
                if item.issue:
                    journal_part += f"({item.issue})"
            if item.page:
                journal_part += f", {item.page}"
            parts.append(f"{journal_part}.")
        elif item.publisher:
            parts.append(f"{item.publisher}.")

        if item.doi:
            doi_url = item.doi if item.doi.startswith("http") else f"https://doi.org/{item.doi}"
            parts.append(doi_url)
        elif item.url:
            parts.append(item.url)

        return " ".join(parts)

    @classmethod
    def _format_ieee(cls, item: CSLItem, *, index: int = 1) -> str:
        """IEEE:
        [1] G. M. Author, "Title," Journal Name, vol. x, no. y, pp. xx-xx, year, doi: ...
        """
        authors_str = cls._authors_ieee(item.author)
        title_clean = item.title.rstrip(".") if item.title else "Untitled"
        parts = [f"[{index}] {authors_str}, \"{title_clean},\""]

        details = []
        if item.container_title:
            details.append(f"*{item.container_title}*")
        if item.volume:
            details.append(f"vol. {item.volume}")
        if item.issue:
            details.append(f"no. {item.issue}")
        if item.page:
            p_prefix = "pp." if "-" in item.page else "p."
            details.append(f"{p_prefix} {item.page}")
        if item.issued_year:
            details.append(str(item.issued_year))

        if details:
            parts.append(f"{', '.join(details)}.")

        if item.doi:
            parts.append(f"doi: {item.doi}.")
        elif item.url:
            parts.append(f"[Online]. Available: {item.url}")

        return " ".join(parts)

    @classmethod
    def _format_harvard(cls, item: CSLItem) -> str:
        """Harvard:
        Author, G. (Year) 'Title', Journal Name, volume(issue), pp. xx-xx.
        """
        authors_str = cls._authors_harvard(item.author)
        year_str = f"({item.issued_year})" if item.issued_year else "(no date)"
        title_clean = item.title.rstrip(".") if item.title else "Untitled"
        parts = [f"{authors_str} {year_str} '{title_clean}',"]

        details = []
        if item.container_title:
            j_part = f"*{item.container_title}*"
            if item.volume:
                j_part += f", {item.volume}"
                if item.issue:
                    j_part += f"({item.issue})"
            details.append(j_part)
        if item.page:
            p_prefix = "pp." if "-" in item.page else "p."
            details.append(f"{p_prefix} {item.page}")

        if details:
            parts.append(f"{', '.join(details)}.")
        elif item.publisher:
            parts.append(f"{item.publisher}.")

        if item.doi:
            doi_url = item.doi if item.doi.startswith("http") else f"https://doi.org/{item.doi}"
            parts.append(f"Available at: {doi_url}.")
        elif item.url:
            parts.append(f"Available at: {item.url}.")

        return " ".join(parts)

    @classmethod
    def _format_chicago(cls, item: CSLItem) -> str:
        """Chicago 17th (Author-Date):
        Author, Given. Year. "Title." Journal Name volume (issue): pages. https://doi.org/...
        """
        authors_str = cls._authors_chicago(item.author)
        year_str = f"{item.issued_year}." if item.issued_year else "n.d."
        title_clean = item.title.rstrip(".") if item.title else "Untitled"
        parts = [f"{authors_str} {year_str} \"{title_clean}.\""]

        if item.container_title:
            j_part = f"*{item.container_title}*"
            if item.volume:
                j_part += f" {item.volume}"
            if item.issue:
                j_part += f", no. {item.issue}"
            if item.page:
                j_part += f": {item.page}"
            parts.append(f"{j_part}.")
        elif item.publisher:
            parts.append(f"{item.publisher}.")

        if item.doi:
            doi_url = item.doi if item.doi.startswith("http") else f"https://doi.org/{item.doi}"
            parts.append(doi_url)
        elif item.url:
            parts.append(item.url)

        return " ".join(parts)

    @classmethod
    def _format_chicago_note(cls, item: CSLItem) -> str:
        """Chicago 17th (Notes & Bibliography / Full Note):
        Given Family, "Title," Journal Name volume, no. issue (Year): pages.
        """
        authors = [f"{a.given} {a.family}".strip() for a in item.author if a.family]
        if not authors:
            auth_str = "Anonymous"
        elif len(authors) == 1:
            auth_str = authors[0]
        elif len(authors) == 2:
            auth_str = f"{authors[0]} and {authors[1]}"
        else:
            auth_str = f"{', '.join(authors[:-1])}, and {authors[-1]}"

        title_clean = item.title.rstrip(".") if item.title else "Untitled"
        parts = [f"{auth_str}, \"{title_clean},\""]

        if item.container_title:
            j_part = f"*{item.container_title}*"
            if item.volume:
                j_part += f" {item.volume}"
            if item.issue:
                j_part += f", no. {item.issue}"
            if item.issued_year:
                j_part += f" ({item.issued_year})"
            if item.page:
                j_part += f": {item.page}"
            parts.append(f"{j_part}.")

        if item.doi:
            doi_url = item.doi if item.doi.startswith("http") else f"https://doi.org/{item.doi}"
            parts.append(doi_url)
        elif item.url:
            parts.append(item.url)

        return " ".join(parts)

    @classmethod
    def _format_mla(cls, item: CSLItem) -> str:
        """MLA 9th Edition:
        Author, Given. "Title." Journal Name, vol. x, no. y, Year, pp. xx-xx. Location.
        """
        authors_str = cls._authors_mla(item.author)
        title_clean = item.title.rstrip(".") if item.title else "Untitled"
        parts = [f"{authors_str}. \"{title_clean}.\""]

        details = []
        if item.container_title:
            details.append(f"*{item.container_title}*")
        if item.volume:
            details.append(f"vol. {item.volume}")
        if item.issue:
            details.append(f"no. {item.issue}")
        if item.issued_year:
            details.append(str(item.issued_year))
        if item.page:
            p_prefix = "pp." if "-" in item.page else "p."
            details.append(f"{p_prefix} {item.page}")

        if details:
            parts.append(f"{', '.join(details)}.")
        elif item.publisher:
            parts.append(f"{item.publisher}.")

        if item.doi:
            doi_url = item.doi if item.doi.startswith("http") else f"https://doi.org/{item.doi}"
            parts.append(doi_url)
        elif item.url:
            parts.append(item.url)

        return " ".join(parts)

    @classmethod
    def _format_vancouver(cls, item: CSLItem, *, index: int = 1) -> str:
        """Vancouver:
        1. Author GM. Title. Journal Abbr. Year;volume(issue):pages.
        """
        authors_str = cls._authors_vancouver(item.author)
        title_clean = item.title.rstrip(".") if item.title else "Untitled"
        parts = [f"{index}. {authors_str}. {title_clean}."]

        if item.container_title:
            j_part = f"{item.container_title}."
            if item.issued_year:
                j_part += f" {item.issued_year}"
            if item.volume:
                j_part += f";{item.volume}"
                if item.issue:
                    j_part += f"({item.issue})"
            if item.page:
                j_part += f":{item.page}"
            parts.append(f"{j_part}.")

        if item.doi:
            doi_url = item.doi if item.doi.startswith("http") else f"https://doi.org/{item.doi}"
            parts.append(f"doi: {doi_url}")

        return " ".join(parts)

    @classmethod
    def _format_oscola(cls, item: CSLItem) -> str:
        """OSCOLA (Oxford Standard for Legal Authorities):
        Author, 'Title' (Year) Volume(Issue) Journal Pages.
        """
        authors_str = cls._authors_oscola(item.author)
        title_clean = item.title.rstrip(".") if item.title else "Untitled"
        year_str = f"({item.issued_year})" if item.issued_year else ""

        lead = f"{authors_str}, '{title_clean}'" if authors_str else f"'{title_clean}'"
        parts = [lead]

        citation_bits = []
        if year_str:
            citation_bits.append(year_str)
        if item.volume:
            citation_bits.append(item.volume)
        if item.container_title:
            citation_bits.append(item.container_title)
        if item.page:
            citation_bits.append(item.page)

        if citation_bits:
            parts.append(" ".join(citation_bits))

        return " ".join(parts)

    @classmethod
    def _format_indonesia(cls, item: CSLItem) -> str:
        """Standar Penulisan Karya Ilmiah Hukum Indonesia:
        Nama Penulis, "Judul Artikel", Nama Jurnal, Vol. X, No. Y (Tahun), hlm. ...
        """
        authors_str = cls._authors_indonesia(item.author)
        title_clean = item.title.rstrip(".") if item.title else "Tanpa Judul"
        parts = [f"{authors_str}, \"{title_clean},\""]

        details = []
        if item.container_title:
            details.append(f"*{item.container_title}*")
        if item.volume:
            details.append(f"Vol. {item.volume}")
        if item.issue:
            details.append(f"No. {item.issue}")
        if item.issued_year:
            details.append(f"({item.issued_year})")
        if item.page:
            details.append(f"hlm. {item.page}")

        if details:
            parts.append(f"{', '.join(details)}.")
        elif item.publisher:
            parts.append(f"{item.publisher}.")

        if item.doi:
            parts.append(f"DOI: {item.doi}.")
        elif item.url:
            parts.append(f"Tersedia pada: {item.url}")

        return " ".join(parts)

    @classmethod
    def _format_legal_case(cls, item: CSLItem, style: str, *, index: int = 1) -> str:
        """Format judicial decisions / Indonesian court judgments (Putusan)."""
        year_str = f"({item.issued_year})" if item.issued_year else ""
        court_name = item.container_title or "Mahkamah Agung RI"

        if style in ("ieee", "vancouver"):
            return f"[{index}] *{item.title}*, {court_name}, {year_str}."

        if style == "oscola":
            # e.g., *Putusan MA No. 1093 K/Pid.Sus/2014* (Mahkamah Agung RI 2014)
            return f"*{item.title}* ({court_name} {item.issued_year or ''})."

        if style == "indonesia":
            # Standar hukum Indonesia: [Pengadilan], *Putusan Nomor ...*, [Tahun]
            return f"{court_name}, *{item.title}* {year_str}."

        if style == "apa":
            # APA legal style: Name v. Name / In re ..., Volume Reporter Page (Court Year)
            return f"*{item.title}*, {court_name} {year_str}."

        # General legal fallback
        return f"*{item.title}* ({court_name} {year_str})."

    @classmethod
    def _format_bibtex(cls, item: CSLItem) -> str:
        """Format CSLItem into clean BibTeX string."""
        entry_type = "article"
        if item.type == "book":
            entry_type = "book"
        elif item.type == "paper-conference":
            entry_type = "inproceedings"
        elif item.type == "legal_case":
            entry_type = "misc"
        elif item.type == "webpage":
            entry_type = "online"

        lines = [f"@{entry_type}{{{item.id},"]
        if item.title:
            lines.append(f"  title = {{{item.title}}},")

        if item.author:
            authors_bib = " and ".join(
                f"{a.family}, {a.given}".strip(", ") for a in item.author if a.family
            )
            if authors_bib:
                lines.append(f"  author = {{{authors_bib}}},")

        if item.container_title:
            field_name = "booktitle" if entry_type == "inproceedings" else "journal"
            lines.append(f"  {field_name} = {{{item.container_title}}},")

        if item.issued_year:
            lines.append(f"  year = {{{item.issued_year}}},")
        if item.volume:
            lines.append(f"  volume = {{{item.volume}}},")
        if item.issue:
            lines.append(f"  number = {{{item.issue}}},")
        if item.page:
            lines.append(f"  pages = {{{item.page}}},")
        if item.doi:
            lines.append(f"  doi = {{{item.doi}}},")
        if item.url:
            lines.append(f"  url = {{{item.url}}},")
        if item.publisher:
            lines.append(f"  publisher = {{{item.publisher}}},")

        lines.append("}")
        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Batch Bibliography Formatter
    # -------------------------------------------------------------------------

    @classmethod
    def format_bibliography(
        cls,
        items: list[CSLItem],
        style: str = "apa",
        *,
        output_format: str = "text",
    ) -> str:
        """Format an entire collection of CSLItems into a sorted bibliography."""
        style_norm = style.lower().strip()

        # Sort items: numbered styles retain original or appearance order;
        # author-date styles sort alphabetically by first author family name, then year.
        if style_norm not in ("ieee", "vancouver"):
            items = sorted(
                items,
                key=lambda x: (
                    (x.author[0].family.lower() if x.author and x.author[0].family else "zzz"),
                    x.issued_year or 9999,
                    x.title.lower(),
                ),
            )

        formatted_entries = [
            cls.format_entry(item, style=style_norm, index=i + 1)
            for i, item in enumerate(items)
        ]

        if output_format == "json" or style_norm == "csl-json":
            return json.dumps([item.to_csl_dict() for item in items], indent=2, ensure_ascii=False)

        if output_format == "bibtex" or style_norm == "bibtex":
            return "\n\n".join(formatted_entries)

        if output_format == "ris" or style_norm == "ris":
            return "\n\n".join(formatted_entries)

        if output_format == "markdown":
            md_lines = [f"# Daftar Pustaka / Bibliography ({style.upper()})\n"]
            for i, entry in enumerate(formatted_entries, 1):
                if style_norm in ("ieee", "vancouver"):
                    md_lines.append(f"{entry}\n")
                else:
                    md_lines.append(f"{i}. {entry}\n")
            return "\n".join(md_lines)

        if output_format == "html":
            html_lines = [f"<h2>Bibliography ({style.upper()})</h2>", "<ul>"]
            for entry in formatted_entries:
                html_lines.append(f"  <li>{entry}</li>")
            html_lines.append("</ul>")
            return "\n".join(html_lines)

        # Plain text
        return "\n\n".join(formatted_entries)
