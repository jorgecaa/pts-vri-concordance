# Gramática de marcadores de inicio de sutta (PTS canon, `edition='mula'`)

Formato de línea de página PTS analizado por [`pts_markers.py`](../pts_markers.py) con **pyparsing**
(regla del proyecto; buenas prácticas en `doc/pyparsing/pyparsing/ai/best_practices.md`).

Cada `find_markers_<nikaya>(text)` recorre las líneas de la página y devuelve `(nº_línea, tag)`
para las líneas que **inician un sutta**. La gramática se verificó **equivalente** a la versión
regex anterior sobre las 3.219 páginas reales (0 divergencias; ver `scratchpad/dev_markers.py`).

## Tokens comunes (BNF)

```
digits      ::= <uno o más dígitos>            # pp.Word(nums)
dot         ::= "."
ws          ::= <uno o más espacios/tabs>      # pp.White(" \t"), OBLIGATORIO (regex \s+)
nonspace    ::= <un carácter no-espacio>       # pp.CharsNotIn(" \t", exact=1)  (regex \S)
evam        ::= ("E"|"e") "va" ("m"|"M")       # NO casa "ṃ" (igual que la regex [Ee]va[mM])
sutam       ::= "suta" ("m"|"M")               # NO casa "ṃ"
evam_sutam  ::= evam ...(SkipTo)... sutam      # se BUSCA en la línea (no anclado)
```

> Nota filológica: `evam`/`sutam` usan la clase `m|M` y **no** el niggahīta `ṃ`, replicando
> exactamente la regex previa. Por eso "Evam me sutaṃ" NO casa como `evam`; en DN los marcadores
> se detectan por `evam_num` (línea numerada), no por `evam`.

## Reglas por Nikāya

Las expresiones de prefijo se aplican **ancladas al inicio** de la línea (`.matches`), salvo
`evam_sutam` y `verse_end` que se **buscan** en la línea (`.scan_string`).

```
# DN — find_markers_dn
dn_line     ::= evam_sutam                         → "evam"        (buscado)
              | dn_evam_num                         → "evam_num"
dn_evam_num ::= Combine(digits dot [digits] [dot]) ws evam
# fallback (si no hubo marcadores en la página), sobre la línea sin corchetes y en minúsculas:
dn_title    ::= Combine(roman [dot]) ws nonspace    → "title"
roman       ::= <uno o más de i v x l c>

# MN — find_markers_mn
mn_line     ::= mn_num_only  (línea completa, len ≤ 5)   → "num"       # p.ej. "1."
              | num_dot_txt                               → "num_txt"
mn_num_only ::= digits [dot]                              # parse_all (toda la línea)
num_dot_txt ::= Combine(digits dot) ws nonspace          # regex ^\d+\.\s+\S

# SN — find_markers_sn
sn_line     ::= sn_id                              → "sn_id"     # "N (M) …" / "N. (M) …"
              | sn_section                         → "section"   # "§ N …"
              | num_dot_txt (len > 5)              → "num"
sn_id       ::= digits [dot] "(" digits
sn_section  ::= "§" ws digits

# SN I — find_markers_sn1  (sn1_markers.py; gramática propia, ver abajo)
sn1_line    ::= sec_marker                         → "section"   # "§ 4. Na santi."
              | bare_marker                        → "bare"      # "4. Nandano."  (§ perdido)
sec_marker  ::= section numlist [dot] name
bare_marker ::= numlist dot name                   # exige sangría ≥8, sin "║", len ≤48,
                                                   #  nombre con mayúscula y ≥3 letras
section     ::= "§"{1,2}
numlist     ::= digits ( ("," | "-"+) digits )*    # "4" | "4,5" | "103--108"

# SN II — find_markers_sn2  (sn2_markers.py; gramática propia, ver abajo)
sn2_line    ::= lead item*                         → "marker"   # "1 (1) Desanā" (sin puntos)
              | item+                              → "cont"     # "(12) Dhītā (13) Pajāpati"
lead        ::= "(" numrange ")" &group | numrange  # "(64)" solo si le sigue un grupo
item        ::= group | remark | name
group       ::= "(" numrange [")"]                 # el ")" lo pierde el OCR
remark      ::= "(" ¬digit … [")"]                 # "(or Miḷhaka? )" — se ignora
numrange    ::= digits [ "-" digits ]              # "38-43"

# AN — find_markers_an
an_line     ::= num_dot_txt                        → "num"

# KN — find_markers_kn(text, vol)
#  · Thag/Thig (vol ∈ {Th, Th & Th, Thi, Thī}):
kn_thag     ::= verse_end (buscado)                → "verse_end"  # "║ N ║"
              | fallback: primera línea de contenido (len ≥ 8, no all-caps) → "content"
#  · Ud/It/Sn/Dh/Kh/Vv/Pv:
kn_line     ::= num_dot_txt → "num" | evam_sutam(buscado) → "evam"
#  · Ja/Ap/Bv/Cp/Patis/Nidd (si lo anterior no dio nada): num_dot_txt → "num"
#  · fallback final: primera línea de contenido (len ≥ 6, no all-caps-con-|) → "content"
verse_end   ::= "║" digits "║"
all-caps    ::= Word( A-Z, espacio, tab, "-", ".", "║" [, "|"] )   # línea de cabecera a ignorar
```

## Notas de implementación (best_practices)

- `pp.ParserElement.set_default_whitespace_chars(" \t")` — el salto de línea es significativo
  (se procesa línea a línea), solo espacios/tabs son saltables.
