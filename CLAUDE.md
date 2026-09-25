# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Context

This is an autonomous research platform (Python 3.13+, managed by `uv`) for
Indonesian normative legal research: academic literature discovery, court
judgment analysis, citation snowballing, PDF→Markdown conversion, and
SQLite RAG, wired end-to-end to a 20-stage normative thesis methodology.

This file covers what `AGENTS.md` does not: the research workflow's runtime
state, verification discipline, and repository conventions.

## Ground rules (non-negotiable)

1. **Zero hallucination.** Every claim about a law, paper, or court decision
   must carry an epistemic label: `[TERBACA]` (verified against the Pasal.id
   corpus via MCP or full text read), `[FULL-TEXT]` (paper read from Markdown
   produced by `fulltext`), `[ABSTRACT]` / `[METADATA]` (degraded fallback),
   `[WEB]`, `[REFERENSI]` / `[PERLU VERIFIKASI]`. Never mark `[FULL-TEXT]`
   from a PDF you grabbed ad hoc.
2. **Verification workflow.** Any Indonesian regulation/pasal/citation used in
   analysis goes through the Pasal.id MCP:
   `resolve_law → get_law_context → read_law`. Always check
   `get_law_context(detail='relationships')` for amendments and MK judicial
   review — a pasal may be modified or held inkonstitusional (e.g. MK 105/2024
   on ITE 27A, MK 115/2024 "kerusuhan" = physical); cross-check against an
   active thesis anchor (UU 1/2024, UU 27/2022).
3. **No ad-hoc retrieval.** Never hand-roll `curl`/`httpx`/`wget` PDF
   downloads. Full text comes only via `uv run research fulltext "<DOI>"` /
   `--pdf-url <direct URL>` / OJS landing URL.

## Workflow runtime state

The normative methodology lives in `workflow.md` (20 tahap, 7 fase; each tahap
has an "Evaluasi & Gate Check" section). Its operational trail lives in
`riset/` — one stage file per tahap (`riset/tahapN.md`), plus audit tracings
(`tahap-audit.md`) and Q&A artifacts (`riset/qa/`, `riset/pasal/`,
`riset/literature-review/`). `draft_skripsi/` holds the thesis chapters.

- **Every tahap runs in a dedicated subagent** (never inline in the main
  session): main session prepares the doctrinally grounded brief
  (pasal `[TERBACA]`, verified papers, knowledge), spawns the subagent, then
  reviews/incorporates the returned `riset/tahapN.md`.
- Completed stages must satisfy their gate check in `workflow.md` before the
  trail moves on; closing verifications is done deliberately (see commit
  history for the V7/V8/V13 closure pattern).
- The 7-phase tracker is mirrored in tooling via
  `uv run research workflow status` / `check N --pass [--grand|--middle|--applied]`.

## Doctrinal knowledge base

`knowledge/` is the shared doctrine library (`knowledge/README.md` indexes it).
Four core files under `knowledge/analisis-status-hukum/`:
`kerangka-teori.md` (three-tier legal science + theory groups),
`framework-operasional.md` (6-stage analysis + worksheet),
`dekonstruksi-unsur-pasal.md` (bestanddelen/elementen, actus reus/mens rea,
monisme/dualisme), `dekonstruksi-isu-hukum.md` (legal-issue decomposition,
IRTAC per sub-issue, cacat norma). Doctrine subagents MUST ground reasoning
here. Auto-enrich: any new doctrine encountered (teori, tokoh, asas, definisi)
goes into `knowledge/` with name, penggagas, sumber (DOI/URL/cite_key + label),
and is indexed in `knowledge/README.md` (update, never duplicate).

## Development loop

```bash
uv sync                      # install deps (uv only — never raw pip)
uv run ruff check .          # must stay 100% clean (no ignored errors)
uv run ruff format .         # formatting
uv build                     # sdist via uv_build backend
```

Tests are standalone integration scripts, run one at a time:
`uv run python tests/test_<name>.py` — e.g. `uv run python tests/test_parallel_pipeline.py`.
No pytest. See `AGENTS.md` for the full list of subsystem tests.

## Repository conventions

- Full CLI guide (17 subcommands: `search`, `fulltext`, `putusan`, `query`,
  `bib`, `cards`, `workflow`, `irac`, `scaffold`, `audit-traceability`,
  `pipeline`, …), Python API, and code layout — see **AGENTS.md**.
- User-facing docs (thesis, riset artifacts) are written in **Bahasa Indonesia**;
  code and commit messages in English.
- `src/research/` layout: `app.py` is the `ResearchApp` facade; everything
  imports via absolute paths (`from research.db import DatabaseManager`).
- SQLite (WAL) is primary storage; schemas self-migrate via
  `DatabaseManager.init_schema()`. Never delete or hand-modify the DB.
- `research` CLI entry point: `research = "research:main"` (`src/research/__init__.py`).
- Static analysis config lives in `pyproject.toml`; `uv.lock` is committed.
  Gitignored: `data/`, `tmp/`, `sessions/`, `logs/`, `*.sqlite`.