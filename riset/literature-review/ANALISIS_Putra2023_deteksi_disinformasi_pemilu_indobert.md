# ANALISIS PAPER — Disinformation Detection on 2024 Indonesia Presidential Election using IndoBERT

**Epistemic Label: [ABSTRACT]** — isi ekstraksi hanya bersumber dari abstrak dan metadata terverifikasi (Crossref, OpenAlex, Semantic Scholar); teks penuh paper **belum dibaca**. Semua klaim temuan didasarkan pada abstrak.

---

## I. IDENTITAS & OTORITAS DOKUMEN (*BIBLIOGRAPHIC & CREDIBILITY*)

| Komponen Evaluasi | Detail Informasi & Catatan Ekstraksi |
| :--- | :--- |
| **Judul Artikel/Paper** | Disinformation Detection on 2024 Indonesia Presidential Election using IndoBERT |
| **Nama Penulis & Afiliasi** | Andhika Bayu Yudhistira Arda Putra; Yuliant Sibaroni; Aditya Firman Ihsan. Afiliasi institusi **tidak tercantum** dalam metadata terverifikasi (IEEE Xplore/Crossref) — [PERLU VERIFIKASI] |
| **Nama Jurnal & Penerbit** | 2023 International Conference on Data Science and Its Applications (ICoDSA), penerbit: IEEE |
| **Volume, Nomor, Halaman** | Prosiding konferensi; Hlm. 350–355 |
| **Tahun Terbit** | 2023 (agustus) |
| **DOI / Link Akses** | 10.1109/icodsa58501.2023.10277572 |
| **Akreditasi / Reputasi Jurnal** | [x] Prosiding Konferensi Internasional/Nasional (IEEE ICoDSA, peer-reviewed) — status Scopus tidak terverifikasi dari sumber terpakai |
| **Kata Kunci Utama (*Keywords*)** | *Disinformation; Indonesia Presidential Election 2024; IndoBERT; Natural Language Processing; Twitter/X* |

---

## II. TIPOLOGI & PENDEKATAN METODOLOGIS (*RESEARCH DESIGN*)

> *Paper ini bersifat **non-hukum** (ilmu data komputasional / NLP). Bagian berikut tetap diisi sesuai template untuk memetakan relevansinya terhadap penelitian hukum, dengan penanda bahwa tipologi hukum tidak berlaku penuh.*

### 1. Karakteristik & Tipologi Penelitian
* [ ] **Penelitian Hukum Normatif / Doktrinal (*Black-Letter Law*)**: —
* [ ] **Penelitian Hukum Empiris / Sosio-Legal (*Law in Action*)**: —
* [ ] **Lainnya: Penelitian komputasional (applied data science)** — pengembangan model klasifikasi teks untuk mendeteksi disinformasi di Twitter/X seputar Pemilihan Presiden Indonesia 2024.

### 2. Pendekatan Penelitian Hukum (*Legal Research Approaches*)
* [ ] **Lainnya: pendekatan eksperimental-komputasional** — pengumpulan dataset, pelabelan, *word embedding* (Word2Vec), klasifikasi IndoBERT, validasi K-Fold Cross Validation.

---

## III. EKSTRAKSI ISU HUKUM & PROBLEMATIKA NORMA (*LEGAL ISSUE*)

### 1. Kesenjangan Normatif (*Das Sollen vs Das Sein*)
* **Das Sollen (Norma Ideal/Aturan yang Diharapkan):** Integritas informasi dalam proses pemilu — disinformasi yang beredar di media sosial seharusnya dapat diidentifikasi dan ditekan penyebarannya demi penyelenggaraan pemilu yang bersih dan demokratis.
* **Das Sein (Realita Hukum/Problem Normatif/Kondisi Faktual):** Disinformasi tersebar luas di Twitter/X menjelang Pemilu 2024 Indonesia; informasi di media sosial tidak selalu terverifikasi kebenarannya; model deteksi otomatis (IndoBERT) diusulkan sebagai salah satu alat mitigasi.

> **Catatan epistemik:** paper ini **tidak menganalisis norma hukum**; ia menyediakan fakta empiris-teknis tentang fenomena disinformasi (objek material yang sama dengan deepfake disinformasi) yang dapat dipakai sebagai bahan *das sein* dalam Bab I skripsi.

### 2. Klasifikasi Problematika Norma
* [ ] ***Vague Norm* (Norma Kabur):** —
* [ ] ***Conflict van Normen / Antinomi* (Konflik Norma):** —
* [ ] ***Leemten van Normen / Wet Vacuum* (Kekosongan Hukum):** —

> *Paper tidak membahas problematika norma; klasifikasi ini **tidak diekstraksi** dari paper (hindari mengarang).*

---

