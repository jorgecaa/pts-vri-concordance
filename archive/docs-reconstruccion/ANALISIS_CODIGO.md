# Análisis del Código Base - Tipitaka PTS Browser v1.0.0

## 1. Resumen Ejecutivo

**Aplicación:** Tipitaka PTS Browser  
**Versión:** 1.0.0  
**Fecha de análisis:** [Fecha actual]  
**Tecnologías principales:** Python 3.14, PyQt6, QML, SQLite  
**Estructura:** Monolítica con alto acoplamiento

## 2. Estructura del Proyecto

### 2.1. Directorios y Archivos Clave
```
squashfs-root/
├── src/
│   ├── main/__init__.py          # TODO EL CÓDIGO PRINCIPAL (500+ líneas)
│   ├── qml/                      # Interfaz QML
│   │   ├── MainWindow.qml        # Ventana principal (~1KB visible)
│   │   ├── SettingsWindow.qml    # Ventana de configuración
│   │   └── VariantPopup.qml      # Popup de variantes
│   ├── data/                     # Datos de la aplicación
│   │   ├── tipitaka.sqlite       # Base de datos principal
│   │   ├── edition_conversions.json
│   │   ├── matn_relations.json
│   │   └── philological_notes.json
│   └── docs/                     # Documentación/PDFs
├── usr/_internal/               # Dependencias empaquetadas
└── AppRun                       # Script de lanzamiento AppImage
```

### 2.2. Dependencias (requirements.txt)
```python
# Core
PyQt6>=6.5.0
PyQt6-Qt6>=6.5.0
PyQt6-sip>=13.5.0

# Data processing
pandas>=2.0.0
numpy>=1.24.0

# Text processing
rapidfuzz>=3.0.0
python-Levenshtein>=0.21.0
charset-normalizer>=3.0.0

# Fonts
royalthai>=0.1.0  # Soporte para fuentes Thai/Pali

# Utilities
setuptools>=65.0.0
wcwidth>=0.2.0
```

## 3. Análisis del Módulo Principal (`main/__init__.py`)

### 3.1. Clases y Estructura

#### Clase `TipitakaBrowser` (líneas 30-250)
**Responsabilidades mezcladas:**
- Gestión de datos (base de datos, JSON)
- Lógica de negocio (búsqueda, diccionario)
- Estado de aplicación (configuración, marcadores)
- Interfaz con QML (señales PyQt)

**Métodos principales:**
```python
# Inicialización y configuración
__init__(data_dir=None)          # Constructor con setup de directorios
_setup_directories(data_dir)     # Configura rutas de datos
_load_data()                     # Carga JSONs y conecta a DB

# Operaciones con textos
get_text(text_id, edition=None)  # Obtiene texto por ID y edición
search_texts(query, limit=50)    # Búsqueda básica con SQL LIKE
get_available_editions(text_id)  # Ediciones disponibles para un texto

# Diccionario
lookup_dictionary(word)          # Búsqueda en diccionario (placeholder)

# Gestión de estado
add_bookmark(text_id, position, note)  # Añade marcador
save_settings(settings)          # Guarda configuración
load_settings()                  # Carga configuración (defaults si no existe)
```

#### Funciones de entrada (líneas 250-400)
```python
main()                           # Punto de entrada principal
run_gui(app)                     # Inicia interfaz gráfica (PyQt6 + QML)
run_cli(app)                     # Modo línea de comandos interactivo
```

### 3.2. Patrones y Anti-patrones Identificados

**Problemas de diseño:**
1. **Clase Dios:** `TipitakaBrowser` hace demasiado
2. **Acoplamiento alto:** UI, datos y lógica mezclados
3. **Gestión de errores básica:** try/except genéricos
4. **Configuración ad-hoc:** Sin sistema de logging
5. **Patrón Singleton implícito:** Solo una instancia de aplicación

**Código espagueti:**
- Manejo de base de datos inline (sin abstracción)
- Lógica de búsqueda mezclada con UI
- Señales PyQt mezcladas con lógica de negocio

### 3.3. Interacción con QML

**Señales definidas (líneas 20-27):**
```python
textLoaded = pyqtSignal(str, str)           # text_id, text_content
searchResultsReady = pyqtSignal(list)
dictionaryLookupReady = pyqtSignal(dict)
settingsChanged = pyqtSignal(dict)
```

**Integración QML (líneas 280-310):**
```python
# Exposición del objeto Python a QML
context.setContextProperty("tipitakaBrowser", app)
```

