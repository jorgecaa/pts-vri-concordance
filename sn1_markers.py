#!/usr/bin/env python3
"""
sn1_markers — gramática de marcadores de sutta de **SN I** (S i, `book_no=12`).

Parseo del formato con **pyparsing** exclusivamente (regla del proyecto; gramática documentada
en `docs/grammar.md`, buenas prácticas en `doc/pyparsing/pyparsing/ai/best_practices.md`).

SN I no usa los marcadores `N. (M) Nombre` de SN II–V, sino **`§ N. Nombre.`** centrado, con el
número **reiniciado en cada vagga** (un cuarto sistema de coordenadas: ni el `Sutta #` del Excel,
ni el canónico, ni el paranum CST). Dos variantes que hay que aceptar o se pierden 6 de los 271:

1. **Marcador de rango con coma** — `§§ 4,5. Saṅgāme dve vuttāni.` ("los dos Saṅgāma dichos"):
   un solo encabezado para dos suttas, con los números `4.` y `5.` como subdivisiones dentro.
2. **Marcador "desnudo"** — el `§` se perdió en el OCR y queda solo `4. Nandano.` centrado. Son 5
   en el volumen (p23 L21, p52 L29, p56 L19, p73 L25, p124 L14). Se discriminan de los números de
   párrafo (margen izquierdo, sangría ~5) y de los versos de las gāthās (que llevan `║`) por la
   sangría, la ausencia de `║`, la brevedad y la mayúscula inicial del nombre.

`find_markers_sn1(text)` devuelve `[(nº_línea, [números], nombre, tag)]` por página, en orden.
`find_submarkers_sn1(text)` localiza los **submarcadores** de un bloque de rango: dentro de
`§§ 4,5.` cada sutta abre con su número centrado a solas (`4.` en S i 82, `5.` en S i 83). Sin
ellos, los dos suttas del rango comparten todo el texto y el cotejo se cae (en S i 82 son dos
batallas con desenlaces opuestos).
"""
import pyparsing as pp

# Formato orientado a línea: el salto de línea es significativo.
pp.ParserElement.set_default_whitespace_chars(" \t")

MIN_INDENT = 8       # sangría mínima de un marcador centrado (los párrafos van a ~5)
MAX_LEN = 48         # un marcador es un título breve, no un verso

# ── Tokens ──────────────────────────────────────────────────────────────────────
_num = pp.Word(pp.nums).set_name("num")
_dot = pp.Literal(".").set_name("dot")
_sep = (pp.Literal(",") | pp.Word("-", min=1)).set_name("sep")     # "4,5" y "103--108"
_section = pp.Word("§", min=1, max=2).set_name("section_sign")     # "§" o "§§"
_name = pp.Regex(r"[^\n]*").set_name("name")                       # resto de la línea

# numlist ::= num ((","|"-"+) num)*    → "4" | "4,5" | "103--108"
_numlist = pp.Group(_num + pp.ZeroOrMore(pp.Suppress(_sep) + _num)).set_name("numlist")

# marcador con signo de sección: "§ 4. Na santi." / "§§ 4,5. Saṅgāme dve vuttāni."
_sec_marker = (pp.Suppress(_section) + _numlist("nums")
               + pp.Opt(pp.Suppress(_dot)) + _name("name")).set_name("sec_marker")

# marcador desnudo (§ perdido en el OCR): "4. Nandano."
_bare_marker = (_numlist("nums") + pp.Suppress(_dot) + _name("name")).set_name("bare_marker")

_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZĀĪŪṄÑṆṬḌḶŚ"


def _parse(expr, s):
    try:
        return expr.parse_string(s, parse_all=True)
    except pp.ParseException:
        return None


def find_markers_sn1(text):
    """Marcadores de inicio de sutta de una página de SN I.

    Devuelve `[(line_no, [nums], name, tag)]` con `tag` ∈ {'section', 'bare'}; `nums` trae más de
    un número solo en los marcadores de rango (`§§ 4,5`).
    """
    out = []
    for i, line in enumerate(text.split("\n"), start=1):
        s = line.rstrip("\r").strip()
        if not s:
            continue
        indent = len(line) - len(line.rstrip("\r").lstrip())

        if s.startswith("§"):
            r = _parse(_sec_marker, s)
            if r is not None:
                out.append((i, [int(n) for n in r["nums"]], r["name"].strip(), "section"))
            continue

        # Marcador desnudo: exige sangría de centrado, brevedad, nombre con mayúscula y
        # ausencia de `║` — así no se confunde con un número de párrafo ni con un pada de gāthā.
        if indent < MIN_INDENT or len(s) > MAX_LEN or "║" in s:
            continue
        r = _parse(_bare_marker, s)
        if r is None:
            continue
        name = r["name"].strip()
        if name[:1] in _UPPER and len(name) >= 3:
            out.append((i, [int(n) for n in r["nums"]], name, "bare"))
    return out


# submarcador de bloque de rango: una línea que es SOLO un número y un punto, centrada
_submarker = (_num("n") + pp.Suppress(_dot)).set_name("submarker")
SUB_MIN_INDENT = 20      # van muy centrados ("4." con sangría 39 en S i 82)


def find_submarkers_sn1(text):
    """`[(nº_línea, número)]` de los submarcadores de un bloque de rango.

    Es una línea que consiste SOLO en `N.`, muy centrada. La sangría alta la separa de los
    números de párrafo (margen izquierdo) y la exigencia de línea completa, de todo lo demás.
    """
    out = []
    for i, line in enumerate(text.split("\n"), start=1):
        s = line.rstrip("\r").strip()
        if not s or "║" in s:
            continue
        if len(line) - len(line.rstrip("\r").lstrip()) < SUB_MIN_INDENT:
            continue
        r = _parse(_submarker, s)
        if r is not None:
            out.append((i, int(r["n"])))
    return out


def build_vaggas(rows):
    """Agrupa `[(page, line, nums, name, tag)]` (en orden de lectura) en vaggas.

    Dentro de un vagga el número `§` **crece estrictamente**, así que un número que no crece
    abre vagga nuevo. Es la única regla fiable: los `§1` de arranque pueden faltar en el OCR.
    """
    vaggas, cur, prev = [], [], 0
    for r in rows:
        n = r[2][0]
        if cur and n <= prev:
            vaggas.append(cur)
            cur = []
        cur.append(r)
        prev = r[2][-1]
    if cur:
        vaggas.append(cur)
    return vaggas
