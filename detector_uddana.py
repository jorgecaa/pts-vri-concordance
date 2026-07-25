#!/usr/bin/env python3
"""
detector_uddana — mapa de **divisiones y fusiones** entre PTS y el CST, vagga por vagga, en AN.

Qué hace y por qué, en una frase: el uddāna que PTS imprime al cerrar cada vagga **nombra sus
suttas, en orden y diciendo cuántos son**, así que comparar `nombres(uddāna)` con
`marcadores(PTS)` y con `suttas(CST)` señala, sin LLM y sin cotejar una línea de texto, dónde una
edición parte o funde lo que la otra numera de una pieza.

Es la única señal que ve esas asimetrías. El contenido no puede: en el *Kamma-vagga* de A ii los
siete suttas abren con la misma fórmula palabra por palabra y el CST elide justo lo que los
diferencia, de modo que su firma de contenido es idénticamente idéntica y el alineamiento monótono
se corre una posición sin que nada chirríe. El uddāna lo canta: diez nombres, once suttas en el
CST — que parte `sikkhāpada` en `Paṭhama-`/`Dutiya-`.

⚠️ **El uddāna NO es autoridad sobre la numeración de PTS, sólo sobre el contenido del vagga.**
Verificado contra el impreso en el *Sañcetaniya-vagga* (A ii 157-167): la estrofa se lee perfecta
—diez nombres, cada uno con un único título del CST, en orden, y el `pañcamaṃ` en su sitio— y aun
así «nombre k ↔ marcador k» es falso, porque PTS **parte** el `Cetanā` del CST en dos marcadores
(171 y 172, el segundo es el `cattāro attabhāvapaṭilābhā`) y **funde** el Mahākoṭṭhika y el Ānanda
en uno solo (174, que imprime los dos seguidos). Una división y una fusión que se compensan y
vuelven a sincronizar en 175. Por eso esto es un **detector**: anota la discrepancia y dice cuántas
unidades bailan; no impone emparejamientos. Imponerlos empeoraba el alineamiento (de 3 fallos a 10
en el piloto de A ii).

Salida: una fila por vagga con `uddāna / PTS / CST` y la marca de qué hay que mirar.

Uso: python3 detector_uddana.py [--vol i,ii,iii,iv,v] [-v]
"""
import sqlite3
import sys
from collections import Counter, defaultdict

import an_peyyala as ap
import uddana as U
from an1_markers import collect_an1

DB = 'src/data/tipitaka.sqlite'

# (volumen PTS, libro en la BD, nipāta como lo etiqueta `an1_markers`, fichero VRI)
NIPATAS = [
    ('i',   17, 'EKA',       's0401m'),
    ('i',   17, 'DUKA',      's0402m1'),
    ('i',   17, 'TIKA',      's0402m2'),
    ('ii',  18, 'CATUKKA',   's0402m3'),
    ('iii', 19, 'PAÑCAKA',   's0403m1'),
    ('iii', 19, 'CHAKKA',    's0403m2'),
    ('iv',  20, 'SATTAKA',   's0403m3'),
    ('iv',  20, 'AṬṬHAKA',   's0404m1'),
    ('iv',  20, 'NAVAKA',    's0404m2'),
    ('v',   21, 'DASAKA',    's0404m3'),
    ('v',   21, 'EKĀDASAKA', 's0404m4'),
]


def lado_pts(conn, book, nipata):
    """`(suttas_por_vagga, uddāna_por_vagga)` del nipāta, delimitando por COLOFÓN.

    El colofón es mejor señal que el numeral (lo dice `an1_markers`): nombra el vagga y da su
    ordinal, y existe en todos los regímenes. El uddāna es lo que va entre el colofón y el primer
    marcador del vagga siguiente.
    """
    pgs = {r['page_no']: (r['unitext'] or '').split('\n')
           for r in conn.execute('SELECT page_no,unitext FROM pages WHERE edition="mula" '
                                 'AND book_no=?', (book,))}
    marcas = [m for m in collect_an1(pgs)
              if m['nipata'] == nipata and (m['num'] is not None or m.get('colofon') is not None)]
    marcas.sort(key=lambda m: (m['page'], m['line']))
    plano = [(pg, ln, t) for pg in sorted(pgs) for ln, t in enumerate(pgs[pg], 1)]
    idx = {(pg, ln): i for i, (pg, ln, _t) in enumerate(plano)}
    suttas, udd, vagga = defaultdict(list), {}, 1
    for k, m in enumerate(marcas):
        i0 = idx[(m['page'], m['line'])]
        i1 = (idx[(marcas[k + 1]['page'], marcas[k + 1]['line'])]
              if k + 1 < len(marcas) else len(plano))
        if m.get('colofon') is not None:
            udd[vagga] = ' '.join(t for _p, _l, t in plano[i0:i1])
            vagga += 1
        else:
            suttas[vagga].append(m['num'])
    return suttas, udd