## 4. Análisis de Archivos QML

### 4.1. `MainWindow.qml` (primeras líneas visibles)
**Estructura básica:**
```qml
ApplicationWindow {
    id: mainWindow
    title: qsTr("Tipitaka PTS Browser")
    width: 1200
    height: 800
    
    // Propiedades bindeadas a Python
    property var tipitakaBrowser
    property string currentTextId: ""
    property string currentTextContent: ""
    property string currentEdition: "PTS"
    property var searchResults: []
    property var bookmarks: []
    property var settings: ({})
    property bool isLoading: false
}
```

**Problemas identificados:**
1. **Monolítico:** Todo en un archivo
2. **Sin componentes:** Falta reutilización
3. **Binding directo:** Sin ViewModels intermediarios
4. **Estilos inline:** Sin sistema de temas

### 4.2. `SettingsWindow.qml` y `VariantPopup.qml`
- Ventanas modales básicas
- Interacción simple con propiedades Python
- Sin validación de entrada

## 5. Sistema de Datos

### 5.1. Base de Datos SQLite (`tipitaka.sqlite`)
**Análisis detallado (REVISADO CON DATABASE.md):**
- **Total tablas:** 45 tablas + 4 vistas
- **Tamaño:** ~100MB+ (textos Pali completos + variantes)
- **Estructura compleja:** Sistema de ediciones y alineaciones
- **INFORMACIÓN CRÍTICA DESCUBIERTA:** Los nombres de tabla en código son diferentes a los reales

**CORRECCIÓN DE NOMBRES DE TABLAS (según DATABASE.md):**
- `RoyalThai__palipg` → **`Dbf1__palipg`** (15,561 filas) - Textos Pali principales
- `RoyalThai__book` → **`Dbf1__book`** (53 filas) - Metadatos de libros
- `RoyalThai__wordat` → **`Dbf1__wordat`** (2,630,606 filas) - Índice de palabras
- `RoyalThai__word` → **`Dbf1__word`** (199,998 filas) - Diccionario de palabras
- `RoyalThai__wordbook` → **`Dbf1__wordbook`** (443,366 filas) - Frecuencia por libro
- `RoyalThai__footpg` → **`Dbf1__footpg`** (12,428 filas) - Apparatus criticus
- `PTS__dicdata` → **`Dbf__dicdata`** (16,262 filas) - Diccionario bilingüe
- `PTS__Dict_PTS` → **`Dbf__Dict_PTS`** (16,232 filas) - Diccionario PTS

**Tablas principales identificadas (nombres corregidos):**
1. **`edition`** (5 filas) - Catálogo de ediciones:
   - `ROYALTHAI` - Royal Thai Tipitaka (Thai/Romanized)
   - `PTS` - Pali Text Society (Romanized) 
   - `CHA` - Chaṭṭhasaṅgīti Tipiṭaka (6th Council, Be)
   - `Ce` - Buddha Jayanti Tripitaka (Sinhala/Romanized)
   - `CeBa` - Variantes sīmu7 alineadas contra Ce

2. **Tablas de contenido por edición:**
   - **`Dbf1__palipg`** (15,561 filas) - **TEXTOS PRINCIPALES PALI**
   - `PTS__contents` (0 filas) - Contenidos PTS (vacía en esta copia)
   - **`Dbf__dicdata`** (16,262 filas) - Datos de diccionario PTS
   - **`Dbf__Dict_PTS`** (16,232 filas) - Diccionario PTS

3. **Sistema de alineación y variantes:**
   - `edition_segment` (0 filas) - Segmentos de edición
   - `segment_alignment` - Alineación entre segmentos
   - `variant_reading` - Variantes de lectura
   - `ce_sutta_variant` (38,933 filas) - Variantes Ce vs PTS
   - `dpr_variant` (16,255 filas) - Variantes DPR

4. **Índices y búsqueda:**
   - **`Dbf1__wordat`** (2,630,606 filas) - **ÍNDICE PRINCIPAL DE PALABRAS**
   - **`Dbf1__wordbook`** (443,366 filas) - Palabras por libro
   - **`Dbf1__word`** (199,998 filas) - Diccionario de palabras

5. **Metadatos y estructura:**
   - **`Dbf1__book`** - Metadatos de libros (53 libros)
   - `canonical_passage` - Pasajes canónicos
   - `dpr_hierarchy_para` (168,671 filas) - Jerarquía DPR

