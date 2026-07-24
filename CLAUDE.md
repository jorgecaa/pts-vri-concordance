# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Two loosely-coupled workstreams share one directory (an unpacked AppImage tree, `squashfs-root`):

1. **The GUI app** (`src/`) — *Tipitaka PTS Browser*, a PyQt6 desktop reader for the Pāli
   Tipiṭaka aligned to the Pali Text Society (PTS) pagination, with search, apparatus criticus,
   and an embedded DPD dictionary panel.
2. **The philology pipeline** (root-level `*.py` scripts, `README.md`, `STATUS.md`,
   `README-COMMY.md`) — batch tooling that builds and validates a **PTS reference concordance**
   (the `PTS_Reference_*.xlsx` outputs) and extracts the 58 Aṭṭhakathā commentary volumes to
   JSON/LaTeX/PDF. These scripts read the same database but are not part of the app.

This is **not a git repository** — there is no version control here. Be careful with
destructive edits; there is no undo.

> **Scope rule — Canon only.** Work strictly on the **Pāli Canon** (`edition='mula'`). **Never
> touch the commentary (aṭṭhakathā) or sub-commentary (ṭīkā).** The commentary pipeline
> (`extract_commentary.py`, `generate_tex.py`, `compile_pdfs.py`, `book_meta.py`,
> `validate_text.py`, `README-COMMY.md`, `rotb_commentary/`, `dpd_check/`, and any
> `edition='atthakatha'` data) is **out of scope** — kept for reference, not modified, unless the
> user explicitly asks. Other standing rules: **(1) nothing is CONFIRMADO without Helmer**
> (PTS↔CST); **(2) any new file-format parser must use `pyparsing`** (docs in `doc/pyparsing/`);
> **(3) never touch SuttaCentral or the Mahāsaṅgīti edition it hosts** — this includes
> `src/data/extract_sc_references.py`, `extract_translation_sujato.py`, `extract_translation_legacy.py`
> and the `pts_xref` / `translation_*` tables derived from SuttaCentral. **NB:** the Helmer's **CST**
> (Chaṭṭha Saṅgāyana, DPR XML) is a *different* edition from Mahāsaṅgīti and remains the allowed
> path to CONFIRMADO. **(4) Never touch the Thai edition (BUDSIR) or the Sinhalese edition
> (tipitaka.lk).** In this repo the project's **"RTE" is BUDSIR** (`extract_rte_pts.py`,
> `rte_pts_refs.json`, `/home/jorge/Code/tipitaka.rte/`, and the `OK+RTE`/`RTE_ONLY` marks) — out of
> scope, do not use to validate. Sinhalese *manuscript sigla* inside the PTS apparatus are fine (that
> is the Canon, not the tipitaka.lk edition). **Net: the only valid sources are PTS (DB) and CST (Helmer).**

## Running & testing the app

```bash
./AppRun                    # launch the GUI (runs src/run.py; prefers ./venv, else python3)
python3 src/run.py          # same, directly
python3 src/run.py check    # verify dependencies (PyQt6, rapidfuzz, charset-normalizer, xelatex)
python3 src/run.py test     # run the pytest suite in src/tests/

python3 -m pytest src/tests/                       # full suite
python3 -m pytest src/tests/test_database.py -v    # one module
python3 src/test_integration.py                    # standalone integration scripts (src/test_*.py)
```

The GUI entry point is `src/main/extracted_appimage_gui.py::TipitakaMainWindow` (PyQt6 **Widgets**,
plus `QWebEngineView` for the DPD panel — `run.py` sets `AA_ShareOpenGLContexts` before creating
the `QApplication`, which QtWebEngine requires). The backend modules under `src/main/` (database,
search, dictionary, citation_parser, apparatus, rota_edition, ui_integration) are the reusable
layer.

> The `usr/` directory holds an **obsolete** compiled binary whose DB schema no longer matches —
> ignore it. `src/run.py` is the current, working code. `src/config.py` is a large aspirational
> config module that the GUI does not actually use — don't assume its options are wired up. Trust
> the actual code and `src/data/DATABASE.md`.

## The database — the one source of truth

`src/data/tipitaka.sqlite` (≈343 MB) is derived from the Dhammakaya Foundation's PaliText V2.5.
Authoritative reference: **`src/data/DATABASE.md`** (describes the current rebuilt schema: friendly
table names, plain-UTF-8 text, two editions, FTS5).

Live tables include: `pages`, `footnotes`, `contents`, `toc`, `nav_tree`, `books`, `editions`,
`dict_pts`, `dict_pali_english`, `pali_fts` (FTS5), `word_*`, `translation_*`, `pts_prefaces`,
`pts_appendices`, `pts_xref`.

Key facts that are easy to get wrong:

- **`pages`** is keyed by `(edition, book_no, page_no)`. `unitext` here is **plain UTF-8** Pāli
  (IAST diacritics), not base64. `head` (running header) is frequently **corrupt, empty, or points
  to the wrong page** — never trust it as ground truth; validate against `unitext` (the page body).
- **`edition`** is either `'mula'` (canon) or `'atthakatha'` (commentary). These were renamed from
  the legacy `ROTA`/`ROTB` labels.
- The **`'ROTA'` label anywhere means PTS**, *not* Royal Thai. The text is the PTS roman-script
  edition (pagination matches PTS volumes exactly). Ignore any doc/comment that calls it "Royal
  Thai / Syāmaraṭṭha".
