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

### Dos cosas que hay que preguntarle al dato, no suponerlas

**El régimen de marcador** (regla (6) de `CLAUDE.md`). Del Tika en adelante el marcador lleva el nº
**corrido** del nipāta y el vagga lo delimita el **colofón**; en el Eka y el Duka el numeral romano
centrado **ES el vagga** y el nº reinicia dentro de él. Contar por colofones en Eka/Duka fundía
vaggas —el Eka tiene 21 y sólo 16 colofones— y producía disparates que parecían divergencias entre
ediciones: un «vagga» con 53 suttas frente a 16 del CST.

**El emparejamiento de vaggas va por NOMBRE, no por posición.** El Eka imprime 21 vaggas y el CST
numera 20; el Duka, 17 contra 19. Con el emparejamiento posicional el vagga 16 del Duka salía
«PTS 30 · CST 10», una divergencia inventada por el desfase acumulado. El nombre está en las dos
ediciones —PTS en el colofón (`Rūpādi-vaggo paṭhamo`), el CST en la cabecera del `div`
(`1. Rūpādivaggo`)— y el alineamiento es monótono, porque el orden sí se respeta; lo que no se
respeta es la cuenta.

⚠️ Y en el Eka y el Duka la **estrofa no lleva cabecera**: va pegada al colofón, sin la palabra
`uddānaṃ` (`Kammakaraṇa-vaggo paṭhamo. Vajjappadhānā dve tapanīyā upaññāsena pañcamaṃ…`). Hay que
leerla desde la línea siguiente al colofón —si no, el propio nombre del vagga entra como si fuera
un sutta— y **deshifenada**, que el verso también parte palabras (`vassūpanāyi-|kena` es una).

Salida: una fila por vagga con `uddāna / PTS / CST` y la marca de qué hay que mirar.

