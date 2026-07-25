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

    # dp[j][r] = mejor puntuación de las filas 0..i con la fila i asignada a j, siendo r la
    # longitud de la racha de filas consecutivas que han caído en j (1 ≤ r ≤ caps[j]).
    dp = [[NEG] * (c + 1) for c in caps]
    back = [[None] * (c + 1) for c in caps]
    skip = NEG                                     # mejor puntuación con la fila i sin asignar
    skip_back = None
    hist = []

    for i in range(n_rows):
        # mejor valor alcanzable habiendo terminado en un marcador < j (prefijo acumulado)
        best_before, arg_before = [NEG] * (n_marks + 1), [None] * (n_marks + 1)
        run, arg = NEG, None
        for j in range(n_marks):
            if i:
                cur = max(dp[j])
                if cur > run:
                    run, arg = cur, ('m', j, dp[j].index(cur))
            best_before[j + 1], arg_before[j + 1] = run, arg
        if i and skip > run:                       # también se puede venir de una fila saltada
            for j in range(n_marks + 1):
                if skip > best_before[j]:
                    best_before[j], arg_before[j] = skip, ('s',)

        ndp = [[NEG] * (c + 1) for c in caps]
        nback = [[None] * (c + 1) for c in caps]
        for j in range(n_marks):
            s = score(i, j)
            if s is None or s == NEG:
                continue
            base = best_before[j] if i else 0.0
            if base > NEG:
                ndp[j][1] = base + s
                nback[j][1] = arg_before[j] if i else None
            if i:                                   # continuar la racha en el mismo marcador
                for r in range(2, caps[j] + 1):
                    if dp[j][r - 1] > NEG and dp[j][r - 1] + s > ndp[j][r]:
                        ndp[j][r] = dp[j][r - 1] + s
                        nback[j][r] = ('m', j, r - 1)
        prev_best = max([max(x) for x in dp] + [skip]) if i else 0.0
        nskip = (prev_best - skip_penalty) if i else -skip_penalty
        nskip_back = None
        if i:
            cand = [(max(dp[j]), ('m', j, dp[j].index(max(dp[j])))) for j in range(n_marks)
                    if max(dp[j]) > NEG]
            if skip > NEG:
                cand.append((skip, ('s',)))
            if cand:
                v, b = max(cand, key=lambda x: x[0])
                nskip, nskip_back = v - skip_penalty, b
            else:
                nskip = NEG
        hist.append((nback, nskip_back))
        dp, skip, skip_back = ndp, nskip, nskip_back

    # reconstrucción hacia atrás
    cand = [(max(dp[j]), ('m', j, dp[j].index(max(dp[j])))) for j in range(n_marks)
            if max(dp[j]) > NEG]
    if skip > NEG:
        cand.append((skip, ('s',)))
    if not cand:
        return [None] * n_rows
    _v, state = max(cand, key=lambda x: x[0])
    out = [None] * n_rows
    for i in range(n_rows - 1, -1, -1):
        nback, nskip_back = hist[i]
        if state[0] == 'm':
            _t, j, r = state
            out[i] = j
            state = nback[j][r]
        else:
            out[i] = None
            state = nskip_back
        if state is None and i:
            break
    return out
