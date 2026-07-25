#!/usr/bin/env python3
"""
sn3_markers — gramática de marcadores de sutta de **SN III** (S iii, `book_no=14`).

Parseo con **pyparsing** exclusivamente (regla del proyecto; ver `docs/grammar.md`).

S iii usa la misma familia que S ii — **`N (M) Nombre` sin puntos**, con `N` = nº corrido en el
saṃyutta y `M` = posición en el vagga — pero añade tres formas propias, y sin ellas se pierden
suttas:

| Forma | Ejemplo | Nota |
|---|---|---|
| estándar | `1 (1) Nakulapitā` | |
| sin posición | `1 Cakkhu` | saṃyuttas de un vagga único (S iii 225 y ss.) |
| desambiguador | `3 (3) Hāliddikāni (1)` | el `(N)` final es parte del nombre |
| **nombre entre paréntesis** | `11 (Samāpatti-ṭhiti)` | sin posición; el nombre va en paréntesis |
| **rango con posición-rango** | `140-142 (5-7) Dukkhena (1-3)` | |
| **prefijo de gamana** | `(3)11-15 Anabhisamayā (1-5)` | los 4 *gamana* del Diṭṭhi-saṃyutta |
| variante en el nombre | `24 (3) Parijānaṃ (or Abhijānaṃ)` | paréntesis no numérico → se ignora |
| sin nombre | `45 (1)` | |
| rango con guion en el nombre | `31-32 (9-10) Khaya-Vaya` | |

Se mantienen los tres principios de `sn2_markers`: el recuento lo fija el **rango del nº corrido**;
la **sangría mínima depende de la forma** (`N (M)` es inequívoco incluso al margen, `N Nombre` solo
centrado); y un rango puede ser el **encabezado de un grupo** cuyos miembros se reimprimen, por lo
que el marcador individual pisa al del rango.

`find_markers_sn3(text)` devuelve `[(nº_línea, [nº corridos], [(pos, nombre)], tag)]`, con
`tag` ∈ {'marker', 'cont'}.
"""
import pyparsing as pp

pp.ParserElement.set_default_whitespace_chars(" \t")

MIN_INDENT_POS = 5     # forma con "(M)" — inequívoca, aparece incluso al margen
# Forma sin paréntesis: los 2285 números de párrafo están a sangría 5 y los marcadores reales
# de este volumen van de 12 a 29 (el `1 Samādhi-samāpatti` que abre SN 34 está a 14, así que un
# umbral de 20 —el de S ii— se lo come). A cambio hay que descartar dos cabeceras de uddāna.
MIN_INDENT_BARE = 12
MAX_LEN = 60

_num = pp.Word(pp.nums).set_name("num")
_dash = pp.Word("-–—", min=1).set_name("dash")
_numrange = pp.Group(_num + pp.Opt(pp.Suppress(_dash) + _num)).set_name("numrange")

_group = pp.Group(pp.Suppress("(") + _numrange("pos") + pp.Opt(pp.Suppress(")")))("group")
# nombre entre paréntesis: "(Samāpatti-ṭhiti)", "(Ṭhiti-āramamṇa --)"
_pname = pp.Regex(r"\(\s*[^\d)][^)\n]*\)?")("pname")
# comentario no numérico que NO es el nombre principal: "(or Abhijānaṃ)"
_remark = pp.Suppress(pp.Regex(r"\(\s*(?:or|vā)\b[^)\n]*\)?"))
_name = pp.Regex(r"[^(\n]+")("name")

# prefijo de *gamana*: "(3)" seguido del nº corrido, en el Diṭṭhi-saṃyutta
_gamana = pp.Group(pp.Suppress("(") + _num + pp.Suppress(")"))("gamana") + pp.FollowedBy(_numrange)
_lead_paren = pp.Suppress("(") + _numrange + pp.Suppress(")") + pp.FollowedBy(_group)
_lead = (_lead_paren | _numrange).set_name("lead")

_item = (_group | _remark | _pname | _name).set_name("item")
_marker = (pp.Opt(_gamana) + _lead("lead") + pp.Group(pp.ZeroOrMore(_item))("items")).set_name("marker")
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
    a = int(rng[0]); b = int(rng[1]) if len(rng) > 1 else a
    return list(range(a, b + 1)) if b >= a else [a]


def _text(v):
    while v is not None and not isinstance(v, str):
        if not len(v):
            return ''
        v = v[0]
    return v or ''