## IV. PANGKALAN TEORI, ASAS, DAN DOKTRIN (*THEORETICAL FOUNDATION*)

| Tingkatan Teori / Asas | Nama Teori / Asas Hukum & Tokoh Penggagas | Fungsi & Peranannya dalam Paper Ini |
| :--- | :--- | :--- |
| **Grand Theory** *(Teori Utama/Filosofis)* | — (tidak ada teori hukum dalam paper) | — |
| **Middle Range Theory** *(Teori Antara)* | — | — |
| **Applied Theory** *(Teori Terapan)* | Model NLP Dasar: Word2Vec; arsitektur **IndoBERT** (varian BERT berbahasa Indonesia); tokenizer (NLTK & BERT AutoTokenizer) | Digunakan sebagai alat klasifikasi teks Twitter untuk mendeteksi disinformasi; bukan teori hukum |
| **Asas Hukum** *(Rechtsbeginselen)* | — (paper non-hukum) | — |
| **Doktrin Sarjana** *(Legal Doctrines)* | — | — |

---

## V. ANATOMI PENALARAN HUKUM & METODE ANALISIS (*LEGAL REASONING*)

### 1. Metode Interpretasi Hukum yang Digunakan (Jika Ada *Vague Norm*)
* [ ] Tidak berlaku — paper non-hukum (tidak menafsirkan norma).

### 2. Metode Konstruksi Hukum yang Digunakan (Jika Ada *Wet Vacuum*)
* [ ] Tidak berlaku — paper non-hukum.

### 3. Struktur Silogisme Deduktif / Model IRAC
```text
  [Issue]     : Dapatkah disinformasi politis (Pemilu 2024 Indonesia) di Twitter/X
                dideteksi secara otomatis dengan model bahasa Indonesia?
  [Rule]      : Model klasifikasi IndoBERT (dengan Word2Vec embedding dan dua
                konfigurasi tokenizer: BERT AutoTokenizer vs NLTK + BERT AutoTokenizer).
  [Analysis]  : Dataset tweet dilakukan preprocessing, pelabelan, embedding, lalu
                pelatihan dan evaluasi klasifikasi; akurasi diukur.
  [Conclusion]: IndoBERT mencapai akurasi 85% (konfigurasi BERT AutoTokenizer) dan
                87% (konfigurasi NLTK Tokenizer + BERT AutoTokenizer) — model efektif
                menekan penyebaran disinformasi di media sosial.
```

---

## VI. TEMUAN UTAMA, ARGUMENTASI & PRESKRIPSI (*KEY FINDINGS*)

### 1. Temuan Utama (*Key Findings & Ratio Decidendi*)
*1. Kombinasi IndoBERT dengan **BERT AutoTokenizer** mencapai akurasi **85%** dalam klasifikasi deteksi disinformasi Pemilu 2024 Indonesia.*
*2. Kombinasi IndoBERT dengan **NLTK Tokenizer + BERT AutoTokenizer** mencapai akurasi lebih tinggi (**87%**).*
*3. Model NLP canggih (IndoBERT) terbukti efektif sebagai alat mendeteksi dan menekan penyebaran disinformasi di media sosial berbahasa Indonesia.*

> **Catatan:** paper ini berfokus pada **disinformasi teks** di Twitter/X, bukan deepfake (konten audio/video sintetis). Narasi abstrak tidak menyebut deteksi deepfake. Kedekatannya dengan deepfake bersifat tematik (disinformasi digital dalam pemilu), bukan teknis.

### 2. Preskripsi Hukum / Rekomendasi Pembaharuan (*De Lege Ferenda*)
— *(Paper bersifat teknis-komputasional; tidak memberikan preskripsi hukum atau usulan perubahan norma.)*

---

## VII. EVALUASI KRITIS & IDENTIFIKASI RESEARCH GAP (*CRITICAL APPRAISAL*)

### 1. Kelebihan & Kebaharuan Paper (*Novelty*)
* **Titik Kuat (*Strengths*):** Menguji deteksi disinformasi dalam konteks pemilu Indonesia yang sangat spesifik (Pemilu 2024) menggunakan model bahasa Indonesia (IndoBERT); membandingkan dua konfigurasi tokenizer; mengukur akurasi secara kuantitatif.
* **Kebaharuan (*Novelty*):** Aplikasi IndoBERT untuk deteksi disinformasi pemilu 2024 Indonesia — domain bahasa dan periode pemilu yang belum banyak diuji model serupa.

