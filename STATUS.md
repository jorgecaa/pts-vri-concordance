# PTS Reference Concordance — Status Report
## Date: 2026-07-21 (updated 2026-07-25 — SN I-V cerrados con el validador: 1810/1814)

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
| SN | 1815 | 1564 | 251 | 86.2% |
| AN | 1738 | 1 | 1737 | 0.1% |
| KN | 2360 | 0 | 2360 | 0.0% |
| **TOTAL** | **6099** | **1751** | **4348** | **28.7%** |

> Cifras al **2026-07-25**. **SN entero pasado por el validador: 1810/1815.** Desglose:
> **S i 271/271, S ii 257/257, S iii 332/332 🔒, S iv 340/344, S v 610/610**. Ya no queda ningún
> `HELMER_*` en SN: los 94 `HELMER_APPROVED` y 12 `HELMER_REJECT` de S iv se re-validaron y se
> sobrescribieron. Las 5 PENDIENTE de SN son desacuerdos gate/Gemini a arbitraje humano.
> El total pasó de 6090 a **6099 filas**: −1 (`12.74`, división solo-CST borrada) y +10 (la
> expansión de `12.75` en los 11 suttas que PTS numera). La columna `#` se renumeró.

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

### SN II — Samyutta Nikaya vol 2 (S ii) — 257 filas / 286 suttas — CERRADO 🔒 257/257
- **Estado 2026-07-25: 257/257 CONFIRMADO** — 246 `VALIDADOR` + 11 `VALIDADOR_HUMANO`
  (el *antara-peyyālaṃ*, ver abajo).
  Antes: 255 filas todas `DB_VERIFIED` → PENDIENTE.
- **El front matter de Feer (`samyutta-vol-II-info.txt`) fija el lado PTS sin LLM**: 10 saṃyuttas
  (numerados **XII–XXI** en la notación corrida), **27 vaggas, 286 suttas**
  (93/11/39/20/13/43/22/21/12/12) y la página de arranque de cada uno. La estructura hallada en la
  BD cuadra al 100%. Feer explica ahí mismo las dos numeraciones (sección/saṃyutta/vagga/sutta vs
  **saṃyutta/sutta**, «XII. 25. 4») y que prefiere la segunda — que es la del `Sutta #` del Excel.
- **248 filas cubren los 286 suttas**: los grupos peyyāla van en **una sola fila de nombre
  colectivo** (`Jātisuttādidasakaṃ` = PTS 72–81, `Suvaṇṇanikkhasuttādiaṭṭhakaṃ` = 17.13–20,
  `Pitusuttādichakkaṃ` = 17.38–43, `Sikkhāsuttādipeyyālaekādasakaṃ` = 12.83–93), igual convención
  que en SN V. **No faltan filas** (un primer diagnóstico dijo «faltan 38» y era falso: eran los
  miembros de esos grupos).
- **Gramática nueva `sn2_markers.py` (pyparsing)** — marcador `N (M) Nombre` **sin puntos**, ajeno
  al `§ N.` de S i y al `N. (M)` de S iv–v. Detalle y las tres reglas no evidentes (el recuento lo
  manda el rango; la sangría mínima depende de la forma; un rango puede ser solo el encabezado de un
  grupo cuyos miembros se reimprimen) en `docs/grammar.md`.
- ⚠️ **21 `Sutta #` ERRÓNEOS corregidos** (`reid_sn2.py`). En SN 17 la numeración del Excel iba
  **desplazada +7** desde 17.14 (la fila que se llamaba `17.21` se titula *Chavi*, está en la p. 237
  y es el sutta **17.28** en PTS y en DPR/CST), y en SN 18 +8 en las dos últimas. Se detectó por la
  comprobación cruzada de nombres (82%, con los fallos agrupados en SN 17), **no por el LLM**: al
  emparejar por el `Sutta #` malo se comparaba un par PTS↔CST correcto entre sí pero ajeno a la
  fila, y Gemini aprobaba. Los 21 veredictos mal adjudicados se descartaron y se re-validaron con la
  identidad corregida (22/22 APPROVE); la concordancia de nombres subió a 85%.
  **Lección: sin una comprobación cruzada independiente de la clave de emparejamiento, un APPROVE
  no dice nada sobre la fila.** La identidad verdadera de una fila la dan `Sutta Name` + `PTS Page`
  (concuerdan entre sí y con las dos fuentes); el `Sutta #` es el campo que se corrompió.
- **7 filas con el VOLUMEN mal puesto** (`fix_sn2_vol_labels.py`): SN 22.153–159 estaban como
  «S ii» y son **S iii** (SN 22 = Khandha abre el vol. III, como dice Feer). Evidencia:
  `cst_p_page = 3.0183…3.0187` (vol 3, mismas páginas), los títulos CST casan uno a uno, S ii 183
  habla de *kappā* (Anamatagga) mientras S iii 183 trata de rūpaṃ/attā, y 152+7 = **159**, el total
  canónico de SN 22.