def lado_cst(stem):
    """`{vagga: [paranums]}` del fichero VRI. En AN el `<div rend=chapter>` ES el vagga."""
    out, divs = defaultdict(list), []
    for u in ap.cst_unidades(stem):
        if not divs or divs[-1] != u['div']:
            divs.append(u['div'])
        out[len(divs)].append(u['pn'])
    return out


def main():
    vols = (sys.argv[sys.argv.index('--vol') + 1].split(',')
            if '--vol' in sys.argv else ['i', 'ii', 'iii', 'iv', 'v'])
    verbose = '-v' in sys.argv
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    print('=' * 104)
    print('DETECTOR DE UDDĀNA — dónde PTS y el CST no cuentan lo mismo (AN)')
    print('=' * 104)
    print(f"{'nipāta':<11}{'vagga':>6}{'uddāna':>8}{'PTS':>6}{'CST':>6}   señal")
    tot = Counter()
    sospechosos = []
    for vol, book, nipata, stem in NIPATAS:
        if vol not in vols:
            continue
        suttas, udd = lado_pts(conn, book, nipata)
        cst = lado_cst(stem)
        nv = max(list(suttas) + list(udd) + list(cst), default=0)
        for v in range(1, nv + 1):
            nom, checks, coherente = U.analiza(ap.fold(udd.get(v, '')))
            n_u, n_p, n_c = len(nom), len(suttas.get(v, [])), len(cst.get(v, []))
            tot['vaggas'] += 1
            # ⚠️ El orden de las preguntas ES el método. Lo que decide si hay una asimetría entre
            # ediciones es **PTS contra CST**, no el uddāna: cuando los dos cuentan lo mismo y la
            # estrofa dice otra cosa, el sospechoso es la lectura de la estrofa, no el texto. El
            # uddāna entra después, como testigo de qué lado tiene razón.
            if n_p != n_c:
                tot['ediciones discrepan'] += 1
                d = n_p - n_c
                testigo = ('' if not nom else
                           f' · el uddāna ({n_u}) da la razón a ' +
                           ('PTS' if n_u == n_p else 'CST' if n_u == n_c else 'ninguno'))
                señal = f'PTS {"parte" if d > 0 else "funde"} {abs(d)}{testigo}'
                sospechosos.append((vol, nipata, v, n_u, n_p, n_c, señal))
            elif not nom:
                tot['sin uddāna'] += 1
                señal = 'sin estrofa (el vagga cierra sólo con colofón)'
            elif not coherente:
                tot['ordinal descolocado'] += 1
                señal = f'estrofa mal leída: ordinal fuera de sitio {checks}'
            elif n_u == n_p:
                tot['cuadra todo'] += 1
                señal = ''
            else:
                tot['estrofa sin cuadrar'] += 1
                señal = f'ediciones de acuerdo ({n_p}); la estrofa da {n_u} → lectura incompleta'
            if señal or verbose:
                print(f'A {vol:<3}{nipata:<8}{v:>5}{n_u:>8}{n_p:>6}{n_c:>6}   {señal}')
    print('\n' + ' · '.join(f'{k}: {v}' for k, v in tot.items()))
    # Los tramos peyyāla se apartan: ahí el CST agrupa cientos de suttas en un `<div>` y PTS
    # imprime cuatro párrafos, así que la diferencia de recuento es esperada y ya la trata
    # `an_peyyala`. Lo que interesa aquí son los vaggas ordinarios, de ~diez suttas, donde una
    # unidad de diferencia ES una división o una fusión concreta que hay que ir a mirar.
    normales = [x for x in sospechosos if x[5] <= 30 and x[4] > 0]
    peyyala = [x for x in sospechosos if x not in normales]
    print(f'\n★ {len(normales)} vaggas ORDINARIOS donde PTS y el CST no cuentan lo mismo')
    print('  (cada uno es una división o una fusión que el cotejo de contenido no puede ver)')
    for vol, nip, v, nu, np_, nc, sen in normales:
        print(f'    A {vol:<4}{nip:<10} vagga {v:>2}   PTS {np_:>3} · CST {nc:>3} · uddāna {nu:>3}   {sen}')
    print(f'\n  (+ {len(peyyala)} tramos peyyāla, donde la diferencia es esperada y la trata '
          f'`an_peyyala.py`)')


if __name__ == '__main__':
    main()
