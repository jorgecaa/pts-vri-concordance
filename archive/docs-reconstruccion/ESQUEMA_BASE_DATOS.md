# Esquema de Base de Datos - Tipitaka PTS Browser

## 1. Resumen Ejecutivo

**Base de datos:** `tipitaka.sqlite`  
**Total tablas:** 45 tablas + 4 vistas  
**Tamaño estimado:** ~100MB+ (datos textuales completos)  
**Fecha de análisis:** [Fecha actual]  
**Estado:** Base de datos compleja con sistema de ediciones, variantes y alineaciones  
**INFORMACIÓN CRÍTICA:** Los nombres de tabla en el código son incorrectos - ver sección 2.1

## 2. Problema Crítico Identificado

### 2.1. Discrepancia Código vs Realidad
- **Código asume:** Tabla única `texts` con columnas `id`, `content`, `edition`, `title`
- **Realidad DB:** Sistema distribuido con múltiples tablas por edición
- **Nombres incorrectos:** Código usa `RoyalThai__*` pero tablas reales son `Dbf1__*`
- **Encoding no manejado:** Textos en `UNITEXT` requieren decodificación Base64 + BOM + UTF-8
- **Consecuencia:** Los métodos `get_text()` y `search_texts()` en `main/__init__.py` NO FUNCIONAN

### 2.2. Consultas Incorrectas en Código Actual
```python
# En get_text() - LÍNEA 100-115
SELECT content FROM texts WHERE id = ? AND edition = ?

# En search_texts() - LÍNEA 120-140  
SELECT id, title, edition, snippet(content, '<b>', '</b>', '...', 10) 
FROM texts WHERE content LIKE ? LIMIT ?
```

**PROBLEMA:** La tabla `texts` NO EXISTE en la base de datos. Además:
1. Los nombres de tabla son incorrectos (`RoyalThai__*` vs `Dbf1__*`)
2. No se decodifica `UNITEXT` (Base64 + BOM + UTF-8)
3. Se usa `ENCPALI` (legacy PUA) en lugar de `UNITEXT`

## 3. Estructura General de la Base de Datos

### 3.1. Sistema de Ediciones
```
edition (tabla maestra)
├── ROYALTHAI → Dbf1__* (tablas principales) [CORRECCIÓN: RoyalThai__* → Dbf1__*]
├── PTS → Dbf__* (tablas) [CORRECCIÓN: PTS__* → Dbf__*]
├── CHA → sutta_variants (en appdata)
├── Ce → ce_variant (tablas)
└── CeBa → ce_variant_witness (tablas)
```

### 3.2. Categorías de Tablas

#### 3.2.1. Catálogo y Metadatos (5 tablas) [NOMBRES CORREGIDOS]
- `edition` - Catálogo de ediciones disponibles
- `canonical_passage` - Pasajes canónicos de referencia
- `Dbf1__book` - Metadatos de libros Royal Thai [CORRECCIÓN: RoyalThai__book → Dbf1__book]
- `Dbf__tranbook2` - Metadatos de traducciones PTS [CORRECCIÓN: PTS__tranbook2 → Dbf__tranbook2]
- `Dbf1__tranbook` - Metadatos de traducciones Royal Thai [CORRECCIÓN: RoyalThai__tranbook → Dbf1__tranbook]

#### 3.2.2. Textos por Edición (8+ tablas) [NOMBRES CORREGIDOS]
- `Dbf1__palipg` - **TEXTOS PRINCIPALES** (15,561 filas) [CORRECCIÓN: RoyalThai__palipg → Dbf1__palipg]
- `Dbf__contents` - Contenidos PTS (vacía en esta copia) [CORRECCIÓN: PTS__contents → Dbf__contents]
- `Dbf__dicdata` - Datos de diccionario PTS (16,262 filas) [CORRECCIÓN: PTS__dicdata → Dbf__dicdata]
- `Dbf__Dict_PTS` - Diccionario PTS (16,232 filas) [CORRECCIÓN: PTS__Dict_PTS → Dbf__Dict_PTS]
- `Dbf1__appendix` - Apéndices [CORRECCIÓN: RoyalThai__appendix → Dbf1__appendix]
- `Dbf1__preface` - Prefacios [CORRECCIÓN: RoyalThai__preface → Dbf1__preface]
- `Dbf1__footpg` - Notas al pie (12,428 filas) [CORRECCIÓN: RoyalThai__footpg → Dbf1__footpg]
- `Dbf1__commentwdc` - Comentarios [CORRECCIÓN: RoyalThai__commentwdc → Dbf1__commentwdc]

