#!/usr/bin/env python3
"""validador.py — Modelo B: gate local ∧ Gemini flash-lite → CONFIRMADO.

Reemplaza el pase DeepSeek "Helmer" (RETIRADO, no fiable a temp=0). Un par PTS↔CST
se marca CONFIRMADO (`Validation=VALIDADOR`) SOLO si el gate local Y
`gemini-flash-lite-latest` coinciden en APPROVE. Desacuerdo → PENDIENTE + cola de
revisión humana (`Validation=REVISAR`). Caso especial: reenvío PTS→Suttanipāta
(sin texto PTS que cotejar) → `PTS_CROSSREF_SN` (CONFIRMADO, sin LLM).

El JUEZ es nikāya-agnóstico: `validate_pair(pts, cst, name, cst_title, nik)`. La
obtención de pares PTS/CST es específica por nikāya (NO HAY HOMOGENEIDAD) — aquí va
el driver DN/MN; SN/AN/KN enganchan sus propios resolvedores CST y llaman al juez.

Uso:
    python3 validador.py --dnmn            # revalida DN/MN (reusa caché Gemini, 0 API)
    python3 validador.py --dnmn --live     # idem pero llamando a Gemini en vivo
    from validador import validate_pair    # integración por nikāya
"""
import json, os, re, sys, time
from collections import Counter

import helmer_ptscst as H
import sutta_hash as sh
from helmer_ptscst import SYS
# gate local reutilizado del piloto (título-núcleo + Jaccard de incipit)
from helmer_haiku_pilot import titles_match, incipit_jaccard

MODEL = 'gemini-flash-lite-latest'
GEMINI_SCHEMA = {'type': 'OBJECT', 'properties': {
    'verdict': {'type': 'STRING', 'enum': ['APPROVE', 'REJECT']},
    'reason': {'type': 'STRING'}}, 'required': ['verdict', 'reason']}

# Umbral de Jaccard de incipit por grupo de nikāya. KN/SN/AN: el título NO basta
# (nombres se repiten, numeración resetea) → exigir más solapamiento de contenido.
JAC_THRESHOLD = {'DN': 0.30, 'MN': 0.30, 'SN': 0.40, 'AN': 0.40, 'KN': 0.40}

# Reenvío PTS→Suttanipāta: PTS no reimprime el sutta (práctica estándar).
_CROSSREF = re.compile(r'not printed here|identical with that of.{0,40}sutta\s*nip', re.I)


def is_crossref(pts_text: str) -> bool:
    return bool(_CROSSREF.search(pts_text or ''))


def gate(pts, cst, name, cst_title, nik):
    """Señal de contenido local. Devuelve ('APPROVE'|'REJECT', detalle)."""
    tm = titles_match(name, cst_title)
    jac = incipit_jaccard(pts, cst)
    thr = JAC_THRESHOLD.get(nik, 0.40)
    ok = (tm is True and jac >= thr)
    return ('APPROVE' if ok else 'REJECT'), {'title': tm, 'jac': round(jac, 2), 'thr': thr}


def _gemini_user(pts, cst):
    vs = H.classify(H.collate(pts, cst))
    b = ['PTS:', pts[:1200], '', 'CST:', cst[:1200], '', 'CollateX (PTS|CST|DPD):']
    for sa, sb, tg in vs:
        b.append(f'  "{sa}" | "{sb}" | {tg}')
    return '\n'.join(b)


_client = None
def _gemini_client():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client()
    return _client


def gemini_judge(pts, cst, tries=4):
    """Juez LLM. Devuelve (verdict, reason, tok_in, tok_out)."""
    from google.genai import types
    cli = _gemini_client()
    for i in range(tries):
        try:
            r = cli.models.generate_content(model=MODEL, contents=_gemini_user(pts, cst),
                config=types.GenerateContentConfig(system_instruction=SYS, temperature=0,
                    response_mime_type='application/json', response_schema=GEMINI_SCHEMA))
            o = json.loads(r.text)
            u = r.usage_metadata
            return o.get('verdict'), o.get('reason'), u.prompt_token_count, u.candidates_token_count
        except Exception as e:
            if i == tries - 1:
                return 'ERROR', str(e)[:80], 0, 0
            time.sleep(2 ** i)


