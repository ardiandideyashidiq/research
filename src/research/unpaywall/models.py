from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

HARDCODED_EMAIL = "rdndds@gmail.com"


@dataclass
class UnpaywallLocation:
    url_for_pdf: str | None = None
    url_for_landing_page: str | None = None
    version: str | None = None
    license: str | None = None
    host_type: str | None = None
    is_best: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UnpaywallRecord:
    doi: str
    is_oa: bool = False
    title: str | None = None
    journal_name: str | None = None
    year: int | None = None
    genre: str | None = None
    published_date: str | None = None
    best_pdf_url: str | None = None
    best_landing_url: str | None = None
    locations: list[UnpaywallLocation] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> UnpaywallRecord:
        """Parse raw Unpaywall API response dictionary."""
        doi = data.get("doi", "")
        is_oa = bool(data.get("is_oa", False))
        title = data.get("title")
        journal = data.get("journal_name")
        year = data.get("year")
        genre = data.get("genre")
        pub_date = data.get("published_date")

        best_loc_data = data.get("best_oa_location") or {}
        best_pdf = best_loc_data.get("url_for_pdf")
        best_landing = best_loc_data.get("url_for_landing_page") or best_loc_data.get("url")

        locations: list[UnpaywallLocation] = []
        for loc in data.get("oa_locations", []):
            locations.append(
                UnpaywallLocation(
                    url_for_pdf=loc.get("url_for_pdf"),
                    url_for_landing_page=loc.get("url_for_landing_page") or loc.get("url"),
                    version=loc.get("version"),
                    license=loc.get("license"),
                    host_type=loc.get("host_type"),
                    is_best=loc.get("is_best", False),
                )
            )

        return cls(
            doi=doi,
            is_oa=is_oa,
            title=title,
            journal_name=journal,
            year=year,
            genre=genre,
            published_date=pub_date,
            best_pdf_url=best_pdf,
            best_landing_url=best_landing,
            locations=locations,
            raw_data=data,
        )
