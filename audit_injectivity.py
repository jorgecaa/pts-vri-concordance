#!/usr/bin/env python3
"""
audit_injectivity — prueba de aceptación estructural de un volumen: ¿cada fila tiene SU marcador?

**Por qué existe.** La resolución del lado PTS se hacía fila a fila, de modo que dos filas podían
acabar en el mismo marcador y una de ellas quedaba validada contra el locus de su vecino. El
validador no puede detectarlo — compara un par PTS↔CST correcto *entre sí* pero ajeno a la fila —
y por eso el error atravesó todos los controles. Es la misma familia que los 21 `Sutta #`
desplazados de S ii: **sin una comprobación estructural, un APPROVE no dice nada sobre la fila.**

**Qué mide.** Para cada marcador, cuántas filas se le asignan frente a su **capacidad**: un marcador
de rango (`140-142 (5-7) Dukkhena`) cubre legítimamente tantas filas como suttas abarca; uno
individual, una sola. El **hueco de inyectividad** es la suma de los excesos.

    hueco = Σ_marcador max(0, filas_asignadas − capacidad)

**Criterio de cierre de un volumen: hueco = 0.** Correr antes y después de cada cambio en un
resolvedor.

Uso:
    python3 audit_injectivity.py            # todos los volúmenes de SN
    python3 audit_injectivity.py iii v      # solo los indicados
"""
import collections
import sqlite3
import sys

DB = 'src/data/tipitaka.sqlite'


def audit(assignment, capacity):
    """`assignment`: {fila → clave de marcador}; `capacity`: {clave → nº de suttas que cubre}.

    Devuelve `(hueco, compartidos)` donde `compartidos` son las claves con más filas que capacidad.
    """
    used = collections.defaultdict(list)
    for row, key in assignment.items():
        if key is not None:
            used[key].append(row)
    gap, shared = 0, {}
    for key, rows in used.items():
        cap = capacity.get(key, 1)
        if len(rows) > cap:
            gap += len(rows) - cap
            shared[key] = (sorted(rows), cap)
    return gap, shared


# ── adaptadores por volumen: (filas asignadas, capacidad, nº de marcadores disponibles) ──────
def _capacity(pts, key_of):
    """Capacidad de cada marcador = nº de suttas que comparten su (página, línea)."""
    cap = collections.Counter()
    for s in (pts.values() if isinstance(pts, dict) else pts):
        cap[key_of(s)] += 1
    return cap


def volume_i():
    from validador_sn1 import build_pts_suttas, excel_entries
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
    pts, _m = build_pts_suttas(conn.cursor())
    entries = excel_entries()
    key = lambda s: (s['page'], s['line'])
    cap = _capacity(pts, key)
    return {e['num']: key(pts[i]) for i, e in enumerate(entries) if i < len(pts)}, cap, len(cap)


def volume_ii():
    from validador_sn2 import build_pts_suttas, excel_entries, FEER
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
    pts = build_pts_suttas(conn.cursor())
    sams = {f[0] for f in FEER}
    key = lambda s: (s['sam'], s['page'], s['line'])
    cap = _capacity(pts, key)
    out = {}
    for e in excel_entries():
        if e['sam'] not in sams:
            continue
        q = pts.get((e['sam'], e['inner']))
        out[e['num']] = key(q) if q else None
    return out, cap, len(cap)


def volume_iii():
    from validador_sn3 import (build_pts_suttas, pts_records, build_massive, excel_entries,
                               calibrate_offsets, ditthi_pairs, assign_volume)
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
    pts = build_pts_suttas(conn.cursor()); mv = build_massive()
    off = calibrate_offsets(pts, mv, {k: v[1] for k, v in mv.items()})
    dit = ditthi_pairs(pts)
    key = lambda s: (s['sam'], s['page'], s['line'])
    cap = _capacity(pts_records(pts), key)
    entries = excel_entries()
    assigned = assign_volume(entries, pts, mv, off, dit)      # el MISMO camino que el driver
    return ({e['num']: (key(assigned[e['num']]) if assigned.get(e['num']) else None)
             for e in entries}, cap, len(cap))


def volume_v():
    """S v usa ahora la asignación global de `validador_sn5_vri.assign_volume`."""
    from validador_sn5_vri import build_vri_index, build_massive, excel_entries, assign_volume
    from validador_sn5 import build_markers
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    mm = build_markers(cur); vri = build_vri_index(); c2p = build_massive()
    cap = collections.Counter()
    for pg, items in mm.items():
        for line, _gid, _vpos, _nm in items:
            cap[(pg, line)] += 1
    return assign_volume(excel_entries(), cur, mm, c2p, vri), cap, len(cap)


VOLUMES = {'i': volume_i, 'ii': volume_ii, 'iii': volume_iii, 'v': volume_v}


def main():
    want = [a for a in sys.argv[1:] if a in VOLUMES] or list(VOLUMES)
    print('=' * 88)
    print('AUDITORÍA DE INYECTIVIDAD — ¿cada fila tiene su propio marcador PTS?')
    print('=' * 88)
    total = 0
    for v in want:
        assignment, cap, nmark = VOLUMES[v]()
        gap, shared = audit(assignment, cap)
        total += gap
        sin = sum(1 for k in assignment.values() if k is None)
        print(f'\nS {v:<4} filas {len(assignment):4} | marcadores {nmark:4} | sin resolver {sin:3} '
              f'| HUECO {gap}  {"OK" if gap == 0 else "<<<"}')
        for key, (rows, c) in sorted(shared.items())[:14]:
            print(f'      {key} capacidad {c} ← {len(rows)} filas: {", ".join(map(str, rows))}')
    print(f'\nHUECO TOTAL: {total}   {"(criterio de cierre satisfecho)" if total == 0 else ""}')
    return 0 if total == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
