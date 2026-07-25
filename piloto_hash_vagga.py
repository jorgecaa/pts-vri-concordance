#!/usr/bin/env python3
"""
piloto_hash_vagga — prueba de la estrategia **vagga primero, contenido después**.

Idea que se pone a prueba (Jorge, 2026-07-25): no emparejar por número —que diverge entre
ediciones y ya nos ha engañado tres veces— sino en dos pasos:

1. **Bloqueo por vagga.** El vagga es la unidad que las dos ediciones sí comparten: PTS lo cierra
   con su colofón y el CST lo marca con un `<div rend="chapter">`. Emparejar vaggas reduce cada
   decisión a ~10 candidatos y hace imposible el error a larga distancia (el `+7` de S ii, el
   `+15` de AN) — un fallo dentro del vagga se ve; uno entre vaggas, no.
2. **Firma de contenido** sobre magnitudes que la elisión y la ortografía NO alteran:
   - **cantidad de palabras** (razón menor/mayor: una edición abrevia, pero no reescribe);
   - **progresión**: el orden de primera aparición de las palabras raras compartidas (correlación
     de rangos) — es lo que distingue dos suttas con el mismo vocabulario y distinto desarrollo;
   - **frecuencia**: las palabras raras del nipāta pesan, las de pericopa (`bhikkhave`, `katame`,
     `hoti`) no discriminan nada y se descartan por frecuencia documental.

Verdad-terreno: **A ii (Catukka)**, cuyas 268 filas están CONFIRMADO con par verificado
(`validador_an2_catukka.json`), así que el piloto se puede puntuar sin pedirle nada a nadie.

Uso: python3 piloto_hash_vagga.py
"""
import json
import math
import re
import sqlite3
from collections import Counter, defaultdict

import an_names as AN
import an_peyyala as ap
import uddana as UD
from align_rows import assign as ar_assign
from an1_markers import collect_an1

DB = 'src/data/tipitaka.sqlite'
STEM, BOOK, NIPATA = 's0402m3', 18, 'CATUKKA'
# El filtro duro por frecuencia documental se ha RETIRADO: con suttas cortos casi todo el
# vocabulario es raro (2352 de 2357 palabras pasaban el umbral del 20 %), así que no filtraba nada
# y en cambio tiraba las pocas palabras de pericopa que sí aportan algo de señal. En su lugar cada
# palabra pesa por su **idf**: `mātugāmo` decide, `bhikkhave` no, y no hay que elegir un corte.
PESOS = {'cov': 0.60, 'prog': 0.25, 'len': 0.15}
# Capa 3. El uddāna no compite con el contenido: lo DESEMPATA. Un peso pequeño no puede voltear un
# par que el contenido resuelve con holgura, pero sí decide entre candidatos que empatan — que es
# exactamente lo que pasa en el Kamma-vagga, donde los siete suttas abren con la misma fórmula
# palabra por palabra y el CST elide justo lo que los diferencia.
PESO_UDD = 0.12
_TIT = re.compile(r'^[\d\s.\-–]+|suttan?[ṃm]?$|suttā?ni$|suttādi.*$|.*sutt[āa]ni$', re.I)


# Partículas de la estrofa: métrica y conectores, no nombres de sutta.
_STOP = {'ti', 'ca', 'ceva', 'eva', 'cati', 'vago', 'udanam', 'udanan', 'tasa', 'tasudanam',
         'imani', 'vuca', 'nama', 'pathamo', 'dutiyo', 'tatiyo', 'catutho', 'pancamo', 'chatho',
         'satamo', 'athamo', 'navamo', 'dasamo', 'kama', 'sata', 'atha'}


