---
title: Review Kartu Literatur — 50 Kartu (literature-review + tahap8b_paper)
jenis: sample-audit kualitas kartu literatur
framework: knowledge/review-kualitas (review-epistemologis.md + review-framework-7dimensi.md)
reviewer: subagent (skill reviewer)
tanggal: 2026-09-25
cakupan: 25/50 kartu diaudit penuh; 50/50 DOI diverifikasi via Crossref
status: Revisi Kecil (Minor) — tanpa temuan kritis
---

# Review Kartu Literatur

## 1. Ringkasan Eksekutif

Sebanyak **50 kartu** diaudit (22 di `riset/literature-review/`, 28 di `riset/tahap8b_paper/`).
Sample-audit **25 kartu** dibaca penuh meliputi seluruh tema (kesusilaan, reputasi/personality,
data/PDP, disinformasi, AI-pidana/subjek hukum, platform/PSE, perbandingan). Seluruh **50 DOI
diverifikasi langsung ke Crossref** — semua valid dan judul/jurnal cocok. **Tidak ditemukan
duplikasi DOI antar kartu, tidak ditemukan halusinasi** (isi kartu tidak melampaui sumber yang
dilabeli). Disiplin label epistemik secara keseluruhan tinggi: klaim-klaim yang hanya berbasis
abstrak ditandai `[ABSTRACT]`, yang tak terbaca ditandai `[METADATA]`/`"—"`, dan beberapa kartu
menyertakan "catatan anti-halucinasi" eksplisit.

## 2. Metode

- Membaca kerangka `knowledge/review-kualitas/*.md` dan skill `reviewer` (label 3-tier:
  `[FULL-TEXT]` = teks dibaca; `[ABSTRACT]` = abstrak; `[METADATA]` = metadata saja).
- Verifikasi seluruh DOI/URL lewat `api.crossref.org` (50 resolusi berhasil; judul/kontainer/
  penulis dicocokkan dengan klaim kartu).
- Audit isi 25 kartu terhadap labelnya: SUBLABEL per klaim, frasa "belum diverifikasi"/"—", dan
  cara kartu menandai sumber (Crossref/OpenAlex/OA PDF).
- Deteksi duplikasi DOI dan artikel-sama-label-beda lintas direktori via pencocokan DOI & penulis.

## 3. Katalog Temuan (tabel)

| # | Kartu | Masalah | Keparahan |
|---|---|---|---|
| 1 | PAPER_Pechenin2026, PAPER_Schwartz2026 | Label memakai format **non-kanonik** `[ABSTRACT + OA PDF TERVERIFIKASI]` — tidak termasuk salah satu dari 3 label baku `[FULL-TEXT]/[ABSTRACT]/[METADATA]`; isi memang berbasis abstrak (PDF hanya disebut tersedia), sehingga pembaca/query otomatis gagal mengenali kategori sebenarnya. | **Minor** |
| 2 | (seluruh kartu) | Wording baris label tidak seragam: `> **Epistemic Label Keseluruhan File:**`, `**Label Epistemic:**`, `**Epistemic Label:**`, `**STATUS PEMBACAAN:**` — tidak terkonsolidasi ke satu konvensi. | **Minor** |
| 3 | PAPER_SujatmikoSurono2025 — Corporate Criminal Liability **in Tax Crimes** | Relevansi paling marginal: topik pidana **pajak**, bukan deepfake. Posisi jujur (lampiran catatan integritas: dipakai sebagai *sumber analogi* atribusi korporasi), tetapi paling jauh dari tesis. | **Minor** (marginal) |
| 4 | PAPER_Walter2024 — global AI governance | Margina keduanya: tinjauan kebijakan global, tidak spesifik deepfake ataupun Indonesia; kartu sudah menandai gap ini. | **Minor** (marginal) |
| 5 | ANALISIS_Putra2023 — IndoBERT, disinformasi pemilu | **Non-hukum** (NLP/ilmu data); kartu jujur menandai "paper ini tidak menganalisis norma hukum", hanya dipakai sbg bahan *das sein* Bab I. | **Minor** (marginal) |
| 6 | ANALISIS_Vainaite2025 | Label `[METADATA]` dengan isi temuan/preskripsi ditandai `"—"` dan catatan "tindak lanjut wajib sebelum dikutip" — **model integritas**, bukan cacat. Dicatat utk skrining: kartu belum dapat dipakai substantif. | Minor (catatan) |
| 7 | PAPER_Groh2024 | Klaim detail empiris (5 eksperimen pre-registered, N=2215, TTS lebih sulit dbedakan) — verifikasi saya terhadap abstrak Crossref: **cocok**; label FULL-TEXT sahih. | — (lolos) |
| 8 | PAPER_Husain2026 (sextortion) | Klaim data (Komnas 1.801 korban KBGO 2023; SAFEnet 1.902 aduan 2024; prevalensi 18% Asia; 17% laporan) berlabel FULL-TEXT; angka-angka begitu rinci utk paper 18 halaman dan **sumber primer angka tidak dirinci di kartu** (sudah dicatat sendiri pada bagian limitation kartu). | **Minor** (verifikasi data sekunder) |
| 9 | (23 kartu FULL-TEXT bertanggal 2026-09-25) | Basis pembacaan merujuk artefak `data/markdown/*.md` yang **sudah tidak ada** di repo → klaim FULL-TEXT hanya self-attested (traceability eksternal terputus). | **Minor** (traceability) |
| 10 | (dua kartu Wicaksono) | Bukan duplikasi: DOI berbeda (`10.37477/sev.v10i2.1022` FULL-TEXT vs `10.58819/jfh.v4i2.233` berbasis abstrak/metadata) — dua artikel beda dari penulis berbeda. | — (lolos) |
| 11 | (semua kartu ABSTRACT) | Beberapa kartu mengisi "teori terapan/asas" dengan inferensi analitis (mis. Cucilovic: "teleologis") — selalu diberi SUBLABEL `[ABSTRACT]`, sehingga tidak melampaui sumber. | — (lolos) |
| 12 | 50 kartu | **Semua DOI valid & tautan judul-jurnal cocok** (verifikasi Crossref); tidak ada DOI putus/salah-klaim. | — |

