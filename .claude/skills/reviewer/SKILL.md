---
name: reviewer
description: >-
  Reviews Indonesian normative/doctrinal legal research artifacts (thesis
  drafts, riset workflow trails, literature review cards) against the
  knowledge/review-kualitas frameworks (7 dimensions, 5 criteria, 35-Cek
  checklist, weighted scorecard). Use when the user asks to review, audit, or
  quality-check a legal-analysis document, draft skripsi chapters, or research
  trail files for coherence, traceability, or methodological rigor.
---

# Reviewer: Kualitas Penelitian Hukum Normatif

Review artefak hukum normatif dengan kerangka pada
`knowledge/review-kualitas/review-epistemologis.md` (trilogi kebenaran **dan**
5 kriteria) serta `knowledge/review-kualitas/review-framework-7dimensi.md`
(7 dimensi + scorecard + 35-Cek). Baca kedua file itu saat skill dipakai.

## Alur review (ceklist — salin & tandai)

```
Review Progress:
- [ ] 1. Tentukan cakupan (bab/artefak / seluruh dokumen / lintas-trail)
- [ ] 2. Skrining awal red flags (istilah empiris, campur das sein/das sollen,
         deskriptif belaka, analysis jump)
- [ ] 3. Telusuri konsistensi lintas artefak (pasal [TERBACA], KUHP 2-1-2026+
         UU 1/2026, PDP 66 jo. 68, label epistemik)
- [ ] 4. Nilai 7 dimensi + hitung scorecard (bobot 15/15/10/15/25/10/10)
- [ ] 5. Tulis laporan ke review/<artefak>.review.md
```

## Cek wajib per jenis artefak

**Draf skripsi (`draft_skripsi/*.md`):**
- 35-Cek per bab; cek **sitasi inline & keterhubungan DAFTAR PUSTAKA** (0
  ghost-citation; tak ada duplikat/entri non-topik).
- **Tanda [PERLU VERIFIKASI] di teks** utk premis belum terverifikasi (mis.
  efek UU 1/2026 pada 407/622/172, putusan inkracht, PP 40(6)).
- **Subsumsi IRAC per unsur** (bestanddelen), urutan interpretasi, dan
  tertium comparationis utk pendekatan perbandingan.

**Trail riset (`riset/tahap*.md`):**
- Konsistensi lintas tahap: tipologi; sanksi **PDP 66 jo. 68** (bukan 67);
  **KUHP efektif 2-1-2026 + UU 1/2026**; label epistemik paper konsisten
  antar-artefak (mis. matriks/literature_matrix.md).
- Jejak klaim: tiap pasal memiliki [TERBACA] / kartu `riset/pasal/*`; putusan
  punya nomor & inkracht terverifikasi.

**Kartu literatur (`riset/literature-review/`, `riset/tahap8b_paper/`):**
- Label jujur ([FULL-TEXT]/[ABSTRACT]/[METADATA]) sesuai isi; sumber (DOI/URL)
  valid; isi tidak melampaui sumber (anti-halusinasi); relevansi ke topik.

## Format laporan (template)

```markdown
# Laporan Review — <artefak>
1. Ringkasan eksekutif (isu, metode, skor)
2. Katalog temuan — tabel: lokasi/baris, kategori, temuan, keparahan
   (Kritis/Penting/Minor) / atau Positif
3. Scorecard (7 dimensi, bobot, skor, terbobot, total, kategori)
4. Kekuatan (strengths)
5. Rekomendasi perbaikan (prioritas; spesifik: buku/pasal/metode)
6. Keputusan akhir — Layak / Revisi Kecil / Revisi Besar / Ditolak
```

## Integritas

- Hanya nilai yang benar-benar ada; kutip baris/file utk tiap temuan.
- Bedakan temuan fakta vs penilaian; klaim tak terverifikasi → tandai
  `[BELUM TERVERIFIKASI]`.
- Jangan edit artefak target — tulis laporan terpisah di `review/`.
- Keputusan akhir gunakan ambang skorckard: 86–100 Sangat Layak ·
  70–85 Revisi · <70 Ditolak.