def nombres_uddana(texto):
    """Estrofa → lista ORDENADA de nombres de sutta.

    El uddāna es la lista que PTS sí imprime: `Saṅkhitta vitthāra Soṇakāyana sikkhāpadaṃ
    ariyamaggo Bojjhaṅgaṃ sāvajjañ ceva avyāpajjhaṃ samaṇo ca sappurisānisaṃso ti`. Su
    **longitud es dato estructural**: ahí son diez nombres para los ONCE suttas del CST, porque
    el CST parte `sikkhāpada` en paṭhama/dutiya y PTS lo imprime como uno. Sin el uddāna eso es
    invisible y el alineamiento monótono se corre una posición desde ese punto (era el fallo
    `233 → 235`).
    """
    t = ap.fold(texto)
    if 'udanam' in t:
        t = t[t.index('udanam') + 6:]
    elif 'udanan' in t:
        t = t[t.index('udanan') + 6:]
    return [w for w in t.split() if len(w) >= 4 and w not in _STOP]


def raiz(w):
    return re.sub(r'[aiueom]+$', '', w)


def casa_nombre(a, b):
    """¿El nombre del uddāna y el título del CST son el mismo? Por contención de raíces."""
    ra, rb = raiz(ap.fold(a)), raiz(ap.fold(b))
    if len(ra) < 4 or len(rb) < 4:
        return False
    return ra.startswith(rb[:5]) or rb.startswith(ra[:5]) or ra in rb or rb in ra


def titulo_limpio(t):
    """`«2. Vitthārasuttaṃ»` → `«Vitthāra»`: fuera el ordinal del CST y la desinencia `-suttaṃ`."""
    return _TIT.sub('', _TIT.sub('', (t or '').strip())).strip()


def palabras(t):
    return [w for w in ap.fold(t).split() if len(w) >= 4]


# ── lado PTS: marcadores del impreso, y el vagga lo fija el COLOFÓN ─────────────────────────
def unidades_pts(conn):
    pgs = {r['page_no']: (r['unitext'] or '').split('\n')
           for r in conn.execute('SELECT page_no,unitext FROM pages WHERE edition="mula" '
                                 'AND book_no=?', (BOOK,))}
    marcas = [m for m in collect_an1(pgs)
              if m['nipata'] == NIPATA and (m['num'] is not None or m.get('colofon') is not None)]
    marcas.sort(key=lambda m: (m['page'], m['line']))
    plano = [(pg, ln, t) for pg in sorted(pgs) for ln, t in enumerate(pgs[pg], 1)]
    idx = {(pg, ln): i for i, (pg, ln, _t) in enumerate(plano)}
    out, vagga, udd = [], 1, {}
    for k, m in enumerate(marcas):
        if m.get('colofon') is not None:
            # El UDDĀNA va detrás del colofón y antes del primer sutta del vagga siguiente: es la
            # estrofa mnemotécnica que nombra, EN ORDEN, los suttas del vagga que se cierra. En
            # este régimen es el único sitio donde PTS los nombra (el impreso no titula suttas).
            i0 = idx[(m['page'], m['line'])]
            i1 = idx[(marcas[k + 1]['page'], marcas[k + 1]['line'])] if k + 1 < len(marcas) else len(plano)
            udd[vagga] = ap.deshifena([t for _p, _l, t in plano[i0:i1]])[0]
            vagga += 1
            continue
        i0 = idx[(m['page'], m['line'])]
        i1 = idx[(marcas[k + 1]['page'], marcas[k + 1]['line'])] if k + 1 < len(marcas) else len(plano)
        out.append({'num': m['num'], 'vagga': vagga, 'page': m['page'],
                    'w': palabras(' '.join(t for _p, _l, t in plano[i0:i1]))})
    return out, udd


# ── lado CST: el `div` ES el vagga en AN; el sutta es su `subhead` ──────────────────────────
def unidades_cst():
    u = [x for x in ap.cst_unidades(STEM) if x['n'] == 1 and x['subhead']]
    divs = []
    for x in u:
        if not divs or divs[-1] != x['div']:
            divs.append(x['div'])
    orden = {d: i + 1 for i, d in enumerate(divs)}
    return [{'pn': x['pn'], 'vagga': orden[x['div']], 'titulo': x['subhead'],
             'w': palabras(x['texto'])} for x in u]


