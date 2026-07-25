#!/usr/bin/env python3
"""
pali_norm — normalización interna a la convención **VRI** (la del CST).

Regla de proyecto: *dentro* del pipeline todo se compara en una sola ortografía, y esa ortografía
es la del CST/VRI, porque es la de las claves de DPD (`lookup`) y la del lado que aporta los
títulos. El impreso de PTS escribe la misma lengua con otras convenciones, y sin normalizar la
comparación falla por motivos que no tienen nada que ver con el texto: `vyākata`/`byākata` son la
misma palabra y `saññojanaṃ` no aparece en DPD sólo porque DPD la guarda como `saṃyojanaṃ`.

**Nada de esto se ha decidido de memoria.** Cada regla está medida sobre los dos corpus completos
del Aṅguttara (2,9 M de caracteres de PTS en la BD, 2,8 M del CST en los XML de VRI):

| regla | PTS | CST (VRI) | decisión |
|---|---|---|---|
| `m` final de palabra | 4.500 | **0** | → `ṃ` siempre |
| `vyā-` / `byā-` | 841 / 8 | 2 / **972** | `vy` → `by` |
| `viriya` / `vīriya` | 329 / 0 | 7 / **355** | `viriy` → `vīriy` |
| `sañño-` / `saṃyo-` | 78 / 203 | 0 / **302** | `sañño` → `saṃyo` |
| `saṅkh-` / `saṃkh-` | 419 / 218 | **713** / 90 | `ṃ`+velar → `ṅ` |
| `aṅg-` / `aṃg-` | 1.479 / 128 | **1.790** / 21 | idem |
| `sañjā-` / `saṃjā-` | 49 / 0 | **56** / 0 | `ṃ`+palatal → `ñ` |

⚠️ **La nasal homorgánica sólo se aplica ante oclusiva.** Ante semivocal el CST **conserva** la
niggahīta (`saṃyojana`, `saṃvāsa`), así que una regla «ṃ → nasal del punto de articulación
siguiente» aplicada a ciegas destruiría justo las formas que queremos alcanzar.

⚠️ **`sañño` → `saṃyo` va como cadena concreta, no como regla general `ññ` → `ṃy`**: `paññā` no es
`paṃyā`. Las alternancias ortográficas del impreso se documentan una a una, con su medición.

`normaliza()` no pierde ni una palabra (regla del punto ciego): sólo sustituye grafías, nunca
descarta. `verifica()` comprueba con `pali_morphology.is_valid_pali` que lo que sale sigue siendo
pali fonotácticamente válido.
"""
import re

VELARES = 'kg'          # k, kh, g, gh → la aspirada la cubre la consonante base
PALATALES = 'cj'        # c, ch, j, jh

_REGLAS = [
    # niggahīta: la variante tipográfica y la `m` final del impreso
    (re.compile(r'ṁ'), 'ṃ'),
    (re.compile(r'm(?=[\s.,;:!?\'"\)\]]|$)'), 'ṃ'),
    # nasal homorgánica ANTE OCLUSIVA (nunca ante semivocal: `saṃyojana` se queda)
    (re.compile(f'ṃ(?=[{VELARES}])'), 'ṅ'),
    (re.compile(f'ṃ(?=[{PALATALES}])'), 'ñ'),
    # alternancias del impreso de PTS, medidas una a una sobre el corpus
    (re.compile(r'\bvy|(?<=[aāiīuūeo])vy'), 'by'),
    (re.compile(r'viriy'), 'vīriy'),
    (re.compile(r'sañño'), 'saṃyo'),
]


def normaliza(texto):
    """Texto en cualquiera de las dos convenciones → convención VRI."""
    if not texto:
        return texto
    for pat, rep in _REGLAS:
        texto = pat.sub(rep, texto)
    return texto


def verifica(palabras):
    """`[palabra]` → `[(antes, después)]` de las que la normalización deja en pali inválido.

    Comprobación de seguridad, no de calidad del texto: si normalizar produce una forma que
    `pali_morphology` rechaza, la regla que la produjo está mal, no el original.
    """
    import pali_morphology as pm
    malas = []
    for w in palabras:
        n = normaliza(w)
        if n != w and pm.is_valid_pali(w) and not pm.is_valid_pali(n):
            malas.append((w, n))
    return malas


if __name__ == '__main__':
    for w in ('vyākataṃ', 'vyañjanaṃ', 'saññojanaṃ', 'viriyaṃ', 'saṃkhāraṃ', 'saṃjānāti',
              'dhammam', 'saṃyojanaṃ', 'saṃvāso', 'paññā', 'aṃgaṃ'):
        print(f'  {w:>14} → {normaliza(w)}')
