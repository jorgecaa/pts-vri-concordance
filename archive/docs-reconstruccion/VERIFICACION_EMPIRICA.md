# Verificación Empírica de Bugs - Tipitaka PTS Browser

## Fecha de Verificación
[Fecha actual]

## Método de Verificación
Consultas directas a la base de datos `tipitaka.sqlite` y pruebas del código actual.

## Resumen Ejecutivo

**ESTADO ACTUAL:** CÓDIGO COMPLETAMENTE NO FUNCIONAL  
**SEVERIDAD:** CRÍTICA - Todos los métodos principales fallan  
**IMPACTO:** Usuarios no pueden leer, buscar ni estudiar textos Pali

## Bugs Confirmados Empíricamente

### 1. Bug Crítico #1: Tabla `texts` No Existe ✅ CONFIRMADO

**Descripción:** Los métodos `get_text()` y `search_texts()` intentan acceder a una tabla `texts` que no existe en la base de datos.

**Evidencia Empírica:**
```sql
-- Consulta que falla:
SELECT content FROM texts WHERE id = 'dn1' AND edition = 'PTS';
-- Error: no such table: texts

-- Verificación directa:
SELECT name FROM sqlite_master WHERE type='table' AND name='texts';
-- Resultado: VACÍO (0 filas)
```

**Consecuencia:** `get_text()` siempre retorna `None`, `search_texts()` siempre retorna lista vacía.

### 2. Bug Crítico #2: Nombres de Tabla Incorrectos ✅ CONFIRMADO

**Descripción:** El código usa nombres de tabla `RoyalThai__*` y `PTS__*` pero las tablas reales son `Dbf1__*` y `Dbf__*`.

**Evidencia Empírica:**
```python
# Tablas que el código intenta usar (NO EXISTEN):
RoyalThai__palipg    → ✗ NO EXISTE
RoyalThai__book      → ✗ NO EXISTE  
RoyalThai__wordat    → ✗ NO EXISTE
RoyalThai__word      → ✗ NO EXISTE
PTS__dicdata         → ✗ NO EXISTE
PTS__Dict_PTS        → ✗ NO EXISTE
PTS__contents        → ✗ NO EXISTE

# Tablas reales disponibles (EXISTEN):
Dbf1__palipg         → ✓ 15,554 filas
Dbf1__book           → ✓ 53 filas
Dbf1__wordat         → ✓ 2,630,606 filas
Dbf1__word           → ✓ 199,998 filas
Dbf__dicdata         → ✓ 16,262 filas
Dbf__Dict_PTS        → ✓ 16,232 filas
Dbf__contents        → ✓ 0 filas (vacía)
```

**Consecuencia:** Imposible cualquier acceso a datos incluso si se corrigieran otros problemas.

### 3. Bug Crítico #3: Encoding No Decodificado ✅ CONFIRMADO

**Descripción:** Los textos Pali están almacenados en `UNITEXT` con encoding `Base64(BOM + UTF-8-bytes)` y no se decodifican.

**Evidencia Empírica:**
```python
# UNITEXT crudo (Base64):
'77u/ICAgICAgICAgICAgICAgICAgICAgICAgICAgVklOQVlBUEnhuaxBS0Hh...'

# Después de decodificación (función decode() de query_pts.py):
'                            VINAYAPIṬAKAṂ
                           ------------------------'
```

**Función de Decodificación Correcta (ya existe en `query_pts.py`):**
```python
def decode(val: str | None) -> str:
    if not val:
        return ""
    try:
        raw = base64.b64decode(val.strip() + "==")
        if raw[:3] == b"\xef\xbb\xbf":
            raw = raw[3:]
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return val
```

**Consecuencia:** Textos Pali ilegibles (se muestra Base64 crudo en lugar de texto decodificado).

### 4. Bug Crítico #4: Diccionario Placeholder ✅ CONFIRMADO

**Descripción:** El método `lookup_dictionary()` devuelve datos ficticios en lugar de usar el diccionario Pali real.

**Evidencia Empírica:**
```python
# Código actual (placeholder):
return {
    "word": word,
    "definition": f"Definition for {word}",  # FICTICIO
    "etymology": "Pali",  # FICTICIO
    "examples": [],
}

# Datos reales disponibles:
Dbf__dicdata: 16,262 entradas de diccionario Pali-Inglés
Dbf__Dict_PTS: 16,232 entradas adicionales

# Ejemplo de entrada real para "buddha":
{
    "ETITLE": "Buddha",
    "EDETAIL": "[for vuddha, pp. of vrdh, see vaddhati] aged, old D II.162 ; J I.164..."
}
```

**Consecuencia:** Funcionalidad de diccionario inútil - no provee definiciones reales.

### 5. Bug Crítico #5: Consultas SQL Incorrectas ✅ CONFIRMADO

**Descripción:** Las consultas SQL en el código no coinciden con la estructura real de la base de datos.

**Evidencia Empírica:**
```python
# Consulta actual (INCORRECTA):
"SELECT content FROM texts WHERE id = ? AND edition = ?"

# Consulta correcta para get_text():
"""
SELECT BOOKNUM, RPAGENUM, HEAD, UNITEXT 
FROM Dbf1__palipg 
WHERE BOOKNUM = ? AND RPAGENUM = ? AND _deleted = 0
"""

# Consulta actual para búsqueda (INCORRECTA):
"""
SELECT id, title, edition, snippet(content, '<b>', '</b>', '...', 10) as snippet
FROM texts WHERE content LIKE ? LIMIT ?
"""

# Consulta correcta para búsqueda:
"""
SELECT DISTINCT w.BOOK, w.PAGE, p.HEAD as title,
       substr(p.UNITEXT, 1, 200) as preview
FROM Dbf1__wordat w
JOIN Dbf1__palipg p ON w.BOOK = p.BOOK AND w.PAGE = p.PAGE
WHERE w.WORD LIKE '%' || ? || '%' AND p._deleted = 0
LIMIT ?
"""
```