- **Líneas: 39 corregidas → 254/254 exactas**; y **14 páginas** corregidas con doble evidencia
  (marcador + ancla `cst_p_page` de acuerdo entre sí y contra el Excel): 12.14, 12.24, 12.25, 12.42,
  12.43, 12.55, 13.5, 13.11, 14.7, 14.8, 14.27, 14.31, 18.3, 21.2 (`calibrate_sn2_lines.py`).
- Fuentes: `sn2_markers.py`, `validador_sn2.py`, `reid_sn2.py`, `reconcile_sn2.py`,
  `calibrate_sn2_lines.py`, `fix_sn2_vol_labels.py`, `fix_sn2_antarapeyyala.py`,
  `samyutta-vol-II-info.txt`. `audit_sn2.py` queda SUPERADO.

### El *antara-peyyālaṃ* de SN 12 (S ii 130–133) — verificado contra el impreso

Dos filas venían con la forma del **CST**, no la de PTS. Se resolvió leyendo lo que PTS declara
(`fix_sn2_antarapeyyala.py`, decisión de Jorge 2026-07-25):

- **`12.74 «Dutiyasatthusuttādidasakaṃ»` BORRADA — no es un sutta en PTS.** El CST parte el sutta
  PTS 82 «Satthā» en `1. Satthusuttaṃ` (ítem jarāmaraṇa) + `2-11. Dutiyasatthusuttādidasakaṃ`
  (ítems jāti…saṅkhāra). PTS imprime todo como UN sutta y lo dice literalmente: tras el §1 escribe
  **`Suttanto eko`** («un solo sutta», S ii 130 L28) y sigue con `Sabbesam evam peyyālo` y los
  §§2–11 (S ii 131 L1–28). Su uddāna remata: «Satthā Sikkhā … **Appamādena dvādasāti**» = **doce**
  suttas, y «Pare te dvādasa honti, suttā dvattiṃsasatāni» = doce (o 132 contando por ítem). Sin
  referencia PTS propia, la fila no pertenece a una concordancia de PTS.
  > ⚠️ **No era una elisión** — el texto SÍ está en PTS; lo que no existe es la división en suttas.
  > Una nota anterior de este documento decía «PTS elide el grupo Dutiyasatthu entero» y era falsa
  > en las dos mitades. **Distinto del caso de SN V**, donde PTS sí numera los suttas
  > (`122--132. (2--12)`, `143--154. (1--12)`) y elide solo el *texto* con `vitthāretabbo`: ahí las
  > 8 filas siguen bien.
- **`12.75 «Sikkhāsuttādipeyyālaekādasakaṃ»` EXPANDIDA a 11 filas (12.83–12.93).** Aquí el CST
  agrupa pero **PTS numera**: `83 (2) Sikkhā`, `84 (3) Yogo`, … `93 (12) Appamādo`, cada uno con su
  marcador (a diferencia de 12.72, 17.13 o 17.38, donde PTS sí imprime rango). Las 11 llevan su
  página y línea reales.
- **Las 11 son `VALIDADOR_HUMANO` por evidencia MECÁNICA, no por LLM**: el nº de ítem del grupo CST
  **es** la posición `(M)` del marcador PTS, y la palabra clave del marcador aparece **literal** en
  su ítem (11/11 verificado: sikkhā, yogo, chando, ussoḷhī, appaṭivāni, ātappa, viriya, sātacca,
  sati, sampajañña, appamāda). El texto PTS son 4 tokens (`ºyogo karaṇīyo ║ (1-11)`), así que
  Gemini no tiene qué cotejar y sus 7 REJECT son falsos negativos por elisión. El emparejamiento
  lo hace `build_cst_group_items` + `CST_GROUP` en `validador_sn2.py`, **fijando el grupo por
  título**: hay varios grupos con los mismos nºs de ítem y buscarlo por parecido de texto elige el
  equivocado (se comprobó: daba `Dutiyasatthu…` y `Jāti…`).

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

### SN III — Samyutta Nikaya vol 3 (S iii) — 332 filas — CERRADO 🔒 332/332
- **Estado 2026-07-25 (5ª pasada): 332/332 CONFIRMADO** (316 `VALIDADOR` + 16 `VALIDADOR_HUMANO`). Antes: 326 filas
  `DB_VERIFIED` (+7 que llegaron de S ii al corregir su volumen) → todo PENDIENTE.
- **Front matter de Feer (`samyutta-vol-III-info.txt`)**: 13 saṃyuttas **XXII–XXXIV**, y la página
  de arranque de cada uno **cuadra al 100%**. Feer distingue **títulos** de **suttantas** (Nāga son
  14 títulos = 50 suttantas; Gandhabba 10 = 112), y el nº de suttantas cuadra en **12 de 13**:
  158/46/·/10/10/10/10/50/46/112/57/55/55.
  - El 13º, **Diṭṭhi (XXIV)**, lo explica Feer mismo: cuenta 114 (18 + 4 gamana × 26) pero
    **confiesa haber omitido del texto los primeros 18 de la 2ª gamana**, así que el volumen imprime
    **96**; y de esos 96 solo **72 llevan marcador**, porque los 72–95 de la 4ª gamana van elididos
    (PTS salta de `71 (1)` a `96 (26)`). Total impreso del volumen: **691 marcadores / 715 suttantas
    reckoned**, y el 733 de Feer = 715 + los 18 que él omitió. Todo conciliado.
