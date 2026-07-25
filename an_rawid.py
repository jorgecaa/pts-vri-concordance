#!/usr/bin/env python3
"""
an_rawid — gramática del identificador crudo de AN (`Raw ID`), con **pyparsing**.

**Por qué existe.** Las filas de AN se importaron de un fichero externo (`rebuild_an.py`, «the
original blog data») partiendo su cadena con una regla ingenua, y el resultado quedó dañado en
**1302 de 1738 filas**: 166 con la cola del número (`-5`) incrustada al principio del nombre, 1126
con un `: ` residual al frente y 9 con el corchete sin cerrar. Nada de eso viene del OCR ni de la
edición de Morris — PTS **no imprime nombres de sutta en AN I**, sólo números.

La columna `Raw ID` conserva la cadena original íntegra y es la autoridad. Su formato es:

    AN <nº> [<referencia DPR>]: <nombre>

`parse(raw)` → `(numero, referencia, nombre)`. Casos que la gramática admite **a propósito**,
porque están en el dato y no son errores que corregir:

| forma | ejemplo | nota |
|---|---|---|
| sin referencia | `AN 3.1: Bhaya` | la mayoría del Tika |
| rango abreviado | `AN 3.58-9: Tikaṇṇa, Jāṇussoṇi` | `58-9` es **58–59**, abreviatura inglesa («pp. 158-9»), no un dígito perdido |
| corchete sin cerrar | `AN 1.31 [AN 1.4.1: Adanta 1` | ya viene así de la fuente (9 filas) |
| corchete cerrado antes de tiempo | `AN 3.111 [AN 3.107]-08: Nidāna 1` | el `-08` es del **rango de la referencia** (`AN 3.107-108`), NO del `Sutta #` |
| anotación con `(*)` | `AN 2.19(*) + AN 3.29(*): Adhikaraṇa 9 + Andha` | fila combinada |

⚠️ **La referencia entre corchetes NO es el `Sutta #`.** Son dos notaciones distintas y divergen
(`3.155 Pubbaṇha` es el `AN3.140` del concordance: desfase +15). Extraerla a su propia columna es
justamente lo que permite emparejar con `massive.tsv` sin adivinar.
"""
import re

import pyparsing as pp

pp.ParserElement.set_default_whitespace_chars(" \t")

# nº de sutta: «1.1», «1.1-5», «3.58-9», «11.982-1151»
_NUM = pp.Regex(r'\d+(?:\.\d+)*(?:\s*-\s*\d+)?')('num')
_AN = pp.Suppress(pp.Regex(r'AN\b'))
# marca «(*)» y continuaciones «+ AN 3.29(*)» de las filas combinadas
_STAR = pp.Regex(r'\(\*\)')('star')
_PLUS = pp.Regex(r'\+\s*AN\s*[\d.\-]+(?:\(\*\))?')('plus')
# referencia entre corchetes; el `]` puede faltar (9 filas de la fuente) y puede
# ir seguida de la cola de su propio rango («[AN 3.107]-08»)
_REF = (pp.Suppress('[') + pp.Regex(r'[^\]:]+')('ref') + pp.Opt(pp.Suppress(']'))
        + pp.Opt(pp.Regex(r'-\s*\d+')('reftail')))
_NAME = pp.Regex(r'.*')('name')
_RAW = (_AN + _NUM + pp.Opt(_STAR) + pp.Opt(_PLUS) + pp.Opt(_REF)
        + pp.Opt(pp.Suppress(':')) + _NAME + pp.StringEnd())


def parse(raw):
    """`Raw ID` → `(numero, referencia, nombre)`; `(None, None, raw)` si no encaja."""
    s = (raw or '').strip()
    if not s:
        return None, None, ''
    try:
        r = _RAW.parse_string(s, parse_all=True)
    except pp.ParseException:
        return None, None, s
    num = re.sub(r'\s+', '', r['num'])
    ref = None
    if 'ref' in r:
        ref = re.sub(r'\s+', ' ', r['ref']).strip()
        if 'reftail' in r:                      # «[AN 3.107]-08» → «AN 3.107-08»
            ref += re.sub(r'\s+', '', r['reftail'])
    name = (r['name'] if 'name' in r else '').strip()
    name = re.sub(r'^[:\s]+', '', name).strip()
    return num, ref, name


def expand_ref(ref):
    """`«AN 3.107-08»` → `(107, 108)`: expande el **rango abreviado** a la inglesa.

    `3.107-08` significa 107–108, no 107–8; hay que completar el final con los dígitos de cabeza
    del inicio. Lo mismo `3.58-9` → 58–59 y `1.982-1151` → 982–1151 (aquí no hace falta).
    """
    m = re.search(r'(\d+)\.(\d+)\s*-\s*(\d+)$', ref or '')
    if not m:
        return None
    a, b = m.group(2), m.group(3)
    if len(b) < len(a):                          # cola abreviada: se completa por delante
        b = a[:len(a) - len(b)] + b
    return int(a), int(b)
