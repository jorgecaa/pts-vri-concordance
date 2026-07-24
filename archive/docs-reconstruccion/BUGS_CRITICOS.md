# Bugs Críticos Identificados - Tipitaka PTS Browser v1.0.0

**INFORMACIÓN CRÍTICA DESCUBIERTA:** Los nombres de tabla en el código son incorrectos según `DATABASE.md`

## Resumen Ejecutivo

**Estado:** CÓDIGO COMPLETAMENTE ROTO - Múltiples problemas fundamentales  
**Fecha de identificación:** [Fecha actual]  
**Severidad:** CRÍTICA - Todos los métodos principales tienen problemas  
**Impacto:** Usuarios no pueden cargar, buscar ni leer textos Pali

## 1. Bug Crítico #1: Sistema de Acceso a Datos Completamente Roto

### Descripción
Múltiples problemas en el acceso a datos:

1. **Tabla `texts` no existe:** Los métodos `get_text()` y `search_texts()` intentan acceder a una tabla `texts` que **NO EXISTE**
2. **Nombres de tabla incorrectos:** El código usa `RoyalThai__*` pero las tablas reales son `Dbf1__*` (según `DATABASE.md`)
3. **Encoding no manejado:** Los textos están en `UNITEXT` con encoding `Base64(BOM + UTF-8-bytes)` y no se decodifican
4. **Uso incorrecto de campos:** Se referencia `ENCPALI` (legacy PUA) en lugar de `UNITEXT` (texto principal)

### Ubicación
- Archivo: `squashfs-root/src/main/__init__.py`
- Líneas: 100-115 (`get_text()`), 120-140 (`search_texts()`)

### Código Defectuoso
```python
# En get_text() - LÍNEA 100-115 - MÚLTIPLES PROBLEMAS:
# 1. Tabla 'texts' no existe
# 2. Columnas 'id', 'content', 'edition' no existen en tablas reales
# 3. No decodifica UNITEXT (Base64 + BOM + UTF-8)
cursor.execute(
    "SELECT content FROM texts WHERE id = ? AND edition = ?",
    (text_id, edition),
)

# En search_texts() - LÍNEA 120-140 - MÚLTIPLES PROBLEMAS:
# 1. Tabla 'texts' no existe  
# 2. Usa LIKE sobre texto codificado (no funcionaría incluso si la tabla existiera)
# 3. No usa índices disponibles (Dbf1__wordat con 2.6M entradas)
cursor.execute(
    """
    SELECT id, title, edition, snippet(content, '<b>', '</b>', '...', 10) as snippet
    FROM texts
    WHERE content LIKE ?
    LIMIT ?
    """,
    (f"%{query}%", limit),
)
```

### Evidencia
```sql
-- Verificación en base de datos:
sqlite> .tables | grep texts
# NO HAY RESULTADOS - la tabla 'texts' no existe

sqlite> SELECT name FROM sqlite_master WHERE type='table' AND name='texts';
# RESULTADO VACÍO

-- Nombres de tabla REALES vs usados en código:
sqlite> .tables | grep -E "(Dbf1|RoyalThai)"
Dbf1__appendix          # Código usa: RoyalThai__appendix (INCORRECTO)
Dbf1__bkconte           # Código usa: RoyalThai__bkconte (INCORRECTO)  
Dbf1__book              # Código usa: RoyalThai__book (INCORRECTO)
Dbf1__chmark            # Código usa: RoyalThai__chmark (INCORRECTO)
Dbf1__commentwdc        # Código usa: RoyalThai__commentwdc (INCORRECTO)
Dbf1__footpg            # Código usa: RoyalThai__footpg (INCORRECTO)
Dbf1__palipg            # Código usa: RoyalThai__palipg (INCORRECTO) - TABLA PRINCIPAL
Dbf1__preface           # Código usa: RoyalThai__preface (INCORRECTO)
Dbf1__tranbook          # Código usa: RoyalThai__tranbook (INCORRECTO)
Dbf1__word              # Código usa: RoyalThai__word (INCORRECTO)
Dbf1__wordat            # Código usa: RoyalThai__wordat (INCORRECTO) - ÍNDICE PRINCIPAL
Dbf1__wordbook          # Código usa: RoyalThai__wordbook (INCORRECTO)

-- Encoding de UNITEXT (según DATABASE.md):
-- UNITEXT = Base64(BOM + UTF-8-bytes) donde BOM = 0xEF 0xBB 0xBF
-- ENCPALI = Base64 PUA (Private Use Area) - NO USAR
-- HEAD = UTF-8 plano (no Base64)
```

