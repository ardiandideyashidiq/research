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
> **Peringatan kategoris:** paper ini **tidak memuat isu hukum**. Yang ada adalah **kesenjangan etis-filosofis**. Menempelkannya ke dalam kerangka hukum adalah pekerjaan penulis skripsi, bukan pengobyeksian dari paper. Pemetaan berikut adalah **bridging eksplisit**, bukan klaim paper.

* **Das Sollen (norma ideal menurut paper ini):**
  - AI harus ditempatkan sebagai **instrumen di bawah otoritas moral manusia** — bukan agen otonom yang menentukan arah kehidupan.
  - Keputusan yang berdampak pada kehidupan manusia **tidak boleh diserahkan kepada mesin**, karena hanya manusia yang memiliki hati nurani dan tanggung jawab moral.
  - Setiap inovasi teknologi harus **diukur berdasarkan dampaknya terhadap martabat manusia** (*Techno-Humanitarian Balance* sebagai prinsip regulatif).
  - Pendekatan *human-centered*: teknologi tetap **sarana**, bukan tujuan.
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
| **Konsep turunan** | *black box* (opasitas, Silalahi 2025); *perverse instantiation*; *treacherous turn*; *Singularitas Antropologis* (Sandu 2017); reduksionisme digital (Bezklubaya 2023) | Mekanisme bagaimana AI mereduksi manusia dan menghapus subjek moral |
| **Dokumen normatif** | *Antiqua et Nova* (Paus Fransiskus, 2025, Dikasteri untuk Ajaran Iman); *Christus Vivit* (Paus Fransiskus, 2019, Seri Dokumen Gerejawi No. 109) | Sumber normatif-teologis primer; landasan konsep: *Imago Dei*, kebijaksanaan hati, delegasi keputusan ke mesin |
| **Asas Hukum** | — **TIDAK ADA asas hukum (*Rechtsbeginselen*) yang dipakai.** Yang ada adalah prinsip moral-teologis: otoritas moral manusia, tanggung jawab moral, dan *discernment* |
| **Doktrin Sarjana (hukum)** | — **TIDAK ADA.** Tidak ada rujukan kepada sarjana hukum Indonesia maupun mancanegara |

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

---

## VI. TEMUAN UTAMA, ARGUMENTASI & PRESKRIPSI (*KEY FINDINGS*)

### 1. Temuan Utama (*Key Findings*)
1. **Kesenjangan ontologis mendasar antara kecerdasan manusia dan AI.** AI berperilaku pada kerangka kecerdasan fungsional (*metis*) yang berbasis kalkulasi dan optimasi data, sedangkan manusia memiliki intelek kontemplatif (*nous*) yang memungkinkan pemahaman makna, intuisi, dan pertimbangan moral. Asumsi AI dapat mereplikasi kecerdasan manusia menjadi problematis secara epistemologis. [FULL-TEXT] hlm. 121 (Kesimpulan)
2. **Paradoks AI: terbatas secara ontologis tetapi berbahaya justru karena keberhasilannya.** Kritik Dreyfus: tanpa *embodiment*, AI tidak memahami konteks realitas dan terjebak pada *frame problem*, serta tidak menyelesaikan *common sense* pada lingkungan terbuka. Sebaliknya, Bostrom: justru ketika AI mencapai *superintelligence*, terbuka risiko eksistensial bila *alignment problem* tak terpecahkan. **Ancaman utama bukan kegagalan mesin, melainkan keberhasilannya yang tidak terkendali.** [FULL-TEXT] hlm. 114, 121
3. **AI tidak memiliki kapasitas ontologis untuk menggantikan manusia sebagai subjek moral.** AI hanya memiliki *ratio* (kemampuan analitis) tanpa *intellectus* (pemahaman intuitif yang menangkap kebenaran secara menyeluruh); tanpa *care* yang menjadi dasar penilaian moral, sehingga nilai tidak dapat direduksi menjadi parameter komputasional. [FULL-TEXT] hlm. 116, 119
4. **"Kematian subjek moral" sebagai risiko terbesar.** Risiko terbesar bukan dominasi mesin secara langsung, melainkan **erosi bertahap** terhadap kemampuan manusia menilai dan memilih secara bebas; dehumanisasi baru berupa reduksi manusia menjadi data atau variabel dalam sistem digital. [FULL-TEXT] hlm. 121

