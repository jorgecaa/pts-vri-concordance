#!/usr/bin/env python3
"""Aligner DEFINITIVO SN V: Excel(DPR) → massive.tsv → cst_paranum → XML VRI → CST.

El Excel usa notación DPR. massive.tsv da, por código DPR, el `cst_paranum`. El XML
VRI (`romn/s0305m.mul.xml`, la fuente que massive referencia) da el texto CST exacto
por paranum (100% verificado). Así la alineación PTS↔CST es EXACTA, sin adivinar por
contenido ni reconciliar agrupaciones. Luego se valida con el validador (Modelo B).

Uso: python3 validador_sn5_vri.py [--dry] [--all] [--n N]
"""
import csv, re, sqlite3, sys, json
import xml.etree.ElementTree as ET
from collections import Counter
import sutta_hash as sh
from openpyxl import load_workbook
from validador import validate_pair
from validador_sn5 import build_markers, pts_for

VRI = '/tmp/tipitaka-xml/romn/s0305m.mul.xml'
DB = 'src/data/tipitaka.sqlite'
SN5_BOOK = 16


# ── XML VRI → paranum → texto CST del sutta ─────────────────────────────────
def build_vri_index():
    root = ET.parse(VRI).getroot()
    body = root.find('.//body')
    suttas, cur = [], None
    for el in body.iter():
        rend = el.get('rend')
        if el.tag == 'p' and rend == 'subhead':
            cur = {'title': ''.join(el.itertext()).strip(), 'pn': [], 'text': ''}
            suttas.append(cur)
        elif el.tag == 'p' and rend == 'bodytext' and cur is not None:
            n = el.get('n')
            if n:
                cur['pn'].append(n)
            cur['text'] += ' ' + ''.join(el.itertext())
    idx = {}
    for s in suttas:
        for n in s['pn']:
            m = re.match(r'(\d+)(?:-(\d+))?$', n)
            if m:
                a, b = int(m.group(1)), int(m.group(2) or m.group(1))
                for p in range(a, b + 1):
                    idx.setdefault(p, s)
    return idx


# ── massive.tsv → cada nº canónico DPR → cst_paranum ────────────────────────
def build_massive():
    canon2para = {}
    for r in csv.DictReader(open('massive.tsv'), delimiter='\t'):
        if not (r['cst_code'] or '').startswith('sn5.'):
            continue
        pm = re.match(r'(\d+)', r['cst_paranum'] or '')     # paranum puede ser rango "42-47"
        if not pm:
            continue
        para = int(pm.group(1))                             # nº de párrafo de inicio
        m = re.match(r'SN(\d+)\.(\d+)(?:-(\d+))?', r['dpr_code'] or '')
        if not m:
            continue
        sam, a = m.group(1), int(m.group(2))
        b = int(m.group(3)) if m.group(3) else a
        for k in range(a, b + 1):                            # expande rangos DPR
            canon2para.setdefault(f'{sam}.{k}', (para, r['cst_sutta']))
    return canon2para


def excel_entries():
    wb = load_workbook('PTS_Reference_Complete_Canon.xlsx', read_only=True)
    ws = wb['Complete Canon']
    hdr = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    ci = {n: i for i, n in enumerate(hdr)}
    out = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if str(row[ci['Nikaya']] or '') != 'SN' or str(row[ci['PTS Roman']] or '').strip().lower() != 'v':
            continue
        num = str(row[ci['Sutta #']]); name = str(row[ci['Sutta Name']] or '')
        m = re.search(r'\(SN\s+(\d+)\.(\d+)', name)
        canon = f'{m.group(1)}.{m.group(2)}' if m else num
        # el nº corrido del marcador PTS = el canónico (no el Sutta# comprimido)
        inner = int(canon.split('.')[1]) if '.' in canon and canon.split('.')[1].isdigit() else None
        out.append({'num': num, 'canon': canon, 'inner': inner,
                    'name': re.sub(r'\(SN[^)]*\)', '', name).strip(),
                    'page': row[ci['PTS Page']], 'legacy': str(row[ci['Validation']] or '')})
    return out


def main():
    dry = '--dry' in sys.argv
    do_all = '--all' in sys.argv
    n = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 30
    vri = build_vri_index()
    canon2para = build_massive()
    entries = excel_entries()
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row; cur = conn.cursor()
    mm = build_markers(cur)

    tasks, no_dpr, no_para, no_pts = [], [], [], []
    for e in entries:
        hit = canon2para.get(e['canon'])
        if not hit:
            no_dpr.append(e); continue
        para, ctitle = hit
        s = vri.get(para)
        if not s:
            no_para.append(e); continue
        cst = ' '.join(sh.tokens(s['text'])[:350])
        pts = None
        if isinstance(e['page'], int) and e['inner']:
            # exacto, luego difuso (irregularidades PTS: nº corrido ≠ canónico ±1, página ±1)
            for pg, inr in [(e['page'], e['inner']), (e['page'], e['inner'] - 1),
                            (e['page'] + 1, e['inner']), (e['page'], e['inner'] + 1),
                            (e['page'] - 1, e['inner'])]:
                pts = pts_for(cur, pg, inr, mm)
                if pts:
                    break
        if not pts:
            no_pts.append(e); continue
        tasks.append((e, pts, cst, s['title']))

    print('=' * 92)
    print('ALINEADOR VRI (Excel→DPR→massive→cst_paranum→XML VRI) — SN V')
    print('=' * 92)
    print(f'Excel SN V: {len(entries)}')
    print(f'  alineadas con texto CST+PTS: {len(tasks)} ({100*len(tasks)/len(entries):.0f}%)')
    print(f'  sin DPR en massive: {len(no_dpr)} | sin paranum en VRI: {len(no_para)} | sin texto PTS: {len(no_pts)}')
    if no_dpr:
        print('  muestra sin DPR:', [e['canon'] for e in no_dpr[:12]])
    if dry:
        return

    run = tasks if do_all else tasks[:n]
    print(f'\nValidando {len(run)} (Gemini en vivo)...', flush=True)
    rows = []
    for k, (e, pts, cst, ctitle) in enumerate(run, 1):
        res = validate_pair(pts, cst, e['name'], ctitle, 'SN')
        rows.append({'num': e['num'], 'canon': e['canon'], 'name': e['name'],
                     'cst_title': ctitle, 'legacy': e['legacy'], **res})
        if k % 25 == 0:
            print(f'  ...{k}/{len(run)}', flush=True)
    json.dump(rows, open('validador_sn5_vri.json', 'w'), ensure_ascii=False, indent=1)
    est = Counter(r['estado'] for r in rows); val = Counter(r['validation'] for r in rows)
    print(f'\nEstado: {dict(est)} | Validation: {dict(val)}')
    print('Resultados → validador_sn5_vri.json (nada escrito al Excel).')


if __name__ == '__main__':
    main()