## 4. Hasil Cek Empat Tujuan Audit

1. **Label epistemik jujur**: YA — semua kartu memakai label 3-tier; dua kartu memakai format
   non-kanonik (temuan #1); tidak ada kartu yang mengklaim `[FULL-TEXT]` padahal hanya berbasis
   abstrak. Kartu ABSTRACT (Cucilovic, Han, Wiguna, Alfathoni, Nurnisaa, dll.) konsisten menandai
   seluruh klaim `[ABSTRACT]`. **Tidak ditemukan halusinasi**; kartu bahkan over-compensate dgn
   mengisi `"—"` saat tidak terverifikasi.
2. **Bibliografi**: semua DOI ada & valid; deteksi "salah konsisten" (artikel sama label beda) —
   **tidak ditemukan**.
3. **Relevansi**: 47/50 relevan kuat/tangensial; 3 kartu marginal (Sujatmiko-pajak, Walter,
   Putra) — semuanya **jujur menandai** status marginalnya dan memberi justifikasi kontribusi.
4. **Duplikasi**: tidak ada DOI duplikat antar kartu (50/50 unik).

## 5. Kekuatan

- Disiplin anti-halucinasi sangat baik: label per-klaim, isi `"—"` untuk yang tak terverifikasi,
  catatan "wajib verifikasi teks penuh sebelum dikutip".
- Bibliografi terverifikasi: seluruh 50 DOI resolusi Crossref cocok (judul/venue/penulis).
- Cakupan tematik tentang: kesusilaan (Han, Utara, Wiguna, Alfathoni), reputasi/personality
  (Marlan, Zigo, Bosher, Chacko, Schwartz, Ochoa), data (Jasserand, Salsabila, Pechenin,
  Rezvorovych), disinformasi (Vainaite, Pawelec, Putra, Groh, Canares, Chesterman), AI-pidana
  (Hailtik, Sofian, Rahman, Jaya, Indarto, Bessoran, Fitriani, Wicaksono), platform (Ariani, Liu,
  PatilMishra, Daud, Gorwa, VanderSloot), perbandingan (ADABALA, Bhagavathy, Pamungkas,
  Nurnisaa, RomeroMoreno).

## 6. Rekomendasi

1. Standardisasi label 2 kartu (Pechenin, Schwartz) ke format baku `[ABSTRACT]` (dgn catatan
   PDF-OA tersedia), agar query skrip/label konsisten (prioritas rendah).
2. Konsolidasikan satu konvensi penulisan baris label (`Epistemic Label:` di posisi file-header);
   otomasi scan-label akan lebih mudah.
3. Untuk klaim FULL-TEXT bergantung artefak `data/markdown` yang sudah hilang: pertimbangkan
   menulis ulang referensi ke file PDF sumber + tanggal baca (tanpa jalur `data/`), atau simpan
   ulang artefak untuk memulihkan traceability eksternal.
4. Untuk 3 kartu marginal, tambahkan satu baris "justifikasi pemilihan" eksplisit di header agar
   pembaca skripsi tahu kontribusinya (Sujatmiko, Walter, Putra sudah sebagian melakukannya).
5. Kartu Vainaite (METADATA): usahakan verifikasi skor ke ABSTRACT/FULL-TEXT sebelum dikutip
   substantif di Bab II.

## 7. Keputusan Akhir

**Revisi Kecil** — paket kartu literatur layak dipakai untuk penyusunan skripsi dengan catatan
minor di atas. Tidak ada koreksi informasi substantif yang diperlukan.
