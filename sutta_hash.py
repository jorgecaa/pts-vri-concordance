#!/usr/bin/env python3
"""sutta_hash.py — cross-edition sutta fingerprint (LOCAL TOOL, not in git).

Verifies Jorge's design for matching suttas across editions (Se =
Syāmaraṭṭha, this corpus; Cha = Chaṭṭha Saṅgāyana, DPR XML at
~/Code/digitalpalireader/tipitaka/my/):

  * every token is reduced to a declension-free stem — DPD headword id
    when the Digital Pāḷi Dictionary knows the form (all inflections of
    a lemma collapse to one id), DPD deconstructor parts for unknown
    compounds, and a rule-based suffix-strip + degemination fallback
    (sukhadukkhassa -> sukha dukha) for the ~3% residue;
  * the fingerprint is the ORDERED stem sequence, featurized as stem
    trigrams weighted by idf (rare trigrams dominate, shared pericopes
    and peyyāla expansions do not);
  * score = asymmetric weighted containment (robust to one edition
    abbreviating with .pe. what the other expands);
  * the progressive-order signal is checked explicitly (Spearman rho of
    first-occurrence positions of shared distinctive trigrams).

Ground truth for validation: sutta titles (DN/MN) and the Thai-edition
page anchors `^a^TV.PPPP^ea^` embedded in the DPR files, which must
fall inside the (Se) page range of the matched row of sutta-index.csv.

Usage:  python3 utils/sutta_hash.py [d1 d2 d3 m1 s1 s2 | all]
"""

import csv
import json
import math
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DPR = Path.home() / 'Code/digitalpalireader/tipitaka/my'
DPD = 'file:/dev/shm/dpd.db?mode=ro'

# pair -> (DPR files in order, sutta heading level, Se volume file)
PAIRS = {
    'd1': (['d1m.xml'], 'h2n', '09-Digha-1.txt'),
    'd2': (['d2m.xml'], 'h2n', '10-Digha-2.txt'),
    'd3': (['d3m.xml'], 'h2n', '11-Digha-3.txt'),
    'm1': (['m1m.xml'], 'h3n', '12-Majjhima-1.txt'),
    'm2': (['m2m.xml'], 'h3n', '13-Majjhima-2.txt'),
    'm3': (['m3m.xml'], 'h3n', '14-Majjhima-3.txt'),
    's1': (['s1m.xml'], 'h4n', '15-Samyutta-1.txt'),
    's2': (['s2m.xml'], 'h4n', '16-Samyutta-2.txt'),
    's3': (['s3m.xml'], 'h4n', '17-Samyutta-3.txt'),
    's4': (['s4m.xml'], 'h4n', '18-Samyutta-4.txt'),
    's5': (['s5m.xml'], 'h4n', '19-Samyutta-5.txt'),
    # Burmese AN is one file per nipāta; Thai packs them 3+1+2+3+2 per tome
    'a20': (['a1m.xml', 'a2m.xml', 'a3m.xml'], 'h4n', '20-Anguttara-1.txt'),
    'a21': (['a4m.xml'], 'h4n', '21-Anguttara-2.txt'),
    'a22': (['a5m.xml', 'a6m.xml'], 'h4n', '22-Anguttara-3.txt'),
    'a23': (['a7m.xml', 'a8m.xml', 'a9m.xml'], 'h4n', '23-Anguttara-4.txt'),
    'a24': (['a10m.xml', 'a11m.xml'], 'h4n', '24-Anguttara-5.txt'),
}
# pairs whose Se side has no (or partial) sutta rows: boundary projection
PROJECT = ['s3', 's4', 's5', 'a20', 'a21', 'a22', 'a23', 'a24']

