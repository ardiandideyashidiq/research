---
name: literature-review
description: >-
  Runs a subagent-driven literature review of Indonesian legal scholarship on a
  topic: federated/Crossref discovery, full-text retrieval via
  `research fulltext`, per-paper analysis cards under
  knowledge/penulisan/abstrak-normatif.md, dedup by DOI, epistemic labelling
  ([FULL-TEXT]/[ABSTRACT]/[METADATA]), and a synthesis matrix. Use when the user
  asks to review literature, gather/expand sources, build a literature matrix,
  or run a literature review for a legal research topic.
---

# Skill: Literature Review (Subagent-Driven)

Alur wajib: **discovery oleh main-agent → analisis per-paper oleh subagent →
sintesis oleh main-agent**. Jangan menganalisis paper langsung di main-agent.

## Prasyarat (wajib dibaca)

- `AGENTS.md` aturan #6 (Full-Text First), #7 (setiap tahap/stage via
  subagent), #8 (dilarang curl manual), #9 (verifikasi pasal via MCP
  Pasal.id), #10 (auto-enrich knowledge).
- `knowledge/penulisan/abstrak-normatif.md` — untuk konteks ringkas tiap paper
  (5 elemen) bila diperlukan.
- `riset/tahap8b.md` — bila korpus sudah ada, **perluas** darinya, jangan
  mengulang yang sudah ada.

## Alur kerja (checklist)

```
Literature Review Progress:
- [ ] 1. Korpus existing diperiksa (riset/literature-review/, riset/tahap8b_paper/)
- [ ] 2. Discovery: research search / snowball (CLI), dedup DOI vs existing
- [ ] 3. Full-text: research fulltext "<DOI>" untuk setiap kandidat (Main)
- [ ] 4. Spawn subagent per batch paper (analisis 1 paper/subagent atau batch kecil)
- [ ] 5. Verifikasi output tiap subagent (label, DOI, non-halusinasi)
- [ ] 6. Review quality pass: subagent reviewer mereview kartu baru
- [ ] 7. Sintesis matriks +update tahap8b.md; commit
```

## 1. Discovery (main-agent)

```bash
uv run research search "<topik>" --providers crossref,openalex,doaj --limit 10 --no-index
uv run research snowball <cite_key> --direction both --limit 6
```

Bandingkan DOI dengan existing (`rg -i "<doi>" riset/`). Skip yang sudah ada.

## 2. Full-text (main-agent, SEBELUM spawn subagent)

```bash
uv run research fulltext "<DOI>" --output-dir data/markdown --timeout 15
```

Label epistemic **sebelum** memberi tugas ke subagent:
- Berhasil → `[FULL-TEXT]` (Markdown di `data/markdown/`).
- PDF gagal → `[ABSTRACT]` (abstrak dari Crossref/OpenAlex).
- Hanya metadata → `[METADATA]`.

## 3. Analisis per paper (subagent — WAJIB)

Untuk tiap batch paper (1–3 paper per subagent), subagent:
- Membaca SKILL.md ini (via `Skill` tool) + full-text/abstrak.
- Menulis satu kartu `riset/<topik>_paper/PAPER_<CiteKey>_<slug>.md` berisi:
  identitas (judul, penulis, tahun, jurnal, DOI, URL) · isu · metode · teori
  · temuan · gap · relevansi ke skripsi · label epistemic.
- **Dilarang** mengarang; isi di luar sumber → "—".
- **Dilarang** mengedit file existing atau `tahap8b.md`.

Prompt subagent harus menyebut: DOI, path full-text (atau "abstract-only"),
path output, dan aturan label.

## 4. Review quality (subagent kedua)

Setelah kartu ditulis, spawn subagent **reviewer** untuk sampel kartu baru
(≥20% atau min. 5 kartu): cek label jujur, DOI valid, isi ≤ sumber, relevansi.
Temuan → perbaiki kartu atau tandai gap.

## 5. Sintesis (main-agent)

- Update tabel di `riset/<topik>.md` (tambah baris "Literatur Baru #N").
- Regenerasi matriks bila ada (label konsisten dengan kartu).
- Commit.

## Aturan kualitas

- Non-duplikasi DOI (antar existing & baru).
- Label epistemik konsisten; `[FULL-TEXT]` hanya bila Markdown dibaca.
- Klaim kutipan (mis. pasal) diverifikasi via MCP Pasal.id, bukan dari
  paper.
- Paper [ABSTRACT] boleh untuk pemetaan tema, **tidak** untuk kutipan
  substantif tanpa verifikasi.