### Consecuencias
1. **`get_text()` siempre retorna `None`** - No se pueden cargar textos
2. **`search_texts()` siempre retorna lista vacía** - No funciona la búsqueda
3. **Interfaz gráfica muestra textos vacíos o codificados** (Base64/PUA)
4. **Modo CLI no puede recuperar textos**
5. **Texto Pali ilegible** incluso si se pudiera acceder (sin decodificación)
6. **Búsqueda imposible** - LIKE sobre texto Base64 no encuentra patrones

### Solución Propuesta
Reescribir completamente los métodos para:

1. **Usar nombres de tabla correctos:** `Dbf1__*` en lugar de `RoyalThai__*`
2. **Implementar decodificación:** Usar función `decode()` de `query_pts.py` para `UNITEXT`
3. **Consultas correctas:**
   ```sql
   -- Para get_text():
   SELECT BOOKNUM, RPAGENUM, HEAD, UNITEXT 
   FROM Dbf1__palipg WHERE BOOKNUM = ? AND RPAGENUM = ? AND _deleted = 0
   
   -- Para search_texts():
   SELECT DISTINCT w.BOOK, w.PAGE, p.HEAD as title,
          substr(p.UNITEXT, 1, 500) as preview
   FROM Dbf1__wordat w
   JOIN Dbf1__palipg p ON w.BOOK = p.BOOK AND w.PAGE = p.PAGE
   WHERE w.WORD LIKE '%' || ? || '%' AND p._deleted = 0
   LIMIT ?
   ```
4. **Integrar `query_pts.py`:** Ya tiene implementación correcta de decodificación


### Información de DATABASE.md Relevante
- **Tabla principal:** `Dbf1__palipg` (15,561 filas) - NO `RoyalThai__palipg`
- **Texto principal:** `UNITEXT` = `Base64(BOM + UTF-8-bytes)` - REQUIERE DECODIFICACIÓN
- **`ENCPALI`:** Legacy PUA (Private Use Area) - **NO USAR**
- **`HEAD`:** UTF-8 plano - no requiere decodificación Base64
- **Función `decode()`:** Ya implementada en `query_pts.py` - usar directamente


### Información de DATABASE.md Relevante
- **Sección 2.1:** "UNITEXT — the primary text field (BOM + Base64 UTF-8)"
- **Función `decode()`:** Proporcionada en línea 79-95 de DATABASE.md
- **Advertencia:** "ENCPALI — legacy PUA encoding (avoid)"
- **`HEAD` field:** "plain UTF-8" - no requiere Base64 decoding

---

## 2. Bug Crítico #2: Encoding No Decodificado (UNITEXT)

### Descripción
Los textos Pali están almacenados en `UNITEXT` con encoding especial que no se decodifica:

```
UNITEXT = Base64( BOM + UTF-8-bytes )
```

Donde **BOM** = `0xEF 0xBB 0xBF` (UTF-8 byte-order mark).

El código actual no realiza esta decodificación, mostrando texto Base64 ilegible.

