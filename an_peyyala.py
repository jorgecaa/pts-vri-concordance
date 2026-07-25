#!/usr/bin/env python3
"""
an_peyyala — **quinto régimen de AN**: los tramos donde una edición ELIDE lo que la otra numera.

Los cuatro alineadores de A ii–A v (`validador_an2_catukka.py`, `_an3`, `_an4`, `_an5`) resuelven
el régimen *numerado*: un marcador de PTS por sutta, un `subhead` del CST por sutta, y el
emparejamiento va uno a uno. Al final de cada nipāta ese régimen **se acaba** —las colas
(*sammuti-*, *sikkhāpada-* y *rāga-peyyāla*, los *vaggas* de «tags» de Hardy) se imprimen
abreviadas— y allí los alineadores dejaban las filas fuera, no por error suyo sino porque el
supuesto «un sutta ↔ una unidad» ya no se cumple:

| tramo | PTS | CST |
|---|---|---|
| A ii 256-257 (`4.277-783`) | **un solo sutta numerado** (`271.`) con 4 párrafos internos | dos `<p>` de rango: `277-303` y `304-783` |
| A iii 271-278 (`5.251-1151`) | bloques separados por **ornamento** (`U+E0E0`), y uno cubre varios | `subhead` de rango (`7-13. Dutiyajhānasuttādisattakaṃ`) |
| A iv 144-148 / 347-349 | bloques separados por **raya** (`-{10,}`) | idem |
| A iv 462-465 (`9.73-94`) | **marcador de RANGO en romano** (`LXXIII-LXXXI.`) + uddāna | 73 individual, el resto en grupo |
| A v 303-310 (`10.221-236`) | 7 suttas numerados (`CCX.`…) | `div` **sin `subhead`**: sólo `<p n=…>` sueltos y de rango |
| A v 359-360 (`11.22-29`) | **un** bloque con el símil del gopālaka y la serie elidida | un `<p n="22-29">` |

Tres consecuencias de diseño, todas aprendidas en SN:

1. **La clave sigue siendo el paranum del VRI** (regla (5) de `CLAUDE.md`). En A ii–A v el
   `Sutta #` del Excel **es** el paranum: comprobado en las **1099** filas ya CONFIRMADO de estos
   cuatro volúmenes, sin una sola excepción (en A i, en cambio, hay un +1 desde el paranum 49, así
   que esto **no** se extrapola).
2. **Los `<p>` de rango del CST se expanden por paranum**, con compuerta: el grupo `277-303` da 27
   unidades que comparten texto. Es el mismo arreglo que `massive_reader.py` hace en SN, y por el
   mismo motivo: sin él, 27 filas compiten por una única unidad y el alineamiento monótono tira 26.
3. **La prueba es MECÁNICA, no del LLM.** Cuando las dos ediciones eliden no hay texto que cotejar
   y el REJECT de Gemini es un falso negativo por elisión (`STATUS.md`, clase peyyāla de S v). Lo
   que sí se puede exigir —y aquí se exige— es que el **término distintivo de cada fila aparezca
   LITERALMENTE y EN ORDEN** en el texto de sus dos contrapartes. Es una prueba fuerte: el
   *rāga-peyyāla* del Catukka enumera sus nueve términos (`pariññāya`, `parikkhayāya`, `pahānāya`,
   `khayāya`, `vayāya`, `virāgāya`, `nirodhāya`, `cāgāya`, `paṭinissaggāya`) en el mismo orden en
   PTS y en el CST, y la aritmética del rango lo confirma (27 = 9 × 3).

⚠️ **El texto de PTS va HIFENADO.** `bhattudde-\nsako` es una sola palabra partida por el salto de
línea del impreso, y buscar `bhattuddesako` sin recomponerla no encuentra nada. Se deshifena antes
de normalizar; la llamada de nota (`uddiṭṭhānuddiṭṭhaṃ1`) también se quita, pero **quitando sólo el
dígito**, nunca la palabra: ninguna transformación puede perder texto (regla del punto ciego).
"""
import re
import xml.etree.ElementTree as ET

