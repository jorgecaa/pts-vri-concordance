#!/usr/bin/env python3
"""
uddana — gramática (pyparsing) de la **estrofa mnemotécnica** que cierra cada vagga en PTS.

El uddāna es, en el régimen numerado de AN, **el único sitio donde PTS nombra sus suttas**: el
impreso no titula. Y no los nombra de cualquier manera, sino en orden y declarando cuántos son
(`te dasa ti` = «éstos, diez»). Eso lo convierte en verdad-terreno estructural del lado PTS, del
mismo tipo que el front matter del volumen (`pts-front-matter-verdad-terreno`), pero a escala de
vagga.

Su valor real **no es desempatar** sino **detectar fusión y división**. En el Kamma-vagga de A ii
la estrofa da diez nombres —`Saṅkhitta vitthāra Soṇakāyana sikkhāpadaṃ ariyamaggo | Bojjhaṅgaṃ
sāvajjañ ceva avyāpajjhaṃ samaṇo ca sappurisānisaṃso ti`— y el CST imprime **once** suttas, porque
parte `sikkhāpada` en `Paṭhama-`/`Dutiya-`. Sin el uddāna esa división es invisible para el
contenido (los siete suttas del vagga abren con la misma fórmula palabra por palabra y el CST elide
justo lo que los diferencia), y el alineamiento monótono se corre una posición desde ahí.

**Invariante duro**: si `nombres(uddāna) == suttas(PTS)` en el vagga, el mapeo «nombre k-ésimo ↔
sutta k-ésimo» es exacto y **manda sobre el contenido**. Si no coincide, el vagga queda marcado y
la diferencia dice *cuántas* fusiones o divisiones hay que buscar. Nunca se adivina.

La estrofa no es una lista de palabras: tiene gramática, y por eso se analiza con **pyparsing**
(regla (2) de `CLAUDE.md`).

    cabecera   `Kammavaggo catuttho tass' uddānaṃ` / `tatr' uddānaṃ bhavati`
    cuerpo     nombres, con dos modificadores propios del verso:
               · **multiplicador**: `dve khatā` = *dos* Khata (dos suttas, un nombre);
                 `tayo agati`, `cattāro vohāra` — el numeral va DELANTE y multiplica al nombre;
               · **ordinal de comprobación**: `anusotaṃ pañcamaṃ` = «Anusota, el quinto» — no es
                 un sutta, es el propio impreso verificando la cuenta a mitad de estrofa.
    cierre     `te dasa ti`, `ca ti`, `vaggo ti`, `paṇṇāsako niṭṭhito`

⚠️ El ordinal de comprobación se **usa**, no se descarta: si `pañcamaṃ` cae detrás del quinto
nombre expandido, la lectura de la estrofa se confirma sola; si cae en otro sitio, la estrofa está
mal leída y el vagga no puede firmar nada. Es una comprobación cruzada gratis, dentro del dato.
"""
import json
import re
import sqlite3

import pali_norm
import pyparsing as pp

DPD = 'file:/dev/shm/dpd.db?mode=ro'

pp.ParserElement.set_default_whitespace_chars(' \t\n')

# numerales cardinales que multiplican al nombre siguiente
# ⚠️ Sólo del dos al cinco. `dasa` NO entra aunque sea un numeral: en el verso casi siempre es el
# cierre (`te dasa ti`, «éstos, diez»), y tomarlo por multiplicador convertía `atho ca dasa kāmaṃ`
# del Sappurisa-vagga en diez suttas llamados «Kāma». `aṭṭha`/`nava`/`cha` quedan fuera por lo
# mismo: coinciden con partículas y con principios de nombre.
MULT = {'dve': 2, 'tayo': 3, 'tini': 3, 'cataro': 4, 'catari': 4, 'panca': 5}
# ordinales: comprueban la posición, no son suttas
ORD = {'pathamam': 1, 'pathamo': 1, 'dutiyam': 2, 'dutiyo': 2, 'tatiyam': 3, 'tatiyo': 3,
       'catutham': 4, 'catutho': 4, 'pancamam': 5, 'pancamo': 5, 'chatham': 6, 'chatho': 6,
       'satamam': 7, 'satamo': 7, 'athamam': 8, 'athamo': 8, 'navamam': 9, 'navamo': 9,
       'dasamam': 10, 'dasamo': 10, 'ekadasamo': 11}