Uso: python3 detector_uddana.py [--vol i,ii,iii,iv,v] [-v]
"""
import sqlite3
import sys
from collections import Counter, defaultdict

import an_names as AN
import an_peyyala as ap
import uddana as U
from align_rows import assign as ar_assign
from an1_markers import REGIMEN, collect_an1

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
    """`(suttas_por_vagga, uddāna_por_vagga)` del nipāta. **El agrupamiento depende del RÉGIMEN.**

    Los dos regímenes de `an1_markers` cuentan cosas distintas y hay que preguntarle a él, no
    suponerlo (regla (6) de `CLAUDE.md`):

    - **`corrido` / `sutta_romano`** (del Tika en adelante): el marcador lleva el nº **corrido** del
      nipāta y el vagga no se imprime, así que lo delimita el **colofón**.
    - **`vagga_romano`** (Eka y Duka): el numeral romano centrado **ES el vagga** y el nº del
      marcador es la posición **dentro** de él, reiniciando cada diez. Ahí el vagga ya viene dado
      en `m['vagga']` y contarlo por colofones es sencillamente otra cosa: el Eka tiene 21 vaggas y
      sólo 16 colofones, de modo que el recuento por colofón fundía vaggas y producía disparates
      —un «vagga» con 53 suttas frente a 16 del CST— que parecían divergencias entre ediciones y
      eran un error de lectura.
    """
    pgs = {r['page_no']: (r['unitext'] or '').split('\n')
           for r in conn.execute('SELECT page_no,unitext FROM pages WHERE edition="mula" '
                                 'AND book_no=?', (book,))}
    marcas = [m for m in collect_an1(pgs)
              if m['nipata'] == nipata and (m['num'] is not None or m.get('colofon') is not None)]
    marcas.sort(key=lambda m: (m['page'], m['line']))
    plano = [(pg, ln, t) for pg in sorted(pgs) for ln, t in enumerate(pgs[pg], 1)]
    idx = {(pg, ln): i for i, (pg, ln, _t) in enumerate(plano)}
    por_vagga = REGIMEN.get(nipata) == 'vagga_romano'
    suttas, udd, nombres, vagga = defaultdict(list), {}, {}, 1
    for k, m in enumerate(marcas):
        i0 = idx[(m['page'], m['line'])]
        i1 = (idx[(marcas[k + 1]['page'], marcas[k + 1]['line'])]
              if k + 1 < len(marcas) else len(plano))
        if m.get('colofon') is not None:
            # el uddāna va detrás del colofón; se acota a 40 líneas para que un colofón sin
            # estrofa detrás no se trague páginas enteras (en el Duka daba 3.331 «nombres»)
            v = m['vagga'] if por_vagga and m.get('vagga') else vagga
            # Desde la línea SIGUIENTE al colofón: sin la palabra `uddānaṃ` que corte la cabecera
            # —el Eka y el Duka no la escriben— el propio nombre del vagga se colaba como si fuera
            # un sutta (`Adhikaraṇavaggo dutiyo.` daba un «nombre» donde no hay estrofa ninguna).
            # Y **deshifenado**, que el verso también parte palabras: `vassūpanāyi-|kena` son una.
            udd[v] = ap.deshifena([t for _p, _l, t in plano[i0 + 1:min(i1, i0 + 40)]])[0]
            nombres[v] = m.get('colofon')
            vagga += 1
        elif por_vagga:
            if m.get('vagga'):
                suttas[m['vagga']].append(m['num'])
        else:
            suttas[vagga].append(m['num'])
    return suttas, udd, nombres


def lado_cst(stem):
    """`({vagga: [paranums]}, [nombres de div])` del fichero VRI. En AN el `<div>` ES el vagga."""
    out, divs = defaultdict(list), []
    for u in ap.cst_unidades(stem):
        if not divs or divs[-1] != u['div']:
            divs.append(u['div'])
        out[len(divs)].append(u['pn'])
    return out, divs


def empareja_vaggas(nombres_pts, nombres_cst):
    """Empareja los vaggas de las dos ediciones **por NOMBRE**, no por posición.

    Emparejarlos por su ordinal supone que las dos ediciones tienen los mismos vaggas, y es falso
    justo donde más duele: el Eka imprime **21** y el CST numera **20**; el Duka, **17** contra
    **19**. Con el emparejamiento posicional, el vagga 16 del Duka salía «PTS 30 · CST 10» —una
    divergencia inventada por el desfase acumulado— y el 21 del Eka se comparaba contra nada.

    El nombre está en las dos: PTS lo pone en el **colofón** (`Rūpādi-vaggo paṭhamo`) y el CST en
    la cabecera del `div` (`1. Rūpādivaggo`). El alineamiento es monótono, porque el orden sí se
    respeta; lo que no se respeta es la cuenta.
    """
    def score(i, j):
        a, b = nombres_pts[i], nombres_cst[j]
        if not a or not b:
            return 0.1                      # sin nombre: que decida el orden
        s = AN.score(b, a)
        return max(s, 0.1) if s >= 50 else 0.1
    idx = ar_assign(len(nombres_pts), len(nombres_cst), score, lambda j: 1, skip_penalty=30.0)
    return {i + 1: (j + 1 if j is not None else None) for i, j in enumerate(idx)}


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
        por_vagga = REGIMEN.get(nipata) == 'vagga_romano'
        suttas, udd, nom_pts = lado_pts(conn, book, nipata)
        cst, nom_cst = lado_cst(stem)
        nv = max(list(suttas) + list(udd) + list(cst), default=0)
        # el vagga k de PTS no es forzosamente el k del CST: se emparejan por nombre
        par = empareja_vaggas([nom_pts.get(k) for k in range(1, nv + 1)], nom_cst)
        for v in range(1, nv + 1):
            # en Eka y Duka la estrofa va sin la palabra `uddānaṃ`, pegada al colofón
            nom, checks, coherente = U.analiza(ap.fold(udd.get(v, '')),
                                               exige_marca=not por_vagga)
            n_u, n_p = len(nom), len(suttas.get(v, []))
            n_c = len(cst.get(par.get(v) or -1, []))
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
                sospechosos.append((vol, nipata, v, n_u, n_p, n_c, señal,
                                    'peyyāl' in (nom_cst[par[v] - 1].lower() if par.get(v) else '')))
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
    # «tramo peyyāla» se decide por el NOMBRE del div del CST (`…peyyālaṃ`), no por un umbral de
    # tamaño: el `Kodhapeyyālaṃ` del Duka tiene diez unidades y pasaba por vagga ordinario.
    peyyala = [x for x in sospechosos if x[7] or x[5] > 30 or x[4] == 0]
    normales = [x for x in sospechosos if x not in peyyala]
    print(f'\n★ {len(normales)} vaggas ORDINARIOS donde PTS y el CST no cuentan lo mismo')
    print('  (cada uno es una división o una fusión que el cotejo de contenido no puede ver)')
    for vol, nip, v, nu, np_, nc, sen, _pey in normales:
        print(f'    A {vol:<4}{nip:<10} vagga {v:>2}   PTS {np_:>3} · CST {nc:>3} · uddāna {nu:>3}   {sen}')
    print(f'\n  (+ {len(peyyala)} tramos peyyāla, donde la diferencia es esperada y la trata '
          f'`an_peyyala.py`)')


if __name__ == '__main__':
    main()