#### 3.2.3. Sistema de Variantes (10+ tablas)
- `variant_reading` - Variantes de lectura generales
- `ce_sutta_variant` - Variantes Ce vs PTS (38,933 filas)
- `ce_variant` - Variantes Ce
- `ce_variant_witness` - Testigos de variantes Ce
- `dpr_variant` - Variantes DPR (16,255 filas)
- `ce_sutta_variant_stats` - Estadísticas de variantes
- `ce_page_text` - Textos por página Ce

#### 3.2.4. Índices y Búsqueda (3 tablas principales) [NOMBRES CORREGIDOS]
- `Dbf1__wordat` - **ÍNDICE PRINCIPAL** (2,630,606 filas) [CORRECCIÓN: RoyalThai__wordat → Dbf1__wordat]
- `Dbf1__wordbook` - Palabras por libro (443,366 filas) [CORRECCIÓN: RoyalThai__wordbook → Dbf1__wordbook]
- `Dbf1__word` - Diccionario de palabras (199,998 filas) [CORRECCIÓN: RoyalThai__word → Dbf1__word]

#### 3.2.5. Sistema de Alineación (4 tablas)
- `edition_segment` - Segmentos de edición (vacía)
- `segment_alignment` - Alineación entre segmentos
- `dpr_hierarchy_para` - Jerarquía DPR (168,671 filas)
- `dpr_mat_map` - Mapeo DPR (17,301 filas)

#### 3.2.6. Configuración y Usuarios (6 tablas) [NOMBRES CORREGIDOS]
- `APPUSER` - Usuarios de aplicación
- `DhammaUser` - Usuarios Dhamma
- `SETSYS` - Configuración del sistema
- `Dbf__LangKeyb` - Configuración de teclado [CORRECCIÓN: PTS__LangKeyb → Dbf__LangKeyb]
- `Dbf__keyboard` - Mapeo de teclado [CORRECCIÓN: PTS__keyboard → Dbf__keyboard]
- `WordOld` - Palabras antiguas

## 4. Tablas Clave Detalladas

### 4.1. `edition` - Catálogo de Ediciones
```sql
CREATE TABLE edition (
    edition_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    code         TEXT NOT NULL UNIQUE,      -- Código corto (ROYALTHAI, PTS, CHA, Ce, CeBa)
    name         TEXT NOT NULL,             -- Nombre completo
    script       TEXT,                      -- Script (Thai/Romanized, Romanized, Sinhala/Romanized)
    source_table TEXT,                      -- Tabla fuente principal
    notes        TEXT                       -- Notas descriptivas
);
```

**Datos actuales:**
| edition_id | code       | name                              | script            | source_table            |
|------------|------------|-----------------------------------|-------------------|-------------------------|
| 1          | ROYALTHAI  | Royal Thai Tipitaka               | Thai/Romanized    | RoyalThai__palipg       |
| 2          | PTS        | Pali Text Society                 | Romanized         | PTS__*                  |
| 5          | CHA        | Chaṭṭhasaṅgīti Tipiṭaka (6th Council, Be) | Romanized | sutta_variants@appdata |
| 82         | Ce         | Buddha Jayanti Tripitaka          | Sinhala/Romanized | ce_variant              |
| 83         | CeBa       | sīmu7 witness variants aligned against Ce | Sinhala/Romanized | ce_variant_witness |

### 4.2. `Dbf1__palipg` - Textos Pali Principales [NOMBRE CORREGIDO]
```sql
CREATE TABLE "Dbf1__palipg" (
  "VOL_ID" TEXT,
  "SKID" TEXT,
  "BOOKNUM" NUMERIC,
  "RPAGENUM" NUMERIC,
  "BOOK" TEXT,          -- Código de libro (ej: "%") - offset-encoded
  "PAGE" TEXT,          -- Página (ej: "$%", "$&") - offset-encoded
  "FOOTNLINE" NUMERIC,
  "ENCPALI" TEXT,       -- **TEXTO PALI ENCODED** (Base64 PUA) - NO USAR
  "HEAD" TEXT,          -- Encabezado (UTF-8 plano)
  "WORDNEXTPA" TEXT,
  "COMMENTWDC" TEXT,
  "UNITEXT" TEXT,       -- **TEXTO PRINCIPAL**: Base64(BOM + UTF-8-bytes)
  "_deleted" INTEGER NOT NULL DEFAULT 0
);
```

