---
title: Tahap 8b — Perluasan Korpus Sumber (Enrichment ≥50)
description: >-
  Perluasan korpus lintas jenis sumber SETELAH penelitian pendahuluan & SEBELUM analisis:
  literatur (+28 paper), yurisprudensi (putusan MK), regulasi pelaksana, doktrin, berita/web.
status: draft
jenis: temuan-riset
tanggal: 2026-09-25
---

# Tahap 8b: Perluasan Korpus Sumber (Target ≥50)

Ditempatkan **setelah Tahap 4 (rumusan masalah) & sebelum Tahap 13 (analisis)**
— sesuai prinsip: korpus harus kaya sebelum penalaran, dan penelitian
pendahuluan selesai sebelum perluasan berdiri sendiri. Ini tahap *enrichment*,
bukan inventarisasi awal (Fase III Tahap 8–10).

## Target & Komposisi

| Jenis | Basis awal | Tambahan | Target | Status |
|---|---|---|---|---|
| Literatur (paper/jurnal) | 22 | +28 (22 selesai: 6 Hak Cipta/Identitas/Biometrik + 7 Deepfake/Pemilu/Disinformasi Global + 6 Pertanggungjawaban Pidana & AI + 3 Subjek Hukum/Hak Cipta & Analogi Korporasi) | **50** | ⏳ 44/50 — 22 kartu ditulis `tahap8b_paper/` (Chacko, Schwartz, Pechenin, Westkamp, Bosher, Ochoa, Groh, Pawelec, BirrerJust, Chesterman, RomeroMoreno, Filipova, Walter, Hailtik, Bessoran, RahmanHabibulah, Sofian, Pamungkas, Indarto, Liu, PatilMishra, DaudAbdGhaniAzmi, Ariani, VanderSloot, GorwaVeale, RamaPrasadaMahadewi, SujatmikoSuronoRangsimanop, JayaGoh) |
| Yurisprudensi (putusan MK/PN) | 2 (via paper) | +~20 putusan MK relevan | 20+ | ⏳ subagent berjalan |
| Regulasi & pelaksana (PP, permen, pasal UU) | pasal inti | PP PSE/71, PP 40(6), PDP 5–11, dsb. | banyak | ⏳ subagent berjalan |
| Doktrin (buku/laporan) | knowledge base | +buku/laporan | ~5–10 | ⏳ via knowledge |
| Berita/web (kasus riil) | 6 kasus | verifikasi + tambah | ~8 | ⏳ |

> Total lintas jenis **≥50** (kuantitas sumber terverifikasi, bukan cuma paper).

## Sumber Output

- `riset/tahap8b_paper/PAPER_*.md` — kartu paper baru (4 tema × 6).
- `riset/tahap8b_putusan.md` — daftar putusan MK uji KUHP/ITE.
- `riset/tahap8b_regulasi.md` — daftar regulasi pelaksana & pasal baru.
- `riset/tahap8b_doktrin.md` — [diisi kemudian] buku/laporan.
- `riset/tahap8b_berita.md` — [diisi kemudian] kasus/berita verifikasi.

## Literatur Baru (Subagent: Hak Cipta, Identitas/Likeness, & Data Biometrik — AI)

Enam paper pertama (22 → 28) — semua DOI-unik, tidak tumpang tindih kartu
`literature-review/` (Marlan, Zigo, Jasserand, Rezvorovych, dsb.). Kartu:
`riset/tahap8b_paper/`.

| # | Cite Key | Judul | DOI (unik) | Label | Isi inti |
|---|---|---|---|---|---|
| 23 | Chacko2026 | Cloning the Persona: Personality and Publicity Rights in the Age of AI Deepfakes and Voice Cloning in India | 10.63090/ijjr/3139.177x.0014 | [ABSTRACT] | Yurisprudensi India (Bachchan, Kapoor, Shroff, Arijit Singh) merakit perlindungan persona tanpa statuta; usul framework legislatif |
| 24 | Schwartz2026 | AI Influencers and a Right of Publicity | 10.52214/jla.v49i2.14632 | [ABSTRACT + OA PDF] | Apakah right of publicity berlaku bagi virtual/AI influencers (Columbia J. Law & Arts 49(2), 355-407) |
| 25 | Pechenin2026 | Consent for Processing Biometric Personal Data by Generative AI | 10.17803/2542-2472.2026.38.2.014-025 | [ABSTRACT + OA PDF] | Gap sistemik consent data biometrik AI; T&C GigaChat/DeepSeek melempar tanggung jawab ke pengguna |
| 26 | Westkamp2026 | The Freedom to Mine and Train AI Models and the Limits of Copyright and Personality Rights | 10.2139/ssrn.7396221 | [ABSTRACT] | Kritik GEMA v. OpenAI; copyright/personality sebagai counter-rights atas AI training |
| 27 | Bosher2026 | Do Deepfakes, Digital Replicas and Human Digital Twins Justify Personality Rights? | 10.1111/jwip.70020 | [ABSTRACT] | Usul personality rights Inggris: hak otomatis unwaivable 70 tahun post-mortem |
| 28 | Ochoa2023 | Overlaps Between Copyright, Rights of Publicity, and Personality Rights | 10.1093/oso/9780192844477.003.0009 | [ABSTRACT] | Peta tumpang tindih copyright/publicity/personality US-UK-EU (OUP) |