# partículas y fórmulas de cierre: métrica y sintaxis del verso, nunca nombres
PARTICULA = {'ca', 'cati', 'ceva', 'eva', 'va', 'pi', 'atho', 'ti', 'honti', 'hoti', 'te',
             'imani', 'tas', 'tasa', 'tatr', 'tatra', 'udanam', 'udanan', 'bhavati', 'vago',
             'vage', 'vageti', 'vagoti', 'panasako', 'panasakam', 'nithito', 'nithitam',
             'samato', 'samatam', 'apare', 'apara', 'puna', 'ceti', 'nama', 'vuta', 'vuca'}

# ≥3 letras: el verso deja fragmentos de una sola (`sañojanaṃ c' eva` → `c`) que no son nombres
_pal = pp.Regex(r'[a-z]{3,}')
_mult = pp.MatchFirst([pp.Keyword(k) for k in sorted(MULT, key=len, reverse=True)])('mult')
_ord = pp.MatchFirst([pp.Keyword(k) for k in sorted(ORD, key=len, reverse=True)])('ord')
_part = pp.MatchFirst([pp.Keyword(k) for k in sorted(PARTICULA, key=len, reverse=True)])
# un ítem del cuerpo: multiplicador opcional + nombre
# El multiplicador y su nombre pueden ir SEPARADOS por partículas del verso: `dve ca nānā`,
# `dve va honti samajīvino`. Exigirlos pegados cortaba la estrofa a la cuarta palabra.
_item = pp.Group(pp.Opt(_mult + pp.ZeroOrMore(pp.Suppress(_part)))
                 + ~_part + ~_ord + _pal('nombre'))
# ⚠️ El último alternativo es un COMEDOR de lo que no encaja, y no es un adorno: `pp.ZeroOrMore`
# se **detiene** en el primer token que no puede analizar, así que la `c` suelta de `c' eva` —una
# letra, ni partícula ni nombre— cortaba la estrofa entera. `Sambodhi nissayo c' eva Meghiyaṃ…`
# daba dos nombres en vez de diez, y el detector lo leía como una fusión de ocho suttas que no
# existe. Lo que no se reconoce se salta; lo que se reconoce, cuenta.
_basura = pp.Suppress(pp.Regex(r'\S+'))
_cuerpo = pp.ZeroOrMore(pp.Group(_ord)('check*') | pp.Suppress(_part) | _item | _basura)


# Fórmula de cierre: `te dasa ti`, `dasati`, `vaggo ti`, `paṇṇāsako niṭṭhito`. Se **corta** el
# texto ahí en vez de tratar `dasa` como partícula suelta: `dasa` también aparece dentro del verso
# (`atho ca dasa kāmaṃ`, `dasamagga`) y borrarlo en todas partes destruía nombres reales.
_CIERRE = re.compile(r'\b(?:te\s+(?:dasa|ekadasa|dvadasa|nava|atha|sata)\b|dasa\s*ti\b|dasati\b'
                     r'|vage\s*ti\b|vageti\b|panasak|nithit|samat[to])')


def _corta_cierre(t):
    m = _CIERRE.search(t)
    return t[:m.start()] if m else t


def _cabecera(t):
    """Recorta todo lo anterior a `uddānaṃ` (el colofón del vagga y su ordinal)."""
    m = None
    for k in ('udanam', 'udanan'):
        i = t.find(k)
        if i >= 0 and (m is None or i < m):
            m = i + len(k)
    return t[m:] if m is not None else t


