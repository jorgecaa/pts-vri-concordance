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
> user explicitly asks. Other standing rules: **(1) nothing is CONFIRMADO without the validador**
> (Modelo B: gate local + Gemini concordantes, PTS↔CST; humano arbitra desacuerdos — DeepSeek
> retirado por no fiable); **(2) any new file-format parser must use `pyparsing`** (docs in `doc/pyparsing/`);
> **(3) never touch SuttaCentral or the Mahāsaṅgīti edition it hosts** — this includes
> `src/data/extract_sc_references.py`, `extract_translation_sujato.py`, `extract_translation_legacy.py`
> and the `pts_xref` / `translation_*` tables derived from SuttaCentral. **NB:** the Helmer's **CST**
> (Chaṭṭha Saṅgāyana, DPR XML) is a *different* edition from Mahāsaṅgīti and remains the allowed
> path to CONFIRMADO. **(4) Never touch the Thai edition (BUDSIR) or the Sinhalese edition
> (tipitaka.lk).** In this repo the project's **"RTE" is BUDSIR** (`extract_rte_pts.py`,
> `rte_pts_refs.json`, `/home/jorge/Code/tipitaka.rte/`, and the `OK+RTE`/`RTE_ONLY` marks) — out of
> scope, do not use to validate. Sinhalese *manuscript sigla* inside the PTS apparatus are fine (that
> is the Canon, not the tipitaka.lk edition). **Net: the only valid sources are PTS (DB) and CST (Helmer).**
> **(5) La clave canónica del lado CST es el paranum del XML VRI, NO la notación DPR.** La columna
> **`VRI Ref`** (`«<fichero>:<paranum>»`, p.ej. `s0303m:146`; rangos `s0304m:33-42`) es la que une
> una fila con el texto cotejado. **`Sutta #` es una etiqueta legible, no una clave**, y `DPR Ref`
> (en AN) es sólo informativa. Motivo: el DPR no identifica el sutta de forma unívoca y lo ha
> demostrado una y otra vez — S ii desplazado +7, S iv (SN 35) +17 y +47, AN +15 por desdoblamientos
> de fila; y el `dpr_code` de AN en `massive.tsv` tiene **138 códigos duplicados** y asignaciones
> incoherentes entre sí (`AN3.2` → `an3.1.2.8` mientras `AN3.11` → `an3.1.2.11`). Cada vez, el
> validador aprobaba un par correcto **ajeno a la fila**. Backfill hecho con
> `backfill_vri_ref.py` (1795/1814 filas de SN), y el criterio de aceptación fue que **el título CST
> recomputado coincidiera con el que se validó**. Todo alineador nuevo debe emitir `VRI Ref`.
> **(6) Ante casos complejos de divergencia estructural, incluso dentro de un mismo archivo, se debe
> separar la lógica algorítmica.** Un analizador por régimen, no uno parametrizado que intente
> servir a todos: una regla única ajustada a la mayoría **se equivoca en silencio** en la minoría, y
> el validador no puede detectarlo porque el par PTS↔CST que recibe es coherente consigo mismo. Ver
> `sn34_series.py` (SN 34: dos convenciones opuestas en un mismo saṃyutta, cuatro filas mal
> emparejadas y tres ya CONFIRMADO).
> **(5-bis) En KN la clave del VRI es el CAPÍTULO, no el paranum.** El `n` del CST es un paranum
> corrido por fichero en SN y AN, pero en KN **reinicia dentro de cada capítulo** (el `s0501m` tiene
> un `n=1` en el capítulo 2, otro en el 4, otro en el 5…) y hay capítulos sin `n` ninguno. La forma
> es **`<fichero>:c<capítulo>[.<item>]`** — `s0501m:c5` —, y `check_integrity` la valida contra los
> `<div rend="chapter">`. Es una extensión de la regla (5), no una excepción: la clave sigue siendo
> el VRI; lo que cambia es cuál es su unidad numerada.
> **(5-ter) En KN la referencia es la ESTROFA o la sección, no la página.** En DN/MN/SN/AN se cita
> `<volumen> <página>,<línea>` porque lo que se cita es el impreso. En las obras en verso de KN eso
> no sirve: lo que las tres ediciones comparten es el **número de estrofa**. `Dhp 21-32` identifica
> el Appamādavagga en cualquier edición; `Dh 7` sólo dice en qué página de PTS empieza. La `PTS Ref`
> va como `Dhp <a>-<b>` (verso) o `Khp <n>` (sección); la página se conserva en su columna, cierta y
> útil, pero deja de ser la referencia.
> **(7) Toda operación declara su presupuesto ANTES de empezar** (`audit_tiempo.py`: pasos y
> minutos). Al agotarse se **para**, se informa de lo conseguido y de lo que falta, y se pide
> decisión; ampliar el presupuesto es decisión de Jorge, no del que ejecuta. Motivo: una
> exploración que debía acotar un régimen de marcadores se convirtió en un alineador nuevo, tres
> iteraciones de heurística y decenas de volcados de página sin ningún punto de parada declarado.
> El trabajo no estaba mal; estaba **sin presupuesto**, y por eso nadie podía decir que se había
> pasado. **(8) Toda comparación de texto se normaliza antes a la convención VRI**
> (`pali_norm.py`), y **antes de plegar**: las reglas necesitan los diacríticos que el plegado
> borra. Ver la memoria `normalizacion-interna-vri`.

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
  - **Y tampoco dentro de un mismo archivo o saṃyutta.** Ante divergencia estructural compleja,
    **separa la lógica algorítmica**: un analizador por régimen, seleccionado por un rasgo
    intrínseco del dato (no por un rango codificado a mano). SN 34 imprime sus 55 suttas bajo dos
    convenciones **opuestas** — en 1-19 la abreviatura del marcador nombra el *segundo* elemento del
    compuesto, en los grupos 20-55 nombra el *par* o, truncada con `--`, la *raíz* — y la regla
    única, ajustada al primer tramo, desplazaba cada fila del segundo al grupo siguiente. Tres de
    las cuatro filas afectadas ya estaban CONFIRMADO. Antes de generalizar una regla de nombres,
    comprueba que la convención no cambia a mitad del volumen, y **conserva el dato en bruto**: el
    `--` que distinguía los dos regímenes lo estaba borrando el `_clean` de la gramática.
    Ver `sn34_series.py`.