Catatan integritas: tidak ada full-text penuh yang diunduh pada batch ini; keenam
kartu memakai abstrak panjang terverifikasi (OpenAlex/Crossref) + dua PDF OA
dikonfirmasi. Semua klaim dibatasi pada abstrak, tidak ada halusinasi; posisi
masing-masing paper terhadap skripsi tidak dibumbui.

## Literatur Baru #2 (Subagent: Deepfake, Pemilu & Disinformasi Global — Perbandingan Negara)

Enam paper kedua (28 → 34) — tema **deepfake & politik/disinformasi (pemilu) +
perbandingan negara baru**. Anti-duplikasi: dicek tidak tumpang tindih kartu
`literature-review/` (Vainaite UE, Canares ASEAN, Putra deteksi pemilu, dsb.)
dan tidak duplikat DOI di `publications`. Satu paper **full-text** (Groh);
sisanya abstrak panjang terverifikasi (OpenAlex/Crossref).

| # | Cite Key | Judul | DOI (unik) | Label | Isi inti |
|---|---|---|---|---|---|
| 29 | Groh2024 | Human detection of political speech deepfakes across transcripts, audio, and video | 10.1038/s41467-024-51998-z | [FULL-TEXT] | 5 eksperimen pra-registrasi (N=2215): manusia tak terpengaruh basis rate; TTS mutakhir lebih sulit dideteksi; audio-visual > teks (Nature Comm. 15:9112) |
| 30 | Pawelec2022 | Deepfakes and Democracy (Theory): How Synthetic Audio-Visual Media for Disinformation and Hate Speech Threaten Core Democratic Functions | 10.1007/s44206-022-00010-6 | [ABSTRACT] | Deepfake melemahkan empowered inclusion, collective will-formation & legitimasi keputusan kolektif (Digital Society 1(2):19) |
| 31 | BirrerJust2024 | What we know and don't know about deepfakes: An investigation into the state of the research and regulatory landscape | 10.1177/14614448241253138 | [ABSTRACT] | Gap riset-regulasi global deepfake; alarmisme; penegakan aturan lama lebih krusial (New Media & Society 27(12):6819-6838) |
| 32 | Chesterman2024 | Lawful but Awful: Evolving Legislative Responses to Address Online Misinformation, Disinformation, and Mal-Information in the Age of Generative AI | 10.1093/ajcl/avaf020 | [ABSTRACT] | Dataset legislasi global; mulai di negara kurang bebas/miskin; kini paling curam di Barat (Am. J. Comp. L. 72(4):933-965) |
| 33 | RomeroMoreno2024 | Generative AI and deepfakes: a human rights approach to tackling harmful content | 10.1080/13600869.2024.2324540 | [ABSTRACT] | AIA (EU AI Act) perlu amendemen: data sintetis utk deteksi & klasifikasi high-risk utk deepfake berbahaya (IRLCT 38(3):297-326) |
| 34 | Filipova2024 | Legal Regulation of Artificial Intelligence: Experience of China | 10.21202/jdtl.2024.4 | [ABSTRACT] | Model Tiongkok: iteratif & sektoral, tanpa undang-undang umum (umbrella law) — studi banding (J. Digital Technologies & Law 2(1):46-73) |
| 35 | Walter2024 | Managing the race to the moon: Global policy and governance in AI regulation | 10.1007/s44163-024-00109-4 | [ABSTRACT] | Perbandingan regulasi AS/UE/Asia/Afrika/Amerika; usul model "dynamic laws" adaptif (Discover AI 4:31) |