import pali_norm

XMLDIR = '/tmp/tipitaka-xml/romn'

_FOLD = str.maketrans({'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṅ': 'n', 'ñ': 'n', 'ṇ': 'n',
                       'ṭ': 't', 'ḍ': 'd', 'ḷ': 'l', 'ṃ': 'm', 'ṁ': 'm', 'ṣ': 's', 'ś': 's'})

# ornamento (A iii) y raya (A iv/A v): las dos formas del mismo separador de suttas del impreso
VENTANA = 400      # caracteres plegados (~60 palabras): radio en el que se busca el término
# Salto máximo respecto a la fila anterior. Sin este tope, una fila cuyo término NO está en el
# impreso —PTS elide a veces miembros que el CST sí enumera: su lista del *sikkhāpada-peyyāla* pasa
# de `sāmaṇerā` a `upāsikā` sin nombrar `upāsaka` ni `sāmaṇerī`— casa con una aparición lejana y
# **se lleva por delante a todas las siguientes**, porque la monotonía ya no puede retroceder. Con
# el tope, esa fila se declara no situada y la serie continúa. En el Pañcaka de A iii recuperaba
# medio tramo.
MAX_SALTO = 1200

_SEPARADOR = re.compile(r'^(?:{3,}|-{8,})$')


def fold(t):
    """Texto comparable: sin diacríticos, sin llamadas de nota, sin puntuación, en minúsculas.

    Colapsa además las letras dobles (`sammannitabbo` ≡ `sammanitabbo`, que el impreso escribe de
    las dos maneras en la misma página) — el mismo colapso que `an_names._root`.
    """
    # Primero a la convención VRI (`pali_norm`), y sólo después el plegado. El orden importa:
    # `vyākata` y `byākata` pliegan distinto (`vyakata` / `byakata`) y no casarían nunca, y
    # `saññojana` pliega a `sanojana` mientras el CST da `samyojana`. Normalizar después del
    # plegado no sirve — las reglas necesitan los diacríticos que el plegado ya ha borrado.
    t = pali_norm.normaliza(t or '').lower().translate(_FOLD)
    t = re.sub(r'[^a-z]+', ' ', t)
    return re.sub(r'(.)\1+', r'\1', t)


def deshifena(lineas):
    """Une las líneas de una página deshaciendo la partición de palabra del impreso.

    Devuelve `(texto, mapa)`, donde `mapa[i]` es el nº de línea (1-based) del carácter `i` del
    texto. Hace falta para poder situar una coincidencia en su línea y emitir la `PTS Ref`.
    """
    buf, mapa = [], []
    for ln, raw in enumerate(lineas, 1):
        s = raw.replace('\r', '').replace('⁣', '').rstrip()
        if not s.strip():
            continue
        s = s.strip()
        corta = s.endswith('-')
        s = s[:-1] if corta else s + ' '
        buf.append(s)
        mapa.extend([ln] * len(s))
    return ''.join(buf), mapa