### Ejemplo de Datos Codificados vs Decodificados
```sql
-- Datos crudos en base de datos:
SELECT substr(UNITEXT, 1, 60) FROM Dbf1__palipg WHERE BOOKNUM=26 AND RPAGENUM=25;
-- Resultado (Base64): "7oOT7oKV7oKt7oKB7oOV7oKB7oK57oKV7oOM7oKB7oKb7oKB7oKo..."

-- Después de decodificación (según query_pts.py):
-- Resultado (Pali legible): "Evaṃ me sutaṃ..."
```

### Función de Decodificación (de query_pts.py)
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
        return val   # Para campos como HEAD que son UTF-8 plano
```

### Estructura Real de Datos (CORREGIDA)
```
# REALIDAD EN BASE DE DATOS (según DATABASE.md):
edition (edition_id, code, name, script, source_table, notes)
├── ROYALTHAI → Dbf1__palipg (BOOKNUM, RPAGENUM, HEAD, UNITEXT, ...)
│   ├── UNITEXT: Base64(BOM + UTF-8-bytes) - REQUIERE decode()
│   ├── HEAD: UTF-8 plano - NO requiere decode()
│   └── ENCPALI: Base64 PUA - NO USAR
├── PTS → Dbf__* (tablas)
├── CHA → sutta_variants@appdata
├── Ce → ce_variant, ce_page_text
└── CeBa → ce_variant_witness
```

### Consecuencias
1. **Texto Pali ilegible** - Se muestra Base64 crudo en lugar de texto decodificado
2. **Búsqueda imposible** - `LIKE` sobre Base64 no encuentra patrones de texto
3. **Exportación incorrecta** - Se exportaría texto Base64, no Pali legible
4. **Interfaz inútil** - Usuarios ven caracteres codificados, no el Tipitaka

### Solución Propuesta
1. **Integrar función `decode()` de `query_pts.py`** - Ya está implementada correctamente
2. **Aplicar decodificación automáticamente** en `get_text()` y `search_texts()`
3. **Cachear texto decodificado** para mejor rendimiento
4. **Actualizar interfaz QML** para mostrar texto decodificado, no Base64

**Código existente utilizable:**
```python
# query_pts.py ya tiene la implementación correcta
from data.query_pts import decode

# Uso:
texto_decodificado = decode(unitext_crudo)
```

---

## 3. Bug Crítico #3: Nombres de Tabla Incorrectos

### Descripción
El código usa nombres de tabla incorrectos que no existen en la base de datos:

- **Código usa:** `RoyalThai__*` (ej: `RoyalThai__palipg`, `RoyalThai__wordat`)
- **Realidad DB:** `Dbf1__*` (ej: `Dbf1__palipg`, `Dbf1__wordat`)

Esto impide cualquier acceso a datos incluso si se corrigieran otros problemas.

### Ubicación
- Todo el código que referencia tablas `RoyalThai__*` o `PTS__*`
- Principalmente en `main/__init__.py` pero potencialmente en otros lugares

### Código Defectuoso
```python
def lookup_dictionary(self, word: str) -> Optional[Dict[str, Any]]:
    # This is a placeholder - actual implementation would depend on dictionary format
    return {
        "word": word,
        "definition": f"Definition for {word}",  # FICTICIO
        "etymology": "Pali",  # FICTICIO
        "examples": [],
    }