Catatan integritas: 1 kartu (Groh) full-text verifikasi (PDF OA diunduh & dibaca);
6 kartu memakai abstrak penuh terverifikasi; label [FULL-TEXT]/[ABSTRACT] jujur.
Semua klaim dibatasi metadata/abstrak/teks penuh yang dibaca — no hallucination.

## Literatur Baru #3 (Subagent: Pertanggungjawaban Pidana & Kecerdasan Buatan — Indonesia)

Enam paper ketiga (35 → 41) — tema **pertanggungjawaban pidana & AI di
Indonesia** (subjek hukum AI, model atribusi pidana AI, deepfake crime, data
pribadi berbasis AI, kekosongan hukum penegakan). Anti-duplikasi: dicek tidak
tumpang tindih DOI kartu `literature-review/` (tidak ada satupun yang
bertabrakan dengan 22 paper basis) dan tidak duplikat di `publications`.
**Semua 6 paper berlabel [FULL-TEXT]** — PDF OA diunduh via
`uv run research fulltext "<doi>"` (Unpaywall) & konversi Markdown penuh dibaca
(`data/markdown/10_*.md`). DOI diverifikasi via Crossref `works` + Unpaywall.

| # | Cite Key | Judul | DOI (unik) | Label | Isi inti |
|---|---|---|---|---|---|
| 36 | Hailtik2024 | Criminal Responsibility of Artificial Intelligence Committing Deepfake Crimes in Indonesia | 10.59888/ajosh.v2i4.222 | [FULL-TEXT] | AI tak dapat dipidana (tak ada *mens rea*/kesadaran); model PVM & NPCLM applicable utk deepfake (pelaku = programmer/pengguna); DLM belum applicable; regulasi terbatas UU ITE (AI = sistem elektronik/electronic agent) |
| 37 | Bessoran2026 | Pertanggungjawaban Pidana Terhadap Penyalahgunaan Kecerdasan Buatan dalam Tindak Kejahatan Digital di Indonesia | 10.61234/ahd.v4i1.108 | [FULL-TEXT] | AI = mediator kejahatan kompleks (deepfake, voice cloning, penipuan digital 2023–26); KUHP/ITE/PDP belum akomodasi AI → gap atribusi; usul *risk-based liability* + *vicarious liability* kombinatif individu-korporasi |
| 38 | RahmanHabibulah2019 | The Criminal Liability of Artificial Intelligence: Is It Plausible to Hitherto Indonesian Criminal System? | 10.22219/jihl.v27i2.10153 | [FULL-TEXT] | Paper fondasional: AI tak bisa dipidana kini (subjek hukum = manusia + korporasi); tiga model Hallevy dapat jadi jembatan atribusi Indonesia; kasus bot hoax Kominfo 2016 |
| 39 | Sofian2025 | Konsepsi Subjek Hukum dan Pertanggungjawaban Pidana Artificial Intelligence | 10.33561/holrev.v9i1.129 | [FULL-TEXT] | KUHP Baru (UU 1/2023) tetap tak kenal AI sbg subjek hukum; kendala mengukur *mens rea* AI; atribusi perlu kontribusi manusia-korporasi; usulan registrasi AI sbg *legal person/moral agent* |
| 40 | Pamungkas2026 | Pertanggungjawaban Pidana atas Pelanggaran Data Pribadi Berbasis Kecerdasan Buatan (Komparasi Indonesia–UE–Singapura) | 10.24127/mlr.v10i2.5438 | [FULL-TEXT] | Deepfake crime = kategori kejahatan data biometrik; 3 gap kritis Indonesia (definisi AI, *mens rea* otonom, strict liability korporasi) → "zona impunitas"; perbandingan GDPR/EU AI Act/PDPA |
| 41 | Indarto2024 | Legal Uncertainty in Criminal Enforcement with the Use of Artificial Intelligence Technology in Indonesia | 10.69726/ijlssm.v1i1.13 | [FULL-TEXT] | AI bukan subjek hukum UU ITE (Pasal 1 angka 1); *legal vacuum* AI dlm penegakan hukum; reformasi UU ITE + PP utk kepastian hukum |

Catatan integritas: enam kartu ini **full-text penuh** (bukan abstrak) — PDF OA
diunduh via `research fulltext` (Unpaywall resolve → download %PDF verified →
convert Markdown), dibaca halaman-ke-halaman. Semua klaim per paper bersumber
teks penuh; posisi terhadap skripsi tidak dibumbui.

## Literatur Baru #4 (Subagent: Tanggung Jawab Platform & Moderasi Konten AI)