**Consecuencia:** Búsqueda imposible - consultas referencian tablas y columnas inexistentes.

### 6. Bug Crítico #6: Edición PTS Sin Textos ✅ CONFIRMADO

**Descripción:** La edición PTS no tiene textos cargados en la base de datos.

**Evidencia Empírica:**
```sql
SELECT COUNT(*) FROM Dbf__contents WHERE _deleted=0;
-- Resultado: 0 filas

SELECT code, name, source_table FROM edition;
-- ROYALTHAI: Royal Thai Tipitaka (Dbf1__palipg) - ✓ CON DATOS
-- PTS: Pali Text Society (PTS__*) - ✗ TABLAS VACÍAS O INEXISTENTES
```

**Consecuencia:** Cambiar a edición PTS en la interfaz no mostrará textos.

## Pruebas de Código Actual

### Resultado de Ejecutar `TipitakaBrowser`:
```
✓ Módulo importado correctamente
✓ Instancia creada
✓ get_text() retornó None (como esperado - tabla texts no existe)
✓ search_texts() retornó lista vacía (como esperado)
✓ lookup_dictionary() retornó (pero es placeholder)
⚠️ DEFINICIÓN PLACEHOLDER - no usa datos reales
✓ Conexión a base de datos establecida
✓ Tabla REAL Dbf1__palipg accesible: 15554 filas
✓ Tabla "texts" NO existe: no such table: texts
```

## Datos Reales Disponibles (No Utilizados)

| Recurso | Cantidad | Estado |
|---------|----------|--------|
| Textos Pali (Dbf1__palipg) | 15,554 páginas | ✅ DISPONIBLE |
| Diccionario Pali (Dbf__dicdata) | 16,262 entradas | ✅ DISPONIBLE |
| Diccionario PTS (Dbf__Dict_PTS) | 16,232 entradas | ✅ DISPONIBLE |
| Índice de palabras (Dbf1__wordat) | 2,630,606 entradas | ✅ DISPONIBLE |
| Apparatus criticus (Dbf1__footpg) | 12,428 notas | ✅ DISPONIBLE |
| Metadatos de libros (Dbf1__book) | 53 libros | ✅ DISPONIBLE |

## Código Existente Utilizable

### 1. `query_pts.py` - Implementación CORRECTA
- ✅ Función `decode()` para decodificar `UNITEXT`
- ✅ Consultas SQL correctas
- ✅ Manejo de citaciones PTS

### 2. `DATABASE.md` - Documentación COMPLETA
- ✅ Esquema real de base de datos
- ✅ Explicación de encoding `UNITEXT`
- ✅ Relaciones entre tablas

## Impacto en Usuarios Finales

### Funcionalidades COMPLETAMENTE ROTAS:
1. **Lectura de textos Pali** - No se pueden cargar textos
2. **Búsqueda en textos** - No devuelve resultados
3. **Diccionario Pali** - Definiciones ficticias
4. **Cambio de edición** - Edición PTS sin textos
5. **Visualización** - Textos mostrados como Base64 crudo

### Experiencia de Usuario:
- Aplicación parece funcionar (no hay crashes evidentes)
- Pero no produce resultados útiles
- Textos ilegibles (Base64/PUA encoding)
- Búsquedas siempre vacías
- Diccionario con definiciones falsas

## Recomendaciones de Corrección (Priorizadas)

### Fase 1: Correcciones Críticas (SEMANA 1)
1. **Corregir nombres de tabla** - `RoyalThai__*` → `Dbf1__*`, `PTS__*` → `Dbf__*`
2. **Integrar función `decode()`** - Usar implementación existente de `query_pts.py`
3. **Reescribir `get_text()`** - Consulta correcta a `Dbf1__palipg` con decodificación
4. **Reescribir `search_texts()`** - Usar `Dbf1__wordat` para búsqueda indexada

### Fase 2: Funcionalidad Básica (SEMANA 2)
1. **Implementar diccionario real** - Usar `Dbf__dicdata` y `Dbf__Dict_PTS`
2. **Corregir gestión de ediciones** - Solo mostrar ediciones con datos reales
3. **Crear tests de integración** - Verificar correcciones funcionan

### Fase 3: Mejoras (SEMANA 3)
1. **Implementar FTS5** - Búsqueda de texto completo eficiente
2. **Cache de textos decodificados** - Mejorar rendimiento
3. **Sistema de logging** - Monitorizar acceso a datos

## Conclusión Final

**LA APLICACIÓN ACTUAL ES COMPLETAMENTE NO FUNCIONAL** debido a múltiples bugs críticos en el acceso a datos. 

**Problemas fundamentales:**
1. Código referencia tablas que no existen
2. No decodifica textos Pali (muestra Base64 crudo)
3. Usa diccionario placeholder en lugar de datos reales
4. Consultas SQL incorrectas

**Sin embargo:** Los datos reales del Tipitaka Pali **SÍ EXISTEN** y son accesibles usando los nombres de tabla correctos (`Dbf1__*`, `Dbf__*`) y la función de decodificación adecuada.

**Prioridad máxima:** Detener cualquier desarrollo de nuevas features hasta corregir estos bugs fundamentales. La aplicación debe poder al menos cargar y mostrar textos Pali correctamente antes de añadir cualquier funcionalidad adicional.

---
**Verificado por:** [Nombre]  
**Fecha:** [Fecha actual]  
**Estado:** CRÍTICO - Requiere atención inmediata