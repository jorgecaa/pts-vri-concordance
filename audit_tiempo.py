#!/usr/bin/env python3
"""
audit_tiempo — auditor de **presupuesto por operación**.

Hermano de `check_integrity.py` y `audit_injectivity.py`, pero lo que vigila no es el dato: es el
**coste de llegar a él**. El fallo que cubre es real y se repitió en el barrido de las colas
peyyāla de A ii–A v: una exploración que debía acotar un régimen de marcadores se convirtió en un
alineador nuevo, tres iteraciones de heurística de sondas y decenas de volcados de página, sin que
en ningún momento hubiera un punto de parada declarado. El trabajo no estaba mal; estaba **sin
presupuesto**, y por eso nadie —ni yo— podía decir que se había pasado.

La regla que implementa (regla (7) de `CLAUDE.md`):

> **Toda operación declara su presupuesto ANTES de empezar.** Al agotarse se para, se informa de lo
> conseguido y de lo que falta, y se pide decisión. Ampliar el presupuesto es una decisión de
> Jorge, no del que ejecuta.

El presupuesto se mide en **pasos** (llamadas a herramienta, corridas de script, iteraciones) y en
**minutos**, porque los dos se agotan por caminos distintos: una espera de API gasta minutos sin
pasos, y una tanda de sondeos gasta pasos sin apenas minutos.

Uso:
    python3 audit_tiempo.py abrir "barrer pendientes de A ii" --pasos 25 --min 20
    python3 audit_tiempo.py paso  "dry-run del alineador"      # +1 paso a la operación abierta
    python3 audit_tiempo.py estado                             # ¿queda presupuesto?  (rc 1 si no)
    python3 audit_tiempo.py cerrar --resultado "25/25 probadas"
    python3 audit_tiempo.py informe                            # histórico y desvíos

`estado` devuelve **código de salida 1** cuando el presupuesto está agotado: así se puede encadenar
(`python3 audit_tiempo.py estado || echo PARAR`) y que la parada no dependa de que alguien lea la
salida.
"""
import json
import os
import sys
import time
from datetime import datetime

LIBRO = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.presupuesto.jsonl')

# Presupuestos por defecto, deliberadamente cortos: el valor de esto está en que se agote pronto y
# obligue a informar, no en que dé permiso para seguir.
PASOS_DEF, MIN_DEF = 20, 15


def _lee():
    if not os.path.exists(LIBRO):
        return []
    with open(LIBRO) as f:
        return [json.loads(l) for l in f if l.strip()]


def _escribe(regs):
    with open(LIBRO, 'w') as f:
        for r in regs:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


def _abierta(regs):
    return next((r for r in reversed(regs) if r.get('fin') is None), None)


def _gasto(op):
    return {'pasos': op['pasos_usados'], 'min': round((time.time() - op['t0']) / 60, 1)}


def _excedida(op):
    g = _gasto(op)
    return g['pasos'] > op['pasos'] or g['min'] > op['min']


def abrir(argv):
    regs = _lee()
    ab = _abierta(regs)
    if ab:
        print(f"⚠ ya hay una operación abierta: «{ab['nombre']}». Ciérrala antes de abrir otra.")
        return 1
    nombre = argv[0] if argv else '(sin nombre)'
    pasos = int(argv[argv.index('--pasos') + 1]) if '--pasos' in argv else PASOS_DEF
    mins = float(argv[argv.index('--min') + 1]) if '--min' in argv else MIN_DEF
    regs.append({'nombre': nombre, 'inicio': datetime.now().isoformat(timespec='seconds'),
                 't0': time.time(), 'pasos': pasos, 'min': mins, 'pasos_usados': 0,
                 'hitos': [], 'fin': None, 'resultado': None})
    _escribe(regs)
    print(f'▸ operación «{nombre}» — presupuesto: {pasos} pasos / {mins:g} min')
    return 0


def paso(argv):
    regs = _lee()
    op = _abierta(regs)
    if not op:
        print('⚠ no hay operación abierta (usa `abrir` primero)')
        return 1
    op['pasos_usados'] += 1
    if argv:
        op['hitos'].append(argv[0])
    _escribe(regs)
    return estado([])


def estado(_argv):
    regs = _lee()
    op = _abierta(regs)
    if not op:
        print('· sin operación abierta')
        return 0
    g = _gasto(op)
    barra = f"{g['pasos']}/{op['pasos']} pasos · {g['min']:g}/{op['min']:g} min"
    if _excedida(op):
        print(f"✗ PRESUPUESTO AGOTADO en «{op['nombre']}» ({barra}).")
        print('  Para, informa de lo conseguido y de lo que falta, y pide decisión.')
        print('  Ampliar el presupuesto es decisión de Jorge, no del que ejecuta.')
        return 1
    print(f"✓ «{op['nombre']}» — {barra}")
    return 0


def cerrar(argv):
    regs = _lee()
    op = _abierta(regs)
    if not op:
        print('⚠ no hay operación abierta')
        return 1
    g = _gasto(op)
    op['fin'] = datetime.now().isoformat(timespec='seconds')
    op['gasto'] = g
    op['excedida'] = _excedida(op)
    if '--resultado' in argv:
        op['resultado'] = argv[argv.index('--resultado') + 1]
    _escribe(regs)
    marca = '✗ excedida' if op['excedida'] else '✓ dentro'
    print(f"{marca}: «{op['nombre']}» {g['pasos']}/{op['pasos']} pasos · "
          f"{g['min']:g}/{op['min']:g} min — {op['resultado'] or 'sin resultado anotado'}")
    return 0


def informe(_argv):
    regs = [r for r in _lee() if r.get('fin')]
    if not regs:
        print('· sin operaciones cerradas')
        return 0
    exc = [r for r in regs if r.get('excedida')]
    print(f'{len(regs)} operaciones cerradas · {len(exc)} excedidas '
          f'({100 * len(exc) / len(regs):.0f} %)')
    for r in regs[-15:]:
        g = r['gasto']
        print(f"  {'✗' if r.get('excedida') else '✓'} {r['inicio'][:16]}  "
              f"{g['pasos']:>3}/{r['pasos']:<3} pasos {g['min']:>5}/{r['min']:<4} min  "
              f"{r['nombre'][:48]}")
    return 0


CMD = {'abrir': abrir, 'paso': paso, 'estado': estado, 'cerrar': cerrar, 'informe': informe}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in CMD:
        print(__doc__.split('Uso:')[1].strip())
        sys.exit(2)
    sys.exit(CMD[sys.argv[1]](sys.argv[2:]))
