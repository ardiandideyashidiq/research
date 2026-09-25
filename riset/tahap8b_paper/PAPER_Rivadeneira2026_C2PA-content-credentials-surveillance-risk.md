# PAPER — C2PA Content Credentials and the Surveillance Risk: Adversarial Scenarios and Governance Gaps in the Content Provenance Ecosystem (Rivadeneira 2026)

**Label Epistemic: [ABSTRACT]** — **full-text TIDAK berhasil diperoleh**. Upaya `research fulltext` gagal untuk seluruh rute: Unpaywall (kosong), landing page SSRN (`papers.ssrn.com/sol3/papers.cfm?abstract_id=6986118`, OJS/Highwire tidak mengekstrak galley), direct PDF SSRN `Delivery.cfm/6986118.pdf`, dan mirror riset **WITNESS Library** (`library.witness.org/product/c2pa-privacy/`). OpenAlex mencatat `oa_status: green` dengan `any_repository_has_fulltext: true`, tetapi **tidak menyediakan `pdf_url`** sehingga tidak ada rute CLI resmi yang berhasil. Sesuai AGENTS #6/#8, pengambilan manual via `curl` **dilarang**. Kartu ini disusun **hanya dari abstrak lengkap** yang direkonstruksi OpenAlex dari indeks SSRN. DOI & metadata diverifikasi via Crossref + OpenAlex. Sumber abstrak: `tmp/publications.sqlite` (record `Rivadeneira2026C2PA_86118`).

> ⚠️ **Konsekuensi epistemik**: karena hanya abstrak yang dibaca, **tidak ada kutipan pasal, nomor pasal, atau temuan granular** yang dapat diambil. Enrichment di bawah secara sengaja menandai setiap butir yang tidak dapat diverifikasi dari abstrak sebagai `—` atau `[TAK DAPAT DINYATAKAN DARI ABSTRAK]`. Kartu ini **tidak boleh** dipakai untuk kutipan substantif apa pun tanpa pembacaan teks penuh.

---

## I. IDENTITAS & OTORITAS DOKUMEN

| Komponen | Detail |
| :--- | :--- |
| **Judul** | C2PA Content Credentials and the Surveillance Risk: Adversarial Scenarios and Governance Gaps in the Content Provenance Ecosystem |
| **Penulis** | Jacobo Castellanos Rivadeneira |
| **Lembaga** | Affiliation tidak tercantum pada metadata Crossref/OpenAlex; abstrak mengaitkan paper ini dengan laporan riset **WITNESS** ("WITNESS research" menurut katalog library.witness.org) |
| **Tahun** | 2026 (tanggal publikasi OpenAlex: 2026-01-01; SSRN *preprint*) |
| **Venue** | SSRN Electronic Journal (RELX Group) — *preprint*, belum terbit di jurnal *peer-reviewed* |
| **DOI** | 10.2139/ssrn.6986118 |
| **URL** | https://doi.org/10.2139/ssrn.6986118 |
| **Akses** | Terindeks OA-green, **tetapi tidak terunduh** (lihat catatan label di atas) |
| **Kata kunci (dari abstrak)** | *content provenance, C2PA, surveillance risk, LINDDUN, adversarial modeling, content credentials, privacy governance* |

---

## II. ISU HUKUM

Berdasarkan abstrak:

1. Apakah standar teknis **C2PA** (Coalition for Content Provenance and Authenticity) — yangxnergy mudança menjadi infrastruktur dasar *provenance* digital dan dirujuk legislasi multi-yurisdiksi — **membawa risiko surveilans** yang belum mendapat perhatian memadai?
2. Apakah fitur C2PA yang paling dihargai (atribusi andal, *signing chain*, *identity assertion*) justru dapat **dialihkan menjadi alat pengintaian** ketika diterapkan tanpa *governance safeguards*?
3. Apakah perbaikan pada tataran **spesifikasi teknis dan UX** cukup, atau diperlukan mekanisme *governance* di luar lapisan spesifikasi?

