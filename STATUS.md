# PTS Reference Concordance — Status Report
## Date: 2026-07-21 (updated 2026-07-25 — SN I 271/271 y SN V 610/610 CERRADOS)

---

## UPDATE 2026-07-24 — Cache↔Excel reconciliation (SN)

The master Excel had been regenerated (by `build_final_excel.py`) *after* the SN Helmer runs,
which **overwrote the SN HELMER marks back to `DB_VERIFIED`**. The DeepSeek verdicts still lived
in `helmer_ptscst_cache.json`, so they were reconciled back without any new API calls:

- **SN IV**: 106 exact-marker verdicts recovered from cache → re-written to Excel as
  **94 `HELMER_APPROVED` + 12 `HELMER_REJECT`** (previously all 106 were flat-marked
  `HELMER_APPROVED`, which hid the rejects). The 12 rejects are Feer-abbreviation / orthographic
  false positives — the sutta *names* match the CST titles exactly, so the page references are
  sound; only **SN 36.26** looks worth a manual look. The 238 peyyāla SN IV entries stay
  `DB_VERIFIED` (no individual marker → not CST-validatable).
- **SN V**: verdicts in cache are **NOT trustworthy** (36 APPROVE / 430 REJECT over 466 exact
  matches = 8%). This reflects a **broken saṃyutta-aware CST mapping** in `helmer_sn5_all.py`,
  not bad references (the pilot on 20 gave 85%). **Not volcado.** SN V still needs the CST mapping
  fixed and re-run. See PENDING below.
- **SN I/II/III**: never had a full Helmer pass (only a SN I pilot); they remain `DB_VERIFIED`.

Current SN validation state: 94 `HELMER_APPROVED`, 12 `HELMER_REJECT`, 1 `HELMER_FIXED`,
1699 `DB_VERIFIED` (of 1806). A timestamped Excel backup was made before the write
(`PTS_Reference_Complete_Canon.bak-*.xlsx`).

> **Where PTS↔CST concordance actually stands (Excel-reflected):** DN 34/34 ✅, MN 152/152 ✅,
> SN IV 94/106 ✅ (12 to review). SN I/II/III, SN V, AN, KN: not CST-validated in the Excel yet.

### `Estado` column (binary status) — added 2026-07-24

`PTS_Reference_Complete_Canon.xlsx` now carries an **`Estado`** column with exactly two values.
Use this terminology consistently across the project:

- **CONFIRMADO** — reference exact, verified and resolved by **Helmer (PTS↔CST) only**. Maps from
  `Validation` ∈ {`HELMER_APPROVED`, `HELMER_PTS_TRUNCATED`, `HELMER_FIXED`}.
  **Rule (2026-07-24): without Helmer, nothing can be CONFIRMADO** — DB/RTE/marker/incipit
  verification is *not* sufficient. (This supersedes the earlier "CST + BD" criterion; `DB_VERIFIED`
  is now PENDIENTE.)
- **PENDIENTE** — everything else: `DB_VERIFIED` (BD-verified but no CST), `HELMER_REJECT`
  (discrepancy), `OK` / `OK+RTE` / `OK_CONT`, `OK_HEAD`, `OK_NEAR`, `RTE_ONLY`, `VERSE_ONLY`,
  `EXTRA_CANON`, `UNVERIFIED` / `UNVERIF`. When evidence is insufficient → **PENDIENTE**.

| Nikāya | Entries | CONFIRMADO | PENDIENTE | % CONF |
|--------|--------:|-----------:|----------:|-------:|
| DN | 34 | 34 | 0 | 100.0% |
| MN | 152 | 152 | 0 | 100.0% |
| SN | 1806 | 975 | 831 | 54.0% |
| AN | 1738 | 1 | 1737 | 0.1% |
| KN | 2360 | 0 | 2360 | 0.0% |
| **TOTAL** | **6090** | **1162** | **4928** | **19.1%** |

> Cifras al **2026-07-25**, tras cerrar SN I (271/271) y SN V (610/610). La hoja `Summary` del Excel
> está alineada. Desglose de SN: SN I 271 ✅ + SN V 610 ✅ (validador Modelo B) + SN IV 94 (Helmer
> legado); SN II–III siguen `DB_VERIFIED` → PENDIENTE.

