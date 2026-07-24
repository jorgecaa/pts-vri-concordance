# Aṭṭhakathā — Extracción de Comentarios PTS

Extracción completa de los **58 volúmenes de Aṭṭhakathā** (comentarios del Tipiṭaka)
desde la base de datos `tipitaka.sqlite` (edición PTS/ROTA).

## 📦 Contenido

```
rotb_commentary/
├── index.json          ← Catálogo de los 58 libros
├── book_01.json        ← Samantapāsādikā (Vinaya-aṭṭhakathā)
├── book_02.json        ← Samantapāsādikā (cont.)
│   ...
├── book_08.json        ← Kaṅkhāvitaraṇī (Pātimokkha-aṭṭh.)
├── book_09.json        ← Sumaṅgala-Vilāsinī (Dīgha-aṭṭh.)
├── book_12.json        ← Papañcasūdanī (Majjhima-aṭṭh.)
├── book_17.json        ← Sāratthappakāsinī (Saṃyutta-aṭṭh.)
├── book_20.json        ← Manorathapūraṇī (Aṅguttara-aṭṭh.)
├── book_26.json        ← Dhammapada-aṭṭhakathā
├── book_47.json        ← Visuddhajanavilāsinī (Apadāna-aṭṭh.)
├── book_51.json        ← Sammohavinodanī (Vibhaṅga-aṭṭh.)
├── book_54.json        ← Nidānakathā (Jātaka-aṭṭh.)
│   ...
├── book_58.json        ← 713 páginas
│
├── book_*.tex          ← Fuentes LaTeX (XeLaTeX, Book Antiqua)
└── book_*.pdf          ← PDFs compilados
```

**58 libros · 16,634 páginas** de texto Pāli romanizado.

## 📄 Formato JSON

Cada archivo `book_NN.json` contiene:

```json
{
  "book_no": 9,
  "name": "Sumaṅgalavilāsinī I",
  "work": "Sumaṅgalavilāsinī",
  "sigla": "Sv",
  "vol": "I",
  "mula": "Dīghanikāya",
  "total_pages": 320,
  "pages": [
    {
      "page": 2,
      "head": "GENERAL INTRODUCTION.",
      "text": "... Vuttaṃ h' etaṃ Bhagavatā: “Yo vo Ānanda mayā1 dhammo...",
      "variants": [
        {"start": 10, "end": 33, "text": "vanappatijeṭṭharukkho"}
      ],
      "folios": [
        {"start": 520, "end": 527, "text": "[F.12]"}
      ],
      "apparatus": "1 So M.P.S. VI. 1; S.P. mayā Ānanda. 2 ...",
      "notes": {"1": "So M.P.S. VI. 1; S.P. mayā Ānanda.", "2": "..."}
    }
  ]
}
```

| Campo | Descripción |
|-------|-------------|
| `text` | Texto Pāli romanizado en Unicode. Conserva `{cursiva}`, `[F.N]`, `║N║` y los números de nota pegados a la palabra (`mayā1`). **Las palabras partidas por el guion de fin de renglón del impreso se rejuntan** (`sacchi-\nkatvā` → `sacchikatvā`). |
| `head` | Cornisa de página de la fuente. ⚠️ Transliteración corrupta (fuente legacy); **no se usa como título** (ver `name`/`work`). |
| `name` / `work` / `sigla` / `vol` / `mula` | Título canónico, sigla académica, volumen y texto mūla comentado (desde `book_meta.py`). |
| `variants` | Posiciones de variantes de manuscritos (cursivas en el impreso). |
| `folios` | Posiciones de marcadores de folio `[F.N]`. |
| `sections` | Posiciones de marcadores de sección `║N║`. |
| `apparatus` | Aparato crítico crudo (texto íntegro). |
| `notes` | Aparato **parseado** en `{nº_nota: texto}`, para enlazar cada nota a su lema. |

## 📐 Formato LaTeX

Los archivos `.tex` usan **XeLaTeX** para compilación nativa Unicode, con criterios
de edición filológica:

- **Cuerpo 11 pt, formato B5** (caja tipo libro, próxima al octavo PTS).
- Fuente: **Book Antiqua** → si no está, **TeX Gyre Pagella** (clon de Palatino,
  Unicode pāli completo) → Latin Modern como último recurso.
- **Sin partición automática** de palabras pāli (XeLaTeX usaría patrones ingleses);
  solo se corta en los guiones de compuesto ya presentes.
