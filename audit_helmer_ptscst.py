#!/usr/bin/env python3
"""audit_helmer.py — INDEPENDENT validation of the matcher (LOCAL TOOL).

Addresses the confirmation-bias worry: the accuracy so far is measured
against the Thai page anchors, which are also (in the projection) used
to seed the search — not independent.  Here Helmer Smith (Deepseek
v4-flash) is an INDEPENDENT auditor, evidence in hand, not a picker:

  * for each critical (Se, Cha) pair the matcher decided, CollateX
    aligns the two texts and extracts the exact variant points;
  * each variant is enriched from DPD: is the Se↔Cha difference a KNOWN
    manuscript variant (DPD `variant` field) or an unexplained divergence;
  * Helmer Smith receives both texts, the CollateX variant table, and
    the DPD verdicts, and returns APPROVE / REJECT + a one-line reason.

Because Helmer's judgement never touches the anchors, agreement between
Helmer and the anchor-based label on the confident matches is genuine
cross-validation; disagreement on the residual flags where the anchor
label (not the matcher) was the problem.  50 critical points decide it.

Usage:  python3 utils/audit_helmer.py [N]
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sutta_hash import (REPO, Stemmer, load_se, load_cha, stem_seq,  # noqa
                        tokens, PAIRS)
import sutta_fingerprint as fp                                # noqa: E402

# thread-local DPD connection: SQLite connections are not safe for
# concurrent use, so give every worker thread its own.
_dpd_local = threading.local()


def _dpd():
    c = getattr(_dpd_local, 'conn', None)
    if c is None:
        c = _dpd_local.conn = sqlite3.connect(
            'file:/dev/shm/dpd.db?mode=ro', uri=True, check_same_thread=False)
    return c


ARB_MODEL = 'deepseek-v4-flash'
AUDIT_CACHE = REPO / 'audit-helmer-cache.json'


def collate_variants(se_text, cha_text, maxwords=180):
    """CollateX-align the two texts; return the differing (Se, Cha) cells.
    An empty witness crashes CollateX (empty index range), so guard it."""
    from collatex import Collation, collate
    ta, tb = tokens(se_text)[:maxwords], tokens(cha_text)[:maxwords]
    if not ta or not tb:
        return []
    a, b = ' '.join(ta), ' '.join(tb)
    c = Collation()
    c.add_plain_witness('Se', a)
    c.add_plain_witness('Cha', b)
    table = collate(c, output='table', segmentation=True)
    diffs = []
    for col in table.columns:
        d = col.tokens_per_witness
        sa = ' '.join(str(t) for t in d.get('Se', [])).strip()
        sb = ' '.join(str(t) for t in d.get('Cha', [])).strip()
        if sa != sb:
            diffs.append((sa, sb))
    return diffs


def dpd_variant_known(w1, w2):
    """Does DPD record w1↔w2 (either direction) as a manuscript variant?"""
    for a, b in ((w1, w2), (w2, w1)):
        if not a:
            continue
        r = _dpd().execute("SELECT variant FROM lookup WHERE lookup_key=?",
                           (a,)).fetchone()
        if r and r[0] not in ('', '[]') and b and b in r[0]:
            return True
    return False


def classify(diffs):
    """Tag each variant: known DPD variant, spelling-only, or divergence."""
    out = []
    for sa, sb in diffs[:25]:
        wa, wb = sa.split(), sb.split()
        if not sa or not sb:
            tag = 'insertion/omission'
        elif len(wa) == 1 and len(wb) == 1 and dpd_variant_known(wa[0], wb[0]):
            tag = 'DPD-known variant'
        elif len(wa) == 1 and len(wb) == 1 and \
                re.sub(r'[ṃṁ]', 'm', wa[0]) == re.sub(r'[ṃṁ]', 'm', wb[0]):
            tag = 'orthographic'
        else:
            tag = 'divergence'
        out.append((sa, sb, tag))
    return out


HELMER_SYS = (
    "You are Helmer Smith, Pāli philologist, auditing whether two passages "
    "from different editions (Se = Syāmaraṭṭha, Cha = Chaṭṭhasaṅgāyana) are "
    "THE SAME textual unit. You are given both passages, a CollateX variant "
    "table (points where they differ), and a DPD verdict on each variant "
    "(known manuscript variant / orthographic / unexplained divergence). "
    "Same unit = the differences are variants/elisions/reorderings of one "
    "text; different units = they are distinct suttas. Reply ONLY JSON "
    '{"verdict":"APPROVE"|"REJECT","reason":"<=15 words}.')


def ask_helmer(se_text, cha_text, variants, cli):
    body = ['Se:', se_text[:900], '', 'Cha:', cha_text[:900], '',
            'CollateX variants (Se | Cha | DPD):']
    for sa, sb, tag in variants:
        body.append(f'  "{sa}" | "{sb}" | {tag}')
    r = cli.chat.completions.create(
        model=ARB_MODEL, temperature=0,
        response_format={'type': 'json_object'},
        messages=[{'role': 'system', 'content': HELMER_SYS},
                  {'role': 'user', 'content': '\n'.join(body)}])
    return json.loads(r.choices[0].message.content)


def critical_points(n=50):
    """Collect the decisions worth auditing: every residual failure, the
    twins/low-margin litigations, plus confident matches as controls."""
    st = Stemmer()
    pts = []
    for name in ['d1', 'm1', 's1', 's2']:
        xf, lv, vf = PAIRS[name]
        se, cha = load_se(vf), load_cha(xf, lv)
        pool = se + cha
        for s in pool:
            s['seq'] = stem_seq(s['text'], st)
        idf = fp.global_idf([s['seq'] for s in pool])
        for s in pool:
            s['sig'] = fp.prose_signature(s['seq'], idf, 32, 6)
        for a in se:
            sc = sorted(((fp.prose_score(a['sig'], b['sig'], idf), j)
                         for j, b in enumerate(cha)), reverse=True)
            (s1, j1), (s2, _) = sc[0], sc[1]
            g = fp._good(a, cha[j1])
            if g is None:
                continue
            margin = s1 - s2
            kind = ('FAIL' if not g else
                    'litigation' if margin < 0.10 else 'confident')
            pts.append(dict(name=name, se=a['text'], cha=cha[j1]['text'],
                            se_t=a.get('title'), cha_t=cha[j1]['title'],
                            anchor_good=g, kind=kind, margin=round(margin, 3)))
    # prioritize: all fails + all litigations + fill with confident controls
    fails = [p for p in pts if p['kind'] == 'FAIL']
    lit = [p for p in pts if p['kind'] == 'litigation']
    conf = [p for p in pts if p['kind'] == 'confident']
    import random
    random.seed(0)
    random.shuffle(conf)
    sel = (fails + lit + conf)[:n]
    return sel


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    from openai import OpenAI
    cli = OpenAI(api_key=os.environ['DEEPSEEK_API_KEY'],
                 base_url='https://api.deepseek.com')
    cache = json.loads(AUDIT_CACHE.read_text()) if AUDIT_CACHE.exists() else {}
    pts = critical_points(n)
    lock = threading.Lock()
    results = []

    def work(p):
        key = hashlib.md5((p['se'][:300]+p['cha'][:300]).encode()).hexdigest()
        if key in cache:
            hv = cache[key]
        else:
            try:
                variants = classify(collate_variants(p['se'], p['cha']))
                hv = ask_helmer(p['se'], p['cha'], variants, cli)
                hv['nvar'] = len(variants)
            except Exception as e:                       # noqa: BLE001
                hv = {'verdict': 'ERROR', 'reason': str(e)[:60], 'nvar': 0}
            with lock:
                cache[key] = hv
                AUDIT_CACHE.write_text(json.dumps(cache, ensure_ascii=False))
        with lock:
            results.append((p, hv))

    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(work, pts))

    # cross-tabulate Helmer (independent) vs the anchor label
    agree = disagree = 0
    print(f'{"kind":11s} {"anchor":7s} {"Helmer":8s} margin  variantes  '
          f'razón')
    for p, hv in sorted(results, key=lambda x: x[0]['kind']):
        v = hv.get('verdict', '?')
        anc = 'MATCH' if p['anchor_good'] else 'no'
        hel = 'APPROVE' if v == 'APPROVE' else ('REJECT' if v == 'REJECT'
                                                else v)
        concur = (v == 'APPROVE') == bool(p['anchor_good'])
        if v in ('APPROVE', 'REJECT'):
            agree += concur
            disagree += not concur
        mark = '' if concur else '  <-- DISCREPA'
        print(f'{p["kind"]:11s} {anc:7s} {hel:8s} {p["margin"]:+.3f}  '
              f'{hv.get("nvar", 0):3d}       {hv.get("reason","")[:38]}{mark}')
    from collections import Counter
    fine = Counter()
    for p, hv in results:
        v = hv.get('verdict')
        if v in ('APPROVE', 'REJECT'):
            fine[(p['kind'], v)] += 1
    print(f'\nHelmer (independiente) coincide con ancla: {agree}/'
          f'{agree + disagree}')
    print(f"litigios/confiados MATCH -> Helmer APPROVE "
          f"{fine[('litigation','APPROVE')]+fine[('confident','APPROVE')]}, "
          f"REJECT {fine[('litigation','REJECT')]+fine[('confident','REJECT')]} "
          f"(confirmación independiente de los positivos)")
    print(f"'fallos'-ancla -> Helmer APPROVE {fine[('FAIL','APPROVE')]} "
          f"(etiqueta-ancla mala, matcher acertó), "
          f"REJECT {fine[('FAIL','REJECT')]} (error real del matcher)")
    # the informative cases: where they disagree
    print('Interpretación: en los FAIL, si Helmer APPROVE => el fallo era de '
          'la etiqueta-ancla, no del matcher.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