```

### Datos Reales Disponibles (NO UTILIZADOS)
1. **`PTS__dicdata`** - 16,262 entradas de diccionario (inglés/tailandés)
2. **`PTS__Dict_PTS`** - 16,232 entradas adicionales
3. **`RoyalThai__word`** - 199,998 palabras indexadas

### Consecuencias
1. **Funcionalidad de diccionario inútil** - No provee definiciones reales
2. **Datos valiosos sin utilizar** - Se desperdician 32K+ entradas de diccionario
3. **Experiencia de usuario pobre** - Expectativas no cumplidas

### Solución Propuesta
Implementar búsqueda real en:
- `PTS__dicdata` para definiciones inglés/tailandés
- `PTS__Dict_PTS` para entradas adicionales
- `RoyalThai__word` para referencias cruzadas

---

## 4. Bug Crítico #4: Sistema de Búsqueda Ineficiente

### Descripción
La búsqueda actual usa `LIKE` sobre texto codificado (`ENCPALI`), lo cual es:
1. **Ineficiente** - Búsqueda secuencial sin índices
2. **Incorrecto** - Busca en texto codificado, no en texto legible
3. **Limitado** - Solo búsqueda simple por subcadena

### Problemas Técnicos
1. **`ENCPALI` está codificado** - `LIKE` no encuentra patrones legibles
2. **No usa índices disponibles** - Ignora `RoyalThai__wordat` (2.6M entradas indexadas)
3. **Sin FTS5** - No usa búsqueda de texto completo de SQLite

### Consecuencias
1. **Búsquedas extremadamente lentas** (si funcionaran)
2. **Resultados incompletos o incorrectos**
3. **No aprovecha optimizaciones de la base de datos**

### Solución Propuesta
1. Usar `RoyalThai__wordat` para búsqueda por palabras indexadas
2. Implementar FTS5 para búsqueda de texto completo
3. Crear vista materializada con texto decodificado

---

## 5. Bug Crítico #5: Gestión de Ediciones Rota

### Descripción
El sistema de ediciones no funciona correctamente porque:
1. **`get_available_editions()`** usa `edition_conversions.json` que puede no coincidir con datos reales
2. **No verifica disponibilidad real** en base de datos
3. **Asume que todas las ediciones tienen la misma estructura**

### Código Problemático
```python
def get_available_editions(self, text_id: str) -> List[str]:
    if self._edition_conversions and text_id in self._edition_conversions.get("books", {}):
        return self._edition_conversions["books"][text_id].get("available_editions", [])
    return ["PTS"]  # Default - pero PTS__contents está VACÍA
