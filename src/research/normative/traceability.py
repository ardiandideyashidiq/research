from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from research.normative.models import AuditReport

if TYPE_CHECKING:
    from research.db.manager import DatabaseManager


class TraceabilityAuditor:
    """Static text auditor for legal thesis drafts verifying citation traceability and checking against DB."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def audit_drafts(
        self,
        draft_dir: str | Path = "draft_skripsi",
        output_report_path: str | Path | None = None,
    ) -> AuditReport:
        """Scan markdown draft files in draft_dir and audit citation traceability against database records."""
        d_path = Path(draft_dir)
        report = AuditReport(draft_dir=str(d_path))

        if not d_path.exists() or not d_path.is_dir():
            report.warnings.append(f"Direktori draf '{d_path}' tidak ditemukan.")
            return report

        # 1. Fetch all known cite_keys from database
        conn = self.db.get_connection()
        cursor = conn.cursor()
        pub_keys = {
            row[0]
            for row in cursor.execute("SELECT cite_key FROM publications").fetchall()
            if row[0]
        }
        card_keys = {
            row[0]
            for row in cursor.execute("SELECT cite_key FROM review_cards").fetchall()
            if row[0]
        }
        all_db_keys = pub_keys | card_keys

        # 2. Regex patterns
        # Cite keys: @CiteKey2025, [@CiteKey2025], `CiteKey2025`
        cite_pattern = re.compile(r"@([A-Za-z0-9_-]+)|`([A-Za-z0-9_-]+)`")
        # Statutory citations: Pasal X UU No Y Tahun Z, Pasal X KUHP, etc.
        statute_pattern = re.compile(
            r"\b(Pasal\s+\d+(?:\s+ayat\s+\(\d+\))?(?:\s+huruf\s+[a-z])?(?:\s+(?:UU|KUHP|KUHPerdata|KUHAP|Perpu|PP|Perpres|UUD\s+1945)[^\n\.,;]*)*)",
            re.IGNORECASE,
        )
        # Court decisions: Putusan MA / MK / PN / etc.
        court_pattern = re.compile(
            r"\b(Putusan\s+(?:MA|MK|PN|PT|PTUN|MKMK|PA|PM)\s+(?:No\.|Nomor)?\s*[^\n\.,;]+)",
            re.IGNORECASE,
        )

        all_found_keys: list[str] = []
        md_files = sorted(d_path.glob("*.md"))
        report.total_files_scanned = len(md_files)

        for mf in md_files:
            if mf.name.startswith("audit_report") or mf.name == "DAFTAR_PUSTAKA.md":
                continue  # Skip audit report itself and raw bib list

            content = mf.read_text(encoding="utf-8")

            # Extract citations
            for match in cite_pattern.finditer(content):
                at_key = match.group(1)
                code_key = match.group(2)
                if at_key and len(at_key) >= 3 and not at_key.isdigit():
                    all_found_keys.append(at_key)
                elif code_key and len(code_key) >= 3 and code_key in all_db_keys:
                    all_found_keys.append(code_key)

            # Extract statutes
            for sm in statute_pattern.finditer(content):
                s_text = sm.group(1).strip()
                if len(s_text) > 8:
                    report.statute_mentions.append(s_text)

            # Extract courts
            for cm in court_pattern.finditer(content):
                c_text = cm.group(1).strip()
                if len(c_text) > 10:
                    report.court_mentions.append(c_text)

        report.total_citations_found = len(all_found_keys)
        unique_keys = sorted(set(all_found_keys))
        report.unique_cite_keys = unique_keys

        # Determine verified vs ghost citations
        report.verified_cite_keys = [k for k in unique_keys if k in all_db_keys]
        report.ghost_cite_keys = [k for k in unique_keys if k not in all_db_keys]
        report.unused_db_keys = sorted(all_db_keys - set(report.verified_cite_keys))

        # Check for quality rules
        if report.ghost_cite_keys:
            report.warnings.append(
                f"Ditemukan {len(report.ghost_cite_keys)} sitasi hantu yang tidak tercatat di database bibliografi. "
                "Tambahkan referensi tersebut melalui 'research bib add' atau 'research bib import' untuk mencegah fabrikasi rujukan."
            )

        if not report.statute_mentions:
            report.warnings.append(
                "Tidak ditemukan rujukan pasal perundang-undangan eksplisit (Bahan Hukum Primer) di draf naskah. "
                "Penelitian hukum normatif wajib mengkaji norma positif (Tahap 8 & Tahap 11)."
            )

        if output_report_path:
            out_p = Path(output_report_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(report.to_markdown(), encoding="utf-8")
            logger.info(f"Audit report saved to {out_p}")

        return report