Enam paper keenam (41 → 47) — tema **platform liability, content moderation
AI, & PSE** (yang hanya Nicoli di 22 paper basis). Anti-duplikasi: dicek tidak
tumpang tindih DOI kartu `literature-review/` (tidak ada yang bertabrakan
dengan 22 paper basis; termasuk tidak duplikat vs `10.2139/ssrn.6795784`
Nicoli) dan tidak duplikat di kartu `tahap8b_paper/` lain. **4 kartu
berlabel [FULL-TEXT]** (PDF OA diunduh via `uv run research fulltext "<doi>"`
& Markdown dibaca penuh di `data/markdown_tahap8b/`), **2 kartu berlabel
[ABSTRACT]** (paywall Elsevier/T&F — abstrak diverifikasi penuh via OpenAlex;
PDF diblokir HTTP 403). DOI diverifikasi via Crossref `works` + OpenAlex.

| # | Cite Key | Judul | DOI (unik) | Label | Isi inti |
|---|---|---|---|---|---|
| 42 | Liu2025 | Normative Construction of Platform Criminal Liability in the Governance of Deepfake Technology | 10.54254/2753-7102/2025.23777 | [FULL-TEXT] | Tanggung jawab pidana platform atas deepfake (RRT): notice-and-takedown gagal tangkap platform lalai; usul presumption of knowledge, duty of care, tiered compliance, dual-layer accountability korporasi-eksekutif (Adv. Social Behavior Research 16(4):47-53) |
| 43 | PatilMishra2026 | Platform Liability and Deepfake Pornography: Are India's Intermediary Rules Fit for the AI Age? | 10.70183/lijdlr.2026.v04.50 | [FULL-TEXT] | Rejim Section 79 IT Act + Rules 2021 (notice-and-takedown) inadekuat atas deepfake porno yang diamplifikasi algoritma; algorithmic amplification membongkar fiksi netralitas; usul *dignity-centric* risk-based platform governance (LawFoyer 4(1):1146-1177) |
| 44 | DaudAbdGhaniAzmi2023 | Intermediary's Liability: Towards a Sustainable AI-Based Content Moderation in Malaysia | 10.31436/iiumlj.v31i2.823 | [FULL-TEXT] | Analisis Mkini, Delfi, Bunt, Godfrey: liabilitas bergantung jenis konten & kontrol; AI moderasi tak boleh di-mandate sebagai syarat immunity; konteks > kata dalam algoritma (IIUM Law J. 31(2):155-178) |
| 45 | Ariani2024 | Pertanggungjawaban Hukum PSE Telegram dalam Kegiatan Produksi Konten Pornografi Menggunakan Fitur Bot Terintegrasi Deepfake | 10.58812/jmws.v3i12.1751 | [FULL-TEXT] | Paper Indonesia kunci: produksi porno via bot deepfake = melawan hukum (UU Pornografi 4(1) jo UU ITE 27(1), ekstrateritorial Pasal 2); PSE Telegram BEBAS karena safe harbour Pasal 11 Permenkominfo 5/2020 (TOS, fitur laporan, transparansi, pemutusan akses) — indirect infringement (J. Multidisiplin West Science 3(12):1851-1860) |
| 46 | VanderSloot2022 | Deepfakes: Regulatory Challenges for the Synthetic Society | 10.1016/j.clsr.2022.105716 | [ABSTRACT] | Deepfake (fake news, pemilu, bukti palsu, fake porno) mengancam demokrasi/rule of law; rejim privacy/data protection kini diragukan memadai; perlu amendemen + aturan ex ante & pembatasan ekspresi (Computer Law & Security Review 46:105716; 112 sitasi) |
| 47 | GorwaVeale2024 | Moderating Model Marketplaces: Platform Governance Puzzles for AI Intermediaries | 10.1080/17579961.2024.2388914 | [ABSTRACT] | Model marketplaces (Hugging Face, GitHub, Civitai) menurunkan hambatan deployment model berbahaya; dual nature konten-tool mempersulit moderasi; praktik industri (licensing, access restriction, autofilter, community takedown) masih terbatas (Law, Innovation and Technology 16(2):341-391) |

Catatan integritas: 4 kartu full-text penuh (PDF OA diunduh & dibaca
halaman-ke-halaman: Liu, Patil-Mishra, Daud-Abd Ghani Azmi, Ariani);
2 kartu [ABSTRACT] — abstrak penuh terverifikasi via OpenAlex (van der Sloot
Elsevier & Gorwa-Veale T&F diblokir PDF, HTTP 403), PDF OA tidak tersedia;
semua klaim dibatasi sumber yang dibaca, no hallucination. Posisi terhadap
skripsi tidak dibumbui. Paper panduan kasus asli yang juga ditemukan
(BhagavathyV2026, DOI 10.69662/jllrd.v3i3.76) **tidak** dimasukkan karena
sudah menjadi bagian 22 paper basis.

