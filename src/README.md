# Tipitaka PTS Browser — aplicación (`src/`)

Lector de escritorio del Tipiṭaka Pāli alineado a la paginación de la **Pali Text Society
(PTS)**, con búsqueda, aparato crítico y un panel de diccionario DPD embebido.

> Para el panorama del repositorio completo (que incluye también el *pipeline* de concordancia
> y de extracción de comentarios en la raíz), lee **[`../CLAUDE.md`](../CLAUDE.md)**.

## Ejecutar

```bash
python3 run.py            # GUI (por defecto)
python3 run.py check      # verifica dependencias
python3 run.py test       # ejecuta pytest sobre tests/
```

También desde la raíz del repo con `./AppRun` (usa `./venv` si existe, si no `python3`).

Dependencias principales (ver `requirements.txt`): **PyQt6** (+ QtWebEngine), **rapidfuzz**,
**charset-normalizer**, **python-Levenshtein**. `xelatex` es opcional (solo para PDFs del pipeline
de comentarios).

## Arquitectura

- **Entrada / ventana:** `run.py` → `main/extracted_appimage_gui.py::TipitakaMainWindow`.
  Es **PyQt6 Widgets** (no QML — la interfaz QML fue abandonada; queda solo `qml/_deprecated/`).
  El panel del diccionario DPD usa `QWebEngineView`, por eso `run.py` activa
  `AA_ShareOpenGLContexts` **antes** de crear el `QApplication`.
- **Capa de backend** (`main/`, reutilizable e independiente de la UI):
  `database.py`, `search.py` / `enhanced_search.py` / `robust_search.py`,
  `dictionary.py` / `stardict_dictionary.py`, `citation_parser.py`, `apparatus.py`,
  `rota_edition.py` / `rota_files.py`, `export.py`, `i18n.py`, `ui_widgets.py`,
  `ui_integration.py`.

## Datos (`data/`)

- **`tipitaka.sqlite`** — corpus PTS. Tablas reales: `pages`, `footnotes`, `contents`, `toc`,
  `nav_tree`, `books`, `editions`, `dict_pts`, `dict_pali_english`, `pali_fts` (FTS5), `word_*`,
  `translation_*`, `pts_*`. La columna `edition` vale `'mula'` (canon) o `'atthakatha'`
  (comentario). **`unitext` es UTF-8 plano** aquí y **`head` no es fiable** (validar por el cuerpo).
  Referencia completa y autoritativa del esquema: **[`data/DATABASE.md`](data/DATABASE.md)**.
  ⚠️ El label `'ROTA'` heredado significa **PTS**, no "Royal Thai".
- **`dictionaries/`** — StarDict CPD (`cpd.*`), PTSPED-2021 (`PTSPED-2021.*`) y `critical.db`.
- Scripts de extracción/derivación de datos: `data/extract_*.py`, `data/query_pts.py`.

## Tests

```bash
python3 -m pytest tests/ -v            # suite
python3 -m pytest tests/test_database.py -v
python3 test_integration.py            # scripts de integración sueltos (test_*.py en src/)
```

---

La hoja de ruta de UX de la GUI (P0 hecho; P1/P2 pendientes) está en
[`docs/PLAN_MEJORA_UX.md`](docs/PLAN_MEJORA_UX.md).

Los documentos históricos de la fase de reconstrucción del código (análisis, plan, bugs,
inventario, guía de usuario antigua — todos describían la interfaz QML ya abandonada) se
movieron a `../archive/docs-reconstruccion/`.