class TextoPTS:
    """Texto continuo de un tramo de páginas de PTS, con posición → (página, línea)."""

    def __init__(self, conn, book, p_lo, p_hi):
        # El APARATO CRÍTICO es parte de la edición y a veces es el único sitio donde PTS escribe
        # el nombre: en A iii 276 el cuerpo imprime `sāmaṇerā` y `upāsikā`, y las notas al pie dan
        # `1 M. S. sāmaṇero sāmaṇerī` y `2 M. T. M6. M7 upāsako upāsikā` — o sea los cuatro suttas
        # que el CST numera por separado. Se guarda por página y se consulta aparte: no entra en
        # la serie monótona del cuerpo, pero atestigua la lectura.
        self.aparato = {r['page_no']: fold(r['unitext'] or '')
                        for r in conn.execute(
                            'SELECT page_no,unitext FROM footnotes WHERE edition="mula" '
                            'AND book_no=? AND page_no BETWEEN ? AND ?', (book, p_lo, p_hi))}
        self.crudo, self.pos, self.paginas = [], [], {}
        for r in conn.execute('SELECT page_no,unitext FROM pages WHERE edition="mula" '
                              'AND book_no=? AND page_no BETWEEN ? AND ? ORDER BY page_no',
                              (book, p_lo, p_hi)):
            lineas = (r['unitext'] or '').split('\n')
            self.paginas[r['page_no']] = lineas
            t, mapa = deshifena(lineas)
            self.crudo.append(t)
            self.pos.extend((r['page_no'], ln) for ln in mapa)
        self.crudo = ''.join(self.crudo)
        # La normalización a VRI va sobre el texto ENTERO, no carácter a carácter: sus reglas son
        # contextuales (`vy`→`by`, la `m` final, la nasal homorgánica) y aplicadas a un carácter
        # suelto no ven nada. Se puede hacer sin romper el mapa de posiciones porque **todas las
        # reglas conservan la longitud en caracteres** (`viriy`→`vīriy` cambia `i` por `ī`, no
        # añade nada); la aserción lo garantiza y avisaría si alguna regla nueva dejara de serlo.
        norm = pali_norm.normaliza(self.crudo)
        assert len(norm) == len(self.crudo), 'pali_norm debe conservar la longitud del texto'
        self.crudo = norm
        # `fold` es carácter-a-carácter salvo por el colapso de dobles y de espacios: para poder
        # llevar el mapa de posiciones se pliega **conservando el índice de origen**.
        self.plano, self.idx = [], []
        prev = None
        for i, ch in enumerate(self.crudo):
            c = fold(ch)
            if not c or c == ' ':
                c = ' '
            if c == ' ' and prev == ' ':
                continue
            if c == prev and c != ' ':
                continue                      # letra doble colapsada
            self.plano.append(c)
            self.idx.append(i)
            prev = c
        self.plano = ''.join(self.plano)

    def buscar(self, sonda, desde=0):
        """Primera aparición literal de `sonda` (ya plegada) a partir de `desde`. → índice o None."""
        k = self.plano.find(sonda, desde)
        return None if k < 0 else k

    def locus(self, k):
        """Índice del texto plano → `(página, línea)`."""
        return self.pos[self.idx[k]]

    def bloques(self):
        """Cortes del tramo en bloques del impreso: separador, numeral centrado o cabecera.

        Devuelve `[(inicio, fin, página, línea)]` en índices del texto plano. Un bloque **no** es
        un sutta: en el *sammuti-peyyāla* de A iii uno solo cubre trece (`273-285`), y en A ii el
        tramo entero es un único sutta numerado. Sirve para acotar el cotejo, no para contar.
        """
        cortes = []
        off = 0
        for pg in sorted(self.paginas):
            t, mapa = deshifena(self.paginas[pg])
            for ln, raw in enumerate(self.paginas[pg], 1):
                s = raw.replace('\r', '').strip()
                if _SEPARADOR.match(s.replace(' ', '')):
                    cortes.append((pg, ln))
            off += len(t)
        # traducir (pg,ln) a índice del texto plano: primer carácter de esa línea o el siguiente
        out, marcas = [], []
        for pg, ln in cortes:
            k = next((j for j, i in enumerate(self.idx)
                      if self.pos[i] == (pg, ln) or self.pos[i] > (pg, ln)), None)
            if k is not None:
                marcas.append((k, pg, ln))
        marcas.sort()
        lim = [0] + [m[0] for m in marcas] + [len(self.plano)]
        for a, b in zip(lim, lim[1:]):
            if b > a:
                out.append((a, b, *self.locus(a)))
        return out


