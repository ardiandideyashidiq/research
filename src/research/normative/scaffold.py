from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from research.bibliography.manager import BibliographyManager
    from research.db.manager import DatabaseManager
    from research.normative.irac import IRACManager
    from research.normative.workflow import WorkflowManager


class ThesisScaffolder:
    """Scaffolder that generates structured 5-chapter skripsi markdown drafts linked to research state."""

    def __init__(
        self,
        db: DatabaseManager,
        workflow: WorkflowManager,
        irac: IRACManager,
        bib: BibliographyManager | None = None,
    ) -> None:
        self.db = db
        self.workflow = workflow
        self.irac = irac
        self.bib = bib

    def generate_draft(
        self,
        output_dir: str | Path = "draft_skripsi",
        project_id: str = "default",
        style: str = "indonesia",
        overwrite: bool = False,
    ) -> dict[str, Path]:
        """Generate 5-chapter thesis Markdown skeleton populated with project data."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        proj = self.workflow.get_project(project_id)
        title = proj.title if proj else "Judul Skripsi Riset Hukum Normatif"
        author = proj.author if proj else "Peneliti"
        questions = (
            proj.research_questions
            if proj and proj.research_questions
            else [
                "Bagaimana kualifikasi yuridis dan rasionalitas norma yang mengatur isu hukum ini?",
                "Bagaimana rekonstruksi pertanggungjawaban hukum dan preskripsi de lege ferenda yang berkeadilan?",
            ]
        )

        grand = (
            proj.grand_theory
            if proj and proj.grand_theory
            else "Teori Keadilan (Aristoteles / John Rawls)"
        )
        middle = (
            proj.middle_theory
            if proj and proj.middle_theory
            else "Teori Sistem Hukum / Teori Positivisme Hukum"
        )
        applied = (
            proj.applied_theory
            if proj and proj.applied_theory
            else "Teori Pertanggungjawaban Hukum / Doktrin Terapan"
        )
        approaches = (
            ", ".join(a.title() for a in proj.approaches)
            if proj and proj.approaches
            else "Statute Approach, Conceptual Approach, Case Approach"
        )
        typology = (
            proj.typology.replace("_", " ").title()
            if proj and proj.typology
            else "Vague Norm / Wet Vacuum"
        )
        principles = (
            ", ".join(proj.principles)
            if proj and proj.principles
            else "Asas Kepastian Hukum, Asas Keadilan, Lex Specialis Derogat Legi Generali"
        )

        generated_files: dict[str, Path] = {}

        # 1. BAB I: PENDAHULUAN
        bab1_path = out / "BAB_I_PENDAHULUAN.md"
        if not bab1_path.exists() or overwrite:
            rq_md = "\n".join(f"{i}. {q}" for i, q in enumerate(questions, start=1))
            bab1_content = f"""---
title: "BAB I: PENDAHULUAN"
skripsi_title: "{title}"
author: "{author}"
---

# BAB I: PENDAHULUAN

## 1.1 Latar Belakang Masalah
<!--
PANDUAN OPERASIONAL (Tahap 1 & 19):
Terapkan teknik PIRAMIDA TERBALIK:
1. Mulai dari norma konstitusi tertinggi (UUD 1945) atau cita hukum Pancasila.
2. Turun ke undang-undang organik dan peraturan teknis yang relevan.
3. Paparkan kesenjangan antara Das Sollen (apa yang dicita-citakan norma) dan Das Sein (fakta/perkembangan nyata).
4. Rumuskan isu hukum yang menunjukkan adanya '{typology}'.
-->

Tatanan hukum nasional yang berlandaskan Pancasila dan Undang-Undang Dasar Negara Republik Indonesia Tahun 1945 menghendaki terwujudnya kepastian hukum yang adil...

Namun demikian, perkembangan dinamika masyarakat menghadirkan ketegangan normatif... *(Uraikan das sollen vs das sein)*.

## 1.2 Rumusan Masalah
Berdasarkan latar belakang yang telah diuraikan, rumusan masalah dalam penelitian hukum normatif ini adalah:
{rq_md}

## 1.3 Tujuan Penelitian
1. Untuk menganalisis dan menemukan kualifikasi yuridis terhadap permasalahan hukum yang diteliti.
2. Untuk memformulasikan konsep preskriptif dan rekomendasi rekonstruksi hukum (*de lege ferenda*).

