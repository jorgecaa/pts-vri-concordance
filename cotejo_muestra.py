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
# ⚠️ En `Bv` (Buddhavaṃsa + Cariyāpiṭaka) la página del Excel es de **otra composición PTS** y
# apunta a un capítulo distinto en la BD: pedirle a la p68 el `Dhātubhājanīya` devuelve el
# `Siddhatthabuddhavaṃsa`. Para esas filas la ventana no sale de la página sino de **la posición del
# capítulo en la BD**, que el `Detail` ya trae escrita («En la BD el texto está en el libro 41,
# pp. 102-102»). La tabla no debe obligar a echar cuentas.
POR_CAPITULO = {'Bv'}
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


def ventana_del_detail(f):
    """`(libro, primera, última)` leídos del propio `Detail`, o `None`.

    Es el caso de `Bv`/`Cp`: la fila ya sabe dónde está su texto en la BD porque el alineador lo
    dejó escrito. Se lee de ahí en vez de recalcularlo — y si algún día el `Detail` y la BD dejaran
    de concordar, se vería aquí.
    """
    m = re.search(r'En la BD el texto está en el libro (\d+), pp\. (\d+)-(\d+)', str(f['Detail'] or ''))
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def recorta(tp, propio, siguiente):
    """Recorta el texto PTS al tramo de la fila usando **el nombre impreso** como frontera.

    La página es una resolución demasiado gruesa: en el Apadāna, el Vimānavatthu o el Cariyāpiṭaka
    dos unidades cortas comparten página, y entonces el control marca al vecino como ganador aunque
    el par sea bueno. El impreso, en cambio, escribe el nombre al abrir cada unidad —`[329.
    Pupphacchattiya]`, `15 Mahālomahaṃsacariyaṃ`— así que **se corta por el nombre**: desde el
    propio hasta el del siguiente. Cuando alguno no se encuentra, se deja como estaba y se dice.
    """
    def raiz(x):
        # ⚠️ el nombre del Excel viene con prefijo de catálogo —`(KN 15.35) Cp 35 Mahālomahaṃsa…`—
        # y sin quitarlo la raíz empieza por «kn» y no casa con nada del impreso
        x = re.sub(r'^\s*\(KN[^)]*\)\s*', '', str(x or '').replace('\u00ad', ''))
        x = re.sub(r'^\s*(Th[īi]? Ap|Tha Ap|Thi Ap|Cp|Bv|Vv|Pv|Nd ?\d*|Iti|Ud|Snp|Thag|Thig)\s+[\d.]+\s*',
                   '', x)
        x = ap.fold(re.sub(r'^[\d.\s\[]+', '', x))
        x = re.sub(r'(vimanavathu|petavathu|cariyam|cariya|budhavamso|apadanam|nideso)\b.*$', '', x)
        # ⚠️ **sin truncar**. Con la raíz recortada a doce letras, el `Pupphacchattiya-` del Excel
        # casaba con trozos que no eran su encabezado y el recorte empeoraba el cotejo (0,94 → 0,59).
        # Con la raíz entera, si el impreso escribe el nombre de otra forma —lo normal en el
        # Apadāna, donde PTS abrevia— sencillamente **no se recorta**, y eso es lo correcto: más
        # vale la ventana entera que un corte inventado.
        return re.sub(r'[^a-z]', '', x)

    plano = ap.fold(tp)
    r = raiz(propio)
    if len(r) < 5:
        return tp, False
    # ⚠️ El nombre aparece DOS veces: al abrir (`[329. Pupphacchattiya.]`) y al cerrar
    # (`Pupphacchattiyattherassa apadānaṃ samattaṃ`). Quedarse con la primera aparición a secas
    # corta por el colofón del anterior y **empeora** el cotejo: `Tha Ap 331` bajaba de 0,94 a 0,59.
    # Se saltan las apariciones de cierre.
    a = -1
    for m in re.finditer(re.escape(r), plano):
        cola = plano[m.start():m.start() + len(r) + 46]
        if re.search(r'apadanam samatam|nithitam|samatam', cola):
            continue
        a = m.start()
        break
    if a < 0:
        return tp, False
    b = plano.find(raiz(siguiente), a + 1) if siguiente and len(raiz(siguiente)) >= 5 else -1
    return tp[a:b if b > a else None], True


def coteja(conn, f, fs, ancho=92, lineas=8):
    vri = f['VRI Ref']
    tc, origen = texto_cst(vri)
    vol = str(f['PTS Vol'])
    libro = LIBRO.get(vol)
    pg = f['PTS Page']
    hermanas = [g for g in fs if str(g['PTS Vol']) == vol and isinstance(g['PTS Page'], int)]
    k = hermanas.index(f) if f in hermanas else -1
    sig = hermanas[k + 1]['PTS Page'] if 0 <= k < len(hermanas) - 1 else pg + 3
    cap = ventana_del_detail(f) if vol in POR_CAPITULO else None
    if cap:
        libro, a, b = cap
        nota = f'por CAPÍTULO (la p{pg} del Excel es de otra composición y no sirve)'
    else:
        a, b = max(1, pg - 1), max(pg, sig)
        nota = 'por página'
    tp = texto_pts(conn, libro, a, b) if libro and pg else ''
    sig_nom = hermanas[k + 1]['Sutta Name'] if 0 <= k < len(hermanas) - 1 else None
    tp, cortado = recorta(tp, f['Sutta Name'], sig_nom)
    print('═' * ancho)
    print(f"  {f['Sutta Name']}")
    print(f"  PTS Ref «{f['PTS Ref']}»   ·   VRI Ref «{vri}» → {origen}")
    print(f"  {vol} p{pg} · BD libro {libro}, pp. {a}-{b} — resuelto {nota}"
          f"   ·   {f['Validation']} / {f['Estado']}")
    print(f"  recorte por nombre impreso: {'sí' if cortado else 'NO — el nombre no se lee en la '
                                                      'página; la ventana va entera'}")
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
        if 0 <= k + d < len(hermanas) and hermanas[k + d]['VRI Ref']:
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
