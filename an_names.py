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
    """`«Pacetana [Sacetana»` → `(['pacetan', 'sacetan'], None)`: alternativas y ordinal.

    Morris imprime la variante entre corchetes y el CST unas veces usa una y otras la otra, así
    que las dos son candidatas legítimas.
    """
    s = (name or '').strip()
    m = re.search(r'(\d+)\s*$', s)
    ordinal = int(m.group(1)) if m else None
    s = re.sub(r'\d+\s*$', '', s)
    parts = [p for p in re.split(r'[\[\]()/,]', s) if p.strip()]
    return [r for r in (_root(p) for p in parts) if len(r) >= 3], ordinal


def cst_parts(title):
    """`«9. Paṭhamapāpaṇikasuttaṃ»` → `('papanik', 1)`: raíz y ordinal en palabra."""
    t = re.sub(r'^\s*[\d\s.,()\-]*', '', title or '')
    t = re.sub(r'\{[^}]*\}', ' ', t)
    t = _fold(t)
    t = re.sub(r'(suttantam|suttani|suttam|sutta)$', '', t)
    ordinal = None
    for w, k in _ORD.items():
        if t.startswith(w):
            ordinal, t = k, t[len(w):]
            break
    t = re.sub(r'(.)\1+', r'\1', t)
    return re.sub(r'[aiueom]+$', '', t), ordinal


def score(cst_title, pts_name):
    """0-100: afinidad del nombre PTS con el título CST, probando ambas variantes."""
    base, _o = cst_parts(cst_title)
    cands, _d = pts_variants(pts_name)
    if not base or not cands:
        return 0
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
    _b, co = cst_parts(cst_title)
    _c, po = pts_variants(pts_name)
    if co is None or po is None:
        return None
    return co == po
