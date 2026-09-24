from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

# 7 Phases and 20 Stages definition from workflow.md
PHASE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "I": {
        "title": "Identifikasi & Tipologisasi Isu Hukum",
        "stages": [1, 2, 3, 4],
    },
    "II": {
        "title": "Desain Kerangka Teoritis, Konseptual & Asas Hukum",
        "stages": [5, 6, 7],
    },
    "III": {
        "title": "Pengumpulan & Inventarisasi Bahan Hukum",
        "stages": [8, 9, 10],
    },
    "IV": {
        "title": "Pengolahan, Validasi & Sistematisasi Bahan Hukum",
        "stages": [11, 12],
    },
    "V": {
        "title": "Penalaran Hukum, Interpretasi & Penemuan Hukum",
        "stages": [13, 14, 15, 16],
    },
    "VI": {
        "title": "Formulasi Preskripsi, Argumentasi & Solusi Hukum",
        "stages": [17, 18],
    },
    "VII": {
        "title": "Penulisan, Review Kualitas & Finalisasi Skripsi",
        "stages": [19, 20],
    },
}

STAGE_DEFINITIONS: dict[int, dict[str, Any]] = {
    1: {
        "phase": "I",
        "title": "Penelusuran Pendahuluan & Identifikasi Isu Hukum",
        "checklist": [
            "Apakah isu yang ditemukan murni masalah hukum normatif (mengenai norma/kaidah) dan bukan sekadar masalah pelaksanaan empiris?",
            "Apakah isu memiliki relevansi akademis dan dapat diuji berdasarkan logika hukum?",
        ],
    },
    2: {
        "phase": "I",
        "title": "Tipologisasi Problematika Hukum (Norm Typology)",
        "checklist": [
            "Teridentifikasi dengan tegas apakah isu termasuk vague norm, wet vacuum, atau conflict van normen?",
            "Apakah instrumen penafsiran/konstruksi disesuaikan dengan problematika normanya?",
        ],
    },
    3: {
        "phase": "I",
        "title": "Pemilihan & Kombinasi Pendekatan Penelitian Hukum",
        "checklist": [
            "Apakah pendekatan yang dipilih minimal 2 (Statute, Conceptual, Case, Historical, Comparative, Philosophical)?",
            "Apakah pendekatan saling melengkapi untuk menjawab rumusan masalah?",
        ],
    },
    4: {
        "phase": "I",
        "title": "Formulasi Rumusan Masalah Akademis & Preskripsi Awal",
        "checklist": [
            "Rumusan masalah tidak menggunakan kata tanya empiris (berapa banyak, bagaimana efektivitas)?",
            "Pertanyaan berfokus pada analisis kualitatif normatif preskriptif?",
        ],
    },
    5: {
        "phase": "II",
        "title": "Penentuan Kerangka Konseptual & Definisi Operasional",
        "checklist": [
            "Seluruh batasan konsep dirumuskan secara eksplisit dan konsisten sesuai kaidah hukum?",
            "Istilah mendasar merujuk pada undang-undang atau kamus hukum standar (Black's Law)?",
        ],
    },
    6: {
        "phase": "II",
        "title": "Konstruksi Kerangka Teoritis Bertingkat (3-Tier Theory)",
        "checklist": [
            "Apakah teori fungsional sebagai pangkalan berpikir, bukan sekadar dekoratif?",
            "Terdapat korelasi logis dari Grand Theory, Middle Range Theory, hingga Applied Theory?",
        ],
    },
    7: {
        "phase": "II",
        "title": "Penelusuran & Pemetaan Asas-Asas Hukum",
        "checklist": [
            "Asas-asas hukum yang menjadi standar normatif telah diklasifikasikan dengan jernih?",
            "Asas digunakan sebagai instrumen untuk menilai norma positif (das sollen)?",
        ],
    },
    8: {
        "phase": "III",
        "title": "Inventarisasi & Pemetaan Bahan Hukum Primer",
        "checklist": [
            "Semua peraturan perundang-undangan versi resmi dan masih berlaku positif (ius constitutum)?",
            "Pengurutan bahan hukum primer taat pada hierarki Pasal 7 UU 12/2011 dan Yurisprudensi?",
        ],
    },
    9: {
        "phase": "III",
        "title": "Pengumpulan Bahan Hukum Sekunder & Tersier",
        "checklist": [
            "Literatur sekunder merupakan publikasi ilmiah bereputasi dan mutakhir?",
            "Bahan non-hukum berada pada koridor pendukung analisis yuridis, bukan menggantikan?",
        ],
    },
    10: {
        "phase": "III",
        "title": "Teknik Pengumpulan Bahan Hukum (Card System & Snowball)",
        "checklist": [
            "Bahan hukum tercatat lengkap beserta identitas bibliografinya?",
            "Teknik bola salju (snowballing) telah mencapai titik jenuh (saturasi bahan hukum)?",
        ],
    },
    11: {
        "phase": "IV",
        "title": "Pengujian Otoritas & Hierarki Norma (Lex Principles)",
        "checklist": [
            "Apakah ada norma pasal yang sudah dibatalkan oleh Judicial Review MK/MA?",
            "Penerapan adagium Lex (superior, posterior, specialis) tepat pada pasal yang berkonflik?",
        ],
    },
    12: {
        "phase": "IV",
        "title": "Editing, Klasifikasi & Sistematisasi Bahan Hukum",
        "checklist": [
            "Bahan hukum primer dan sekunder terstruktur rapi sesuai kerangka bab pembahasan?",
            "Eliminasi terhadap bahan hukum yang tidak relevan telah selesai dilakukan?",
        ],
    },
    13: {
        "phase": "V",
        "title": "Kualifikasi & Subsumsi Fakta Hukum ke Peristilahan Yuridis",
        "checklist": [
            "Seluruh fakta non-hukum yang tidak berpengaruh pada akibat hukum telah dieliminasi?",
            "Penerjemahan fakta konkret ke terminologi yuridis akurat secara dogmatis?",
        ],
    },
    14: {
        "phase": "V",
        "title": "Penerapan Metode Interpretasi Hukum (Penafsiran)",
        "checklist": [
            "Metode penafsiran (gramatikal, teleologis, sistematis, dll) didasari alasan akademis yang tepat?",
            "Penafsiran menjaga koherensi dengan sistem hukum secara keseluruhan?",
        ],
    },
    15: {
        "phase": "V",
        "title": "Penerapan Metode Konstruksi Hukum (Penemuan Hukum)",
        "checklist": [
            "Menghormati batasan hukum pidana yang melarang analogi (nullum crimen sine lege)?",
            "Konstruksi hukum (a contrario, rechtsverfijning, fiksi) logis dan memenuhi nilai keadilan?",
        ],
    },
    16: {
        "phase": "V",
        "title": "Pengoperasian Logika Hukum & Argumentasi (IRAC / Silogisme)",
        "checklist": [
            "Silogisme terhindar dari cacat pangkalan berpikir (fallacy) dan analysis jump?",
            "Kesimpulan ditarik koheren secara mutlak dari premis mayor dan premis minor?",
        ],
    },
    17: {
        "phase": "VI",
        "title": "Pembangunan Argumentasi Yuridis Komprehensif",
        "checklist": [
            "Argumentasi bebas dari subjektivitas tanpa dasar doktrinal?",
            "Argumentasi mampu menangkis pandangan-pandangan kontra (counter-arguments)?",
        ],
    },
    18: {
        "phase": "VI",
        "title": "Perumusan Preskripsi Hukum & Rekomendasi (De Lege Ferenda)",
        "checklist": [
            "Solusi yang ditawarkan bersifat konkrit, operasional, dan dapat diterapkan (applicable)?",
            "Preskripsi menjawab secara tuntas seluruh rumusan masalah?",
        ],
    },
    19: {
        "phase": "VII",
        "title": "Penyusunan Laporan Penelitian (Sistematika Skripsi Bab I-V)",
        "checklist": [
            "Laporan bebas dari istilah riset empiris (populasi, sampel, responden)?",
            "Gaya bahasa adalah bahasa hukum akademis yang lugas dan baku?",
        ],
    },
    20: {
        "phase": "VII",
        "title": "Evaluasi Kebenaran Koherensi, Traceability & Peer Review",
        "checklist": [
            "Kebenaran logika koherensi teruji dari Bab I hingga Bab V?",
            "Setiap klaim didukung pangkalan bahan hukum primer/sekunder yang sah (no fabrication)?",
            "Menghasilkan preskripsi yang orisinal dan bernilai kebaruan (novelty)?",
        ],
    },
}


