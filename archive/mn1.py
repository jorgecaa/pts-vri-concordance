#!/usr/bin/env python3
"""MN I (Mūlapaṇṇāsa) — suttas 1-76, book 9, pp.1-524.
Pattern: paṇṇāsaka headers alternate with sutta headers.
Even pages = vagga, odd pages = sutta name."""
import sqlite3
conn = sqlite3.connect('src/data/tipitaka.sqlite')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

MN1 = [
    (1,1),(2,6),(3,12),(4,16),(5,24),(6,33),(7,36),(8,40),
    (9,46),(10,55),(11,63),(12,68),(13,83),(14,91),(15,95),
    (16,101),(17,104),(18,108),(19,114),(20,118),(21,122),
    (22,130),(23,142),(24,145),(25,151),(26,160),(27,175),
    (28,184),(29,192),(30,198),(31,205),(32,212),(33,220),
    (34,225),(35,227),(36,237),(37,251),(38,256),(39,271),
    (40,281),(41,285),(42,290),(43,292),(44,299),(45,305),
    (46,309),(47,317),(48,320),(49,326),(50,332),(51,339),
    (52,349),(53,353),(54,359),(55,368),(56,371),(57,387),
    (58,392),(59,396),(60,400),(61,414),(62,420),(63,426),
    (64,432),(65,437),(66,447),(67,456),(68,462),(69,469),
    (70,473),(71,481),(72,483),(73,489),(74,497),(75,501),(76,513),
]

def sd(t):
    for k,v in {'ā':'a','ī':'i','ū':'u','ṁ':'m','ṃ':'m','ṅ':'n','ñ':'n','ṭ':'t','ḍ':'d','ṇ':'n','ḷ':'l'}.items():
        t=t.replace(k,v).replace(k.upper(),v.upper())
    return t

print('MN I — Mūlapaṇṇāsa (suttas 1-76, book 9)')
print('═'*60)

ok = fix = fail = 0
for num, page in MN1:
    # Strategy: MN I sutta headers appear on ODD pages
    # Even pages have vagga headers (MŪLAPAṆṆĀSAṂ)
    # Check: stated page, or stated±1
    
    found_page = None
    found_where = ''
    
    for delta in [0, -1, 1, -2, 2]:
        p = page + delta
        cur.execute('SELECT head, unitext FROM pages WHERE book_no=9 AND page_no=? AND edition="mula"', (p,))
        r = cur.fetchone()
        if not r: continue
        
        head = r['head'] or ''
        ns = str(num)
        txt = (r['unitext'] or '').lower()
        
        # Check 1: Sutta number in head: "(14)" or "(14.)"
        if f'({ns})' in head or f'({ns}.)' in head:
            found_page = p
            found_where = f'head num ({ns})'
            break
        
        # Check 2: Opening formula in body
        if 'evam me sutam' in txt or 'evaṃ me sutaṃ' in txt:
            found_page = p
            found_where = 'evam me sutam'
            break
    
    if found_page == page:
        print(f'  ✓ MN {num:>3d} p.{page} — confirmed ({found_where})')
        ok += 1
    elif found_page is not None and found_page != page:
        diff = found_page - page
        print(f'  ⚠ MN {num:>3d} p.{page} → CORRECT p.{found_page} ({found_where}) [Δ={diff:+d}]')
        fix += 1
    else:
        # Last resort: check full body text for sutta name
        cur.execute('SELECT head, unitext FROM pages WHERE book_no=9 AND page_no=? AND edition="mula"', (page,))
        r = cur.fetchone()
        head = r['head'][:60].strip() if r else 'MISSING'
        print(f'  ✗ MN {num:>3d} p.{page} — UNVERIFIED head=[{head}]')
        fail += 1

print(f'\n  ✓ OK: {ok}  ⚠ To fix: {fix}  ✗ Unverified: {fail}')
print(f'  Total: {ok+fix+fail}/76')

conn.close()
