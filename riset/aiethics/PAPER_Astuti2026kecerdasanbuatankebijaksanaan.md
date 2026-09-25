# PAPER — Kecerdasan Buatan dan Kebijakan Hati: Menjaga Martabat Manusia di Tengah Risiko Teknologi Digital

**Label Epistemic: [FULL-TEXT]**

> **Koreksi label terhadap packet.** Packet `tmp/aiethics_review/packets/Astuti2026kecerdasanbuatankebijaksanaan.json` menetapkan label `[ABSTRACT]` dengan `pdf_path: null` / `md_path: null`. **Label itu tidak akurat**: PDF open-access 14 halaman (429.639 byte) berhasil diunduh dari `https://ojs.ukip.ac.id/index.php/eirene_jit/article/download/483/447` → `data/downloads/10_56942_24d1jc75.pdf` (magic bytes `%PDF-1.7` valid; 14 halaman sesuai hlm. 110–123) dan dikonversi ke Markdown `data/markdown/10_56942_24d1jc75.md` (42.040 karakter) memakai konverter proyek sendiri (`research.pdf.converter.PDFConverter` via PyMuPDF4LLM). Seluruh uraian di bawah berbasis **teks penuh yang dibaca**, bukan abstrak. Sumber: [FULL-TEXT] `data/markdown/10_56942_24d1jc75.md`.
>
> **Catatan tooling (bug, bukan isu substansi):** `uv run research fulltext "10.56942/24d1jc75"` (dicoba 3×, termasuk `--force` dan `--pdf-url` eksplisit) tetap melaporkan `[-] Could not obtain a valid PDF … {'pending': 1}` padahal PDF valid ada di disk. Penyebab: di `Downloader.download_record` (src/research/downloader/downloader.py, Tier 3) PDF valid ditemukan → `db.update_status(...)` → `DatabaseManager.update()` (src/research/db/manager.py:578) mengembalikan `None` bila `cite_key` tidak ada di DB, sehingga `return updated or record` mengembalikan record yang `download_status` masih `"pending"` dan `download_path` masih `None`; statistik `{'pending': 1}` lalu memicu pesan gagal. Perlu diperbaiki terpisah; **tidak** memengaruhi status paper ini.

---

## I. IDENTITAS & OTORITAS DOKUMEN (*BIBLIOGRAPHIC & CREDIBILITY*)

| Komponen Evaluasi | Detail Informasi & Catatan Ekstraksi |
| :--- | :--- |
| **Judul Artikel/Paper** | *Kecerdasan Buatan dan Kebijakan Hati: Menjaga Martabat Manusia di Tengah Risiko Teknologi Digital* (judul Inggris: *Artificial Intelligence and the Wisdom of the Heart: Maintaining Human Dignity Amidst the Risks of Digital Technology*) |
| **Nama Penulis & Afiliasi** | Rosalia Enny Astuti (kontak: rosalia.enny@gmail.com) & Herkulana Mekarryani Soeryamassoeka — **Kedua-duanya Sekolah Tinggi Agama Katolik Negeri (STAKatN) Pontianak, Indonesia** [FULL-TEXT] hlm. 110 |
| **Nama Jurnal & Penerbit** | *EIRENE: Jurnal Ilmiah Teologi* — E-ISSN 2540-962X, ISSN 2528-1887; diterbitkan oleh **Lembaga Penelitian dan Pengabdian Masyarakat, Universitas Katolik Indonesia (UKiP) Sorong** [FULL-TEXT] hlm. 110. Hosting OJS: `ojs.ukip.ac.id`. *[PERLU VERIFIKASI]* Lisensi pada halaman OJS tidak konsisten (field lisensi CC BY 4.0, tetapi teks copyright menyebut CC BY-NC-SA 4.0 dan judul jurnal "Veritas") — suspected template error; tidak relevan untuk sitasi, tetapi jangan dianggap bebas reuse tanpa konfirmasi. |
| **Volume, Nomor, Halaman** | Vol. 11, No. 1 (2026), Hlm. 110–123 (14 halaman, terverifikasi dari jumlah halaman PDF) |
| **Tahun Terbit** | 2026 (Juli 2026; tanggal publikasi OJS 17-07-2026) |
| **DOI / Link Akses** | `10.56942/24d1jc75` — **terverifikasi** via Crossref + OpenAlex (kedua provider mengembalikan record yang sama: Astuti & Soeryamassoeka, EIRENE, 2026). PDF OA: `https://ojs.ukip.ac.id/index.php/eirene_jit/article/download/483/447` |
| **Akreditasi / Reputasi Jurnal** | — *[PERLU VERIFIKASI]*. Jurnal **teologi**, bukan jurnal hukum; tidak ada indeks hukum/SINTA yang terverifikasi di sini. Penilaian bobot untuk skripsi harus menggunakan reputasi bidang, bukan akreditasi hukum. |
| **Kata Kunci Utama (*Keywords*)** | *Kecerdasan Buatan (AI); Martabat Manusia; Hubert Dreyfus; Nick Bostrom; Antiqua et Nova* (5 kata kunci, sesuai OJS) [FULL-TEXT] hlm. 110 |

