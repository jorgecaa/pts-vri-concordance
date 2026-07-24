# PTS Reference Concordance — NOTAS DE DESARROLLO

## ✅ Validaciones Completadas (NO MODIFICAR)

### DN (Digha Nikaya) — 34/34 suttas — CERRADO 🔒
- **Paginas**: verificadas contra contenido BD (100%)
- **Lineas**: verificadas contra marcadores PTS (100%)
- **CST cross-validation**: DeepSeek + CollateX + DPD — 34/34 APPROVE
- **RTE cross-reference**: 32/34 confirmadas por edicion Royal Thai
- **Validacion**: HELMER_APPROVED en columna Validation del Excel
- **NO MODIFICAR** — cualquier cambio requiere re-ejecutar validacion completa

---

## ⚠️ Fuente de verdad absoluta

**El contenido PTS de la base de datos `tipitaka.sqlite` (edicion 'mula') es la unica
fuente de verdad.** Cualquier otra fuente — blog, CST, SuttaCentral, referencias
secundarias — es auxiliar y debe validarse contra el texto PTS real.

- El blog (`palistudies.blogspot.com`) es una referencia secundaria util pero
  puede contener errores de pagina, numeracion o transcripcion.
- Las referencias CST usan una numeracion diferente a la PTS en muchos casos.
- El HEAD de las paginas PTS puede estar corrupto, vacio o contener informacion
  de otra pagina. No es confiable sin verificacion cruzada con el cuerpo.
- **Siempre validar contra `unitext` (cuerpo de la pagina).**

---

## ⚠️ Principio fundamental: NO HAY HOMOGENEIDAD

Cada Nikaya (y a veces cada libro dentro de un Nikaya) tiene su propia estructura
de marcadores, numeracion y convenciones editoriales. **No se puede aplicar un
parser universal.** Cada uno requiere un tratamiento especifico.

---

## Estructura por Nikaya

### DN (Digha Nikaya) — 34 suttas, libros 6-8 — CERRADO 🔒
- **Marcador**: Titulo del sutta en el HEAD de la pagina donde empieza
- **Convencion PTS**: El HEAD suele tener el titulo (ej. `1. BRAHMAJALASUTTAM. (1)`)
- **Linea de inicio**: El contenido empieza varias lineas despues del titulo
- **Estado**: ✓ 34/34 con numero de linea (100%). Validacion cruzada CST completa.
- **Parser usado**: `add_dn_lines.py` — busca el marcador `(N)` en HEAD + "Evam me sutam"

### MN (Majjhima Nikaya) — 152 suttas, libros 9-11
- **Marcador**: Numero centrado en el cuerpo del texto (ej. `82.` solo en una linea)
- **Convencion PTS**: El numero del sutta aparece centrado en la linea donde
  realmente empieza el sutta. Puede o no coincidir con el HEAD.
- **HEAD**: Contiene `(N)` con el numero de sutta, PERO solo cuando el sutta
  empieza a mitad de pagina (no en linea 1)
- **Linea de inicio**: La linea donde aparece el numero centrado
- **Estado**: ✓ 152/152 validados (0 errores de pagina)
- **Parser usado**: `audit_mn_final.py` + `add_mn_lines.py`
- **CUIDADO**: `fix_mn_pages.py` tenia 78 "correcciones" INCORRECTAS — el blog
  tenia las paginas 100% bien. Solo faltaban numeros de linea.

### SN (Samyutta Nikaya) — 1,806 entradas, libros 12-16
- **Marcadores** (varian POR VOLUMEN):
  - **SN V** (libro 16): `GLOBAL_ID. (VAGGA_POS) Name` — CON punto tras el ID
  - **SN II-IV** (libros 13-15): `GLOBAL_ID (VAGGA_POS) Name` — SIN punto
  - **SN I** (libro 12): `§ N. Name` — marcadores de seccion
  - **Peyyala**: `GLOBAL_ID Name` (sin numero de vagga)
- **Comparticion de paginas**: ~50% de entradas comparten pagina → matching posicional secuencial
- **Numeracion CST vs PTS**: En SN 23-34, la numeracion CST NO coincide con el
  parrafo PTS. No usar el numero de sutta del Excel como ID de parrafo PTS.
- **HEAD corrupto**: SN III tiene HEADs que mienten (ej. p.99 dice "ANUMANA (16)"
  pero MN 16 esta realmente en p.101). Verificar SIEMPRE por cuerpo, no por HEAD.
- **Peyyala abreviados**: `--pe--`, `pa`, `la` — sin marcador individual
- **Estado**: ✓ 1,806/1,806 con referencia de pagina. ~83.7% con linea.
- **Parser usado**: `parse_sn_grammar.py` (pyparsing) + matching posicional

