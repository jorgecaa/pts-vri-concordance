#!/usr/bin/env python3
"""sn4_names — analizador de nombres de sutta de **SN IV**, que tiene convención propia.

Comparar los nombres con la regla genérica del repo (raíz contra raíz, con prefijo) falla en 96 de
332 filas de S iv **sin que ninguna esté mal alineada**: lo que cambia es cómo nombra Feer.

| CST | PTS | qué pasa |
|---|---|---|
| `1. Ajjhattāniccasuttaṃ` | `Aniccam1; ajjhattam` | mismos dos términos, **orden invertido** y separados por `;` |
| `7. Ajjhattāniccātītānāgatasuttaṃ` | `Aniccam3; ajjhattam` | el CST añade `atītānāgata`, PTS lo deja en el dígito |
| `1. Paṭhamapubbesambodhasuttaṃ` | `Sambodhena1` | PTS pone el término en **instrumental** y el ordinal como **dígito volado** |
| `3. Paṭhamaassādapariyesanasuttaṃ` | `Assādena1` | idem, y PTS abrevia el compuesto |

De ahí las dos reglas de este módulo:

1. **Contención de términos, no igualdad de raíces.** El nombre de PTS se parte en términos y cada
   uno debe aparecer *dentro* del compuesto del CST. El orden no cuenta.
2. **El dígito volado de PTS es el ordinal que el CST escribe con palabra** (`paṭhama`, `dutiya`,
   …). Comprobarlo es lo que impide el desfase dentro de una serie: `Sambodhena1` es
   `Paṭhamapubbesambodha` y `Sambodhena2` es `Dutiya…`, y sin esto las dos casan igual de bien.

`score(cst_title, pts_name)` devuelve 0-100 y `ordinal_ok(...)` el contraste del ordinal.
"""
import re

_FOLD = str.maketrans({'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṅ': 'n', 'ñ': 'n', 'ṇ': 'n',
                       'ṭ': 't', 'ḍ': 'd', 'ḷ': 'l', 'ṃ': 'm', 'ṁ': 'm'})

_ORD = {'pathama': 1, 'dutiya': 2, 'tatiya': 3, 'catuttha': 4, 'pancama': 5, 'chattha': 6,
        'sattama': 7, 'atthama': 8, 'navama': 9, 'dasama': 10}

# desinencias que hay que quitar para comparar un término suelto con un compuesto
_SUFF = re.compile(r'(suttantam|suttam|suttani|sutta|vaggo|ena|assa|aya|smim|mhi|ani|am|a|o|e|i|u)$')


def _fold(t):
    return re.sub(r'[^a-z]', '', (t or '').lower().translate(_FOLD))


def _root(t):
    """Raíz de un término: sin diacríticos, sin desinencia, sin dobles."""
    t = _fold(t)
    for _ in range(2):
        t = _SUFF.sub('', t) or t
    return re.sub(r'(.)\1+', r'\1', t)


def pts_terms(name):
    """`«Aniccam1; ajjhattam»` → `(['anicc', 'ajjhat'], 1)`: términos y dígito volado."""
    s = (name or '').strip()
    digits = re.findall(r'(\d+)', s)
    ordinal = int(digits[-1]) if digits else None
    s = re.sub(r'\d+', ' ', s)
    parts = [p for p in re.split(r'[;,()/]|\s+|--+', s) if p.strip()]
    terms = [r for r in (_root(p) for p in parts) if len(r) >= 3]
    return terms, ordinal


def cst_parts(title):
    """`«1. Paṭhamapubbesambodhasuttaṃ»` → `('pubesambodh', 1)`: compuesto y ordinal en palabra."""
    t = re.sub(r'^\s*[\d\s.,()-]*', '', title or '')
    t = _fold(t)
    t = re.sub(r'(suttantam|suttam|suttani|sutta)$', '', t)
    ordinal = None
    for w, k in _ORD.items():
        if t.startswith(w):
            ordinal, t = k, t[len(w):]
            break
    return re.sub(r'(.)\1+', r'\1', t), ordinal


def score(cst_title, pts_name):
    """0-100: cuánto del nombre de PTS aparece dentro del compuesto del CST."""
    comp, _o = cst_parts(cst_title)
    terms, _d = pts_terms(pts_name)
    if not comp or not terms:
        return 0
    hits = sum(1 for t in terms if t and t in comp)
    if not hits:
        # último recurso: prefijo largo compartido (nombres abreviados por Feer)
        return 40 if any(len(t) >= 5 and (comp.startswith(t[:5]) or t[:5] in comp) for t in terms) else 0
    return 100 if hits == len(terms) else 70


def ordinal_ok(cst_title, pts_name):
    """`True`/`False` si ambos declaran ordinal y concuerdan; `None` si alguno no lo declara.

    Es el desempate dentro de una serie: `Sambodhena1` ≡ `Paṭhama…`, `Sambodhena2` ≡ `Dutiya…`.
    """
    _c, co = cst_parts(cst_title)
    _t, po = pts_terms(pts_name)
    if co is None or po is None:
        return None
    return co == po