def cst_unidades(stem, lo=None, hi=None):
    """Párrafos del CST **expandidos por paranum**: una unidad por sutta, aunque el `<p>` agrupe.

    Cada unidad trae `grupo=(a,b)` y `k` (posición dentro del grupo, 0-based) para poder exigir
    que el término de la fila caiga en el sitio que le toca dentro del texto elidido.
    `subhead` puede ser `None`: en el *Sāmañña-vagga* de A v el `div` no lleva ninguno.
    """
    root = ET.parse(f'{XMLDIR}/{stem}.mul.xml').getroot()
    out = []
    for d in root.iter('div'):
        h = d.find('head')
        if h is None or h.get('rend') != 'chapter':
            continue
        div = ' '.join(''.join(h.itertext()).split())
        sub = None
        for p in d.iter('p'):
            rend = p.get('rend')
            txt = ' '.join(''.join(p.itertext()).split())
            if rend == 'subhead':
                sub = txt
                continue
            m = re.match(r'(\d+)(?:-(\d+))?$', p.get('n') or '')
            if not m:
                # ⚠️ Párrafo de CONTINUACIÓN: el CST sólo pone `n` en el PRIMER `<p>` de cada
                # sutta, y los siguientes van sin atributo. Descartarlos tiraba el **74 % del
                # texto** de `s0403m1` — y con él, justo la parte que enumera los miembros de los
                # grupos elididos (`Sāṭiyaggāhāpako na sammannitabbo…` vivía en uno de ellos). Se
                # agregan a la unidad anterior, que es a quien pertenecen.
                if out and rend in ('bodytext', 'gatha1', 'gatha2', 'gatha3', 'gathalast'):
                    grupo = out[-1]['grupo']
                    for u in out:
                        if u['grupo'] == grupo:
                            u['texto'] += ' ' + txt
                continue
            a, b = int(m.group(1)), int(m.group(2) or m.group(1))
            unidades = []
            for k, pn in enumerate(range(a, b + 1)):
                if (lo is not None and pn < lo) or (hi is not None and pn > hi):
                    continue
                unidades.append({'pn': pn, 'div': div, 'subhead': sub, 'texto': txt,
                                 'grupo': (a, b), 'k': k, 'n': b - a + 1})
            out.extend(unidades)
    out.sort(key=lambda u: u['pn'])
    return out


# ruido del nombre del Excel que no es término distintivo de nada
_RUIDO = re.compile(r'\b(peyyala|peyyāla|adi|ādi|sutta|suttam|vagga|dvadasa|dasaka)\b', re.I)