- **CST numbering ≠ PTS numbering**, especially in SN and AN (per-saṃyutta/per-vagga resets).
  Match by content/name and global ID, never by assuming sequential numeric correspondence.
- **El validador tiene un PUNTO CIEGO y hay que cubrirlo aparte.** No puede ver (a) que el par que
  recibe sea el equivocado —si los dos lados son coherentes entre sí, aprueba— ni (b) que el texto
  que se le entrega esté corrompido, si la corrupción produce prosa legible. El caso canónico:
  `sutta_hash.tokens` partía `n' atthi` y descartaba la `n` suelta, de modo que **«no hay» llegaba
  como «hay»** — 12.561 casos en DN/MN/AN, invisibles durante cinco volúmenes cerrados porque SN
  apenas usa esa elisión. Correr **`check_integrity.py`** (skill `integridad-datos`) y
  **`audit_injectivity.py`** antes y después de tocar texto, Excel o alineadores, y **siempre antes
  de gastar API**. Regla derivada: **ninguna transformación de texto puede perder una palabra**; si
  un paso descarta tokens «cortos» o «ruido», hay que demostrar que no descarta significado.
- **"NADA se cierra sin el validador"** — a nikāya/volume is only marked CERRADO 🔒 after the
  **validador** pass (**Modelo B**): the local content gate (título-núcleo + Jaccard de incipit +
  divergencias CollateX) **and** `gemini-flash-lite-latest` (salida estructurada, `temperature=0`)
  deben **ambos** dar APPROVE. Desacuerdo → PENDIENTE + **revisión humana** (Jorge arbitra contra
  el impreso/CST). El antiguo pase DeepSeek "Helmer" (`helmer_ptscst.py`, `helmer_ptscst_cache.json`)
  está **RETIRADO**: probado no-determinista a `temperature=0` (los veredictos se voltean entre
  corridas en casos borderline), ya no se confía en él para CONFIRMADO. DB verification (pages,
  markers, sequence) is necessary but *not sufficient*.