## Literatur Baru #5 (Subagent: Subjek Hukum, Hak Cipta AI & Analogi Pertanggungjawaban Korporasi)

Tiga paper tambahan (47 → 50) — menutup target **50 paper**. Ketiga PDF sudah
terunduh di `data/downloads/` (DOI sesuai nama file) dari sesi
snowball/sebelumnya; dikonversi Markdown & dibaca penuh. Anti-duplikasi: DOI
ketiganya berbeda dari 22 kartu `literature-review/` maupun 25 kartu
`tahap8b_paper/`; juga bukan duplikat `publications`/`data/markdown_tahap8b/`.
**Semua 3 kartu berlabel [FULL-TEXT]** — konversi Markdown penuh dibaca
halaman-ke-halaman (`data/markdown_tahap8b/10_*.md`); DOI diverifikasi via
Crossref `works`.

| # | Cite Key | Judul | DOI (unik) | Label | Isi inti |
|---|---|---|---|---|---|
| 48 | RamaPrasadaMahadewi2023 | Urgensi Pengaturan *Artificial Intelligence* (AI) dalam Bidang Hukum Hak Cipta di Indonesia | 10.56013/rechtens.v12i2.2395 | [FULL-TEXT] | UUHC tidak kenal AI sebagai subjek hukum & tak atur ciptaan AI (Pasal 54 pun tanpa istilah AI); potensi AI dipersamakan badan hukum via teori fiksi/organ + *Work Made For Hire* US; rekomendasi UU khusus AI (J. Rechtens 12(2)) |
| 49 | SujatmikoSuronoRangsimanop2025 | Corporate Criminal Liability in Tax Crimes in Indonesia | 10.56107/penalaw.v3i2.240 | [FULL-TEXT] | Peta doktrin pidana korporasi paling matang (identification/*directing mind*, vicarious, strict liability; KUHP baru 45–52 denda Rp50M; Perma 13/2016; PMK 17/2025); kritik *overcriminalization* korporasi kecil & DJP rangkap peran; analogi atribusi platform deepfake (PENA LAW 3(2)) |
| 50 | JayaGoh2021 | Analisis Yuridis Kedudukan Kecerdasan Buatan (AI) sebagai Subjek Hukum pada Hukum Positif Indonesia | 10.33592/jsh.v17i2.1287 | [FULL-TEXT] | AI yang mampu perbuatan hukum = subjek hukum sederajat badan hukum (UU ITE hanya tempatkan AI sbg "Informasi Elektronik"); tanggung jawab di Pencipta + Pengguna AI; usul UU khusus AI + akta otentik identitas AI (Supremasi Hukum 17(2)) |

Catatan integritas: tiga kartu ini **full-text penuh** — PDF OA diunduh dari
`data/downloads/` & dibaca halaman-ke-halaman; semua klaim bersumber teks
penuh, posisi terhadap skripsi tidak dibumbui, label [FULL-TEXT] jujur.
Posisi ke-skrpsi: #48 memperkuat bab hak cipta/perdata (likeness-biometrik),
#49 memberi analogi atribusi pidana korporasi untuk bab pertanggungjawaban
platform, #50 menyediakan argumen pro-AI-subjek-hukum (counter-argument untuk
bab subjek hukum). Paper yang tersisa dari daftar kandidat PDF (`10_21275_sr24724150350`
IJSR/Mantri — moderasi konten AI teknis 3 halaman, pustaka tidak berkaitan;
`10_59188_jurnalsostech_v5i6_32207` SOSTECH — AI dalam sistem peradilan pidana,
fokus lebih luas; `10_56895_plr_v12i1_1644` PLR — revenge porn UU ITE/TPKS,
menarik untuk konteks korban namun tanpa unsur AI/deepfake) dinilai kurang tajam
terhadap isu deepfake/AI-legal dan tidak dimasukkan pada batch ini.

## Integritas

- Paper baru: full-text first (AGENTS #6), label [FULL-TEXT]/[ABSTRACT]/[METADATA], DOI unik.
- Pasal/regulasi: verifikasi MCP [TERBACA], cek amendemen & MK.
- Putusan: hanya dari korpus (nomor & amar nyata), dgn implikasi utk deepfake.