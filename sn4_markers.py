#!/usr/bin/env python3
"""
sn4_markers — gramática de marcadores de sutta de **SN IV** (S iv, `book_no=15`).

Parseo con **pyparsing** exclusivamente (regla del proyecto; ver `docs/grammar.md`).

S iv **no es homogéneo**: sus 10 saṃyuttas se imprimen bajo dos convenciones, y hay que tratarlas
por separado (regla (5) de `CLAUDE.md`).

| régimen | saṃyuttas | forma | ejemplo |
|---|---|---|---|
| **A — con posición** | XXXV, XXXVI, XXXVII, XLIII | `N (M) Nombre` | `53 (1) Avijjā` |
| **B — escueta** | XXXVIII, XXXIX, XL, XLI, XLII, XLIV | `N Nombre` | `16 Dukkaram` |
| **C — `saṭṭhi-peyyāla`** | XXXV, pp. 148-156 | `(M) Nombre`, **sin nº corrido** | `(2) Chandena2` |

El régimen C es el que Feer explica en su introducción: imprime **20 números corridos (167-186)**
para las **60** suttantas del peyyāla («Peyyālo saṭṭhiko vutto / Suttantāni saṭṭhi», dice su uddāna),
y en las líneas intermedias **elide el nº corrido** y deja sólo la posición. Exigir dígito inicial
dejaba 12 filas del Excel sin marcador.

En los dos, `N` es el **nº corrido dentro del saṃyutta**; en el régimen A, `M` es además la posición
dentro del vagga. La diferencia no es sólo de forma: en el régimen B **el número desnudo colisiona
con los números de párrafo del cuerpo** (`1 Evaṃ me sutaṃ…`), que también abren línea con un
dígito. Lo que los separa es la **caja**: el marcador va *centrado* (sangría 19-29) y el cuerpo a
sangría 5 (primera línea) o 0 (continuación). De ahí que `MIN_INDENT_BARE` sea alto y que la forma
`N (M)`, inequívoca por sí misma, admita sangría menor.

Hay que descartar además tres cosas que también van centradas:
- las cabeceras de libro y capítulo (`BOOK IV JAMBUKHĀDAKA-SAṂYUTTAṂ`), en **versales**;
- las líneas de elisión (`Sāvatthi ║ la ║`), que no llevan número al frente;
- los uddāna.

`find_markers_sn4(text)` devuelve `[(nº_línea, [nº corridos], [(pos, nombre, bruto)], tag)]`, con
`tag` ∈ {'marker', 'cont'} — misma interfaz que `sn3_markers`, para que el resto del pipeline
(`collect_suttas`, el alineador, la calibración de líneas) valga sin cambios.
"""
import pyparsing as pp

pp.ParserElement.set_default_whitespace_chars(" \t")

MIN_INDENT_POS = 5      # forma «N (M) Nombre»: inequívoca, el paréntesis ya la identifica
# Forma escueta «N Nombre»: los números de párrafo del cuerpo están a sangría 5 y los marcadores
# reales de este volumen van de 19 a 29. Un umbral bajo se tragaría el cuerpo entero.
MIN_INDENT_BARE = 15
MAX_LEN = 60

_num = pp.Word(pp.nums).set_name("num")
_dash = pp.Word("-–—", min=1).set_name("dash")
_numrange = pp.Group(_num + pp.Opt(pp.Suppress(_dash) + _num)).set_name("numrange")

_group = pp.Group(pp.Suppress("(") + _numrange("pos") + pp.Opt(pp.Suppress(")")))("group")
# nombre entre paréntesis, sin posición: «(Anicca vaggo)»
_pname = pp.Regex(r"\(\s*[^\d)][^)\n]*\)?")("pname")
# comentario no numérico que NO es el nombre: «(or Abhijānaṃ)», «(aṭṭhārasa)»
_remark = pp.Suppress(pp.Regex(r"\(\s*(?:or|vā|a[ṭt][ṭt]h[āa]rasa|dv[āa]dasa)\b[^)\n]*\)?"))
_name = pp.Regex(r"[^(\n]+")("name")

_lead = _numrange.set_name("lead")
_item = (_group | _remark | _pname | _name).set_name("item")
_marker = (_lead("lead") + pp.Group(pp.ZeroOrMore(_item))("items")).set_name("marker")
# régimen C: la línea abre con la POSICIÓN entre paréntesis y sin nº corrido — «(2) Chandena2»
_lead_pos = (pp.Suppress("(") + _numrange("leadpos") + pp.Suppress(")"))
_marker_pos = (_lead_pos + pp.Group(pp.ZeroOrMore(_item))("items")).set_name("marker_pos")
_cont = pp.Group(pp.OneOrMore(_item))("items").set_name("cont")

