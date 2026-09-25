---
title: "Review ULANG (Banding) — Draf Skripsi 'Status Hukum Deepfake di Indonesia'"
artefak: draft_skripsi/BAB_I..V.md + DAFTAR_PUSTAKA.md + audit_report.md
metode: Skill reviewer (knowledge/review-kualitas: 7 Dimensi + 35-Cek + scorecard 15/15/10/15/25/10/10) + verifikasi lintas-korpus (riset/tahap20.md V1–V17, riset/pasal/*, riset/tahap8b_putusan.md, DAFTAR_PUSTAKA 343 entri)
tanggal: 2026-09-25
cakupan: seluruh dokumen (5 bab + daftar pustaka) — review ULANG banding vs draft-skripsi.review.md (75,5/100, Revisi Besar)
status: revisi-besar
---

# LAPORAN REVIEW ULANG (BANDING) DRAF SKRIPSI

## 1. Ringkasan Eksekutif

Review ulang dilakukan terhadap **versi draft yang tidak berubah sejak review
pertama** (git working-tree bersih untuk `draft_skripsi/*.md`; commit terakhir
`c5f5137` menyentuh skill, bukan draft). Kerangka yang sama dipakai ulang:
7 dimensi + 35-Cek + scorecard berbobot, dengan penelusuran tambahan pada
fokus yang diminta: (i) sitasi inline ↔ keterhubungan DAFTAR PUSTAKA;
(ii) penanda `[PERLU VERIFIKASI]` di teks; (iii) subsumsi IRAC per unsur &
tertium comparationis; (iv) scorecard 7 dimensi.

**Tiga perubahan status yang terverifikasi mandiri oleh reviewer:**

1. **Koreksi K2 (sanksi PDP) SUDAH TUNTAS di draft** — konfirmasi positif:
   `BAB_III`:28 menulis "sanksi 66 = **Pasal 68** (≤6 th, denda ≤Rp6 M)
   **[bukan 67]**", konsisten dengan kartu pasal `riset/pasal/pdp-65-67-68.md`
   dan koreksi `riset/tahap20.md` K2/V2. Review pertama menempatkan kekeliruan
   67/68 sebagai temuan; temuan itu **tidak lagi berlaku**. Ini adalah
   satu-satunya perbaikan substantif yang ditemukan antar-review.

2. **Temuan-temuan kritis review pertama SEMUA MASIH BERDIRI** (diverifikasi
   ulang baris-per-baris):
   - **0 sitasi inline** di seluruh 5 bab (0 ekspresi tahun-dalam-kurung,
     0 marker footnote; label `[TERBACA]`/`[F-T]` menunjuk file riset,
     bukan entri pustaka — teks l. BAB_III:91–93, BAB_IV:142–144);
   - **DAFTAR_PUSTAKA tidak terhubung ke teks**: dari 343 entri, 87
     duplikat ekstra (86 grup, signature unik 256), dan ±70 entri non-topik
     (LAPACK, quantum error-correcting, BERT/Attention Is All You Need,
     CoinMarketCap AI Network/Bittensor, pseudopotensial/density-functional,
     LSTM, berita Jessica Wongso Kopi Sianida, putusan MA/PN tanpa relevansi,
     perpustakaan digital & skimming & phishing) — verifikasi mandiri;
   - **Paper & putusan yang dikutip di teks tidak punya entri daftar**:
     4 putusan MK yang dibebani argumen (MK 105/2024, 115/2024, 50/2026,
     282/2025; BAB_III:39–43, BAB_V:31–35) **tidak ada satu pun entri di
     DAFTAR_PUSTAKA**; paper [ABSTRACT] yang dikutip substantif (Han,
     Čučilović, Bhagavathy, Filipova, Nurnisaa, Vainaite, Sakti;
     BAB_II:68–90, BAB_IV:59–76) juga tidak terdaftar → *ghost gap*
     ganda: entri yang ada tak disitasi, klaim yang disitasi tak berentri.

3. **Penanda verifikasi tetap minimal**: hanya 2 `[PERLU VERIFIKASI]` dalam
   teks (ITE 40(6) BAB_IV:48; LPDP BAB_V:38). Premis-premis besar —
   KUHP efektif **2 Januari 2026** + UU 1/2026 mengubah 407/622/172
   (BAB_III:12, BAB_IV:32–36, BAB_V:26), **ketiadaan putusan inkracht**
   (BAB_III:92), dan **5/6 kasus Das Sein** Bab I:32–38 — tetap berdiri
   bulat tanpa tanda, meski `riset/tahap20.md` V1/V7/V17 secara jujur
   menyatakan "belum diverifikasi / sebagian terverifikasi". Pelanggaran
   zero-hallucination parsial (kebenaran konsensus di sumber audit, tetapi
   tidak diterjemahkan ke kontrak traceability skripsi).

Substansi dogmatik tidak berubah dan tetap kuat: pasal inti [TERBACA]
terverifikasi korpus (ITE 27(1)/27A/40, KUHP 172/407/622/624, PDP 66 jo. 68,
TPKS 14), koherensi RM→Bab III/IV→Bab V utuh, kategori cacat norma tepat
(conflict temporal + vague + leemten parsial), preskripsi 5 blok original &
applicable. Yang menghambat menembus ambang "Sangat Layak" tetap pada
**disiplin sitasi/traceability (Dimensi 7)** dan **eksekusi metode
(D3 comparative, D5 subsumsi per unsur, D4 middle-range theory)**.

**Keputusan**: **Diterima dengan Revisi Besar** — total **75,3/100**
(kategori 70–85). Naik tipis (+0,2 dari 75,5) semata akibat konfirmasi
koreksi K2 yang sudah benar di draft; seluruh agenda perbaikan review pertama
belum dieksekusi di draft.

---

## 2. Katalog Temuan (Tabel)

Lokasi dinormalisasi `B#` = baris file; `DP#` = nomor entri daftar pustaka 1–343.

| # | Lokasi/Baris | Kategori | Temuan | Keparahan |
|---|---|---|---|---|
| R1 | `BAB_III` 27–29; `pdp-65-67-68.md` | bahan | **Perbaikan terkonfirmasi**: sanksi PDP ditulis "**66 jo. 68**, bukan 67" — selaras koreksi K2 `tahap20.md`. *Berbeda dari yang dinilai review pertama.* | Positif (perbaikan) |
| R2 | `BAB_III` 39–43; `BAB_V` 31–35 | bahan/trace | 4 putusan MK (105/2024, 115/2024, 282/2025, 50/2026) dijadikan landasan argumen — **terverifikasi ada di tahap8b_putusan.md** ✓ — tetapi **0 entri di DAFTAR_PUSTAKA** → bahan primer yang dikutip tak tertelusur; yang terdaftar malah putusan tak-relevan (DP 6, 69–70, 94, 134–135, 235–236, 293, 295) | Kritis |
| R3 | `BAB_II` 63–90; `BAB_IV` 59–76 | bahan/trace | Paper komparatif yang menjadi tulang preskripsi — Han, Čučilović, Bhagavathy, Filipova, Nurnisaa, Vainaite, Sakti [ABS/MET] — **tidak terdaftar di DAFTAR_PUSTAKA** (grep mandiri nama penulis nihil) → *ghost gap*: klaim disitasi tanpa entri | Kritis |
| R4 | `DP#` seluruh 343 | bahan/trace | **87 duplikat ekstra** (86 grup; 256 signature unik; mis. DP 2–3 Abidin, 12–14 Amelia, 21–23 Ariwibowo, 42–43 Bessoran) — diverifikasi mandiri (regex signature 120-char) | Kritis |
| R5 | `DP#` 5,17,18,38,46,49,53,54,55,56,57,60,61,62,71,72,73,79,88,105,108,110,120,141,155,166,167,168,173,174,176,177,178,184,186,191,222,226,227,235,267,281,290,304,306,320,332… | bahan | **±70 entri non-topik**: LAPACK, quantum error-correction, BERT/Attention Is All You Need, ImageNet/Xception/LSTM/RNN (teknis ML), CoinMarketCap AIN/Bittensor, pseudopotensial density-functional, berita Kopi Sianida Jessica Wongso, putusan MA/PN tanpa relevansi, perpustakaan digital, skimming, phishing, pinjol — sampel terverifikasi | Kritis |
| R6 | `BAB_I..V` semua | trace | **0 sitasi inline** (0 pola `(tahun)`, 0 footnote). Semua klaim menunjuk konvensi file riset (`riset/tahap5.md`, `[TERBACA]`) — daftar pustaka **putus hubungan struktural** dengan teks (audit `audit_report.md`: 0 sitasi terdeteksi, 343 tak dikutip) | Kritis |
| R7 | `BAB_IV` 48; `BAB_V` 38 | trace | Hanya **2 penanda `[PERLU VERIFIKASI]`** dalam teks (PP 40(6), LPDP) — benar adanya, tapi sangat parsial | Penting (sebagian baik) |
| R8 | `BAB_III` 12; `BAB_IV` 32–36; `BAB_V` 26 | trace | Premis "KUHP efektif **2 Januari 2026** (Pasal 624) **diubah UU 1/2026** (butir 407/172/622)" dipakai sebagai premis normatif **tanpa tanda di teks**; `tahap20.md` V1 dinyatakan "butir konkret perubahan Pasal 407/622 oleh UU 1/2026 **masih** [PERLU VERIFIKASI]" → jurang antara sumber audit (jujur) dan teks skripsi (bulat) | Kritis |
| R9 | `BAB_I` 32–38; `tahap20.md` V17 | isu/trace | **6 kasus Das Sein** dikutip sebagai fakta; verifikasi mandiri: hanya kasus **mahasiswi Solo (pole & IAM ditangkap)** terkonfirmasi (tahap1 baris 268; V17 "SEBAGIAN TERVERIFIKASI"); 5 lainnya tetap [BELUM TERVERIFIKASI] tanpa tanda di teks | Penting |
| R10 | `BAB_III` 63–79 | penalaran | **IRAC RM1 — subsumsi tidak per-unsur (bestanddelen)**: fakta hipotetis (wajah Z didistribusikan X tanpa izin) langsung dikonklusikan memenuhi 4 rezim; unsur "tanpa hak", "untuk diketahui umum", mens rea, subjek tidak diuji satu per satu → variasi *analysis jump* (Cek 15/19) | Penting |
| R11 | `BAB_IV` 78–94 | penalaran | **IRAC RM2**: Rule = Triade + klaster komparasi; Analysis = 4 premis fakta → langsung 5 preskripsi tanpa subsumsi "mengapa tiap solusi merupakan kebutuhan normatif sah" | Penting |
| R12 | `BAB_IV` 57–76 | pendekatan | **Tertium comparationis tidak dijalankan**: klaster G (Korea/EU/AS/Denmark/China/India/ASEAN) = daftar label+paper, tanpa matriks kesetaraan (objek, unsur, sanksi, mekanisme) & tanpa uji *non-transferability* (Cek 24) | Kritis |
| R13 | `BAB_II` 61–90 | pendekatan | Sintesis tinjauan pustaka tipis: klaster A–G berupa daftar paper berlabel, tanpa perbandingan tesis/antitesis antar-paper (Cek 12) | Penting |
| R14 | `BAB_II` 35–42; `BAB_III/IV` | teori | Middle-range (Positivisme/Progresif/Dworkin) & Kualifikasi Scholten/Sudikno didaftarkan di Bab I/II tetapi **tidak dieksekusi eksplisit** di Bab III/IV (Cek 25) — konfirmasi review pertama | Penting |
| R15 | `BAB_I` 44 | trace | Rujukan file salah: `riset/tahap1-2.md` (tidak ada) → benar `tahap1.md`+`tahap2.md` — konfirmasi T31 (tidak diperbaiki) | Minor |
| R16 | `BAB_IV` 51 | bahasa | "Perkuat **Best Sob**" — istilah tidak baku (typo) — konfirmasi T32 (tidak diperbaiki) | Minor |
| R17 | `BAB_V` 76–80 | preskripsi | Saran "menutup verifikasi tersisa (V7, V8, V13)" diucapkan di tempat klaim itu sendiri masih belum bertanda → kontrak traceability tidak tertutup | Penting |
| R18 | `BAB_II` 71; `BAB_IV` 126; `BAB_V` 56 | trace | Wicaksono-BBD [F-T] (`DP#323`) dan Utara&Widyawati (`DP#317–318`) — **contoh entri yang benar-benar terdaftar tapi tidak pernah disitasi inline** (kebalikan R3): menyiratkan daftar dibangun dari korpus paper, bukan dari sitasi teks | Penting |
| R19 | `BAB_III` 43 | trace | Jalur `tahap8b_putusan.md` kini ditulis benar (perbaikan minor sejak review pertama) | Minor (baik) |

---

## 3. Scorecard (7 Dimensi)

| No | Dimensi | Bobot | Skor 0–100 | Terbobot | Catatan |
|---|---|---|---|---|---|
| 1 | Formulasi Isu Hukum & Cacat Norma | 15% | 90 | 13,5 | Isu murni *geschil van normen* (conflict temporal ITE↔KUHP via 622 + vague + leemten); RM preskriptif; latar piramida terbalik; minus verifikasi 5/6 kasus Das Sein (R9) |
| 2 | Kebersihan, Hierarki & Validitas Bahan Hukum | 15% | 83 | 12,45 | Pasal inti [TERBACA] terverifikasi korpus; **K2 SUDAH benar** (+positif sejak review pertama); hierarki Stufenbau/asas preferensi tepat; minus besar: DP rusak (87 duplikat + ±70 non-topik) dan **putusan MK/paper komparatif yang dikutip tak punya entri** (R2–R5) |
| 3 | Konsistensi Pendekatan Penelitian | 10% | 70 | 7,0 | Statute/Conceptual/Case (ratio) terpakai; **Comparative tanpa tertium comparationis** (R12); sintesis pustaka tipis (R13) |
| 4 | Arsitektur Kerangka Teoritis & Asas | 15% | 75 | 11,25 | Three-tier terdefinisi; Radbruch/Stufenbau berfungsi; **Middle-range Progresif/Dworkin & Kualifikasi Scholten belum dieksekusi** di Bab III/IV (R14) |
| 5 | Rigoritas Penalaran & Rechtsvinding | 25% | 72 | 18,0 | IRAC struktural utuh & premis pasal benar; **subsumsi tidak per-unsur** (R10), interpretasi tak berurutan, konstruksi (analogi/a-contrario) belum dioperasikan eksplisit meski leemten ada; larangan analogi dijaga implisit |
| 6 | Mutu Preskripsi & Kebahruan (Novelty) | 10% | 78 | 7,8 | 5 blok preskripsi konkret & applicable (definisi, delik khusus, harmonisasi Pasal Z, pelabelan+forensik, jalur perdata/admin+korporasi); novelty orisinal; minus: komparasi berdiri di [ABSTRACT] tak terdaftar (R3) & tak diuji Triade/legisprudensi eksplisit |
| 7 | Sistematika, Bahasa & Traceability | 10% | 52 | 5,2 | Bahasa akademis lugas; **tapi 0 sitasi inline, DP putus hubungan (ghost gap), 87 duplikat, ±70 non-topik, hanya 2 tanda [PERLU VERIFIKASI]**, premis besar tanpa tanda (R6–R8). Naik tipis karena penanda 40(6) & jalur tahap8b telah ada/perbaikan minor |
| | **TOTAL** | **100%** | | **75,3** | **Kategori: 70–85 → DITERIMA DENGAN REVISI BESAR** |

**Ambang**: 86–100 Sangat Layak · 70–85 Diterima dengan Revisi · <70 Ditolak.
Total 75,3 berimpit dengan review pertama (75,5): **naik tipis +0,2** (D2
terangkat karena K2 sudah benar — sebelumnya dinilai sebagai kelemahan
Dimensi 2), namun seluruh agenda perbaikan substantif belum dieksekusi.

---

## 4. Kekuatan (Strengths)

1. **Anchor pasal [TERBACA] kokoh & terverifikasi**: ITE 27(1)/27A/40, KUHP
   172/407/622/624, PDP 66 jo. 68, TPKS 14 — konsisten dengan kartu
   `riset/pasal/*.md`; label [TERBACA] adalah praktik traceability yang jernih.
2. **Koherensi lintas bab**: RM Bab I dijawab persis Bab III (lex lata,
   klaster A–D) dan Bab IV (de lege ferenda, klaster E–G); Bab V bukan
   ringkasan — simpulan preskriptif koheren dengan premis.
3. **Tipologi cacat norma tepat** (conflict temporal + vague + leemten
   parsial) dan dipetakan ke pasal nyata — tidak mengarang konflik.
4. **Preskripsi original & actionable**: 5 blok dengan basis [TERBACA] dan
   kartu paper; rajut komparasi Korea/EU/AS/Denmark/China menjadi usulan
   executable, bukan sekadar rekomendasi.
5. **Etika integritas di sumber audit**: `riset/tahap20.md` V1/V7/V17
   mendaftar apa yang belum terverifikasi (efektif UU 1/2026, putusan
   inkracht, 5/6 kasus) — kejujuran di tahap riset; yang kurang adalah
   komitmen yang sama di **teks skripsi**.
6. **Koreksi K2 sudah tuntas di draft** (sanksi PDP 66 jo. 68) — bukti
   mekanisme audit→revisi berfungsi.

---

## 5. Rekomendasi Perbaikan (prioritas)

1. **[Kritis] Tutup *ghost gap* daftar pustaka ↔ teks (Cek 32/33/35).**
   - Tambahkan footnote/endnote inline per klaim pasal & paper (format
     IA-Turabian: `ITE 27(1) jo. 45(1)`; `MK Putusan No. 105/PUU-XXII/2024`),
     sehingga tiap klaim punya entri terkait.
   - Tambahkan **entri untuk 4 putusan MK** (105/2024, 115/2024, 50/2026,
     282/2025) dan **paper komparatif** (Han, Čučilović, Bhagavathy,
     Filipova, Nurnisaa, Vainaite, Sakti) yang kini dikutip tanpa entri.
   - Hapus 87 duplikat + ±70 entri non-topik (DP 17, 46, 49, 54–55, 61–62,
     72, 155, 176, 177, 222, 226, 304, 306, 320, 5, 38, 53, 57, 60, 105,
     108, 168, 74, 173, 184, 267, 281, 332, dst).
2. **[Kritis] Terjemahkan daftar [PERLU VERIFIKASI] `tahap20.md` ke teks.**
   - Beri `[PERLU VERIFIKASI]` di tempat premis dipakai: KUHP efektif
     2-1-2026 + efek UU 1/2026 pada 407/622/172 (BAB_III/IV/V);
     ketiadaan putusan inkracht (BAB_III catatan); 5/6 kasus Bab I;
     PP 40(6) & LPDP (sudah ber-tanda).
   - Tambahkan daftar penutup Bab V berisi seluruh item [PERLU VERIFIKASI]
     agar kontrak traceability tertutup (Cek 33).
3. **[Penting] Subsumsi IRAC per unsur.** Pecah fakta hipotetis (IRAC RM1)
   ke tiap bestanddeel (subjek→dolus→tanpa hak→perbuatan→objek→"untuk
   diketahui umum") dan nyatakan terpenuhi/tidak per unsur; tampilkan urutan
   interpretasi gramatikal→teleologis→restriktif; operasikan konstruksi
   (analogi/a-contrario) dengan batas asas legalitas untuk leemten.
4. **[Penting] Tertium comparationis klaster G.** Buat matriks simetris
   (negara, instrumen, definisi, unsur, sanksi/mekanisme) + evaluasi
   non-transferability (mis. Korea substantial-vs-exact vs sistem pidana RI;
   Denmark copyright-likeness vs UU 28/2014) (Cek 24).
5. **[Penting] Eksekusi middle-range theory.** Nyatakan bagaimana
   Positivisme/Progresif/Dworkin dan Kualifikasi Scholten/Sudikno dipakai
   membedah argumen MK 105/2024 & 50/2026 (bukan hanya didaftarkan).
6. **[Penting] Uji Triade Radbruch & legisprudensi atas tiap preskripsi.**
   Untuk tiap 5 blok: keseimbangan keadilan–kepastian–kemanfaatan & batas
   legalitas (evitasi konflik baru dgn UU 1/2026; non-ambiguity redaksi).
7. **[Minor] Koreksi teknis**: `tahap1-2.md`→`tahap1.md`+`tahap2.md`
   (BAB_I:44); "Perkuat Best Sob"→rumusan baku (BAB_IV:51); pastikan
   Wicaksono-BBD & Utara&Widyawati disitasi inline agar terhubung.

---

## 6. Keputusan Akhir Reviewer

**Diterima dengan Revisi Besar** (total **75,3/100**, kategori 70–85),
**konfirmasi** keputusan review pertama (75,5/100) dengan **naik tipis
(+0,2)** — satu-satunya perubahan material antar-review adalah **koreksi
K2 (PDP 66 jo. 68) yang sudah benar di draft**. Seluruh agenda perbaikan
kritis review pertama (ghost gap daftar↔teks, tanda [PERLU VERIFIKASI],
subsumsi per unsur, tertium comparationis, eksekusi teori) **belum
dieksekusi di draft**.

Syarat sebelum sidang (tidak berubah dari review pertama):
- Daftar pustaka dibersihkan (duplikat/non-topik) & disitasi inline per
  klaim + entri putusan MK & paper komparatif ditambahkan;
- Seluruh premis yang belum terverifikasi diberi tanda & didaftarkan;
- Subsumsi IRAC per unsur, tertium comparationis, dan eksekusi
  middle-range theory dilengkapi.

Setelah itu karya layak menembus ambang 86+ (Sangat Layak). Fondasi
dogmatik, koherensi, dan orisinalitas preskripsi sudah di atas rata-rata
skripsi hukum normatif; penghambatnya murni disiplin penulisan sitasi dan
operasionalisasi metode.