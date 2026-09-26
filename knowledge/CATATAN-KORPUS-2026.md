---
title: Catatan Validasi Korpus — Hasil Verifikasi Pasal.id September 2026
description: >-
  Daftar temuan yang wajib diperhatikan sebelum menulis file knowledge baru:
  instrumen yang sudah dicabut, instrumen yang tidak ada di korpus Pasal.id,
  dan pemetaan salah yang terdeteksi. Semua temuan di sini sudah diverifikasi
  lewat resolve_law dan get_law_context, bukan dari ingatan.
status: knowledge
jenis: catatan-verifikasi
---

# Catatan Validasi Korpus (Corpus Validation Notes)

Dokumen ini berisi temuan yang **wajib** dibaca sebelum menulis file knowledge
baru dari korpus buku di
`/home/rd/Documents/organized/01-kuliah/hukum/topikal/topical/`. Setiap butir
sudah diverifikasi melalui MCP `pasal-id` pada September 2026. Ini bukan
daftar teori — ini daftar jebakan yang akan menghasilkan klaim salah kalau
diabaikan.

## I. Instrumen yang Sudah Dicabut

### A. KUHAP (UU No. 8 Tahun 1981) — SUDAH DICABUT

`get_law_context(3724, detail='relationships')` mencatat `status: dicabut`,
dengan `amendments_total: 1`:

| Hubungan | Instrumen |
|---|---|
| Dicabut oleh | **UU No. 20 Tahun 2025 tentang Kitab Undang-Undang Hukum Acara Pidana** |

Konsekuensi doctrinal: seluruh buku dalam korpus yang mengutip nomor pasal
KUHAP sedang mendeskripsikan praktik **sebelum** reformasi. Buku-buku itu
belum sepenuhnya kedaluwarsa doktrinalnya, tetapi rujukan pasalnya harus
diperlakukan sebagai deskripsi praktik lama, bukan hukum yang berlaku.

> **Label yang benar untuk rujukan pasal KUHAP di file knowledge baru:**
> `[PERLU VERIFIKASI]` atau `[FULL-TEXT]` dengan catatan bahwa rujukan pada
> klausul dasar adalah UU 20/2025, bukan UU 8/1981. Jangan tulis `[TERBACA]`
> untuk pasal KUHAP tanpa menyebut bahwa statusnya sudah dicabut.

KUHAP juga memiliki 99 putusan MK dalam korpus (`court_reviews_total: 99`).
Beberapa yang mengubah substansi pasal tertentu:

| Putusan | Amar | Klasifikasi |
|---|---|---|
| MK 231/PUU-XXIII/2025 | inkonstitusional bersyarat | frasa "pejabat yang bersangkutan" Pasal 72 |
| MK 170/PUU-XXII/2024 | inkonstitusional bersyarat | frasa Pasal 143 ayat (2) tentang surat dakwaan bertanggal dan bertanda tangan |
| MK 28/PUU-XX/2022 | inkonstitusional bersyarat | frasa "batal demi hukum" Pasal 143 ayat (3) |
| MK 122/PUU-XXI/2023 | dikabulkan sebagian | kasasi dan peninjauan kembali tanpa kehadiran para pihak |
| MK 123/PUU-XXI/2023 | tidak diterima | tenggat waktu penetapan dan praperadilan |
| MK 96/PUU-XX/2022 | ditolak | surat perintah penyidikan, laporan polisi |
| MK 61/PUU-XX/2022 | ditolak | bantuan hukum bagi saksi |

### B. Ringkasan Instrumen yang Perlu Dicek Ulang

| Instrumen | Temuan | Label wajib |
|---|---|---|
| **UU 36/2009** tentang Kesehatan | Tercatat `berlaku` sekaligus "Dicabut oleh UU 17/2023" pada `relationships` | `[TERBACA]` hanya bila menyebut bahwa UU 17/2023 yang berlaku |
| **UU 5/1999** tentang Hak Agraria | Tidak resolve. `law_id 3027` adalah UU 39/1999 tentang **HAM**, bukan Hak Agraria | `[PERLU VERIFIKASI]` untuk UUPA |
| **PP 24/1998** | Resolve ke "Informasi Keuangan Tahunan Perusahaan", bukan Pendaftaran Tanah | `[PERLU VERIFIKASI]` |
| **UU 1/2023** (KUHP) | `status: diubah`, 전면 amendemen oleh **UU No. 1 Tahun 2026 tentang Penyesuaian Pidana** | `[TERBACA]` hanya dengan catatan UU 1/2026 |