_LETTER = ("ABCDEFGHIJKLMNOPQRSTUVWXYZĀĪŪṄÑṆṬḌḶŚ"
           "abcdefghijklmnopqrstuvwxyzāīūṅñṇṭḍḷṃ{[")


def _clean(s):
    return (s or '').strip().strip('║').strip(' .{}[]()-–—').strip()


def _parse(expr, s):
    try:
        return expr.parse_string(s, parse_all=True)
    except pp.ParseException:
        return None


def _expand(rng):
    while len(rng) and not isinstance(rng[0], str):
        rng = rng[0]
    a = int(rng[0])
    b = int(rng[1]) if len(rng) > 1 else a
    return list(range(a, b + 1))


def _pairs(items):
    """Empareja items en `[(pos, nombre, bruto)]`; `bruto` conserva los guiones (ver
    `sn3_markers._pairs`: el guión de truncamiento distingue regímenes de nombres)."""
    out, pending = [], None
    for it in items:
        if isinstance(it, str):
            nm = _clean(it)
            raw = (it or '').strip().strip('║').strip(' .{}[]()').strip()
            if not nm or nm[0] not in _LETTER:
                continue
            out.append((pending, nm, raw)); pending = None
        else:
            if pending is not None:
                out.append((pending, '', ''))
            pending = _expand(it)[0]
    if pending is not None:
        out.append((pending, '', ''))
    return out


_OCR_DIGIT = {'O': '0', 'o': '0', 'l': '1', 'I': '1', '|': '1'}


def _repair_leading(s):
    """Repara letras leídas por dígitos en el nº corrido: `2O (6) Sīlavā` → `20 (6) Sīlavā`.

    El OCR de la BD mete `O` por cero en los marcadores (ya visto en S v 397, `4O. (10) Nandiya`).
    Sin esto se pierde el sutta entero: aquí faltaba el nº 20 del Mātugāma-saṃyutta, y con él la
    cuenta del volumen no cerraba contra el front matter de Feer (33 en vez de 34).

    Se aplica **sólo al primer token**, **sólo si no era ya un número válido** y **sólo si contiene
    al menos un dígito de verdad**. Esta última condición es imprescindible: sin ella una `I` o una
    `l` inicial de *nombre* («Iddhipāda») se convertía en un `1` y se colaban 42 marcadores falsos.
    """
    i = 0
    while i < len(s) and (s[i].isdigit() or s[i] in _OCR_DIGIT):
        i += 1
    head = s[:i]
    if not head or head.isdigit() or not any(c in _OCR_DIGIT for c in head):
        return s
    if not any(c.isdigit() for c in head):
        return s
    fixed = ''.join(_OCR_DIGIT.get(c, c) for c in head)
    return fixed + s[i:] if fixed.isdigit() else s


def _is_header(t):
    """Cabecera de libro/capítulo: va centrada como un marcador, pero en versales."""
    letters = [c for c in t if c.isalpha()]
    return len(letters) > 4 and sum(c.isupper() for c in letters) / len(letters) > 0.8


def find_markers_sn4(text):
    """Marcadores de una página de S iv: `[(line_no, [nums], [(pos, name, raw)], tag)]`."""
    out = []
    for i, line in enumerate(text.split('\n'), start=1):
        raw = line.replace('⁣', '')
        indent = len(raw) - len(raw.lstrip())
        s = raw.strip().strip('║').strip()
        if not s or len(s) > MAX_LEN:
            continue
        if _is_header(s) or 'uddān' in s.lower() or s.startswith('['):
            continue
        s = _repair_leading(s)
        if not s[0].isdigit():
            if s[0] != '(':
                continue
            r = _parse(_marker_pos, s)
            if r is None or r.get("leadpos") is None or indent < MIN_INDENT_BARE:
                continue
            names = _pairs(r["items"])
            if not any(n for _p, n, _rw in names):
                continue
            pos = _expand(r["leadpos"])[0]
            # sin nº corrido: hereda el del marcador anterior (es una posición suya)
            out.append((i, [], [(pos, n, rw) for _p, n, rw in names], 'marker'))
            continue
        # La sangría exigida depende de la FORMA: «N (M)» se identifica sola; «N Nombre» sólo vale
        # centrado, porque compite con los números de párrafo del cuerpo.
        r = _parse(_marker, s)
        if r is None or r.get("lead") is None:
            continue
        names = _pairs(r["items"])
        has_pos = any(p is not None for p, _n, _rw in names)
        if indent < (MIN_INDENT_POS if has_pos else MIN_INDENT_BARE):
            continue
        if not any(n for _p, n, _rw in names):
            continue
        out.append((i, _expand(r["lead"]), names, 'marker'))
    return out
