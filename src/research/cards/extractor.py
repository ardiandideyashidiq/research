from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from research.cards.models import ReviewCard

if TYPE_CHECKING:
    from research.db.models import PublicationRecord


class CardExtractor:
    """Intelligent extractor for literature review elements (Isu Hukum, Teori, Temuan, Gap, Positioning)."""

    def __init__(self, *, max_field_chars: int = 800) -> None:
        self.max_field_chars = max_field_chars

    def extract_from_record(
        self,
        record: PublicationRecord,
        *,
        markdown_text: str | None = None,
    ) -> ReviewCard:
        """Extract structured literature review card from a PublicationRecord and its Markdown content."""
        cite_key = record.cite_key
        corpus = "literature"
        if record.entry_type == "putusan" or "putusan" in record.sources or cite_key.startswith("Putusan_"):
            corpus = "putusan"
        elif record.entry_type == "online" or "web" in record.sources or cite_key.startswith("web_"):
            corpus = "web"

        # Load markdown text if not provided
        md_text = markdown_text
        if not md_text and record.markdown_path:
            p = Path(record.markdown_path)
            if p.is_file():
                try:
                    md_text = p.read_text(encoding="utf-8")
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Failed reading markdown file {}: {}", p, exc)

        if not md_text:
            md_text = record.abstract or record.title

        if corpus == "putusan":
            return self._extract_putusan_card(record, md_text)

        return self._extract_literature_card(record, md_text, corpus=corpus)

    def _extract_putusan_card(
        self,
        record: PublicationRecord,
        md_text: str,
    ) -> ReviewCard:
        """Extract legal review elements from an Indonesian Court Ruling (Putusan)."""
        meta = record.full_metadata or {}
        sections = self._split_markdown_sections(md_text)

        # 1. Isu Hukum (Dari Duduk Perkara atau Kepala Putusan)
        duduk_perkara = sections.get("DUDUK_PERKARA", "")
        kepala = sections.get("KEPALA_PUTUSAN", "")
        identitas = sections.get("IDENTITAS_PIHAK", "")

        isu_parts = []
        if meta.get("klasifikasi"):
            isu_parts.append(f"Klasifikasi Perkara: {meta.get('klasifikasi')}")
        if meta.get("pihak_utama"):
            isu_parts.append(f"Para Pihak: {meta.get('pihak_utama')}")

        dakwaan_match = re.search(
            r"(didakwa\s+melakukan|didakwa\s+bahwa|bahwa\s+terdakwa|gugatan\s+penggugat|pokok\s+perkara)[^\.\n]{20,300}\.",
            duduk_perkara or kepala,
            re.IGNORECASE,
        )
        if dakwaan_match:
            isu_parts.append(dakwaan_match.group(0).strip())
        elif duduk_perkara:
            isu_parts.append(duduk_perkara[:350].strip() + "...")
        elif identitas:
            isu_parts.append(identitas[:250].strip())

        legal_issue = "\n\n".join(isu_parts) or f"Pemeriksaan perkara pada {record.journal or 'Pengadilan'}."

        # 2. Teori & Dasar Hukum (Dari Pertimbangan Hukum)
        pertimbangan = sections.get("PERTIMBANGAN_HUKUM", "")
        pasal_matches = re.findall(
            r"(?:Pasal\s+\d+[A-Za-z0-9\s,\(\)]*(?:KUHP|KUHPerdata|UU\s+[^\.\n]{5,50}))",
            pertimbangan or md_text,
            re.IGNORECASE,
        )
        dasar_hukum = list(dict.fromkeys(p.strip() for p in pasal_matches[:5]))
        theory = ""
        if dasar_hukum:
            theory = "Dasar Hukum: " + "; ".join(dasar_hukum) + "."
        else:
            theory = "Dasar Hukum & Doktrin: Penerapan ketentuan perundang-undangan terkait tindak pidana/perdata materiil."

        # 3. Metodologi / Pembuktian
        methodology = (
            "Analisis Yuridis Yudisial: Pemeriksaan fakta persidangan, pembuktian alat bukti (keterangan saksi, surat, "
            "ahli), dan pemenuhan unsur-unsur pasal dakwaan."
        )

        # 4. Temuan & Amar Putusan
        amar = sections.get("AMAR_PUTUSAN", "")
        if not amar and meta.get("amar_ringkas"):
            amar = meta.get("amar_ringkas")
        if not amar:
            amar_match = re.search(r"(M\s*E\s*N\s*G\s*A\s*D\s*I\s*L\s*I[^\n]{10,600})", md_text, re.IGNORECASE)
            if amar_match:
                amar = amar_match.group(0)

        findings = amar[: self.max_field_chars].strip() if amar else "Amar putusan terlampir dalam salinan resmi."

        # 5. Gap / Kelemahan / Masalah Penerapan Hukum
        gap_parts = []
        if "onvoldoende gemotiveerd" in md_text.lower():
            gap_parts.append("Terdapat dalil putusan kurang pertimbangan hukum (onvoldoende gemotiveerd).")
        if "kekhilafan hakim" in md_text.lower() or "kekeliruan yang nyata" in md_text.lower():
            gap_parts.append("Didalilkan adanya kekhilafan hakim atau kekeliruan nyata dalam penerapan hukum.")
        if not gap_parts:
            gap_parts.append(
                "Tantangan konsistensi penerapan pasal dakwaan dan kepastian pemenuhan hak-hak para pihak."
            )
        gap = " ".join(gap_parts)

        # 6. Positioning / Nilai Preseden
        tingkat = meta.get("tingkat_peradilan") or "Pengadilan"
        positioning = (
            f"Preseden Peradilan ({tingkat}): Menjadi rujukan yurisprudensi terkait pertimbangan hakim "
            f"pada yurisdiksi {record.journal or meta.get('pengadilan')}."
        )

        tags = self._extract_tags(md_text, extra_tags=["putusan", tingkat.lower().replace(" ", "-")])

        return ReviewCard(
            card_id=f"card_{record.cite_key}",
            cite_key=record.cite_key,
            corpus="putusan",
            title=record.title,
            authors=record.authors,
            year=record.year,
            venue=record.journal,
            legal_issue=self._trim(legal_issue),
            theory=self._trim(theory),
            methodology=self._trim(methodology),
            findings=self._trim(findings),
            gap=self._trim(gap),
            positioning=self._trim(positioning),
            tags=tags,
        )

    def _extract_literature_card(
        self,
        record: PublicationRecord,
        md_text: str,
        *,
        corpus: str = "literature",
    ) -> ReviewCard:
        """Extract structured literature review elements from academic papers or web research."""
        sections = self._split_markdown_sections(md_text)

        # 1. Isu Hukum / Permasalahan Penelitian
        legal_issue = self._find_first_pattern(
            md_text,
            [
                r"(?:tujuan\s+penelitian\s+ini|penelitian\s+ini\s+bertujuan|permasalahan\s+yang\s+diangkat|fokus\s+penelitian\s+ini|artikel\s+ini\s+mengkaji|penulisan\s+ini\s+bertujuan)[^\.\n]{20,350}\.",
                r"(?:the\s+purpose\s+of\s+this\s+study|this\s+paper\s+aims\s+to|this\s+article\s+examines|we\s+investigate|the\s+central\s+issue)[^\.\n]{20,350}\.",
            ],
            fallback=sections.get("PENDAHULUAN") or sections.get("INTRODUCTION") or record.abstract or "",
        )

        # 2. Teori / Landasan Konseptual
        theory = self._find_first_pattern(
            md_text,
            [
                r"(?:menggunakan\s+teori|landasan\s+teori|teori\s+yang\s+digunakan|berdasarkan\s+teori|doktrin\s+hukum|asas\s+hukum|pendekatan\s+teoretis)[^\.\n]{20,350}\.",
                r"(?:theoretical\s+framework|grounded\s+in\s+the\s+theory|theory\s+of|doctrine\s+of|legal\s+certainty\s+theory)[^\.\n]{20,350}\.",
            ],
            fallback=sections.get("LANDASAN_TEORI") or sections.get("TINJAUAN_PUSTAKA") or "",
        )
        if not theory:
            # Look for mentioned legal theories or legislation
            laws = re.findall(r"(?:Undang-Undang|UU\s+Nomor|KUHP|KUHPerdata|Civil\s+Code)[^\.\n,]{3,40}", md_text)
            if laws:
                theory = "Kerangka Yuridis & Perundang-undangan: " + ", ".join(list(dict.fromkeys(laws[:4]))) + "."
            else:
                theory = "Kerangka konseptual berbasis analisis asas-asas hukum dan doktrin peraturan perundang-undangan."

        # 3. Metode Penelitian
        methodology = self._find_first_pattern(
            md_text,
            [
                r"(?:metode\s+penelitian\s+yang\s+digunakan|penelitian\s+ini\s+menggunakan\s+metode|jenis\s+penelitian\s+ini|penelitian\s+hukum\s+normatif|yuridis\s+normatif|yuridis\s+empiris)[^\.\n]{20,350}\.",
                r"(?:the\s+research\s+method|normative\s+legal\s+research|empirical\s+legal|statutory\s+approach|methodology\s+employed)[^\.\n]{20,350}\.",
            ],
            fallback=sections.get("METODE_PENELITIAN") or sections.get("METHODS") or "",
        )
        if not methodology:
            if "normatif" in md_text.lower():
                methodology = "Penelitian hukum yuridis normatif dengan pendekatan perundang-undangan dan konseptual."
            elif "empiris" in md_text.lower():
                methodology = "Penelitian hukum yuridis empiris dengan analisis data lapangan dan perundang-undangan."
            else:
                methodology = "Penelitian doktrinal/studi kepustakaan (library research) terhadap bahan hukum primer dan sekunder."

        # 4. Temuan Utama / Argumen
        findings = self._find_first_pattern(
            md_text,
            [
                r"(?:hasil\s+penelitian\s+menunjukkan\s+bahwa|dapat\s+disimpulkan\s+bahwa|temuan\s+penelitian\s+ini|pembahasan\s+menunjukkan\s+bahwa|penulis\s+berpendapat\s+bahwa)[^\.\n]{20,400}\.",
                r"(?:the\s+findings\s+reveal\s+that|results\s+indicate\s+that|we\s+conclude\s+that|this\s+study\s+finds\s+that)[^\.\n]{20,400}\.",
            ],
            fallback=sections.get("KESIMPULAN") or sections.get("CONCLUSION") or sections.get("HASIL_DAN_PEMBAHASAN") or "",
        )
        if not findings and record.abstract:
            findings = record.abstract[:350]

        # 5. Research Gap / Kekurangan Regulasi
        gap = self._find_first_pattern(
            md_text,
            [
                r"(?:kekosongan\s+hukum|kekosongan\s+norma|belum\s+ada\s+pengaturan|belum\s+mengatur\s+secara\s+khusus|kelemahan\s+regulasi|ketidakpastian\s+hukum|kelemahan\s+dalam\s+penegakan|masih\s+terdapat\s+kendala)[^\.\n]{20,350}\.",
                r"(?:regulatory\s+gap|lacuna\s+in\s+the\s+law|lack\s+of\s+specific\s+regulation|unresolved\s+legal|open\s+question|limitation\s+of\s+current)[^\.\n]{20,350}\.",
            ],
            fallback="",
        )
        if not gap:
            gap = "Kekosongan regulasi komprehensif dan perlunya reformulasi ketentuan hukum positif terkait tantangan kontemporer."

        # 6. Positioning & Kontribusi
        positioning = self._find_first_pattern(
            md_text,
            [
                r"(?:kebaruan\s+penelitian|kontribusi\s+penelitian\s+ini|berbeda\s+dengan\s+penelitian|artikel\s+ini\s+memberikan\s+kontribusi|kebaruan\s+\(novelty\))[^\.\n]{20,350}\.",
                r"(?:this\s+paper\s+contributes\s+to|the\s+novelty\s+of\s+this\s+research|distinguishes\s+itself\s+from|unlike\s+prior\s+work)[^\.\n]{20,350}\.",
            ],
            fallback="",
        )
        if not positioning:
            positioning = f"Menawarkan analisis yuridis kritis dan rekomendasi kebijakan regulasi dalam domain {record.title[:60]}."

        tags = self._extract_tags(md_text, extra_tags=[corpus])

        return ReviewCard(
            card_id=f"card_{record.cite_key}",
            cite_key=record.cite_key,
            corpus=corpus,
            title=record.title,
            authors=record.authors,
            year=record.year,
            venue=record.journal,
            legal_issue=self._trim(legal_issue),
            theory=self._trim(theory),
            methodology=self._trim(methodology),
            findings=self._trim(findings),
            gap=self._trim(gap),
            positioning=self._trim(positioning),
            tags=tags,
        )

    def _split_markdown_sections(self, md_text: str) -> dict[str, str]:
        """Split markdown into named sections based on H1/H2 headings."""
        sections: dict[str, str] = {}
        heading_pat = re.compile(r"^(?:#{1,3})\s+(.*)$", re.MULTILINE)
        matches = list(heading_pat.finditer(md_text))

        for i, match in enumerate(matches):
            raw_title = match.group(1).strip()
            # Canonicalize key
            key = re.sub(r"[^A-Za-z0-9]+", "_", raw_title.upper()).strip("_")
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(md_text)
            content = md_text[start:end].strip()

            if "PENDAHULUAN" in key or "INTRODUCTION" in key or "LATAR_BELAKANG" in key:
                sections["PENDAHULUAN"] = content
            elif "TEORI" in key or "PUSTAKA" in key or "THEORY" in key:
                sections["LANDASAN_TEORI"] = content
            elif "METODE" in key or "METHOD" in key:
                sections["METODE_PENELITIAN"] = content
            elif "HASIL" in key or "PEMBAHASAN" in key or "FINDINGS" in key or "DISCUSSION" in key:
                sections["HASIL_DAN_PEMBAHASAN"] = content
            elif "KESIMPULAN" in key or "CONCLUSION" in key or "PENUTUP" in key:
                sections["KESIMPULAN"] = content
            elif "DUDUK_PERKARA" in key:
                sections["DUDUK_PERKARA"] = content
            elif "PERTIMBANGAN" in key:
                sections["PERTIMBANGAN_HUKUM"] = content
            elif "AMAR" in key:
                sections["AMAR_PUTUSAN"] = content
            elif "IDENTITAS" in key:
                sections["IDENTITAS_PIHAK"] = content
            elif "KEPALA" in key:
                sections["KEPALA_PUTUSAN"] = content

            sections[key] = content

        return sections

    def _find_first_pattern(
        self,
        text: str,
        patterns: list[str],
        *,
        fallback: str = "",
    ) -> str:
        """Find the first matching regex pattern in text, with fallback."""
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                clean = re.sub(r"\s+", " ", m.group(0)).strip()
                if len(clean) > 25:
                    return clean
        if fallback:
            # Clean and return first sentence or chunk of fallback
            paras = [p.strip() for p in fallback.split("\n\n") if len(p.strip()) > 30]
            if paras:
                clean = re.sub(r"\s+", " ", paras[0]).strip()
                return clean[: self.max_field_chars]
        return ""

    def _extract_tags(self, text: str, *, extra_tags: list[str] | None = None) -> list[str]:
        """Extract thematic legal and domain tags from text."""
        tags = set(extra_tags or [])
        keyword_map = {
            "pidana": ["tindak pidana", "hukum pidana", "kriminal", "kejahatan", "penjara"],
            "perdata": ["perdata", "gugatan", "wanprestasi", "perbuatan melawan hukum", "pmh"],
            "ai": ["artificial intelligence", "kecerdasan buatan", "deepfake", "algoritma"],
            "uu-ite": ["uu ite", "informasi dan transaksi elektronik", "cybercrime", "elektronik"],
            "korupsi": ["korupsi", "tipikor", "penyuapan", "gratifikasi"],
            "pembuktian": ["alat bukti", "pembuktian", "saksi", "alat bukti elektronik"],
            "hakim": ["pertimbangan hakim", "judex facti", "kasasi", "mahkamah agung"],
            "perlindungan-data": ["perlindungan data", "hak privasi", "data pribadi"],
        }
        text_lower = text.lower()
        for tag, words in keyword_map.items():
            if any(w in text_lower for w in words):
                tags.add(tag)
        return sorted(tags)

    def _trim(self, text: str) -> str:
        """Trim text cleanly to max_field_chars."""
        s = re.sub(r"\s+", " ", text).strip()
        if len(s) > self.max_field_chars:
            return s[: self.max_field_chars].rstrip() + "..."
        return s