- **Gramática nueva `sn3_markers.py` (pyparsing)** — misma familia que S ii (`N (M) Nombre` sin
  puntos) más tres formas propias: **nombre entre paréntesis** (`11 (Samāpatti-ṭhiti)`), **rango con
  posición-rango** (`140-142 (5-7) Dukkhena (1-3)`) y **prefijo de subdivisión** (`(3)11-15
  Anabhisamayā (1-5)`), que es el *gamana* en el Diṭṭhi y el **nº de título** en el Vacchagotta
  (11 títulos × 5 khandhas = 55 suttantas). Ese prefijo abre saṃyutta solo si vale 1 — `(27)1-4`
  (SN 34) es una combinación interna. La sangría mínima de la forma sin paréntesis baja a **12**
  (el `1 Samādhi-samāpatti` que abre SN 34 está a 14; el umbral 20 de S ii se lo comía), a cambio
  de descartar las cabeceras de uddāna y de *gamana* en versal.
- ⚠️ **La clave `(saṃyutta, nº)` NO sirve en este volumen** — y aquí el desajuste es al revés que en
  S ii: **el Excel y el concordance concuerdan entre sí** y es la numeración PTS la que difiere,
  porque PTS imprime **158** suttas en el Khandha-saṃyutta y el CST/DPR cuenta **159**, con lo que
  se desfasa +1 en la cola. El lado PTS se resuelve por **nombre del marcador sobre la página que
  ancla `cst_p_page`** (`resolve_pts`): las 333 filas resolvieron por nombre (234) o por clave con
  el ancla de acuerdo (99), **sin fallbacks**.
- **Pares `Dutiya-`**: Feer no escribe el ordinal — imprime dos veces el mismo nombre —, así que hay
  que tomar el **k-ésimo homónimo en orden de lectura** o se coteja el sutta contiguo. Era la causa
  de la mayoría de los REJECT del primer pase (22.52, 22.158, 29.4, 29.5…).
- **Líneas**: 75 + 35 corregidas → **316/316 exactas**; **7 páginas** con doble evidencia
  (22.15, 22.42, 22.52, 22.114, 22.121, 23.25, 28.2).
#### Cómo se resolvieron las 24 pendientes (2ª pasada)

Tres causas, ninguna resoluble por el LLM; el cruce de nombres subió de **63% a 88%**.

1. **`massive.tsv` colapsa los rangos** — el TSV da un solo `cst_paranum` por grupo (el del primer
   miembro), así que los 17 miembros de `SN24.19-35` se cotejaban contra el sutta 1 del saṃyutta.
   **`massive.tsv` NO se modifica**: el arreglo va en el lector, `massive_reader.py`, que expande
   `para + (k−a)` **con compuerta** — solo si TODOS los paranum resultantes existen en el XML, que
   es lo que ocurre cuando el destino cae en el bloque elidido del CST (`225-240`, `251-274`,
   `277-300`). Si algún paranum no existe se deja colapsado: nunca se inventa una referencia.
2. **El Diṭṭhi-saṃyutta (SN 24) no sigue ninguna numeración** — sus 32 filas van `24.1`…`24.32`, un
   índice corrido que no es DPR (`24.21 «Rūpīattā»` es DPR `SN24.37`) ni PTS. Pero las tres fuentes
   listan **los mismos 32 suttas EXPLÍCITOS** (los que no caen en bloque elidido) y en el mismo
   orden, así que se alinean por posición (`ditthi_pairs`): **32/32 con el nombre coincidiendo**.
   Los bloques elididos quedan fuera en ambas ediciones y las dos lo dicen — el CST con
   `(Purimavagge viya aṭṭhārasa veyyākaraṇāni vitthāretabbānī)`, PTS con `20--35 (2--17)` y el salto
   de `71 (1)` a `96 (26)`.
3. **PTS agrupa donde el CST numera** — en S iii 179 PTS imprime TRES suttas
   (`146-148 Kulaputtena dukkhā (1)(2)(3)`) donde el CST tiene CUATRO, y de ahí el último vagga
   corre con **PTS = CST − 1**. `calibrate_offsets` prueba desplazamientos pequeños y acepta el
   tramo **solo si con él casan TODOS los nombres** hasta el final del saṃyutta (en el Khandha,
   10/10). Nada se adivina.

- Efecto colateral controlado: la lectura nueva cambia el texto CST bajo filas ya validadas, así que
  se **re-validaron** las afectadas en vez de heredar el veredicto (58 + 33 en S iii, 20 en S v).
  En S v el resultado se sostiene (610/610): 8 de los 9 rechazos nuevos ya eran `VALIDADOR_HUMANO`
  de la clase peyyāla, y **50.3** se reclasificó a `VALIDADOR_HUMANO` junto a sus hermanas 48.74,
  49.5, 50.4 y 53.2 (PTS imprime solo el uddāna del grupo).
