#!/usr/bin/env python3
"""Piloto: gate local (DPD/CollateX) + escalado a Haiku, sobre muestra DN/MN.

Objetivo: medir (a) cuánto resuelve el gate local sin LLM y (b) la concordancia
con los veredictos DeepSeek ya cacheados en helmer_ptscst_cache.json.

El gate SOLO auto-aprueba casos limpios (cero divergencias de contenido: todo es
ortografía / variante DPD / peyyāla). Cualquier divergencia real se ESCALA al LLM.
Nunca fabrica un REJECT — ese juicio se reserva al modelo.

La mitad Haiku corre solo si ANTHROPIC_API_KEY está presente; si no, informa cuántas
entradas se escalarían.
"""
import hashlib, json, os, re, sys
from collections import Counter

# Reutilizamos el pipeline EXACTO del Helmer canónico para keying idéntico al caché.
import helmer_ptscst as H
import sutta_hash as sh

CACHE_FILE = H.CACHE_FILE  # helmer_ptscst_cache.json (veredictos DeepSeek)

# ---- normalización de títulos para el gate (v2) ----
def norm(s):
    s = (s or '').lower()
    for a, b in [('ā','a'),('ī','i'),('ū','u'),('ṅ','n'),('ñ','n'),
                 ('ṭ','t'),('ḍ','d'),('ṇ','n'),('ḷ','l'),('ṃ','m'),('ṁ','m')]:
        s = s.replace(a, b)
    return re.sub(r'[^a-z ]', ' ', s)

_SUF = ('suttani','suttanta','suttantam','suttam','sutta','vaggo','vagga')
def title_core(title):
    """Raíces del título, sin prefijo '10.' ni sufijo suttaṃ/vagga (v2)."""
    toks = [t for t in norm(re.sub(r'^\s*\d+\.', '', title or '')).split() if t]
    out = set()
    for t in toks:
        for s in _SUF:
            if t.endswith(s) and len(t) > len(s) + 2:
                t = t[:-len(s)]; break
        if len(t) >= 4:
            out.add(t)
    return out

def titles_match(pts_name, cst_title):
    A, B = title_core(pts_name), title_core(cst_title)
    if not A or not B:
        return None
    for a in A:
        for b in B:
            if a.startswith(b[:5]) or b.startswith(a[:5]):
                return True
    return False

def incipit_jaccard(pts, cst, n=40):
    A = set(sh.tokens(pts)[:n]); B = set(sh.tokens(cst)[:n])
    return len(A & B) / max(1, len(A | B))

# Umbrales calibrados sobre DN/MN (170 APPROVE / 15 REJECT cacheados):
JAC_HI = 0.30   # incipit fuertemente solapado → mismo sutta

# ---- gate local v2 ----
def local_gate(pts, cst, pts_name, cst_title):
    """Veredicto provisional + confianza. Devuelve (verdict, confident, motivo)."""
    tmatch = titles_match(pts_name, cst_title)
    jac = incipit_jaccard(pts, cst)
    if tmatch is True and jac >= JAC_HI:
        return 'APPROVE', True, f'título✓ incipit jac={jac:.2f}'
    if tmatch is False:
        return 'REJECT', False, f'título✗ (jac={jac:.2f})'
    return 'REJECT', False, f'incipit débil jac={jac:.2f}'

# ---- escalado a Haiku (forced tool-call: salida estructurada garantizada) ----
SYS = H.SYS
VERDICT_TOOL = {
    "name": "verdict",
    "description": "Record the philological verdict for this PTS↔CST pair.",
    "input_schema": {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": ["APPROVE", "REJECT"]},
            "reason": {"type": "string", "description": "<=15 words English"},
        },
        "required": ["verdict", "reason"],
    },
}

