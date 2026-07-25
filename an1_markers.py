#!/usr/bin/env python3
"""
an1_markers — gramática de marcadores de **AN I** (A i, `book_no=17`), con **pyparsing**.

AN I **no es homogéneo** ni por nipāta (regla (6) de `CLAUDE.md`). Sus tres nipātas se imprimen
bajo dos regímenes, y ninguno se parece a los de SN:

| nipāta | pp. | vagga | sutta |
|---|---|---|---|
| **Eka** | 1-46 | numeral **romano centrado** (`I.`, `XIV.3`) | `N.` a **sangría 5**, reinicia por vagga |
| **Duka** | 47-100 | idem (`II.`) | idem |
| **Tika** | 101-300 | **ninguno** | `N.` **CENTRADO** y **corrido** (`1.` p101, `11.` p106) |

Tres trampas del dato:

- **La llamada de nota va pegada al numeral**: `XIV.3`, `XVII.4`, `XIX.2`, `XXI.1`. Exigir el
  romano limpio pierde 4 de los 21 vaggas del Eka.
- **Marcadores de PAR**: `4, 5. Kosajjaṃ … viriyārambho.`, `3,4.`, `10, 11.` — una sola línea que
  cubre dos suttas. Leerlos como uno solo descuadra el recuento del Eka.
- **El colofón de vagga es mejor señal que el romano**: `Kalyāṇamittādi-vaggo aṭṭhamo.`,
  `Pamādādivaggo navamo.` — nombra el vagga *y* da su ordinal, y el nombre casa con el del CST.
- En el Tika **el vagga no se imprime**: hay que inferirlo del nº corrido (cambia cada diez) y
  contrastarlo con las páginas de arranque del índice de Morris
  (`anguttara-vol-I-info.txt`), que es la verdad-terreno estructural del lado PTS.

`find_markers_an1(text)` devuelve `[(línea, tipo, valor, sangría)]` con
`tipo ∈ {'nipata', 'vagga', 'sutta'}`; el llamador lleva el contexto de nipāta, porque de él
depende qué forma es un sutta.
"""
import re

import pyparsing as pp

pp.ParserElement.set_default_whitespace_chars(" \t")

MIN_INDENT_CENTRED = 14     # vagga romano y, en el Tika, el nº corrido del sutta
SUTTA_INDENT = (5, 6)       # régimen Eka/Duka: el sutta abre párrafo a esta sangría
MAX_LEN_HEAD = 44

_num = pp.Word(pp.nums)
# numeral romano + posible llamada de nota pegada: «XIV.3»
_roman = pp.Regex(r'X{0,3}(?:IX|IV|V?I{0,3})')('roman')
_VAGGA = _roman + pp.Opt(pp.Suppress('.')) + pp.Opt(pp.Suppress(_num)) + pp.StringEnd()
# nº de sutta centrado (Tika): «11.» y nada más
_SUTTA_C = _num('num') + pp.Opt(pp.Suppress('.')) + pp.Opt(pp.Suppress(_num)) + pp.StringEnd()
# nº de sutta a sangría 5 (Eka/Duka): «1. Evaṃ me sutaṃ…»; admite PARES «4, 5. …», «3,4. …»
_numlist = pp.Group(pp.delimited_list(_num, delim=','))('nums')
_SUTTA_P = _numlist + pp.Suppress('.') + pp.Regex(r'.+')('rest')
# colofón de vagga: «Kalyāṇamittādi-vaggo aṭṭhamo.» — nombra el vagga y da su ordinal
_COLOPHON = re.compile(r'^(.{3,40}?)[- ]?vaggo\s+(\S+?)\.?\d*$', re.I)
_ORD = {'pathamo': 1, 'dutiyo': 2, 'tatiyo': 3, 'catuttho': 4, 'pancamo': 5, 'chattho': 6,
        'sattamo': 7, 'atthamo': 8, 'navamo': 9, 'dasamo': 10, 'ekadasamo': 11,
        'dvadasamo': 12, 'terasamo': 13, 'cuddasamo': 14, 'pannarasamo': 15,
        'solasamo': 16, 'sattarasamo': 17, 'attharasamo': 18, 'ekunavisatimo': 19,
        'visatimo': 20, 'ekavisatimo': 21}
_FOLD = str.maketrans({'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṅ': 'n', 'ñ': 'n', 'ṇ': 'n',
                       'ṭ': 't', 'ḍ': 'd', 'ḷ': 'l', 'ṃ': 'm', 'ṁ': 'm'})

_NIPATA = re.compile(r'(EKA|DUKA|TIKA)-NIP[ĀA]TA', re.I)


def _parse(expr, s):
    try:
        return expr.parse_string(s, parse_all=True)
    except pp.ParseException:
        return None


def find_markers_an1(text):
    """Marcadores de una página de A i: `[(línea, tipo, valor, sangría)]`."""
    out = []
    for i, line in enumerate(text.split('\n'), start=1):
        raw = line.replace('⁣', '')
        indent = len(raw) - len(raw.lstrip())
        s = raw.strip()
        if not s:
            continue
        m = _NIPATA.search(s)
        if m:
            out.append((i, 'nipata', m.group(1).upper(), indent))
            continue
        if indent >= MIN_INDENT_CENTRED and len(s) <= MAX_LEN_HEAD:
            r = _parse(_VAGGA, s)
            if r is not None and r['roman']:
                out.append((i, 'vagga', r['roman'], indent))
                continue
            r = _parse(_SUTTA_C, s)
            if r is not None:
                out.append((i, 'sutta', int(r['num']), indent))
                continue
        c = _COLOPHON.match(s)
        if c and indent >= 10:
            o = _ORD.get(re.sub(r'[^a-z]', '', c.group(2).lower().translate(_FOLD)))
            if o:
                out.append((i, 'colofon', (c.group(1).strip(), o), indent))
                continue
        if indent in SUTTA_INDENT:
            r = _parse(_SUTTA_P, s)
            if r is not None:
                for x in r['nums']:
                    out.append((i, 'sutta', int(x), indent))
    return out


ROMAN = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9,
         'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17,
         'XVIII': 18, 'XIX': 19, 'XX': 20, 'XXI': 21}


def collect_an1(pages):
    """`{página: [líneas]}` → `[{nipata, vagga, num, page, line}]` en orden de lectura.

    En Eka y Duka el `num` es la posición **dentro del vagga** (reinicia); en el Tika es el nº
    **corrido** del nipāta y el vagga se deja a `None` (lo fija después el índice de Morris).
    """
    out, nip, vag = [], None, None
    for pg in sorted(pages):
        for ln, kind, val, ind in find_markers_an1('\n'.join(pages[pg])):
            if kind == 'nipata':
                nip, vag = val, None
            elif kind == 'vagga':
                vag = ROMAN.get(val)
            elif kind == 'colofon':
                out.append({'nipata': nip, 'vagga': val[1], 'num': None,
                            'page': pg, 'line': ln, 'colofon': val[0]})
            elif kind == 'sutta' and nip:
                # en Eka/Duka sólo cuenta la forma de párrafo; en el Tika, sólo la centrada
                if nip in ('EKA', 'DUKA') and ind not in SUTTA_INDENT:
                    continue
                if nip == 'TIKA' and ind < MIN_INDENT_CENTRED:
                    continue
                out.append({'nipata': nip, 'vagga': vag, 'num': val, 'page': pg, 'line': ln})
    return out