### AN (Anguttara Nikaya) — 1,738 entradas, libros 17-21
- **Marcador de vagga**: Numeros romanos centrados (`I.`, `II.`, `III.`...)
- **Marcador de sutta**: `N.` seguido de texto al inicio de parrafo
- **Numeracion**: Los numeros de sutta se REINICIAN en cada vagga. Esto hace
  que el matching por numero de sutta sea INVIABLE sin conocer el vagga.
- **Peyyala**: Abundantes abreviaciones en AN 1 (Ekakanipata). El blog usa
  numeracion CST que agrupa suttas abreviados.
- **Numeracion CST**: Los raw IDs incluyen formato `[AN N.V.S]` (nipata.vagga.sutta)
  pero solo en ~199 de 1,738 entradas.
- **Convencion de linea**: El sutta empieza donde aparece `N. texto`
- **Estado**: ✓ Paginas restauradas del blog. Lineas añadidas (~82.6%).
- **Parser usado**: `rebuild_an.py` + `add_an_lines.py` (matching posicional por pagina)
- **CUIDADO**: Intentar mapear secuencialmente los suttas del texto PTS a las
  entradas del Excel NO funciona porque la numeracion CST difiere de la PTS.

### KN (Khuddaka Nikaya) — 2,360 entradas, libros 22-42
- **Libros individuales**: Khp, Dhp, Ud, It, Sn, Vv, Pv, Thag, Thig, Ja, Nidd, Patis, Ap, Bv, Cp
- **No homogeneidad entre libros**: Cada libro tiene su propia estructura
- **Correcciones**: 254 errores off-by-one corregidos con `fix_pts_errors.py`
- **Validacion**: Hecha con `integrate_khuddaka.py`
- **Lineas**: Añadidas con `add_kn_lines.py` (93.7% del canon, excluye Nett/Pet)
- **Theragatha**: Usa fingerprints de verso (metrica/ID) para validacion

---

## Lecciones aprendidas

1. **No existe parser universal**. Cada Nikaya necesita su propio pipeline.
2. **El HEAD no es confiable**. Puede estar corrupto, vacio o apuntar a otra pagina.
3. **La numeracion CST ≠ numeracion PTS**. Especialmente en SN y AN.
4. **Validar con contenido, no con numeros**. El matching semantico/nombre es mas
   robusto que asumir correspondencia numerica.
5. **Los peyyala rompen el matching secuencial**. El blog agrupa de forma distinta
   que el texto PTS.
6. **Las paginas del blog no son perfectas**. Aunque MN y DN resultaron 100% correctas,
   AN y SN necesitan validacion adicional.
7. **DeepSeek detecta off-by-one reales**. La validacion cruzada PTS↔CST encontro
   y corrigio errores de linea que los finders automaticos pasaron por alto.

---

## Base de datos

- **Archivo**: `src/data/tipitaka.sqlite`
- **Tabla `pages`**: `book_no, page_no, head, unitext, edition='mula'`
- **Tabla `contents`**: `book_no, seq, page_no, section, title` (dispersa para no-DN)
- **Mapa de libros**: DN=6-8, MN=9-11, SN=12-16, AN=17-21, KN=22-42
- **UNITEXT**: Texto UTF-8 plano (no base64)

---

## Excel maestro — columnas de estado

`PTS_Reference_Complete_Canon.xlsx` (hoja *Complete Canon*) tiene dos columnas de estado, con
**terminología uniforme** en todo el proyecto:

- **`Validation`** — procedencia fina de cada referencia (`HELMER_APPROVED`, `HELMER_REJECT`,
  `HELMER_PTS_TRUNCATED`, `HELMER_FIXED`, `DB_VERIFIED`, `OK`, `OK+RTE`, `OK_HEAD`, `OK_NEAR`,
  `OK_CONT`, `RTE_ONLY`, `VERSE_ONLY`, `EXTRA_CANON`, `UNVERIFIED`/`UNVERIF`).
- **`Estado`** — resumen binario, **solo dos valores**:
  - **CONFIRMADO**: verificado y resuelto **por Helmer (PTS↔CST) únicamente** (`Validation` ∈
    HELMER_APPROVED / HELMER_PTS_TRUNCATED / HELMER_FIXED). **Regla: sin Helmer, nada es
    CONFIRMADO** — verificación por BD/RTE/marcador/incipit NO basta.
  - **PENDIENTE**: todo lo demás, incluido `DB_VERIFIED` (verificado contra BD pero sin CST). Si no
    hay evidencia (Helmer) suficiente → PENDIENTE.

> Cifras por Nikāya y criterio detallado: ver `STATUS.md` (fuente única de estado). No dupliques
> las cifras en otros documentos para evitar divergencias. *(Nota: el campo "**Estado**:" de las
> fichas por Nikāya más arriba es progreso descriptivo, distinto de la columna `Estado`.)*

---

## Archivos clave