### 2. Preskripsi (*De Lege Ferenda*)
> **Peringatan:** preskripsi paper ini **seluruhnya konseptual dan bercorak aras kebijakan**: tidak ada draft pasal, tidak ada usulan norma positif, dan tidak ada lembaga maupun regulator yang ditunjuk.

* **Preskripsi utama - *Techno-Humanitarian Balance* (THB):**
  - Menolak **dua posisi ekstrem**: dominasi *technocentrism* dan penolakan total terhadap teknologi.
  - Menempatkan AI sebagai **instrumen yang berada di bawah otoritas moral manusia**, bukan agen otonom yang menentukan arah kehidupan manusia.
  - Berfungsi sebagai **prinsip regulatif**: setiap inovasi teknologi harus **diukur berdasarkan dampaknya terhadap martabat manusia**.
  - Keseimbangan ini **tidak berarti menolak teknologi**, melainkan menempatkannya dalam kerangka etis yang jelas.
* **Preskripsi turunan:**
  - Pendekatan *human-centered* yang bersifat teknis, normatif, dan reflektif.
  - Pendidikan digital: tidak hanya kompetensi teknis, tetapi kesadaran kritis, tanggung jawab etis, dan **kebijaksanaan hati**.
  - **Regulasi global** yang menjaga keseimbangan inovasi teknologi dan perlindungan martabat manusia (dinyatakan sebagai kebutuhan, **tanpa spesifikasi**).
  - **Prinsip anti-delegasi**: keputusan yang berdampak pada kehidupan manusia (diagnosis medis, putusan hukum, kebijakan militer) **tidak boleh diserahkan kepada mesin**.

---

## VII. EVALUASI KRITIS & IDENTIFIKASI RESEARCH GAP (*CRITICAL APPRAISAL*)

### 1. Kelebihan & Kebaharuan Paper (*Novelty*)
* **Titik Kuat:**
  - Integrasi tiga sumber yang jarang digabung: kritik fenomenologis Dreyfus (batas epistemologis) + peringatan eksistensial Bostrom (risiko) + bingkai teologi Katolik (norma). Penulis secara eksplisit mengidentifikasi ini sebagai kesenjangan penelitian ("Kajian yang mengintegrasikan kritik fenomenologis Hubert Dreyfus dengan analisis risiko Nick Bostrom dalam kerangka teologi Katolik masih relatif terbatas", hlm. 114).
  - Konsep *Techno-Humanitarian Balance* menolak dikotomi ekstrem (dominasi teknologi vs penolakan total), sehingga tidak terjebak techno-determinisme maupun Luddisme.
  - Pembedaan *reckoning* vs *judgment*, serta *ratio* vs *intellectus*, memberi alat konseptual yang tajam untuk menjelaskan mengapa kapasitas komputasi tidak akan pernah menyamai kapasitas moral.
  - Penyebutan *black box* dan *engagement optimization* membuat argumen tidak terjebak pada AI "cerdas" saja, tetapi juga pada AI yang biasa digunakan sehari-hari.