- **16 `VALIDADOR_HUMANO`** — peyyāla donde una edición agrupa lo que la otra numera, con el par ya
  identificado; se firman por **prueba mecánica**, no por LLM: las palabras clave del nombre
  aparecen literalmente en el texto de su contraparte (16/17 verificado).
- **El Jhāna-saṃyutta, resuelto por TÍTULO.** Sus 10 series van colapsadas en el CST y el
  concordance mandaba varias filas al bloque de la serie «ṭhiti-». Pero el **título del subhead
  nombra la serie** y es casi idéntico al `Sutta Name` del Excel
  (`Kallitamūlakaārammaṇasuttādichakkaṃ` = `n=696-701`), así que `build_cst_by_title` lo resuelve.
  La regla se aplica **solo si el título del paranum no tiene NADA que ver** (score 0) **y** el
  título candidato coincide **exactamente** (score 100): con un umbral laxo se disparaba en 43 filas
  cuyo paranum era correcto y empeoraba el resultado.
- **1 PENDIENTE — `30.5 «Aṇḍajadānūpakārasuttadasakaṃ»`**: el título CST coincide exacto y el lado
  PTS es su marcador de rango («Dānupakārā»), pero la palabra clave `aṇḍaja` no aparece literalmente
  en el bloque elidido de PTS, así que no supera la prueba mecánica. Queda a criterio humano.
- **Líneas: 317/317 exactas**; ninguna fila queda sin nº de línea.

#### Tres fallos de resolución corregidos en la 3ª pasada

Los detectó revisar «¿está terminado?» fila a fila, no el LLM:

- **Nombres compuestos `X-mūlaka-Y`** (Jhāna-saṃyutta): el marcador correcto es el **compuesto** de
  PTS («Kallita -- ārammaṇa», «Gocara-Abhinīhāra»), no el simple. Buscar por afinidad suelta elegía
  «Kallita» o «Gocara», que son otros suttas (`_MULAKA` en `resolve_pts`).
- **La contención de nombres se medía tras recortar la terminación de caso**, con lo que «Saññā»
  quedaba en «san» —por debajo del mínimo— y su compuesto «Rūpasaññā» casaba con «Rūpa» de la página
  vecina (S iii 25.6). Ahora se mide antes del recorte.
- ⚠️ **Una corrección de página previa era ERRÓNEA**: `22.15 «Yadanicca»` se había pasado de p22 a
  p21 apoyándose en una resolución equivocada. El sutta arranca en «15 (4) Yad anicca (1)», **S iii
  22 L1**; revertida. Las otras seis correcciones de página de S iii se re-verificaron y son buenas.
- Fuentes: `sn3_markers.py`, `validador_sn3.py`, `reid_sn3.py`, `reconcile_sn3.py`,
  `calibrate_sn3_lines.py`, `samyutta-vol-III-info.txt`. `parse_sn_grammar.py` queda SUPERADO.

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

---

## PLAN DE REMEDIACIÓN Y CIERRE (2026-07-25)

### El defecto que lo motiva

La resolución del lado PTS se hace **fila a fila y no es inyectiva**: dos filas del Excel pueden
acabar en el mismo marcador, con lo que una de ellas se valida contra el locus de su vecino. El
validador no puede detectarlo — compara un par PTS↔CST correcto *entre sí* pero ajeno a la fila —
y por eso pasó los controles. Es la misma familia de error que los 21 `Sutta #` desplazados de S ii.

Alcance medido (marcadores compartidos / filas implicadas):

| Volumen | Cómo resuelve el lado PTS | Estado |
|---|---|---|
| **S i** | posicional (1:1 por construcción) | **limpio** — 0 |
| **S ii** | clave exacta `(saṃyutta, nº corrido)` | **limpio** — 0 |
| **S iii** | por nombre sobre la página del ancla | **16 marcadores / 38 filas**; 22 filas sin marcador propio pudiendo tenerlo |
| **S v** | nombre → nº → nombre laxo, con fallbacks | **16 marcadores / 36 filas** |
| **S iv** | — | sin hacer; heredaría el defecto |

### Estado de ejecución (2026-07-25)

- **Fase 0 — HECHA.** `audit_injectivity.py`. Línea base: S i 0, S ii 0, S iii 12, S v 12 (total 24).
  **Tras la fase 1: 0 en los cuatro volúmenes.**
- **Fase 1 — HECHA.** `align_rows.py` (alineamiento monótono con capacidad por DP, probado en
  aislamiento) enchufado a S iii y S v. Antes hubo que arreglar un defecto anterior que lo impedía:
  > **`build_pts_suttas` perdía 4 marcadores.** Indexaba por `(saṃyutta, nº)` y en el Jhāna-saṃyutta
  > las claves de *gamana* (`(27)1-4`) machacaban los números 1–4 reales, así que
  > `1 Samādhi-samāpatti` (S iii 263), `2 Ṭhiti`, `3 Vuṭṭhāna` y `4 Kallavā` nunca llegaban al
  > resolvedor — la razón de fondo de que `34.1` apuntara a S iii 273 desde el primer pase. Ahora
  > cada registro lleva su posición de lectura (`ord`) como identidad única, el índice por
  > `(saṃyutta, nº)` da preferencia al registro sin gamana y `pts_records()` expone el inventario
  > completo. SN 34 pasa a mapear 1:1 (34.1→`Samādhi-samāpatti` … 34.10→`Sappāyam`).
  En S v la asignación va sobre **todo el volumen**, no por saṃyutta: por partes, dos filas de
  saṃyuttas contiguos reclamaban el mismo marcador en la frontera (S v 305: 52.21 y 53.1).