- El prefijo numérico de `dn_evam_num`/`dn_title` va en `pp.Combine` para que los elementos
  opcionales internos no consuman el `ws` obligatorio siguiente (un `Optional` avanza sobre el
  whitespace que salta aunque su contenido no case).
- `set_name()` en todas las expresiones para diagramas de vías y mejores mensajes de error.
- Tests mínimos con `ParserElement.run_tests` en el `__main__` de `pts_markers.py`.

## Mantenimiento

Al cambiar la gramática, **actualiza este documento** y vuelve a correr el test de equivalencia
(`scratchpad/dev_markers.py`) o un test dedicado antes de regenerar el Excel.


## SN I — `sn1_markers.py` (nota aparte)

SN I no comparte la gramática de SN II–V. Sus marcadores son **`§ N. Nombre.`** centrados, con el
número **reiniciado en cada vagga** — un cuarto sistema de coordenadas, ajeno al `Sutta #` del
Excel, al canónico y al `cst_paranum`. `find_markers_sn1(text)` devuelve
`[(nº_línea, [números], nombre, tag)]`.

Dos variantes hay que aceptar o se pierden **6 de los 271** suttas del volumen:

| Variante | Ejemplo | Dónde |
|---|---|---|
| Rango con coma (un encabezado, dos suttas) | `§§ 4,5. Saṅgāme dve vuttāni.` | S i 82 |
| Marcador «desnudo»: el `§` se perdió en el OCR | `4. Nandano.` | S i 23, 52, 56, 73, 124 |

El marcador desnudo se discrimina del **número de párrafo** (margen izquierdo, sangría ~5) y del
**pada de gāthā** (lleva `║`) por: sangría ≥ 8, ausencia de `║`, longitud ≤ 48 y nombre con
mayúscula inicial.

**Agrupación en vaggas:** dentro de un vagga el `§` crece estrictamente, así que *un número que no
crece abre vagga nuevo* (`build_vaggas`). Es la única regla fiable, porque el `§1` de arranque es
justamente uno de los que el OCR puede haber perdido. Con esto la estructura hallada cuadra al
100% con el front matter de Feer (`samyutta-vol-I-info.txt`): **28 vaggas, 271 suttas y la página
de arranque de cada vagga**.


## SN II — `sn2_markers.py` (nota aparte)

S ii no comparte gramática ni con S i ni con S iv–v: el marcador es **`N (M) Nombre` sin puntos**,
con `N` = nº corrido dentro del saṃyutta (reinicia en cada saṃyutta) y `M` = posición en el vagga.
`find_markers_sn2(text)` devuelve `[(nº_línea, [nº corridos], [(pos, nombre)], tag)]`.

Variantes que hay que aceptar (cada una cuesta suttas si se ignora):

| Forma | Ejemplo | Dónde |
|---|---|---|
| estándar | `1 (1) Desanā` | |
| sin posición | `1 Nakhasikhā` | saṃyuttas de un vagga único (S ii 133) |
| grupo TRAS el nombre | `8 Ovādo (3)` | S ii 203, 205, 208 |
| desambiguador de cola | `13 (3) Samaṇa-brāhmaṇā (1)` | |
| con `║` de cola | `68 (8) Kosambi ║` | S ii 115, 260, 282 |
| comentario no numérico | `5 (5) Piḷhika (or Miḷhaka? )` | S ii 228 |
| sin nombre | `71 (1)` | S ii 129 |
| rango | `72-80 (2-10)` | S ii 129 |
| rango multi-nombre + continuación | `38-43 (8) Pitā (9) Bhātā …` / `(12) Dhītā (13) Pajāpati` | S ii 243 |
| nº entre paréntesis | `(64) (4) Atthirāgo` | S ii 101 |
| paréntesis perdido (OCR) | `40 (10 Cetanā (3)` | S ii 66 |

### Tres reglas que no son evidentes

1. **El recuento lo fija el rango del nº corrido** (`38-43` → 6 suttas), nunca el número de grupos
   `(M) Nombre`: así el desambiguador de cola no inventa un sutta ni el rango multi-nombre se queda
   corto.
2. **La sangría mínima depende de la forma.** `N (M) …` es inequívoco y aparece incluso al margen
   (son los **miembros peyyāla** de un rango impresos como texto corrido, S ii 234 y 243), mientras
   `N Nombre` sin paréntesis es ambiguo: **2178 párrafos** empiezan así a sangría 5–8 y los 39
   marcadores reales están a sangría ≥ 27.
3. **Un rango puede ser solo el ENCABEZADO de un grupo** cuyos miembros se imprimen después uno a
   uno (S ii 250: `12-20 (2-10)` y luego `13 (3) Viññānaṃ`…`20 (10) Khandha`). Por eso
   `collect_suttas` acumula en un dict por nº corrido donde **el marcador individual pisa al del
   rango**; si no, se duplican 9 suttas.

**Saṃyuttas:** el **nº 1 abre saṃyutta nuevo**. No vale la regla de S i («un nº que no crece»),
porque aquí los miembros peyyāla se reimprimen con números ya vistos y partirían el saṃyutta.

Con esto la estructura hallada cuadra al 100% con el front matter de Feer
(`samyutta-vol-II-info.txt`): **10 saṃyuttas (XII–XXI), 27 vaggas, 286 suttas**
(93/11/39/20/13/43/22/21/12/12) y la página de arranque de cada saṃyutta.