**Características:**
- 15,561 registros de texto Pali
- **Texto principal en `UNITEXT`**: Base64(BOM + UTF-8-bytes) - REQUIERE DECODIFICACIÓN
- **`ENCPALI` es legacy PUA**: Base64 con caracteres Private Use Area - NO USAR
- **`HEAD` es UTF-8 plano**: No requiere decodificación Base64
- Estructura por libro (`BOOKNUM`) y página (`RPAGENUM`)
- Claves offset-encoded: `BOOK` y `PAGE` (para joins con `Dbf1__footpg`)
- Siempre filtrar `_deleted = 0`

### 4.3. `Dbf1__wordat` - Índice de Palabras [NOMBRE CORREGIDO]
```sql
CREATE TABLE "Dbf1__wordat" (
  "WORD" TEXT,          -- Palabra
  "BOOK" TEXT,          -- Libro (offset-encoded)
  "PAGE" TEXT,          -- Página (offset-encoded)
  "LINE" TEXT,          -- Línea
  "WORDLEN" TEXT,       -- Longitud de palabra
  "ATCOL" TEXT,         -- Columna
  "ISCROSS" TEXT,       -- Es referencia cruzada
  "FOOTPOST" TEXT,      -- Posición en nota al pie
  "WORD2" TEXT,
  "WORD3" TEXT,
  "WORD4" TEXT,
  "WORD5" TEXT,
  "LINENO" TEXT,
  "_deleted" INTEGER NOT NULL DEFAULT 0
);
```

**Características:**
- 2,630,606 entradas - índice completo de palabras
- Permite búsqueda rápida por palabra
- Referencias a libro, página, línea

### 4.4. `PTS__dicdata` y `PTS__Dict_PTS` - Diccionario Pali
```sql
-- PTS__dicdata (16,262 filas)
CREATE TABLE "PTS__dicdata" (
  "TTITLE" TEXT,        -- Título tailandés
  "TDETAIL" TEXT,       -- Detalle tailandés
  "KEY" NUMERIC,        -- Clave numérica
  "NUMBER" TEXT,        -- Número de entrada
  "ETITLE" TEXT,        -- Título inglés
  "EDETAIL" TEXT,       -- Detalle inglés
  "_deleted" INTEGER NOT NULL DEFAULT 0
);

-- PTS__Dict_PTS (16,232 filas)  
CREATE TABLE "PTS__Dict_PTS" (
  "TTITLE" TEXT,        -- Título tailandés
  "TDETAIL" TEXT,       -- Detalle tailandés
  "PAGE_NO" TEXT,       -- Número de página
  "WORD_NO" TEXT,       -- Número de palabra
  "_deleted" INTEGER NOT NULL DEFAULT 0
);
```

## 5. Vistas Disponibles

### 5.1. `royal_thai_volume_book_detail`
- Vista que une `royal_thai_physical_volume`, `royal_thai_volume_book_map` y `RoyalThai__book`
- Proporciona mapeo entre volúmenes físicos y libros lógicos

### 5.2. `royal_thai_book_volume_detail`
- Vista inversa: libros → volúmenes físicos

### 5.3. `royal_thai_volume_overview`
- Resumen de volúmenes con libros asociados

## 6. Consultas Corregidas para Reemplazar Código Actual

### 6.1. Para `get_text(text_id, edition)` - Obtener texto
```sql
-- Para edición ROYALTHAI
SELECT BOOK, PAGE, ENCPALI, HEAD, COMMENTWDC
FROM RoyalThai__palipg 
WHERE BOOK = ? AND PAGE = ?
LIMIT 1;

-- Para edición PTS (si hubiera datos)
SELECT BOOK, CONTENTS, PIDOK, PAGE
FROM PTS__contents
WHERE BOOK = ? AND PAGE = ?
LIMIT 1;
```

### 6.2. Para `search_texts(query, limit)` - Buscar textos
```sql
-- Búsqueda en textos Royal Thai
SELECT BOOK, PAGE, 
       substr(ENCPALI, 1, 500) as preview,
       HEAD as title
FROM RoyalThai__palipg 
WHERE ENCPALI LIKE '%' || ? || '%'
LIMIT ?;

-- Búsqueda usando índice de palabras (más eficiente)
SELECT DISTINCT w.BOOK, w.PAGE, p.HEAD as title,
       substr(p.ENCPALI, 1, 500) as preview
FROM RoyalThai__wordat w
JOIN RoyalThai__palipg p ON w.BOOK = p.BOOK AND w.PAGE = p.PAGE
WHERE w.WORD LIKE '%' || ? || '%'
LIMIT ?;
```