- **Fase 2 — HECHA en S iii; S v se deja como está (decisión de Jorge).**
  - **S iii**: 33 pares cambiaron, se re-validaron (30 APPROVE) y se volcaron; líneas recalibradas
    con la misma asignación → **316/316 exactas**. Sigue en **332/333**.
- **Fase 2bis (2026-07-25) — el alineador no devolvía el óptimo.** Al mirar S iii 30.5 salió a la luz
  que `main()` de `validador_sn3.py` seguía llamando al resolvedor fila a fila (la conexión de
  `assign_volume` se había perdido en un `git checkout`), y al reconectarlo aparecieron **24 pares
  distintos**, 21 APPROVE. Pero el tramo 22.146-149 seguía mal, y la causa era un **defecto de
  `align_rows.assign`**: el estado «fila saltada» era un escalar sin memoria de la posición del
  marcador, así que sólo se admitía cuando superaba el máximo global — y se perdía el óptimo justo
  donde importa, en una fila del CST que PTS **no imprime** en mitad de una serie. Reescrito: el
  salto conserva el estado `(marcador, racha)`, que además es lo correcto filológicamente (si a un
  marcador de rango le falta uno de los suttas del CST, sus vecinos siguen cayendo en él). Ahora es
  **óptimo demostrado**: 400/400 casos aleatorios contra fuerza bruta, con monotonía y capacidad.
  Se añadió también al score el **solapamiento léxico CST↔marcador**, única evidencia que discrimina
  cuando PTS numera una serie `(1)(2)(3)` bajo un título común.
  - **Efecto**: en S v, **ninguna** asignación cambia; en S iii cambian sólo `22.148` y `22.149`.
  - **Hallazgo**: PTS **no imprime** `22.148 Dukkhānupassī`. Los tres marcadores «Kulaputtena dukkhā
    (1)(2)(3)» de S iii 179-180 rezan *nibbidā-bahulaṃ* (146), *aniccānupassī* (147) y
    *anattānupassī* (148); el dukkhānupassī del CST cae dentro del «pa» de elisión al final del
    nº 147. Es la fusión 4→3 que ya detectaba `calibrate_offsets` (de ahí `PTS = CST − 1` a partir
    de 150), pero hasta ahora se le quitaba el marcador al sutta equivocado (149 en vez de 148).
  - **`22.148 Dukkhānupassī`: fila BORRADA (arbitraje de Jorge, 2026-07-25).** PTS **no numera**
    ese sutta —su cuenta corre 146, 147, 148 para tres, cuyos cuerpos rezan *nibbidā-bahulaṃ*,
    *aniccānupassī* y *anattānupassī*— y **el uddāna nunca cuenta cuatro**: PTS y CST transmiten el
    MISMO verso, «…kulaputtena **dve** dukāti» (dos), con la nota de Feer *«So all the MSS.; it
    ought to be tayo»*; él enmienda a tres e imprime tres, y el CST imprime cuatro. La cuenta de
    suttas *Kulaputtena* es inestable en la tradición (2 transmitido / 3 Feer / 4 CST). Es por tanto
    una división **sólo del CST**, sin referencia PTS: mismo criterio que zanjó `12.74` («Suttanto
    eko», S ii 130). En contra jugaba el `║ pa ║` al final del nº147, que cae donde va el
    *dukkhānupassī* en la serie *anicca→dukkha→anatta*: PTS conoce la continuación y la abrevia,
    pero no la numera. **Canon: 6098 filas** (la columna `#` se renumeró).

### SN 34 (Jhāna-saṃyutta): NO HAY HOMOGENEIDAD NI DENTRO DE UN SAṂYUTTA

Corregido 2026-07-25 tras la observación de Jorge («deberías crear dos analizadores»). SN 34 se
imprime bajo **dos convenciones opuestas** y una sola regla se equivocaba en una de ellas:

| parte | CST | marcador PTS | qué nombra la abreviatura |
|---|---|---|---|
| **1-19** individuales | `3. Samādhimūlakavuṭṭhānasuttaṃ` | «Vuṭṭhāna» | el **segundo** elemento (la raíz es constante y se da por sabida) |
| **20-55** grupos | `46-49. Gocaramūlakaabhinīhārasuttādicatukkaṃ` | «Gocara-Abhinīhāra» / «Ārammaṇa **--**» | el **par**, o sólo la **raíz** si va truncado con guiones |

