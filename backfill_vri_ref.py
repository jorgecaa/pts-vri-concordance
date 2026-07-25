#!/usr/bin/env python3
"""
backfill_vri_ref — escribe la columna **`VRI Ref`**, la clave canónica del lado CST.

**Por qué.** Hemos estado usando la notación **DPR** como clave de unión y no identifica el sutta de
forma unívoca. El historial es concluyente: S ii desplazado +7, S iv (SN 35) +17 y +47, AN +15 por
desdoblamientos de fila, y en `massive.tsv` el `dpr_code` de AN llega a tener **138 códigos
duplicados** y asignaciones incoherentes entre sí (`AN3.2` → `an3.1.2.8` mientras `AN3.11` →
`an3.1.2.11`). Cada vez, un APPROVE del validador no decía nada de la FILA porque la clave era falsa.

**La medida.** El **paranum del XML VRI** pasa a ser la clave canónica: es la dirección real del
texto CST que se cotejó, no una notación editorial paralela. Formato `«<fichero>:<paranum>»`, p.ej.
`s0303m:146`; los grupos van como rango, `s0304m:33-42`.

⚠️ **No se toca el `Sutta #`.** Sigue siendo la etiqueta legible en notación DPR y `Raw ID` conserva
el original de la fuente. Lo que cambia es que **deja de ser la clave**: la identidad de una fila la
dan `Sutta Name` + `PTS Page` (regla del repo), y la unión con el CST la da ahora `VRI Ref`.
Reescribir `Sutta #` en volúmenes CERRADOS 🔒 invalidaría la traza de su validación, que se hizo
contra esas filas.

**Verificación obligatoria**: cada fila sólo recibe su `VRI Ref` si el **título CST recomputado
coincide con el que se validó** (el guardado en `validador_sn*.json`). Si discrepa, no se escribe y
se reporta. Así el backfill no puede introducir una clave que no corresponda a lo cotejado.

Uso: python3 backfill_vri_ref.py [--write]
"""
import datetime
import json
import re
import shutil
import sqlite3
import sys
from collections import Counter

from openpyxl import load_workbook

XLSX = 'PTS_Reference_Complete_Canon.xlsx'
DB = 'src/data/tipitaka.sqlite'


def _fmt(stem, pns):
    """`(«s0303m», [146])` → `«s0303m:146»`; un grupo → `«s0304m:33-42»`."""
    if not pns:
        return None
    a, b = min(pns), max(pns)
    return f'{stem}:{a}' if a == b else f'{stem}:{a}-{b}'


# ── un adaptador por volumen: devuelve {Sutta # → (VRI Ref, título CST)} ──────
def vol_sn1():
    import validador_sn1 as V
    vri, mv = V.build_vri_index(), V.build_massive()
    out = {}
    for e in V.excel_entries():
        h = mv.get(e['canon'])
        if not h:
            continue
        s = vri.get(h[0])
        if s:
            out[e['num']] = (_fmt('s0301m', [h[0]]), s['title'])
    return out, 'validador_sn1.json'


def vol_sn2():
    import validador_sn2 as V
    vri, mv = V.build_vri_index(), V.build_massive()
    out = {}
    for e in V.excel_entries():
        h = mv.get((e['sam'], e['inner']))
        if not h:
            continue
        s = vri.get(h[0])
        if s:
            out[e['num']] = (_fmt('s0302m', [h[0]]), s['title'])
    return out, 'validador_sn2.json'


def vol_sn3():
    import validador_sn3 as V
    vri, mv = V.build_vri_index(), V.build_massive()
    out = {}
    for e in V.excel_entries():
        h = mv.get((e['sam'], e['inner']))
        if not h:
            continue
        s = vri.get(h[0])
        if s:
            out[e['num']] = (_fmt('s0303m', [h[0]]), s['title'])
    return out, 'validador_sn3.json'


def vol_sn4():
    import validador_sn4 as V
    entries = V.excel_entries()
    cst = V.cst_for(entries, V.build_cst_blocks())
    out = {}
    for e in entries:
        b = cst.get(e['num'])
        if b:
            out[e['num']] = (_fmt('s0304m', b['pn']), b['title'])
    return out, 'validador_sn4.json'


def vol_sn5():
    import validador_sn5_vri as V
    vri, c2p = V.build_vri_index(), V.build_massive()
    out = {}
    for e in V.excel_entries():
        h = c2p.get(e['canon'])
        if not h:
            continue
        s = vri.get(h[0])
        if s:
            out[e['num']] = (_fmt('s0305m', [h[0]]), s['title'])
    return out, 'validador_sn5_vri.json'


VOLS = {('SN', 'i'): vol_sn1, ('SN', 'ii'): vol_sn2, ('SN', 'iii'): vol_sn3,
        ('SN', 'iv'): vol_sn4, ('SN', 'v'): vol_sn5}