* **Kebaharuan (*Novelty*):** kerangka normatif *Techno-Humanitarian Balance* yang menempatkan AI secara proporsional di bawah otoritas moral manusia, dengan landasan *Imago Dei* serta distingsi *metis*/*nous*.

### 2. Keterbatasan, Kelemahan, & Cacat Logika (*Limitations & Gaps*)
* **Celah paling menentukan: kekosongan normatif total (paper ini bukan paper hukum).** Paper tidak menganalisis satu pun pasal, undang-undang, atau putusan. Klaim normatif terkuatnya ("AI harus di bawah otoritas moral manusia") **tidak pernah diproyeksikan ke sistem hukum mana pun**: tidak ada UU Indonesia, tidak ada Deklarasi Universal Hak Asasi Manusia, tidak ada GDPR, tidak ada AI Act, tidak ada kebijakan platform. Konsekuensinya, THB **tidak teruji dan tidak dapat diuji** tanpa titik jangkar normatif.
* **Celah substantif: nol sentuhan pada deepfake.** Istilah "deepfake" **tidak muncul satu kali pun** dalam seluruh paper (verifikasi leksikal atas Markdown hasil konversi: 0 hit). Konteks yang dianalisis adalah AI *generik*: LAWS, diagnosis medis, media sosial, ChatGPT, algoritma rekomendasi. Karena itu **seluruh relevansi terhadap deepfake bersifat analogis, bukan langsung**.
* **Cakupan domain yang dipilih tidak relevan:** bagian sintesis implikasi (hlm. 122) membahas empat ranah eksemplar, tetapi **tidak satu pun** masuk ke ranah yang dikaji skripsi (identitas, persetujuan, data pribadi, konten non-konsensual).
* ***Analysis jump* dari deskripsi ke normatif:** dari "AI tidak memiliki *embodiment*" (premis empiris-filosofis) melompat ke "AI tidak dapat menjadi subjek moral" (premis normatif) tanpa premis bridging yang diuji. Untuk konteks hukum normatif, lompatan semacam ini adalah **analysis jump** — karena tesis tentang subjek moral sebenarnya adalah **tesis teologis** (manusia diciptakan sebagai *Imago Dei*), bukan konsekuensi yang mengikuti secara logis dari *frame problem*.
* **"Regulasi global" tanpa daya ikat:** seruan untuk regulasi global, tetapi paper tidak menetapkan lembaga mana yang bertanggung jawab, forum, maupun standarnya. Hasilnya sebuah botol kosong normatif.
* **Temporal gap:** paper terbit Juli 2026, sehingga **tidak ada** masalah temporal pada paper ini. Namun material normatif yang dirujuk (*Antiqua et Nova* 2025) bersifat global-Vatikan, bukan Indonesia; perlu diuji apakah doktrin ini memiliki *resonansi* dalam *local values* (Pancasila, adat, keberagaman) sebelum dipakai sebagai pijakan.
* **Keterbatasan yang diakui penulis sendiri:** analisis konseptual, tanpa studi empiris (hlm. 113). Jadi klaim empiris (mis. "AI unggul di catur, gagal di *common sense*") bersifat pengetahuan sekunder, **tidak diuji ulang** di sini.

---

## VIII. ANALISIS MANUAL - TEKNIK PENALARAN, DASAR HUKUM & KRITIK (enrichment)

### 2b. Teknik Penalaran Penulis (*Author's Analytical Technique*)

| Teknik | Yang Dilakukan | Catatan |
| :--- | :--- | :--- |
| **Dekonstruksi unsur pasal** | **TIDAK ADA.** | Paper tidak menguraikan sub-unsur pasal apa pun; tidak ada fakta hukum yang diuji ke norma. [FULL-TEXT] Tidak ada satu pun pasal dalam dokumen. |
| **Pemetaan rezim** | **TIDAK ADA (0 rezim).** Tidak memetakan ITE/PDP/KUHP/TPKS maupun rezim hukum apa pun. | Tidak ada argumen *lex specialis*, *lex superior*, atau *lex posterior*. Konsekuensi: paper **tidak punya titik jangkar** untuk dialog dengan rezim mana pun, termasuk rezim Indonesia. |
| **Struktur argumentasi** | **Bukan silogisme, bukan IRAC, bukan tipologi cacat norma.** Adalah **argumentasi filosofis dua-kaki + sintesis aksiologis**: (1) kaki epistemologis (Dreyfus), (2) kaki eksistensial (Bostrom), lalu disintesiskan pada tataran aksiologis (*metis* vs *nous*, *ratio* vs *intellectus*). | Kerangka orisinal dan konsisten secara internal; **tetapi bukan penalaran hukum**. Tidak ada premis normatif yang diuji ke fakta empiris atau ke kasus. |
| **Komparasi** | **Ada komparasi konseptual, tanpa *tertium comparationis* hukum.** Bandingkan: manusia vs AI (bukan sistem hukum A vs B); dan *metis* vs *nous* (bukan pasal vs pasal). | Tidak ada daftar negara, tidak ada perbandingan rezim, tidak ada *tertium comparationis* (objek/unsur/sanksi) yang diuji. Perbandingan bersifat **ontologis-filosofis**. |
| **Preskripsi** | **Konseptual-aras kebijakan.** *Techno-Humanitarian Balance* + pendekatan *human-centered* + *discernment* + anti-delegasi keputusan. **TIDAK ada draf pasal, tidak ada usulan norma positif, tidak ada lembaga maupun regulator yang ditunjuk.** | Preskripsi tidak cukup detail untuk *de lege ferenda* dalam arti hukum normatif; ia baru berupa **kaidah etis** (*ethical yardstick*), bukan **kaidah hukum** (*rule of law*). |

### 2c. Pasal/Dokumen yang Dianalisis Penulis (*Statutes & Sources*)

| Pasal/Dokumen | Status | Peran dalam Argumen |
| :--- | :--- | :--- |
| **Seluruh peraturan perundang-undangan Indonesia** (UUD 1945, UU ITE, UU PDP 27/2022, KUHP, dsb.) | **[TAK DISEBUT]** | Tidak satu pun disebut. **Methodological gap total.** |
| **UU / undang-undang mana pun (Indonesia maupun mancanegara)** | **[TAK DISEBUT]** | Verifikasi leksikal atas teks penuh: nol kutipan UU, Konstitusi, undang-undang, atau peraturan manapun di seluruh paper. |
| **Pasal / ayat / kualifikasi delik** | **[TAK DISEBUT]** | Nol penyebutan pasal. |
| **Putusan / yurisprudensi** | **[TAK DISEBUT]** | Nol penyebutan court case. |
| **Dokumen normatif non-hukum (dipakai sebagai rujukan utama)** | **[VERBATIM] (kutipan+parafrasa, tanpa nomor halaman/kutipan presisi dari dokumen asli)** | Sumber primer yang benar-benar dipakai: *Antiqua et Nova* (Paus Fransiskus, 2025) — tentang *Imago Dei*, *ratio* vs *intellectus*, delegasi keputusan; *Christus Vivit* (Paus Fransiskus, 2019) — tentang ruang digital dan generasi muda. **Catatan:** paper mengutip kedua dokumen ini secara konsisten, tetapi **tidak pernah memberikan nomor bagian atau paragraf** dari dokumen asli, sehingga kutipan tidak dapat diverifikasi secara presisi. |
| **Karya ilmiah primer** | **[VERBATIM] (dengan sitasi lengkap)** | Hubert Dreyfus, *What Computers Still Can't Do* (1992); Nick Bostrom, *Superintelligence* (2014). Disitasi lengkap dengan identitas, tahun, dan penerbit. |
| **Karya ilmiah sekunder** | **[VERBATIM] (sitasi reguler)** | 30-an rujukan sekunder (Bezklubaya 2023, Sandu 2017, Reynolds 2024, Goertzel 2015, Kowalczyk 2025, Karsli 2025, dll). |
| **Regulasi global / standar AI** | **[RUJUKAN] (tanpa spesifikasi)** | Autors *menyebut kebutuhan* "regulasi global" untuk menyeimbangkan inovasi versus perlindungan martabat (hlm. 118), **tanpa menyebut** lembaga, forum, atau standar tertentu. Ini rujukan normatif *implisit* — tidak ada spesifikasi konkret. |

> **Catatan metodologis (blok 2c):** Ini adalah **paper filosofis-teologis, bukan paper hukum**. Karena itu **[TAK DISEBUT] untuk seluruh peraturan perundang-undangan merupakan sifat intrinsiknya**, bukan kelalaian metodologis semata. Namun, **dampaknya terhadap skripsi tetap substansial**: karena paper tidak memiliki titik jangkar hukum, kontribusinya ke skripsi bersifat **normatif-eksploratif** (menyediakan *ethical yardstick* untuk menjustifikasi solusi hukum), bukan **dogmatis** (menyediakan *black-letter law* untuk dianalisis).

### 2d. Kritik Analisis terhadap Tulisan (*Counter-Points*)

* **(a) Potensi *analysis jump*:**
  - **Ya, ada dan besar.** Terlihat pada tiga lompatan: (i) dari "AI tidak memiliki *embodiment*" (premis filosofis) ke "AI tidak dapat menjadi subjek moral" (premis normatif-ontologis) — lompatan ini sebenarnya bertumpu pada *Imago Dei* (teologis), **bukan** pada argumen Dreyfus/Bostrom; (ii) dari "manusia adalah *subjek moral*" ke "AI adalah *instrumen*" — implisit, tidak dirumuskan secara eksplisit; (iii) dari temuan normatif ("AI di bawah otoritas moral manusia") ke rekomendasi ("perlu regulasi global") — tanpa perantara argumentatif. Untuk standar penalaran hukum normatif, (i) dan (iii) adalah **analysis jump** yang perlu dilokalisasi.
  - **Tidak ada uji unsur ke fakta**: tidak ada fakta yuridis (peristiwa deepfake, kasus konkret) yang diuji terhadap premis. Klaim tetap pada tataran konseptual-abstrak.

* **(b) Batasan asas legalitas dalam penafsiran progresif:**
  - **Tidak relevan secara langsung** - paper tidak pernah menafsirkan teks norma, jadi tidak ada *analysis* progresif yang perlu dibatasi. **Namun**, ini juga berarti paper **tidak menyediakan pijakan yang sah secara hukum**: *Techno-Humanitarian Balance* sebagai prinsip etis **tidak akan memenuhi standar kepastian hukum** jika di-*codify* tanpa landasan yuridis (misal: asas kepastian hukum, asas proporsionalitas, asas non-diskriminasi). **Rekomendasi:** THB harus diformulasikan ulang menjadi **prinsip hukum** agar memiliki daya ikat - misalnya dengan memadankannya ke asas non-diskriminasi atau perlindungan martabat yang sudah ada dalam tatanan hukum Indonesia.
  - **Asas legalitas (*nullum crimen, nulla poena sine lege*)**: paper justru mengisyaratkan kebutuhan regulasi, dan dengan menyerukan "regulasi global" tanpa batas, justru **membuka kemungkinan penyimpangan** dari asas legalitas. Jika THB diadopsi tanpa kejelasan norma, ia berpotensi menjadi **dasar tatanan hukum yang tidak pasti** - *vague norm* di balik selubung normatif.

* **(c) Data empiris tanpa verifikasi primer:**
  - **Tidak ada data empiris lapangan.** Klaim empiris (mis. "AI gagal di *common sense*") bersifat pengetahuan sekunder dari Dreyfus/Reynolds/Cappelen & Dever (2021), **tidak diuji ulang oleh paper**. Ini **tidak otomatis cacat** (paper secara eksplisit menyatakan ini adalah *conceptual* study), tetapi **penggunaannya sebagai pijakan hukum harus hati-hati**: klaim empiris sekunder tidak bisa dijadikan dasar konklusi hukum tanpa verifikasi primer.
  - **Analogi catur versus *common sense*:** paper membandingkan kemampuan AI pada lingkungan tertutup (catur) dengan kemampuan *common sense* pada lingkungan terbuka. Klaim ini bersifat **knowledge sekunder dari Cappelen & Dever (2021)** dan **tidak diuji ulang di dalam paper**. Relevansi terhadap deepfake (yang bekerja di lingkungan *closed-world* untuk *inpainting*, bukan *open-world* untuk *common sense*) **tidak langsung**.

* **(d) Celah *tertium comparationis* pada analisis perbandingan:**
  - **Tidak ada analisis perbandingan hukum sama sekali**, sehingga tidak ada *tertium comparationis* (objek, unsur, sanksi) yang bisa diuji. Perbandingan yang ada bersifat **manusia vs AI** dan ***metis* vs *nous*** — bukan perbandingan sistem hukum.
  - **Implikasi bagi skripsi:** paper ini tidak bisa dipakai sebagai *comparative authority* (tidak bisa dipakai untuk menunjukkan "di negara X, pendekatan seperti ini berhasil"). Paper hanya bisa dipakai sebagai *normative compass*.

### Research-gap mapping terhadap gap skripsi
| Gap Skripsi | Hubungan dengan Paper Ini |
| :--- | :--- |
| **Temporal ITE vs KUHP** | **Tidak menyumbang apa pun.** Tidak ada ITE, tidak ada KUHP, tidak ada UU 1/2024. Tidak ada persinggunan sama sekali. |
| **Multi-aktor** | **Kontribusi bermedan, tapi abstrak.** Paper menganggap delegasi keputusan kepada mesin secara moral tidak sah (anti-delegasi), yang bisa menjadi *ethical yardstick* bagi positioning multi-aktor: siapa yang tetap "bertanggung jawab moral" ketika keputusan diambil dengan bantuan AI? Tapi paper **tidak memetakan** aktor-aktor konkret (platform, penyedia model, pengguna, korban), sehingga harus disambungkan sendiri di skripsi. |
| **Forensik** | **Tidak menyentuh langsung.** Namun argumen *black box* (ketidaktransparanan proses algoritme) bisa dipinjam sebagai pijakan normatif bagi kebutuhan *transparansi* dan *explainability* dalam investigasi forensik deepfake. |
| **Moderasi/PSE** | **Kontribusi konseptual, bukan spesifik.** Paper membahas *engagement optimization* (media sosial) sebagai contoh reduksionisme; ini bersinggungan dengan dinamika moderasi platform yang melibatkan algoritma. Tapi **tidak menyentuh** rezim PSE/penyiaran konten, dan **tidak menyebut** *content moderation* atas konten bermuatan negatif - sehingga **belum melengkapi** `PAPER_Liu2025` dan `PAPER_DaudAbdGhaniAzmi2023` secara langsung. |
| **Perdata (identitas, consent, data pribadi)** | **Nol kontribusi langsung.** Tidak ada *deepfake*, tidak ada konten non-konsensual, tidak ada *data pribadi*, tidak ada *personality rights*, tidak ada *biometric data*. Kontribusinya **hanya filosofis**: menyediakan landasan normatif bahwa **martabat manusia tidak bisa direduksi menjadi data yang dapat dimanipulasi** - yang bisa diperkuat menjadi argumen bahwa *deepfake*, yang memanipulasi data biometrik untuk membangun identitas palsu, adalah pelanggaran ontologis terhadap kedaulatan data yang lebih fundamental daripada sekadar pelanggaran norma. |

> **Kesimpulan research-gap mapping:** paper ini **mengisi gap teoretis-antropologis, bukan gap normatif-hukum Indonesia**. Kontribusinya ke skripsi bersifat: (1) *legitimasi* — memberikan "hati nurani" (kebijaksanaan hati) sebagai pijakan normatif yang menggabungkan dimensi teologis dan dimensi HAM; (2) *justifikasi eksploratif* — memberi alasan filosofis mengapa AI harus "di bawah" manusia, yang bisa di-*deploy* untuk menjustifikasi solusi hukum yang skripsi usulkan. **Namun skripsi harus berhati-hati**: (a) meng-*bridge* THB dari etika ke hukum; (b) *memverifikasi* bahwa doktrin *Imago Dei* memiliki resonansi dalam *local values* Indonesia; (c) **tidak** menggunakan paper ini sebagai primary source hukum — semua *claim* hukum harus diverifikasi ke *Pasal.id* secara terpisah (bukan mengutip paper ini sebagai sumber hukum).

---

## IX. POSISI & RELEVANSI TERHADAP PENELITIAN SAYA (*RESEARCH POSITIONING*)

| Pertanyaan Evaluatif | Analisis Posisi untuk Skripsi |
| :--- | :--- |
| **Dimana letak kesepakatan (persamaan) paper ini dengan skripsi Anda?** | Kesesepakatan ada pada **orientasi normatif**: skripsi juga berorientasi pada perlindungan martabat korban, dan deepfake adalah bentuk nyata dari "degradasi identitas menjadi entitas algoritmik" yang identik dengan "fotokopi algoritmik" yang deskripsikan paper. Keduanya menangkap bahwa ada sesuatu yang *ontologis* hilang ketika manusia direduksi menjadi data yang dapat dimanipulasi. |
| **Dimana letak perbedaan / pertentangan paper ini dengan skripsi Anda?** | (1) **Objek**: paper membahas AI generik; skripsi spesifik pada deepfake. (2) **Basis sumber**: paper berbasis teologi dan filosofi (Dreyfus, Bostrom, dokumen Vatikan); skripsi berbasis *black-letter law* Indonesia (UU 1/2024, UU 27/2022, dsb.) + doktrin hukum Indonesia. (3) **Metode**: paper konseptual-aras kebijakan; skripsi normatif-doktrinal. (4) **Level analisis**: paper di tataran etis; skripsi di tataran hukum. Paper **tidak bisa menggantikan** analisis hukum; hanya bisa menjadi pijakan *ethical foundation*. |
| **Bagaimana paper ini menjadi bukti *Research Gap* bagi skripsi Anda?** | Paper ini justru adalah **bukti bahwa ada kesenjangan** antara literatur yang ada (yang fokus pada etika/teologi AI *generik*, dengan mengabaikan norma) dan *objek skripsi* (deepfake dalam rezim hukum Indonesia). Paper ini menunjukkan bahwa literatur yang ada *justru tidak pernah* menjawab pertanyaan hukum: **"Bagaimana martabat manusia yang direduksi menjadi data algoritmik itu dapat dilindungi melalui norma hukum positif Indonesia?"** - pertanyaan yang justru menjadi inti skripsi. Jadi paper ini adalah *gap*, bukan *solusi*. |
| **Rencana Penempatan dalam Skripsi:** | [x] **Bab I (Latar Belakang)**: hanya sebagai konteks normatif-etis, *bukan* sebagai sumber hukum; [x] **Bab II (Tinjauan Pustaka)**: sebagai literatur filosofis-teologis yang melengkapi literatur hukum; [x] **Bab III/IV (Pembahasan)**: sebagai **ethical yardstick** untuk menguji solusi hukum yang diusulkan; **TIDAK** untuk *bridge* normatif langsung (harus di-*relay* via Pasal.id). |

---

## X. MATRIKS RINGKASAN EKSTRAKSI CEPAT (*QUICK EXTRACTION CARD*)

```markdown
+------------------------------------------------------------------------------------------------------------------------------------------+
| IDENTITAS PAPER  : R.E. Astuti & H.M. Soeryamassoeka (2026), "Kecerdasan Buatan dan Kebijakan Hati:                       
|                    Menjaga Martabat Manusia di Tengah Risiko Teknologi Digital", EIRENE : Jurnal Ilmiah Teologi,                            |
|                    Vol. 11(1), Hlm. 110-123. DOI: 10.56942/24d1jc75. Label: [FULL-TEXT]                                              |
| ISU HUKUM        : Bukan isu hukum. Isu FILOSOFIS-TEOLOGIS: apakah AI dapat ditempatkan di bawah otoritas moral manusia tanpa mereduksi            |
|                    martabat manusia sebagai Imago Dei.                                                                                    |
| TEORI & METODE   : Imago Dei + Dreyfus (epistemologi) + Bostrom (eksistensial) + metis/nous | Kualitatif, integrative                 |
|                    literature review, analisis tematik induktif                                                                              |
| TEMUAN UTAMA     : (1) Kesenjangan ontologis kecerdasan manusia vs AI (metis vs nous); (2) Paradoks: AI terbatas secara ontologis tapi          |
|                    berbahaya karena keberhasilannya (superintelligence, alignment problem); (3) AI tak dapat menjadi subjek moral; (4)               |
|                    risiko "kematian subjek moral".                                                                                           |
| RESEARCH GAP     : (a) ZERO analisis hukum — nol pasal, nol UU, nol jurisprudence; (b) ZERO sentuhan pada deepfake (istilah tidak            |
|                    muncul); (c) Regulasi global bersifat normatif-deklaratif tanpa spesifikasi.                                           |
| KONTRIBUSI KITA  : Menyediakan ethical yardstick (THB, Imago Dei, metis/nous) untuk menjustifikasi solusi hukum atas pelanggaran             |
|                    martabat korban deepfake — tetapi seluruh *claim* hukum harus diverifikasi ke Pasal.id, bukan mengutip paper ini             |
|                    sebagai sumber hukum Indonesia.                                                                                          |
+------------------------------------------------------------------------------------------------------------------------------------------+
```

---

## XI. CHECKLIST FINAL EKSTRAKSI PAPER

- [x] Identitas bibliografi dan venue diverifikasi (Crossref + OpenAlex + PDF full-text).
- [x] Label epistemik **[FULL-TEXT]** diperbaiki dari packet [ABSTRACT] (PDF berhasil diunduh & dikonversi).
- [x] Kesenjangan normatif (*Das Sollen vs Das Sein*) dan jenis problematika diidentifikasi — dengan peringatan bahwa ini kesenjangan *etis-filosofis*, bukan normatif-hukum.
- [x] Kerangka teori (Grand, Middle, Applied) dan asas-asas hukum dicatat — **catatan: TIDAK ADA asas hukum**.
- [x] Metode penafsiran/konstruksi hukum dan penalaran silogisme diekstraksi — **catatan: TIDAK ADA penafsiran, pemetaan IRAC adalah *closest legal fit* bikinan penulis skripsi, bukan klaim paper**.
- [x] Temuan utama dan preskripsi *de lege ferenda* dirangkum — **catatan: preskripsi konseptual-aras kebijakan, tanpa draft pasal**.
- [x] *Research gap* dan keterbatasan paper ditemukan.
- [x] Posisi dan relevansi paper terhadap skripsi ditetapkan.
- [x] Blok enrichment 2b (teknik penalaran), 2c (pasal/dokumen dengan status [VERBATIM]/[RUJUKAN]/[TAK DISEBUT]), 2d (kritik) lengkap.
- [x] *Research-gap mapping* terhadap gap skripsi (temporal ITE↔KUHP, multi-aktor, forensik, moderasi/PSE, perdata) dipetakan.

