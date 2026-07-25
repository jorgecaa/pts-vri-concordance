#!/usr/bin/env python3
"""
sn2_markers — gramática de marcadores de sutta de **SN II** (S ii, `book_no=13`).

Parseo del formato con **pyparsing** exclusivamente (regla del proyecto; gramática documentada
en `docs/grammar.md`).

S ii no usa ni el `§ N.` de S i ni el `N. (M) Nombre` de S iv–v: aquí el marcador es
**`N (M) Nombre` sin puntos**, donde `N` es el nº corrido dentro del saṃyutta (reinicia en cada
saṃyutta) y `M` la posición dentro del vagga. Variantes reales del volumen, todas necesarias:

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
| rango con nombres | `13-20 (3-10) Suvaṇṇanikkha -- Janapadakalyāṇī` | S ii 233 |
| rango multi-nombre | `38-43 (8) Pitā (9) Bhātā (10) Bhagini (11) Puttā` | S ii 243 (+ continuación) |
| nº entre paréntesis | `(64) (4) Atthirāgo` | S ii 101 |
| paréntesis perdido (OCR) | `40 (10 Cetanā (3)` | S ii 66 |
| nombre entre llaves | `12 {Paraṃmaraṇaṃ}` | S ii 222 |

Tres principios de diseño, cada uno aprendido de un fallo real:

1. **El recuento lo fija el rango del nº corrido** (`38-43` → 6 suttas), NUNCA el número de grupos
   `(M) Nombre`. Así el desambiguador de cola no inventa un sutta ni el rango multi-nombre se
   queda corto.
2. **Los items van en cualquier orden** tras el nº corrido: `grupo`, `nombre` y `comentario`
   entremezclados. Exigir `(M)` antes del nombre perdía los 3 `Ovādo` de Kassapa.
3. **Un rango puede ser un ENCABEZADO de grupo** cuyos miembros se imprimen luego individualmente
   (S ii 250: `12-20 (2-10)` y después `13 (3) Viññānaṃ`…`20 (10) Khandha`). Por eso los suttas se
   acumulan en un dict por nº corrido donde el marcador individual PISA al del rango
   (`collect_suttas`); si no, se duplican 9.

`find_markers_sn2(text)` devuelve `[(nº_línea, [nº corridos], [(pos, nombre)], tag)]`, con
`tag` ∈ {'marker', 'cont'}; un `cont` (línea que abre con `(M) Nombre`, sin nº corrido) es
continuación del marcador anterior y aporta los nombres que faltan de su rango.
"""
import pyparsing as pp

pp.ParserElement.set_default_whitespace_chars(" \t")

# La sangría mínima depende de la FORMA, porque las dos convive en el volumen:
#  · `N (M) …` es inequívoco (ningún párrafo lleva posición entre paréntesis) y aparece incluso al
#    margen: son los MIEMBROS PEYYĀLA de un rango, impresos como texto corrido (S ii 234, 243).
#  · `N Nombre` sin paréntesis es ambiguo — 2178 párrafos empiezan así a sangría 5–8 — y solo es
#    marcador cuando va centrado (los 39 reales están a sangría ≥ 27).
MIN_INDENT_POS = 5    # forma con "(M)"
MIN_INDENT_BARE = 20  # forma sin paréntesis
MAX_LEN = 60

_num = pp.Word(pp.nums).set_name("num")
_dash = pp.Word("-–—", min=1).set_name("dash")
_numrange = pp.Group(_num + pp.Opt(pp.Suppress(_dash) + _num)).set_name("numrange")

# grupo de posición "(M)" / "(M-N)"; el ")" es OPCIONAL (el OCR lo pierde)
_group = pp.Group(pp.Suppress("(") + _numrange("pos") + pp.Opt(pp.Suppress(")")))("group")
# nº corrido al frente: "13" | "38-43" | "(64)". La forma entre paréntesis solo cuenta como nº
# corrido si le SIGUE un grupo de posición — así `(64) (4) Atthirāgo` es marcador pero
# `(2) Rūpam` es continuación del rango anterior, no un sutta nº 2.
_lead_paren = (pp.Suppress("(") + _numrange + pp.Suppress(")") + pp.FollowedBy(_group))
_lead = (_lead_paren | _numrange).set_name("lead")
# comentario no numérico entre paréntesis: "(or Miḷhaka? )" — se ignora
_remark = pp.Suppress(pp.Regex(r"\((?!\d)[^)\n]*\)?"))
# nombre: texto hasta el siguiente "(" o el fin de línea
_name = pp.Regex(r"[^(\n]+")("name")

_item = (_group | _remark | _name).set_name("item")
_marker = (_lead("lead") + pp.Group(pp.ZeroOrMore(_item))("items")).set_name("marker")
_cont = pp.Group(pp.OneOrMore(_item))("items").set_name("cont")