- La regla única premiaba el *segundo* elemento también en el tramo de grupos, así que **cada fila
  se emparejaba con el grupo siguiente**: 34.22 (`35-40`) caía en el marcador nº41, 34.23 (`41-45`)
  en el nº47, 34.24 (`46-49`) en el nº50 y 34.25 (`50-52`) en el nº51. **Tres de las cuatro estaban
  ya CONFIRMADO** y una firmada a mano: el validador no puede verlo, porque el par PTS↔CST que
  recibe es coherente consigo mismo, y aquí además todo el saṃyutta repite la misma fórmula con los
  términos permutados, así que Gemini tampoco distingue.
- **Causa raíz de la invisibilidad**: `sn3_markers._clean` borraba los guiones, y el `--` es
  justamente lo que separa los dos regímenes. Ahora el registro conserva el nombre en bruto
  (`rec['raw']`).
- **Solución**: `sn34_series.py` — gramática `pyparsing` de la forma del nombre
  (`pair` / `trunc` / `plain`) y **dos analizadores**, `score_individual` y `score_grouped`, cada uno
  aplicado a su parte. El desempate definitivo del régimen de grupos **no es el nombre sino el
  número**: el subhead del CST declara su rango («46-49.») y el marcador PTS su nº corrido (46) —
  misma numeración en ambas ediciones, así que la cabeza del rango *debe* ser el nº del marcador.
- **Verificación independiente**: de las 16 firmas humanas de S iii, **15 coinciden ahora con la
  alineación calculada**, incluida `34.23`, que Jorge había firmado bien y el resolvedor tenía mal.
  La única discrepancia que queda, `23.24` (firma p198,25 vs marcador p199,16), es una **disputa de
  página**, que la calibración de líneas no toca por diseño.
  - Líneas recalibradas: **318/324 exactas (98%)**, 6 corregidas. Auditoría de inyectividad: **hueco
    0** en los cuatro volúmenes contrastados.
  - **S v**: 69 pares cambiaron y las asignaciones nuevas son **mejores** (`45.12 Dutiyavihāra`→
    `Vihāra2.`, `45.28 Samādhi`→`Samādhi.`, con los textos coincidiendo), pero al ceñirse el texto
    al marcador **cae la cobertura del gate local**: 72 desacuerdos son `gate=REJECT /
    gemini=APPROVE` con cobertura mediana 0.40 frente al umbral 0.55, calibrado sobre textos laxos.
    > **Decisión (Jorge, 2026-07-25): no reabrir.** Si el par ya está verificado y Gemini aprueba,
    > no tiene sentido re-revisarlo para llegar al mismo resultado. S v se queda en 610/610 y el
    > Excel no se toca; `reconcile_sn5.py --dry` confirma que no habría degradación (538 filas
    > reescribirían el mismo valor, 40 protegidas). El umbral del gate **no se recalibra**: se deja
    > documentado que en régimen de texto ceñido su cobertura baja, para no volver a tropezar.

### S v contrastado con su front matter (2026-07-25) — CERRADO

`pts_samyutta_v_layout.txt` (12 saṃyuttas XLV–LVI, 103 vaggas, 1208 suttas) nunca se había usado.
Contrastado ahora, **todo queda explicado**; el volumen no tenía ningún defecto de datos.

> ⚠️ El layout **no trae páginas de arranque**, solo vaggas y suttas. Una nota anterior decía que
> «las páginas de arranque salen correctas»: era circular, porque esas páginas las había tomado de
> mi propia segmentación. Las reales, leídas de los encabezados del texto, son
> 1, 63, 141, 193, 244, 249, 254, 294, 307, 311, 342, 414.

- **Vaggas: 103/103 exactos**, saṃyutta por saṃyutta (contados por las líneas `CHAPTER`).
- **`LVI Sacca = 181` es un error de OCR del fichero; son 131.** Lo prueba la aritmética de la
  propia tabla: 180+187+103+185+54+110+86+24+54+20+74+**131** = **1208**, el total impreso (con 181
  daría 1258). Y el texto numera hasta `131. (30) Pañcagati` (S v 477). El «3» se leyó como «8».
- **`LIV Ānāpāna` daba 33 en vez de 20 por un defecto de mi parser**, ya corregido
  (`_drop_paragraph_runs`): en S v 328, dentro del sutta 54.12 Kaṅkheyya, hay párrafos numerados con
  la misma forma que un marcador (`7 (1). Ekam idāham āvuso Mahānāma…`). En todo el volumen solo 9
  marcadores caen en la banda del margen (sangría 4–7) y **uno solo es genuino** — el rango peyyāla
  de S v 134, que lleva la fórmula de elisión `vitthāretabba` —, así que en esa banda se exige la
  fórmula. **Ninguna fila del Excel estaba asignada a los marcadores espurios**, así que el dato
  nunca estuvo contaminado; SN 54 mapea 1:1 (54.1→p311 L4 … 54.20→p340 L19).

Los cinco desvíos restantes son **irregularidades del propio impreso**, no del pipeline, y suman
exactamente la diferencia (1190 frente a 1208 = −18):