**INFORMACIÓN CRÍTICA SOBRE ENCODING (de DATABASE.md):**
1. **`UNITEXT`** - Texto principal: `Base64(BOM + UTF-8-bytes)` donde BOM = `0xEF 0xBB 0xBF`
2. **`ENCPALI`** - Encoding legacy PUA (Private Use Area) - **NO USAR**
3. **`HEAD`** - Texto plano UTF-8 (no Base64)
4. **Función de decodificación requerida:** Ver `query_pts.py` para implementación correcta

**Problemas identificados (ACTUALIZADO):**
1. **Consulta incorrecta en código:** La tabla `texts` NO EXISTE en la base de datos
2. **Nombres de tabla incorrectos:** Código usa `RoyalThai__*` pero tablas reales son `Dbf1__*`
3. **Encoding no decodificado:** Textos en `UNITEXT` necesitan decodificación Base64 + BOM
4. **Estructura real vs código:** El código asume estructura simple que no coincide con DB real

**Consultas reales necesarias (CORREGIDAS):**
```sql
-- Para obtener texto Royal Thai (CORRECTO):
SELECT BOOKNUM, RPAGENUM, HEAD, UNITEXT 
FROM Dbf1__palipg WHERE BOOKNUM = ? AND RPAGENUM = ? AND _deleted = 0

-- Para búsqueda en textos (usando índice):
SELECT DISTINCT w.BOOK, w.PAGE, p.HEAD as title,
       substr(p.UNITEXT, 1, 500) as preview
FROM Dbf1__wordat w
JOIN Dbf1__palipg p ON w.BOOK = p.BOOK AND w.PAGE = p.PAGE
WHERE w.WORD LIKE '%' || ? || '%' AND p._deleted = 0
LIMIT ?
```

### 5.2. Archivos JSON de Configuración

#### `edition_conversions.json`
```json
{
  "books": {
    "dn1": {
      "available_editions": ["PTS", "MYANMAR", "VRI"],
      "conversions": {...}
    }
  }
}
```

#### `matn_relations.json`
- Relaciones entre textos (referencias cruzadas)
- Estructura jerárquica

#### `philological_notes.json`
- Notas académicas sobre textos
- Metadatos filológicos

### 5.3. Archivos CSV
- `reference_related_my.csv` - Referencias en edición Myanmar
- `reference_related_ro_pts.csv` - Referencias en edición PTS

## 6. Flujos de Usuario

### 6.1. Modo GUI
1. **Inicio:** `main()` → `run_gui(app)`
2. **Carga QML:** `QQmlApplicationEngine` carga `MainWindow.qml`
3. **Binding:** Propiedades QML bindeadas a `tipitakaBrowser`
4. **Interacción:** Señales PyQt comunican cambios

### 6.2. Modo CLI
1. **Inicio:** `main()` → `run_cli(app)` (si PyQt6 no disponible)
2. **Loop interactivo:** Comandos básicos (search, get, editions, dict, exit)
3. **Operaciones:** Llamadas directas a métodos de `TipitakaBrowser`

## 7. Problemas Críticos Identificados

### 7.1. Arquitecturales
1. **Monolito:** Todo en `__init__.py`
2. **Acoplamiento:** Base de datos, UI y lógica mezclados
3. **Sin testing:** No hay pruebas automatizadas
4. **Gestión de estado primitiva:** Variables de instancia como estado global

### 7.2. De Código
1. **Type hints básicos:** Solo en firmas principales
2. **Manejo de errores:** try/except genéricos
3. **Sin logging:** print() statements para debugging
4. **Configuración hardcodeada:** Rutas y defaults inline

### 7.3. De UI/UX
1. **QML monolítico:** Sin componentes reutilizables
2. **Sin temas:** Estilos inline
3. **Accesibilidad limitada:** Sin roles ARIA o soporte screen readers
4. **Responsividad básica:** Tamaños fijos

### 7.4. De Datos
1. **Esquema no documentado:** Estructura de DB desconocida
2. **Sin migraciones:** Cambios de esquema difíciles
3. **Búsqueda básica:** Solo SQL LIKE
4. **Diccionario placeholder:** Funcionalidad mínima

## 8. Funcionalidades Existentes

### 8.1. Completamente Implementadas
- ✅ Interfaz gráfica (QML) y línea de comandos
- ✅ Gestión básica de configuración
- ✅ Sistema de marcadores (en memoria)