# Vinaya + Khuddaka: one Burmese file per work; the digit of the embedded
# Thai anchor (T<d>.<page>) is the work-relative tome, mapping to our
# volume; pages are absolute within that volume.  k19m-k21m (Milinda,
# Netti, Peṭakopadesa) carry no anchors — Milinda is Non-Canonical here,
# the other two are absent from this corpus.
VK_FILES = [
    ('v1m.xml', 'h4n', {1: '01-Mahavibhanga-1.txt', 2: '02-Mahavibhanga-2.txt'}),
    ('v2m.xml', 'h4n', {2: '02-Mahavibhanga-2.txt'}),
    ('v3m.xml', 'h4n', {0: '03-Bhikkunivibhanga.txt'}),
    ('v4m.xml', 'h4n', {1: '04-Mahavagga-1.txt', 2: '05-Mahavagga-2.txt'}),
    ('v5m.xml', 'h4n', {1: '06-Cullavagga-1.txt', 2: '07-Cullavagga-2.txt'}),
    ('v6m.xml', 'h4n', {0: '08-Parivara.txt'}),
    ('k1m.xml', 'h4n', {0: '25-Khp-Dhp-Ud-Iti-Sn.txt'}),
    ('k2m.xml', 'h4n', {0: '25-Khp-Dhp-Ud-Iti-Sn.txt'}),
    ('k3m.xml', 'h4n', {0: '25-Khp-Dhp-Ud-Iti-Sn.txt'}),
    ('k4m.xml', 'h4n', {0: '25-Khp-Dhp-Ud-Iti-Sn.txt'}),
    ('k5m.xml', 'h4n', {0: '25-Khp-Dhp-Ud-Iti-Sn.txt'}),
    ('k6m.xml', 'h4n', {0: '26-Vv-Pv-Th-Thi.txt'}),
    ('k7m.xml', 'h4n', {0: '26-Vv-Pv-Th-Thi.txt'}),
    ('k8m.xml', 'h4n', {0: '26-Vv-Pv-Th-Thi.txt'}),
    ('k9m.xml', 'h4n', {0: '26-Vv-Pv-Th-Thi.txt'}),
    ('k14m.xml', 'h4n', {1: '27-Jataka-1.txt'}),
    ('k15m.xml', 'h4n', {1: '27-Jataka-1.txt', 2: '28-Jataka-2.txt'}),
    ('k16m.xml', 'h4n', {0: '29-Mahaniddesa.txt'}),
    ('k17m.xml', 'h4n', {0: '30-Culaniddesa.txt'}),
    ('k18m.xml', 'h4n', {1: '31-Patisambhidamagga.txt'}),
    ('k10m.xml', 'h4n', {1: '32-Apadana-1.txt', 2: '33-Apadana-2.txt'}),
    ('k11m.xml', 'h4n', {2: '33-Apadana-2.txt'}),
    ('k12m.xml', 'h4n', {2: '33-Apadana-2.txt'}),
    ('k13m.xml', 'h4n', {2: '33-Apadana-2.txt'}),
]

VOLSIG = {}
for _v in range(1, 9):
    VOLSIG[_v] = ('Vin', ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII',
                          'VIII'][_v - 1])
