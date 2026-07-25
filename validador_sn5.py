#!/usr/bin/env python3
"""Driver SN V para el validador (Modelo B).

Resolvedor CST específico de SN V (book 16, saṃyuttas 45–56, s5m.xml), portado de
helmer_sn5_all.py: parsea los marcadores PTS `N. (gid) nombre`, extrae el texto del
sutta hasta el siguiente marcador, y mapea al CST por fronteras de saṃyutta
(cst_idx = frontera[saṃyutta] + (inner-1)).  OJO: CST≠PTS numbering en SN — si el
mapeo desalinea, el Modelo B lo marca como desacuerdo/REVISAR, no lo auto-confirma.

Uso: python3 validador_sn5.py [--n 30] [--all]
No escribe el Excel; vuelca a validador_sn5_batch.json.
"""
import re, sqlite3, sys, json
from collections import defaultdict, Counter
import sutta_hash as sh
from openpyxl import load_workbook
from validador import validate_pair, _nfold

SN5_BOOK = 16
DB = 'src/data/tipitaka.sqlite'
ALIGN_WINDOW = 30     # segmentos CST hacia delante a considerar por sutta PTS
ALIGN_MIN = 0.30      # cobertura mínima para aceptar una alineación


def _nset(s, n=150):
    return {_nfold(x) for x in sh.tokens(s)[:n]}

# ordinales pāli → distinguir paṭhama/dutiya/tatiya… en series repetitivas
_ORD = {'paṭhama': 1, 'dutiya': 2, 'tatiya': 3, 'catuttha': 4, 'pañcama': 5, 'chaṭṭha': 6,
        'sattama': 7, 'aṭṭhama': 8, 'navama': 9, 'dasama': 10, 'ekādasama': 11, 'dvādasama': 12}
def ordinal_of(s):
    t = re.sub(r'^\s*[\d\-]+\.\s*', '', (s or '').lower())   # quita "4. " / "2-6. "
    for w, k in _ORD.items():
        if t.startswith(w):
            return k
    return None
def is_range(title):
    return bool(re.match(r'^\s*\d+\s*-\s*\d+\.', title or ''))


def align(pts_items, cst_items):
    """Alineación monótona por cobertura con consistencia de ordinal y avance
    rango-aware. pts_items: [(key, pts_text, name)]; cst_items: [(text, title)].
    Devuelve [(key, cst_idx|None, cov)]."""
    cst_sets = [_nset(t) for t, _ in cst_items]
    cst_ord = [ordinal_of(title) for _, title in cst_items]
    cst_rng = [is_range(title) for _, title in cst_items]
    out, ptr = [], 0
    for key, pts, name in pts_items:
        A = _nset(pts)
        pord = ordinal_of(name)
        best_cov, best_idx = -1.0, None
        for j in range(ptr, min(ptr + ALIGN_WINDOW, len(cst_items))):
            if pord and cst_ord[j] and pord != cst_ord[j]:
                continue                          # ordinal en conflicto → no es este miembro
            cov = len(A & cst_sets[j]) / max(1, len(A))
            if cov > best_cov:
                best_cov, best_idx = cov, j
        if best_idx is not None and best_cov >= ALIGN_MIN:
            out.append((key, best_idx, round(best_cov, 2)))
            ptr = best_idx                        # re-ancla (reuso permitido para grupos)
        else:
            out.append((key, None, round(max(best_cov, 0), 2)))  # no mover el puntero
    return out


def load_entries():
    wb = load_workbook('PTS_Reference_Complete_Canon.xlsx', read_only=True)
    ws = wb['Complete Canon']
    hdr = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    ci = {n: i for i, n in enumerate(hdr)}
    out = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if str(row[ci['Nikaya']] or '') != 'SN':
            continue
        snum = str(row[ci['Sutta #']] or '')
        parts = snum.split('.')
        if len(parts) < 2 or not parts[0].isdigit():
            continue
        if not (45 <= int(parts[0]) <= 56):
            continue
        if str(row[ci['PTS Roman']] or '').strip().lower() != 'v':
            continue
        out.append({'num': snum, 'ref': str(row[ci['PTS Ref']] or ''),
                    'name': str(row[ci['Sutta Name']] or ''), 'page': row[ci['PTS Page']],
                    'sn': int(parts[0]), 'sn_inner': int(parts[1]),
                    'legacy': str(row[ci['Validation']] or '')})
    out.sort(key=lambda e: (e['sn'], e['sn_inner']))
    return out