- **DO NOT MODIFY closed sections** (DN, MN, SN I–V — see `STATUS.md`) without re-running full
  validation. SN I, SN II y SN V están cerrados por el **validador**; SN III–IV siguen sin CST.
  Pending: SN III–IV, AN, KN.
- **`fix_mn_pages.py` contains 78 INCORRECT "corrections" — do not use it.**

The legacy Helmer validation persona/workflow is packaged as a repo skill
(`.agents/skills/pts-helmer-smith-validator/`) — **histórico**; el pase vigente es el **validador**
(Modelo B: gate local + `gemini-flash-lite-latest`), no el DeepSeek "Helmer" retirado.

**Status columns in the master Excel** (`PTS_Reference_Complete_Canon.xlsx`, sheet *Complete
Canon*): `Validation` holds the fine-grained provenance; **`Estado`** is the binary rollup with
exactly two values — **CONFIRMADO** (`Validation` ∈ VALIDADOR / VALIDADOR_HUMANO / HELMER_APPROVED /
HELMER_PTS_TRUNCATED / HELMER_FIXED / PTS_CROSSREF_SN) and **PENDIENTE** (everything else,
including `DB_VERIFIED`). **Rule: without the validador, nothing is CONFIRMADO** (BD/RTE/incipit
verification is not sufficient). **`VALIDADOR`** = CONFIRMADO por acuerdo automático (Modelo B: gate
local + `gemini-flash-lite-latest` ambos APPROVE); **`VALIDADOR_HUMANO`** = un desacuerdo gate/Gemini
que Jorge arbitró a mano (misma fuerza, provenance humana). Los valores
`HELMER_*` son verdictos legados del pase DeepSeek — se mantienen como CONFIRMADO histórico pero
son **provisionales**: re-validar con el validador al revisitar cada nikāya (DeepSeek resultó no
fiable). `REF_ERROR_DPR` es un valor **PENDIENTE** (no CONFIRMADO): la referencia DPR del Excel
apunta a nada (error de DPR), no cotejable. `REVISAR_DIFUSO` es **PENDIENTE**: se confirmó vía una
resolución PTS difusa (±1) que resultó poco fiable y no re-verifica con el match por nombre — a
revisar (evidencia PTS incierta). El lado PTS del pipeline VRI casa el texto por **nombre**
(`pts_by_name`, robusto al off-by-one PTS), NO por número corrido difuso.

