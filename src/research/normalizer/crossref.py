from __future__ import annotations

import json
import re
from typing import Any

import httpx
from loguru import logger


def normalize_doi(raw_doi: str | None) -> str | None:
    """Normalize a DOI string into canonical format (e.g. 10.1234/xyz)."""
    if not raw_doi:
        return None
    cleaned = raw_doi.strip()
    cleaned = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^doi:\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip("/ .;")
    match = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", cleaned)
    if match:
        return match.group(0).lower()
    return cleaned.lower() if cleaned.startswith("10.") else None


HARDCODED_EMAIL = "rdndds@gmail.com"


def fetch_crossref_metadata(
    doi: str,
    *,
    email: str = HARDCODED_EMAIL,
    timeout: float = 10.0,
    client: httpx.Client | None = None,
    cache: Any | None = None,
) -> dict[str, Any] | None:
    """Fetch Crossref metadata for a DOI synchronously using HTTPX."""
    norm_doi = normalize_doi(doi)
    if not norm_doi:
        return None

    url = f"https://api.crossref.org/works/{norm_doi}"
    if cache is not None:
        cached = cache.get(url)
        if cached is not None:
            if cached.status_code == 200:
                try:
                    return cached.json().get("message", {})
                except (json.JSONDecodeError, TypeError, AttributeError) as exc:
                    logger.debug(f"Failed to decode cached Crossref json: {exc}")
            return None

    headers = {"User-Agent": f"research-tool/0.1 (mailto:{email})"}

    try:
        if client is not None:
            r = client.get(url, headers=headers, timeout=timeout)
        else:
            with httpx.Client(timeout=timeout, follow_redirects=True) as s:
                r = s.get(url, headers=headers)

        if cache is not None:
            cache.set(url, r.status_code, r.content, content_type="application/json")

        if r.status_code == 200:
            data = r.json()
            return data.get("message", {})
        logger.debug(f"Crossref HTTP {r.status_code} for {norm_doi}")
    except httpx.HTTPError as e:
        logger.debug(f"Crossref HTTP error for {norm_doi}: {e}")
    except Exception as e:  # noqa: BLE001
        logger.debug(f"Crossref unexpected error for {norm_doi}: {e}")
    return None


async def fetch_crossref_metadata_async(
    doi: str,
    *,
    client: httpx.AsyncClient | None = None,
    email: str = HARDCODED_EMAIL,
    timeout: float = 10.0,
    cache: Any | None = None,
) -> dict[str, Any] | None:
    """Fetch Crossref metadata for a DOI asynchronously using HTTPX."""
    norm_doi = normalize_doi(doi)
    if not norm_doi:
        return None

    url = f"https://api.crossref.org/works/{norm_doi}"
    if cache is not None:
        cached = cache.get(url)
        if cached is not None:
            if cached.status_code == 200:
                try:
                    return cached.json().get("message", {})
                except (json.JSONDecodeError, TypeError, AttributeError) as exc:
                    logger.debug(f"Failed to decode cached Crossref json: {exc}")
            return None

    headers = {"User-Agent": f"research-tool/0.1 (mailto:{email})"}

    try:
        if client is not None:
            r = await client.get(url, headers=headers, timeout=timeout)
        else:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as sess:
                r = await sess.get(url, headers=headers)

        if cache is not None:
            cache.set(url, r.status_code, r.content, content_type="application/json")

        if r.status_code == 200:
            data = r.json()
            return data.get("message", {})
        logger.debug(f"Crossref HTTP {r.status_code} for {norm_doi}")
    except httpx.HTTPError as e:
        logger.debug(f"Crossref HTTP error for {norm_doi}: {e}")
    except Exception as e:  # noqa: BLE001
        logger.debug(f"Crossref unexpected error for {norm_doi}: {e}")

    return None