- **Versos (gāthā)** compuestos en entorno `verse` (conservan los pādas), no en prosa.
- **Aparato crítico enlazado**: cada nota va en un `\footnote[n]` anclado a su lema
  (no un volcado único por página). La numeración usa el **número original del
  aparato**, que **reinicia en 1 en cada página PTS** (no se acumula a lo largo del libro).
- **Siglas de manuscrito con sufijo en superíndice** (convención PTS): el sufijo es
  un **cluster de subediciones consonánticas** que se acumula —`Bm`→Bᵐ, `B2`→B²,
  `Ssp`→Sˢᵖ, `Scdg`→Sᶜᵈᵍ, `Scdgh`→Sᶜᵈᵍʰ, `Scgt`→Sᶜᵍᵗ—. Como ninguna palabra pāli
  es solo-consonantes, los clusters no chocan con palabras (`Sutta`, `Sum`, `Budv`)
  ni con vocales; solo se excluyen las refs de TEXTO consonánticas (`Dhs`, `Spk`,
  `Pts`, `Skt`, `Khp`…). El alfabeto `_SUB`, las bases `MS_BASES` y la lista
  `NON_SIGLA` están en `generate_tex.py` y son **revisables**.
- `\textit{...}` — cursivas de variantes `{...}`.
- `\textsuperscript{[F.N]}` / `\textsuperscript{\textbf{N}}` — folios y secciones.
- **Índice (ToC) desde los títulos PALI del cuerpo**, no de la cabecera. La cornisa
  del impreso (`head`: rótulos en inglés del editor, referencia `[D. I. 1.`) **no** es
  un título. Los títulos reales aparecen centrados en el texto y terminan en una
  palabra-tipo (`…-vaṇṇanā`, `[… vaṇṇanā]`, `N. …-vatthu`, `…niddeso`, `…vaggo`,
  `…kathā`) o en un colofón (`… niṭṭhitā/samattā`). Se detectan en todos los formatos
  (mayúscula, minúscula entre corchetes, numerado), se limpia el colofón y se
  excluyen portada/homenaje y el título de la obra.
- **Marcador de página PTS**: cada página del impreso PTS se marca en el texto con una
  **regla horizontal gris claro** y el número centrado (`── Sv I 121 ──`), para alinear
  con la edición original. La cornisa cita obra · sigla.
- **Niggahīta normalizado** a `ṃ` por defecto (norma moderna); usar `--diplomatic`
  para conservar la ortografía PTS antigua (m/n final).

### Compilación

```bash
xelatex book_09.tex
xelatex book_09.tex   # segunda pasada para el índice (ToC)
```

## 🔧 Scripts

| Script | Función |
|--------|---------|
| `book_meta.py` | Mapa canónico de los 58 libros (título, sigla, volumen, mūla). |
| `extract_commentary.py` | Extrae los JSON desde `tipitaka.sqlite` (dehyphenation + aparato parseado). |
| `generate_tex.py` | Genera los `.tex` desde los JSON. `--diplomatic` desactiva la normalización del niggahīta. |
| `compile_pdfs.py` | Compila todos los `.tex` a PDF (dos pasadas para el índice). |

### Regenerar todo

```bash
# 1. Extraer de la base de datos
python extract_commentary.py src/data/tipitaka.sqlite rotb_commentary

# 2. Generar LaTeX (añade --diplomatic para no normalizar el niggahīta)
python generate_tex.py

# 3. Compilar PDFs
python compile_pdfs.py rotb_commentary
```

## 📚 Correspondencia Tipiṭaka → Aṭṭhakathā

Fuente única de verdad: [`book_meta.py`](book_meta.py). Sigla académica entre paréntesis.