def validate_pair(pts, cst, name, cst_title, nik, gemini_verdict=None, gemini_reason=None):
    """Modelo B. Si se pasa `gemini_verdict` (p.ej. cacheado) no se llama a la API.

    Devuelve dict: estado, validation, gate, gemini, reason.
    """
    if is_crossref(pts):
        return {'estado': 'CONFIRMADO', 'validation': 'PTS_CROSSREF_SN',
                'gate': None, 'gemini': None, 'reason': 'PTS reenvía a Suttanipāta (sin texto que cotejar)'}
    gv, gd = gate(pts, cst, name, cst_title, nik)
    if gemini_verdict is None:
        jv, jr, _in, _out = gemini_judge(pts, cst)
    else:
        jv, jr = gemini_verdict, gemini_reason
    if gv == 'APPROVE' and jv == 'APPROVE':
        return {'estado': 'CONFIRMADO', 'validation': 'VALIDADOR',
                'gate': gd, 'gemini': jv, 'reason': jr}
    return {'estado': 'PENDIENTE', 'validation': 'REVISAR',
            'gate': gd, 'gemini': jv, 'reason': f'desacuerdo (gate={gv} / gemini={jv}): {jr or ""}'}


# ─────────────────────── driver DN/MN (revalidación) ───────────────────────
def run_dnmn(live=False):
    """Revalida DN/MN con el validador. Sin --live reusa los veredictos Gemini de
    helmer_gemini_dnmn.json (0 coste API); con --live llama a Gemini."""
    gcache = {}
    if not live and os.path.exists('helmer_gemini_dnmn.json'):
        for r in json.load(open('helmer_gemini_dnmn.json')):
            gcache[(r['nik'], r['num'])] = (r['gemini'], r.get('reason'))
        print(f'(reusando {len(gcache)} veredictos Gemini cacheados; 0 llamadas API)')

    tests = H.select(200)
    cst_cache = {}
    for t in tests:
        xf, lv, i = H.cst_for_dnm(t['nik'], t['num'])
        if xf and tuple(xf) not in cst_cache:
            cst_cache[tuple(xf)] = sh.load_cha(list(xf), lv)

    rows = []
    for t in tests:
        xf, lv, ci = H.cst_for_dnm(t['nik'], t['num'])
        if xf is None:
            continue
        pts = H.pts_text(t['bn'], t['page'], t['line'])
        if not pts:
            continue
        segs = cst_cache.get(tuple(xf), [])
        if ci >= len(segs):
            continue
        cst = ' '.join(sh.tokens(segs[ci]['text'])[:350])
        ct = segs[ci].get('title', '')
        gv, gr = gcache.get((t['nik'], t['num']), (None, None))
        res = validate_pair(pts, cst, t['name'], ct, t['nik'],
                            gemini_verdict=gv, gemini_reason=gr)
        rows.append({'nik': t['nik'], 'num': t['num'], 'ref': t['ref'], 'name': t['name'],
                     'cst_title': ct, **res})

    json.dump(rows, open('validador_dnmn.json', 'w'), ensure_ascii=False, indent=1)
    _report_dnmn(rows)


def _report_dnmn(rows):
    est = Counter(r['estado'] for r in rows)
    val = Counter(r['validation'] for r in rows)
    revisar = [r for r in rows if r['validation'] == 'REVISAR']
    print('=' * 92)
    print('VALIDADOR (Modelo B) — revalidación DN/MN')
    print('=' * 92)
    print(f'Paradas: {len(rows)}')
    print(f'Estado:  {dict(est)}')
    print(f'Validation: {dict(val)}')
    print(f'\nCola de REVISIÓN HUMANA ({len(revisar)}) — gate y Gemini discrepan:')
    for r in sorted(revisar, key=lambda x: (x['nik'], int(x['num']))):
        g = r['gate']; gj = f"jac={g['jac']} tit={g['title']}" if g else ''
        print(f'  {r["nik"]} {r["num"]:>4} | {r["name"][:22]:22} -> {r["cst_title"][:22]:22} | {gj} | {r["reason"][:44]}')
    print('\nResultados en validador_dnmn.json (nada escrito al Excel).')


if __name__ == '__main__':
    if '--dnmn' in sys.argv:
        run_dnmn(live='--live' in sys.argv)
    else:
        print(__doc__)