**Alineación SN/AN/KN por CONCORDANCIA (VRI):** en SN/AN/KN la numeración diverge entre notaciones;
el `Sutta #` del Excel usa **notación DPR**. El aligner definitivo (`validador_sn5_vri.py`) NO adivina
por contenido: Excel(DPR) → `massive.tsv` (`cst_paranum`) → **XML VRI** (`romn/*.mul.xml`, párrafos
`<p n="N">`) → texto CST exacto; lado PTS por marcadores DB casando contra el **canónico** (=nº
corrido PTS). Con alineación exacta, CONFIRMADO = concordancia ∧ Gemini (el gate de cobertura sobra).
**SN V 610/610, SN I 271/271 y SN II 257/257 CERRADOS 🔒, SN III 332/333 (2026-07-25)**; las líneas de `PTS Ref` recalibradas
contra el marcador real de la BD (`calibrate_sn5_lines.py` / `calibrate_sn1_lines.py`, exactas al
100%). Cada volumen tiene **su propia gramática de marcadores** (`sn1_markers.py`: `§ N.` numerado por
vagga; `sn2_markers.py` / `sn3_markers.py`: `N (M) Nombre` sin puntos, con S iii añadiendo nombre
entre paréntesis y prefijo de subdivisión; SN IV–V: `N. (M) Nombre`) y su lado PTS lo fija
el **front matter del volumen** (`samyutta-vol-<N>-info.txt`: nº de vaggas y suttas, suttas por
vagga y página de arranque) — verdad-terreno estructural sin LLM.
⚠️ **`massive.tsv` colapsa los rangos**: da un solo `cst_paranum` por grupo (el del primer miembro),
así que asignárselo a todos coteja los miembros contra el primer sutta del grupo. **El TSV no se
toca** — el arreglo va en el lector, `massive_reader.py`, que expande `para + (k−a)` **con compuerta**
(solo si todos los paranum resultantes existen en el XML, que es lo que pasa cuando el destino cae en
el bloque elidido del CST). Al cambiar la lectura cambia el texto CST bajo filas ya validadas:
**re-validar las afectadas, nunca heredar el veredicto**.
⚠️ **Distinguir «PTS elide el texto» de «PTS no reconoce esa división».** Si el CST parte en varios
suttas lo que PTS imprime como uno (S ii 130: PTS escribe `Suttanto eko` y su uddāna cuenta *doce*),
esa división **no tiene referencia PTS** y su fila no va en la tabla (se borró `12.74`). Al revés, si
PTS numera el sutta y solo abrevia el texto (`vitthāretabbo`, S v `122--132. (2--12)`), la fila sí va
y el REJECT del LLM es un falso negativo por elisión. Y si PTS numera lo que el CST agrupa, la fila
se expande (12.75 → 12.83–93) casando el **ítem `(N)` del grupo CST con la posición `(M)` del
marcador PTS**. Leer siempre el impreso antes de decidir: la nota anterior de este repo decía «PTS
elide el grupo Dutiyasatthu» y era falsa en las dos mitades.
⚠️ **Un APPROVE del validador no dice nada sobre la FILA si la clave de emparejamiento es falsa.**
En S ii el `Sutta #` del Excel iba desplazado +7 en SN 17: emparejar por él comparaba un par PTS↔CST
correcto entre sí pero ajeno a la fila, y Gemini aprobaba. **El desajuste puede ir en cualquier
dirección**: en S iii el Excel y el concordance concuerdan y es la numeración PTS la que difiere
(158 suttas impresos en el Khandha frente a 159 del CST), así que allí el lado PTS se resuelve por
nombre sobre la página que ancla `cst_p_page` — y en los pares `Dutiya-` hay que tomar el k-ésimo
homónimo, porque Feer no escribe el ordinal sino que repite el nombre. Se detectó por la **comprobación cruzada
de nombres**, no por el LLM. Exigir siempre ≥1 comprobación cruzada independiente de la clave
(nombre del marcador ≡ título CST, y página del marcador ≡ `cst_p_page`), y recordar que la
identidad real de una fila la dan `Sutta Name` + `PTS Page`, no el `Sutta #` (ver `reid_sn2.py`). Detalle en la memoria
`sn-alineacion-estructura`. DN/MN (donde las 3 notaciones coinciden) siguen por el validador normal.
El **mismo pipeline es la plantilla para AN/KN** (están en `massive.tsv`, notación DPR, con sus XML
VRI); el flujo, los pitfalls y la regla de auditar el resolvedor con un diff de texto **antes** de
gastar API están en `STATUS.md` § METHOD.
`PTS_CROSSREF_SN` is the one non-LLM route to CONFIRMADO: PTS reenvía el sutta al
Suttanipāta sin reimprimir el texto (no hay texto PTS que cotejar), y la referencia fue
verificada a mano contra la edición impresa. Únicas dos paradas: MN 92 Sela (M ii 146 → Sn
p.99 Fausböll) y MN 98 Vāseṭṭha (M ii 196 → Sn nº35).
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
| **`.agents/skills/integridad-datos/`** | **Invariantes del dato** (`check_integrity.py`): caza la corrupción silenciosa que el validador no puede ver. Correr antes/después de tocar texto, Excel o alineadores, y **siempre antes de gastar API**. |
| **`.agents/skills/pts-helmer-smith-validator/`** | The Helmer PTS↔content validation skill (persona + `db_reference.md`). |
| **`PLAN_MEJORA.md`** | Historical plan for resolving the last low-scoring concordance entries (incipit matching, RTE gaps). |

**Stale/superseded docs** have been moved out of the way, not deleted:
- `archive/docs-reconstruccion/` — 9 obsolete code-reconstruction docs (described the abandoned QML
  UI, the legacy `Dbf1__*` schema, a non-existent CLI). Historical reference only.
- `archive/` — superseded one-off pipeline scripts (per-Nikāya iterations, `*_v2/_v3/_pilot` runs).

When you change how the app or pipeline works, update the relevant doc above and keep this index in
sync — don't create new top-level docs that duplicate an existing one.