| saṃyutta | dif | causa |
|---|---:|---|
| XLV Magga | +1 | el nº **170 se imprime dos veces**: S v 57 `170. (10) Taṇhā (vivekaº)` y S v 58 `170. (11) Tasinā (Rāgavinayaº)` |
| XLVI Bojjhaṅga | −10 | **errata que Feer documenta** en su propia nota: S v 135 imprime `99--100` donde debía decir `99--110`, y por eso el saṃyutta cierra en `175` (S v 139) en vez de 185 |
| XLVII Satipaṭṭhāna | +1 | **rangos solapados** en S v 191: `83--93. (1--11)` y `93--102. (1--9)` comparten el 93 |
| XLVIII Indriya | −9 | los números **119–127 no llevan marcador** (elididos) |
| LI Iddhipāda | −1 | el número **78 no lleva marcador** |

**Conclusión: S v queda contrastado con el impreso** — vaggas exactos, recuento explicado hasta el
último número, y el inventario de marcadores corregido sin que cambie ninguna asignación (610/610
asignadas, hueco de inyectividad 0).

**Excel actualizado (2026-07-25).** `calibrate_sn5_lines.py` pasa a usar la misma asignación global
que el validador (antes repetía la cadena de heurísticas por fila, que no es inyectiva): **41 líneas
corregidas → 577/577 exactas**. Estado de las líneas en los cuatro volúmenes contrastados:

| | S i | S ii | S iii | S v |
|---|---|---|---|---|
| líneas exactas | 271/271 | 254/254 | 316/316 | 577/577 |
| sin nº de línea | 0 | 1 | 0 | 1 |

Las 2 filas sin línea (`S ii 15.18 Putta`, `S v 46.66 Uddhumātaka`) caen en el bucket de **página en
disputa** que la calibración no toca por diseño: la primera es miembro de un marcador de rango y en
la segunda el nombre del marcador no casa. No son un residuo del pipeline, sino la política de no
reescribir una página apoyándose solo en la línea.

### Fase 0 — prueba de aceptación común (sin API)

`audit_injectivity.py`: para un volumen dado, lista los marcadores compartidos y calcula el
**hueco de inyectividad** (filas − marcadores distintos usados), descontando los miembros legítimos
de un marcador de rango (su capacidad es el nº de suttas que cubre). **Criterio de cierre de
cualquier volumen: hueco = 0.** Se corre antes y después de cada fase.

### Fase 1 — resolvedor inyectivo y monótono (sin API)

Sustituir la resolución fila-a-fila por una **asignación por saṃyutta**: filas en orden canónico
contra marcadores en orden de lectura, maximizando la suma de las puntuaciones que ya existen
(nombre + proximidad al ancla) con dos restricciones:

- **monotonía** — si la fila *i* va al marcador *j*, la fila *i+1* va a *j* o posterior (las dos
  secuencias están ordenadas: es alineamiento de secuencias, DP O(m·n), exacto y barato);
- **capacidad** — un marcador de rango admite tantas filas como suttas cubre; uno individual, una.

Es la generalización de lo que ya funciona en S i (posicional) y en el Diṭṭhi (`ditthi_pairs`).

### Fase 2 — aplicar a S iii y S v, y re-validar

Re-validar **solo** las filas cuyo par cambie (≈40 en S iii, ≈36 en S v), descartando su veredicto
previo — nunca heredarlo. Recalibrar líneas. Cierre esperado: S iii 333/333 y S v revalidado.

### Fase 3 — S iv — ✅ **HECHA** (2026-07-25): 340/344, SN entero con el validador

Los 94 `HELMER_APPROVED` son del pase DeepSeek retirado: se re-validan las 344, no se hereda nada.

**Estructura (`samyutta-vol-IV-info.txt`, front matter de Feer).** 10 saṃyuttas XXXV-XLIV, 33
vaggos, 391 suttas. Las **10 cabeceras de libro caen en la página exacta** que declara Feer y **9
de los 10 recuentos son exactos**, con numeración contigua 1..N. El único desajuste, SN 39
Sāmaṇḍaka (PTS 2, Feer 16), lo explica él: *«All the MSS give only the beginning and the end»* —
se imprimen el nº1 y el nº16. (La tabla resumen de Feer suma 394, pero sus columnas dan 391 y la
prosa confirma 29 y 34: la tabla se equivoca.)

**Lo que cazó la auditoría previa a gastar API** — sin ella, ~120 filas se habrían cotejado contra
otro sutta:

1. **El `Sutta #` NO es la numeración del CST en SN 35.** Es la cuenta **reducida de Feer** (207)
   mientras `massive.tsv` usa la del CST. Los desfases (+17 en p29; +27/+37/+47 en pp. 151-155)
   caen donde Feer explica que comprimió: los 19 suttas de `Jātidhammādi…`+`Aniccādi…` que el Excel
   lleva como **2 filas**, y el **`satthi peyyala`**, donde «reduce» 60 suttantas a 20.
   → El lado CST se resuelve por **POSICIÓN**: los bloques de subhead del XML y las filas del Excel
   se corresponden **1:1 en los 10 saṃyuttas** (344=344) y la comprobación por nombre da **344/344**.
   `massive.tsv` queda sólo para la página de cotejo. Es la regla de siempre: la identidad de una
   fila la dan `Sutta Name` + `PTS Page`, no el `Sutta #`.