> MN 14/38/64 (antes `OK+RTE`/PENDIENTE por errores de API transitorios) fueron re-corridos por
> Helmer DeepSeek el 2026-07-24 → **3/3 APPROVE** → `HELMER_APPROVED`/CONFIRMADO (cacheados).

> The `Validation` column is kept as the fine-grained provenance; `Estado` is the binary rollup.
> The `Summary` sheet is aligned to these counts.

---

## COMPLETED (DO NOT MODIFY)

### DN — Digha Nikaya — 34 suttas — CERRADO 🔒
- Excel: `HELMER_APPROVED`
- DeepSeek PTS↔CST: 34/34 APPROVE
- RTE cross-ref: 32/34 confirmed
- DB content: 34/34 verified
- Source files: `helmer_dn_all.py`

### MN — Majjhima Nikaya — 152 suttas — CERRADO 🔒
- Excel: `HELMER_APPROVED` (138) + `HELMER_PTS_TRUNCATED` (14)
- DeepSeek PTS↔CST: 135/149 APPROVE
- 14 PTS_TRUNCATED: suttas where PTS abbreviates text (e.g., MN 98 = Sn 35)
- MN 14, 38, 64: were transient API errors (`OK+RTE`); Helmer DeepSeek re-run on 2026-07-24 →
  3/3 APPROVE → `HELMER_APPROVED`. All 152 now CONFIRMADO.
- DB content: 152/152 verified
- Source files: `audit_mn_final.py`, `add_mn_lines.py`, cached in `helmer_ptscst_cache.json`

### SN I — Samyutta Nikaya vol 1 (S i) — 271 suttas — CERRADO 🔒 271/271
- **Estado 2026-07-25: 271/271 CONFIRMADO** (`VALIDADOR`, concordancia VRI ∧ Gemini APPROVE).
  Antes eran 270 `DB_VERIFIED` + 1 `HELMER_FIXED` (todo PENDIENTE salvo uno).
- **El front matter de Feer (`samyutta-vol-I-info.txt`) fija el lado PTS sin LLM.** Su índice y su
  introducción dan la verdad-terreno estructural: 11 saṃyuttas, **28 vaggas, 271 suttas** y la
  **página de arranque de cada vagga**. La estructura hallada en la BD cuadra al 100% con ella, y
  el recuento por saṃyutta del Excel (81/30/25/25/10/15/22/12/14/12/25) coincide exacto.
- **Marcadores `§ N. Nombre.`, numerados POR VAGGA** (reinician) — un cuarto sistema de
  coordenadas. Gramática nueva en **`sn1_markers.py` (pyparsing**, documentada en
  `docs/grammar.md`). Dos variantes, sin las cuales se pierden **6 de los 271**:
  - **marcador «desnudo»**: el `§` se perdió en el OCR y queda `4. Nandano.` (S i 23, 52, 56, 73,
    124). Se discrimina del nº de párrafo (margen izquierdo) y del pada de gāthā (lleva `║`) por
    sangría ≥ 8, ausencia de `║`, longitud ≤ 48 y mayúscula inicial.
  - **rango con coma**: `§§ 4,5. Saṅgāme dve vuttāni.` (S i 82) — un encabezado, dos suttas. El
    bloque se parte por los **submarcadores** internos (`4.`/`5.` centrados a solas); sin partirlo
    ambos suttas comparten todo el texto y Gemini rechaza con razón (son dos batallas con
    desenlaces opuestos). Era el único REJECT de la tanda: 270/271 → 271/271.
  - **agrupación en vaggas**: dentro de un vagga el `§` crece estrictamente, así que un número que
    no crece abre vagga nuevo. Es la única regla fiable, porque el `§1` de arranque es justamente
    uno de los que el OCR puede haberse comido.
- **Alineación POSICIONAL** (Excel canónico ↔ marcadores en orden de lectura), no difusa, con dos
  comprobaciones cruzadas independientes: el nombre del marcador ≡ título CST en **231/271 (85%)**
  — el resto son los títulos variantes que Feer mismo advierte («los MSS no concuerdan»; imprime
  el de B) — y la página del marcador ≡ **`cst_p_page`** del concordance en **271/271 (100%)**.