@dataclass
class NormativeProject:
    """Project tracker record representing an ongoing normative legal research project."""

    project_id: str
    title: str
    author: str = ""
    typology: str = ""  # 'vague_norm', 'wet_vacuum', 'conflict_van_normen'
    approaches: list[str] = field(
        default_factory=list
    )  # ['statute', 'conceptual', 'case', ...]
    research_questions: list[str] = field(default_factory=list)
    grand_theory: str = ""
    middle_theory: str = ""
    applied_theory: str = ""
    principles: list[str] = field(default_factory=list)
    current_stage: int = 1
    gate_checks: dict[str, bool] = field(
        default_factory=dict
    )  # {"1": True, "2": False, ...}
    stage_notes: dict[str, str] = field(
        default_factory=dict
    )  # {"1": "Catatan...", ...}
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> NormativeProject:
        def _parse_json(val: Any, default: Any) -> Any:
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    return default
            return val if val is not None else default

        return cls(
            project_id=row["project_id"],
            title=row.get("title", ""),
            author=row.get("author") or "",
            typology=row.get("typology") or "",
            approaches=_parse_json(row.get("approaches"), []),
            research_questions=_parse_json(row.get("research_questions"), []),
            grand_theory=row.get("grand_theory") or "",
            middle_theory=row.get("middle_theory") or "",
            applied_theory=row.get("applied_theory") or "",
            principles=_parse_json(row.get("principles"), []),
            current_stage=int(row.get("current_stage") or 1),
            gate_checks=_parse_json(row.get("gate_checks"), {}),
            stage_notes=_parse_json(row.get("stage_notes"), {}),
            created_at=row.get("created_at") or datetime.now(UTC).isoformat(),
            updated_at=row.get("updated_at") or datetime.now(UTC).isoformat(),
        )

    def is_stage_completed(self, stage_num: int) -> bool:
        return bool(self.gate_checks.get(str(stage_num), False))

    def completed_count(self) -> int:
        return sum(1 for v in self.gate_checks.values() if v)

    def progress_percentage(self) -> float:
        return (self.completed_count() / 20.0) * 100.0