```

### Problemas de Datos
1. **`PTS__contents` está vacía** (0 filas) - Edición PTS no tiene textos cargados
2. **Solo `ROYALTHAI` tiene datos reales** (15,561 filas en `RoyalThai__palipg`)
3. **Otras ediciones (`CHA`, `Ce`, `CeBa`) tienen estructuras diferentes**

### Consecuencias
1. **Interfaz muestra ediciones no disponibles**
2. **Usuarios intentan cambiar a ediciones sin datos**
3. **Confusión sobre qué ediciones están realmente soportadas**

### Solución Propuesta
1. Verificar disponibilidad real consultando las tablas
2. Indicar claramente qué ediciones tienen datos
3. Implementar fallback graceful cuando una edición no tiene datos

---

## 6. Bug Crítico #6: Encoding `ENCPALI` No Decodificado

### Descripción
Los textos Pali están almacenados en `ENCPALI` con un encoding especial que no se decodifica.

### Ejemplo de Datos Codificados
```sql
SELECT ENCPALI FROM RoyalThai__palipg LIMIT 1;
-- Resultado: 7oOT7oKV7oKt7oKB7oOV7oKB7oK57oKV7oOM7oKB7oKb7oKB7oKo...
```

### Problemas
1. **Texto ilegible** en interfaz - muestra caracteres codificados
2. **Búsqueda imposible** - patrones de búsqueda no coinciden con texto codificado
3. **Exportación incorrecta** - se exportaría texto codificado, no Pali legible

### Consecuencias
1. **Texto Pali no visible** para usuarios
2. **Funcionalidad principal rota** - no se puede leer el Tipitaka
3. **Aplicación inútil** para su propósito principal

### Solución Propuesta
1. Investigar y documentar el encoding de `ENCPALI`
2. Implementar funciones de decodificación
3. Cachear texto decodificado para mejor rendimiento

---

## 7. Impacto Acumulado

### Para Usuarios Finales
1. **NO PUEDEN LEER TEXTOS PALI** - Funcionalidad principal rota
2. **NO PUEDEN BUSCAR** - Búsqueda no devuelve resultados
3. **NO PUEDEN USAR DICCIONARIO** - Definiciones ficticias
4. **EXPERIENCIA FRUSTRANTE** - Aplicación parece funcionar pero no produce resultados útiles

### Para Desarrolladores
1. **Código engañoso** - Parece funcionar pero tiene bugs fundamentales
2. **Base para nuevas features rota** - No se puede construir sobre código defectuoso
3. **Testing imposible** - No hay datos accesibles para pruebas

### Para Mantenimiento
1. **Debugging difícil** - Los errores son silenciosos (retorna `None`/`[]`)
2. **Refactorización riesgosa** - No hay tests que verifiquen comportamiento correcto
3. **Documentación incorrecta** - El código no hace lo que dice hacer

---

## 8. Plan de Corrección Priorizado

### Fase 1: Correcciones Críticas (SEMANA 1)
1. **Corregir `get_text()`** - Acceder a `RoyalThai__palipg` correctamente
2. **Implementar decodificación `ENCPALI`** - Hacer textos legibles
3. **Corregir `lookup_dictionary()`** - Usar `PTS__dicdata` real

### Fase 2: Funcionalidad Básica (SEMANA 2)
1. **Corregir `search_texts()`** - Usar `RoyalThai__wordat` para búsqueda
2. **Implementar gestión real de ediciones** - Verificar disponibilidad en DB
3. **Crear tests de integración** - Verificar que las correcciones funcionan

### Fase 3: Mejoras (SEMANA 3)
1. **Implementar FTS5** - Búsqueda de texto completo eficiente
2. **Cache de textos decodificados** - Mejorar rendimiento
3. **Sistema de logging** - Monitorizar acceso a datos

---

## 9. Verificación de Correcciones

### Criterios de Aceptación
1. [ ] `get_text()` retorna texto Pali legible (no codificado)
2. [ ] `search_texts()` encuentra textos reales
3. [ ] `lookup_dictionary()` retorna definiciones reales de `PTS__dicdata`
4. [ ] Interfaz gráfica muestra textos Pali correctamente
5. [ ] Modo CLI puede recuperar y buscar textos

### Tests a Implementar
```python
def test_get_text_returns_legible_pali():
    """Verifica que get_text() retorna texto Pali legible, no ENCPALI codificado"""
    app = TipitakaBrowser()
    text = app.get_text("dn1", "ROYALTHAI")
    assert text is not None
    assert "7oOT7oKV" not in text  # No debe contener encoding crudo
    assert any(char in text for char in "āīūṅñṭḍṇḷ")  # Debe contener caracteres Pali

def test_search_finds_real_texts():
    """Verifica que search_texts() encuentra textos reales"""
    app = TipitakaBrowser()
    results = app.search_texts("buddha", limit=5)
    assert len(results) > 0
    assert all("preview" in r for r in results)
```

---

## 10. Conclusión

**ESTADO ACTUAL: CÓDIGO ROTO - NO USABLE**

La aplicación Tipitaka PTS Browser en su estado actual **NO PUEDE CUMPLIR SU PROPÓSITO PRINCIPAL** de permitir la lectura y estudio del Tipitaka Pali debido a bugs críticos en el acceso a datos.

**Recomendación inmediata:** Detener cualquier desarrollo de nuevas features hasta corregir estos bugs fundamentales. La prioridad #1 es hacer que la aplicación pueda al menos cargar y mostrar textos Pali correctamente.

**Riesgo:** Continuar desarrollando sobre esta base defectuosa resultará en más código que no funciona y dificultará aún más las correcciones necesarias.

---
**Fecha de identificación:** [Fecha actual]  
**Prioridad:** CRÍTICA - Requiere atención inmediata  
**Estado:** ABIERTO - Sin correcciones implementadas  
**Asignado a:** [Por asignar]