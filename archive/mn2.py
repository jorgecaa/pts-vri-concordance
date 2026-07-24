#!/usr/bin/env python3
"""MN II (Majjhimapaṇṇāsa) — suttas 77-106, book 10, pp.1-266."""
import sqlite3
conn = sqlite3.connect('src/data/tipitaka.sqlite')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

MN2 = [
    (77,1),(78,22),(79,29),(80,40),(81,45),(82,54),(83,74),(84,83),
    (85,91),(86,97),(87,106),(88,112),(89,118),(90,125),(91,133),
    (92,146),(93,147),(94,157),(95,164),(96,177),(97,184),(98,196),
    (99,196),(100,209),(101,214),(102,228),(103,238),(104,243),
    (105,252),(106,261),
]

print('MN II — Majjhimapaṇṇāsa (suttas 77-106, book 10)')
print('═'*60)

ok = fix = fail = 0
for num, page in MN2:
    found_page = None
    found_where = ''
    
    for delta in [0, -1, 1, -2, 2]:
        p = page + delta
        cur.execute('SELECT head, unitext FROM pages WHERE book_no=10 AND page_no=? AND edition="mula"', (p,))
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
        cur.execute('SELECT head FROM pages WHERE book_no=10 AND page_no=? AND edition="mula"', (page,))
        r = cur.fetchone()
        head = (r['head'] or '')[:60].strip() if r else 'MISSING'
        print(f'  ✗ MN {num:>3d} p.{page} — UNVERIFIED head=[{head}]')
        fail += 1

print(f'\n  ✓ OK: {ok}  ⚠ To fix: {fix}  ✗ Unverified: {fail}  Total: {ok+fix+fail}/30')
conn.close()
