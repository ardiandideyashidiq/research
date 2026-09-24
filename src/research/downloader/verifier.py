from __future__ import annotations

import hashlib


def compute_file_hash(data: bytes) -> str:
    """Compute SHA-256 hash of byte data."""
    return hashlib.sha256(data).hexdigest()


def inspect_content(data: bytes) -> tuple[bool, str]:
    """Inspect binary content to verify if it is a valid PDF or another file type.

    Returns:
        (is_pdf: bool, content_type: str)
    """
    if len(data) == 0:
        return False, "empty"

    # Check magic bytes for PDF: %PDF-
    if data.startswith(b"%PDF"):
        return True, "application/pdf"

    # Also check if %PDF appears in the first 1024 bytes (some servers prepend UTF-8 BOM or whitespace)
    if b"%PDF-" in data[:1024]:
        return True, "application/pdf"

    # Microsoft Word / Office magic bytes (OLE2 CFBF or OOXML zip)
    if data.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return False, "application/msword"
    if data.startswith(b"PK\x03\x04") and (b"word/" in data[:4096] or b"[Content_Types].xml" in data[:1024]):
        return False, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    # Check HTML
    start_chunk = data[:512].lower().strip()
    if start_chunk.startswith((b"<!doctype html", b"<html")) or b"<body" in start_chunk:
        return False, "text/html"

    return False, "application/octet-stream"


def classify_error(
    status_code: int | None,
    exception: Exception | None,
    target_url: str,
) -> tuple[str, str]:
    """Carefully classify failure causes to eliminate false positives for dead links.

    Returns:
        (status_string: str, diagnostic_detail: str)
    """
    if status_code in (404, 410):
        # 404/410 explicitly returned by webserver: link is dead
        return "dead_link", f"HTTP {status_code}: Resource permanently not found at {target_url}"

    if status_code in (401, 403):
        return "failed_blocked", f"HTTP {status_code}: Access denied / Cloudflare or IP block at {target_url}"

    if status_code is not None and 500 <= status_code <= 599:
        # Server-side failure (PHP crash, database connection error, 502 bad gateway)
        # MUST NOT be marked as dead link because the paper exists, host is having downtime
        return "failed_server_error", f"HTTP {status_code}: Host server error at {target_url} (manual retry later)"

    if exception is not None:
        err_str = str(exception).lower()
        if "timed out" in err_str or "timeout" in err_str:
            # Network latency / server slow: transient failure, NOT a dead link!
            return "failed_timeout", f"Connection timed out: {exception}"
        if "could not resolve host" in err_str or "name or service not known" in err_str:
            return "dead_link", f"DNS resolution failed (domain expired or offline): {exception}"
        if "connection refused" in err_str or "reset by peer" in err_str:
            return "failed_server_error", f"Connection refused/reset by server: {exception}"

        return "failed_network", f"Network error: {exception}"

    if status_code is not None:
        return "failed", f"Unexpected HTTP status {status_code} for {target_url}"

    return "failed", f"Unknown download failure for {target_url}"
