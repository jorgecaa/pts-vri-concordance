#!/usr/bin/env python3
"""an_names — analizador de nombres de sutta de **AN**, que tiene convención propia.

El Excel nombra los suttas de AN con las convenciones del impreso de Morris, que no son las del
CST. Comparar raíz contra raíz falla en ~30 % de las filas del Tika **sin que ninguna esté mal
alineada**; lo que cambia es cómo nombra cada edición:

| Excel (PTS) | CST | qué pasa |
|---|---|---|
| `Pāpaṇika 1` | `9. Paṭhamapāpaṇikasuttaṃ` | el **ordinal va como dígito**, no como palabra |
| `Catumahārāja 2` | `8. Dutiyacatumahārājasuttaṃ` | idem |
| `Pacetana [Sacetana` | `5. Sacetanasuttaṃ` | Morris da la **variante entre corchetes**, y el CST usa *esa* |
| `Saviṭṭha [Samiddha` | `1. Samiddhasuttaṃ` | idem |
| `Kesaputti [Kālāma` | `65. Kesaputtisuttaṃ` | …y a veces el CST usa la primera |

De ahí las tres reglas:

1. **El dígito final del nombre PTS es el ordinal** que el CST escribe con palabra (`paṭhama`,
   `dutiya`, …). Comprobarlo es lo que impide el desfase dentro de una serie: `Pāpaṇika 1` es
   `Paṭhamapāpaṇika` y `Pāpaṇika 2` es `Dutiya…`, y sin esto ambos casan igual de bien.
2. **La variante entre corchetes cuenta como alternativa legítima**: se prueban las dos.
3. Comparación por **contención de raíces**, no por igualdad, y colapsando letras dobles.

`score(cst_title, pts_name)` → 0-100; `ordinal_ok(...)` → `True`/`False`/`None`.
"""
import re

_FOLD = str.maketrans({'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṅ': 'n', 'ñ': 'n', 'ṇ': 'n',
                       'ṭ': 't', 'ḍ': 'd', 'ḷ': 'l', 'ṃ': 'm', 'ṁ': 'm'})

_ORD = {'pathama': 1, 'dutiya': 2, 'tatiya': 3, 'catuttha': 4, 'pancama': 5, 'chattha': 6,
        'sattama': 7, 'atthama': 8, 'navama': 9, 'dasama': 10}


def _fold(t):
    return re.sub(r'[^a-z]', '', (t or '').lower().translate(_FOLD))


def _root(t):
    """Raíz comparable: sin diacríticos, sin desinencia, sin letras dobles."""
    t = _fold(t)
    t = re.sub(r'(suttantam|suttani|suttam|sutta|vaggo)$', '', t)
    t = re.sub(r'(.)\1+', r'\1', t)
    return re.sub(r'[aiueom]+$', '', t)


def pts_variants(name):
    """`«Magga 1 [Bālapaṇḍita 4]»` → `[('mag', 1), ('balapandit', 4)]`.

    **Cada variante lleva SU propio ordinal**, y el bueno es el de la que case con el CST. Tomar
    siempre el último dígito de la línea se equivoca en las dos direcciones: en
    `«Paṭipadā 4 [Khama 1]»` ≡ `«4. Paṭhamakhamasuttaṃ»` manda el 1 del corchete, pero en
    `«Magga 1 [Bālapaṇḍita 4]»` ≡ `«5. Paṭhamamaggasuttaṃ»` manda el 1 del nombre principal — el
    número del corchete pertenece a la *otra* numeración (la del vagga Bālapaṇḍita).

    Morris imprime la variante entre corchetes y el CST unas veces usa una y otras la otra, así
    que las dos son candidatas legítimas.
    """
    out = []
    for p in re.split(r'[\[\]()/,]', (name or '').strip()):
        p = p.strip()
        if not p:
            continue
        m = re.search(r'(\d+)\s*$', p)
        o = int(m.group(1)) if m else None
        r = _root(re.sub(r'\d+\s*$', '', p))
        # umbral 2: hay nombres genuinamente cortos («Agga» → raíz «ag») y descartarlos deja la
        # fila sin candidato
        if len(r) >= 2:
            out.append((r, o))
    return out


def cst_parts(title):
    """`«9. Paṭhamapāpaṇikasuttaṃ»` → `('papanik', 1, 'pathamapapanik')`.

    Devuelve la raíz **sin el ordinal**, el ordinal, y la raíz **entera** — porque no siempre lo
    que parece un ordinal lo es (`Dasamagga`), y quien compara debe poder probar las dos.
    """
    t = re.sub(r'^\s*[\d\s.,()\-]*', '', title or '')
    t = re.sub(r'\{[^}]*\}', ' ', t)
    t = _fold(t)
    t = re.sub(r'(suttantam|suttani|suttam|sutta)$', '', t)
    ordinal, sin_ord = None, t
    for w, k in _ORD.items():
        if t.startswith(w) and len(t) - len(w) >= 4:
            # se exige un resto sustancioso: «Dasamaggasuttaṃ» EMPIEZA por «dasama» (el ordinal
            # de 10) pero no es un ordinal — es el nombre «Dasamagga», y recortarlo dejaba «gga»
            ordinal, sin_ord = k, t[len(w):]
            break

    def _r(x):
        return re.sub(r'[aiueom]+$', '', re.sub(r'(.)\1+', r'\1', x))
    return _r(sin_ord), ordinal, _r(t)


def score(cst_title, pts_name):
    """0-100: afinidad del nombre PTS con el título CST, probando ambas variantes."""
    base, _o, entero = cst_parts(cst_title)
    cands = [r for r, _o2 in pts_variants(pts_name)]
    if not base or not cands:
        return 0
    # se prueban las DOS lecturas del título: con el ordinal recortado y sin recortar. Si el
    # «ordinal» era en realidad parte del nombre, la segunda es la buena.
    return max(_score1(base, cands), _score1(entero, cands))


def _score1(base, cands):
    if len(base) < 3:                       # raíz muy corta: exigir igualdad, no contención
        return 100 if base in cands else 0
    best = 0
    for c in cands:
        if c == base:
            best = max(best, 100)
        elif c.startswith(base) or base.startswith(c):
            best = max(best, 80)
        elif min(len(c), len(base)) >= 4 and (c in base or base in c):
            best = max(best, 60)
    return best


def ordinal_ok(cst_title, pts_name):
    """`True`/`False` si ambos declaran ordinal y concuerdan; `None` si alguno no lo declara.

    Es el desempate de serie: `Pāpaṇika 1` ≡ `Paṭhama…`, `Pāpaṇika 2` ≡ `Dutiya…`.
    """
    base, co, entero = cst_parts(cst_title)
    if co is None:
        return None
    # el ordinal que cuenta es el de la variante que MEJOR casa con el título del CST
    mejor, po = -1, None
    for r, o in pts_variants(pts_name):
        sc = max(_score1(base, [r]), _score1(entero, [r]))
        if sc > mejor:
            mejor, po = sc, o
    if po is None or mejor <= 0:
        return None
    return co == po