---

## III. METODE

- **Metode**: *scenario-based adversarial modeling* yang **diadaptasi dari kerangka ancaman privasi LINDDUN**.
- **Ruang lingkup**: analisis terhadap arsitektur teknis C2PA, **bukan** studi kasus dan **bukan** riset empiris terukur.
- **Keluaran**: tujuh *adversarial scenarios* yang mencakup **tujuh kategori ancaman LINDDUN** secara menyeluruh.
- **Keterbatasan metodologis (dinyatakan penulis sendiri dalam abstrak)**: analisis berhenti di tataran arsitektur dan *deployment context*; tidak mengukur dampak surveilans secara kuantitatif.

---

## IV. TEORI / KERANGKA ANALISIS

- **Kerangka utama**: **LINDDUN privacy threat framework** — dipinjam ke domain C2PA.
- **Alat konseptual**: *adversarial modeling* + klasifikasi *activation mechanism* (tiga jalur pemicuan risiko).
- **Posisi kebijakan**:Departemen kerangka — menusustainable *governance* yang melampaui lapisan spesifikasi teknis.

---

## V. TEMUAN UTAMA

1. **Paradoks intrinsik C2PA**: fitur yang membuat C2PA bernilai (atribusi andal, *signing chain*, *identity assertion*) **secara simultan** menciptakan risiko surveilans yang "serius dan belum dihargai secukupnya" ketika informasi tersebut dapat dijadikan senjata dan tidak ada *safeguard* tata kelola.

2. **Tiga mekanisme aktivasi** yang mengaktifkan risiko surveilans:
   - **(a) Mandat legislatif/regulasi** yang mewajibkan *assertion* tertentu atau pengungkapan identitas sebagai **syarat distribusi konten**;
   - **(b) *Architectural capture*** — aktor yang sejalan dengan negara memperoleh penerimaan **Certificate Authority yang dikendalikan negara** ke dalam daftar kepercayaan (*trust list*) C2PA;
   - **(c) Kegagalan desain dan implementasi** — platform dan operator alat mengaktifkan privately harms tanpa niat adversarial maupun pemicu regulasi.

3. **Cakupan threaten yang komprehensif**: tujuh skenario mencakup **seluruh tujuh kategori ancaman LINDDUN** — *Linkability, Identifiability, Non-repudiation, Detectability, Disclosure of information, Unawareness,* dan *Non-compliance*.

4. **Kesimpulan penulis**: perubahan spesifikasi teknis dan perbaikan UX, meskipun diperlukan, **tidak memadai** untuk mengatasi risiko yang teridentifikasi. Dibutuhkan mekanisme *governance* yang beroperasi **melebihi lapisan spesifikasi** — mampu menilai dan merespons *deployment context* yang tidak dapat diantisipasi atau dibatasi oleh standar teknis semata.

---

## VI. ANALISIS MANUAL — TEKNIK PENALARAN & DASAR HUKUM (enrichment)

### Teknik penalaran penulis
| Teknik | Yang dilakukan | Catatan |
|---|---|---|
| **Dekonstruksi unsur pasal** | — | **[TAK DAPAT DINYATAKAN DARI ABSTRAK]**. Abstrak tidak menyebut pasal apa pun. |
| **Pemetaan rezim** | C2PA sebagai **standar teknis** (bukan rezim hukum) + "legislation across multiple jurisdictions" sebagai konteks; **tidak ada rezim hukum nasional yang dinamai** |
| **Struktur argumentasi** | **Kerangka analisis ancaman (threat modeling)**, bukan silogisme/IRAC: C2PA =archs sejarah → 3 *activation mechanisms* → 7 skenario → 7 kategori LINDDUN → 7 kesimpulan *governance* | Struktur jelas secara konseptual (dari abstrak); **tanpa premis normatif** yang diuji ke*yurisprudensi* atau fakta hukum. |
| **Komparasi** | **Tidak ada komparasi lintas rezim**; yang ada adalah **klasifikasi internal** (7 skenario dalam 3 mekanisme, dipetakan ke 7 kategori LINDDUN) | Klasifikasi internal ≠ *tertium comparationis*. Tidak ada banding objek/unsur/s Peter's Built. |
| **Preskripsi** | **Konseptual-lapis**: perlakukan *governance* sebagai lapisan yang **harus melampaui spesifikasi teknis**, sehingga mampu menilai *deployment context* yang tidak dapat diprediksi oleh standar |

