#!/usr/bin/env python3
"""MN III (Uparipaṇṇāsa) — suttas 107-152, book 11, pp.1-302."""
import sqlite3
conn = sqlite3.connect('src/data/tipitaka.sqlite')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

MN3 = [
    (107,1),(108,7),(109,15),(110,20),(111,25),(112,29),(113,37),
    (114,45),(115,61),(116,68),(117,71),(118,78),(119,88),(120,99),
    (121,104),(122,109),(123,118),(124,124),(125,128),(126,138),
    (127,144),(128,152),(129,163),(130,178),(131,187),(132,189),
    (133,192),(134,199),(135,202),(136,207),(137,215),(138,223),
    (139,230),(140,237),(141,248),(142,253),(143,258),(144,263),
    (145,267),(146,270),(147,277),(148,280),(149,287),(150,290),
    (151,293),(152,298),
]

print('MN III — Uparipaṇṇāsa (suttas 107-152, book 11)')
print('═'*60)

ok = fix = fail = 0
for num, page in MN3:
    found_page = None
    found_where = ''
    
    for delta in [0, -1, 1, -2, 2]:
        p = page + delta
        cur.execute('SELECT head, unitext FROM pages WHERE book_no=11 AND page_no=? AND edition="mula"', (p,))
        r = cur.fetchone()
        if not r: continue
        head = r['head'] or ''
        ns = str(num)
        txt = (r['unitext'] or '').lower()
        
        if f'({ns})' in head or f'({ns}.)' in head:
            found_page = p; found_where = f'head num ({ns})'; break
        if 'evam me sutam' in txt or 'evaṃ me sutaṃ' in txt:
            found_page = p; found_where = 'evam me sutam'; break
    
    if found_page == page:
        print(f'  ✓ MN {num:>3d} p.{page} — OK ({found_where})')
        ok += 1
    elif found_page is not None:
        diff = found_page - page
        print(f'  ⚠ MN {num:>3d} p.{page} → p.{found_page} ({found_where}) [Δ={diff:+d}]')
        fix += 1
    else:
        cur.execute('SELECT head FROM pages WHERE book_no=11 AND page_no=? AND edition="mula"', (page,))
        r = cur.fetchone()
        head = (r['head'] or '')[:60].strip() if r else 'MISSING'
        print(f'  ✗ MN {num:>3d} p.{page} — UNVERIFIED head=[{head}]')
        fail += 1

print(f'\n  ✓ OK: {ok}  ⚠ To fix: {fix}  ✗ Unverified: {fail}  Total: {ok+fix+fail}/46')
conn.close()
