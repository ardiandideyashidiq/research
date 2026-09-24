from __future__ import annotations

import re

SPACED_LEGAL_KEYWORDS = [
    ("MAHKAMAH AGUNG", r"\bM\s*A\s*H\s*K\s*A\s*M\s*A\s*H\s+A\s*G\s*U\s*N\s*G\b"),
    ("MAHKAMAH KONSTITUSI", r"\bM\s*A\s*H\s*K\s*A\s*M\s*A\s*H\s+K\s*O\s*N\s*S\s*T\s*I\s*T\s*U\s*S\s*I\b"),
    ("PUTUSAN", r"\bP\s*U\s*T\s*U\s*S\s*A\s*N\b"),
    ("PENETAPAN", r"\bP\s*E\s*N\s*E\s*T\s*A\s*P\s*A\s*N\b"),
    ("MENGADILI", r"\bM\s*E\s*N\s*G\s*A\s*D\s*I\s*L\s*I\b"),
    ("MENIMBANG", r"\bM\s*E\s*N\s*I\s*M\s*B\s*A\s*N\s*G\b"),
    ("MENGINGAT", r"\bM\s*E\s*N\s*G\s*I\s*N\s*G\s*A\s*T\b"),
    ("MEMPERHATIKAN", r"\bM\s*E\s*M\s*P\s*E\s*R\s*H\s*A\s*T\s*I\s*K\s*A\s*N\b"),
    ("DEMI KEADILAN", r"\bD\s*E\s*M\s*I\s+K\s*E\s*A\s*D\s*I\s*L\s*A\s*N\b"),
    ("DUDUK PERKARA", r"\bD\s*U\s*D\s*U\s*K\s+P\s*E\s*R\s*K\s*A\s*R\s*A\b"),
    ("PERTIMBANGAN HUKUM", r"\bP\s*E\s*R\s*T\s*I\s*M\s*B\s*A\s*N\s*G\s*A\s*N\s+H\s*U\s*K\s*U\s*M\b"),
    ("AMAR PUTUSAN", r"\bA\s*M\s*A\s*R\s+P\s*U\s*T\s*U\s*S\s*A\s*N\b"),
    ("KONKLUSI", r"\bK\s*O\s*N\s*K\s*L\s*U\s*S\s*I\b"),
    ("EKSEPSI", r"\bE\s*K\s*S\s*E\s*P\s*S\s*I\b"),
    ("REPLIK", r"\bR\s*E\s*P\s*L\s*I\s*K\b"),
    ("DUPLIK", r"\bD\s*U\s*P\s*L\s*I\s*K\b"),
    ("TERDAKWA", r"\bT\s*E\s*R\s*D\s*A\s*K\s*W\s*A\b"),
    ("PENGGUGAT", r"\bP\s*E\s*N\s*G\s*G\s*U\s*G\s*A\s*T\b"),
    ("TERGUGAT", r"\bT\s*E\s*R\s*G\s*U\s*G\s*A\s*T\b"),
    ("PEMOHON", r"\bP\s*E\s*M\s*O\s*H\s*O\s*N\b"),
    ("TERMOHON", r"\bT\s*E\s*R\s*M\s*O\s*H\s*O\s*N\b"),
    ("PENGADU", r"\bP\s*E\s*N\s*G\s*A\s*D\s*U\b"),
    ("TERADU", r"\bT\s*E\s*R\s*A\s*D\s*U\b"),
]

WATERMARK_PATTERNS = [
    re.compile(r"^hkama$", re.IGNORECASE),
    re.compile(r"^ahkamah(?:\s+Agung(?:\s+Repub(?:lik(?:\s+Indonesia)?)?)?)?$", re.IGNORECASE),
    re.compile(r"^mah\s+Agung(?:\s+Republik(?:\s+Indonesia)?)?$", re.IGNORECASE),
    re.compile(r"^blik\s+Indonesi(?:a)?$", re.IGNORECASE),
    re.compile(r"Direktori\s+Putusan\s+Mahkamah\s+Agung\s+Republik\s+Indonesia", re.IGNORECASE),
    re.compile(r"putusan\.mahkamahagung\.go\.id", re.IGNORECASE),
    re.compile(r"SALINAN\s+PUTUSAN\s+DEWAN\s+KEHORMATAN\s+PENYELENGGARA\s+PEMILU", re.IGNORECASE),
    re.compile(r"Diunduh\s+dari\s+laman\s*:\s*www\.dkpp\.go\.id", re.IGNORECASE),
]