def analiza(texto_plegado):
    """Estrofa plegada → `(nombres, comprobaciones, coherente)`.

    `nombres` va **expandido** por los multiplicadores: `dve khatā` aporta dos entradas con el
    mismo nombre, porque son dos suttas. `comprobaciones` son los ordinales hallados con la
    posición en que caen; `coherente` es False si alguno no cuadra con esa posición — señal de que
    la estrofa está mal leída y el vagga no puede firmar nada.
    """
    # Sin la palabra `uddāna` no hay estrofa: hay vaggas que cierran sólo con su colofón (todo el
    # Eka, varios del Dasaka). Analizar el colofón como si fuera la lista daba un nombre suelto y
    # el detector lo tomaba por una fusión masiva.
    if not any(k in texto_plegado for k in ('udanam', 'udanan')):
        return [], [], False
    cuerpo = _corta_cierre(_cabecera(texto_plegado))
    nombres, checks = [], []
    for tok in _cuerpo.parse_string(cuerpo, parse_all=False):
        if isinstance(tok, pp.ParseResults) and 'ord' in tok:
            checks.append((ORD[tok['ord']], len(nombres)))
            continue
        if isinstance(tok, pp.ParseResults) and 'nombre' in tok:
            n = MULT.get(tok.get('mult'), 1) if 'mult' in tok else 1
            nombres.extend([tok['nombre']] * n)
    coherente = all(pos == n for n, pos in checks)
    return nombres, checks, coherente


_FOLD = str.maketrans({'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṅ': 'n', 'ñ': 'n', 'ṇ': 'n',
                       'ṭ': 't', 'ḍ': 'd', 'ḷ': 'l', 'ṃ': 'm', 'ṁ': 'm'})


def pliega(t):
    t = pali_norm.normaliza(t or '').lower().translate(_FOLD)
    t = re.sub(r'[^a-z]+', ' ', t)
    return re.sub(r'(.)\1+', r'\1', t).strip()


# ─────────────────────── dvandvas del verso, con el DECONSTRUCTOR de DPD ───────────────────
# El verso funde nombres para que quepan en el metro: `…vesārajjaṃ **taṇhāyogena**` son DOS
# suttas —Taṇhā y Yoga— en una palabra, y `valāhakakumbhā` son Valāhaka y Kumbha. Por eso la
# estrofa da nueve nombres donde PTS marca diez, y no es ruido ni OCR: es la lengua del verso.
#
# DPD ya sabe deshacerlos (`lookup.deconstructor`: `taṇhāyogena → ["taṇhā + yogena"]`), así que no
# hay que inventar un segmentador. Pero el deconstructor se usa como **generador de candidatos,
# nunca como autoridad**: `bhattuddesena → bhatto + uddesena` es un compuesto de verdad y sin
# embargo es UN solo sutta (Bhattuddesa). La partición sólo se acepta si sus partes casan con
# títulos **consecutivos** del CST — es el CST quien decide, DPD sólo propone.
#
# ⚠️ Cobertura parcial, y la razón importa: las claves de DPD siguen la ortografía del CST y el
# uddāna va en la de PTS. `saññojanaṃ` (CST `saṃyojana`), `puññābhisandā` y `sappurisānisaṃso` no
# están en `lookup`. Sobre A ii el deconstructor parte tres dvandvas reales y sube de 11 a 13 los
# vaggas cuyo recuento cuadra; lo que queda fuera **no son compuestos**, son diferencias de
# ortografía entre las dos ediciones.
_dpd = None


def _conn():
    global _dpd
    if _dpd is None:
        _dpd = sqlite3.connect(DPD, uri=True)
    return _dpd


def dvandva(palabra):
    """Particiones que DPD propone para la palabra (en IAST, tal cual la imprime PTS).

    Devuelve `[[parte, …], …]` en orden de preferencia de DPD, sólo con partes de ≥3 letras.
    Lista vacía si la palabra no está o no es compuesta. **El llamador debe validar** cada
    partición contra los títulos del CST antes de usarla.
    """
    # Las claves de `lookup` van en la ortografía del CST y el uddāna en la de PTS: sin
    # normalizar, `saññojanaṃ` simplemente no está en la tabla.
    palabra = pali_norm.normaliza(palabra)
    try:
        r = _conn().execute('SELECT deconstructor FROM lookup WHERE lookup_key=?',
                            (palabra,)).fetchone()
    except sqlite3.Error:
        return []                    # la db en RAM puede no estar montada; no es un error fatal
    if not r or not r[0]:
        return []
    try:
        ana = json.loads(r[0])
    except ValueError:
        return []
    out = []
    for a in ana:
        ps = [p.strip() for p in a.split('+')]
        if len(ps) >= 2 and all(len(p) >= 3 for p in ps):
            out.append(ps)
    return out
