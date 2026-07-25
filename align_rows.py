#!/usr/bin/env python3
"""
align_rows — asignación **inyectiva y monótona** de filas del Excel a marcadores PTS.

**El problema que resuelve.** Resolver cada fila por su cuenta («busca el marcador que mejor se
parezca») no garantiza que dos filas no acaben en el mismo sitio: en S iii y S v había 12 filas de
más sobre marcadores ya ocupados, y cada una quedaba validada contra el locus de su vecino. El
validador no puede verlo, porque el par PTS↔CST que recibe es coherente consigo mismo.

**La solución.** Las dos secuencias están ordenadas — las filas en orden canónico y los marcadores
en orden de lectura —, así que la asignación correcta es un **alineamiento monótono**, no una
búsqueda por fila. Se resuelve exacto por programación dinámica maximizando la suma de las
puntuaciones que ya usan los drivers, con dos restricciones:

- **monotonía**: si la fila *i* va al marcador *j*, la fila *i+1* va a *j* o posterior;
- **capacidad**: un marcador de rango (`140-142 (5-7) Dukkhena`) admite tantas filas como suttas
  cubre; uno individual, una sola.

Por monotonía, las filas que comparten marcador son necesariamente consecutivas, así que basta
llevar en el estado la longitud de la racha actual. Coste O(Σ_j capacidad(j) × nº de filas), que en
estos volúmenes son ~10⁵ operaciones.

Es la generalización de lo que ya funcionaba donde no había defecto: la alineación posicional de
S i y la del Diṭṭhi (`ditthi_pairs`).
"""

NEG = float('-inf')


def assign(n_rows, n_marks, score, capacity, skip_penalty=0.0):
    """Devuelve `[índice de marcador | None]` por fila.

    `score(i, j)` → afinidad fila *i* ↔ marcador *j* (usa `None`/`-inf` para prohibir el par).
    `capacity(j)` → cuántas filas admite el marcador *j*.
    `skip_penalty` → coste de dejar una fila sin marcador (0 = gratis; súbelo para forzar
    asignación cuando se sabe que todas las filas tienen marcador).
    """
    if not n_rows:
        return []
    caps = [max(1, capacity(j)) for j in range(n_marks)]

    # Estado tras procesar la fila *i*: `(j, r)` = el último marcador ASIGNADO es j y ya lleva r
    # filas (1 ≤ r ≤ caps[j]); más el estado inicial `START`, sin marcador aún. Saltar una fila
    # **conserva el estado** y sólo resta `skip_penalty`.
    #
    # Que el salto conserve la posición es lo que hace correcto el alineamiento. Antes el estado de
    # salto era un escalar sin memoria del marcador, así que para no romper la monotonía sólo se
    # admitía cuando superaba el máximo global: se perdía el óptimo justo en el caso que importa
    # —una fila del CST que PTS no imprime en mitad de una serie— porque el camino bueno pasa por
    # un salto que NO es el máximo global (S iii 22.148 «Dukkhānupassī», ausente de PTS: la ruta
    # correcta puntúa 292.8 y se devolvía la de 292.1).
    #
    # Y conservar la racha es además lo correcto filológicamente: si a un marcador de rango
    # («140-142 (5-7) Dukkhena») le falta uno de los suttas del CST, sus vecinos siguen cayendo en
    # ese mismo marcador; la capacidad cuenta filas asignadas, no filas consecutivas del Excel.
    dp = [[NEG] * (c + 1) for c in caps]
    start = 0.0                                    # aún no se ha asignado ningún marcador
    hist = []

    for i in range(n_rows):
        # prefijo: mejor estado anterior cuyo último marcador es ESTRICTAMENTE menor que j
        before, arg = [NEG] * (n_marks + 1), [None] * (n_marks + 1)
        run, run_arg = start, (None if start > NEG else None)
        for j in range(n_marks):
            before[j], arg[j] = run, run_arg
            cur = max(dp[j])
            if cur > run:
                run, run_arg = cur, (j, dp[j].index(cur))
        before[n_marks], arg[n_marks] = run, run_arg

        ndp = [[NEG] * (c + 1) for c in caps]
        nback = [[None] * (c + 1) for c in caps]
        for j in range(n_marks):
            s = score(i, j)
            if s is None or s == NEG:
                continue
            if before[j] > NEG:
                ndp[j][1] = before[j] + s
                nback[j][1] = arg[j]
            for r in range(2, caps[j] + 1):        # una fila más sobre el mismo marcador
                if dp[j][r - 1] > NEG and dp[j][r - 1] + s > ndp[j][r]:
                    ndp[j][r] = dp[j][r - 1] + s
                    nback[j][r] = (j, r - 1)
        # saltar la fila i: el estado se conserva tal cual
        for j in range(n_marks):
            for r in range(1, caps[j] + 1):
                if dp[j][r] - skip_penalty > ndp[j][r]:
                    ndp[j][r], nback[j][r] = dp[j][r] - skip_penalty, ('skip', (j, r))
        nstart = start - skip_penalty

        hist.append((nback, ndp, dp, start))
        dp, start = ndp, nstart

    # reconstrucción hacia atrás
    cand = [(max(dp[j]), (j, dp[j].index(max(dp[j])))) for j in range(n_marks)
            if max(dp[j]) > NEG]
    cand.append((start, None))
    _v, state = max(cand, key=lambda x: x[0])
    out = [None] * n_rows
    for i in range(n_rows - 1, -1, -1):
        nback, _ndp, _pdp, _ps = hist[i]
        if state is None:                          # veníamos de START: esta fila y las previas van sin marcador
            continue
        j, r = state
        b = nback[j][r]
        if isinstance(b, tuple) and b and b[0] == 'skip':
            out[i] = None
            state = b[1]
        else:
            out[i] = j
            state = b
    return out