- **XML VRI del Sagāthāvagga** (`romn/s0301m.mul.xml`): el nº de párrafo lo llevan `bodytext`
  **y `hangnum`** (223+48=271 — los suttas solo-verso usan `hangnum`) y el texto vive en los
  `gatha1/2/3/gathalast`. El índice de SN V (solo `bodytext`) se queda en 223.
- ⚠️ **Ojo con `cst_p_page`**: es `vol.pppp` (`1.0001` = vol I p. 1) pero guardado como DECIMAL, así
  que los ceros de cola se perdieron — `1.004` es la p. **40** y `1.01` la p. **100**. Hay que
  rellenar la fracción a 4 dígitos (`_pts_page`); leerla tal cual da 25 falsos desacuerdos.
- **Líneas calibradas: 201 corregidas → 271/271 exactas** (`calibrate_sn1_lines.py`). 162 filas no
  traían línea y solo 66 de las 266 con línea acertaban.
- **4 errores de PÁGINA corregidos** con doble evidencia independiente (marcador `§` en la BD *y*
  ancla `cst_p_page`, ambos contra el Excel, cuya página además contenía el marcador de otro
  sutta): **SN 4.3** p105→104, **4.5** p106→105, **6.8** p149→148, **11.10** p226→227.
- SN 3.1 (el viejo `HELMER_FIXED`, p70→68 corregida a mano) queda **confirmado por partida doble**:
  el marcador `§1 Daharo.` está en p68 L3 y el título CST casa.
- Fuentes: `sn1_markers.py`, `validador_sn1.py`, `reconcile_sn1.py`, `calibrate_sn1_lines.py`,
  `samyutta-vol-I-info.txt`. Los viejos `parse_sn_grammar.py` / `helmer_sn1_pilot.py` quedan
  SUPERADOS.

### SN II — Samyutta Nikaya vol 2 (S ii) — 255 suttas — CERRADO 🔒
- Excel: `DB_VERIFIED`
- Sequential audit: 0 page breaks
- Markers: 75% found (format: `N (M) Name` or `(N) (M) Name`)
- CST fingerprint sample: 83% accuracy (30 suttas)
- Note: Per-saṃyutta numbering with peyyāla gaps
- Source files: `audit_sn2.py`

### SN III — Samyutta Nikaya vol 3 (S iii) — 326 suttas — CERRADO 🔒
- Excel: `DB_VERIFIED`
- Sequential audit: 0 page breaks
- Source files: `parse_sn_grammar.py`

### SN IV — Samyutta Nikaya vol 4 (S iv) — 344 suttas — CERRADO 🔒
- Excel (as of 2026-07-24 reconciliation): `HELMER_APPROVED` (94) + `HELMER_REJECT` (12) +
  `DB_VERIFIED` (238 peyyāla). See "UPDATE 2026-07-24" at top.
- DeepSeek PTS↔CST: 94/106 APPROVE (89%)
- 12 REJECT: false positives (Feer abbreviation / orthographic; names match CST). Review SN 36.26.
- 238 PEYYALA: no individual markers (abbreviated suttas)
- Marker format: `N (M) Name` or `N. (M) Name`
- CST file: s4m.xml (344 suttas, perfect match)
- Method: exact gid match on stated page → sutta-bounded text → DeepSeek
- Source files: `helmer_sn4_pilot20.py`, `helmer_sn4_v3.py`, cached in `helmer_ptscst_cache.json`

### SN V — Samyutta Nikaya vol 5 (S v) — 610 suttas — CERRADO 🔒 610/610
- **Estado 2026-07-25 (3ª pasada): 610/610 CONFIRMADO.** 571 `VALIDADOR` (concordancia VRI ∧
  Gemini APPROVE) + 39 `VALIDADOR_HUMANO` (18 desacuerdos arbitrados antes + las 21 peyyāla
  elididas, dispuestas en bloque por Jorge el 2026-07-25 vía
  `reconcile_sn5.py --humano firmas_sn5_peyyala.json`).