2. **Una gāthā tomada por sutta.** `13 Pittaṃ semhaṃ ca vāto ca` (S iv 231) es un verso numerado
   como párrafo; el alineador lo tomaba por marcador y desplazaba `36.22` en adelante. Lo descarta
   la **continuidad de la secuencia** (un nº de párrafo queda POR DEBAJO del esperado; una elisión
   salta hacia delante), que además preserva el `5 Daṭṭhabbena` (p207, marcador legítimo sin
   posición) y el `16 Dukkaram` (p262, salto de elisión de Sāmaṇḍaka).
3. **El `saṭṭhi-peyyāla` es un tercer régimen de marcador**: `(2) Chandena2`, con el **nº corrido
   elidido**. Exigir dígito inicial dejaba 12 filas sin marcador.
4. **Las capacidades se MIDEN en el texto, no se adivinan por el nombre.** Feer junta a veces dos
   suttas del CST bajo un marcador y el título no siempre lo dice: «Agayha» (S iv 126) imprime los
   dos Rūpārāma sin nombrar ninguno, mientras «Devadahakhaṇo» *parece* doble y no lo es — el Khaṇa
   del CST es el marcador siguiente (su texto es el del nº135 «Saṅgayha»). Contar raíces del nombre
   acertaba en tres casos y fallaba en dos; el solapamiento léxico acierta en los cinco.

**Resultado: 340 `VALIDADOR` + 4 `REVISAR`.** Las 4 a arbitraje son desacuerdos gate/Gemini con el
**nombre casado** y cobertura baja por elisión de un lado: `35.41 Anusayapahāna` (0.11),
`36.1 Samādhi` (0.33), `36.30 Suddhika` (0.12) y `37.14 Pañcavera` (0.33). Los `HELMER_*` de
`36.1` y `37.14` **se degradaron a PENDIENTE**: heredarlos habría dejado como CONFIRMADO justo lo
que el validador vigente rechaza. Líneas: 260/337 ya exactas, **77 corregidas**; 7 páginas en
disputa quedan a arbitraje (no se tocan).

**Gemini cazó un desfase real, no un falso negativo.** Rechazó `35.146/35.147` diciendo «PTS habla
de *dukkha* donde el CST habla de *anattā*»: el tramo Koṭṭhika iba corrido un puesto porque mi
estimación de capacidad había inflado el nº160 — en S iv 144 dos suttas casi idénticas del
Jīvakambavana empatan su máximo de solapamiento por 0.02 (0.65 frente a 0.63). De ahí la regla
definitiva: **la capacidad no se estima a priori, la demuestra el alineamiento**. Se resuelve con
la capacidad natural y sólo las filas que quedan huérfanas prueban que un encabezado cubre más de
uno. Los **tres** dobles reales de S iv quedan declarados uno a uno en `audit_injectivity.SN4_DOBLES`
(«Agayha» = los dos Rūpārāma; «Pubbeñāṇam»; «Suddhikaṃ nirāmisam»), porque son afirmaciones
filológicas y deben poder auditarse a mano.

**Estado del alineador:** 344/344 alineadas, **hueco de inyectividad 0**, página del marcador ≡
`cst_p_page` 343/344 (100 %), ordinal `paṭhama`/`dutiya` 52/53 (98 %), solapamiento léxico mediano
0.70 (sólo 6 filas < 0.30, y 5 de ellas con el nombre casado: la cobertura baja porque un lado
elide). Módulos nuevos: `sn4_markers.py` (gramática pyparsing, 3 regímenes), `sn4_names.py`
(Feer nombra con el término en instrumental y el ordinal como dígito volado), `validador_sn4.py`.

### Fase 4 — deuda de DN/MN — ✅ **HECHA** (verificado 2026-07-25)

Las 186 filas que venían del pase DeepSeek retirado **ya se re-validaron con el validador**:
`validador_dnmn.json` = 186 filas, **176 CONFIRMADO** (174 `VALIDADOR` + 2 `PTS_CROSSREF_SN`) y 10
desacuerdos que Jorge arbitró a mano → `VALIDADOR_HUMANO` (5 en DN, 5 en MN). En el Excel no queda
**ningún** `HELMER_*` en DN/MN. DN 34/34 y MN 152/152 descansan por tanto en la fuente vigente.

### Fase 5 — AN y KN (4.098 filas, el 67% de lo que queda)

Los XML VRI existen (`s04*`, `s05*`) y `massive.tsv` cubre 1.508 de AN y 2.054 de KN. **Falta la
verdad-terreno estructural**: los front matter por volumen (AN I–V; KN por obra), que en los cuatro
volúmenes de SN han sido lo que permite fijar el lado PTS sin conjeturas. Sin ellos no se empieza.

### Orden recomendado

**0 → 1 → 2 → 3 → 4 → 5.** Las fases 0–2 no gastan API salvo la re-validación de ~76 filas; la 3 y
la 4 son el grueso del coste; la 5 depende de que lleguen los OCR.
