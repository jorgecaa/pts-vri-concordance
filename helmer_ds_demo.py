#!/usr/bin/env python3
"""Integración end-to-end del cliente endurecido sobre datos reales DN/MN.

Muestra el flujo completo guardado por las dos capas de validación, usando el
pipeline real (pts_text / collate / classify). NO escribe caché ni Excel.
"""
import sys
import helmer_ptscst as H
import sutta_hash as sh
from helmer_ds_client import HelmerDSClient, build_payload


def variant_lines(pts, cst):
    diffs = H.collate(pts, cst)
    return [f'"{sa}" | "{sb}" | {tag}' for sa, sb, tag in H.classify(diffs)]


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    tests = H.select(n)
    cli = HelmerDSClient()

    print('=' * 92)
    print(f'INTEGRACIÓN END-TO-END — {n} paradas DN/MN reales (flujo guardado)')
    print('=' * 92)
    tin = tout = 0
    for t in tests:
        xf, lv, ci = H.cst_for_dnm(t['nik'], t['num'])
        pts = H.pts_text(t['bn'], t['page'], t['line'])
        segs = sh.load_cha(list(xf), lv)
        cst = ' '.join(sh.tokens(segs[ci]['text'])[:350])

        payload = build_payload(pts, cst, variant_lines(pts, cst))
        r = cli.call(payload)   # capa1 → red → capa2, todo dentro

        head = f'{t["nik"]} {t["num"]:>4} {t["ref"]:>16}'
        if r.ok:
            tin += r.meta.get('in') or 0
            tout += r.meta.get('out') or 0
            sym = '✓' if r.verdict == 'APPROVE' else '✗'
            print(f'{sym} {head} | {r.verdict:7} | {r.reason[:52]}'
                  f'  [{r.meta.get("in")}→{r.meta.get("out")} tok]')
        else:
            print(f'! {head} | ABORTADO/DESCARTADO en capa "{r.stage}": {"; ".join(r.errors)[:60]}')

    print('-' * 92)
    print(f'Tokens totales: {tin} in / {tout} out  ·  las 2 capas guardan cada llamada.')


if __name__ == '__main__':
    main()