### 6.3. Para `lookup_dictionary(word)` - Buscar en diccionario
```sql
-- En PTS__dicdata (inglés/tailandés)
SELECT ETITLE as word, EDETAIL as definition, 
       TTITLE as word_th, TDETAIL as definition_th,
       NUMBER as entry_number
FROM PTS__dicdata
WHERE ETITLE LIKE ? OR TTITLE LIKE ?
LIMIT 10;

-- En PTS__Dict_PTS
SELECT TTITLE as word, TDETAIL as definition,
       PAGE_NO, WORD_NO
FROM PTS__Dict_PTS
WHERE TTITLE LIKE ?
LIMIT 10;
```

## 7. Plan de Corrección

### 7.1. Fase 1: Corrección Crítica (Urgente)
1. **Modificar `TipitakaBrowser._load_data()`:** Conectar correctamente a tablas reales
2. **Reescribir `get_text()`:** Usar consultas de la sección 6.1
3. **Reescribir `search_texts()`:** Usar consultas de la sección 6.2
4. **Reescribir `lookup_dictionary()`:** Usar consultas de la sección 6.3

### 7.2. Fase 2: Normalización
1. **Crear vista unificada `texts`:** Para mantener compatibilidad con código existente
2. **Implementar sistema de decodificación:** Para `ENCPALI` (encoding especial)
3. **Añadir soporte para múltiples ediciones:** No solo ROYALTHAI

### 7.3. Fase 3: Mejoras
1. **Implementar FTS5:** Para búsqueda de texto completo eficiente
2. **Cache de consultas frecuentes:** Mejorar rendimiento
3. **Sistema de migración:** Para futuras actualizaciones de esquema

## 8. Estructura de Decodificación de `ENCPALI`

### 8.1. Análisis preliminar
Los datos en `ENCPALI` parecen usar encoding personalizado:
- Caracteres especiales (ej: `7oOT7oKV7oKt7oKB`)
- Posiblemente encoding Thai/Romanizado
- Necesita función de decodificación

### 8.2. Ejemplo de datos:
```sql
SELECT BOOK, PAGE, substr(ENCPALI, 1, 50) as sample 
FROM RoyalThai__palipg LIMIT 3;

-- Resultado:
-- % | $% | 7oOT7oKV7oKt7oKB7oOV7oKB7oK57oKV7oOM7oKB7oKb7oKB7oKo
-- % | $& | 7oKy7oKX7oOA7oK47oKL7oKT7oK4IO6Ck+6CuO6Dje6CmO6Dje6Cly4g7oOYMu6DmCDugoPug43ugpPugoMg7oKc7oKT7oK4IO6C
-- % | $' | 7oOU7oKD7oKy7oON7oKD7oKsIO6Cju6Dje6Cg+6CiyDugoPug5TugrjugojugoM6IO6CnO6Cl+6Dje6Dje6ChO6DlO6Cg+6Dje6C
```

## 9. Recomendaciones de Implementación

### 9.1. Archivo `database.py` (nuevo)
```python
class TipitakaDatabase:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
    def get_text(self, book, page, edition="ROYALTHAI"):
        """Obtiene texto real de la base de datos"""
        if edition == "ROYALTHAI":
            return self._get_royalthai_text(book, page)
        elif edition == "PTS":
            return self._get_pts_text(book, page)
        # ... otras ediciones
    
    def search_texts(self, query, limit=50, edition="ROYALTHAI"):
        """Búsqueda real en textos"""
        # Implementar usando consultas corregidas
```

### 9.2. Decodificador `text_decoder.py`
```python
class TextDecoder:
    @staticmethod
    def decode_encpali(encpali_text):
        """Decodifica texto ENCPALI a Unicode"""
        # Implementar decodificación del encoding especial
        pass
    
    @staticmethod  
    def encode_to_encpali(unicode_text):
        """Codifica texto Unicode a ENCPALI"""
        pass
```

## 10. Conclusión

La base de datos `tipitaka.sqlite` es un sistema complejo y completo para el estudio del Tipitaka Pali, pero:

1. **El código actual no funciona** porque asume una estructura simplificada que no existe
2. **Los datos reales están disponibles** en tablas específicas por edición
3. **Se necesita reescribir el acceso a datos** para usar la estructura real
4. **El diccionario Pali ya existe** en `PTS__dicdata` y `PTS__Dict_PTS`

**Prioridad máxima:** Corregir los métodos `get_text()` y `search_texts()` antes de cualquier otra mejora.

---
**Fecha de análisis:** [Fecha actual]  
**Versión del esquema:** 1.0  
**Próxima actualización:** Después de implementar correcciones