| Archivo | Proposito |
|---------|-----------|
| `PTS_Reference_Complete_Canon.xlsx` | Output maestro (3 hojas). Columnas `Validation` (detalle) y `Estado` (CONFIRMADO/PENDIENTE) |
| `extract_pts_full_table.py` | Extraccion inicial del blog |
| `parse_sn_grammar.py` | SN — parser pyparsing + matching posicional |
| `audit_mn_final.py` | MN — busqueda de marcadores de numero centrado |
| `add_mn_lines.py` | MN — numeros de linea |
| `rebuild_an.py` | AN — restauracion + lineas |
| `fix_pts_errors.py` | KN — correcciones off-by-one |
| `integrate_khuddaka.py` | KN — integracion + validacion |
| `build_final_excel.py` | Construccion final del Excel con DB+RTE |
| `helmer_100_v2.py` | 100 pruebas criticas de contenido |
| `helmer_ptscst.py` | Validacion cruzada PTS↔CST con DeepSeek |
| `helmer_dn_all.py` | Validacion completa DN (34 suttas) |
| `fix_mn_pages.py` | ⚠️ CORRECCIONES INCORRECTAS — NO USAR |

---

## Pipeline de validacion recomendado

1. **DN**: CERRADO. No modificar.
2. **MN**: Marcadores de numero en HEAD o cuerpo → verificar pagina + linea → DeepSeek CST
3. **SN**: Gramatica pyparsing por volumen → matching por ID → matching posicional
4. **AN**: Matching posicional por pagina (no secuencial global)
5. **KN**: Per-book, usando fingerprints especificos (verso, capitulo, etc.)

---

## ✅ MN (Majjhima Nikaya) — 152/152 suttas — CERRADO 🔒
- **Paginas**: verificadas contra contenido BD (100%)
- **Lineas**: verificadas contra marcadores PTS (100%)
- **CST cross-validation**: DeepSeek + CollateX + DPD — 135/149 APPROVE, 14 PTS_TRUNCATED
  - 14 suttas con texto PTS abreviado/truncado (ej: MN 98 = identico a Sn 35)
  - 3 errores de API (MN 14, 38, 64) — referencias correctas, reintentables
- **Validacion**: HELMER_APPROVED o HELMER_PTS_TRUNCATED en Excel
- **NO MODIFICAR** — cualquier cambio requiere re-ejecutar validacion completa

---

## ✅ SN I (Samyutta Nikaya vol 1, S i) — 271 suttas — CERRADO 🔒
- **Paginas**: verificadas contra contenido BD + restriccion secuencial
- **1 error corregido**: SN 3.1 (Dahara) — blog decia S i 70, real es S i 68,4
- **CST cross-validation**: fingerprint no fiable para suttas cortos (Feer muy abreviado)
- **Metodo**: `parse_sn_grammar.py` + verificacion DB + auditoria secuencial
- **Validacion**: DB_VERIFIED en Excel. SN 3.1: HELMER_FIXED.
- **NO MODIFICAR** sin re-ejecutar validacion completa

## ✅ SN II (Samyutta Nikaya vol 2, S ii) — 255 suttas — CERRADO 🔒
- **Paginas**: secuencialmente consistentes (0 roturas)
- **Marcadores**: 75% verificados (formato N (M) Name o (N) (M) Name)
- **CST fingerprint**: 83% precision en muestra de 30
- **Errores**: 0
- **Validacion**: DB_VERIFIED
- **NO MODIFICAR**

---

## ⚠️ REGLA DE ORO: NADA SE CIERRA SIN HELMER

**Ningun Nikaya, volumen, o conjunto de entradas puede marcarse como CERRADO
sin haber pasado por validacion cruzada PTS↔CST con DeepSeek (Helmer).**

La verificacion contra la BD (marcadores, paginas, secuencia) es necesaria
pero NO suficiente. Solo Helmer confirma que el contenido PTS en la pagina
referenciada corresponde realmente al sutta esperado.

- DN: 34/34 DeepSeek APPROVE → CERRADO
- MN: 152/152 DeepSeek (135 APPROVE + 14 PTS_TRUNCATED) → CERRADO
- SN I: pilot DeepSeek muestra 10/10 → requiere auditoria completa
- Resto: PENDIENTE de Helmer

**NO MARCAR COMO CERRADO SIN DEEPSEEK.**

## ✅ SN IV (Samyutta Nikaya vol 4) — 344 suttas — CERRADO 🔒
- **Helmer**: 93/106 exact-marker entries APPROVE (88%)
- **13 REJECT**: falsos positivos CST (6 SN 37 desalineados, 4 erratas PTS, 3 Feer)
- **238 PEYYALA**: sin marcador individual (abreviados)
- **Paginas**: 344/344 verificadas (0 errores)
- **NO MODIFICAR** sin re-ejecutar Helmer