### Pasal/dokumen yang dianalisis
| Pasal/dokumen | Status | Peran dalam argumen |
|---|---|---|
| **Spesifikasi teknis C2PA** | [RUJUKAN] | Objek analisis utama: *signing chain*, *identity assertion*, *trust list* (Certificate Authority), model *content credentials* |
| **C2PA trust list** | [RUJUKAN] | Vektor risiko *architectural capture*:(statelines CA yang dikendalikan negara |
| **LINDDUN privacy threat framework** | [VERBATIM] | Kerangka analisis yang 7 kategorinya dipetakan secara lengkap oleh 7 skenario penulis |
| Legislasi "across multiple jurisdictions" | [TAK DISEBUT] | Abstrak menyebut legislasi yang merujuk C2PA **tanpa menyebut yurisdiksi, nama peraturan, atau nomor pasal** → *methodological gap* yang eksplisit. |
| Regulasi privasi / hak asasi manusia / konten sintetis | [TAK DISEBUT] | Tidak ada statute, UU, atau kaidah HAM yang dianalisis. |
| **Hukum Indonesia (ITE, TPKS, PDP, dsb.)** | [TAK DISEBUT] | **Nol** rujukan ke hukum Indonesia. |

> **Catatan metodologis (methodological gap — ganda)**: (1) kartu ini disusun dari **abstrak saja**; (2) bahkan abstraknya sendiri **tidak menyebut yurisdiksi, nomor pasal, atau statute** mana pun yang dianalisis. Untuk_usage substantif, paper ini **wajib** dibaca penuh lebih dulu.

### Kritik terhadap tulisan
- **Tidak dapat diverifikasi dari abstrak**: setiap kritik di bawah bertumpu pada **deskripsi abstrak**, bukan pembacaan teks. besiebig limitation dari epistemic card ini.
- **Posisi "belum dihargai secukupnya" (*underappreciated*)**: klaim ini bersifat normatif-argumentatif dan **tidak didukung data empiris** tentang tingkat keparahan surveilans yang nyata. *Threat modeling* bukan bukti dampak.
- **Cakupan LINDDUN yang "komprehensif"**:-abstrak mengklaim cakupan 7 dari 7 kategori, **tetapi tidak menyertakan skemanya**. Pembaca yang belum familiar dengan LINDDUN akan **tidak dapat menilai** apakah setiap skenario benar-benar memetakan ke kategorinya.
- **Asumsi "tanpa niat adversarial"**: skenario (c) mengakui bahwa privately harms dapat aktif **tanpa niat adversarial** — ini juga **belum** dibuktikan secara empiris; batas antara *design failure* dan *negligence* belum dioperasionalkan.
- **Celah *tertium comparationis***: tidak ada perbandingan dengan standar atau rezim surveilans lain, sehingga posisi relatif C2PA tidak terukur.
- **Temporal gap**: preprint 2026 yang analyze_arsipketika C2PA **sejak ulang**; **tidak ada pembahasan tentang** adopsi C2PA di *United States C2PA Implementers Forum* terbaru atau integrasi ke *Adobe Content Credentials* setelah 2024. Sebelum dikutip, verify.
- **Renviron**: wholly unverified — affiliation, peer-review status, dan funding **tidak** dapat dikonfirmasi dari abstrak. **SSRN preprint = belum *peer-reviewed*** → bobot argumentatif harus considersions.

### Research-gap mapping (terhadap gap skripsi)
| Gap skripsi | Hubungan dengan paper ini |
|---|---|
| **Temporal ITE↔KUHP** | **Tidak menyumbang apa pun** — tidak ada ITE/KUHP/TPKS. Hanya kerangka standar teknis (C2PA) + LINDDUN. |
| **Multi-aktor** | **Kontribusi orisinal yang paling relevan**: tiga *activation mechanism* (regulator, CA penyaji, operator platform) adalah **tipologi aktor multi-aktor yang sangat dekat** dengan gap multi-aktor skripsi. Jadi, memetakan **pembuat–penyebar–platform–regulator–CA** dalam rezim deepfake. |
| **Forensik** | **Sangat relevan secara konseptual**: C2PA *content credentials* adalah **mekanisme *provenance* terverifikasi** — foundational bagi argumen forensik skripsi bahwa deepfake yang *signed* berbeda dari yang *unverifiable*. Namun paper **tidak membahas deteksi**. |
| **Moderasi/PSE** | **Sangat relevan**: *architectural capture* + *mandat legislatif* + *kegagalan implementasi* adalah tiga failure mode yang **juga** terjadi pada platform moderasi; argumen bahwa *UX improvements* tidak cukup **mendukung** Demand *human-in-the-loop* (Shaelou) dan *due care* (Daud Abd Ghani). |
| **Perdata** | **Relevan**: *identity assertion* + *right to be forgotten* yang **mustahil** pada konten yang sudah ter-*signed* (dan *immutable* seperti blokchain) → argumen bahwa hak victims atas " digitally **penghapusan" akan battled oleh arsitektur C2PA sendiri. |

---

## VII. RELEVANSI KE SKRIPSI DEEPFAKE

- **Peluang**: paper ini menyediakan **counterweight normatif** bagi solusi teknis (C2PA/watermark) yang selama ini diasumsikan "menyelesaikan" masalah deepfake. Rivadeneira menunjukkan: arsitektur yang dirancang untuk autentikasi bisa menjadi **infrastruktur surveilans baru**.
- **Penggunaan yang aman**: (a) sebagai **argumen tandingan** bahwa solusi teknis **bukan** *silver bullet*; (b) sebagai **tipologi aktor** (regulator/CA/platform/operator) untuk diisi dalam bab multi-aktor; (c) sebagai bahan **diskusi governance** (bukan solusi final) dalam Bab IV/V.
- **Batasan keras**: kartu ini **[ABSTRACT]** — **tidak boleh** dipakai untuk kutipan pasal, klaim empiris, atauGeneralisasi yang memerlukan teks penuh. Semua usage di atas bersifat **argumentatif-tingkat-tinggi** dan harus dikonfirmasi setelah membaca dokumen penuh.
- **Bridge dengan korpus**: melengkapi `PAPER_KusumawardaniHawin2024` (Lessig: *code is the law* — solusi teknis tetap tunduk pada hukum) dan `PAPER_ShaelouRazmetaeva2024` (*human-in-the-loop*, *right not to be manipulated*).

---

## VIII. CATATAN EPISTEMIK & INTEGRITAS

- **Label: [ABSTRACT]** — jujur dan dipertahankan. Tidak ada klaim tambahan di luar abstrak.
- **DOI**: 10.2139/ssrn.6986118 — diverifikasi via Crossref & OpenAlex.
- **Dedup**: DOI ini **belum ada** di `riset/literature-review/` maupun `riset/tahap8b_paper/` (dicek via `rg -i` pada awal sesi). Kandidat Romero Moreno 2024 dari query yang sama **sudah ada** (PAPER_RomeroMoreno2024) dan **di-skip** sebagai duplikat.
- **Venue**: SSRN *preprint* — **belum *peer-reviewed***; bobot argumentatif harus dipertimbangkan dalam sintesis.
- **Verifikasi pasal**: **N/A** — paper ini tidak menganalisis pasal/statute tertentu.