def build_markers(cur):
    mm = defaultdict(list)
    cur.execute('SELECT page_no,unitext FROM pages WHERE book_no=? AND edition="mula"', (SN5_BOOK,))
    for r in cur.fetchall():
        for i, line in enumerate((r['unitext'] or '').split('\n')):
            # marcador "48. (8) Nombre", rango "103--108. (1--6) Pācīna", o grupo
            # profundo sin nombre "63--72. (1--10)." (uddāna a continuación)
            m = re.match(r'^(\d+)(?:\s*-+\s*(\d+))?\.?\s*\((\d+)(?:\s*-+\s*(\d+))?\)\.?\s*(\S.*)?$', line.strip())
            if m:
                a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else a
                for run in range(a, b + 1):        # registra cada nº corrido del rango
                    mm[r['page_no']].append((i + 1, run, int(m.group(3)), (m.group(5) or '')[:60]))
    return mm


def pts_for(cur, page, target, mm):
    for line, gid, vpos, name in mm.get(page, []):
        if gid == target:
            cur.execute('SELECT unitext FROM pages WHERE book_no=? AND page_no=? AND edition="mula"',
                        (SN5_BOOK, page))
            r = cur.fetchone()
            if not r:
                return None
            lines = (r['unitext'] or '').split('\n')
            start, end = line - 1, len(lines)
            for j in range(start + 1, len(lines)):
                if re.match(r'^\d+(?:\s*-+\s*\d+)?\.?\s*\(', lines[j].strip()):
                    end = j
                    break
            return ' '.join(sh.tokens(' '.join(lines[start:end]))[:350])
    return None


_FOLD_N = str.maketrans({'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṅ': 'n', 'ñ': 'n', 'ṇ': 'n',
                         'ṭ': 't', 'ḍ': 'd', 'ḷ': 'l', 'ṃ': 'm', 'ṁ': 'm'})
def _norm_name(t):
    t = re.sub(r'^[\d\-\s]*\.?\s*', '', (t or '').lower()).translate(_FOLD_N)
    return re.sub(r'(.)\1+', r'\1', re.sub(r'[^a-z]', '', t))

def _stem(t):
    # raíz del nombre: quita sufijo sutta/vagga y la terminación de caso (PTS "Ogho" vs CST "Oghasuttaṃ")
    n = re.sub(r'(suttantam|suttam|suttani|vaggo).*$', '', _norm_name(t))
    return re.sub(r'[aiueom]+$', '', n)


def pts_by_name(cur, page, cst_title, mm, span=1):
    """Resuelve el texto PTS casando el NOMBRE del título CST contra el nombre del
    marcador PTS (robusto al off-by-one de numeración de las vaggas peyyāla)."""
    tgt = _stem(cst_title)
    if not tgt or len(tgt) < 3:
        return None
    pages = [page] + [page + d for d in range(1, span + 1)] + [page - d for d in range(1, span + 1)]
    for pg in pages:
        seen = set()
        for line, gid, vpos, name in mm.get(pg, []):
            if line in seen:
                continue
            seen.add(line)
            ns = _stem(name)
            if ns and len(ns) >= 3 and (tgt == ns or tgt.startswith(ns) or ns.startswith(tgt)):
                cur.execute('SELECT unitext FROM pages WHERE book_no=? AND page_no=? AND edition="mula"', (SN5_BOOK, pg))
                r = cur.fetchone()
                lines = (r['unitext'] or '').split('\n')
                start, end = line - 1, len(lines)
                for j in range(start + 1, len(lines)):
                    if re.match(r'^\d+(?:\s*-+\s*\d+)?\.?\s*\(', lines[j].strip()):
                        end = j
                        break
                return ' '.join(sh.tokens(' '.join(lines[start:end]))[:350])
    return None


def cst_boundaries(segs):
    b, cur = {}, 45
    for i, s in enumerate(segs):
        if re.match(r'^1\.\s+\S', s.get('title', '')):
            b[cur] = i
            cur += 1
    b[cur] = len(segs)
    return b


