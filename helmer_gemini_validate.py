#!/usr/bin/env python3
"""Validación DN/MN completa con gemini-flash-lite-latest vs caché DeepSeek.

Mide concordancia con la referencia (caché DeepSeek) y marca discrepancias,
en especial Gemini=APPROVE / DeepSeek=REJECT (presuntos falsos-rechazos de DS).
No escribe el caché DeepSeek ni el Excel; vuelca resultados a JSON aparte.
"""
import hashlib, json, sys, time
from collections import Counter
from google import genai
from google.genai import types
import helmer_ptscst as H, sutta_hash as sh
from helmer_ptscst import SYS

MODEL = 'gemini-flash-lite-latest'
OUT = 'helmer_gemini_dnmn.json'
SCHEMA = {'type': 'OBJECT', 'properties': {
    'verdict': {'type': 'STRING', 'enum': ['APPROVE', 'REJECT']},
    'reason': {'type': 'STRING'}}, 'required': ['verdict', 'reason']}


def user_text(pts, cst):
    vs = H.classify(H.collate(pts, cst))
    b = ['PTS:', pts[:1200], '', 'CST:', cst[:1200], '', 'CollateX (PTS|CST|DPD):']
    for sa, sb, tg in vs:
        b.append(f'  "{sa}" | "{sb}" | {tg}')
    return '\n'.join(b)


def ask(cli, text, tries=4):
    for i in range(tries):
        try:
            r = cli.models.generate_content(model=MODEL, contents=text,
                config=types.GenerateContentConfig(system_instruction=SYS, temperature=0,
                    response_mime_type='application/json', response_schema=SCHEMA))
            o = json.loads(r.text)
            return o.get('verdict'), o.get('reason'), r.usage_metadata.prompt_token_count, r.usage_metadata.candidates_token_count
        except Exception as e:
            if i == tries - 1:
                return 'ERROR', str(e)[:80], 0, 0
            time.sleep(2 ** i)


def main():
    cache = json.loads(H.CACHE_FILE.read_text())
    cli = genai.Client()
    tests = H.select(200)
    cst_cache = {}
    for t in tests:
        xf, lv, i = H.cst_for_dnm(t['nik'], t['num'])
        if xf and tuple(xf) not in cst_cache:
            cst_cache[tuple(xf)] = sh.load_cha(list(xf), lv)

    rows = []
    tin = tout = 0
    for k, t in enumerate(tests, 1):
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
        key = hashlib.md5((pts[:300] + cst[:300]).encode()).hexdigest()
        ds = cache.get(key)
        dsv = ds.get('verdict') if ds else None

        gv, gr, pin, pout = ask(cli, user_text(pts, cst))
        tin += pin; tout += pout
        rows.append({'nik': t['nik'], 'num': t['num'], 'ref': t['ref'], 'name': t['name'],
                     'cst_title': ct, 'gemini': gv, 'reason': gr, 'ds': dsv})
        if k % 25 == 0:
            print(f'  ...{k}/{len(tests)}', flush=True)
            json.dump(rows, open(OUT, 'w'), ensure_ascii=False, indent=1)

    json.dump(rows, open(OUT, 'w'), ensure_ascii=False, indent=1)
    report(rows, tin, tout)


def report(rows, tin, tout):
    cov = [r for r in rows if r['ds'] and r['gemini'] in ('APPROVE', 'REJECT')]
    agree = [r for r in cov if r['gemini'] == r['ds']]
    err = [r for r in rows if r['gemini'] == 'ERROR']
    ga_dr = [r for r in cov if r['gemini'] == 'APPROVE' and r['ds'] == 'REJECT']  # DS falso-reject
    gr_da = [r for r in cov if r['gemini'] == 'REJECT' and r['ds'] == 'APPROVE']  # Gemini rechaza

    print('\n' + '=' * 92)
    print(f'GEMINI flash-lite vs caché DeepSeek — DN/MN')
    print('=' * 92)
    print(f'Evaluadas: {len(rows)} | con caché DS: {len(cov)} | errores Gemini: {len(err)}')
    print(f'Concordancia: {len(agree)}/{len(cov)} ({100*len(agree)/max(1,len(cov)):.0f}%)')
    print(f'Tokens: {tin} in / {tout} out  (~{tin/max(1,len(rows)):.0f} in por parada)')

    print(f'\nGemini=APPROVE / DeepSeek=REJECT  (presuntos falsos-rechazos de DS): {len(ga_dr)}')
    for r in ga_dr:
        print(f'  {r["nik"]} {r["num"]:>4} | {r["name"][:22]:22} -> {r["cst_title"][:22]:22} | {r["reason"][:40]}')
    print(f'\nGemini=REJECT / DeepSeek=APPROVE: {len(gr_da)}')
    for r in gr_da:
        print(f'  {r["nik"]} {r["num"]:>4} | {r["name"][:22]:22} -> {r["cst_title"][:22]:22} | {r["reason"][:40]}')
    print(f'\nResultados en {OUT}')


if __name__ == '__main__':
    main()
