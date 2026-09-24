from __future__ import annotations

import re
from typing import TYPE_CHECKING

from research.putusan.models import LegalSectionType, PutusanSection

if TYPE_CHECKING:
    from research.putusan.models import PutusanMetadata


# Heading patterns for legal sections
SECTION_TRIGGER_PATTERNS = [
    # AMAR PUTUSAN (Highest priority near the end)
    (
        LegalSectionType.AMAR_PUTUSAN,
        re.compile(
            r"^(?:MENGADILI(?:\s+SENDIRI)?|(?:\d+\.|\bTENTANG\s+)?AMAR\s+PUTUSAN|M\s*E\s*M\s*U\s*T\s*U\s*S\s*K\s*A\s*N)\s*:?$",
            re.IGNORECASE,
        ),
    ),
    # PENUTUP
    (
        LegalSectionType.PENUTUP,
        re.compile(
            r"^(?:Demikianlah?\s+diputuskan|Demikian\s+diputuskan|Demikian\s+ditetapkan|Demikian\s+Putusan\s+ini)",
            re.IGNORECASE,
        ),
    ),
    # PERTIMBANGAN HUKUM (Ratio Decidendi)
    (
        LegalSectionType.PERTIMBANGAN_HUKUM,
        re.compile(
            r"^(?:(?:\d+\.|\bTENTANG)\s+)?PERTIMBANGAN\s+HUKUM(?:NYA)?\s*:?$|"
            r"^(?:TENTANG\s+)?HUKUMNYA\s*:?$|"
            r"^\d+\.\s+KONKLUSI\s*:?$|"
            r"^MENIMBANG\s+BAHWA\s+TERHADAP\s+ALASAN(?:-ALASAN)?\s+KASASI|"
            r"^MENIMBANG\s+BAHWA\s+MAHKAMAH\s+AGUNG\s+BERPENDAPAT|"
            r"^MENIMBANG,\s+BAHWA\s+TERHADAP\s+UNSUR-UNSUR|"
            r"^MENIMBANG,\s+BAHWA\s+BERDASARKAN\s+FAKTA-FAKTA\s+HUKUM|"
            r"^MENIMBANG,\s+BAHWA\s+SELANJUTNYA\s+MAJELIS\s+(?:HAKIM\s+)?AKAN\s+MEMPERTIMBANGKAN",
            re.IGNORECASE,
        ),
    ),
    # DUDUK PERKARA (Posita, Dakwaan, Tuntutan, Pembuktian)
    (
        LegalSectionType.DUDUK_PERKARA,
        re.compile(
            r"^(?:(?:\d+\.|\bTENTANG)\s+)?DUDUK(?:NYA)?\s+PERKARA\s*:?$|"
            r"^TENTANG\s+DAKWAAN\s*:?$|"
            r"^SETELAH\s+MENDENGAR\s+PEMBACAAN\s+TUNTUTAN\s+PIDANA|"
            r"^MEMBACA\s+(?:SURAT\s+)?(?:DAKWAAN|TUNTUTAN\s+PIDANA)|"
            r"^MENIMBANG,\s+BAHWA\s+TERDAKWA\s+DIHADAPKAN\s+KE\s+PERSIDANGAN|"
            r"^MENIMBANG,\s+BAHWA\s+PENGGUGAT\s+DALAM\s+SURAT\s+GUGATANNYA|"
            r"^MENIMBANG,\s+BAHWA\s+UNTUK\s+MEMBUKTIKAN\s+DAKWAANNYA",
            re.IGNORECASE,
        ),
    ),
    # IDENTITAS PIHAK
    (
        LegalSectionType.IDENTITAS_PIHAK,
        re.compile(
            r"^\d+\.\s+IDENTITAS\s*:?$|"
            r"^(?:Terdakwa|TERDAKWA)\s*:?$|"
            r"^(?:antara|ANTARA)\s*:?$|"
            r"^Telah\s+menjatuhkan\s+putusan\s+dalam\s+perkara\s*:?$|"
            r"^dalam\s+perkara\s+(?:Terdakwa\s*)?:?$",
            re.IGNORECASE,
        ),
    ),
]


def segment_putusan(
    pages_text: list[str],
    metadata: PutusanMetadata | None = None,
) -> list[PutusanSection]:
    """Segment a Putusan document into structured legal sections with page boundaries."""
    total_pages = len(pages_text)
    if total_pages == 0:
        return []

    # Milestones state machine
    current_sec = LegalSectionType.KEPALA_PUTUSAN
    current_title = "Kepala Putusan & Identitas"
    sec_start_page = 1
    collected_blocks: list[str] = []
    sections: list[PutusanSection] = []
    seen_pertimbangan = False

    for page_idx, page_content in enumerate(pages_text):
        page_num = page_idx + 1
        lines = page_content.split("\n")

        for line in lines:
            s = line.strip()
            if not s:
                continue

            # Skip inline quotes and evidence citations
            if s.startswith(("“", '"')) or "vide Bukti" in s or "Vide Bukti" in s:
                continue

            detected_sec: LegalSectionType | None = None
            detected_title = s

            # Match against known section patterns
            for sec_type, pat in SECTION_TRIGGER_PATTERNS:
                if pat.search(s):
                    # Guard AMAR PUTUSAN: must not trigger prematurely in early pages
                    if (
                        sec_type == LegalSectionType.AMAR_PUTUSAN
                        and not seen_pertimbangan
                        and page_num < (total_pages * 0.5)
                    ):
                        continue
                    # Guard IDENTITAS: must only trigger near the beginning
                    if sec_type == LegalSectionType.IDENTITAS_PIHAK and (
                        page_num > 4
                        or current_sec
                        not in [
                            LegalSectionType.KEPALA_PUTUSAN,
                            LegalSectionType.IDENTITAS_PIHAK,
                        ]
                    ):
                        continue
                    # Guard DUDUK PERKARA: must not trigger after PERTIMBANGAN HUKUM
                    if sec_type == LegalSectionType.DUDUK_PERKARA and current_sec in [
                        LegalSectionType.PERTIMBANGAN_HUKUM,
                        LegalSectionType.AMAR_PUTUSAN,
                        LegalSectionType.PENUTUP,
                    ]:
                        continue

                    detected_sec = sec_type
                    if sec_type == LegalSectionType.PERTIMBANGAN_HUKUM:
                        seen_pertimbangan = True
                    break

            if detected_sec and detected_sec != current_sec:
                # Flush previous section
                sec_text = "\n".join(collected_blocks).strip()
                if sec_text:
                    sections.append(
                        PutusanSection(
                            section_type=current_sec,
                            title=current_title,
                            page_start=sec_start_page,
                            page_end=max(sec_start_page, page_num - 1),
                            content=sec_text,
                        )
                    )
                # Switch to new section
                current_sec = detected_sec
                current_title = detected_title[:80]
                sec_start_page = page_num
                collected_blocks = []

        collected_blocks.append(page_content)

    # Flush final section
    sec_text = "\n".join(collected_blocks).strip()
    if sec_text:
        sections.append(
            PutusanSection(
                section_type=current_sec,
                title=current_title,
                page_start=sec_start_page,
                page_end=total_pages,
                content=sec_text,
            )
        )

    # Fallback: If document was not partitioned, create single section
    if not sections:
        sections.append(
            PutusanSection(
                section_type=LegalSectionType.LAINNYA,
                title="Isi Putusan",
                page_start=1,
                page_end=total_pages,
                content="\n\n".join(pages_text),
            )
        )

    return sections