- Alineado por el **pipeline VRI por concordancia** (definitivo): Excel(DPR) → `massive.tsv`
  (`cst_paranum`) → XML VRI (`/tmp/tipitaka-xml/romn/s0305m.mul.xml`) → texto CST exacto; lado
  PTS por marcadores DB (libro 16). Validador Modelo B con `concordant=True` (concordancia
  exacta ∧ Gemini; el gate de cobertura sobra). Drivers: `validador_sn5_vri.py` + `validador_sn5.py`
  (parser de marcadores: `(M)`, rangos `103--108. (1--6)`, grupo profundo `89--98.1--10.`,
  centrado simple `5. Bhikkhu.`, y fallback a página). Reconciliación: `reconcile_sn5.py`.
  Los viejos `helmer_sn5_*.py` quedan SUPERADOS.
- **580 → 589: 9 de las 30 "peyyāla" NO lo eran** — eran fallos del resolvedor PTS, ahora
  corregidos en `validador_sn5.py` (auditados con un diff de texto PTS viejo↔nuevo sobre las 602
  entradas, sin gastar API, para garantizar que ninguna de las ya CONFIRMADO se degradaba):
  1. **Marcador perdido por OCR** — `4O. (10) Nandiya.` en S v 397 lleva letra `O` por cero, así
     que el parser no veía la línea y caía al texto de página entera (`_fix_ocr_num`; es el único
     caso del volumen). SN 55.40 ✅.
  2. **Off-by-one de PÁGINA** — `pts_for` solo miraba la página declarada; el marcador está a
     veces en la siguiente (ahora busca ±1). Recupera 55.56, 56.22, 46.36, 51.19, 54.16, 48.72/73,
     51.34, 56.102/104…
  3. **`_stem` no quitaba `-suttaṃ`** — colapsaba las consonantes dobles ANTES de recortar el
     sufijo, así que `suttaṃ`→`sutam` ya no casaba con el patrón. Corregido el orden.
  4. **Nombre laxo vs nº corrido** — la contención de nombres NO distingue los pares
     paṭhama/dutiya de las series peyyāla (el marcador PTS los llama igual, `Pathavī1./Pathavī2.`),
     así que el nombre solo se antepone al nº cuando la coincidencia es fuerte, o cuando es
     inequívoca y el título CST no lleva ordinal (`name!`: recupera 45.112 `Nivaraṇāni`, que es el
     177 en PTS y el 178 en DPR). Empate → marcador de más arriba (antes ganaba el de más abajo,
     que se llevaba el sutta siguiente).
  5. **Fragmento sin cuerpo** — dos marcadores de rango consecutivos dejaban un "sutta" de 1 token;
     `MIN_PTS_TOKENS=3` lo descarta y sigue la cadena (ojo: los peyyāla PTS legítimos tienen 4
     tokens, un umbral alto degrada decenas de filas).
- **21 PENDIENTE = clase peyyāla** (concordancia VRI exacta, texto ELIDIDO en PTS y/o CST → sin
  texto que Gemini pueda cotejar; su REJECT es falso-negativo por elisión, no desalineación).
  Desglose: 13 `DB_VERIFIED` (grupos `Esanādi/Oghādi/Tathāgatādi/Balādi/Pācīnādi/Chedanādi`,
  donde PTS imprime solo el uddāna) + 8 `REF_ERROR_DPR` **verificados: NO son error de DPR** —
  son los grupos de repetición "Puna-" (46.130/131/143/153/165/175, 49.13, 50.13), elididos
  SIMÉTRICAMENTE en ambas ediciones con `...rāgavasena vitthāretabbo` (solo uddāna; análogo
  inverso del `PTS_CROSSREF_SN`). Disposición PENDIENTE de decisión de Jorge (valor nuevo
  `VALIDADOR_PEYYALA` vs `VALIDADOR_HUMANO` en bloque) — dejado abierto a propósito.
  Excepción dentro de las 21: **45.113 Upādānakkhandha** no es peyyāla sino ambigüedad de nombre
  (el marcador PTS `Khandā.` gid 178 es el correcto, pero `Upādānam.` gid 173 es prefijo del
  título CST `Upādānakkhandhasuttaṃ` y gana; ninguna regla de nombre lo desempata) → arbitraje.
