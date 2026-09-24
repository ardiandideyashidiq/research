from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime
from html import unescape
from typing import Any

from loguru import logger

from research.db.models import PublicationRecord
from research.normalizer.crossref import (
    fetch_crossref_metadata,
    fetch_crossref_metadata_async,
    normalize_doi,
)
from research.ojs.client import OJSClient
from research.unpaywall import UnpaywallClient, get_unpaywall_record


def normalize_title(title: str) -> str:
    """Clean and normalize a publication title."""
    if not title:
        return ""
    cleaned = title.strip()
    while cleaned.startswith("{") and cleaned.endswith("}"):
        cleaned = cleaned[1:-1].strip()
    cleaned = unescape(cleaned)
    cleaned = re.sub(r"[{}\"\\]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def normalize_authors(authors: list[str] | str) -> list[str]:
    """Clean and standardize author names."""
    if isinstance(authors, str):
        raw = re.split(r"\s+and\s+", authors, flags=re.IGNORECASE)
    else:
        raw = authors

    normalized = []
    for a in raw:
        cleaned = a.strip().strip("{}").strip()
        cleaned = unescape(cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        if cleaned:
            normalized.append(cleaned)
    return normalized


def normalize_abstract(abstract: str | None) -> str | None:
    """Clean and standardize abstract text."""
    if not abstract:
        return None
    cleaned = unescape(abstract)
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # Strip leading "Abstract " or "Abstrak "
    cleaned = re.sub(r"^(?:Abstract|Abstrak)[:\s—\-]+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if cleaned else None


def normalize_record(
    record: PublicationRecord | dict[str, Any],
    *,
    enrich_crossref: bool = True,
    enrich_ojs: bool = True,
    enrich_unpaywall: bool = True,
    ojs_client: OJSClient | None = None,
) -> PublicationRecord:
    """Normalize fields and enrich metadata for a single publication record synchronously."""
    rec = record if isinstance(record, PublicationRecord) else PublicationRecord.from_row(record)

    rec.title = normalize_title(rec.title)
    rec.authors = normalize_authors(rec.authors)
    rec.abstract = normalize_abstract(rec.abstract)
    rec.doi = normalize_doi(rec.doi)

    enrichment: dict[str, Any] = dict(rec.full_metadata)

    # 1. Enrich from Crossref if DOI is available
    if enrich_crossref and rec.doi:
        crossref_data = fetch_crossref_metadata(rec.doi)
        if crossref_data:
            enrichment["crossref"] = crossref_data
            if not rec.journal and crossref_data.get("container-title"):
                containers = crossref_data["container-title"]
                if containers:
                    rec.journal = containers[0]

            if not rec.year and crossref_data.get("published"):
                parts = crossref_data["published"].get("date-parts", [[]])[0]
                if parts:
                    rec.year = parts[0]

            if not rec.abstract and crossref_data.get("abstract"):
                rec.abstract = normalize_abstract(crossref_data["abstract"])

            if not rec.url and crossref_data.get("resource", {}).get("primary", {}).get("URL"):
                rec.url = crossref_data["resource"]["primary"]["URL"]

    # 2. Enrich from OJS if URL is available
    if enrich_ojs and rec.url:
        client = ojs_client or OJSClient()
        ojs_meta = client.fetch_metadata_sync(rec.url)
        if ojs_meta.is_ojs:
            rec.is_ojs = True
            enrichment["ojs"] = ojs_meta.to_dict()
            if ojs_meta.pdf_url:
                rec.pdf_url = ojs_meta.pdf_url
            if not rec.abstract and ojs_meta.abstract:
                rec.abstract = normalize_abstract(ojs_meta.abstract)
            if not rec.journal and ojs_meta.journal_title:
                rec.journal = ojs_meta.journal_title
            if not rec.doi and ojs_meta.doi:
                rec.doi = normalize_doi(ojs_meta.doi)
            if not rec.year and ojs_meta.year:
                rec.year = ojs_meta.year

    # 3. Enrich from Unpaywall for direct Open Access PDF if DOI is available
    if enrich_unpaywall and rec.doi:
        up_rec = get_unpaywall_record(rec.doi)
        if up_rec and up_rec.is_oa:
            enrichment["unpaywall"] = up_rec.to_dict()
            if not rec.pdf_url and up_rec.best_pdf_url:
                rec.pdf_url = up_rec.best_pdf_url
            if not rec.journal and up_rec.journal_name:
                rec.journal = up_rec.journal_name

    enrichment["normalized_at"] = datetime.now(UTC).isoformat()
    rec.full_metadata = enrichment
    return rec


async def normalize_record_async(
    record: PublicationRecord | dict[str, Any],
    *,
    enrich_crossref: bool = True,
    enrich_ojs: bool = True,
    enrich_unpaywall: bool = True,
    ojs_client: OJSClient | None = None,
    unpaywall_client: UnpaywallClient | None = None,
) -> PublicationRecord:
    """Normalize fields and enrich metadata for a single publication record asynchronously."""
    rec = record if isinstance(record, PublicationRecord) else PublicationRecord.from_row(record)

    rec.title = normalize_title(rec.title)
    rec.authors = normalize_authors(rec.authors)
    rec.abstract = normalize_abstract(rec.abstract)
    rec.doi = normalize_doi(rec.doi)

    enrichment: dict[str, Any] = dict(rec.full_metadata)

    # 1. Enrich from Crossref if DOI is available
    if enrich_crossref and rec.doi:
        crossref_data = await fetch_crossref_metadata_async(rec.doi)
        if crossref_data:
            enrichment["crossref"] = crossref_data
            if not rec.journal and crossref_data.get("container-title"):
                containers = crossref_data["container-title"]
                if containers:
                    rec.journal = containers[0]

            if not rec.year and crossref_data.get("published"):
                parts = crossref_data["published"].get("date-parts", [[]])[0]
                if parts:
                    rec.year = parts[0]

            if not rec.abstract and crossref_data.get("abstract"):
                rec.abstract = normalize_abstract(crossref_data["abstract"])

            if not rec.url and crossref_data.get("resource", {}).get("primary", {}).get("URL"):
                rec.url = crossref_data["resource"]["primary"]["URL"]

    # 2. Enrich from OJS if URL is available
    if enrich_ojs and rec.url:
        client = ojs_client
        should_close = False
        if client is None:
            client = OJSClient()
            should_close = True

        try:
            ojs_meta = await client.fetch_metadata(rec.url)
            if ojs_meta.is_ojs:
                rec.is_ojs = True
                enrichment["ojs"] = ojs_meta.to_dict()
                if ojs_meta.pdf_url:
                    rec.pdf_url = ojs_meta.pdf_url
                if not rec.abstract and ojs_meta.abstract:
                    rec.abstract = normalize_abstract(ojs_meta.abstract)
                if not rec.journal and ojs_meta.journal_title:
                    rec.journal = ojs_meta.journal_title
                if not rec.doi and ojs_meta.doi:
                    rec.doi = normalize_doi(ojs_meta.doi)
                if not rec.year and ojs_meta.year:
                    rec.year = ojs_meta.year
        finally:
            if should_close:
                await client.close()

    # 3. Enrich from Unpaywall for direct Open Access PDF if DOI is available
    if enrich_unpaywall and rec.doi:
        up_client = unpaywall_client
        should_close_up = False
        if up_client is None:
            up_client = UnpaywallClient()
            should_close_up = True

        try:
            up_rec = await up_client.get_record(rec.doi)
            if up_rec and up_rec.is_oa:
                enrichment["unpaywall"] = up_rec.to_dict()
                if not rec.pdf_url and up_rec.best_pdf_url:
                    rec.pdf_url = up_rec.best_pdf_url
                if not rec.journal and up_rec.journal_name:
                    rec.journal = up_rec.journal_name
        finally:
            if should_close_up:
                await up_client.close()

    enrichment["normalized_at"] = datetime.now(UTC).isoformat()
    rec.full_metadata = enrichment
    return rec


async def normalize_records_async(
    records: list[PublicationRecord],
    *,
    concurrency: int = 5,
    enrich_crossref: bool = True,
    enrich_ojs: bool = True,
    enrich_unpaywall: bool = True,
) -> list[PublicationRecord]:
    """Batch normalize multiple records concurrently with rate limiting."""
    sem = asyncio.Semaphore(concurrency)
    async with (
        OJSClient() as ojs_client,
        UnpaywallClient() as unpaywall_client,
    ):

        async def _worker(rec: PublicationRecord) -> PublicationRecord:
            async with sem:
                try:
                    return await normalize_record_async(
                        rec,
                        enrich_crossref=enrich_crossref,
                        enrich_ojs=enrich_ojs,
                        enrich_unpaywall=enrich_unpaywall,
                        ojs_client=ojs_client,
                        unpaywall_client=unpaywall_client,
                    )
                except Exception as e:  # noqa: BLE001 - worker safeguard
                    logger.warning(f"Error normalizing record {rec.cite_key}: {e}")
                    return rec

        tasks = [_worker(r) for r in records]
        return await asyncio.gather(*tasks)