def _pairs(items):
    """Empareja items en `[(pos, nombre, bruto)]`. Un grupo `(M)` toma el nombre siguiente; un
    nombre sin grupo delante va con `pos=None`; un grupo sin nombre aporta solo posición.

    `bruto` conserva los guiones de truncamiento que `_clean` quita. En el Jhāna-saṃyutta ese
    guión **no es adorno: es el que dice qué mitad del compuesto ha escrito Feer**. «Ārammaṇa --»
    abrevia *Ārammaṇa-mūlaka* (la raíz), mientras que un «Ārammaṇa» a secas, en la serie
    Samādhimūlaka, nombra el segundo elemento. Sin el guión los dos regímenes son indistinguibles
    y las series 35-40/41-45/46-49/50-52 se emparejaban con el grupo siguiente.
    """
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


def find_markers_sn3(text):
    """Marcadores de una página de S iii: `[(line_no, [nums], [(pos, name)], tag)]`."""
    out = []
    for i, line in enumerate(text.split("\n"), start=1):
        s = line.rstrip("\r").rstrip()
        indent = len(s) - len(s.lstrip())
        s = s.strip().rstrip('║').strip()
        if not s or '║' in s or len(s) > MAX_LEN or s[0] not in "0123456789(":
            continue
        # "(Section …)" y otros encabezados: paréntesis sin dígito y sin nº corrido detrás
        if s.startswith("(") and not s[1:2].isdigit():
            continue
        has_pos = next(_group.scan_string(s), None) is not None
        if indent < (MIN_INDENT_POS if has_pos else MIN_INDENT_BARE):
            continue

        r = _parse(_marker, s)
        if r is not None and r.get("lead") is not None:
            names = _pairs(r["items"])
            # A esta sangría se colarían cabeceras que no son suttas: los uddāna, los fragmentos
            # entre corchetes y los encabezados de *gamana* en versal («2 DUTIYAGAMANAM»), que
            # llevan el nº de gamana y se confundirían con un nº corrido.
            if any('uddān' in n.lower() or n.startswith('[') or (n.isupper() and len(n) > 4)
                   for _p, n, _r in names):
                continue
            gam = int(_text(r["gamana"])) if r.get("gamana") else None
            out.append((i, _expand(r["lead"]), names, 'marker' if gam is None else f'gamana{gam}'))
            continue
        r = _parse(_cont, s)
        if r is not None:
            names = [(p, n, rw) for p, n, rw in _pairs(r["items"]) if n]
            if names:
                out.append((i, [], names, 'cont'))
    return out


def collect_suttas(rows, restart=1):
    """`[(page, line, nums, names, tag)]` → suttas en orden canónico + los saṃyuttas.

    Igual criterio que en S ii: el nº `restart` (=1) abre saṃyutta nuevo y, dentro de cada
    saṃyutta, el marcador individual pisa al de un rango. Los marcadores de *gamana* NO abren
    saṃyutta: son subdivisiones del Diṭṭhi-saṃyutta que reinician su propia cuenta, así que se
    indexan como `(gamana, nº)` para no pisarse entre sí.
    """
    sams, cur, order, prev, gam = [], {}, [], 0, None
    for pg, ln, nums, names, tag in rows:
        if tag == 'cont':
            for pos, nm, rw in names:
                for _n, rec in cur.items():
                    if rec['pos'] == pos and not rec['name']:
                        rec['name'] = nm; rec['raw'] = rw
                        rec['page'], rec['line'] = pg, ln
                        break
            continue
        g = int(tag[6:]) if tag.startswith('gamana') else None
        # El `(N)` inicial es un índice de subdivisión: el *gamana* en el Diṭṭhi-saṃyutta y el nº de
        # TÍTULO en el Vacchagotta (11 títulos × 5 khandhas = 55 suttantas, dice Feer). Abre
        # saṃyutta nuevo solo si ese índice ES el primero: `(1)1 Aññāṇā` inicia SN 33, mientras
        # `(27)1-4` (SN 34) es una combinación interna y no debe partir nada.
        if nums[0] == restart and cur and (g is None or g == restart):
            sams.append((order, cur)); cur, order, gam = {}, [], None
        if g is not None:
            gam = g
        pairs = list(names)
        for k, n in enumerate(nums):
            pos, nm, rw = (pairs[k] if k < len(pairs) else (None, '', ''))
            key = (gam, n) if gam else n
            rec = {'page': pg, 'line': ln, 'num': n, 'pos': pos, 'name': nm, 'raw': rw,
                   'gamana': gam, 'from_range': len(nums) > 1}
            if key in cur and cur[key]['from_range'] and not rec['from_range']:
                cur[key] = rec
            elif key not in cur:
                cur[key] = rec; order.append(key)
        prev = nums[-1]
    if cur:
        sams.append((order, cur))

    out = []
    for si, (_order, d) in enumerate(sams, start=1):
        for key in sorted(d, key=lambda k: (k if isinstance(k, tuple) else (0, k))):
            rec = dict(d[key]); rec['sam_idx'] = si
            out.append(rec)
    return out, sams