- ⚠️ **6 filas CONFIRMADO con evidencia superada** (`Validation=VALIDADOR` en el Excel pero el
  veredicto vigente en `validador_sn5_vri.json` es REJECT): **45.71, 50.3, 52.18, 55.67, 55.69,
  55.71**. `reconcile_sn5.py` no degrada por diseño (protege la procedencia), así que siguen
  marcadas. 45.71 y 50.3 rechazan con el texto MEJOR alineado de esta pasada (su APPROVE previo
  se apoyaba en el texto de página entera); 52.18/55.67/55.69/55.71 ya rechazaban antes. Decisión
  de Jorge: degradar a PENDIENTE (→ 583/610 real) o arbitrar a mano.

- **Líneas calibradas (2026-07-25)** — `calibrate_sn5_lines.py`. La línea de `PTS Ref`
  (`S v <pág>,<línea>`) es la del **marcador centrado** del sutta, y el dato del Excel venía
  MEZCLADO: solo 75/546 coincidían; el resto se agolpaba en 2–8 sobre páginas de ~29 líneas
  (distribución imposible para posiciones reales — no eran líneas, y 144 filas no traían ninguna).
  Recalculadas contra el texto de la BD (libro 16) reusando la cadena de resolución del pipeline
  VRI: **471 corregidas → 546/546 exactas**. Auditoría independiente antes de escribir: el nombre
  del *Excel* contra el nombre del *marcador* (señal que el resolvedor no usó, pues casa por título
  CST) → 441/546 casan; las 105 que no son variantes abreviadas de Feer (`Araham1.` =
  `Paṭhamārahanta`, `Bodhanā.` = `Bodhāya`) donde el marcador sí concuerda con el título CST.
- **2 residuos deliberados en las líneas** (no se tocan, a arbitraje contra el impreso):
  - **45 filas con la página en disputa** — el marcador está en la página vecina, no en la que
    declara el Excel. Reescribir la *página* es una afirmación mayor que la línea y queda fuera del
    alcance de la calibración; `calibrate_sn5_lines.py` las lista.
  - **19 sin marcador resoluble** (45.75/76, 46.58, 46.87–92, 48.74, 49.2/5, 50.2/5/6,
    56.99–101, 56.109): grupos peyyāla sin marcador propio → línea intacta.
- ⚠️ **6 filas CONFIRMADO con evidencia superada** (`VALIDADOR` en el Excel pero el veredicto
  vigente en `validador_sn5_vri.json` es REJECT): **45.71, 50.3, 52.18, 55.67, 55.69, 55.71**.
  `reconcile_sn5.py` no degrada por diseño (protege la procedencia). Jorge decidió (2026-07-25)
  **dejarlas y revisarlas a mano** contra el impreso/CST — cola de arbitraje abierta, no un
  pendiente del pipeline. Nótese que 45.71 y 50.3 también aparecen en las 45 con página en disputa.

---

## PENDING

### AN — Anguttara Nikaya — 1,738 entries ⏳
- Pages restored from blog, lines added via sequential matching
- Spot-check: 11/11 pages verified
- No Helmer validation yet

### KN — Khuddaka Nikaya — 2,360 entries ⏳
- 254 off-by-one corrections applied
- 624 vol/page fields repaired
- Line numbers added for 93.7% of canon entries
- No Helmer validation yet
- Thag 100%, Ud 100%, Sn 100% marker coverage

---

## METHOD: cómo validar lo que queda (AN/KN) — pipeline VRI + validador

> **Histórico:** lo que había aquí describía el pase **DeepSeek "Helmer"** (RETIRADO: no
> determinista a `temperature=0`) y un mapeo CST `frontera[saṃyutta] + (inner-1)` que se demostró
> **roto** (dio 8% de APPROVE en SN V). No usar ninguno de los dos. El método vigente es el que
> cerró SN V 610/610.

### Flujo (probado en SN V, directamente portable a AN/KN)
1. **Alinear por CONCORDANCIA, no por contenido ni por número.** El `Sutta #` del Excel está en
   notación **DPR**; `massive.tsv` (raíz del repo) enlaza `dpr_code` → `cst_paranum` + `cst_sutta`.