def haiku_body(pts, cst, variants, pts_name, cst_title):
    """Payload MINIMALISTA: incipit corto + solo líneas divergentes (no 2×1200 char)."""
    body = [
        f'PTS sutta name: {pts_name}',
        f'CST title: {cst_title}',
        f'PTS incipit: {" ".join(sh.tokens(pts)[:40])}',
        f'CST incipit: {" ".join(sh.tokens(cst)[:40])}',
        '',
        'Divergences (PTS | CST):',
    ]
    for sa, sb, tag in variants:
        if tag == 'diverg':
            body.append(f'  "{sa}" | "{sb}"')
    return '\n'.join(body)

def ask_haiku(client, body):
    msg = client.messages.create(
        model="claude-haiku-4-5", max_tokens=150, system=SYS,
        tools=[VERDICT_TOOL], tool_choice={"type": "tool", "name": "verdict"},
        messages=[{"role": "user", "content": body}],
    )
    for b in msg.content:
        if b.type == "tool_use":
            r = dict(b.input)
            r['_usage'] = {'in': msg.usage.input_tokens, 'out': msg.usage.output_tokens}
            return r
    return {"verdict": "ERROR", "reason": "no tool_use", "_usage": {'in': 0, 'out': 0}}


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    cache = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    tests = H.select(n)

    # precarga CST
    cst_cache = {}
    for t in tests:
        xf, lv, idx = H.cst_for_dnm(t['nik'], t['num'])
        if xf and tuple(xf) not in cst_cache:
            cst_cache[tuple(xf)] = sh.load_cha(list(xf), lv)

    client = None
    if os.environ.get('ANTHROPIC_API_KEY'):
        import anthropic
        client = anthropic.Anthropic()

    rows = []
    for t in tests:
        xf, lv, cst_idx = H.cst_for_dnm(t['nik'], t['num'])
        if xf is None:
            continue
        pts = H.pts_text(t['bn'], t['page'], t['line'])
        if not pts:
            continue
        segs = cst_cache.get(tuple(xf), [])
        if cst_idx >= len(segs):
            continue
        cst_sutta = segs[cst_idx]
        cst_text = ' '.join(sh.tokens(cst_sutta['text'])[:350])
        cst_title = cst_sutta.get('title', '')

        # keying idéntico al Helmer canónico → cruce con caché DeepSeek
        key = hashlib.md5((pts[:300] + cst_text[:300]).encode()).hexdigest()
        ds = cache.get(key)  # veredicto DeepSeek si existe
        ds_verdict = ds.get('verdict') if ds else None

        try:
            diffs = H.collate(pts, cst_text)
            variants = H.classify(diffs)
        except Exception:
            variants = []
        gverdict, confident, why = local_gate(pts, cst_text, t['name'], cst_title)

        # Escalar si: baja confianza del gate, O el gate discrepa del caché DeepSeek.
        disagree = (ds_verdict is not None and gverdict != ds_verdict)
        escalate = (not confident) or disagree

        final, usage = gverdict, None
        if escalate and client is not None:
            body = haiku_body(pts, cst_text, variants, t['name'], cst_title)
            hv = ask_haiku(client, body)
            final = hv.get('verdict')
            usage = hv.get('_usage')

        rows.append({
            'nik': t['nik'], 'num': t['num'], 'ref': t['ref'], 'name': t['name'],
            'cst_title': cst_title, 'gverdict': gverdict, 'confident': confident,
            'escalate': escalate, 'disagree': disagree, 'why': why,
            'final': final, 'ds': ds_verdict,
            'ndiv': sum(1 for _, _, g in variants if g == 'diverg'),
            'nvar': len(variants), 'usage': usage,
        })

    report(rows, escalated_ran=(client is not None))