_LETTER = ("ABCDEFGHIJKLMNOPQRSTUVWXYZĀĪŪṄÑṆṬḌḶŚ"
           "abcdefghijklmnopqrstuvwxyzāīūṅñṇṭḍḷṃ{[")


def _clean(s):
    return (s or '').strip().strip('║').strip(' .{}[]').strip()


def _parse(expr, s):
    try:
        return expr.parse_string(s, parse_all=True)
    except pp.ParseException:
        return None


def _expand(rng):
    """`["38","43"]` → `[38..43]`. Desenvuelve los `Group` anidados del nombre de resultado."""
    while len(rng) and not isinstance(rng[0], str):
        rng = rng[0]
    a = int(rng[0]); b = int(rng[1]) if len(rng) > 1 else a
    return list(range(a, b + 1)) if b >= a else [a]


def _pairs(items):
    """Empareja items en `[(pos, nombre)]`: cada grupo `(M)` toma el nombre que le sigue; un
    nombre sin grupo delante va con `pos=None`; un grupo sin nombre detrás aporta solo posición."""
    out, pending = [], None
    for it in items:
        if isinstance(it, str):                       # nombre
            nm = _clean(it)
            if not nm or nm[0] not in _LETTER:
                continue
            out.append((pending, nm))
            pending = None
        else:                                          # grupo de posición
            if pending is not None:
                out.append((pending, ''))
            pending = _expand(it)[0]
    if pending is not None:
        out.append((pending, ''))
    return out


def find_markers_sn2(text):
    """Marcadores de una página de S ii: `[(line_no, [nums], [(pos, name)], tag)]`."""
    out = []
    for i, line in enumerate(text.split("\n"), start=1):
        s = line.rstrip("\r").rstrip()
        indent = len(s) - len(s.lstrip())
        s = s.strip().rstrip('║').strip()             # el `║` de cola es tipográfico
        if not s or '║' in s or len(s) > MAX_LEN:
            continue
        if s[0] not in "0123456789(":
            continue
        has_pos = next(_group.scan_string(s), None) is not None
        if indent < (MIN_INDENT_POS if has_pos else MIN_INDENT_BARE):
            continue
        if s.startswith("(") and not s[1:2].isdigit():  # "(Section I …)" y otros encabezados
            continue

        r = _parse(_marker, s)
        if r is not None and r.get("lead") is not None:
            out.append((i, _expand(r["lead"]), _pairs(r["items"]), 'marker'))
            continue
        r = _parse(_cont, s)
        if r is not None:
            names = [(p, n) for p, n in _pairs(r["items"]) if n]
            if names:
                out.append((i, [], names, 'cont'))
    return out


def collect_suttas(rows):
    """`[(page, line, nums, names, tag)]` en orden de lectura → `[sutta]` en orden canónico.

    El nº corrido reinicia en cada saṃyutta, así que **el nº 1 abre saṃyutta nuevo** (los 9
    reinicios de S ii están todos presentes y caen en las páginas que da Feer). No sirve la regla
    de S i («un nº que no crece»): aquí los miembros peyyāla de un rango se reimprimen con números
    ya vistos (S ii 234, 243) y partirían el saṃyutta en dos.

    Dentro de un saṃyutta los suttas se indexan por nº corrido y **el marcador individual pisa al
    de un rango** (un rango puede ser solo el encabezado de un grupo que luego se imprime sutta a
    sutta). Cada sutta sale con `page`, `line`, `num`, `pos`, `name` y `from_range`.
    """
    sams, cur, prev = [], {}, 0
    order = []
    for pg, ln, nums, names, tag in rows:
        if tag == 'cont':
            # aporta nombres a los suttas del rango anterior que aún no lo tengan
            for pos, nm in names:
                for n, rec in cur.items():
                    if rec['pos'] == pos and not rec['name']:
                        rec['name'] = nm
                        rec['page'], rec['line'] = pg, ln
                        break
            continue
        if cur and nums[0] == 1:                       # el nº 1 abre saṃyutta nuevo
            sams.append((order, cur)); cur, order = {}, []
        pairs = list(names)
        for k, n in enumerate(nums):
            pos, nm = (pairs[k] if k < len(pairs) else (None, ''))
            if len(nums) > 1 and k >= len(pairs):
                pos, nm = (None, '')
            rec = {'page': pg, 'line': ln, 'num': n, 'pos': pos, 'name': nm,
                   'from_range': len(nums) > 1}
            if n in cur and cur[n]['from_range'] and not rec['from_range']:
                cur[n] = rec                            # el individual pisa al del rango
            elif n not in cur:
                cur[n] = rec; order.append(n)
        prev = nums[-1]
    if cur:
        sams.append((order, cur))

    out = []
    for si, (_order, d) in enumerate(sams, start=1):
        for n in sorted(d):
            rec = dict(d[n]); rec['sam_idx'] = si
            out.append(rec)
    return out, sams