---

## II. TIPOLOGI & PENDEKATAN METODOLOGIS (*RESEARCH DESIGN*)

### 1. Karakteristik & Tipologi Penelitian
* [ ] **Penelitian Hukum Normatif / Doktrinal (*Black-Letter Law*)**: **TIDAK ADA.** Paper ini **bukan** penelitian hukum. Tidak ada satu pun kutipan peraturan perundang-undangan, konstitusi, atau putusan (lihat blok 2c).
* [ ] **Penelitian Hukum Empiris / Sosio-Legal (*Law in Action*)**: **TIDAK ADA.** Penulis sendiri menyatakan: "Penelitian ini dibatasi pada analisis konseptual dan tidak mencakup studi empiris lapangan, sehingga temuan yang dihasilkan bersifat normatif dan interpretatif" [FULL-TEXT] hlm. 113 (Metodologi).
* [ ] **Penelitian Normatif-Empiris / Terapan (*Applied Legal Research*)**: **TIDAK ADA.**
* [x] **Penelitian Filsafat/Teologi Kualitatif**: pendekatan kualitatif dengan desain *integrative literature review*; analisis tematik induktif; telaah teologi Katolik + filsafat ilmu terhadap AI. **Kategori yang paling dekat dalam tipologi hukum adalah "pendekatan filsafat (*philosophical approach*)"**, tetapi berada pada tataran etika-teologi, bukan pada tataran norma.

### 2. Pendekatan Penelitian Hukum (*Legal Research Approaches*)
* [ ] **Statute Approach**: — (tidak ada UU yang dianalisis)
* [x] **Conceptual Approach**: ya, dalam arti **teori/pemikiran** (Dreyfus, Bostrom, dokumen magisterium), **bukan** doktrin hukum
* [ ] **Case Approach**: —
* [ ] **Comparative Approach**: —
* [ ] **Historical Approach**: —
* [x] **Philosophical Approach**: Approach dominan — filsafat ilmu (*philosophy of science*) dan teologi Katolik (perspektif utama penulis)

### Metodologi yang dinyatakan penulis (terverifikasi dari teks penuh)
| Unsur | Isi [FULL-TEXT] hlm. 112–113 (Metodologi Penelitian) |
|---|---|
| Pendekatan | Kualitatif; desain *integrative literature review* |
| Latar pilihan metode | "fokus penelitian tidak terletak pada pengumpulan data empiris, melainkan pada penafsiran konseptual dan sintesis teoritis" |
| Data primer | Hubert Dreyfus, *What Computers Still Can't Do* (1992); Nick Bostrom, *Superintelligence* (2014); dokumen Gereja *Antiqua et Nova* (2025) & *Christus Vivit* (2019) |
| Data sekunder | Artikel jurnal, buku akademik, publikasi AI/etika digital/filsafat teknologi 2015–2025 |
| Kriteria seleksi | (1) relevansi tematik, (2) kredibilitas akademik, (3) kontribusi konseptual; menyisihkan literatur deskriptif umum |
| Teknik analisis | Analisis tematik induktif: pengumpulan → reduksi → kategorisasi tema → penarikan kesimpulan interpretatif (mengikuti Sugiyono 2013) |
| Konsep kunci | *embodiment*, *frame problem*, *superintelligence*, *alignment problem* |
| Validitas | Triangulasi sumber lintas perspektif (filsafat, teologi, etika teknologi) + pembacaan kritis berulang |
| Batasan eksplisit | "tidak mencakup studi empiris lapangan"; temuan bersifat normatif-interpretatif |

---

## III. EKSTRAKSI ISU HUKUM & PROBLEMATIKA NORMA (*LEGAL ISSUE*)