| Texto mūla | Aṭṭhakathā (sigla) | Libros ROTB |
|------------|--------------------|-------------|
| Vinaya | Samantapāsādikā (Sp) | 1–7 |
| Pātimokkha | Kaṅkhāvitaraṇī (Kkh) | 8 |
| Dīghanikāya | Sumaṅgalavilāsinī (Sv) | 9–11 |
| Majjhimanikāya | Papañcasūdanī (Ps) | 12–16 |
| Saṃyuttanikāya | Sāratthappakāsinī (Spk) | 17–19 |
| Aṅguttaranikāya | Manorathapūraṇī (Mp) | 20–24 |
| Khuddakapāṭha | Paramatthajotikā I (Pj I) | 25 |
| Dhammapada | Dhammapada-aṭṭhakathā (Dhp-a) | 26–29 |
| Udāna | Paramatthadīpanī (Ud-a) | 30 |
| Itivuttaka | Paramatthadīpanī (It-a) | 31–32 |
| Suttanipāta | Paramatthajotikā II (Pj II) | 33–34 |
| Vimānavatthu | Paramatthadīpanī (Vv-a) | 35 |
| Petavatthu | Paramatthadīpanī (Pv-a) | 36 |
| Theragāthā | Paramatthadīpanī (Th-a) | 37–39 |
| Therīgāthā | Paramatthadīpanī (Thī-a) | 40 |
| Niddesa | Saddhammapajjotikā (Nidd-a) | 41–43 |
| Paṭisambhidāmagga | Saddhammappakāsinī (Paṭis-a) | 44–46 |
| Apadāna | Visuddhajanavilāsinī (Ap-a) | 47 |
| Buddhavaṃsa | Madhuratthavilāsinī (Bv-a) | 48 |
| Cariyāpiṭaka | Paramatthadīpanī (Cp-a) | 49 |
| Dhammasaṅgaṇī | Atthasālinī (As) | 50 |
| Vibhaṅga | Sammohavinodanī (Vibh-a) | 51 |
| Dhātukathā…Paṭṭhāna | Pañcappakaraṇaṭṭhakathā (Pañc-a) | 52–56 |
| — | Milindapañha (Mil) | 57 |
| — | Visuddhimagga (Vism) | 58 |

> Los vols. **52–58 se identificaron por el texto inicial** de cada libro (no por el
> `head`, corrupto); revísalos contra los impresos PTS si tienes acceso. El set **no
> incluye** la Jātaka-aṭṭhakathā.

## ⚠️ Notas sobre el formato

- Los `{...}` marcan **variantes de manuscritos** que en el impreso PTS van en cursiva. Se preservan como `{texto}` en el campo `text` y como posiciones `start/end` en el array `variants`.
- Las **cursivas de lemas** (palabras que se están glosando, ej. *Ibbhā ti gahapatikā*) no se preservaron en la digitalización original — solo existen en el impreso/PDF.
- El texto se extrae de la columna `unitext` de la tabla `pages` (edición `atthakatha`), que
  está en **UTF-8 plano**; los diacríticos Pāli (ā ī ū ṅ ñ ṭ ḍ ṇ ḷ ṃ) son Unicode nativo. (En el
  esquema FoxPro original este campo estaba en Base64(BOM+UTF-8); el `decode_unitext` heredado del
  código lo tolera pero ya no es necesario. Esquema: `src/data/DATABASE.md`.)
- El aparato crítico (`apparatus`) contiene notas de Buddhaghosa y variantes entre manuscritos (Cb=Cambridge, Bm=Burmese, S=Sinhala, etc.).

## ⚠️ Limitaciones conocidas

- **Los títulos salen del CUERPO, no de la cabecera**: el `head` (running header del
  impreso) trae los rótulos en inglés del editor y la referencia `[D. I. 1.` (el `]`
  tiene sentido filológico, marca el pasaje comentado), pero **no** es un título.
  Los títulos pali genuinos van centrados en el texto; se detectan por su palabra-tipo
  final (`is_title_line` en `generate_tex.py`). Lista de palabras-tipo (`_TITLE_KW`) y
  colofones (`_COLOPHON`) **revisables**. Un libro cuyo formato de título no encaje
  podría quedar con pocas secciones.
- **Detección de títulos heurística**: distingue título de verso/cornisa por
  centrado + palabra-tipo. Puede colarse alguna línea de cuerpo que termine en
  palabra-tipo, o quedar el prefijo genitivo del colofón (`Mahāniddesaṭṭhakathāya …`).
- **Detección de versos heurística**: se basa en la sangría de la fuente (líneas
  con ≥3 espacios = gāthā). Una glosa en prosa muy sangrada puede clasificarse como
  verso; un único renglón largo se reclasifica automáticamente como prosa.
- **Notas de rango a caballo entre páginas**: una nota cuyo span (`³…³`) cruza el
  límite de página puede dejar un dígito suelto aislado (caso poco frecuente).
- **Normalización del niggahīta**: por defecto se convierte el `m`/`n` final a `ṃ`
  (norma moderna). Es seguro en pāli (toda palabra termina en vocal o `ṃ`) salvo
  ante apóstrofo de elisión, que se respeta. Usa `--diplomatic` para desactivarla.

## 📖 Fuente original

Base de datos: `src/data/tipitaka.sqlite`  
Edición: **Pali Text Society** (PTS) · **Royal Thai Tipiṭaka** (ROTA/ROTB)  
Digitalización: Dhammakaya Foundation / VFP9 → SQLite
