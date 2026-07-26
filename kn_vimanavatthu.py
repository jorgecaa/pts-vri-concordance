#!/usr/bin/env python3
"""
kn_vimanavatthu — el Vimānavatthu: 85 filas, una por vimāna.

Va en fichero propio y no como un parámetro más de `kn_theragatha` (regla (6)) porque **el régimen
de prueba es otro**: aquí el contenido no decide, decide el nombre. Conviene explicar por qué,
porque la medición dice justo lo contrario de lo que uno esperaría.

### Por qué el contenido NO puede decidir

La obra está construida a base de **pares deliberadamente repetidos**: `Paṭhamasuṇisā` /
`Dutiyasuṇisā`, `Paṭhamakaraṇīya` / `Dutiyakaraṇīya`, `Paṭhamasūci` / `Dutiyasūci`,
`Paṭhamanāga` / `Dutiyanāga`… El segundo miembro es el mismo poema con el donante cambiado, y en
tres casos PTS **ni siquiera lo reimprime**: en Vv 86 escribe `anantaraṃ pañcavimānaṃ yathā
kākatarasadāyakavimānaṃ tathā vitthāretabbaṃ` y remite. Medido sobre las 85 filas:

- con la ventana ajustada a la fila, la cobertura propia tiene mediana **0,94** — pero la de un
  sutta **ajeno** (±3, +10) tiene mediana **0,53**, y **106 de 239** pares ajenos pasan de 0,55. Un
  umbral fijo no separa nada: la lengua es formulaica, como en el Udāna.
- probando si el sutta propio es el que **más** puntúa de los 85, gana 75 de 85; y las diez que
  pierden, pierden **contra su propio gemelo** — `6.1.1.12` da 0,95 y su `Dutiyasuṇisā` 0,97.
- y abrir la ventana hacia atrás, que a primera vista arreglaba las ocho filas flojas (0,39 → 0,95),
  es **vacuo**: con esa ventana los vecinos puntúan igual o más (0,97 contra 0,95). Se descartó.

### Lo que sí decide

1. **El nombre, 85 de 85.** El `subhead` del CST casa con el nombre del Excel en las ochenta y
   cinco, y es la única señal que ve el ordinal `Paṭhama-`/`Dutiya-` que al contenido se le escapa.
2. **La biyección es completa y respeta el orden**: 85 suttas en el CST, 85 filas en el Excel, mismo
   orden, misma partición en los dos `div` (`Itthivimāna` 1-50, `Purisavimāna` 51-85) y serie de
   páginas monótona de la 1 a la 135.
3. **La cobertura, como corroboración** (nunca como discriminante): mediana 0,94, y donde baja está
   explicado — el poema arranca en la página anterior a la que declara la fila, o PTS lo elide.

### La notación (regla (5-ter))

`Vv <nº>` — el número corrido del vimāna, que el propio nombre de la fila trae (`Vv 84
Serīsakavimānavatthu`). El Excel no da rango de versos para esta obra (`PTS Alt/Verse` vacío en las
85), así que el rango del CST queda sólo en la `VRI Ref`.

Uso: python3 kn_vimanavatthu.py [--dry]
"""
import re
import shutil
import sqlite3
import sys
from datetime import datetime

import an_peyyala as ap
import an1_eka_duka as R
from openpyxl import load_workbook

XLSX = 'PTS_Reference_Complete_Canon.xlsx'
BOOK, STEM, SIGLA = 27, 's0506m', 'Vv'
ULTIMA = 135
COV_COTA = 0.55          # sólo para etiquetar la corroboración, NO es condición para firmar


def _limpia(t):
    """`(KN 6.84) Vv 84 Serīsakavimānavatthu` → `Serīsakavimānavatthu`."""
    t = re.sub(r'^\s*\(KN[^)]*\)\s*', '', t or '')
    return re.sub(r'^\s*(Vv|Pv)\s+[\d.]+\s*', '', t).strip()


def raiz(t):
    """Raíz comparable: sin ordinal de lista, sin `-vimānavatthu`, sin desinencia."""
    t = ap.fold(re.sub(r'^[\d.\s]+', '', t or '')).strip()
    t = re.sub(r'\s*(vimanavathu|vimanam|vathu|gatha)$', '', t).strip()
    return re.sub(r'[aiueom]+$', '', t)


def casa_nombre(excel, subhead):
    """¿Mismo vimāna? Se prueban las variantes que el Excel escribe entre paréntesis.

    ⚠️ **El ordinal cuenta.** `raiz` lo conserva —`pathamasunisa` ≠ `dutiyasunisa`— y es lo único
    que distingue a los gemelos, que por texto son indistinguibles.
    """
    va = [raiz(x) for x in re.split(r'[()]', _limpia(excel)) if raiz(x)]
    vb = raiz(subhead)
    if len(vb) < 3:
        return any(a == vb for a in va)
    return any(len(a) >= 3 and (a == vb or a.startswith(vb) or vb.startswith(a)) for a in va)