### 1. Kesenjangan Normatif (*Das Sollen vs Das Sein*)
> **Peringatan kategoris:** paper ini **tidak memuat isu hukum**. Yang ada adalah **kesenjangan etis-filosofis**. Menempelkannya ke dalam kerangka hukum adalah pekerjaan penulis skripsi, bukan penigansan dari paper. Pemetaan berikut adalah **bridging eksplisit**, bukan klaim paper.

* **Das Sollen (norma ideal menurut paper ini):**
  - AI harus ditempatkan sebagai **instrumen di bawah otoritas moral manusia** — bukan agen otonom yang menentukan arah kehidupan.
  - Keputusan yang berdampak pada kehidupan manusia **tidak boleh diserahkan kepada mesin**, karena hanya manusia yang memiliki hati nurani dan tanggung jawab moral.
  - Setiap inovasi teknologi harus **diukur berdasarkan dampaknya terhadap martabat manusia** (*Techno-Humanitarian Balance* sebagai prinsip regulatif).
  - abordar pendekatan *human-centered*: teknologi tetap **sarana**, bukan tujuan.
* **Das Sein (problem yang diangkat paper):**
  - **Reduksionisme digital**: kecenderungan mereduksi realitas manusia kompleks menjadi data dan variabel komputasional; intuisi, emosi, dan hati nurani terpinggirkan dalam logika algoritmik.
  - **Bergeseran status manusia**: teknologi menggeser manusia dari **subjek moral menjadi objek yang dioptimalkan**.
  - **Degradasi identitas**: individu menjadi "fotokopi algoritmik"; homogenisasi identitas via *engagement optimization* dan *echo chambers*.
  - **Kesenjangan ontologis** antara kecerdasan manusia dan AI: *mêtis* (AI, fungsional-optimatif) vs *noûs* (manusia, intelek kontemplatif).
  - **Risiko eksistensial** dari *superintelligence*: *alignment problem*, *orthogonality thesis*, *value is fragile*, *perverse instantiation*, *treacherous turn*.
  - **Krisis subjek moral** ("kematian subjek moral"): erosi bertahap kemampuan manusia menilai dan memilih secara bebas.
  - Contoh penerapan domain: LAWS (militer), *engagement optimization* (media sosial), ChatGPT (pendidikan), diagnosis AI (kesehatan).

### 2. Klasifikasi Problematika Norma
* [ ] ***Vague Norm***: — *(tidak ada norma hukum)*
* [ ] ***Conflict van Normen / Antinomi***: — *(tidak ada norma)*
* [x] ***Leemten van Normen / Wet Vacuum***: **secara substantif YA** — penulis secara eksplisit menuntut "regulasi global" yang menjaga keseimbangan inovasi dan perlindungan martabat, namun **tidak pernah menyusun atau mengidentifikasi norma yang seharusnya ada**. Jadi: kekosongan hukum hanyalah *temuan normatif implisit* (paper menyiratkan kebutuhan regulasi), **bukan hasil analisis normatif yang dilakukan paper**.

---

## IV. PANGKALAN TEORI, ASAS, DAN DOKTRIN (*THEORETICAL FOUNDATION*)

| Tingkatan Teori / Asas | Nama Teori / Asas & Tokoh Penggagas | Fungsi & Peranannya dalam Paper Ini |
| :--- | :--- | :--- |
| **Grand Theory (Filosofis/Teologis)** | **Imago Dei** (Kristologi/humanologi Katolik, Landasan dari *Antiqua et Nova* 2025) | Kualifikasi ontologis martabat manusia sesuai kodrat yang diberikan oleh Tuhan; **dasar penilaian** bahwa martabat **tidak bisa direduksi** menjadi data |
| **Grand Theory (Filosofis)** | **Filsafat ilmu** (*philosophy of science*): epistemologi–aksiologi AI (Dedes, Wibawa & Budiarto 2021) | Kerangka tiga bidang (ontologi, epistemologi, aksiologi) untuk membedah klaim AI |
| **Middle Range Theory** | **Hubert Dreyfus** — *What Computers Still Can't Do* (1992), khususnya lewat Reynolds 2024 | Kritik epistemologis: AI gagal karena mengabaikan *embodiment*; **frame problem**; *reckoning* vs *judgment*; *intentional arc*; *affordances* |
| **Middle Range Theory** | **Nick Bostrom** — *Superintelligence* (2014) | Kritik eksistensial: *orthogonality thesis*, *superintelligence*, **alignment problem**, *value is fragile* |
| **Applied Theory (aplikasi filosofis)** | **Arsitektur Aristotelian**: *ratio* vs *intellectus* (dari *Antiqua et Nova*); **mêtis** (kecerdasan praktis) vs **noûs** (intelek kontemplatif) (via Kowalczyk 2025) | Alat **aksiological** untuk memisahkan kapasitas AI vs kapasitas moral manusia |
| **Konsep turunan** | *black box* (opasitas, Silalahi 2025); *perverse instantiation*; *treacherous turn*; *Singularitas Antropologis* (Sandu 2017); *reksionisme digital* (Bezklubaya 2023) | Mekanisme/how AI mereduksi dan verrahas-subjek moral |
| **Dokumen normative** | *Antiqua et Nova* (Paus Fransiskus, 2025, Dikasteri untuk Ajaran Iman); *Christus Vivit* (Paus Fransiskus, 2019, Seri Dokumen Gerejawi No. 109) | Sumber normatif-teologis primer; landasan concepts: *Imago Dei*, kebijaksanaan hati, delegasi keputusan ke mesin |
| **Asas Hukum** | — **TIDAK ADA asas hukum (*Rechtsbeginselen*) yang dipakai.** Yang ada adalah prinsip moral-teologis: otoritas moral manusia, responsibility, *discernment* |
| **Doktrin Sarjana (hukum)** | — **TIDAK ADA.** Tidak ada rujukan ke nazw sarjana hukum Indonesia manapun |

