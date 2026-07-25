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
| **Catukka** (A ii) | — | ninguno; lo cierra el **colofón** | `N.` centrado y corrido |
| **Pañcaka / Chakka** (A iii) | — | ninguno; lo cierra el **colofón** | **numeral ROMANO centrado y corrido** (`XI.`, `CCL.`); los arábigos a sangría 5 son **párrafos** |

El régimen se elige **por nipāta** en `REGIMEN`, y **no es monótono**: Tika y Catukka usan el nº
corrido centrado (`21.` en A ii 20), pero el Pañcaka y el Chakka de A iii **vuelven** al numeral
romano de vagga. Comprobarlo por volumen, nunca extrapolarlo.

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
# Numeral romano COMPLETO + posible llamada de nota pegada: «XIV.3», «CCL.», «CXXIV».
# En el Pañcaka llegan a CCL (250) y en el Chakka a CXXIV, así que un patrón limitado a 39 —el que
# bastaba para los vaggas del Eka— pierde casi todo el volumen.
_roman = pp.Regex(r'M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})')('roman')
# También hay RANGOS en romanos: «CLXXXII-CLXXXIX.» (A iii 219) cubre los suttas 182-189 de una
# vez. Sin esto se pierden ocho seguidos y parece que faltan del impreso.
_roman2 = pp.Regex(r'M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})')('roman2')
# la llamada de nota puede ir PEGADA («XIV.3») o SEPARADA por un espacio («I 2.», A iv 150)
_VAGGA = (_roman + pp.Opt(pp.Suppress(pp.Word('-–—')) + _roman2)
          + pp.Opt(pp.Suppress('.')) + pp.Opt(pp.Suppress(_num)) + pp.StringEnd())
# nº de sutta centrado (Tika): «11.» y nada más
_SUTTA_C = _num('num') + pp.Opt(pp.Suppress('.')) + pp.Opt(pp.Suppress(_num)) + pp.StringEnd()
# nº de sutta a sangría 5 (Eka/Duka): «1. Evaṃ me sutaṃ…»; admite PARES «4, 5. …», «3,4. …»
_numlist = pp.Group(pp.delimited_list(_num, delim=','))('nums')
_SUTTA_P = _numlist + pp.Suppress('.') + pp.Regex(r'.+')('rest')
# Colofón de vagga. Cuatro formas conviven en el impreso, y ceñirse a la canónica pierde 8 de los
# 26 vaggas de A ii:
#   «Kalyāṇamittādi-vaggo aṭṭhamo.»   canónica: nombre + ordinal
#   «VAGGO PAṬHAMO.»                  en VERSALES y SIN nombre (A ii 12)
#   «Macalavaggo.1» / «Asuravaggo.»   SIN ordinal (A ii 91, 101)
#   «[Indriya-]1vaggo [paṭhamo] 1»    con corchetes y la llamada de nota PEGADA antes de «vaggo»
#   «Yodhajīvavaggo1 catuttho.»       llamada pegada al nombre
#   «Caravaggo [dutiyo.]»             el punto va DENTRO del corchete
#   «Āhuneyyavaggo2 paṭhamo2.»        llamadas de nota ANTES del punto, en nombre y ordinal
#   «Sītivaggo14 navamo15.»           idem
#   «Sativaggo10 navamo11 samatto.»   con «samatto»/«niṭṭhito» detrás del ordinal
_COLOPHON = re.compile(r'^\[?\s*(.{0,40}?)\s*\]?\d*[- ]?vaggo\d*\.?'
                       r'(?:\s*\[?\s*([a-zāīūṃṅñṭḍṇḷ]+)[\d\s.]*\]?)?'
                       r'(?:\s*(?:samatto|niṭṭhito|nitthito)[\d\s.]*)?[\d\s.]*$', re.I)
_ORD = {'pathamo': 1, 'dutiyo': 2, 'tatiyo': 3, 'catuttho': 4, 'pancamo': 5, 'chattho': 6,
        'sattamo': 7, 'atthamo': 8, 'navamo': 9, 'dasamo': 10, 'ekadasamo': 11,
        'dvadasamo': 12, 'terasamo': 13, 'cuddasamo': 14, 'pannarasamo': 15,
        'solasamo': 16, 'sattarasamo': 17, 'attharasamo': 18, 'ekunavisatimo': 19,
        'visatimo': 20, 'ekavisatimo': 21}
_FOLD = str.maketrans({'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṅ': 'n', 'ñ': 'n', 'ṇ': 'n',
                       'ṭ': 't', 'ḍ': 'd', 'ḷ': 'l', 'ṃ': 'm', 'ṁ': 'm'})