- **Book number map:** DN=6–8, MN=9–11, SN=12–16, AN=17–21, KN=22–42 (canon); 58 commentary volumes.

## The concordance pipeline — critical rules

Read `STATUS.md` (current state, per-nikaya) and `README.md` (methodology, lessons learned) before
touching any concordance script. Non-negotiable principles baked into this project:

- **NO HAY HOMOGENEIDAD** — every Nikāya (sometimes every volume) has its own marker/numbering
  convention. There is *no universal parser*. Each has a dedicated script (`add_*_lines.py`,
  `parse_sn_grammar.py`, `rebuild_an.py`, `integrate_khuddaka.py`, …).
- **CST numbering ≠ PTS numbering**, especially in SN and AN (per-saṃyutta/per-vagga resets).
  Match by content/name and global ID, never by assuming sequential numeric correspondence.
- **"NADA se cierra sin Helmer"** — a nikāya/volume is only marked CERRADO 🔒 after cross-validating
  PTS↔CST content with the DeepSeek "Helmer" pass (`helmer_*.py`), cached in
  `helmer_ptscst_cache.json`. DB verification (pages, markers, sequence) is necessary but *not
  sufficient*.
- **DO NOT MODIFY closed sections** (DN, MN, SN I–IV — see `STATUS.md`) without re-running full
  validation. Pending: SN V, AN, KN.
- **`fix_mn_pages.py` contains 78 INCORRECT "corrections" — do not use it.**

The Helmer validation persona/workflow is also packaged as a repo skill:
`.agents/skills/pts-helmer-smith-validator/`.

**Status columns in the master Excel** (`PTS_Reference_Complete_Canon.xlsx`, sheet *Complete
Canon*): `Validation` holds the fine-grained provenance; **`Estado`** is the binary rollup with
exactly two values — **CONFIRMADO** (Helmer only: `Validation` ∈ HELMER_APPROVED /
HELMER_PTS_TRUNCATED / HELMER_FIXED) and **PENDIENTE** (everything else, including `DB_VERIFIED`).
**Rule: without Helmer, nothing is CONFIRMADO** (BD/RTE/incipit verification is not sufficient).
Use these two terms consistently. Per-Nikāya counts live in `STATUS.md` (single source of truth).

### Commentary extraction (Aṭṭhakathā → JSON/LaTeX/PDF)

Full workflow and format details in `README-COMMY.md`. Regenerate with:

```bash
python3 extract_commentary.py src/data/tipitaka.sqlite rotb_commentary  # DB → JSON (58 books)
python3 generate_tex.py         # JSON → XeLaTeX .tex (--diplomatic keeps old niggahīta m/n)
python3 compile_pdfs.py rotb_commentary   # .tex → PDF (two xelatex passes for the ToC)
```

Canonical book/sigla/mūla map lives in `book_meta.py`. Title/verse detection in `generate_tex.py`
is heuristic (`is_title_line`, `_TITLE_KW`, `_COLOPHON`) — these lists are meant to be revised.

## DPD (Digital Pāḷi Dictionary)

A separate DPD SQLite DB is available system-wide at `/dev/shm/dpd.db` (in RAM, ≈2.1 GB;
canonical copy `/home/jorge/Code/dpd-db/dpd.db`). It also has an MCP server
(`mcp__pali-dictionaries__*`: `lookup`, `search`, `analyze`, `list_dictionaries`). Use it for Pāli
lookups, inflections, roots, and word families. `validate_text.py` uses it to spell-check
commentary text. Do not overwrite the RAM file while `dpd-webapp.service` is running.

## Documentation index

This file is the entry point. The other live docs, and what each authoritatively covers:

| Doc | Covers |
|-----|--------|
| **`CLAUDE.md`** (this file) | Repo overview, how to run/test, DB facts, pipeline rules — start here. |
| **`README.md`** | Concordance pipeline: per-Nikāya methodology, marker conventions, lessons learned. |
| **`STATUS.md`** | Current state of the concordance per Nikāya/volume (what is CERRADO 🔒 vs pending) + Helmer method. |
| **`README-COMMY.md`** | Aṭṭhakathā (commentary) extraction: JSON/LaTeX/PDF formats and the regenerate workflow. |
| **`src/README.md`** | The GUI app: how to run it, module layout, data files. |
| **`src/docs/PLAN_MEJORA_UX.md`** | GUI UX roadmap (P0 done; P1/P2 pending) — book-naming, search results, commentary view. |
| **`src/data/DATABASE.md`** | Authoritative `tipitaka.sqlite` schema reference (current rebuilt schema: tables, encodings, editions, FTS, query recipes). |
| **`.agents/skills/pts-helmer-smith-validator/`** | The Helmer PTS↔content validation skill (persona + `db_reference.md`). |
| **`PLAN_MEJORA.md`** | Historical plan for resolving the last low-scoring concordance entries (incipit matching, RTE gaps). |

**Stale/superseded docs** have been moved out of the way, not deleted:
- `archive/docs-reconstruccion/` — 9 obsolete code-reconstruction docs (described the abandoned QML
  UI, the legacy `Dbf1__*` schema, a non-existent CLI). Historical reference only.
- `archive/` — superseded one-off pipeline scripts (per-Nikāya iterations, `*_v2/_v3/_pilot` runs).

When you change how the app or pipeline works, update the relevant doc above and keep this index in
sync — don't create new top-level docs that duplicate an existing one.