def strip_page_watermarks_and_disclaimers(page_text: str) -> str:
    """Remove Direktori Putusan MA watermarks, disclaimers, and repeating page artifacts."""
    lines = page_text.split("\n")
    cleaned_lines: list[str] = []
    in_disclaimer_block = False

    for line in lines:
        s = line.strip()

        # Check for disclaimer start
        if re.match(r"^Disclaimer\b", s, re.IGNORECASE):
            in_disclaimer_block = True
            continue

        if in_disclaimer_block:
            # Disclaimer block ends on telephone/page marker or empty line after details
            if (
                re.search(r"Telp\s*:", s, re.IGNORECASE)
                or re.search(r"kepaniteraan@mahkamahagung\.go\.id", s, re.IGNORECASE)
                or re.match(r"^Halaman\s+\d+", s, re.IGNORECASE)
            ):
                in_disclaimer_block = False
            continue

        # Check watermark patterns
        if any(pat.search(s) for pat in WATERMARK_PATTERNS):
            continue

        # Check page markers like 'Halaman 1 dari 28 halaman Putusan Nomor 1466 K/Pid/2024'
        if re.match(r"^Halaman\s+\d+(\s+dari\s+\d+.*)?$", s, re.IGNORECASE):
            continue

        # Standalone digits on first/last line representing page number
        if re.match(r"^\d{1,4}$", s) and (len(cleaned_lines) <= 1 or len(cleaned_lines) >= len(lines) - 2):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def normalize_spaced_typography(text: str) -> str:
    """Normalize widely spaced letters (P U T U S A N -> PUTUSAN, M E N G A D I L I -> MENGADILI)."""
    for normalized, pattern in SPACED_LEGAL_KEYWORDS:
        text = re.sub(pattern, normalized, text, flags=re.IGNORECASE)

    # General spaced uppercase words (e.g. 'P E M I L I H A N' -> 'PEMILIHAN')
    def _collapse_spaced(match: re.Match[str]) -> str:
        s = match.group(0)
        # Collapse single spaces between capital letters
        collapsed = re.sub(r"(?<=[A-Z])\s+(?=[A-Z])", "", s)
        return collapsed

    # Match isolated spaced words: at least 4 letters separated by spaces
    text = re.sub(r"\b([A-Z]\s+){3,}[A-Z]\b", _collapse_spaced, text)
    return text


def reflow_hanging_colons(text: str) -> str:
    """Fix court table format where colon and value are placed on newlines.

    Example:
    Nama lengkap
    :
    HELENA;
    -> Nama lengkap: HELENA;
    """
    # 1. Label followed by standalone colon on next line
    text = re.sub(
        r"([A-Za-z0-9\(\)\/\-\.\,\s]{2,40})\n\s*:\s*\n([^\n]+)",
        r"\1: \2",
        text,
    )
    # 2. Label with colon at end of line followed by value on next line (if value isn't a new field)
    text = re.sub(
        r"([A-Za-z0-9\(\)\/\-\.\,\s]{2,40}):\s*\n\s*([A-Za-z0-9][^\n]{1,80}(?:;|,|\.))\n",
        r"\1: \2\n",
        text,
    )
    return text


def dehyphenate_legal_text(text: str) -> str:
    """Rejoin Indonesian words split by line-wrap hyphens (e.g., 'seba-\ngaimana' -> 'sebagaimana')."""
    return re.sub(r"([A-Za-z]{2,})-\n\s*([a-z]{2,})", r"\1\2", text)


def normalize_bullets(text: str) -> str:
    """Convert non-standard decorative bullet glyphs to markdown dashes."""
    bullets = ["", "", "", "", "", "", "–", "—", "•"]
    for b in bullets:
        text = text.replace(b, "- ")
    # Clean multiple spaces after bullet
    text = re.sub(r"^-\s{2,}", "- ", text, flags=re.MULTILINE)
    return text


def normalize_putusan_text(page_texts: list[str]) -> list[str]:
    """Execute end-to-end normalization on all pages of a putusan document."""
    cleaned_pages: list[str] = []

    for page_text in page_texts:
        if not page_text or not page_text.strip():
            cleaned_pages.append("")
            continue

        # 1. Watermark and disclaimer removal
        text = strip_page_watermarks_and_disclaimers(page_text)

        # 2. Typography unspacing
        text = normalize_spaced_typography(text)

        # 3. Hanging colon table reflow
        text = reflow_hanging_colons(text)

        # 4. Dehyphenation
        text = dehyphenate_legal_text(text)

        # 5. Bullet normalization
        text = normalize_bullets(text)

        # 6. Compress excessive empty lines
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        cleaned_pages.append(text)

    return cleaned_pages