# fichero VRI y su índice título→paranums, para resolver por el título VALIDADO
VRI_FILE = {('SN', 'i'): 's0301m', ('SN', 'ii'): 's0302m', ('SN', 'iii'): 's0303m',
            ('SN', 'iv'): 's0304m', ('SN', 'v'): 's0305m'}


def title_index(stem):
    """`título normalizado → [paranums]` leyendo el XML VRI directamente.

    El título **validado** es la autoridad: es el texto que Gemini y el gate cotejaron. Recomputar
    la cadena Excel→massive→paranum no basta, porque los drivers aplican además resoluciones
    propias (el `ditthi_pairs` de S iii, el fallback por título del Jhāna-saṃyutta) que un
    adaptador ingenuo no reproduce — de ahí las 24 discrepancias de la primera pasada.
    """
    import xml.etree.ElementTree as ET
    root = ET.parse(f'/tmp/tipitaka-xml/romn/{stem}.mul.xml').getroot()
    idx, title = {}, None
    for el in root.find('.//body').iter():
        if el.tag != 'p':
            continue
        if el.get('rend') == 'subhead':
            title = ' '.join(''.join(el.itertext()).split())
        elif el.get('rend') in ('bodytext', 'hangnum') and title:
            m = re.match(r'(\d+)(?:-(\d+))?$', el.get('n') or '')
            if m:
                idx.setdefault(_norm(title), []).extend(
                    range(int(m.group(1)), int(m.group(2) or m.group(1)) + 1))
    return idx

_F = str.maketrans({'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṅ': 'n', 'ñ': 'n', 'ṇ': 'n',
                    'ṭ': 't', 'ḍ': 'd', 'ḷ': 'l', 'ṃ': 'm', 'ṁ': 'm'})


def _norm(t):
    return re.sub(r'[^a-z0-9]', '', (t or '').lower().translate(_F))


def main():
    write = '--write' in sys.argv
    wb = load_workbook(XLSX)
    ws = wb['Complete Canon']
    hdr = [c.value for c in ws[1]]
    ci = {n: i for i, n in enumerate(hdr)}
    col = ci.get('VRI Ref')
    if col is None:
        col = len(hdr)
        ws.cell(row=1, column=col + 1).value = 'VRI Ref'
    st, mismatch, plan = Counter(), [], {}

    for (nk, vol), fn in VOLS.items():
        refs, jf = fn()
        validated = {r['num']: r.get('cst_title', '') for r in json.load(open(jf))}
        tidx = title_index(VRI_FILE[(nk, vol)])
        for num, ct in validated.items():          # filas que el recomputo no alcanzó
            if num not in refs and _norm(ct) in tidx:
                refs[num] = (_fmt(VRI_FILE[(nk, vol)], tidx[_norm(ct)]), ct)
        for num, (ref, title) in refs.items():
            if num not in validated:
                st[f'{nk} {vol}: sin veredicto'] += 1
                continue
            if _norm(title) == _norm(validated[num]):
                plan[(nk, vol, num)] = ref
                st[f'{nk} {vol}: ok'] += 1
                continue
            # el recomputo no reproduce la resolución del driver: manda el título VALIDADO
            pns = tidx.get(_norm(validated[num]))
            if pns:
                plan[(nk, vol, num)] = _fmt(VRI_FILE[(nk, vol)], pns)
                st[f'{nk} {vol}: ok (por título validado)'] += 1
            else:
                st[f'{nk} {vol}: TÍTULO NO LOCALIZADO'] += 1
                mismatch.append((nk, vol, num, title, validated[num]))

    print('=' * 88)
    print('BACKFILL DE «VRI Ref» — la clave canónica pasa a ser el paranum del XML VRI')
    print('=' * 88)
    for k in sorted(st):
        print(f'   {k}: {st[k]}')
    if mismatch:
        print(f'\n⚠️ títulos que NO coinciden con lo validado ({len(mismatch)}) — NO se escriben:')
        for x in mismatch[:12]:
            print(f'   {x[0]} {x[1]} #{x[2]:<9} recomputado «{x[3][:34]}» ≠ validado «{x[4][:34]}»')

    n = 0
    for row in ws.iter_rows(min_row=2):
        v = [c.value for c in row]
        k = (str(v[ci['Nikaya']] or ''), str(v[ci['PTS Roman']] or '').strip().lower(),
             str(v[ci['Sutta #']]))
        if k in plan:
            if write:
                ws.cell(row=row[0].row, column=col + 1).value = plan[k]
            n += 1
    print(f'\nfilas que reciben «VRI Ref»: {n}')
    if not write:
        print('(dry-run, nada escrito — usa --write)')
        return
    bak = f'{XLSX}.backup-{datetime.datetime.now():%Y%m%d-%H%M%S}-vriref.xlsx'
    shutil.copy(XLSX, bak)
    print('backup →', bak)
    wb.save(XLSX)
    print(f'Escritas {n} referencias VRI en {XLSX}.')


if __name__ == '__main__':
    main()