### 2. Keterbatasan, Kelemahan, & Cacat Logika (*Limitations & Gaps*)
* **Celah Analisis (*Analysis Gap / Analysis Jump*):** Tidak ada dimensi hukum sama sekali — paper menyarankan mitigasi teknis tanpa memetakan norma (mis. UU ITE, Pasal 28/45A jo. UU 1/2024) yang berlaku atas disinformasi; tidak membedakan *disinformation* (teks) dari *synthetic media/deepfake*.
* **Keterbatasan Ruang Lingkup:** Hanya Twitter/X; hanya pemilu presiden 2024; hanya konten teks (bukan video/audio sintetis).
* **Perubahan Posisi Hukum (*Temporal Gap*):** Diterbitkan 2023, sebelum penyelenggaraan Pemilu 2024 dan sebelum penegakan hukum disinformasi pemilu 2024 di Indonesia terdokumentasi; tidak memperhitungkan peraturan pelaksana UU 1/2024 (mis. kebijakan PSE/moderasi konten).

---

## VIII. POSISI & RELEVANSI TERHADAP PENELITIAN SAYA (*RESEARCH POSITIONING*)

| Pertanyaan Evaluatif | Analisis Posisi untuk Skripsi / Penelitian Anda |
| :--- | :--- |
| **Dimana letak kesepakatan (persamaan) paper ini dengan skripsi Anda?** | Paper memperkuat **fakta das sein disinformasi digital pemilu Indonesia** — bahan empiris latar belakang bahwa disinformasi (dan perluasannya deepfake) adalah ancaman nyata integritas informasi pemilu. |
| **Dimana letak perbedaan / pertentangan paper ini dengan skripsi Anda?** | Paper menyelesaikan masalah melalui **teknologi deteksi**, sedangkan skripsi menyelesaikan via **norma hukum** (kualifikasi perbuatan, tanggung jawab, penegakan). Paper non-hukum; skripsi normatif. |
| **Bagaimana paper ini menjadi bukti *Research Gap* bagi skripsi Anda?** | Paper menunjukkan deteksi teknis tanpa kerangka hukum — menegaskan gap bahwa **norma hukum Indonesia yang menjangkau konten sintetis/disinformasi pemilu belum dipetakan secara doktrinal**, terutama definisi "deepfake" dan kualifikasi hukumnya. |
| **Rencana Penempatan dalam Skripsi:** | [x] Bab I (Latar Belakang — fakta disinformasi digital pemilu Indonesia)<br>[ ] Bab II (Tinjauan Pustaka & Kerangka Teori)<br>[x] Bab III/IV (Pembahasan — kontras: pendekatan teknologis vs normatif terhadap disinformasi) |

---

## IX. MATRIKS RINGKASAN EKSTRAKSI CEPAT (*QUICK EXTRACTION CARD*)

```markdown
+------------------------------------------------------------------------------------------------------------------------------------------+
| IDENTITAS PAPER  : A. B. Y. A. Putra, Y. Sibaroni & A. F. Ihsan (2023), "Disinformation Detection on 2024                            |
|                    Indonesia Presidential Election using IndoBERT", Proc. ICoDSA 2023 (IEEE), hlm. 350-355.                              |
| ISU HUKUM        : Disinformasi digital dalam Pemilu 2024 Indonesia sebagai fenomena das sein; paper tidak membahas norma hukum.          |
| TEORI & METODE   : IndoBERT + Word2Vec | Eksperimen NLP (klasifikasi teks, K-Fold CV)                                                     |
| TEMUAN UTAMA     : Akurasi deteksi disinformasi 85% (BERT AutoTokenizer) dan 87% (NLTK + BERT AutoTokenizer).                              |
| RESEARCH GAP     : Tidak ada dimensi hukum; hanya teks (bukan deepfake audio/video); tanpa pemetaan UU ITE/Pasal 28 jo. 45A.             |
| KONTRIBUSI KITA  : Skripsi mengangkat fenomena yang sama (disinformasi digital pemilu) ke ranah norma: kualifikasi hukum konten sintetis. |
+------------------------------------------------------------------------------------------------------------------------------------------+
```

---

## X. CHECKLIST FINAL EKSTRAKSI PAPER

- [x] Identitas bibliografi dan reputasi jurnal telah terverifikasi (Crossref + IEEE Xplore + Semantic Scholar).
- [x] Kesenjangan normatif (Das Sollen vs Das Sein) — direkonstruksi dari abstrak, ditandai sebagai bukan analisis hukum paper.
- [ ] Kerangka teori (Grand, Middle, Applied) — **tidak ada** teori hukum dalam paper; dicatat sebagai keterbatasan.
- [ ] Metode penafsiran/konstruksi hukum — tidak berlaku (paper non-hukum).
- [x] Temuan utama dirangkum dari abstrak; **preskripsi hukum tidak ada** (—).
- [x] Research gap dan keterbatasan paper ditemukan.
- [x] Posisi dan relevansi paper terhadap skripsi ditetapkan (Bab I & III/IV).