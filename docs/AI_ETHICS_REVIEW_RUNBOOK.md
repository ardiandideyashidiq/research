# Runbook: Literature Review dari File .bib

Alur baku untuk Turning a `.bib` export into a template-conformant literature
review, dengan penghematan token lewat **relevance-ranked, capped snowball**.

## Kapan dipakai

Ketika pengguna memberi file `.bib` (export dari Zotero/Mendeley/Google
Scholars) dan meminta review literatur. Ini bukan output `research` CLI biasa:
ini pipeline di mana persiapan (retrieval, dedup, snowball) selesai dulu,
lalu review ditulis subagent.

## Perintah

```bash
# 1. Diagnosa dulu: berapa entri unik?
uv run python - <<'PY'
from research.bibtex.parser import parse_bib_file
raw = parse_bib_file("refs.bib")
uniq = {e.doi.lower() for e in raw if e.doi}
print(f"{len(raw)} entries, {len(uniq)} unique DOIs")
PY

# 2. Bangun run (dedup + ranked snowball + Unpaywall + packets)
uv run research review-run \
  --bib refs.bib \
  --relevance-query "<topik yang dicari>" \
  --relevance-top-k 10 \
  --relevance-min-score 0.3 \
  --seeds 3 \
  --snowball-limit 20 \
  --out tmp/<nama>_review

# 3. Lihat hasilnya
cat tmp/<nama>_review/manifest.json
```

## Membaca Manifest

| Label | Arti | Boleh? |
|---|---|---|
| `FULL-TEXT` | Markdown full text ada di disk (`data/markdown/<cite_key>.md`) | Kutip isi dengan[rxu] blok/sebut halaman |
| `ABSTRACT` | Hanya abstrak (Crossref/OpenAlex) | **Jangan kutip isi**; label `[ABSTRACT]` di kartu |
| `METADATA` | Hanya judul/penulis | Kartu minimal, sebagian besar "—" |

> Penting: label di manifest adalah **ground truth saat run**. Kalau reviewer
> berhasil memperoleh full text yang lebih baik dari packet, ia harus
> **mencatat koreksinya secara eksplisit** di kartu (seperti yang dilakukan
> kartu Astuti).

## Menulis Review (per-paper subagent)

Satu subagent per paper. Prompt memuat: cite key, packet path, output path,
dan aturan label. Subagent **wajib** mengisi `template-analisis-paper.md` I–X
termasuk blok enrichment:

- **2b Teknik penalaran penulis** — dekonstruksi unsur? pemetaan rezim?
  struktur argumen? komparasi? preskripsi konkret/konseptual?
- **2c Pasal/dokumen** — status `[VERBATIM]` / `[RUJUKAN]` / `[TAK DISEBUT]`.
  Paper filsafat/agama biasanya **[TAK DISEBUT] — catat sebagai methodological gap**.
- **2d Kritik** — analysis jump? batasan legalitas? data tak terverifikasi?
  celah komparasi?
- **Research-gap mapping** — kaitkan ke gap skripsi.

## Interpretasi Skor Relevansi

Skor di manifest = **tumpang tindih kata kunci**, bukan relevansi substantif.
Paper Teologi/filosofi bisa saja diskor 0,85 hanya karena kata
"kecerdasan buatan" muncul — review **wajib** menilai relevansi substantif
sendiri dan menandainya di bagian VIII. Contoh nyata: dari 7 paper pada
`riset/aiethics/`, **4 tidak memuat hukum Indonesia sama sekali**.

## Full-Text Quandary

Banyak penerbit (OJS Indonesia, Elsevier, Springer) memblokir traffic
datacenter dengan HTTP 403 meski TLS Chrome impersonationthroughout.
`failed_blocked` adalah hasil **jujur**, bukan bug — jangan dipaksa retries.
Jika akses institution tersedia, coba:

```bash
uv run research fulltext "<DOI>" --pdf-url "<URL PDF langsung dari jurnal>"
```

## Guardrails

- **Jangan `curl` manual** untuk PDF. Kalau `fulltext` gagal, catat
  `failed_blocked`; kalau kamu memakai workaround dengan tangan, itu
  **bug** yang harus diperbaiki di `src/research/downloader/` atau
  `src/research/cli/main.py`, bukan di skirt.
- **Dedup selalu**: `...2` suffixed cite keys = paper yang sama.
- **Relevance floor wajib** (`--relevance-min-score`): tanpa itu, seed
  off-topic menarik sitasi off-topic.
- **Label jujur**: tidak boleh `[FULL-TEXT]` tanpa Markdown di disk.

## Troubleshooting

| Gejala | Penyebab | Solusi |
|---|---|---|
| `Unique seeds: 0` | DOI tidak ada di DB | `research search` dulu untuk mengindeks |
| Semua `seed=0` referred | Judul non-Inggris / ejaan beda | `relevance-query` pakai istilah lokal juga |
| `Ranked out` = 0, `dropped` tinggi | Query terlalu sempit | Longgarkan `relevance_min_score` |
| Full text selalu 403 | Penerbit memblokir datacenter | Institutional access via `--pdf-url`; jangan retry buta |
| `fulltext` bilang gagal padahal PDF ada | **Fixed** — record transien tak ter-insert (lihat `src/research/cli/main.py` `fulltext`) | — |