def main():
    import statistics as st
    n = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 30
    do_all = '--all' in sys.argv
    dry = '--dry' in sys.argv
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row; cur = conn.cursor()
    entries = load_entries()
    mm = build_markers(cur)
    segs = sh.load_cha(['s5m.xml'], 'h4n')
    cst_items = [(' '.join(sh.tokens(s['text'])[:350]), s.get('title', '')) for s in segs]

    pts_items, meta = [], {}
    for e in entries:
        pts = pts_for(cur, e['page'], e['sn_inner'], mm)
        if not pts:
            continue
        pts_items.append((e['num'], pts, e['name']))
        meta[e['num']] = (e, pts)

    aligned = align(pts_items, cst_items)
    if not do_all and not dry:
        aligned = aligned[:n]
    na = sum(1 for _, i, _ in aligned if i is None)
    print(f'SN V: {len(entries)} entradas, {len(pts_items)} PTS resolubles; '
          f'alineador → {len(aligned) - na}/{len(aligned)} alineadas')

    if dry:
        covs = [c for _, i, c in aligned if i is not None]
        # consistencia de título: ¿la raíz del nombre PTS aparece en el título CST?
        ok = tot = 0
        for num, idx, _c in aligned:
            if idx is None:
                continue
            tot += 1
            base = _nfold(re.sub(r'^(paṭhama|dutiya|tatiya|catuttha|pañcama|chaṭṭha|sattama|aṭṭhama|navama|dasama)', '',
                                 meta[num][0]['name'].lower()))[:6]
            if base and base in _nfold(cst_items[idx][1].lower()):
                ok += 1
        print(f'[DRY] cobertura alineada: min={min(covs):.2f} mediana={st.median(covs):.2f} '
              f'max={max(covs):.2f} | sin alinear: {na}')
        print(f'[DRY] consistencia de título (raíz PTS ⊂ título CST): {ok}/{tot} ({100*ok/max(1,tot):.0f}%)')
        for thr in (0.45, 0.55, 0.65):
            print(f'  cov>={thr}: {sum(1 for c in covs if c >= thr)}/{len(aligned)}')
        return

    rows = []
    n_align = sum(1 for _, i, _ in aligned if i is not None)
    done = 0
    for num, idx, cov in aligned:
        e, pts = meta[num]
        if idx is not None:
            done += 1
            if done % 25 == 0:
                print(f'  ...{done}/{n_align} alineadas validadas (Gemini)', flush=True)
        if idx is None:
            rows.append({'num': num, 'name': e['name'], 'cst_title': '(sin alinear)', 'legacy': e['legacy'],
                         'estado': 'PENDIENTE', 'validation': 'REVISAR', 'gate': {'cov': cov},
                         'gemini': None, 'reason': f'sin alineación CST confiable (cov={cov})'})
            continue
        cst, ct = cst_items[idx]
        res = validate_pair(pts, cst, e['name'], ct, 'SN')
        rows.append({'num': num, 'name': e['name'], 'cst_title': ct, 'legacy': e['legacy'],
                     'aligncov': cov, **res})
    json.dump(rows, open('validador_sn5_batch.json', 'w'), ensure_ascii=False, indent=1)
    report(rows)


def report(rows):
    est = Counter(r['estado'] for r in rows)
    val = Counter(r['validation'] for r in rows)
    revisar = [r for r in rows if r['validation'] == 'REVISAR']
    print('=' * 92)
    print(f'VALIDADOR (Modelo B) — SN V, primera tanda ({len(rows)})')
    print('=' * 92)
    print(f'Estado: {dict(est)} | Validation: {dict(val)}')
    print(f'\nA revisión humana ({len(revisar)}) — gate y Gemini discrepan:')
    for r in revisar[:60]:
        g = r['gate'] or {}
        gj = f"cov={g['cov']}" if 'cov' in g else (f"jac={g.get('jac')} tit={g.get('title')}" if g else '')
        print(f'  SN {r["num"]:>7} | {r["name"][:20]:20} -> {r["cst_title"][:22]:22} | {gj} | {r["reason"][:40]}')
    print('\nResultados en validador_sn5_batch.json (nada escrito al Excel).')


if __name__ == '__main__':
    main()