2. **Texto CST** desde el **XML VRI** (`/tmp/tipitaka-xml/romn/*.mul.xml`), por `<p rend="bodytext"
   n="N">` con `N = cst_paranum` (los `n` pueden ser rangos, `"42-47"`).
3. **Texto PTS** desde la BD (`pages`, `edition='mula'`) localizando el **marcador centrado** del
   sutta. Prioridad que funciona: **nombre fuerte** (idéntico/prefijo del título CST) → **nº
   corrido** (el único que separa los pares paṭhama/dutiya de las series peyyāla) → **nombre laxo
   inequívoco** → contenido → página. Buscar siempre la página declarada **±1**.
4. **Validar** con `validador.validate_pair(..., concordant=True)`: con alineación exacta,
   CONFIRMADO = concordancia ∧ Gemini APPROVE (el gate de cobertura sobra).
5. **Volcar** con un reconciliador que NO degrade la procedencia humana y haga backup del Excel.

### Antes de gastar API: auditar el resolvedor con un diff de texto
Cualquier cambio en el resolvedor PTS se audita **sin llamadas a la API** comparando el texto que
devuelve el resolvedor viejo contra el nuevo, entrada por entrada. Así se ve de inmediato si una
"mejora" degrada filas ya CONFIRMADO — así se encontraron los 5 fallos que subieron SN V de 580 a
610. Umbrales: cuidado con los mínimos de longitud, los peyyāla PTS legítimos tienen 4 tokens.

### Líneas de `PTS Ref`
La línea es la del **marcador centrado** del sutta en la página. Los valores del Excel vienen
mezclados y en su mayoría no son líneas (ver SN V): recalcular con el mismo resolvedor
(`calibrate_sn5_lines.py` como plantilla) y **no reescribir la página**, solo la línea.

### Key files:
- `PTS_Reference_Complete_Canon.xlsx` — master output (3 hojas; `Estado` = rollup binario)
- `validador.py` — el juez (Modelo B), nikāya-agnóstico
- `validador_sn5.py` / `validador_sn5_vri.py` / `reconcile_sn5.py` / `calibrate_sn5_lines.py`
  — driver SN V completo, la plantilla a copiar para AN/KN
- `massive.tsv` — concordancia dpd/cst/dpr/sc/bjt con `cst_paranum` y páginas VRI
- `/tmp/tipitaka-xml/romn/*.mul.xml` — texto CST (VRI)
- `src/data/tipitaka.sqlite` — edición PTS (`edition='mula'`)
- `/dev/shm/dpd.db` — DPD
- `helmer_*.py`, `helmer_ptscst_cache.json` — **legado del pase DeepSeek retirado**

### Pitfalls:
- La numeración SN resetea por saṃyutta — usar el nº corrido (gid), no la posición en la vagga
- Peyyāla: suttas sin marcador propio, con el texto ELIDIDO en PTS y/o CST. El REJECT del LLM ahí
  es un falso negativo por elisión, no una desalineación → arbitraje, no PENDIENTE automático
- Los ficheros CST traen más saṃyuttas que el Excel (s5m.xml llega a SN 112)
- SN I usa marcadores `§ N.`; SN II–V, `N (M) Nombre` (y rangos, y centrados sin paréntesis)
- Feer abrevia más que el CST — contar con ~10% de REJECT falsos
- **El OCR de la BD mete letras por dígitos en los marcadores** (`4O. (10)` en S v 397): un
  marcador "ausente" puede ser esto, no una laguna del texto
- El nombre del marcador PTS puede ser una variante de Feer (`Araham1.` = `Paṭhamārahanta`): casar
  por nombre contra el título CST, y usar el nombre del Excel solo como señal de auditoría

---

## RULES (from README)
- ⚠️ NADA se cierra sin el **validador** (Modelo B: gate local ∧ Gemini, PTS↔CST). El pase
  DeepSeek "Helmer" está RETIRADO (no fiable); sus marcas `HELMER_*` son CONFIRMADO provisional
- ⚠️ La única fuente de verdad es `tipitaka.sqlite` (edición 'mula')
- ⚠️ NO HAY HOMOGENEIDAD entre Nikayas — cada uno requiere su propio parser
