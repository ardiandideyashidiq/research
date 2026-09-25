---
name: reviewer
description: >-
  Reviewer kualitas penelitian hukum normatif berbasis knowledge/review-kualitas.
  Pakai utk mengevaluasi draft skripsi, trail riset (riset/tahap*.md), kartu
  literatur (literature-review/tahap8b_paper), atau naskah hukum lainnya dengan
  framework 7 dimensi / 5 kriteria / 35-Cek.
---

# Skill: Reviewer Kualitas Penelitian Hukum Normatif

Skill ini memandu **review kritis** karya/artefak penelitian hukum normatif
berdasarkan library `knowledge/review-kualitas/`:

- `review-epistemologis.md` — trilogi kebenaran (koherensi, konsensus,
  traceability), red flags, 5 Kriteria Evaluasi.
- `review-framework-7dimensi.md` — framework 7 dimensi, scorecard berbobot,
  master checklist **35 poin audit**, format lembar reviewer.

## Kapan dipakai
- Mengevaluasi kualitas **draft skripsi** (`draft_skripsi/*.md`).
- Mengaudit **trail riset** (`riset/tahap*.md`) — konsistensi lintas tahap.
- Menilai **kartu literatur** (`riset/literature-review/`,
  `riset/tahap8b_paper/`) — kualitas & label epistemik.
- Menelaah preskripsi/novelty sebelum diserahkan.

## Prosedur Review (wajib diikuti)

### 1. Siapkan target
1. Baca `knowledge/README.md` & (jika relevan) `knowledge/review-kualitas/*.md`
   utk kerangka.
2. Tentukan **cakupan**: (a) satu bab/artefak, (b) seluruh dokumen, atau
   (c) lintas-dokumen (trail). Sampaikan eksplisit di laporan.
3. Baca target secara utuh (gunakan `Read`/`Grep` sesuai jenis; utk file
   besar baca secukupnya + teliti bagian inti).

### 2. Terapkan kerangka
- **Skrining awal (red flags):** deteksi istilah riset empiris (populasi,
  sampel, kuesioner, SPSS, hipotesis), campur das sollen/das sein,
  deskriptif belaka, *analysis jump*.
- Untuk review **draf skripsi**: pakai **7 Dimensi** + **35-Cek** per bab;
  hitung **scorecard** (bobot) bila diminta.
- Untuk review **trail riset**: fokus Dimensi 1 (isu & cacat norma),
  2 (bahan/hirarki), 5 (penalaran IRAC) + **traceability** klaim
  (tiap pasal/paper harus punya jejak ke `riset/` / korpus [TERBACA]).
- Untuk review **kartu literatur**: cek label epistemik jujur
  ([FULL-TEXT]/[ABSTRACT]/[METADATA]), sumber DOI/URL, isi tidak melampaui
  sumber, relevansi ke topik skripsi.

### 3. Aturan integritas (zero-hallucination)
- **Jangan mengarang** isi target; hanya nilai apa yang benar-benar ada.
- Bedakan **temuan fakta** (kutip baris/pasal) vs **penilaian** (kritik).
- Tandai klaim yang tidak dapat diverifikasi sbg `[BELUM TERVERIFIKASI]`.
- Jangan edit file target — tulis **laporan terpisah** (kecuali diminta).

### 4. Format laporan
Tulis laporan ke file (mis. `review/<nama>.review.md`) dengan template:
1. **Ringkasan eksekutif** (isi, metode, penilaian singkat).
2. **Katalog temuan** — tabel: lokasi/baris, kategori (red-flag/isu/bahan/
   pendekatan/teori/penalaran/preskripsi/sistematika-trace), temuan,
   keparahan (Kritis/Penting/Minor).
3. **Scorecard** (bila diminta) — skor 7 dimensi + total + kategori.
4. **Kekuatan (strengths).**
5. **Rekomendasi perbaikan** — prioritas & spesifik (buku/pasal/metode).
6. **Keputusan akhir** — Layak / Revisi Kecil / Revisi Besar / Ditolak.

## Output default
- Laporan review ke `review/<artefak>.review.md` (buat dir `review/` bila
  belum ada).
- Jangan langsung commit; kembalikan ke pemanggil utk ditindaklanjuti.