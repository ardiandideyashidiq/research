from __future__ import annotations

import re
from html import unescape
from urllib.parse import urljoin

from research.ojs.models import OJSMetadata


def extract_ojs_metadata(html: str, base_url: str) -> OJSMetadata:
    """Extract Open Journal Systems metadata from page HTML."""
    raw_meta: dict[str, list[str]] = {}

    # Extract all <meta> tags with name/content or property/content
    meta_tags = re.findall(
        r"""<meta\s+[^>]*?(?:name|property)\s*=\s*['"]([^'"]+)['"][^>]*?content\s*=\s*['"]([^'"]*)['"][^>]*>""",
        html,
        re.IGNORECASE,
    )
    # Also handle content before name
    meta_tags += re.findall(
        r"""<meta\s+[^>]*?content\s*=\s*['"]([^'"]*)['"][^>]*?(?:name|property)\s*=\s*['"]([^'"]+)['"][^>]*>""",
        html,
        re.IGNORECASE,
    )

    for item in meta_tags:
        # Check ordering of group 1 and 2
        name, content = item if len(item[0]) < len(item[1]) or "." in item[0] or "_" in item[0] else (item[1], item[0])
        name = name.strip().lower()
        content = unescape(content.strip())
        raw_meta.setdefault(name, []).append(content)

    generator = " ".join(raw_meta.get("generator", [])).lower()
    has_ojs_meta = any(k.startswith("citation_") for k in raw_meta) or "open journal systems" in generator
    is_ojs_url = any(p in base_url for p in ["/article/view/", "/article/download/", "index.php"])
    is_ojs = has_ojs_meta or is_ojs_url or "pkp" in html.lower()

    # Extract title
    title = None
    if raw_meta.get("citation_title"):
        title = raw_meta["citation_title"][0]
    elif raw_meta.get("dc.title"):
        title = raw_meta["dc.title"][0]
    else:
        title_m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if title_m:
            title = re.sub(r"\s+", " ", unescape(title_m.group(1))).strip()

    # Extract authors
    authors: list[str] = []
    if "citation_author" in raw_meta:
        authors = [a for a in raw_meta["citation_author"] if a]
    elif "dc.creator.personalname" in raw_meta:
        authors = [a for a in raw_meta["dc.creator.personalname"] if a]
    elif "dc.creator" in raw_meta:
        authors = [a for a in raw_meta["dc.creator"] if a]

    # Journal title
    journal = None
    if raw_meta.get("citation_journal_title"):
        journal = raw_meta["citation_journal_title"][0]
    elif raw_meta.get("dc.source"):
        journal = raw_meta["dc.source"][0]

    # Publication date and year
    pub_date = None
    if raw_meta.get("citation_publication_date"):
        pub_date = raw_meta["citation_publication_date"][0]
    elif raw_meta.get("citation_date"):
        pub_date = raw_meta["citation_date"][0]
    elif raw_meta.get("dc.date.created"):
        pub_date = raw_meta["dc.date.created"][0]
    elif raw_meta.get("dc.date.issued"):
        pub_date = raw_meta["dc.date.issued"][0]

    year = None
    if pub_date:
        year_m = re.search(r"\b(19\d\d|20\d\d)\b", pub_date)
        if year_m:
            year = int(year_m.group(1))

    # Volume and issue
    volume = raw_meta.get("citation_volume", [None])[0]
    issue = raw_meta.get("citation_issue", [None])[0]
    firstpage = raw_meta.get("citation_firstpage", [None])[0]
    lastpage = raw_meta.get("citation_lastpage", [None])[0]

    # DOI
    doi = None
    if raw_meta.get("citation_doi"):
        doi = raw_meta["citation_doi"][0]
    elif raw_meta.get("dc.identifier.doi"):
        doi = raw_meta["dc.identifier.doi"][0]

    # Abstract
    abstract = None
    if raw_meta.get("dc.description"):
        abstract = raw_meta["dc.description"][0]
    else:
        abs_m = re.search(
            r"""<(?:div|section|p)[^>]*?(?:class|id)=['"][^'"]*?abstract[^'"]*?['"][^>]*>(.*?)</(?:div|section|p)>""",
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if abs_m:
            raw_abs = re.sub(r"<[^>]+>", " ", abs_m.group(1))
            cleaned_abs = re.sub(r"\s+", " ", unescape(raw_abs)).strip()
            if len(cleaned_abs) > 20:
                abstract = cleaned_abs

    # PDF direct download URL
    pdf_url = None
    if raw_meta.get("citation_pdf_url"):
        pdf_url = urljoin(base_url, raw_meta["citation_pdf_url"][0])

    # Galley links in HTML
    galley_matches = re.findall(
        r"""href=['"]([^'"]*(?:/article/view/[^'"]+/[^'"]+|/article/download/[^'"]+))['"]""",
        html,
        re.IGNORECASE,
    )
    galley_urls = [urljoin(base_url, g) for g in galley_matches]

    # If no pdf_url was in meta, try deriving from galley link
    if not pdf_url and galley_urls:
        for g_url in galley_urls:
            if "/article/download/" in g_url:
                pdf_url = g_url
                break
            if "/article/view/" in g_url:
                # OJS /article/view/{article_id}/{galley_id} -> /article/download/{article_id}/{galley_id}
                derived = re.sub(r"/article/view/(\d+/\d+)", r"/article/download/\1", g_url)
                if derived != g_url:
                    pdf_url = derived
                    break

    return OJSMetadata(
        url=base_url,
        is_ojs=is_ojs,
        title=title,
        authors=authors,
        journal_title=journal,
        publication_date=pub_date,
        year=year,
        doi=doi,
        volume=volume,
        issue=issue,
        firstpage=firstpage,
        lastpage=lastpage,
        abstract=abstract,
        pdf_url=pdf_url,
        galley_urls=galley_urls,
        raw_meta=raw_meta,
    )