### C. Konflik Nomor Undang-Undang yang Tersebar di Buku Korpus

Dua kekeliruan berikut ada di dalam buku-buku itu dan sering diulang:

| Yang tertulis di buku | Yang benar di korpus |
|---|---|
| "UU No. 23/2004" sebagai perubahan UU 1/1974 tentang Perkawinan | `law_id 12528` = UU 23/2004 tentang **Penghapusan Kekerasan dalam Rumah Tangga**. Perubahan UU 1/1974 adalah **UU 16/2004**, yang **tidak ada** di korpus |
| "UU No. 5 Tahun 2018" tentang terorisme | UU 5/2018 | Indeks terorisme berhenti di UU 15/2003; UU 5/2018 tidak ada di korpus |

Satu koreksi substantif yang sering terbalik: **MK 46/PUU-VIII/2010**
(*dikabulkan sebagian*, dengan *concurring opinion* **Maria Farida Indrati**)
menyatakan bahwa anak luar perkawinan **tetap memiliki hubungan perdata**
dengan ayah biologis dan keluarganya begitu ayah kandung dibuktikan.
Analisis yang menyatakan sebaliknya berada di belakang perkembangan putusan.

## II. Instrumen yang Tidak Ada di Korpus Pasal.id

| Instrumen | Yang Terverifikasi | Implikasi |
|---|---|---|
| **UUD 1945 naskah asli** | Hanya varian P1–P4 (amandemen) yang ada: P3 = `285722`, P4 = `285724` | Pasal 1, 18, 27, 28, 33(1)–(3) teks asli harus `[PERLU VERIFIKASI]` |
| **KUHPerdata** | `resolve_law("KUH Perdata")` hanya mengembalikan **putusan MK yang mengujinya**, bukan teks kitabnya | Semua pasal KUHPerdata hanya `[FULL-TEXT]` dari buku, bukan `[TERBACA]` |
| **UU 5/1999** (Hak Agraria) | Tidak ditemukan | Lihat tabel di Bagian I.B |
| UU 5/2018 (terorisme) | Tidak ada di korpus; buku korpus berhenti di UU 15/2003 | Rantai terorisme wajib diverifikasi dari sumber lain |

**Konsekuensi untuk UUD 1945:** Pasal 1 ayat (1) tentang NkRI adalah klausul yang paling sering dikutip dan
paling sering disalahartikan. Worker wajib menyatakan secara eksplisit bahwa teks
Pasal 1 ayat (1) **tidak dapat diverifikasi dari korpus**, bukan menuliskannya
dari ingatan.

## III. Temuan Validasi yang Sudah Mengarahkan File Terkini

### A. File yang Sudah Lolos Gate

Semua file di bawah sudah diverifikasi: satu H1, section Referensi ada, dan
lulus pemindaian korupsi (CJK, U+FFFD, dan kata glued).

| Folder | File | Baris |
|---|---|---|
| `hukum-islam/` | `fikih-muamalat.md` | 371 |
| `hukum-islam/` | `fikih-jinayah.md` | 230 |
| `hukum-islam/` | `usul-fikih.md` | 318 |
| `hukum-islam/` | `hukum-waris-islam.md` | 340 |
| `hukum-islam/` | `hukum-keluarga-islam.md` | 311 |
| `hukum-islam/` | `tasawuf-dzikir.md` | 219 |
| `hukum-islam/` | `hukum-islam-indonesia.md` | 339 |
| `hukum-perdata/` | `perikatan.md` | 400 |
| `hukum-perdata/` | `harta-benda.md` | 372 |
| `hukum-keluarga/` | `perkawinan.md` | 469 |
| `hukum-adat/` | `kedudukan-hukum-adat.md` | 471 |
| `hukum-tata-negara/` | `uud-1945.md` | 480 |
| `ilmu-hukum/` | `pengantar-ilmu-hukum.md` | 373 |
| `ham/` | `ham-konstitusional.md` | 288 |
| `ham/` | `ham-ranah-sosial.md` | 309 |
| `ham/` | `ham-individu-kelompok-rentan.md` | 381 |