# ── firma de contenido ─────────────────────────────────────────────────────────────────────
def rho(a, b):
    """Correlación de rangos de Spearman sobre las posiciones de primera aparición."""
    n = len(a)
    if n < 3:
        return 0.0
    d2 = sum((x - y) ** 2 for x, y in zip(a, b))
    return max(0.0, 1 - 6 * d2 / (n * (n * n - 1)))


def firma(ws):
    """Palabras del sutta en orden de PRIMERA aparición (la progresión), sin repetir."""
    visto, orden = set(), []
    for w in ws:
        if w not in visto:
            visto.add(w)
            orden.append(w)
    return orden


def puntua(fa, fb, na, nb, idf, fa_tf, fb_tf):
    """Firma ↔ firma. La cobertura va **ponderada por idf**, no por conteo de palabras.

    Es lo que rompe los empates: en las series de repetición (los diez `Puggala`, los cuatro
    `Duccarita`) los suttas comparten casi todo el vocabulario y la cobertura sin pesos daba
    exactamente el mismo número a tres candidatos seguidos. Lo que los distingue es una sola
    palabra rara —el término que cambia de un miembro al siguiente— y con idf esa palabra pesa
    tanto como veinte de pericopa.

    El denominador es el **lado menor** a propósito: una edición elide y la otra no, y penalizar
    por lo que la abreviada no imprime castigaría justo a los pares correctos del peyyāla.
    """
    A, B = set(fa), set(fb)
    if not A or not B:
        return 0.0, {}
    com = A & B
    # Cobertura sobre **frecuencias**, no sobre presencia: `Σ idf(w)·min(tf_a, tf_b)`. Los empates
    # que quedaban tras el idf son series cuyo VOCABULARIO es idéntico y sólo cambia cuántas veces
    # se repite cada término (el impreso desarrolla lo que el CST abrevia con `…pe…`), de modo que
    # con conjuntos los tres candidatos daban exactamente el mismo número. Con tf el empate se
    # rompe sin inventar ninguna señal nueva: es la misma palabra, contada.
    peso = lambda cnt: sum(idf.get(w, idf['__max__']) * n for w, n in cnt.items())
    ca, cb = Counter(fa_tf), Counter(fb_tf)
    menor = ca if peso(ca) <= peso(cb) else cb
    inter = Counter({w: min(ca[w], cb[w]) for w in com})
    cov = peso(inter) / max(1e-9, peso(menor))
    pa = {w: i for i, w in enumerate(fa)}
    pb = {w: i for i, w in enumerate(fb)}
    orden = sorted(com, key=lambda w: pa[w])
    ra = list(range(len(orden)))
    rb = [sorted(orden, key=lambda w: pb[w]).index(w) for w in orden]
    pr = rho(ra, rb)
    ln = min(na, nb) / max(na, nb)
    s = PESOS['cov'] * cov + PESOS['prog'] * pr + PESOS['len'] * ln
    return s, {'cov': round(cov, 2), 'prog': round(pr, 2), 'len': round(ln, 2)}


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    (P, UDD), C = unidades_pts(conn), unidades_cst()

    df = Counter()
    for x in C:
        df.update(set(x['w']))
    N = len(C)
    idf = {w: math.log(N / c) for w, c in df.items()}
    idf['__max__'] = math.log(N)          # palabra que sólo está en PTS: máximamente distintiva

    for x in P + C:
        x['f'] = firma(x['w'])

    # ⚠️ La verdad-terreno es una RELACIÓN, no una función. Un marcador de PTS puede servir a
    # VARIOS suttas del CST: en A ii el nº 174 imprime seguidos el Mahākoṭṭhika (CST 173) y el
    # Ānanda (CST 174), y el Excel los distingue por línea (`A ii 161,2` y `A ii 162,4`). Leerla
    # como diccionario descartaba silenciosamente uno de los dos y contaba como fallo del piloto
    # lo que era un acierto — el mismo tipo de error que el piloto existe para cazar.
    verdad = {}
    for r in json.load(open('validador_an2_catukka.json')):
        if r.get('estado') == 'CONFIRMADO' and r.get('pts_num'):
            verdad.setdefault(r['pts_num'], set()).add(int(r['num'].split('.')[1]))

    print('=' * 92)
    print('PILOTO — A ii (Catukka): bloqueo por vagga + firma de contenido')
    print('=' * 92)
    print(f'PTS: {len(P)} suttas en {max(x["vagga"] for x in P)} vaggas | '
          f'CST: {len(C)} suttas en {max(x["vagga"] for x in C)} vaggas | '
          f'vocabulario: {len(df)} palabras, idf de {min(idf.values()):.2f} a {math.log(N):.2f}')

    porvagga = defaultdict(list)
    for x in C:
        porvagga[x['vagga']].append(x)

    pts_vagga = defaultdict(list)
    for x in P:
        pts_vagga[x['vagga']].append(x)

    # Dentro del vagga, asignación MONÓTONA (no argmax independiente): las dos ediciones imprimen
    # el vagga en el mismo orden, así que el orden es evidencia — y es lo que desempata las series
    # de repetición, donde varios suttas comparten vocabulario y la puntuación queda empatada.
    elegido, top1, tot, mismo_vagga = {}, 0, 0, 0
    udd_ok = udd_tit = 0
    cuadra = []
    for v, ps in sorted(pts_vagga.items()):
        cs = porvagga.get(v, [])
        if not cs:
            continue
        M = [[puntua(p['f'], c['f'], len(p['w']), len(c['w']), idf, p['w'], c['w'])[0]
              for c in cs] for p in ps]
        # ── capa 3: INVARIANTE DURO del uddāna ─────────────────────────────────────────────
        # La estrofa se analiza con su gramática (`uddana.py`, pyparsing) y sus dvandvas se
        # deshacen con el deconstructor de DPD, **validando cada partición contra dos títulos
        # CONSECUTIVOS del CST** — DPD propone, el CST decide.
        #
        # Si el nº de nombres resultante coincide con el nº de suttas que PTS imprime en el vagga,
        # el mapeo «nombre k-ésimo ↔ sutta k-ésimo» es exacto y **manda sobre el contenido**: no
        # es un bonus, sustituye la puntuación. Si no coincide, no se toca nada y la diferencia
        # queda anotada — dice cuántas fusiones o divisiones hay que buscar. Nunca se adivina.
        nom, _checks, coherente = UD.analiza(ap.fold(UDD.get(v, '')))
        crudo = {}
        for w in re.findall(r"[A-Za-zāīūṅñṇṭḍḷṃṁ']+", UDD.get(v, '')):
            crudo.setdefault(ap.fold(w).strip(), w.strip("'"))
        T = [c['titulo'] for c in cs]
        exp, j = [], 0
        for n in nom:
            cr = crudo.get(n, n)
            partido = False
            for partes in UD.dvandva(cr):     # ojo: `ps` es el vagga de PTS, no reusar el nombre
                if j + len(partes) <= len(T) and all(AN.score(T[j + k], p) >= 60
                                                     for k, p in enumerate(partes)):
                    exp += partes
                    j += len(partes)
                    partido = True
                    break
            if not partido:
                exp.append(cr)
                while j < len(T) and AN.score(T[j], cr) < 60:
                    j += 1
                j += 1
        if nom:
            udd_ok += 1
            udd_tit += sum(1 for n in exp if any(AN.score(c['titulo'], n) >= 60 for c in cs))
        # El invariante sólo puede mandar si la lectura de la estrofa se sostiene ENTERA. No basta
        # con que el recuento cuadre: hay que exigir que cada nombre case con **exactamente un**
        # título y que los títulos casados vayan en orden ESTRICTAMENTE CRECIENTE. Sin esas dos
        # condiciones el invariante se dispara sobre un vagga mal leído y, como manda sobre el
        # contenido, impone el error en vez de corregirlo: con el recuento a secas pasó de 3
        # fallos a 10, y siete eran de un solo vagga.
        casadas = ([[k for k, c in enumerate(cs) if AN.score(c['titulo'], n) >= 60] for n in exp]
                   if nom and coherente and len(exp) == len(ps) else None)
        firme = (casadas is not None and all(len(x) == 1 for x in casadas)
                 and all(casadas[i][0] < casadas[i + 1][0] for i in range(len(casadas) - 1)))
        # ⚠️ HALLAZGO que obliga a NO imponer el mapeo: el uddāna nombra los suttas **del vagga**,
        # y eso NO es lo mismo que los marcadores numerados de PTS. En el Sañcetaniya-vagga la
        # estrofa se lee perfecta —diez nombres, cada uno con un único título del CST, en orden
        # estricto, y el `pañcamaṃ` cae en el quinto— y aun así el mapeo «nombre k ↔ marcador k»
        # es falso: PTS **parte en dos** (sus nº 171 y 172) lo que la estrofa y el CST nombran una
        # sola vez (`Cetanā`), de modo que a partir de ahí sus marcadores van corridos uno.
        #
        # O sea que el uddāna es verdad-terreno del CONTENIDO del vagga, no de la numeración de
        # PTS, y la desigualdad `nombres ≠ marcadores` es justamente la señal de que PTS ha
        # partido o fundido algo. Por eso aquí sólo se ANOTA: imponerlo metía el error en vez de
        # corregirlo (de 3 fallos a 10 con el recuento a secas, y el único vagga que pasaba el
        # filtro estricto también salía mal).
        if firme:
            cuadra.append(v)

        idx = ar_assign(len(ps), len(cs), lambda i, j: max(M[i][j], 0.001), lambda j: 1,
                        skip_penalty=0.5)
        for i, j in enumerate(idx):
            elegido[ps[i]['num']] = (cs[j]['pn'] if j is not None else None,
                                     sorted(((M[i][k], cs[k]['pn']) for k in range(len(cs))),
                                            key=lambda t: -t[0])[:3])
    fallos = []
    for p in P:
        real = verdad.get(p['num'])
        if not real:
            continue
        tot += 1
        if any(c['pn'] in real for c in porvagga.get(p['vagga'], [])):
            mismo_vagga += 1
        prop, rank = elegido.get(p['num'], (None, []))
        if prop in real:
            top1 += 1
        else:
            fallos.append((p['num'], sorted(real), prop, [(round(s, 2), n) for s, n in rank]))
    top3 = tot - len(fallos)
    empates = sum(1 for p in P if p['num'] in elegido and len(elegido[p['num']][1]) > 1
                  and round(elegido[p['num']][1][0][0], 3) == round(elegido[p['num']][1][1][0], 3))

    print(f'\ncon verdad-terreno: {tot} suttas')
    print(f'  el par correcto cae en el vagga bloqueado: {mismo_vagga}/{tot} '
          f'({100 * mismo_vagga / max(1, tot):.1f} %)')
    print(f'  acierto con asignación monótona en el vagga: {top1}/{tot} '
          f'({100 * top1 / max(1, tot):.1f} %)')
    print(f'  filas con EMPATE en la cabeza de la puntuación:  {empates}/{len(P)}')
    print(f'  uddāna: {udd_ok}/{len(pts_vagga)} vaggas con estrofa · '
          f'{udd_tit} nombres casados con un título del CST · '
          f'{len(cuadra)} vaggas donde nº de nombres = nº de suttas de PTS')
    if fallos:
        print(f'\nfallos ({len(fallos)}):')
        for n, real, prop, ss in fallos[:20]:
            print(f'   PTS {n:>4} → real {real} | propuesto {prop} | mejores {ss}')


if __name__ == '__main__':
    main()
