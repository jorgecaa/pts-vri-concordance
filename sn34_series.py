#!/usr/bin/env python3
"""sn34_series.py — los DOS analizadores de nombres del Jhāna-saṃyutta (SN 34, S iii 263-278).

**Por qué dos.** El saṃyutta no es homogéneo: sus 55 suttas se imprimen bajo dos convenciones
incompatibles, y una sola regla no puede servir a las dos sin equivocarse en una.

*Régimen A — individuales (suttas 1-19).* La raíz del compuesto es **constante** dentro de cada
serie (`Samādhimūlaka-`, luego `Samāpattimūlaka-`), así que Feer la da por sabida y el marcador
nombra el **segundo** elemento: «Ṭhiti», «Vuṭṭhāna», «Ārammaṇa» = *Samādhimūlaka-ṭhiti*, etc. Sólo
encabeza el par completo cuando la raíz cambia («Samāpatti-ṭhiti»).

*Régimen B — grupos (suttas 20-55).* Aquí el CST agrupa («35-40. Kallitamūlakaārammaṇasuttādi-
chakkaṃ») y PTS titula el grupo por el par **raíz-primer elemento**, en dos formas: completa
(«Gocara-Abhinīhāra» = *Gocaramūlaka-abhinīhāra*) o **truncada con guiones** («Ārammaṇa --» =
*Ārammaṇa-mūlaka*, con el `--` en lugar del resto). En la forma truncada el marcador nombra la
**raíz**, justo al revés que en el régimen A.

Aplicar la regla de A en el tramo de B desplazaba cada fila al grupo siguiente: «Ārammaṇa» se leía
como *segundo* elemento y casaba con `41-45. Ārammaṇamūlakagocara…` la fila que era de
`35-40. Kallitamūlakaārammaṇa…`. Cuatro filas mal emparejadas (34.22-34.25), tres de ellas ya
CONFIRMADO y una firmada a mano — el fallo clásico: **el validador no puede verlo, porque el par
PTS↔CST que recibe es coherente consigo mismo**.

El desempate definitivo en el régimen B no es el nombre sino el **número**: el subhead del CST
declara su rango («46-49.») y el marcador de PTS lleva su nº corrido (46). Son la misma numeración,
así que la cabeza del rango CST **debe** ser el nº del marcador. El nombre sólo confirma.

La gramática de la forma del nombre va en `pyparsing`, como el resto del parseo del repo.
"""
import re

import pyparsing as pp

# ── gramática de la FORMA del nombre de un marcador ──────────────────────────
_DASH = pp.Word('-–—', min=1).suppress()
_WORD = pp.Regex(r'[^\s\-–—][^\-–—]*?(?=\s*(?:[-–—]|$))')
# «X -- Y» (par completo) | «X --» (truncado: sólo la raíz) | «X» (simple)
_PAIR = (_WORD('x') + _DASH + _WORD('y') + pp.StringEnd())('pair')
_TRUNC = (_WORD('x') + _DASH + pp.StringEnd())('trunc')
_PLAIN = (pp.Regex(r'.+')('x') + pp.StringEnd())('plain')
_NAME = _PAIR | _TRUNC | _PLAIN

_FOLD = str.maketrans({'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṅ': 'n', 'ñ': 'n', 'ṇ': 'n',
                       'ṭ': 't', 'ḍ': 'd', 'ḷ': 'l', 'ṃ': 'm', 'ṁ': 'm'})
_MULAKA = re.compile(r'^(.+?)m[ūu]lak[aā](.+?)(?:sutt|$)', re.I)
_RANGE = re.compile(r'^\s*(\d+)(?:\s*-+\s*(\d+))?\.')


def stem(t):
    """Raíz comparable: sin diacríticos, sin dobles, sin desinencia."""
    t = re.sub(r'[^a-z]', '', (t or '').lower().translate(_FOLD))
    t = re.sub(r'(suttam|suttani|sutta|vaggo|kari)$', '', t)
    return re.sub(r'[aiueom]+$', '', re.sub(r'(.)\1+', r'\1', t))


def parse_name(raw):
    """Forma del nombre del marcador → `('pair', x, y)` | `('trunc', x)` | `('plain', x)`.

    `raw` debe conservar los guiones (ver `sn3_markers._pairs`): sin ellos «Ārammaṇa --» y
    «Ārammaṇa» son el mismo texto y los dos regímenes se vuelven indistinguibles.
    """
    s = (raw or '').strip()
    if not s:
        return ('plain', '')
    try:
        r = _NAME.parse_string(s, parse_all=True)
    except pp.ParseException:
        return ('plain', s)
    if 'y' in r:
        return ('pair', r['x'].strip(), r['y'].strip())
    if s.rstrip().endswith(('-', '–', '—')):
        return ('trunc', r['x'].strip())
    return ('plain', r['x'].strip())


def split_row(name):
    """`Sutta Name` del Excel → `(raíz, segundo elemento)` de `X-mūlaka-Y`."""
    m = _MULAKA.match(name or '')
    return (m.group(1), m.group(2)) if m else (None, None)


def cst_range(title):
    """`«46-49. Gocaramūlaka…»` → `(46, 49)`; `«19. Samāpatti…»` → `(19, 19)`."""
    m = _RANGE.match(title or '')
    if not m:
        return None
    a = int(m.group(1))
    return (a, int(m.group(2)) if m.group(2) else a)


def _hit(a, b):
    """¿Nombran lo mismo dos elementos del compuesto?"""
    x, y = stem(a), stem(b)
    if not x or not y or min(len(x), len(y)) < 3:
        return False
    return x == y or x.startswith(y) or y.startswith(x)


# ── régimen A: suttas individuales (1-19) ────────────────────────────────────
def score_individual(row_name, raw_marker):
    """La raíz es constante y se da por sabida: el marcador abreviado nombra la **Y**."""
    root, second = split_row(row_name)
    if not second:
        return 0
    kind, *parts = parse_name(raw_marker)
    if kind == 'pair':
        x, y = parts
        if _hit(root, x) and _hit(second, y):
            return 120                       # par completo: cambia la raíz de la serie
        return 60 if _hit(second, y) else 0
    # 'plain' / 'trunc': un solo elemento, que aquí es el SEGUNDO del compuesto
    return 100 if _hit(second, parts[0]) else 0


# ── régimen B: grupos colectivos (20-55) ─────────────────────────────────────
def score_grouped(row_name, raw_marker, marker_num=None, rng=None):
    """El marcador titula el grupo; truncado («X --») nombra la **raíz**, no el segundo elemento.

    Si se conocen el rango del subhead CST y el nº del marcador, manda el número: son la misma
    numeración en las dos ediciones, así que la cabeza del rango debe ser el nº del marcador.
    """
    root, second = split_row(row_name)
    s = 0
    if rng and marker_num is not None:
        if marker_num == rng[0]:
            s += 200                         # evidencia numérica explícita en ambas ediciones
        elif rng[0] <= marker_num <= rng[1]:
            s += 40                          # dentro del grupo, pero no es su cabeza
        else:
            return 0                         # fuera del rango declarado: no es este grupo
    if not root:
        return s
    kind, *parts = parse_name(raw_marker)
    if kind == 'pair':
        x, y = parts
        if _hit(root, x) and _hit(second, y):
            s += 120
        elif _hit(root, x):
            s += 70
    elif kind == 'trunc':
        if _hit(root, parts[0]):
            s += 100                         # «Ārammaṇa --» = Ārammaṇa-mūlaka
    else:
        if _hit(root, parts[0]):
            s += 60
    return s