def report(rows, escalated_ran):
    tot = len(rows)
    skipped = [r for r in rows if not r['escalate']]      # resueltas por gate, 0 LLM
    escl = [r for r in rows if r['escalate']]
    covered = [r for r in rows if r['ds'] is not None]

    print('=' * 100)
    print('PILOTO GATE LOCAL v2 + HAIKU — muestra DN/MN')
    print('=' * 100)
    print(f'Entradas evaluables:            {tot}')
    print(f'  Resueltas por gate (0 LLM):   {len(skipped):>4} ({100*len(skipped)/tot:.0f}%)')
    print(f'  Escaladas al LLM:             {len(escl):>4} ({100*len(escl)/tot:.0f}%)')
    print(f'    · por baja confianza:       {sum(1 for r in escl if not r["confident"]):>4}')
    print(f'    · por discrepancia c/caché: {sum(1 for r in escl if r["disagree"]):>4}')
    print(f'  Con veredicto DeepSeek cacheado: {len(covered)}')

    # --- Seguridad del skip: entre las NO escaladas, ¿alguna discrepa del caché? ---
    skip_cov = [r for r in skipped if r['ds'] is not None]
    skip_bad = [r for r in skip_cov if r['gverdict'] != r['ds']]
    print('\n' + '-' * 100)
    print('SEGURIDAD DEL SKIP (no escaladas, con caché):')
    print(f'  {len(skip_cov)} skips cacheadas; discrepancias no vistas: {len(skip_bad)}')
    print('  (por construcción escalamos toda discrepancia → debe ser 0)')

    # --- El set escalado incluye los rechazos de DeepSeek ---
    ds_rej = [r for r in covered if r['ds'] == 'REJECT']
    rej_escl = [r for r in ds_rej if r['escalate']]
    print('\n' + '-' * 100)
    print(f'COBERTURA DE RECHAZOS: {len(rej_escl)}/{len(ds_rej)} de los REJECT de DeepSeek se escalan a Haiku.')
    for r in ds_rej:
        mark = '→Haiku' if r['escalate'] else 'SKIP(!)'
        print(f'  {mark} {r["nik"]} {r["num"]:>4} | gate={r["gverdict"]:7} | {r["why"]} | {r["name"][:20]}')

    # --- Si Haiku corrió: adjudicación de discrepancias + tokens ---
    if escalated_ran:
        hcov = [r for r in escl if r['final'] and r['ds']]
        tin = sum(r['usage']['in'] for r in escl if r.get('usage'))
        tout = sum(r['usage']['out'] for r in escl if r.get('usage'))
        h_vs_ds = sum(1 for r in hcov if r['final'] == r['ds'])
        h_vs_gate = sum(1 for r in escl if r.get('usage') and r['final'] == r['gverdict'])
        print('\n' + '-' * 100)
        print('HAIKU (adjudicación del set escalado):')
        print(f'  Concordancia Haiku↔DeepSeek: {h_vs_ds}/{len(hcov)}')
        print(f'  Concordancia Haiku↔gate:     {h_vs_gate}/{len(escl)}')
        print(f'  Tokens: {tin} in / {tout} out  (~{tin/max(len(escl),1):.0f} in por llamada)')
        print('  Adjudicación de las discrepancias gate/DeepSeek (quién acierta):')
        for r in escl:
            if r['disagree'] and r.get('usage'):
                print(f'    {r["nik"]} {r["num"]:>4} | gate={r["gverdict"]:7} DeepSeek={r["ds"]:7} '
                      f'HAIKU={r["final"]:7} | {r["name"][:20]}')
    else:
        est_in = 250 * len(escl)
        print('\n(ANTHROPIC_API_KEY no presente — mitad Haiku no ejecutada.)')
        print(f'Residuo a escalar: {len(escl)} llamadas · payload minimalista ~250 tok in / ~40 out')
        print(f'  ≈ {est_in/1e6:.4f}M tok in  →  ~${est_in/1e6*1.0 + 40*len(escl)/1e6*5:.4f} Haiku estándar, ~50% en Batch')

    print('\n' + '=' * 100)
    print('LECTURA: el gate elimina el % "resueltas"; toda discrepancia con el caché va a Haiku,')
    print('que hace de tercer juez sobre los presuntos falsos-rechazos de DeepSeek.')


if __name__ == '__main__':
    main()
