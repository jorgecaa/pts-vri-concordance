# Plan de Resolución — 26 entradas "Buenas" (4/6) y "Aceptables" (3/6)

## Diagnóstico

De 98 pruebas críticas, 72 son perfectas/fuertes (5-6/6) y 26 tienen
puntuación 3-4/6. **Ninguna tiene página errónea.** Las pérdidas de
puntos se deben a tres causas:

| Causa | Entradas | Descripción |
|-------|----------|-------------|
| **A. Keyword fallido** | ~15 | Nombres compuestos pali (Sabbāsava, Vatthūpama) no generan keywords de 4+ chars que aparezcan en el cuerpo del texto |
| **B. RTE gap** | ~8 | La edición Royal Thai no tiene cross-reference PTS para esa página |
| **C. Página título** | ~3 | SN 22.1, SN 35.1, MN 7 empiezan en páginas de front-matter de volumen sin marcador de sutta |

---

## Plan de acción

### A. Reemplazar keyword matching por incipit matching

**Problema**: `norm("Sabbāsava")` → `"sabbasava"` → keywords `["sabb", "asav"]`
no aparecen en el texto porque el texto dice `āsavā` (con diacrítico) y la
ventana de búsqueda es limitada.

**Solución**: Para cada sutta, extraer el **incipit** (primeras 10-15 palabras
reales del texto PTS en la página) y compararlo contra un incipit conocido
del sutta. El incipit es un fingerprint único mucho más fiable que keywords.

**Implementación**:
1. Para entradas ya verificadas (DN/MN), extraer el incipit de la página PTS
2. Guardar en el Excel columna `Incipit` con primeras 80 chars de contenido
3. Para entradas no verificadas, buscar el incipit en la página candidata
4. Si el incipit aparece, confirmar; si no, buscar en páginas ±3

**Impacto**: ~15 entradas pasan de 4/6 a 5-6/6.

### B. Marcar gaps RTE como conocidos

**Problema**: La edición Royal Thai tiene ~4,300 PTS cross-references pero
no cubre todas las páginas. Páginas como D i 1, M i 12, S ii 1 no tienen
`(pts. X r, N)`.

**Solución**: No es un error — es una limitación del RTE. Marcar estas
entradas como `RTE_GAP` en lugar de penalizarlas. La verificación contra
la BD PTS ya confirma la página.

**Implementación**:
1. Listar todas las páginas PTS que SÍ tienen RTE ref (ya lo tenemos)
2. Para entradas sin RTE, verificar si la página adyacente SÍ tiene RTE
   (confirmando que estamos en la zona correcta)
3. Si la página ±1 tiene RTE, marcar como `RTE_NEAR` (confirmación por adyacencia)

**Impacto**: ~8 entradas ya no pierden el punto RTE.

### C. Verificar páginas título por contenido en página siguiente

**Problema**: SN 22.1 (S iii 1), SN 35.1 (S iv 1), MN 7 (M i 36) están en
páginas de front-matter (título de volumen, namo tassa, etc.). El contenido
real del sutta empieza en la misma página después del front-matter, o en la
página siguiente.

**Solución**: Para páginas de inicio de volumen (page 1), verificar que:
1. La página contiene el título del volumen/saṃyutta correcto
2. El contenido del sutta aparece en la misma página (después del header)
   o en página 2-3

**Implementación**:
1. Detectar páginas de inicio de volumen (page_no == 1 con HEAD corto)
2. Buscar el título del saṃyutta/vagga en la página
3. Buscar el incipit del sutta en páginas 1-3
4. Confirmar la página correcta

**Impacto**: ~3 entradas verificadas.

---

## Prioridad y esfuerzo

| Fase | Qué | Entradas | Esfuerzo | Impacto |
|------|-----|----------|----------|---------|
| **1** | Incipit matching | ~15 | Medio | Alto — elimina falsos negativos |
| **2** | RTE adjacency | ~8 | Bajo | Medio — documenta limitación |
| **3** | Title page handling | ~3 | Bajo | Bajo — casos ya conocidos |

## Resultado esperado

Después de las 3 fases, las 26 entradas 3-4/6 deberían pasar a 5-6/6,
llevando el promedio general de 5.0 a **≥5.5/6** y eliminando todos los
casos "fair" (3/6).