@dataclass
class LegalSyllogism:
    """Formal deductive legal syllogism (IRAC) unit."""

    syllogism_id: str
    project_id: str
    issue: str
    rule_major: str  # Premis Mayor (p)
    facts_minor: str  # Premis Minor (q)
    conclusion: str  # Konklusi Preskriptif (r)
    research_question_idx: int = 1
    legal_domain: str = (
        "umum"  # 'pidana', 'perdata', 'tata_negara', 'administrasi', 'umum'
    )
    method_type: str = "interpretasi_gramatikal"  # 'interpretasi_*', 'analogi', 'a_contrario', 'rechtsverfijning', 'fiksi'
    cite_keys: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> LegalSyllogism:
        cite_keys = row.get("cite_keys")
        if isinstance(cite_keys, str):
            try:
                cite_keys = json.loads(cite_keys)
            except (json.JSONDecodeError, TypeError):
                cite_keys = [k.strip() for k in cite_keys.split(",") if k.strip()]
        elif cite_keys is None:
            cite_keys = []

        return cls(
            syllogism_id=row["syllogism_id"],
            project_id=row.get("project_id", "default"),
            research_question_idx=int(row.get("research_question_idx") or 1),
            issue=row.get("issue", ""),
            rule_major=row.get("rule_major", ""),
            facts_minor=row.get("facts_minor", ""),
            legal_domain=row.get("legal_domain", "umum"),
            method_type=row.get("method_type", "interpretasi_gramatikal"),
            conclusion=row.get("conclusion", ""),
            cite_keys=cite_keys,
            created_at=row.get("created_at") or datetime.now(UTC).isoformat(),
            updated_at=row.get("updated_at") or datetime.now(UTC).isoformat(),
        )

    def validate_logic(self) -> list[str]:
        """Validate syllogism according to normative legal logic rules. Returns warning list."""
        warnings: list[str] = []
        # Tahap 15 check: Analogy prohibited in criminal law
        domain_clean = self.legal_domain.lower().strip()
        method_clean = self.method_type.lower().strip()
        if "pidana" in domain_clean and "analogi" in method_clean:
            warnings.append(
                "VIOLATION [Tahap 15]: Metode Analogi dilarang keras dalam Hukum Pidana berdasarkan "
                "Asas Legalitas (nullum crimen sine lege praevia lege stricta)."
            )

        if not self.rule_major.strip():
            warnings.append("WARNING: Premis Mayor (Rule/Norma) kosong.")
        if not self.facts_minor.strip():
            warnings.append("WARNING: Premis Minor (Fakta yuridis) kosong.")
        if not self.conclusion.strip():
            warnings.append("WARNING: Konklusi preskriptif belum dirumuskan.")

        return warnings

    def to_irac_markdown(self) -> str:
        """Format syllogism as an IRAC markdown section for Bab III / Bab IV."""
        cite_str = (
            ", ".join(f"`{k}`" for k in self.cite_keys) if self.cite_keys else "—"
        )
        return f"""#### IRAC: {self.issue}
- **Bidang Hukum**: `{self.legal_domain.upper()}` | **Metode**: `{self.method_type}` | **Rujukan**: {cite_str}
- **I (Issue)**: {self.issue}
- **R (Rule / Premis Mayor)**:
  > {self.rule_major}
- **A (Analysis & Subsumsi / Premis Minor)**:
  {self.facts_minor}
- **C (Conclusion / Simpulan Preskriptif)**:
  {self.conclusion}
"""


