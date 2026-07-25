#!/usr/bin/env python3
"""
massive_reader — lectura de `massive.tsv` con **expansión de rangos con compuerta**.

`massive.tsv` **no se modifica** (es un insumo del proyecto): esto solo cambia cómo se lee.

**El problema.** Cuando un grupo va como rango, el TSV le pone un único `cst_paranum`, el del primer
miembro:

    SN24.19-35 → cst_paranum 224   («1. Vātasuttaṃ»)
    SN24.36    → cst_paranum 241   = 224 + 17

Asignar 224 a los 17 miembros hace que todos se cotejen contra el sutta 1 del saṃyutta. Fue la causa
de las 13 filas irresolubles de SN 24 (Diṭṭhi) en S iii.

**La compuerta.** Expandir `para + (k − a)` solo si **todos** los paranum resultantes existen en el
índice del XML VRI. Como `build_vri_index` ya expande los `n="225-240"` a las claves 225…240, esa
comprobación equivale a exigir que el destino caiga en párrafos reales — normalmente el **bloque
elidido** del CST (`225-240`, `251-274`, `277-300`), que es justo el homólogo del rango de PTS. Si
algún paranum no existe, se deja el comportamiento colapsado: nunca se inventa una referencia.

Devuelve además, por clave, cómo se resolvió (`'exact'`, `'range+offset'`, `'range-collapsed'`) para
poder auditar qué filas cambian antes de gastar API.
"""
import csv
import re


def build_massive(prefix, vri_index=None, path='massive.tsv', pts_page=None):
    """`(saṃyutta, nº DPR)` → `(cst_paranum, título CST, página PTS, cómo)`.

    `vri_index` es el índice paranum→sutta del XML VRI; sin él no se expande nada (compuerta
    cerrada). `pts_page` es el conversor de `cst_p_page` (ver `validador_sn1._pts_page`).
    """
    out = {}
    for r in csv.DictReader(open(path), delimiter='\t'):
        if not (r['cst_code'] or '').startswith(prefix):
            continue
        pm = re.match(r'(\d+)', r['cst_paranum'] or '')
        m = re.match(r'SN(\d+)\.(\d+)(?:-(\d+))?', r['dpr_code'] or '')
        if not (pm and m):
            continue
        sam, a = int(m.group(1)), int(m.group(2))
        b = int(m.group(3)) if m.group(3) else a
        p0 = int(pm.group(1))
        page = pts_page(r['cst_p_page']) if pts_page else None
        title = r['cst_sutta']

        how = 'exact' if b == a else 'range-collapsed'
        if b > a and vri_index is not None:
            if all((p0 + (k - a)) in vri_index for k in range(a, b + 1)):
                how = 'range+offset'
        for k in range(a, b + 1):
            para = p0 + (k - a) if how == 'range+offset' else p0
            out.setdefault((sam, k), (para, title, page, how))
    return out


def audit(prefix, vri_index, pts_page, path='massive.tsv'):
    """Compara la lectura colapsada con la expandida y devuelve las claves que cambian."""
    old = build_massive(prefix, None, path, pts_page)
    new = build_massive(prefix, vri_index, path, pts_page)
    return {k: (old[k][0], new[k][0]) for k in old if old[k][0] != new[k][0]}