File-file ini tidak mengutip KUHAP, UU 36/2009, UU 5/1999, PP 24/1998, atau
UU 13/2003, sehingga catatan pada Bagian I tidak mengubah isinya. Verifikasi
ulang diperlukan bila file tersebut kemudian direvisi.

### B. Pemeriksaan Korupsi Wajib Sebelum Commit

Pemeriksaan CJK saja **tidak cukup**. Kerusakan yang paling sering muncul
adalah kata gabung yang menyamar, misalnya `slappingPasal`, `dapatTonness`,
`mengUdahukan`, `kebutuhanagatChannel`, `doKons`, dan `harta danMuamalah`.
Semuanya muncul sebagai degenerasi keluaran panjang dan lolos pemeriksaan
karakter non-ASCII.

Jalankan kedua pemeriksaan berikut sebelum commit:

```bash
# 1. CJK dan replacement character
grep -rlP '[\x{3000}-\x{9FFF}\x{FFFD}]' knowledge/ || echo "bersih"

# 2. Kata glued
python3 -c "
import re, glob
GLUED = re.compile(r'[a-z]{2,}[A-Z][a-z]{2,}')
for f in glob.glob('knowledge/**/*.md', recursive=True):
    for i, l in enumerate(open(f, encoding='utf-8'), 1):
        if l.startswith('|') or 'http' in l:
            continue
        for m in GLUED.finditer(l):
            print(f'{f}:{i} glued {m.group(0)!r}')
"
```

## IV. Istilah yang Tidak Ada di Korpus Buku

Beberapa istilah yang lazim dalam literatur hukum **tidak muncul sama sekali**
di dalam 40–200 buku subjek terkait. Worker tidak boleh menulisnya dari
ingatan dan menyodorkan sebagai doktrin bersumber:

- `UAS` (*Undang-Undang Adat Sumatra*) — 0 hit di 40 buku hukum adat
- `Uluhuy` — 0 hit
- `khato` — 0 hit
- `H.R. Wardojo` — 0 hit di 111 buku
- `Soebrono Aminoto` — 0 hit di 111 buku
- `Willeke Verheijen` dan `Z.F.S. Sitanggang` — 0 hit

Untuk istilah seperti ini, tulis `[PERLU VERIFIKASI]` beserta catatan
"tidak ditemukan dalam korpus sumber", lalu lanjutkan dengan analisis yang
bersumber).

## V. Antisipasi Pertanyaan Lanjutan

> **"Mengapa KUHAP dicabut — apakah buku-buku hukum pidana jadi tidak berlaku
> semua?"**

Tidak. Yang dicabut adalah KUHAP sebagai satu kesatuan,
UU No. 8 Tahun 2021 tentang Hukum Acara Pidana. Buku-buku itu tetap
bernilai sebagai sumber doctrine tentang DIRI PERADILAN,-modalitas, dan
asas. Yang hilang adalah AUTHORITAS PASALNYA. Saat menulis knowledge file,
fokuskan pada prinsip yang abadi (asas-asas acara pidana, burden of proof,
*) Instead of pada nomor pasal yang sudah tidak berlaku.

> **"Bagaimana menulis tentang-protected UUD 1945 Pasal 1 dan 28 bila korpus
> tidak memuatnya?"**

Tulis sebagai `[PERLU VERIFIKASI]` dan rujuk ke Putusan MK yang tersedia
di korpus sebagai jangkar. Contoh: Putusan MK 68/PUU-XII/2014 (UU 1/1974),
MK 79/PUU-XXI/2023 (UU 1/PNPS/1965), dan MK 105/PUU-XXII/2024 (ITE Pasal
27A) semuanya ada di korpus `search_court_decisions` dan dapat dipakai
sebagai sumber sekunder yang terverifikasi.

---

## Referensi

1. **Pasal.id** (2026). *Kitab Undang-Undang Hukum Acara menyelenggarakan Criminal*
   (UU 8/1981), law_id 3724. Diakses September 2026. Status: dicabut oleh
   UU 20/2025.

2. **Pasal.id** (2026). *Undang-Undang Nomor 1 Tahun 2026 tentang Penyesuaian
   Pidana*, law_id 29. Diakses September 2026.

3. **Mahkamah Konstitusi** (2025). *Putusan Nomor 231/PUU-XXIII/2025*.
   Diakses melalui korpus Pasal.id September 2026.