for _i, _v in enumerate(range(9, 12)):   VOLSIG[_v] = ('D', ['I', 'II', 'III'][_i])
for _i, _v in enumerate(range(12, 15)):  VOLSIG[_v] = ('M', ['I', 'II', 'III'][_i])
for _i, _v in enumerate(range(15, 20)):  VOLSIG[_v] = ('S', ['I', 'II', 'III', 'IV', 'V'][_i])
for _i, _v in enumerate(range(20, 25)):  VOLSIG[_v] = ('A', ['I', 'II', 'III', 'IV', 'V'][_i])
for _i, _v in enumerate(range(25, 34)):  VOLSIG[_v] = ('Khu', ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX'][_i])

TOK = re.compile(r"[a-zāīūṃṅñṭḍṇḷ]+")
ANCHOR_T = re.compile(r'\^a\^T(\d+)\.(\d+)\^ea\^')
DPR_NOISE = re.compile(r'\^a\^[^^]*\^ea\^|\^[a-z]+\^|<[^>]+>|\[\d+\]')

# Rule fallback: longest-match declension endings, then degemination.
ENDINGS = sorted(['ssa', 'smiṃ', 'mhi', 'mhā', 'bhi', 'ehi', 'esu', 'āsu',
                  'ānaṃ', 'īnaṃ', 'ūnaṃ', 'āya', 'āyo', 'ena', 'assa',
                  'āni', 'īni', 'ūni', 'aṃ', 'iṃ', 'uṃ', 'o', 'ā', 'e',
                  'i', 'u', 'ī', 'ū'], key=len, reverse=True)


PTS_REF = re.compile(r'\(pts\.[^)]*(?:\([^)]*\))?[^)]*\)')


def tokens(text):
    """Tokenize + re-fuse the quotative: the Burmese XML prints the
    sandhi-lengthened form split (`paripūressatī ti`) where Se fuses it
    (`paripūressatīti`); DPD only knows the fused form, so unfused stubs
    would stem differently on each side.  Single-letter tokens are XML
    debris, dropped.  PTS references — present only on the Se side, so
    pure asymmetric noise that depressed every score — are stripped."""
    text = PTS_REF.sub(' ', text.lower().replace('ṁ', 'ṃ'))
    ws = TOK.findall(text)
    out = []
    for w in ws:
        if w == 'ti' and out and out[-1][-1] in 'āīū':
            out[-1] += 'ti'
        elif len(w) > 1 and w != 'pts':
            out.append(w)
    return out


def rule_stem(w):
    for e in ENDINGS:
        if w.endswith(e) and len(w) - len(e) >= 3:
            w = w[:-len(e)]
            break
    w = re.sub(r'([kgcjṭḍtdpb])\1h', r'\1h', w)      # kkh -> kh
    w = re.sub(r'([kgcjtdpbmnyrlvshṭḍṇḷ])\1', r'\1', w)  # kk -> k
    return w


# Pure discourse particles (Jorge, 2026-07-17): semantically empty or
# exclamative, and — crucially — inserted/omitted freely between editions,
# so they break n-grams.  Filtered at STEM level, which also catches the
# forms the deconstructor splits out of fusions (vuccatīti -> vuccati + iti).
PARTICLES = ['kho', 'ca', 'vā', 'va', 'pana', 'hi', 'eva', 'pi', 'api',
             'ha', 'kira', 'nu', 'ce', 'atha', 'iti', 'iva']


class Stemmer:
    """token -> tuple of stems, via DPD (headwords / deconstructor) with
    rule fallback.  Batched lookups, memoized."""

    def __init__(self):
        self.db = sqlite3.connect(DPD, uri=True)
        self.map = {}
        self.stats = {'hw': 0, 'dec': 0, 'rule': 0}
        # authoritative sandhi resolutions for the DPD-unknown fusions,
        # built once by build_sandhi.py (rules + Helmer-Smith LLM) — a
        # form here maps straight to its component stem tuple.
        sf = REPO / 'sandhi-resolved.json'
        self.sandhi = ({k: tuple(v) for k, v in
                        json.loads(sf.read_text()).items()} if sf.exists()
                       else {})
        self.prime(set(PARTICLES))
        self.pstems = set()
        for w in PARTICLES:
            self.pstems.update(self.stems(w))

    def prime(self, vocab):
        """Resolve a vocabulary set (two query rounds for compound parts)."""
        pending = [w for w in vocab if w not in self.map]
        for _round in range(2):
            if not pending:
                break
            rows = {}
            todo = list(pending)
            for i in range(0, len(todo), 900):
                chunk = todo[i:i + 900]
                q = ','.join('?' * len(chunk))
                rows.update({k: (h, d) for k, h, d in self.db.execute(
                    f'SELECT lookup_key, headwords, deconstructor '
                    f'FROM lookup WHERE lookup_key IN ({q})', chunk)})
            nxt = []
            for w in pending:
                h, d = rows.get(w, ('', ''))
                if h and h != '[]':
                    self.map[w] = (f'#{min(json.loads(h))}',)
                    self.stats['hw'] += 1
                elif d and d != '[]':
                    parts = [p.strip() for p in
                             json.loads(d)[0].split(' + ') if p.strip()]
                    self.map[w] = ('DEC', tuple(parts))
                    self.stats['dec'] += 1
                    nxt.extend(p for p in parts if p not in self.map)
                else:
                    self.map[w] = (rule_stem(w),)
                    self.stats['rule'] += 1
            pending = list(set(nxt))

    def stems(self, w):
        sr = self.sandhi.get(w)
        if sr is not None:
            return sr
        v = self.map.get(w) or (rule_stem(w),)
        if v[0] != 'DEC':
            return v
        out = []
        for p in v[1]:
            pv = self.map.get(p) or (rule_stem(p),)
            out.extend(pv if pv[0] != 'DEC' else (rule_stem(p),))
        return tuple(out)


def stem_seq(text, st):
    out = []
    for w in tokens(text):
        out.extend(s for s in st.stems(w) if s not in st.pstems)
    return out


def trigrams(seq):
    return [tuple(seq[i:i + 3]) for i in range(len(seq) - 2)]


def ngram_set(seq, n):
    return set(tuple(seq[i:i + n]) for i in range(len(seq) - n + 1))


# Score is a blend of stem n-grams at three granularities: unigrams give
# recall (a real match reaches ~0.87, close to the ~0.90 token-overlap
# ceiling), trigrams give discrimination against near-duplicate peyyāla
# twins.  Weighted toward unigrams to raise the absolute score, keeping a
# trigram term so twins do not tie.  (Diagnostic 2026-07-17: trigram-only
# scored a real match at 0.72; this blend, ~0.83.)
BLEND = ((1, 0.45), (2, 0.30), (3, 0.25))


def featurize(s):
    """Attach the n-gram sets used by the blended score to a segment dict
    that already has s['seq'] (the stem sequence)."""
    for n, _ in BLEND:
        s[f'g{n}'] = ngram_set(s['seq'], n)
    return s


def build_idf(pool):
    idf = {}
    for n, _ in BLEND:
        df = {}
        for s in pool:
            for g in s[f'g{n}']:
                df[g] = df.get(g, 0) + 1
        N = len(pool)
        idf[n] = {g: math.log(N / c) for g, c in df.items()}
    return idf


def blended_contain(a, b, idf):
    """Asymmetric idf-weighted containment, blended over granularities and
    over-weighting the theme (a stem repeated inside a is its topic)."""
    total = 0.0
    for n, wt in BLEND:
        A, B = a[f'g{n}'], b[f'g{n}']
        cnt = a.get(f'c{n}')
        if cnt is None:
            from collections import Counter
            cnt = a[f'c{n}'] = Counter(
                tuple(a['seq'][i:i + n]) for i in range(len(a['seq']) - n + 1))
        w = lambda g: idf[n].get(g, 0.0) * (1 + math.log(cnt[g]))
        wa = sum(w(g) for g in A)
        total += wt * (sum(w(g) for g in A & B) / max(wa, 1e-9))
    return total


def spearman(xs, ys):
    n = len(xs)
    if n < 3:
        return 1.0
    rx = {v: r for r, v in enumerate(sorted(xs))}
    ry = {v: r for r, v in enumerate(sorted(ys))}
    d2 = sum((rx[a] - ry[b]) ** 2 for a, b in zip(xs, ys))
    return 1 - 6 * d2 / (n * (n * n - 1))


def load_se(volfile):
    lines = (REPO / 'Canonical' / volfile).read_text(
        encoding='utf-8-sig').split('\n')
    rows = [r for r in csv.DictReader(
        open(REPO / 'sutta-index.csv', encoding='utf-8-sig'))
        if r['file'] == volfile and r['type'] == 'sutta']
    segs = []
    for r in rows:
        seg = lines[int(r['start_line']) - 1:int(r['end_line'])]
        body = ' '.join(l for l in seg if not l.startswith(
            ('footnote:', 'page number:')))
        segs.append(dict(title=r['title'],
                         pages=(int(r['start_page']), int(r['end_page'])),
                         text=body))
    return segs


def load_cha(xmlfiles, level):
    segs = []
    for xmlfile in xmlfiles:
        x = (DPR / xmlfile).read_text()
        parts = re.split(rf'<{level}>([^<]*)</{level}>', x)
        for i in range(1, len(parts), 2):
            raw = parts[i + 1]
            pairs_a = [(int(d), int(p)) for d, p in ANCHOR_T.findall(raw)]
            anchors = [p for _, p in pairs_a]
            by_digit = {}
            for d, p in pairs_a:
                by_digit.setdefault(d, []).append(p)
            segs.append(dict(title=parts[i].strip(), src=xmlfile,
                             anchors=(min(anchors), max(anchors)) if anchors
                             else None,
                             anchors_by_digit={d: (min(v), max(v))
                                               for d, v in by_digit.items()},
                             text=DPR_NOISE.sub(' ', raw)))
    return segs


def norm_title(t):
    t = t.lower().replace('ṃ', 'ṁ')
    return re.sub(r'[^a-zāīūṁṅñṭḍṇḷ]', '', t)


def run_pair(name, st):
    xmlfile, level, volfile = PAIRS[name]
    se, cha = load_se(volfile), load_cha(xmlfile, level)
    for s in se + cha:
        st.prime(set(tokens(s['text'])))
    pool = se + cha
    for s in pool:
        s['seq'] = stem_seq(s['text'], st)
        s['tg'] = trigrams(s['seq'])
        s['set'] = set(s['tg'])
        featurize(s)
    idf = build_idf(pool)
    idf3 = idf[3]

    def contain(a, b):
        return blended_contain(a, b, idf)

    def order_score(a, b):
        shared = sorted(a['set'] & b['set'], key=lambda g: -idf3.get(g, 0))[:60]
        if not shared:
            return 0.0
        pa = {g: i for i, g in reversed(list(enumerate(a['tg'])))}
        pb = {g: i for i, g in reversed(list(enumerate(b['tg'])))}
        xs = [pa[g] for g in shared]
        ys = [pb[g] for g in shared]
        return spearman(xs, ys)

    # score matrix + MONOTONIC alignment (both editions preserve sutta
    # order — Jorge's "orden progresivo" at collection level): dynamic
    # programming maximizes total score with skips allowed, so exact-tie
    # twins in peyyāla series are resolved by their position.
    n, m = len(se), len(cha)
    S = [[contain(a, b) for b in cha] for a in se]
    THR = 0.12
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

    ok = bad = untestable = unmatched = 0
    margins, ratios = [], []
    failures = []
    for ia, a in enumerate(se):
        if ia not in pairs:
            unmatched += 1
            continue
        jb = pairs[ia]
        b = cha[jb]
        s1 = S[ia][jb]
        s2 = max((S[ia][k] for k in range(m) if k != jb), default=0.0)
        margins.append(s1 - s2)
        ratios.append(len(b['seq']) / max(len(a['seq']), 1))
        # validation: T anchors are authoritative (titles legitimately
        # differ across editions: mālukya/māluṅkyovāda, bākula/bakkula…);
        # fall back to title comparison when no anchors exist.
        good = None
        if b['anchors']:
            lo, hi = b['anchors']
            good = not (hi < a['pages'][0] or lo > a['pages'][1])
        elif a['title'] and b['title']:
            ta, tb = norm_title(a['title']), norm_title(b['title'])
            import difflib
            good = ta in tb or tb.endswith(ta) or \
                difflib.SequenceMatcher(None, ta, tb).ratio() >= 0.66
        if good is None:
            untestable += 1
        elif good:
            ok += 1
        else:
            bad += 1
            failures.append((a['title'] or f"(Se) p.{a['pages'][0]}",
                             b['title'], s1, s2, order_score(a, b)))
    med = sorted(margins)[len(margins) // 2] if margins else 0
    medr = sorted(ratios)[len(ratios) // 2] if ratios else 0
    print(f'{name}: Se {len(se)} vs Cha {len(cha)} | alineados correctos '
          f'{ok}/{ok + bad} (sin ancla/título: {untestable}, '
          f'sin pareja: {unmatched}) | margen mediano {med:.3f} | '
          f'ratio palabras mediano {medr:.2f}')
    for f in failures[:8]:
        print(f'   FALLO: {f[0]!r} -> {f[1]!r}  s1={f[2]:.3f} s2={f[3]:.3f} '
              f'orden={f[4]:.2f}')
    return ok, bad, untestable


# ── verse mode (Thera-/Therīgāthā): structural pairing + metrical print ──────
# Jorge's insight (2026-07-17): both editions number the poems identically
# inside each vagga (constant delta, here 0), so pairing is structural; and
# the surest identity check for a gāthā is its METRE — the laghu/garu
# (light/heavy) syllable-weight sequence survives orthographic variation
# that breaks n-grams, because transmission preserved the metre even where
# the wording drifted.

VOWELS = 'aāiīuūeo'


def metric_weights(text):
    """Syllable-weight string ('L'/'H') of romanized Pali: heavy if long
    vowel, or nasalized (ṃ), or followed by 2+ consonants (aspirate
    digraphs count as ONE consonant)."""
    s = re.sub(r'[^a-zāīūṃṅñṭḍṇḷ]', '',
               text.lower().replace('ṁ', 'ṃ'))
    units = []
    i = 0
    while i < len(s):
        c = s[i]
        if c in VOWELS:
            units.append(('V', c)); i += 1
        elif c == 'ṃ':
            units.append(('M', c)); i += 1
        else:
            if i + 1 < len(s) and s[i + 1] == 'h' and c in 'kgcjtdpbṭḍ':
                units.append(('C', c + 'h')); i += 2
            else:
                units.append(('C', c)); i += 1
    out = []
    for idx, (t, c) in enumerate(units):
        if t != 'V':
            continue
        j = idx + 1
        ncons = 0
        nasal = False
        while j < len(units) and units[j][0] != 'V':
            if units[j][0] == 'M':
                nasal = True
            else:
                ncons += 1
            j += 1
        out.append('H' if (c in 'āīūeo' or nasal or ncons >= 2) else 'L')
    return ''.join(out)


def parse_verses(xmlfile):
    """Ordered poems of k8m/k9m.  The heading nesting is irregular (higher
    nipātas skip the h3n vagga level, Thīg leaves it empty), so we walk the
    h2n/h3n/h4n tags in DOCUMENT order — the canonical poem order, shared
    by both editions — and cut a poem at every numbered h4n, tracking the
    enclosing nipāta (h2n) and vagga (h3n) for reporting only."""
    x = (DPR / xmlfile).read_text()
    poems = []
    nipata = vagga = 0
    cur = None
    for m in re.finditer(r'<(h2n|h3n|h4n)>([^<]*)</\1>(.*?)(?=<h[234]n>|$)',
                         x, re.S):
        tag, title, bodytail = m.group(1), m.group(2).strip(), m.group(3)
        if tag == 'h2n':
            nipata += 1; vagga = 0
        elif tag == 'h3n':
            if title:
                vagga += 1
        else:  # h4n
            nm = re.match(r'(\d+)\.\s*(.*)', title)
            if not nm:
                continue
            body = DPR_NOISE.sub(' ', bodytail)
            # the last poem of a vagga is followed by its uddāna (mnemonic
            # index) before the next heading; cut it so it never enters the
            # poem's verse text or metrical fingerprint
            body = re.split(r'\b(?:tassuddāna|uddāna)', body)[0]
            cur = dict(nipata=nipata, vagga=vagga, num=int(nm.group(1)),
                       title=title, src=xmlfile, text=body)
            poems.append(cur)
    return poems


def verse_mode():
    """Pair Se Thag/Thīg rows with k8m/k9m poems structurally, verify by
    metrical fingerprint, and rewrite those rows in the projected CSV."""
    import difflib
    vol_lines = {}

    def se_row_text(r):
        f = r['file']
        if f not in vol_lines:
            vol_lines[f] = (REPO / 'Canonical' / f).read_text(
                encoding='utf-8-sig').split('\n')
        seg = vol_lines[f][int(r['start_line']) - 1:int(r['end_line'])]
        return ' '.join(l for l in seg if not l.startswith(
            ('footnote:', 'page number:')))

    allrows = list(csv.DictReader(
        open(REPO / 'sutta-index.csv', encoding='utf-8-sig')))
    out_rows = []
    for xmlfile, prefix in (('k8m.xml', 'Thag'), ('k9m.xml', 'Thīg')):
        se = [r for r in allrows if r['file'] == '26-Vv-Pv-Th-Thi.txt'
              and r['title'].startswith(prefix + ' ')]
        cha = parse_verses(xmlfile)
        n = min(len(se), len(cha))
        print(f'{xmlfile} ↔ {prefix}: Se {len(se)} vs Cha {len(cha)} poemas'
              f'{"  ⚠ conteos distintos" if len(se) != len(cha) else ""}')
        if n == 0:
            continue
        sims = []
        numok = 0
        for a, b in zip(se[:n], cha[:n]):
            wa = metric_weights(se_row_text(a))
            wb = metric_weights(b['text'])
            # autojunk=False is essential: on a 2-symbol (L/H) alphabet the
            # default heuristic junks BOTH symbols and returns ~0.
            sim = difflib.SequenceMatcher(None, wa, wb,
                                          autojunk=False).ratio()
            sims.append(sim)
            if int(a['title'].split()[-1]) == b['num']:
                numok += 1
            out_rows.append({
                'work': a['work'], 'se_start': a['se_start'],
                'se_end': a['se_end'], 'title_cha': b['title'],
                'file': a['file'], 'start_page': a['start_page'],
                'start_line': a['start_line'], 'end_page': a['end_page'],
                'end_line': a['end_line'],
                'confidence': f'{sim:.2f}', 'source': xmlfile})
        sims.sort()
        print(f'  números iguales (delta 0): {numok}/{n} | '
              f'similitud métrica mediana {sims[n // 2]:.3f}, '
              f'p10 {sims[n // 10]:.3f}, <0.75: {sum(1 for s in sims if s < 0.75)}')
    # rewrite the k8m/k9m rows of the projected CSV
    path = REPO / 'sutta-index-projected.csv'
    keep = [r for r in csv.DictReader(open(path, encoding='utf-8-sig'))
            if r['source'] not in ('k8m.xml', 'k9m.xml')]
    fields = list(keep[0].keys())
    allout = keep + out_rows
    allout.sort(key=lambda r: (r['file'], int(r['start_line'])))
    with open(path, 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(allout)
    print(f'-> {path}: filas k8m/k9m sustituidas por emparejamiento '
          f'estructural+métrico ({len(out_rows)})')


def load_se_volume(volfile, st):
    """Whole Se volume as one stem stream with per-stem (page, line)."""
    lines = (REPO / 'Canonical' / volfile).read_text(
        encoding='utf-8-sig').split('\n')
    page = 0
    toks, origins = [], []
    for ln, raw in enumerate(lines, 1):
        m = re.match(r'^page number: (\d{3})$', raw)
        if m:
            page = int(m.group(1))
            continue
        if raw.startswith('footnote:') or not raw.strip():
            continue
        for w in tokens(raw):
            toks.append(w)
            origins.append((page, ln))
    st.prime(set(toks))
    stems, pos = [], []
    for w, o in zip(toks, origins):
        for s in st.stems(w):
            stems.append(s)
            pos.append(o)
    return stems, pos


def project_pair(name, st, writer):
    xmlfiles, level, volfile = PAIRS[name]
    return project_group(name, load_cha(xmlfiles, level), volfile, st, writer)


def project_group(name, cha, volfile, st, writer):
    """Project every Burmese sutta boundary onto the Se volume: seed the
    segment's first distinctive stem trigrams inside the window given by
    its Thai page anchors, take the median consistent hit as the start."""
    for s in cha:
        s['cst_work'] = ''  # set by caller; populated below
        st.prime(set(tokens(s['text'])))
    # Determine cst_work from the projection name
    cst = PAIR_TO_CST.get(name, '')
    if not cst:
        xmlfile = name.split('/')[0] + '.xml'
        cst = SOURCE_TO_CST.get(xmlfile, '')
    stems, pos = load_se_volume(volfile, st)
    vol = int(volfile.split('-')[0])
    sig, tome = VOLSIG[vol]
    quad_pos = {}
    for i in range(len(stems) - 3):
        quad_pos.setdefault(tuple(stems[i:i + 4]), []).append(i)
    page_first = {}
    for i, (p, _) in enumerate(pos):
        page_first.setdefault(p, i)
    maxpage = pos[-1][0]

    results = []
    prev_idx = 0
    for s in cha:
        seq = stem_seq(s['text'], st)
        qg = [tuple(seq[i:i + 4]) for i in range(len(seq) - 3)]
        if s['anchors']:
            lo_p, hi_p = s['anchors']
            lo0 = page_first.get(max(1, lo_p - 1), 0)
            hi = page_first.get(min(maxpage, hi_p + 2), len(stems) - 1)
        else:
            lo0 = prev_idx
            hi = min(prev_idx + 20000, len(stems) - 1)
        lo = max(lo0, prev_idx - 200)
        if lo > hi:      # a runaway prev_idx must not override the anchors
            lo = lo0
        # candidate starts: every in-window occurrence of the segment's
        # leading 4-grams, shifted by their offset; densest cluster wins
        # (repetitive peyyāla text has no unique n-grams, but the true
        # position accumulates hits from every seed).
        cand = []
        for k, g in enumerate(qg[:200]):
            occ = [p for p in quad_pos.get(g, ()) if lo <= p <= hi]
            if len(occ) <= 6:
                cand.extend(p - k for p in occ)
            if len(cand) >= 60:
                break
        if not cand:
            # repetitive series: nothing is rare — walk monotonically and
            # take each seed's first occurrence after the previous sutta
            for k, g in enumerate(qg[:200]):
                occ = [p for p in quad_pos.get(g, ())
                       if prev_idx <= p <= hi]
                if occ:
                    cand.append(occ[0] - k)
                if len(cand) >= 30:
                    break
        if cand:
            cand.sort()
            best_n, best_slice = 0, None
            j = 0
            for i in range(len(cand)):
                while cand[i] - cand[j] > 40:
                    j += 1
                if i - j + 1 > best_n:
                    best_n, best_slice = i - j + 1, (j, i)
            cluster = cand[best_slice[0]:best_slice[1] + 1]
            start = cluster[len(cluster) // 2]
            agree = best_n / len(cand)
        else:
            start, agree = None, 0.0
        results.append(dict(seg=s, start=start, conf=agree, n=len(seq)))
        # only a confident projection may advance the monotonic frontier —
        # a garbage start would poison every later window
        if start is not None and agree >= 0.3:
            prev_idx = max(prev_idx, start)

    # monotonic cleanup: keep the confidence-weighted longest increasing
    # subsequence of starts and demote everything off it — robust against
    # both backward- and forward-jumping outliers (a greedy frontier lets
    # one bad jump poison every later segment).
    live = [(i, r['start'], r['conf'])
            for i, r in enumerate(results) if r['start'] is not None]
    if live:
        n = len(live)
        dp = [c for _, _, c in live]
        par = [-1] * n
        for a in range(n):
            for b in range(a):
                if live[a][1] >= live[b][1] - 60 and dp[b] + live[a][2] > dp[a]:
                    dp[a], par[a] = dp[b] + live[a][2], b
        k = max(range(n), key=dp.__getitem__)
        keep = set()
        while k != -1:
            keep.add(live[k][0])
            k = par[k]
        for i, r in enumerate(results):
            if r['start'] is not None and i not in keep:
                r['start'], r['conf'] = None, 0.0

    # interpolation: a segment whose content Se abbreviates away (peyyāla
    # compressed to one line) gets a start interpolated between its known
    # neighbours, proportional to Burmese token mass; confidence 0.05.
    known = [i for i, r in enumerate(results) if r['start'] is not None]
    for a, b in zip(known, known[1:]):
        if b - a < 2:
            continue
        total = sum(results[k]['n'] for k in range(a, b))
        cum = results[a]['n']
        span = results[b]['start'] - results[a]['start']
        for k in range(a + 1, b):
            results[k]['start'] = results[a]['start'] + int(
                span * cum / max(total, 1))
            results[k]['conf'] = 0.05
            cum += results[k]['n']

    # ends: next segment's start - 1 (monotonic); fill missing starts.
    # GUARD: ensure end_page < next_start_page — Burmese anchors sit at the
    # colophon (end of previous segment), so stem matching often places nxt
    # on the same page as nxt-1.  We walk end_idx backward until its page
    # no longer collides with the next start's page.
    n_ok = 0
    starts = [r['start'] for r in results]
    for i, r in enumerate(results):
        if r['start'] is None:
            continue
        nxt = next((s for s in starts[i + 1:] if s is not None), len(stems))
        end_idx = max(r['start'], nxt - 1)
        sp, sl = pos[min(r['start'], len(pos) - 1)]
        ep, el = pos[min(end_idx, len(pos) - 1)]
        # If end page collides with the next segment's start page, pull
        # end_idx back to the last stem on a different (earlier) page.
        if nxt < len(stems):
            nxt_pg = pos[nxt][0]
            while end_idx > r['start'] and ep >= nxt_pg:
                end_idx -= 1
                ep, el = pos[min(end_idx, len(pos) - 1)]
        n_ok += 1
        writer.writerow({
            'work': f'{sig} {tome}', 'se_start': f'(Se) {sig} {tome} {sp}',
            'se_end': f'(Se) {sig} {tome} {ep}',
            'title_cha': r['seg']['title'], 'file': volfile,
            'start_page': sp, 'start_line': sl,
            'end_page': ep, 'end_line': el,
            'confidence': f"{r['conf']:.2f}", 'source': r['seg']['src'],
            'cst_work': cst})
    lost = len(results) - n_ok
    med = sorted(r['conf'] for r in results if r['start'] is not None)
    med = med[len(med) // 2] if med else 0
    print(f'{name}: {n_ok}/{len(results)} suttas Cha proyectados sobre '
          f'{volfile} (sin semilla: {lost}) | confianza mediana {med:.2f}')
    return results


def run_projection(names):
    st = Stemmer()
    out = REPO / 'sutta-index-projected.csv'
    with open(out, 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.DictWriter(fh, fieldnames=[
            'work', 'se_start', 'se_end', 'title_cha', 'file',
            'start_page', 'start_line', 'end_page', 'end_line',
            'confidence', 'source', 'cst_work'])
        w.writeheader()
        for n in names:
            project_pair(n, st, w)
        for xmlfile, level, dmap in VK_FILES:
            segs = load_cha([xmlfile], level)
            cur = min(dmap)
            groups = {}
            for s in segs:
                digs = [d for d in s['anchors_by_digit'] if d in dmap]
                if digs:
                    cur = max(digs) if len(digs) > 1 else digs[0]
                if cur in s['anchors_by_digit']:
                    s['anchors'] = s['anchors_by_digit'][cur]
                else:
                    s['anchors'] = None
                groups.setdefault(cur, []).append(s)
            for d in sorted(groups):
                project_group(f'{xmlfile[:-4]}/T{d}', groups[d],
                              dmap[d], st, w)
    print(f'\n-> {out}')


def main():
    names = sys.argv[1:] or ['d1']
    if names == ['project']:
        run_projection(PROJECT)
        return 0
    if names == ['verses']:
        verse_mode()
        return 0
    if names == ['all']:
        names = ['d1', 'd2', 'd3', 'm1', 'm2', 'm3', 's1', 's2']
    st = Stemmer()
    tot_ok = tot_bad = 0
    for n in names:
        ok, bad, _ = run_pair(n, st)
        tot_ok += ok; tot_bad += bad
    print(f'\nTOTAL top-1 correcto: {tot_ok}/{tot_ok + tot_bad}  |  '
          f'stemmer: {st.stats}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

# CST work abbreviations -----------------------------------------------
PAIR_TO_CST = {p: 'SN' for p in ['s3', 's4', 's5']}
PAIR_TO_CST.update({p: 'AN' for p in ['a20', 'a21', 'a22', 'a23', 'a24']})

SOURCE_TO_CST = {
    'v1m.xml': 'Vin', 'v2m.xml': 'Vin', 'v3m.xml': 'Vin',
    'v4m.xml': 'Vin', 'v5m.xml': 'Vin', 'v6m.xml': 'Vin',
    'k1m.xml': 'Khp', 'k2m.xml': 'Dhp', 'k3m.xml': 'Ud',
    'k4m.xml': 'Iti', 'k5m.xml': 'Snp',
    'k6m.xml': 'Vv', 'k7m.xml': 'Pv', 'k8m.xml': 'Thag', 'k9m.xml': 'Thīg',
    'k10m.xml': 'Ap', 'k13m.xml': 'Ap', 'k11m.xml': 'Bv', 'k12m.xml': 'Cp',
    'k14m.xml': 'Ja', 'k15m.xml': 'Ja',
    'k16m.xml': 'Nidd I', 'k17m.xml': 'Nidd II', 'k18m.xml': 'Ps',
}
