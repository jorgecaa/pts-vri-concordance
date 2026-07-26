#!/usr/bin/env python3
"""
cotejo_muestra — saca a la vista, **lado a lado**, el texto PTS y el texto CST de una fila concreta
del Excel, para que un humano arbitre.

No decide nada: no escribe en el Excel, no puntúa, no aprueba. Resuelve la `VRI Ref` contra el XML,
resuelve la página contra la BD, y lo pone en dos columnas con la cobertura al pie. Es la
herramienta del paso que el proyecto llama **revisión humana**, y sirve sobre todo para lo que el
validador **no** puede ver: que el par sea el equivocado.

Por eso el control importa tanto como el par: se imprime también la cobertura del texto PTS de la
fila contra el sutta **anterior y siguiente** del CST. Si el propio no gana con holgura, la fila es
sospechosa aunque su cobertura sea alta — es exactamente el caso que destapó el desplazamiento +1
del Petavatthu.

Uso:
    python3 cotejo_muestra.py --fila «<Sutta Name o Sutta #>» [--ancho 92]
"""
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET

import an_peyyala as ap
import an1_eka_duka as R
from openpyxl import load_workbook

XLSX = 'PTS_Reference_Complete_Canon.xlsx'
XMLDIR = '/tmp/tipitaka-xml/romn'
# etiqueta `PTS Vol` del Excel → libro de la BD
LIBRO = {'Kh': 22, 'Dh': 23, 'Ud': 24, 'It': 25, 'Sn': 26, 'Vv': 27, 'Pv': 28, 'Th': 29,
         'Th & Th': 29, 'Nidd': 36, 'Nidd II': 37, 'Paṭis I': 38, 'Paṭis II': 39, 'Ap': 40,
         'Bv': 41}


def filas():
    wb = load_workbook(XLSX, read_only=True)
    ws = wb['Complete Canon']
    hdr = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    ci = {n: i for i, n in enumerate(hdr)}
    return [{k: r[ci[k]] for k in hdr} for r in ws.iter_rows(min_row=2, values_only=True)]


def texto_cst(vri):
    """Texto del CST al que apunta una `VRI Ref`, en cualquiera de sus tres formas."""
    m = re.match(r'^([a-z0-9]+):c(\d+)(?:\.(\d+))?$', str(vri))
    if m:                                   # KN: `<fichero>:c<capítulo>[.<item>]`
        stem, cap, item = m.group(1), int(m.group(2)), m.group(3)
        raiz = ET.parse(f'{XMLDIR}/{stem}.mul.xml').getroot()
        divs = [d for d in raiz.iter('div') if '_' in (d.get('n') or '')]
        if cap > len(divs):
            return None, f'el capítulo {cap} no existe en {stem}'
        d = divs[cap - 1]
        if item is None:
            return ' '.join(''.join(p.itertext()) for p in d.iter('p')), f'{stem} div {cap}'
        act, k, out = None, 0, []
        for p in d.iter('p'):
            if p.get('rend') in ('subhead', 'title'):
                k += 1
                act = (k == int(item))
                if act:
                    out.append(''.join(p.itertext()).strip())
                continue
            if act:
                out.append(''.join(p.itertext()))
        return ' '.join(out), f'{stem} div {cap}, unidad {item}'
    m = re.match(r'^([a-z0-9]+):(\d+)(?:-(\d+))?$', str(vri))
    if m:                                   # SN/AN/KN corrido: `<fichero>:<a>[-<b>]`
        stem, a = m.group(1), int(m.group(2))
        b = int(m.group(3) or a)
        u = [x for x in ap.cst_unidades(stem) if a <= x['pn'] <= b]
        return ' '.join(x['texto'] for x in u), f'{stem} paranums {a}-{b}'
    return None, f'VRI Ref no reconocida: {vri!r}'


def texto_pts(conn, libro, a, b):
    return ' '.join((x['unitext'] or '') for x in conn.execute(
        'SELECT unitext FROM pages WHERE edition="mula" AND book_no=? AND page_no BETWEEN ? AND ?',
        (libro, a, b)))


def columnas(izq, der, ancho):
    """Dos textos en dos columnas, envueltos, con separador."""
    import textwrap
    w = (ancho - 3) // 2
    a = textwrap.wrap(re.sub(r'\s+', ' ', izq).strip(), w) or ['—']
    b = textwrap.wrap(re.sub(r'\s+', ' ', der).strip(), w) or ['—']
    n = max(len(a), len(b))
    a += [''] * (n - len(a))
    b += [''] * (n - len(b))
    return '\n'.join(f'{x:<{w}} │ {y}' for x, y in zip(a, b))


def coteja(conn, f, fs, ancho=92, lineas=8):
    vri = f['VRI Ref']
    tc, origen = texto_cst(vri)
    vol = str(f['PTS Vol'])
    libro = LIBRO.get(vol)
    pg = f['PTS Page']
    hermanas = [g for g in fs if str(g['PTS Vol']) == vol and isinstance(g['PTS Page'], int)]
    k = hermanas.index(f) if f in hermanas else -1
    sig = hermanas[k + 1]['PTS Page'] if 0 <= k < len(hermanas) - 1 else pg + 3
    tp = texto_pts(conn, libro, max(1, pg - 1), max(pg, sig)) if libro and pg else ''
    print('═' * ancho)
    print(f"  {f['Sutta Name']}")
    print(f"  PTS Ref «{f['PTS Ref']}»   ·   VRI Ref «{vri}» → {origen}")
    print(f"  {vol} p{pg} (libro {libro} de la BD, ventana {max(1, pg - 1)}-{max(pg, sig)})"
          f"   ·   {f['Validation']} / {f['Estado']}")
    print('─' * ancho)
    print(f"{'PTS (impreso, BD)':<{(ancho - 3) // 2}} │ CST (VRI)")
    print('─' * ancho)
    if tc is None:
        print(f'  ⚠ {origen}')
        return
    print('\n'.join(columnas(tp, tc, ancho).split('\n')[:lineas]))
    print('─' * ancho)
    cov = R.cobertura(ap.fold(tp), ap.fold(tc))
    ctl = []
    for d in (-1, 1):
        if 0 <= k + d < len(hermanas):
            t2, _ = texto_cst(hermanas[k + d]['VRI Ref'])
            if t2:
                ctl.append(f'{"anterior" if d < 0 else "siguiente"} {R.cobertura(ap.fold(tp), ap.fold(t2)):.2f}')
    marca = '✓' if not ctl or cov >= max(float(x.split()[-1]) for x in ctl) else '⚠ EL VECINO GANA'
    print(f'  cobertura propia {cov:.2f}   ·   control: {" · ".join(ctl) or "—"}   {marca}')


def main():
    ancho = int(sys.argv[sys.argv.index('--ancho') + 1]) if '--ancho' in sys.argv else 92
    claves = sys.argv[sys.argv.index('--fila') + 1:] if '--fila' in sys.argv else []
    fs = filas()
    conn = sqlite3.connect(R.DB)
    conn.row_factory = sqlite3.Row
    for clave in claves:
        hit = [f for f in fs if clave in str(f['Sutta Name']) or clave == str(f['Sutta #'])]
        if not hit:
            print(f'⚠ sin fila para {clave!r}')
            continue
        coteja(conn, hit[0], fs, ancho)


if __name__ == '__main__':
    main()