### 8.2. Parcialmente Implementadas (con problemas CRÍTICOS)
- ⚠️ Carga de textos Pali: **CÓDIGO COMPLETAMENTE ROTO** - Múltiples problemas:
  1. Consulta tabla `texts` que no existe
  2. Usa nombres de tabla incorrectos (`RoyalThai__*` vs `Dbf1__*`)
  3. No decodifica `UNITEXT` (Base64 + BOM + UTF-8)
  4. Usa `ENCPALI` (legacy PUA) en lugar de `UNITEXT`
- ⚠️ Soporte múltiples ediciones: Datos existen pero código no los accede correctamente
- ⚠️ Búsqueda básica: **NO FUNCIONA** - SQL LIKE sobre tabla inexistente + encoding incorrecto
- ⚠️ Diccionario Pali: Datos existen (`Dbf__dicdata`, `Dbf__Dict_PTS`) pero código usa placeholder

### 8.3. Implementadas en datos pero no en código
- ✅ Sistema de variantes textuales (38K+ variantes Ce vs PTS)
- ✅ Alineación entre ediciones (estructura preparada)
- ✅ Índice de palabras (2.6M+ entradas en `Dbf1__wordat`)
- ✅ Metadatos de libros y estructura jerárquica (53 libros en `Dbf1__book`)
- ✅ **Sistema completo de decodificación** (documentado en `DATABASE.md` y `query_pts.py`)
- ✅ **Apparatus criticus** (12,428 filas en `Dbf1__footpg`)
- ✅ **Diccionario Pali completo** (32K+ entradas en `Dbf__dicdata` y `Dbf__Dict_PTS`)

### 8.4. No Implementadas
- ❌ Búsqueda avanzada (operadores, filtros)
- ❌ Exportación de textos
- ❌ Sincronización de marcadores
- ❌ Anotaciones personales persistentes
- ❌ Comparación lado a lado de ediciones
- ❌ Estadísticas de texto (frecuencia de palabras, etc.)

### 8.2. Parcialmente Implementadas
- ⚠️ Diccionario Pali (placeholder, no datos reales)
- ⚠️ Referencias cruzadas (datos existen, UI limitada)
- ⚠️ Notas filológicas (datos existen, integración básica)

### 8.3. No Implementadas
- ❌ Búsqueda avanzada (operadores, filtros)
- ❌ Exportación de textos
- ❌ Sincronización de marcadores
- ❌ Anotaciones personales persistentes
- ❌ Comparación lado a lado de ediciones
- ❌ Estadísticas de texto (frecuencia de palabras, etc.)

## 9. Recomendaciones Inmediatas

### 9.1. Prioridad Crítica (Fase 1 - Urgente)
1. **Corregir acceso a base de datos:** El código actual NO FUNCIONA - múltiples problemas:
   - Tabla `texts` no existe
   - Nombres de tabla incorrectos (`RoyalThai__*` vs `Dbf1__*`)
   - No decodifica `UNITEXT` (Base64 + BOM + UTF-8)
2. **Implementar decodificación correcta:** Usar función `decode()` de `query_pts.py`
3. **Crear módulo de base de datos:** `database.py` con acceso correcto a `Dbf1__palipg`, `Dbf__dicdata`, etc.
4. **Documentar esquema real:** Actualizar `ESQUEMA_BASE_DATOS.md` con nombres corregidos y encoding

### 9.2. Prioridad Alta (Fase 1)
5. **Implementar logging estructurado:** Reemplazar print() statements
6. **Crear modelos de datos:** `models.py` que reflejen estructura real con nombres corregidos
7. **Reparar búsqueda básica:** Implementar sobre `Dbf1__wordat` (índice) y `Dbf1__palipg` (textos)
8. **Habilitar diccionario:** Usar `Dbf__dicdata` y `Dbf__Dict_PTS` reales
9. **Integrar `query_pts.py`:** Incorporar funciones de decodificación y consulta existentes

### 9.2. Prioridad Media (Fase 2)
1. **Separar lógica de negocio:** `TextService`, `SearchService`, `DictionaryService`
2. **Implementar ViewModels:** Separar estado de UI de lógica
3. **Componentizar QML:** Extraer `TextReader`, `SearchPanel`, etc.
4. **Añadir tests unitarios:** pytest para módulos core