def sondas(nombre):
    """Términos buscables del `Sutta Name` del Excel, ya plegados y de más largo a más corto.

    Se prueban **todas** las variantes: Morris imprime la del CST entre corchetes tan a menudo
    como al revés (`Macchariya [Pañcamacchariya]`), y quedarse con una sola pierde la mitad.
    """
    out = []
    for parte in re.split(r'[\[\]()/,]', nombre or ''):
        parte = _RUIDO.sub(' ', parte)
        for w in re.split(r'\s+', parte.strip()):
            w = fold(re.sub(r'\d+', '', w)).strip()
            # el mínimo es 3 y no 4 porque `issā` pliega a `isa`: con 4 el *rāga-peyyāla* del
            # Catukka se quedaba sin término para su séptimo kilesa y la serie entera fallaba
            if len(w) >= 3:
                out.append(w)
            # …y además la RAÍZ, sin la desinencia: el Excel nombra `Sāmaṇera` y el impreso
            # escribe `sāmaṇero upaṭṭhāpetabbo`. Buscar la palabra entera no encuentra nada;
            # la raíz (`samaner`) casa con las dos. Se emiten las dos formas y decide la rareza.
            # `-ādi` («y siguientes») no es parte del nombre sino la marca de serie del Excel:
            # `Dosādi peyyāla` es el peyyāla de *dosa*, y `Bhallikādi` el grupo que abre
            # *Bhallika*. Sin quitarlo, la sonda `dosadi` no existe en ningún impreso.
            # `-ādi` otra vez con sandhi: `dosa` + `ādi` se escribe `dosādi`, así que quitar las
            # tres letras deja `dos` —que ni es palabra ni cubre el 60 % de `dosassa`— cuando el
            # stem es `dosa`. Se emiten las dos formas, con la vocal restituida y sin ella.
            if len(w) > 5 and w.endswith('adi'):
                out.append(w[:-3] + 'a')
                w = w[:-3]
            # `apara-` («otro, ulterior») es prefijo SERIAL, no parte del nombre: marca la segunda
            # vuelta de una serie que ya se ha impreso (`Aparapaṭhamajjhāna` es el `Paṭhamajjhāna`
            # de la segunda tanda), y el impreso no lo escribe. Se emite también la forma sin él y
            # la monotonía se encarga de coger la aparición que toca — la SEGUNDA.
            if w.startswith('apara') and len(w) > 9:
                out.append(w[5:])
                # …y con la vocal RESTITUIDA. `apara` + `anāgāmi` se escribe `aparānāgāmi`: el
                # sandhi funde las dos vocales, así que quitar los cinco caracteres deja
                # `nāgāmi…`, que no existe. Hay que devolver la `a` inicial para volver a
                # `anāgāmiphala`, que es lo que imprime PTS.
                out.append('a' + w[5:])
            r = re.sub(r'[aiueom]+$', '', w)
            if len(w) >= 3:
                out.append(w)
            if len(r) >= 3 and r != w:
                out.append(r)
    # …y los SUFIJOS largos, porque el Excel escribe junto lo que el impreso separa:
    # `Cakkhudukkhānupassī` es `cakkhusmiṃ dukkhānupassī` en A iv 146, y ningún prefijo de la
    # forma compuesta lo alcanza. Se exigen ≥7 caracteres —el sufijo es una sonda ciega, no una
    # raíz— y la cobertura mínima de `_apariciones` impide que casen con cualquier cosa.
    for w in list(out):
        for k in range(1, len(w) - 6):
            if len(w) - k >= 7:
                out.append(w[k:])
    # Y los PREFIJOS, hasta 5 caracteres. El impreso parte los compuestos que el Excel escribe
    # juntos: `Macchariyapahāna` se lee `macchariyānaṃ pahānāya` en A iii 272, y exigir el
    # compuesto entero no encuentra nada. El prefijo `machariya` sí, y la monotonía lo coloca en
    # su sitio (la aparición SIGUIENTE a la del sutta anterior, que es justo la que le toca).
    # Se conservan de más largo a más corto para poder informar de **con qué fuerza** casó cada
    # fila: una sonda corta prueba menos y la salida lo dice.
    vistos, res = set(), []
    for w in sorted(out, key=len, reverse=True):
        # la palabra entera SIEMPRE (aunque sea corta: `dosa`, `moha`, `māyā`, `mada` son cuatro
        # de los dieciséis kilesa del peyyāla), y luego sus prefijos hasta 5
        for k in [len(w)] + list(range(len(w) - 1, 4, -1)):
            if w[:k] not in vistos:
                vistos.add(w[:k])
                res.append(w[:k])
    return res


COBERTURA_MIN = 0.6      # la sonda debe SER la palabra, no sólo su principio