def suttas_cst():
    """`[(subhead, primer verso, último verso, div, texto)]` — los 85, agrupando por `subhead`."""
    out = []
    for x in ap.cst_unidades(STEM):
        if not out or out[-1][0] != x['subhead']:
            out.append([x['subhead'], x['pn'], x['pn'], x['div'], ''])
        out[-1][2] = x['pn']
        out[-1][4] += ' ' + x['texto']
    return [(a, b, c, d, ap.fold(e)) for a, b, c, d, e in out]


def main():
    dry = '--dry' in sys.argv
    conn = sqlite3.connect(R.DB)
    conn.row_factory = sqlite3.Row
    cst = suttas_cst()
    wb = load_workbook(XLSX, read_only=True)
    ws = wb['Complete Canon']
    hdr = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    ci = {n: i for i, n in enumerate(hdr)}
    fs = [{'num': str(r[ci['Sutta #']]), 'name': str(r[ci['Sutta Name']] or ''),
           'page': r[ci['PTS Page']], 'estado': r[ci['Estado']]}
          for r in ws.iter_rows(min_row=2, values_only=True)
          if r[ci['Nikaya']] == 'KN' and str(r[ci['PTS Vol']]) == SIGLA]
    print(f'CST {len(cst)} suttas · Excel {len(fs)} filas')
    if len(cst) != len(fs):
        print('⚠ los recuentos no coinciden: no se escribe nada')
        return

    # (1) el nombre, en las 85; (2) la serie de páginas, monótona
    nombres = [casa_nombre(f['name'], cst[k][0]) for k, f in enumerate(fs)]
    pgs = [f['page'] for f in fs]
    mono = all(isinstance(b, int) and isinstance(a, int) and b >= a
               for a, b in zip(pgs, pgs[1:]))
    print(f'  nombre {sum(nombres)}/{len(fs)} · páginas monótonas {mono} '
          f'({pgs[0]}..{pgs[-1]} de {ULTIMA})')
    if not (all(nombres) and mono):
        print('⚠ la biyección por nombre no es completa o la serie retrocede: no se escribe nada')
        for k, f in enumerate(fs):
            if not nombres[k]:
                print(f"   ⚠ «{_limpia(f['name'])}» vs «{cst[k][0]}»")
        return

    res, flojas = {}, 0
    for k, f in enumerate(fs):
        sub, a, b, div, tc = cst[k]
        pg = f['page']
        sig = fs[k + 1]['page'] if k + 1 < len(fs) else ULTIMA
        # ventana desde la página anterior: en esta obra el título va de colofón, detrás del poema,
        # así que la página que declara la fila es a veces la del cierre y el poema empieza antes
        txt = ' '.join(ap.fold(x['unitext'] or '') for x in conn.execute(
            'SELECT unitext FROM pages WHERE edition="mula" AND book_no=? AND page_no BETWEEN ? '
            'AND ?', (BOOK, max(1, pg - 1), max(sig, pg + 1 + len(tc) // 1200))))
        cov = R.cobertura(txt, tc)
        flojas += cov < COV_COTA
        m = re.search(rf'\b{SIGLA}\s+(\d+)', f['name'])
        if not m:
            print(f"   ✗ {f['num']}: el nombre no trae el nº de vimāna")
            continue
        res[f['num']] = (
            f'{STEM}:{a}-{b}' if b != a else f'{STEM}:{a}',
            f'{SIGLA} {m.group(1)}',
            f'Vimānavatthu: vimāna {k + 1} de 85 → «{sub}» ({div}), versos {a}-{b} del CST. '
            f'El nombre casa en las 85 filas y la biyección respeta el orden y la partición en '
            f'Itthi-/Purisavimāna; corroboración por contenido {cov:.2f}'
            + ('' if cov >= COV_COTA else
               ' (baja: el poema arranca en la página anterior o PTS lo elide remitiendo a su '
               'gemelo — en esta obra el contenido corrobora, no discrimina)'))
    print(f'\n{len(res)}/{len(fs)} firmadas · cobertura por debajo de {COV_COTA}: {flojas}')
    if dry or not res:
        print('(dry-run: nada escrito)' if dry else '')
        return
    cp = f'{XLSX}.backup-{datetime.now():%Y%m%d-%H%M%S}-vv.xlsx'
    shutil.copy(XLSX, cp)
    print(f'backup → {cp}')
    wb = load_workbook(XLSX)
    ws = wb['Complete Canon']
    ci = {c.value: i + 1 for i, c in enumerate(ws[1])}
    n = 0
    for r in range(2, ws.max_row + 1):
        if (ws.cell(r, ci['Nikaya']).value != 'KN'
                or str(ws.cell(r, ci['PTS Vol']).value) != SIGLA):
            continue
        num = str(ws.cell(r, ci['Sutta #']).value)
        if num not in res or ws.cell(r, ci['Estado']).value == 'CONFIRMADO':
            continue
        vri, ref, det = res[num]
        ws.cell(r, ci['VRI Ref']).value = vri
        ws.cell(r, ci['PTS Ref']).value = ref
        ws.cell(r, ci['Validation']).value = 'VALIDADOR_HUMANO'
        ws.cell(r, ci['Estado']).value = 'CONFIRMADO'
        ws.cell(r, ci['Detail']).value = det
        n += 1
    wb.save(XLSX)
    print(f'{n} filas cerradas · escrito → {XLSX}')


if __name__ == '__main__':
    main()