## 1.4 Manfaat Penelitian
### 1.4.1 Manfaat Teoretis
Memberikan kontribusi bagi pengembangan ilmu hukum dogmatik, khususnya dalam ranah pengayaan doktrin...

### 1.4.2 Manfaat Praktis
Menjadi bahan pertimbangan akademis bagi pembentuk undang-undang (*legislator*) dan aparat penegak hukum (*rechtsvinding*).

## 1.5 Kerangka Teoretis & Konseptual (Three-Tier Theory)
Penelitian ini membedah isu hukum menggunakan tiga lapisan kerangka teoritis:
1. **Grand Theory**: *{grand}* — sebagai landasan nilai filosofis tertinggi.
2. **Middle Range Theory**: *{middle}* — sebagai pisau analisis tatanan norma hukum positif.
3. **Applied Theory**: *{applied}* — sebagai instrumen terapan dalam menilai kasus konkret.

## 1.6 Metode Penelitian Hukum
Penelitian ini merupakan **penelitian hukum normatif (doktrinal)**.
- **Tipologi Problematika**: *{typology}*.
- **Pendekatan (*Legal Approaches*)**: Menggabungkan *{approaches}*.
- **Bahan Hukum**:
  - *Bahan Hukum Primer*: Peraturan Perundang-undangan (Pasal 7 UU 12/2011) dan Yurisprudensi Putusan Pengadilan.
  - *Bahan Hukum Sekunder*: Buku teks, jurnal hukum terakreditasi, dan naskah akademik.
  - *Bahan Hukum Tersier*: Kamus hukum (*Black's Law Dictionary*).
- **Metode Pengolahan & Penalaran**: Sistematisasi dogmatik, metode interpretasi hukum, konstruksi hukum, dan silogisme deduktif model IRAC (*Issue, Rule, Analysis, Conclusion*).
"""
            bab1_path.write_text(bab1_content, encoding="utf-8")
            generated_files["bab1"] = bab1_path

        # 2. BAB II: TINJAUAN PUSTAKA
        bab2_path = out / "BAB_II_TINJAUAN_PUSTAKA.md"
        if not bab2_path.exists() or overwrite:
            bab2_content = f"""---
title: "BAB II: TINJAUAN PUSTAKA / KERANGKA DOKTRINAL"
skripsi_title: "{title}"
---

# BAB II: TINJAUAN PUSTAKA DAN KERANGKA DOKTRINAL

## 2.1 Kerangka Konseptual & Definisi Operasional Istilah Hukum
<!--
PANDUAN OPERASIONAL (Tahap 5):
Definisikan batasan istilah penting agar terhindar dari bias makna.
Rujuk undang-undang resmi, Black's Law Dictionary, atau doktrin terkemuka.
-->

### 2.1.1 Pengertian Dasar Hukum
Subjek hukum, hak dan kewajiban, serta objek hukum dalam ranah penelitian ini dibatasi secara operasional sebagai berikut...

## 2.2 Tinjauan Teoretis Bertingkat
### 2.2.1 {grand}
*(Uraikan prinsip-prinsip filosofis dari grand theory yang dipilih)*

### 2.2.2 {middle}
*(Uraikan struktur norma, doktrin sistematisasi, atau pandangan pakar terkait)*

### 2.2.3 {applied}
*(Uraikan kriteria penerapan teori terapan pada peristiwa hukum)*

## 2.3 Pemetaan Asas-Asas Hukum (*Rechtsbeginselen*)
Asas hukum merupakan pengendap dari hukum positif. Penelitian ini menggunakan standar asas normatif:
- {principles}
"""
            bab2_path.write_text(bab2_content, encoding="utf-8")
            generated_files["bab2"] = bab2_path

        # 3. BAB III & BAB IV: PEMBAHASAN RUMUSAN MASALAH
        # Generate one chapter per research question
        num_q = len(questions)
        for idx, q_text in enumerate(questions, start=1):
            bab_num = idx + 2
            roman_bab = ["III", "IV", "V", "VI", "VII"][idx - 1]
            bab_file_name = f"BAB_{roman_bab}_PEMBAHASAN_{idx}.md"
            bab_path = out / bab_file_name

            if not bab_path.exists() or overwrite:
                # Fetch IRAC syllogisms linked to this research question
                syllogisms = self.irac.list_syllogisms(
                    project_id=project_id, question_idx=idx
                )
                irac_blocks_text = (
                    "\n".join(s.to_irac_markdown() for s in syllogisms)
                    if syllogisms
                    else (
                        "<!-- Tambahkan unit silogisme IRAC menggunakan command:\n"
                        f'     uv run research irac add --issue "..." --rule "..." --facts "..." --conclusion "..." --question-idx {idx}\n-->\n'
                        "*(Belum ada unit silogisme IRAC terdaftar untuk rumusan masalah ini)*"
                    )
                )

                bab_content = f"""---
title: "BAB {roman_bab}: PEMBAHASAN RUMUSAN MASALAH {idx}"
skripsi_title: "{title}"
---

# BAB {roman_bab}: PEMBAHASAN RUMUSAN MASALAH {idx}

## {bab_num}.1 Fokus Masalah: {q_text}

## {bab_num}.2 Analisis Normatif, Kualifikasi & Subsumsi Fakta
<!--
PANDUAN OPERASIONAL (Fase V / Tahap 13-16):
Operasikan penalaran deduktif-silogistik:
Premis Mayor (Rule/Pasal) -> Premis Minor (Fakta Konkret) -> Subsumsi -> Konklusi.
-->

{irac_blocks_text}

## {bab_num}.3 Sintesis Penalaran & Penemuan Hukum (*Rechtsvinding*)
Berdasarkan pengujian silogistik di atas, pertimbangan hukum yang dapat ditarik adalah...
"""
                bab_path.write_text(bab_content, encoding="utf-8")
                generated_files[f"bab_{bab_num}"] = bab_path

        # 4. BAB PENUTUP (Last Chapter)
        penutup_idx = num_q + 3
        roman_penutup = (
            ["IV", "V", "VI", "VII"][num_q - 1] if num_q <= 4 else f"BAB_{penutup_idx}"
        )
        bab_penutup_path = out / f"BAB_{roman_penutup}_PENUTUP.md"

        if not bab_penutup_path.exists() or overwrite:
            bab_penutup_content = f"""---
title: "BAB {roman_penutup}: PENUTUP"
skripsi_title: "{title}"
---

# BAB {roman_penutup}: PENUTUP

## {penutup_idx}.1 Kesimpulan Preskriptif
<!--
PANDUAN OPERASIONAL (Tahap 18 & 20):
Kesimpulan harus menjawab secara tuntas seluruh rumusan masalah yang diajukan di Bab I.
Pastikan setiap poin kesimpulan traceable (dapat dilacak) kembali ke silogisme di Bab III/IV.
-->

Berdasarkan keseluruhan analisis penalaran hukum yang telah dilakukan, dapat disimpulkan bahwa:
1. ... *(Jawaban tuntas Rumusan Masalah 1)*
2. ... *(Jawaban tuntas Rumusan Masalah 2)*

## {penutup_idx}.2 Saran & Rekomendasi (*De Lege Ferenda*)
### {penutup_idx}.2.1 Aspek Rekonstruksi Regulasi (*Ius Constituendum*)
Direkomendasikan kepada pembentuk undang-undang untuk menyusun ketentuan norma baru...

### {penutup_idx}.2.2 Aspek Penegakan & Penemuan Hukum (*Rechtsvinding*)
Bagi aparat penegak hukum dan hakim, disarankan menggunakan metode interpretasi teleologis...
"""
            bab_penutup_path.write_text(bab_penutup_content, encoding="utf-8")
            generated_files["penutup"] = bab_penutup_path

        # 5. DAFTAR PUSTAKA
        dafpus_path = out / "DAFTAR_PUSTAKA.md"
        if not dafpus_path.exists() or overwrite:
            if self.bib:
                try:
                    self.bib.export_bibliography(
                        dafpus_path,
                        style=style,
                        output_format="markdown",
                        limit=500,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.debug(f"Could not auto-export bibliography: {exc}")
                    dafpus_path.write_text(
                        "# DAFTAR PUSTAKA\n\n*(Jalankan 'research bib export --output DAFTAR_PUSTAKA.md' untuk mengisi)*\n",
                        encoding="utf-8",
                    )
            else:
                dafpus_path.write_text(
                    "# DAFTAR PUSTAKA\n\n*(Jalankan 'research bib export --output DAFTAR_PUSTAKA.md' untuk mengisi)*\n",
                    encoding="utf-8",
                )
            generated_files["daftar_pustaka"] = dafpus_path

        logger.info(f"Scaffolded thesis draft files under '{out}'")
        return generated_files