---

## V. ANATOMI PENALARAN HUKUM & METODE ANALISIS (*LEGAL REASONING*)

### 1. Metode Interpretasi Hukum (jika ada *Vague Norm*)
* **Gramatikal / Sistematis / Teleologis / Historis / Ekstensif / Restriktif**: **tidak ada seluruhnya.** Paper tidak menafsirkan teks norma apa pun karena tidak ada norma yang dikutip.

### 2. Metode Konstruksi Hukum (jika ada *Wet Vacuum*)
* **Analogi / *a contrario* / *Rechtsverfijning***: **tidak ada.** Paper tidak pernah mengkonstruksi kaidah hukum; ia hanya menyatakan kebutuhan regulasi secara deklaratif.

### 3. Struktur Silogisme Deduktif / Model IRAC
Paper **tidak menyusun IRAC**. Struktur penalarannya adalah argumentasi filosofis dua-kaki (Dreyfus-Bostrom) yang disintesiskan secara aksiologis. Pemetaan ke IRAC berikut adalah **closest legal fit yang dibuat penulis skripsi, bukan klaim paper**:

```text
  [Issue]     : Apakah kecerdasan buatan dapat ditempatkan secara proporsional
                di bawah otoritas moral manusia tanpa mereduksi martabat manusia?

  [Rule]      : BUKAN norma hukum, melainkan prinsip filsafat-teologi:
                (a) Imago Dei - martabat manusia secara ontologis tidak dapat
                    dikomodifikasi;
                (b) kritik epistemologis Dreyfus - AI tanpa embodiment gagal
                    memahami konteks (frame problem);
                (c) peringatan eksistensial Bostrom - superintelligence tanpa
                    keselarasan nilai berbahaya (orthogonality, value is fragile);
                (d) distingsi metis (AI) vs nous (manusia); ratio vs intellectus.

  [Analysis]  : (a) vs (b) -> kesenjangan ontologis: AI tidak memadai dalam
                intuisi dan common sense, unggul hanya pada sistem tertutup
                yang teroptimasi;
                (b) vs (c) -> paradoks AI: secara ontologis terbatas, tetapi
                secara eksistensial berpotensi melampaui kendali manusia;
                (a) + (b) + (c) -> AI tidak memiliki kapasitas ontologis menjadi
                subjek moral;
                --> disintesiskan pada tataran aksiologis: AI adalah instrumen
                fungsional, manusia adalah subjek moral.

  [Conclusion]: PRINSIP NORMATIF: Techno-Humanitarian Balance - setiap inovasi
                diukur berdasarkan dampaknya terhadap martabat; AI berada di
                bawah otoritas moral manusia; teknologi adalah SARANA, bukan
                tujuan; keputusan yang berdampak pada nyawa tidak boleh
                didelegasikan kepada mesin.
```

> **Catatan kehati-hatian:** Slot `[Rule]` di atas **tidak berisi kaidah hukum positif**; seluruhnya adalah premis filosofis-teologis. Mengubah premis ini menjadi premis hukum (misalnya mewajibkan AI "berada di bawah otoritas moral manusia" melalui norma positif) adalah **pekerjaan skripsi**, bukan klaim yang sudah diperiksa paper.

<!--APPEND-MARKER-->