### 9.3. Prioridad Baja (Fase 3)
1. **Sistema de temas:** Light/dark mode
2. **Búsqueda avanzada:** FTS5, operadores booleanos
3. **Sistema de plugins/extensions**
4. **Internacionalización completa**

## 10. Métricas de Código

### 10.1. Complejidad
- **Líneas de código:** ~500 en `__init__.py`
- **Clases:** 1 principal (`TipitakaBrowser`)
- **Métodos:** ~15 métodos públicos/privados
- **Acoplamiento:** Alto (mezcla UI, datos, lógica)

### 10.2. Bugs Críticos Identificados (ACTUALIZADO)
1. **Base de datos completamente rota:** Múltiples problemas:
   - Métodos `get_text()` y `search_texts()` usan tabla `texts` que NO EXISTE
   - Nombres de tabla incorrectos: usa `RoyalThai__*` pero tablas reales son `Dbf1__*`
   - No decodifica `UNITEXT` (textos en Base64 + BOM + UTF-8)
   - Usa `ENCPALI` (legacy PUA) en lugar de `UNITEXT`
2. **Consulta SQL incorrecta:** `SELECT content FROM texts WHERE id = ? AND edition = ?`
3. **Datos no accesibles:** Textos reales en `Dbf1__palipg` no son accedidos ni decodificados
4. **Diccionario placeholder:** Método `lookup_dictionary()` devuelve datos ficticios (datos reales en `Dbf__dicdata`)
5. **Falta integración con código existente:** `query_pts.py` tiene implementación correcta pero no se usa

### 10.3. Discrepancia Datos vs Código (ACTUALIZADO)
- **Código asume:** Tabla única `texts` con columnas `id`, `content`, `edition`, `title`
- **Realidad DB:** Sistema complejo con:
  - Tabla principal: `Dbf1__palipg` con `BOOKNUM`, `RPAGENUM`, `HEAD`, `UNITEXT`
  - Encoding especial: `UNITEXT` = Base64(BOM + UTF-8-bytes)
  - Índice de palabras: `Dbf1__wordat` (2.6M entradas)
  - Diccionario: `Dbf__dicdata` y

### 10.2. Calidad
- **Type hints:** Parciales (solo en firmas públicas)
- **Docstrings:** Básicos (solo en clases/métodos principales)
- **Comentarios:** Mínimos
- **Manejo de errores:** Básico (try/except genéricos)

### 10.3. Mantenibilidad
- **Deuda técnica:** Alta (monolito, acoplamiento)
- **Testeabilidad:** Baja (sin tests, acoplamiento alto)
- **Extensibilidad:** Baja (difícil añadir nuevas features)

## 11. Próximos Pasos

### 11.1. Análisis de Base de Datos (COMPLETADO)
✅ Ejecutado: `sqlite3 tipitaka.sqlite ".schema"` - 45 tablas + 4 vistas  
✅ Ejecutado: `sqlite3 tipitaka.sqlite ".tables"` - Lista completa  
✅ Ejecutado: Conteo de filas por tabla - Identificadas tablas principales  
✅ Identificado: **BUG CRÍTICO** - Código usa tabla `texts` que no existe

### 11.2. Pruebas Funcionales (PRIORIDAD)
1. **Probar comando `get` en CLI:** Fallará porque tabla `texts` no existe
2. **Probar comando `search` en CLI:** Fallará por misma razón
3. **Verificar carga GUI:** Probablemente falle al intentar cargar textos
4. **Validar diccionario:** Usa placeholder, no datos reales

### 11.3. Documentación de Esquema (URGENTE)
Crear `ESQUEMA_BASE_DATOS.md` con:
- Diagrama ER de estructura REAL (no la asumida por código)
- Descripción de tablas REALES que contienen textos
- Mapeo entre estructura de código y estructura real
- Plan de migración para corregir acceso a datos

### 11.4. Acciones Inmediatas
1. **Crear archivo `BUGS_CRITICOS.md`** documentando problemas encontrados
2. **Analizar `RoyalThai__palipg`** para entender formato real de textos
3. **Crear consultas SQL corregidas** que funcionen con estructura real
4. **Plan de corrección** para métodos `get_text()` y `search_texts()`

---

**Nota:** Este análisis se basa en examen inicial del código. Algunas conclusiones pueden refinarse tras análisis más profundo de la base de datos y pruebas funcionales completas.

**Responsable del análisis:** [Nombre]  
**Fecha:** [Fecha actual]  
**Versión del análisis:** 1.0