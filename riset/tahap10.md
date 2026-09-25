---
title: Tahap 10 — Penerapan Teknik Pengumpulan Bahan Hukum (Card System & Snowball)
description: >-
  Teknik studi dokumen, card system, dan snowball method yang dijalankan lewat CLI
  (search/fulltext/query) pada proyek deepfake.
status: draft
jenis: temuan-riset
tanggal: 2026-09-25
---

# Tahap 10: Teknik Pengumpulan Bahan Hukum

Melanjutkan `workflow.md` Tahap 10 & `riset/tahap1.md`–`tahap9.md`.
Teknik pengumpulan berikut sudah & akan dijalankan lewat platform.

## A. Documentary Study / Studi Dokumen

- Korpus Pasal.id (MCP): baca pasal UU ITE/PDP/KUHP baru **langsung dari
  teks** [TERBACA] — tahap1 §4, tahap8 §B.
- `research search` (federated): menemukan 22 paper (metadata/DOI).
- `research fulltext`: mengambil **full text** paper (yang OA) → Markdown di
  `data/markdown/`. Yang berhasil: Utara-Widyawati (29 hlm), Wicaksono-BBD
  (16 hlm); yang terblokir galley → [ABSTRACT].
- `research web-search`: menemukan 6 kasus riil deepfake Indonesia (tahap1
  §5b.1) — das sein.
- `research query` (RAG): menggali DB terindeks (tahap1 §5c).

## B. Card System (Sistem Kartu)

**Cards literal** disintesis dari bahan yang terbaca; setiap kartu berisi
kode topik → pasal/isu → bukti → sumber. Contoh kartu inti (dari tahap1–8):

| Kartu | Isi (ringkas) | Sumber |
|---|---|---|
| DF-KESUSILAAN | Deepfake seksual = Informasi Elektronik + Pornografi (172) → delik 27(1)/45(1) ITE kini; 407 KUHP baru nanti | [TERBACA] |
| DF-REPUTASI | Deepfake menuduh → 27A/45(4–6) ITE; KUHP 441 (penghinaan TI +1/3) | [TERBACA] |
| DF-DATA | Wajah/suara = data biometrik (PDP 4(2)b); Pasal 66 (memalsukan data) | [TERBACA] |
| DF-DISINFO | Deepfake berita bohong → 28(1,3)/45A | [TERBACA] |
| DF-MODERASI | Pemerintah/PSE moderasi (Pasal 40) | [TERBACA] |
| DF-KONFLIK | ITE↔KUHP 407 via Pasal 622(10) — konflik temporal | [TERBACA] |

Tabel ini diperluas menjadi **Matriks Literature Review** (Tahap 12/19) untuk
Bab III/IV.

## C. Snowball Method (Bola Salju)

- Dari paper [FULL-TEXT] → rujukan dalam paper (mis. FK Utara&Widyawati
  merujuk Sijabat, Putra, Respati; Rezvorovych merujuk literatur biometrik
  Jasserand, dll.) dilacak untuk memperdalam.
- Dari `knowledge/` → buku-buku dasar (Sudikno, Kelsen, dll.) di-telusuri ke
  karya asli bila perlu.
- Mencapai **titik jenuh** ketika snowball tak lagi menghasilkan sumber baru
  (dalam tahap ini: litigasi deepfake putusan langsung masih langka →
  penelusuran putusan via korpus putusan akan dilakukan bila tersedia).

## D. Alat Operasional (platform) — ringkas

| Tujuan | Perintah |
|---|---|
| Cari jurnal/paper | `uv run research search "<topik>" --providers crossref,openalex --no-index` |
| Full text paper | `uv run research fulltext "<DOI>" [--pdf-url <URL>]` |
| Web/kasus riil | `uv run research web-search "<topik>" --provider ddgs --no-index` |
| Gali DB terindeks | `uv run research query "<isu>" --mode hybrid --with-source --output f.md` |

## E. Evaluasi & Gate Check

- [x] Bahan tercatat lengkap dgn identitas bibliografi (file analisis
      `riset/literature-review/`; kartu di atas).
- [x] Snowball menuju titik jenuh; putusan deepfake langsung masih langka →
      dicatat sebagai bahan lanjutan.
- [x] Full text diutamakan (workflow Tahap 10 & AGENTS rule #6); yang
      terblokir jelas dilabel [ABSTRACT]/[METADATA].