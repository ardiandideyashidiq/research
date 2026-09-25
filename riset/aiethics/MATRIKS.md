# Matriks Literatur — AI, Martabat Manusia & Regulasi

**Sumber**: `apaurgensikitauntukmemperlambatperkembanganai-2026-09-25.bib` — 11 entri unik dari 22 (duplikat `...2` di-dedup by DOI).
**Alur**: `research review-run` → dedup → snowball berk relevansi → Unpaywall → 1 subagent per paper.
**Relevance query**: `kecerdasan buatan martabat manusia` · **top-k**: 10 · **seeds expanded**: 3
**Dipilih**: 7 paper (15 *ranked out* oleh cap + 21 *dropped* oleh filter relevansi).

| # | Cite Key | Judul | DOI | Asal | Skor | Label |
|---:|---|---|---|---|---:|---|
| 1 | `Pabubung2023kecerdasanbuatandampak` | Era Kecerdasan Buatan dan Dampak terhadap Martabat Manusia | 10.23887/jfi.v6i1.49293 | seed | 1.438 | [ABSTRACT] |
| 2 | `Astuti2026kecerdasanbuatankebijaksanaan` | KECERDASAN BUATAN DAN KEBIJAKSANAAN HATI: MENJAGA MARTABAT | 10.56942/24d1jc75 | seed | 1.45 | [FULL-TEXT] (manifest salah; PDF 14 hlm diperoleh reviewer) |
| 3 | `Zaenudin2024perkembangankecerdasanbuatan` | Perkembangan Kecerdasan Buatan (AI) Dan Dampaknya Pada Dun | 10.55903/jitu.v2i2.240 | seed | 0.844 | [ABSTRACT] |
| 4 | `Kulal2026etikaalgoritmakosmologi` | Etika Algoritma dan Kosmologi Islam: Menakar Masa Depan Ke | — | seed | 0.55 | [ABSTRACT] |
| 5 | `Suparmadi2026kerendahanhatisebagai` | Kerendahan Hati sebagai Jawaban: Spiritualitas Vinsensian  | 10.35312/rrfb5977 | seed | 0.85 | [ABSTRACT] |
| 6 | `Pabubung2024persoalanprivasidegradasi` | Persoalan Privasi dan Degradasi Martabat Manusia dalam Pen | 10.23887/jfi.v7i2.68070 | seed | 1.444 | [ABSTRACT] |
| 7 | `Pabubung2021Epistemologi_81383` | EPISTEMOLOGI KECERDASAN BUATAN (AI) DAN PENTINGNYA ILMU ET | 10.23887/jfi.v4i2.34734 | snowball | 0.826 | [ABSTRACT] |

## Relevansi substantif (hasil review subagent — bukan skor mesin)

Skor di kolom *Skor* adalah **tumpang tindih kata kunci**, **bukan** relevansi substantif.
Empat paper ternyata **tidak memuat hukum Indonesia sama sekali**:

| Paper | Isi sebenarnya | Penempatan |
|---|---|---|
| `Astuti2026` | Teologi: *Imago Dei*, Dreyfus, Bostrom. **0 pasal, 0 "deepfake"** | Bab II (ethical yardstick), **dilarang** Bab III/IV |
| `Zaenudin2024` | Teknis/informatika. Statistik industri **tidak terverifikasi** | Bab II, **dilarang** Bab III/IV |
| `Suparmadi2026` | Teologi/spiritual. 0 pasal/UU | Bab II, **dilarang** Bab III/IV |
| `Kulal2026` | Etika Islam/kosmologi (*marātib al-wujūd*) | Bab II, **dilarang** Bab III/IV |

**Yang benar-benar menopang kerangka *martabat manusia*** hanya 3 paper Pabubung (2021, 2023, 2024).

## Gap temporal (ruang kontribusi skripsi)

Pabubung 2021 & 2023 terbit **sebelum** UU PDP 27/2022 dan UU 1/2024 — pemetaan
*martabat manusia* ke rezim positif Indonesia **belum pernah dipetakan**; itulah ruang
kontribusi skripsi ini (lihat `riset/tahap2.md` §2.2).

## Catatan metodologis

- Full text hanya berhasil untuk 1 dari 7 paper: penerbit lain memblokir host ini
  (HTTP 403) meski dengan TLS impersonation Chrome. Label `[ABSTRACT]` berarti analisis
  berbasis abstrak — **tidak boleh** mengutip isi paper substantif tanpa full text.
- Bug tooling ditemukan & diperbaiki: `fulltext` melaporkan gagal padahal PDF
  valid (record transien tidak ter-insert ke DB).