@dataclass
class AuditReport:
    """Report generated by TraceabilityAuditor comparing draft against DB."""

    draft_dir: str
    total_files_scanned: int = 0
    total_citations_found: int = 0
    unique_cite_keys: list[str] = field(default_factory=list)
    verified_cite_keys: list[str] = field(default_factory=list)
    ghost_cite_keys: list[str] = field(
        default_factory=list
    )  # In text, but missing in DB
    unused_db_keys: list[str] = field(default_factory=list)  # In DB, but not in text
    statute_mentions: list[str] = field(default_factory=list)
    court_mentions: list[str] = field(default_factory=list)
    traceability_chains: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Render report as a markdown document."""
        verified_pct = (
            (len(self.verified_cite_keys) / len(self.unique_cite_keys) * 100.0)
            if self.unique_cite_keys
            else 100.0
        )
        status_badge = (
            "✅ PASSED" if not self.ghost_cite_keys else "❌ ATTENTION NEEDED"
        )

        md = [
            f"# Laporan Audit Traceability & Kontrol Kebenaran Ilmiah ({status_badge})",
            f"*Direktori Draf*: `{self.draft_dir}` | *File Dipindai*: {self.total_files_scanned}",
            "",
            "## 1. Ringkasan Keterlacakan Sitasi (Traceability Summary)",
            f"- **Total Sitasi Ditemukan**: {self.total_citations_found}",
            f"- **Sitasi Unik**: {len(self.unique_cite_keys)}",
            f"- **Sitasi Terverifikasi di Database**: {len(self.verified_cite_keys)} ({verified_pct:.1f}%)",
            f"- **Sitasi Hantu (Ghost / Tidak Ada di DB)**: {len(self.ghost_cite_keys)}",
            f"- **Referensi di DB Belum Dikutip**: {len(self.unused_db_keys)}",
            "",
        ]

        if self.ghost_cite_keys:
            md.extend(
                [
                    "### ⚠️ Peringatan: Sitasi Hantu (Ghost Citations / Missing from DB)",
                    "Sitasi berikut ditemukan dalam naskah tetapi tidak memiliki rekaman bibliografi sah di database:",
                    "",
                ]
            )
            for k in self.ghost_cite_keys:
                md.append(f"- ❌ `{k}`")
            md.append("")

        if self.statute_mentions:
            md.extend(
                [
                    "## 2. Inventarisasi Peraturan Perundang-undangan Disebut (Bahan Primer)",
                    f"Ditemukan {len(self.statute_mentions)} rujukan pasal/undang-undang dalam teks:",
                    "",
                ]
            )
            for s in sorted(set(self.statute_mentions))[:20]:
                md.append(f"- 📜 {s}")
            if len(self.statute_mentions) > 20:
                md.append(f"- *... dan {len(self.statute_mentions) - 20} lainnya.*")
            md.append("")

        if self.court_mentions:
            md.extend(
                [
                    "## 3. Inventarisasi Putusan Pengadilan Disebut (Yurisprudensi)",
                    f"Ditemukan {len(self.court_mentions)} rujukan putusan:",
                    "",
                ]
            )
            for c in sorted(set(self.court_mentions)):
                md.append(f"- ⚖️ {c}")
            md.append("")

        if self.warnings:
            md.extend(
                [
                    "## 4. Catatan & Rekomendasi Kualitas Ilmiah (Tahap 20 Gate Check)",
                    "",
                ]
            )
            for w in self.warnings:
                md.append(f"- ⚠️ {w}")
            md.append("")

        return "\n".join(md)