def _apariciones(plano, sonda):
    """Posiciones de la sonda como PALABRA (con espacio delante), no como subcadena.

    Sin el límite, `khayaya` casa dentro de `parikhayaya` y `mada` dentro de `pamada`: los dos
    pares existen, consecutivos, en el mismo peyyāla del Catukka, y sin límite la serie se
    «prueba» a sí misma en el sitio equivocado.

    ⚠️ Y no basta con el límite por la izquierda: la sonda tiene que **cubrir al menos el 60 % de
    la palabra** que casa. `Sāmaṇerī` se quedaba en la sonda `saman` —porque `samaner` ya no
    estaba al alcance— y casaba con `samannāgatā`, que aparece **65 veces** en el tramo: una
    coincidencia vacía que firmaba la fila con nada. Exigir que la sonda sea la palabra, y no su
    principio, es lo que distingue una prueba de una casualidad.
    """
    out = []
    for m in _posiciones(plano, ' ' + sonda):
        fin = plano.find(' ', m + 1)
        largo = (len(plano) if fin < 0 else fin) - (m + 1)
        if len(sonda) >= COBERTURA_MIN * largo:
            out.append(m + 1)
    if plano.startswith(sonda):
        fin = plano.find(' ')
        if len(sonda) >= COBERTURA_MIN * (len(plano) if fin < 0 else fin):
            out.insert(0, 0)
    return out


def _posiciones(plano, s):
    out, k = [], plano.find(s)
    while k >= 0:
        out.append(k)
        k = plano.find(s, k + 1)
    return out


def buscar_palabra(plano, sonda):
    """¿Aparece la sonda como palabra (con la misma exigencia de cobertura)? → bool."""
    return bool(_apariciones(plano, sonda))


def serie_monotona(plano, filas, desde=0):
    """Sitúa una serie de filas en un texto exigiendo aparición LITERAL y en ORDEN.

    `filas` es `[(clave, [sondas])]`. Devuelve `({clave: (posición, sonda)}, [claves sin situar])`.
    La monotonía es **dura** —cada fila se busca a partir de la anterior situada— pero una fila que
    no case no tumba la serie: se anota como no situada y la búsqueda sigue desde donde estaba. Sin
    eso, un solo nombre que el impreso escribe de otra manera dejaba las 76 filas del tramo sin
    diagnóstico y era imposible ver cuáles sí estaban probadas.

    De las sondas de una fila se toma la **más rara** del texto, no la primera que case: `Rāga
    pariññāya peyyāla` da `raga` y `pariññāya`, y `raga` aparece en las nueve filas de la serie
    (encabeza cada término), así que casaría siempre en el sitio donde ya estamos y la serie
    entera «avanzaría» sin probar nada. La rara es la que discrimina.
    """
    pos, sin, cur = {}, [], desde
    for clave, ss in filas:
        cand = []
        for s in ss:
            ap = _apariciones(plano, s)
            sig = [k for k in ap if cur <= k <= cur + MAX_SALTO]
            if sig:
                cand.append((-len(s), len(ap), sig[0], s))
        if not cand:
            sin.append(clave)
            continue
        # Manda la sonda MÁS LARGA (la que más prueba) **de entre las cercanas**. Sin la ventana,
        # una sonda larga que sólo aparece páginas después se lleva la fila y descoloca a todas
        # las siguientes (en el *rāga-peyyāla* del Catukka tumbaba seis de veinticinco); y sin
        # preferir la larga, una sonda corta y ubicua —`raga`, que encabeza los nueve términos—
        # casa siempre donde ya estamos y la serie «avanza» sin probar nada.
        # De entre las sondas CERCANAS manda la más RARA (y a igual rareza, la más larga). La
        # rareza es la que discrimina: en el Navaka, `9.75 Nīvaraṇa sammappadhāna` y sus ocho
        # hermanas comparten `sammappadhāna`, así que preferir la sonda larga hacía casar a las
        # nueve con la MISMA palabra en posiciones sucesivas — monótono y vacío, que es justo el
        # modo de fallo contra el que existe esta prueba. `nīvaraṇa` aparece una vez y decide.
        cerca = min(c[2] for c in cand) + VENTANA
        elegida = min([(c[1], c[0], c[2], c[3]) for c in cand if c[2] <= cerca])
        elegida = (0, 0, elegida[2], elegida[3])
        pos[clave] = (elegida[2], elegida[3])
        cur = elegida[2] + 1
    return pos, sin
