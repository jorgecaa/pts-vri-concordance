#!/usr/bin/env python3
"""sutta_fingerprint.py — custom cross-edition fingerprint (LOCAL TOOL).

A bespoke signature for matching a text unit across editions, built on
what this corpus actually is (Jorge's design, 2026-07-18):

  Layer 1 — NORMALIZED STREAM (materialized, cached, reusable): each unit
    from the CLEAN corpus (Canonical/, Non-Canonical/ — never txt/) is
    reduced to its ordered content stems (DPD lemma + sandhi-resolved,
    particles/pts/apparatus dropped) with global idf and relative
    position.  The expensive, deterministic part — computed once.

  Layer 2 — SIGNATURE (cheap, recomputable/tunable):
    * PROSE: a positional-bin sketch of the rarest (highest-idf) stems.
      B position-bins × k rare stems.  Encodes Jorge's two measured
      invariants — near-constant word count (bins align 1:1 across
      editions) and progressive order (bin position is information) —
      so it is asymmetry-tolerant (peyyāla thins a bin, never shifts it)
      and separates content-identical twins (their rare stems fall in
      DIFFERENT bins).  Proper names (idf-max) dominate a bin by design.
    * VERSE (Thera/Therī/Dhp/Sn/Jātaka): the laghu/garu metrical weight
      string — the invariant that survives orthographic drift (validated
      0.96).  Material dictates the hash.

  Layer 3 — LITIGATION RESOLVER: for a low-margin decision (margin below
    the data-calibrated 0.10) rerank the top candidates by difflib ratio
    on the STEM STREAMS.  Measured 2026-07-18: over the litigations this
    corrected 8 and broke 0 (95.7% -> 96.9%).  It works precisely where
    the two other approaches fail: the lossy bin signature BLURS a twin's
    one distinguishing keyword, and the LLM (Helmer-Smith on the texts)
    MISREADS two near-identical passages (it fixed 0, broke 5) — but a
    mechanical diff COUNTS every occurrence of the differing keyword
    (tatiya- vs paṭhama-, du- vs su-), so the true twin wins cleanly.
    Deterministic, no API.  (CollateX is heavier and belongs to the
    future apparatus layer — generating the variant readings — not to
    this binary twin choice, which difflib already settles.)

Usage:
    python3 utils/sutta_fingerprint.py bench      # reproduce match bench
    python3 utils/sutta_fingerprint.py build      # materialize streams
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sutta_hash import (                                      # noqa: E402
    REPO, Stemmer, tokens, stem_seq, load_se, load_cha, metric_weights,
    PAIRS)

# ── Layer 1: normalized stream ───────────────────────────────────────────────

def normalized_stream(text, st):
    """Ordered content stems of a unit (particles already dropped by
    stem_seq; sandhi + DPD lemma already applied by the Stemmer)."""
    return stem_seq(text, st)


def global_idf(streams):
    """Document-frequency idf of every stem over the pool of units."""
    df = {}
    for seq in streams:
        for s in set(seq):
            df[s] = df.get(s, 0) + 1
    n = len(streams)
    return {s: math.log(n / c) for s, c in df.items()}


# ── Layer 2: prose positional-bin signature ──────────────────────────────────

def prose_signature(seq, idf, B=24, k=3):
    """B position-bins, each the k highest-idf (rarest) stems present.
    Returns a tuple of B frozensets — fixed shape, comparable, packable."""
    n = len(seq)
    if n == 0:
        return tuple(frozenset() for _ in range(B))
    bins = []
    for b in range(B):
        lo, hi = b * n // B, (b + 1) * n // B
        seg = seq[lo:hi] if hi > lo else seq[lo:lo + 1]
        # k rarest distinct stems in this bin
        top = sorted(set(seg), key=lambda s: -idf.get(s, 0.0))[:k]
        bins.append(frozenset(top))
    return tuple(bins)


def prose_score(a, b, idf, alpha=0.5):
    """Blend of two idf-weighted asymmetric containments, both read off the
    same B×k signature at no extra storage:
      * GLOBAL: a's rare-stem SET in b's — recovers recall (matches even
        when a peyyāla shifts material across a bin boundary);
      * POSITIONAL: bin-by-bin — discriminates content-identical twins
        (same set, different order → different bins).
    alpha weights positional; (1-alpha) global."""
    set_a, set_b = set().union(*a), set().union(*b)
    dg = sum(idf.get(s, 0.0) for s in set_a)
    ng = sum(idf.get(s, 0.0) for s in set_a & set_b)
    g = ng / dg if dg else 0.0
    npos = dpos = 0.0
    for ba, bb in zip(a, b):
        for s in ba:
            w = idf.get(s, 0.0)
            dpos += w
            if s in bb:
                npos += w
    p = npos / dpos if dpos else 0.0
    return alpha * p + (1 - alpha) * g


# ── Layer 2: verse metrical signature ────────────────────────────────────────

def verse_signature(text):
    return metric_weights(text)


def verse_score(a, b):
    import difflib
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


# ── benchmark: does the signature reproduce the matcher's accuracy? ──────────

def bench(names=('d1', 'd2', 'd3', 'm1', 'm2', 'm3', 's1', 's2'),
          B=24, k=3):
    st = Stemmer()
    tot_ok = tot = 0
    for name in names:
        xmlfiles, level, volfile = PAIRS[name]
        se, cha = load_se(volfile), load_cha(xmlfiles, level)
        pool = se + cha
        for s in pool:
            s['seq'] = normalized_stream(s['text'], st)
        idf = global_idf([s['seq'] for s in pool])
        for s in pool:
            s['sig'] = prose_signature(s['seq'], idf, B, k)
        # monotonic alignment on the signature score (same DP as the matcher)
        n, m = len(se), len(cha)
        S = [[prose_score(a['sig'], b['sig'], idf) for b in cha] for a in se]
        THR = 0.05
        dp = [[0.0] * (m + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1],
                               dp[i - 1][j - 1] + (S[i - 1][j - 1]
                                                   if S[i - 1][j - 1] > THR
                                                   else 0.0))
        pairs = {}
        i, j = n, m
        while i > 0 and j > 0:
            if S[i - 1][j - 1] > THR and \
                    dp[i][j] == dp[i - 1][j - 1] + S[i - 1][j - 1]:
                pairs[i - 1] = j - 1
                i, j = i - 1, j - 1
            elif dp[i][j] == dp[i - 1][j]:
                i -= 1
            else:
                j -= 1
        ok = 0
        for ia, a in enumerate(se):
            if ia not in pairs:
                continue
            b = cha[pairs[ia]]
            good = None
            if b['anchors']:
                lo, hi = b['anchors']
                good = not (hi < a['pages'][0] or lo > a['pages'][1])
            elif a['title'] and b['title']:
                import re
                nt = lambda t: re.sub(r'[^a-zāīūṁṅñṭḍṇḷ]', '',
                                      t.lower().replace('ṃ', 'ṁ'))
                good = nt(a['title']) in nt(b['title'])
            if good is not False:
                ok += 1
        tot_ok += ok
        tot += len([1 for ia in range(len(se)) if ia in pairs])
        print(f'{name}: {ok}/{len([1 for ia in range(len(se)) if ia in pairs])}'
              f' emparejados-correctos  (Se {len(se)} vs Cha {len(cha)})')
    print(f'\nfirma B={B} k={k}: {tot_ok}/{tot}')
    return tot_ok, tot


# ── Layer 3: Helmer-Smith arbiter for litigation cases ───────────────────────

ARB_CACHE = REPO / 'fingerprint-arbiter-cache.json'
ARB_SYS = (
    "You are Helmer Smith, Pāli philologist. A passage from the Syāmaraṭṭha "
    "(Thai) edition is given, then numbered candidate passages from the "
    "Chaṭṭhasaṅgāyana (Burmese) edition. Exactly one candidate is the SAME "
    "textual unit (allowing manuscript variants, sandhi and .pe. elision "
    "differences). Reply ONLY JSON {\"match\": N} with the candidate number, "
    "or {\"match\": 0} if none is the same unit.")


def arbiter(query_text, candidates, _cache={}):
    """Ask Helmer-Smith which candidate matches; cached (static corpus).
    `candidates` = list of (label, text).  Returns the 1-based index or 0."""
    if not _cache and ARB_CACHE.exists():
        _cache.update(json.loads(ARB_CACHE.read_text()))
    key = str(hash((query_text[:400],
                    tuple(t[:200] for _, t in candidates))))
    if key in _cache:
        return _cache[key]
    import os
    from openai import OpenAI
    cli = OpenAI(api_key=os.environ['DEEPSEEK_API_KEY'],
                 base_url='https://api.deepseek.com')
    body = ['SYĀMARAṬṬHA:', query_text[:1500], '', 'CANDIDATES:']
    for i, (_, t) in enumerate(candidates, 1):
        body.append(f'[{i}] {t[:1200]}')
    try:
        r = cli.chat.completions.create(
            model='deepseek-chat', temperature=0,
            response_format={'type': 'json_object'},
            messages=[{'role': 'system', 'content': ARB_SYS},
                      {'role': 'user', 'content': '\n'.join(body)}])
        v = int(json.loads(r.choices[0].message.content).get('match', 0))
    except Exception:                                        # noqa: BLE001
        v = 0
    _cache[key] = v
    ARB_CACHE.write_text(json.dumps(_cache, ensure_ascii=False))
    return v


def _good(a, b):
    if b['anchors']:
        lo, hi = b['anchors']
        return not (hi < a['pages'][0] or lo > a['pages'][1])
    if a['title'] and b['title']:
        import re
        nt = lambda t: re.sub(r'[^a-zāīūṁṅñṭḍṇḷ]', '',
                              t.lower().replace('ṃ', 'ṁ'))
        return nt(a['title']) in nt(b['title'])
    return None


def calibrate(names=('d1', 'd2', 'd3', 'm1', 'm2', 'm3', 's1', 's2'),
              B=32, k=6):
    """For every top-1 decision record (margin = s1 - s2, correct?), then
    report the margin band where correctness collapses — the litigation
    threshold below which the arbiter should take over."""
    st = Stemmer()
    rows = []
    for name in names:
        xmlfiles, level, volfile = PAIRS[name]
        se, cha = load_se(volfile), load_cha(xmlfiles, level)
        pool = se + cha
        for s in pool:
            s['seq'] = normalized_stream(s['text'], st)
        idf = global_idf([s['seq'] for s in pool])
        for s in pool:
            s['sig'] = prose_signature(s['seq'], idf, B, k)
        for a in se:
            sc = sorted(((prose_score(a['sig'], b['sig'], idf), j)
                         for j, b in enumerate(cha)), reverse=True)
            (s1, j1), (s2, _) = sc[0], sc[1]
            g = _good(a, cha[j1])
            if g is not None:
                rows.append((s1 - s2, s1, g))
    rows.sort()
    print(f'{len(rows)} decisiones verificables')
    for lo, hi in [(0, .02), (.02, .05), (.05, .1), (.1, .2), (.2, 1)]:
        band = [r for r in rows if lo <= r[0] < hi]
        if band:
            acc = sum(r[2] for r in band) / len(band)
            print(f'  margen [{lo:.2f},{hi:.2f}): {len(band):4d} casos, '
                  f'acierto {acc:.0%}')
    # threshold = lowest margin at which accuracy stays >= 0.95 upward
    for thr in [.02, .05, .08, .1, .15]:
        above = [r for r in rows if r[0] >= thr]
        below = [r for r in rows if r[0] < thr]
        aa = sum(r[2] for r in above) / max(len(above), 1)
        print(f'  umbral {thr:.2f}: arriba {len(above)} (acierto {aa:.1%}), '
              f'litigio {len(below)} -> árbitro')
    return rows


def bench_arbiter(names=('d1', 'd2', 'd3', 'm1', 'm2', 'm3', 's1', 's2'),
                  B=32, k=6, thr=0.10):
    """Top-1 by the hash; escalate margin<thr litigations to Helmer-Smith
    over the top-3 candidates.  Reports deterministic vs arbitrated."""
    st = Stemmer()
    det_ok = det_n = arb_ok = arb_n = arb_fixed = 0
    for name in names:
        xmlfiles, level, volfile = PAIRS[name]
        se, cha = load_se(volfile), load_cha(xmlfiles, level)
        pool = se + cha
        for s in pool:
            s['seq'] = normalized_stream(s['text'], st)
        idf = global_idf([s['seq'] for s in pool])
        for s in pool:
            s['sig'] = prose_signature(s['seq'], idf, B, k)
        for a in se:
            sc = sorted(((prose_score(a['sig'], b['sig'], idf), j)
                         for j, b in enumerate(cha)), reverse=True)
            (s1, j1), (s2, _) = sc[0], sc[1]
            g = _good(a, cha[j1])
            if g is None:
                continue
            if s1 - s2 >= thr:                       # deterministic
                det_n += 1
                det_ok += g
            else:                                    # litigation -> arbiter
                arb_n += 1
                cands = [(str(j), cha[j]['text']) for _, j in sc[:3]]
                pick = arbiter(a['text'], cands)
                chosen = sc[pick - 1][1] if 1 <= pick <= len(cands) else j1
                ga = _good(a, cha[chosen])
                arb_ok += bool(ga)
                if ga and not g:
                    arb_fixed += 1
    print(f'deterministas: {det_ok}/{det_n} ({det_ok/max(det_n,1):.1%})')
    print(f'litigios al árbitro: {arb_n} | árbitro acierta {arb_ok}/{arb_n}'
          f' | corrigió {arb_fixed} que el hash fallaba')
    print(f'TOTAL: {det_ok + arb_ok}/{det_n + arb_n} '
          f'({(det_ok+arb_ok)/max(det_n+arb_n,1):.1%})')


def arb_residual(names=('d1', 'd2', 'd3', 'm1', 'm2', 'm3', 's1', 's2'),
                 B=32, k=6):
    """Run the FULL system: hash -> monotonic alignment -> arbiter only on
    the pairs the alignment got wrong-or-uncertain.  Measures whether the
    arbiter adds anything on top of the alignment (its proper niche)."""
    st = Stemmer()
    align_ok = align_n = fixed = broke = escalated = 0
    for name in names:
        xmlfiles, level, volfile = PAIRS[name]
        se, cha = load_se(volfile), load_cha(xmlfiles, level)
        pool = se + cha
        for s in pool:
            s['seq'] = normalized_stream(s['text'], st)
        idf = global_idf([s['seq'] for s in pool])
        for s in pool:
            s['sig'] = prose_signature(s['seq'], idf, B, k)
        n, m = len(se), len(cha)
        S = [[prose_score(a['sig'], b['sig'], idf) for b in cha] for a in se]
        THR = 0.05
        dp = [[0.0] * (m + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1],
                               dp[i - 1][j - 1] + (S[i - 1][j - 1]
                                                   if S[i - 1][j - 1] > THR
                                                   else 0))
        pairs = {}
        i, j = n, m
        while i > 0 and j > 0:
            if S[i - 1][j - 1] > THR and \
                    dp[i][j] == dp[i - 1][j - 1] + S[i - 1][j - 1]:
                pairs[i - 1] = j - 1; i, j = i - 1, j - 1
            elif dp[i][j] == dp[i - 1][j]:
                i -= 1
            else:
                j -= 1
        for ia, a in enumerate(se):
            if ia not in pairs:
                continue
            jb = pairs[ia]
            g = _good(a, cha[jb])
            if g is None:
                continue
            align_n += 1
            align_ok += g
            # arbitrate only the low-margin (uncertain) alignment decisions
            row = sorted(((S[ia][jj], jj) for jj in range(m)), reverse=True)
            if row[0][0] - row[1][0] < 0.10:
                escalated += 1
                cands = [(str(jj), cha[jj]['text']) for _, jj in row[:3]]
                pick = arbiter(a['text'], cands)
                chosen = row[pick - 1][1] if 1 <= pick <= 3 else jb
                ga = _good(a, cha[chosen])
                if ga and not g:
                    fixed += 1
                elif g and not ga:
                    broke += 1
    print(f'alineamiento solo: {align_ok}/{align_n} '
          f'({align_ok/max(align_n,1):.1%})')
    print(f'árbitro sobre {escalated} decisiones inciertas: '
          f'corrigió {fixed}, rompió {broke} (neto {fixed - broke:+d})')
    print(f'sistema completo: {align_ok + fixed - broke}/{align_n} '
          f'({(align_ok + fixed - broke)/max(align_n,1):.1%})')


VERSE_VOLS = {'26-Vv-Pv-Th-Thi.txt'}    # verse -> metric signature


def build(B=32, k=6):
    """Materialize a fingerprint for every Se unit of sutta-index.csv,
    keyed by its (Se) citation.  Prose units get the positional-bin stem
    signature (idf over the whole Se corpus); verse units the metric
    string.  Written to sutta-fingerprints.json — the stored identifier
    any project can compare without recomputing."""
    import csv
    st = Stemmer()
    rows = [r for r in csv.DictReader(
        open(REPO / 'sutta-index.csv', encoding='utf-8-sig'))]
    vol_lines = {}
    def text_of(r):
        f = r['file']
        if f not in vol_lines:
            vol_lines[f] = (REPO / 'Canonical' / f).read_text(
                encoding='utf-8-sig').split('\n')
        seg = vol_lines[f][int(r['start_line']) - 1:int(r['end_line'])]
        return ' '.join(l for l in seg if not l.startswith(
            ('footnote:', 'page number:')))
    # global idf over all prose units
    prose = [r for r in rows if r['file'] not in VERSE_VOLS]
    streams = {}
    for r in prose:
        streams[id(r)] = normalized_stream(text_of(r), st)
    idf = global_idf(list(streams.values()))
    out = {}
    for r in rows:
        cite = r['se_start']
        if r['file'] in VERSE_VOLS:
            out[cite] = {'type': 'verse', 'file': r['file'],
                         'lines': [r['start_line'], r['end_line']],
                         'metric': verse_signature(text_of(r))}
        else:
            sig = prose_signature(streams[id(r)], idf, B, k)
            out[cite] = {'type': 'prose', 'file': r['file'],
                         'lines': [r['start_line'], r['end_line']],
                         'bins': [sorted(b) for b in sig]}
    (REPO / 'sutta-fingerprints.json').write_text(
        json.dumps(out, ensure_ascii=False), encoding='utf-8')
    np = sum(1 for v in out.values() if v['type'] == 'prose')
    print(f'{len(out)} huellas -> sutta-fingerprints.json '
          f'({np} prosa B={B}×k={k}, {len(out) - np} verso métrico)')


def bench_diff(names=('d1', 'd2', 'd3', 'm1', 'm2', 'm3', 's1', 's2'),
               B=32, k=6, thr=0.10):
    """Full system: hash + monotonic alignment, then for every low-margin
    litigation rerank the top candidates by difflib ratio on the STEM
    streams (deterministic, replaces the counterproductive LLM arbiter).
    difflib counts every occurrence of a twin's distinguishing keyword,
    which the lossy bin signature blurs."""
    import difflib
    st = Stemmer()
    base_ok = diff_ok = n = lit = flipped_good = flipped_bad = 0
    for name in names:
        xmlfiles, level, volfile = PAIRS[name]
        se, cha = load_se(volfile), load_cha(xmlfiles, level)
        pool = se + cha
        for s in pool:
            s['seq'] = normalized_stream(s['text'], st)
        idf = global_idf([s['seq'] for s in pool])
        for s in pool:
            s['sig'] = prose_signature(s['seq'], idf, B, k)

        def ratio(x, y):
            return difflib.SequenceMatcher(None, x, y, autojunk=False).ratio()

        for a in se:
            sc = sorted(((prose_score(a['sig'], b['sig'], idf), j)
                         for j, b in enumerate(cha)), reverse=True)
            (s1, j1), (s2, _) = sc[0], sc[1]
            if _good(a, cha[j1]) is None:
                continue
            n += 1
            base = _good(a, cha[j1])
            base_ok += base
            if s1 - s2 < thr:                        # litigation: difflib
                lit += 1
                cands = [j for _, j in sc[:4]]
                dj = max(cands, key=lambda j: ratio(a['seq'], cha[j]['seq']))
                d = bool(_good(a, cha[dj]))
                diff_ok += d
                if d and not base:
                    flipped_good += 1
                elif base and not d:
                    flipped_bad += 1
            else:
                diff_ok += base
    print(f'hash+alineamiento solo:  {base_ok}/{n} ({base_ok/n:.1%})')
    print(f'+ difflib en {lit} litigios: corrigió {flipped_good}, '
          f'rompió {flipped_bad} (neto {flipped_good - flipped_bad:+d})')
    print(f'SISTEMA hash+difflib:    {diff_ok}/{n} ({diff_ok/n:.1%})')


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'bench'
    if cmd == 'bench-diff':
        bench_diff()
        return 0
    if cmd == 'build':
        build()
        return 0
    if cmd == 'calibrate':
        calibrate()
        return 0
    if cmd == 'bench-arb':
        bench_arbiter()
        return 0
    if cmd == 'arb-residual':
        arb_residual()
        return 0
    if cmd == 'bench':
        Bk = [(int(a.split('=')[1]) if a.startswith('B=') else None,
               int(a.split('=')[1]) if a.startswith('k=') else None)
              for a in sys.argv[2:]]
        B = next((x[0] for x in Bk if x[0]), 24)
        k = next((x[1] for x in Bk if x[1]), 3)
        bench(B=B, k=k)
    return 0


if __name__ == '__main__':
    sys.exit(main())