# Los nipātas de todo el Aṅguttara, para que el módulo valga en los cinco volúmenes: A ii es el
# Catukka y usa el MISMO régimen que el Tika (nº corrido centrado, vagga implícito cada diez).
# El vagga 26 del Pañcaka (Upasampadā, A iii 271-278) es un peyyāla y **no numera sus suttas**:
# los separa una fila de ornamentos que el OCR guardó en el área de uso privado (U+E0E0). Es la
# única parte del Aṅguttara que marca así — 21 separadores, o sea 22 suttas.
_ORNAMENTO = re.compile('\ue0e0{3,}')
# cabecera de paṇṇāsaka: abre el bloque y, en el peyyāla, el PRIMER sutta —que no lleva ornamento
# delante, porque el ornamento SEPARA, no abre
_PANNASAKA = re.compile(r'PA[ṆN][ṆN][ĀA]SAK', re.I)

_NIPATA = re.compile(r'(EKA|DUKA|TIKA|CATUKKA|PA[ÑN]CAKA|CHAKKA|SATTAKA|A[ṬT][ṬT]HAKA|'
                     r'NAVAKA|DASAKA|EK[ĀA]DASAKA)-NIP[ĀA]TA', re.I)
# régimen por nipāta: 'vagga_romano' (Eka/Duka) o 'corrido' (Tika en adelante)
# ⚠️ El régimen NO es monótono por nipāta: el Tika y el Catukka marcan el sutta con el nº corrido
# centrado, pero el **Pañcaka y el Chakka VUELVEN** al numeral romano de vagga con el sutta a
# sangría 5, como el Eka y el Duka. Suponer que «del Tika en adelante todo es corrido» es falso.
REGIMEN = {'EKA': 'vagga_romano', 'DUKA': 'vagga_romano',
           'PAÑCAKA': 'sutta_romano', 'PANCAKA': 'sutta_romano', 'CHAKKA': 'sutta_romano',
           'SATTAKA': 'sutta_romano', 'AṬṬHAKA': 'sutta_romano', 'ATTHAKA': 'sutta_romano',
           'NAVAKA': 'sutta_romano', 'DASAKA': 'sutta_romano',
           'EKĀDASAKA': 'sutta_romano', 'EKADASAKA': 'sutta_romano'}


def _parse(expr, s):
    try:
        return expr.parse_string(s, parse_all=True)
    except pp.ParseException:
        return None


# el guion entra en la clase: los RANGOS también llegan con la llamada pegada
# («LXXIII-LXXXI6.», A iv 462)
_SOLO_ROMANO = re.compile(r'^[IVXLCDM\s\-–—]+[\s.]*[*)\d]*[\s.]*$')


def _limpia_romano(s):
    """Repara el numeral romano roto por el OCR.

    Tres daños reales en A iv: `«LI. *)»` arrastra una llamada al pie, `«LX XXVII.»` (A iv 344)
    lleva **un espacio dentro del numeral** —es LXXXVII partido— y `«I 2.»` (A iv 150) separa la
    llamada con un espacio. Sólo se aplica si la línea entera son letras romanas, espacios y
    puntuación, así que no toca ningún nombre.

    La llamada se quita **aquí** y no aflojando la gramática: reordenar `_VAGGA` para admitirla
    hundía el recuento de A i de 272 a 56.
    """
    if not _SOLO_ROMANO.match(s):
        return s
    t = re.sub(r'\s+', '', re.sub(r'[*)]+', '', s))
    return re.sub(r'\d+(?=\.?$)', '', t)          # llamada de nota final: los romanos no llevan dígitos


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
        if _PANNASAKA.search(s) and indent >= 10:
            out.append((i, 'bloque', None, indent))
            continue
        if _ORNAMENTO.search(s):
            out.append((i, 'separador', None, indent))
            continue
        if indent >= MIN_INDENT_CENTRED and len(s) <= MAX_LEN_HEAD:
            # variable APARTE: reasignar `s` contaminaría las comprobaciones de más abajo
            sr = _limpia_romano(s)
            r = _parse(_VAGGA, sr)
            if r is not None and r['roman']:
                out.append((i, 'vagga', (r['roman'], r['roman2'] if 'roman2' in r else None),
                            indent))
                continue
            r = _parse(_SUTTA_C, s)
            if r is not None:
                out.append((i, 'sutta', int(r['num']), indent))
                continue
        c = _COLOPHON.match(s)
        if c and indent >= 8 and 'vagg' in s.lower():
            ord_txt = c.group(2) or ''
            o = _ORD.get(re.sub(r'[^a-z]', '', ord_txt.lower().translate(_FOLD)))
            nombre = re.sub(r'[\[\]\d.-]', '', c.group(1) or '').strip()
            # el ordinal puede faltar («Macalavaggo.»): el colofón sigue siendo válido y su
            # posición en la serie la fija el orden de lectura
            if o or nombre:
                out.append((i, 'colofon', (nombre, o), indent))
                continue
        if indent in SUTTA_INDENT:
            r = _parse(_SUTTA_P, s)
            if r is not None:
                for x in r['nums']:
                    out.append((i, 'sutta', int(x), indent))
    return out


