---
name: integridad-datos
description: Caza la corrupción silenciosa del dato — la que el validador NO puede ver porque el par PTS↔CST que recibe es coherente consigo mismo. Invocar antes y después de tocar el texto, el Excel maestro o cualquier alineador, y siempre antes de gastar API.
---

# Integridad del dato

## El punto ciego

El validador (Modelo B) coteja un par PTS↔CST y dice si concuerdan. **No puede detectar dos cosas**:

1. que el par que recibe sea **el equivocado** — si los dos lados son coherentes *entre sí*, aprueba,
   aunque no correspondan a la fila;
2. que el texto que se le entrega esté **corrompido** — si la corrupción produce prosa legible.

Todos los defectos graves de este proyecto han vivido en ese punto ciego, y **ninguno lo destapó el
validador**. Esta skill existe para cubrirlo.

## El caso que hay que tener siempre presente

`sutta_hash.tokens` partía la elisión del impreso PTS por el apóstrofo y descartaba la letra suelta
como «ruido de un carácter»:

```
n' atthi kammaṃ   («NO hay acción»)   →   atthi kammaṃ   («hay acción»)
```

**Borraba la negación.** El texto seguía siendo pāli legible y perfectamente plausible; sólo
afirmaba lo contrario del original. 12.561 casos en DN, MN y AN. SN apenas usa la convención (15 en
cinco volúmenes), y por eso el defecto atravesó **cinco volúmenes cerrados** sin que nada lo
señalara. Salió por casualidad, al preparar el dossier de un rechazo de Gemini que resultó tener
razón.

Moraleja operativa: **una transformación de texto nunca debe poder perder una palabra.** Si un paso
descarta tokens «cortos», «raros» o «ruido», hay que demostrar que no descarta significado.

## Cómo se usa

```bash
python3 check_integrity.py            # todas las invariantes
python3 check_integrity.py -v         # lista cada incidencia
python3 check_integrity.py --quick    # salta las que leen la BD entera
python3 audit_injectivity.py          # aparte: ¿cada fila tiene SU marcador?
```

Devuelve 0 si todo pasa, 1 si alguna invariante **de nivel fallo** tiene incidencias. Las de nivel
*aviso* se listan pero no hacen fallar: tienen excepciones legítimas conocidas.

**Cuándo correrlo, sin excepción:**
- antes y después de tocar `sutta_hash.py` o cualquier preparación de texto;
- antes y después de escribir en `PTS_Reference_Complete_Canon.xlsx`;
- al cambiar un alineador, **junto con** `audit_injectivity.py`;
- **antes de gastar API**: validar sobre dato corrupto es tirar el dinero y, peor, produce firmas
  que luego hay que deshacer.

## Las invariantes, y el incidente real que motiva cada una

| invariante | incidente |
|---|---|
| `tokens_no_pierden_palabras` | el apóstrofo, arriba. Ninguna palabra puede desaparecer al tokenizar |
| `negacion_preservada` | corolario sobre el texto real de la BD, no sobre casos de laboratorio |
| `prefijo_de_ref_coincide_con_nikaya` | una fila de AN llevaba `S i 68,4`, una referencia del Saṃyutta |
| `pagina_coincide_con_la_ref` | página y referencia editadas por separado dejan de decir lo mismo |
| `nombre_sin_residuo_de_parseo` | el importador de AN partió el `Sutta #` mal: 166 nombres empezaban por `-5 [AN…` y 1126 por `: ` |
| `clave_sutta_no_duplicada` | 36 claves duplicadas en AN impedían emparejar por clave |
| `sutta_num_coincide_con_raw_id` | *aviso*: `Raw ID` es la fuente; divergir sólo vale si hubo re-identificación deliberada (S ii, SN 17 desplazado +7) |
| `estado_coherente_con_validation` | `Estado` es lo que se publica; si se edita aparte de `Validation`, miente |
| `vri_ref_bien_formada_y_existente` | la clave canónica del lado CST no puede apuntar a un paranum inexistente |
| `confirmado_exige_procedencia` | sin validador nada es CONFIRMADO: una firma sin procedencia válida es una firma sin respaldo |
| `paginas_monotonas_por_volumen` | un salto de página hacia atrás delata fila mal colocada o referencia ajena |

## Cómo añadir una invariante

Cada vez que aparezca un defecto de integridad **nuevo**, se añade aquí antes de darlo por
arreglado. Con el decorador:

```python
@check('nombre_corto', 'El incidente REAL que lo motiva, con cifras.', nivel='fallo')
def inv_lo_que_sea(verbose=False, quick=False):
    return [ ... ]     # lista de incidencias; vacía = pasa
```

Dos exigencias de estilo, y no son cosméticas:

- **El `porque` cita el incidente real, con cifras.** Una invariante sin historia detrás se borra en
  la primera limpieza porque nadie recuerda para qué estaba.
- **`nivel='aviso'` si hay excepciones legítimas.** Una comprobación que grita en falso acaba
  ignorándose, y entonces no protege de nada.

## Lo que esta skill NO cubre

- **La inyectividad de las asignaciones** — va en `audit_injectivity.py` (¿dos filas sobre el mismo
  marcador?). Correr los dos.
- **La corrección filológica de un emparejamiento.** Eso es el validador y, en desacuerdo, el
  arbitraje humano. Aquí sólo se comprueba que el dato no esté roto por el código.
- **Lo que aún no se ha procesado.** KN no tiene numeración en `Sutta #` y sus obras tienen
  paginación propia; las invariantes lo tienen en cuenta para no generar ruido.