_RVAL = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}


def roman_to_int(r):
    """`«CCXLIX»` → 249. Hace falta el parser completo: en A iii los suttas van numerados en
    romano hasta CCL, no como los 21 vaggas del Eka."""
    if not r:
        return None
    total, prev = 0, 0
    for ch in reversed(r.upper()):
        v = _RVAL.get(ch)
        if v is None:
            return None
        total += -v if v < prev else v
        prev = max(prev, v)
    return total or None


def collect_an1(pages):
    """`{página: [líneas]}` → `[{nipata, vagga, num, page, line}]` en orden de lectura.

    En Eka y Duka el `num` es la posición **dentro del vagga** (reinicia); en el Tika es el nº
    **corrido** del nipāta y el vagga se deja a `None` (lo fija después el índice de Morris).
    """
    out, nip, vag, last_sutta, bloque = [], None, None, 0, None
    for pg in sorted(pages):
        for ln, kind, val, ind in find_markers_an1('\n'.join(pages[pg])):
            if kind == 'nipata':
                nip, vag, last_sutta, bloque = val, None, 0, None
            elif kind == 'vagga':
                a, b = (val if isinstance(val, tuple) else (val, None))
                # en el régimen «sutta_romano» el numeral centrado ES el sutta, no el vagga
                if REGIMEN.get(nip) == 'sutta_romano':
                    n0, n1 = roman_to_int(a), roman_to_int(b)
                    # Errata del impreso/OCR: «CCIX.» (209) aparece entre «CCXVIII» (218) y
                    # «CCXX» (220) — le falta una X y debe leerse CCXIX (219). Se repara por
                    # CONTINUIDAD: si el valor rompe la serie hacia atrás y el esperado encaja,
                    # manda la secuencia. Es la misma clase de errata que el «2O» por «20» de S iv.
                    if n0 and last_sutta and n0 <= last_sutta and n1 is None:
                        n0 = last_sutta + 1
                    if n0:
                        last_sutta = (n1 or n0)
                        for n in range(n0, (n1 or n0) + 1):
                            out.append({'nipata': nip, 'vagga': vag, 'num': n, 'page': pg,
                                        'line': ln, 'from_range': n1 is not None})
                else:
                    vag = roman_to_int(a)
            elif kind == 'bloque':
                bloque = (pg, ln)
            elif kind == 'separador':
                # El ornamento SEPARA dos suttas: abre el siguiente, no el que termina. El primero
                # del bloque no lleva ninguno delante y arranca en la cabecera del paṇṇāsaka, así
                # que hay que emitirlo aparte o toda la serie queda corrida uno.
                if bloque is not None:
                    last_sutta += 1
                    out.append({'nipata': nip, 'vagga': vag, 'num': last_sutta,
                                'page': bloque[0], 'line': bloque[1], 'sin_numero': True})
                    bloque = None
                last_sutta += 1
                out.append({'nipata': nip, 'vagga': vag, 'num': last_sutta, 'page': pg,
                            'line': ln, 'sin_numero': True})
            elif kind == 'colofon':
                out.append({'nipata': nip, 'vagga': val[1], 'num': None,
                            'page': pg, 'line': ln, 'colofon': val[0]})
                vag = val[1] if val[1] else vag
            elif kind == 'sutta' and nip:
                # en Eka/Duka sólo cuenta la forma de párrafo; en el Tika, sólo la centrada
                reg = REGIMEN.get(nip, 'corrido')
                if reg == 'sutta_romano':
                    continue          # aquí los arábigos a sangría 5 son PÁRRAFOS, no suttas
                if reg == 'vagga_romano' and ind not in SUTTA_INDENT:
                    continue
                if reg == 'corrido' and ind < MIN_INDENT_CENTRED:
                    continue
                out.append({'nipata': nip, 'vagga': vag, 'num': val, 'page': pg, 'line': ln})
    return out
