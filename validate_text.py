#!/usr/bin/env python3
"""
Valida el texto puro de cada libro contra el Digital Pāḷi Dictionary (DPD) para
detectar typos de digitalización.

Compara solo el TEXTO (omite aparato crítico y cabecera). Normaliza el estilo
ortográfico de la edición (que es IAST estándar, compatible con DPD) antes de
comparar, para no marcar como error lo que solo es sandhi/elisión:
  · niggahīta sin asimilar:  saṃkhepo → saṅkhepo  (ṃ+velar→ṅ, +palatal→ñ, …)
  · ṃ final escrito ñ/ṅ/m/n ante la palabra siguiente:  dhammañ → dhammaṃ
  · elisión con apóstrofo:   c'eva, pan'assa, ten'  (vocal elidida)
  · iti citativo fusionado:  hotīti, vuccatīti
  · consonante de enlace:    tasmāt, yāvad, kenacid

Para cada token que NO se resuelve, intenta una corrección a 1 cambio de
diacrítico (t↔ṭ, n↔ṇ/ṅ, a↔ā, …): si la corrección existe en DPD, es un typo
casi seguro. El resto queda como «desconocido» para revisión manual.

Salida: dpd_check/book_NN.txt por libro + resumen por pantalla.

Uso:  python validate_text.py [DPD_DB] [DIR_JSON]
"""

import functools
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

DPD_DB = sys.argv[1] if len(sys.argv) > 1 else "/dev/shm/dpd.db"
JSON_DIR = Path(sys.argv[2] if len(sys.argv) > 2 else "rotb_commentary")
OUT_DIR = Path("dpd_check")

# Asimilación del niggahīta a la nasal homorgánica (estilo DPD)
_NAS = {
    "k": "ṅ",
    "g": "ṅ",
    "c": "ñ",
    "j": "ñ",
    "ṭ": "ṇ",
    "ḍ": "ṇ",
    "t": "n",
    "d": "n",
    "p": "m",
    "b": "m",
}
# Pares de intercambio de diacrítico para sugerir correcciones de typo
_SWAP = {
    "t": ["ṭ"],
    "ṭ": ["t"],
    "d": ["ḍ"],
    "ḍ": ["d"],
    "n": ["ṇ", "ṅ"],
    "ṇ": ["n"],
    "ṅ": ["n", "ṃ"],
    "ñ": ["ṃ", "n"],
    "l": ["ḷ"],
    "ḷ": ["l"],
    "m": ["ṃ"],
    "ṃ": ["m", "ṅ", "ñ", "ṇ", "n"],
    "a": ["ā"],
    "ā": ["a"],
    "i": ["ī"],
    "ī": ["i"],
    "u": ["ū"],
    "ū": ["u"],
    "s": ["ś", "ṣ"],
}
_DIGRAPH = {
    "tt": ["ṭṭ"],
    "ṭṭ": ["tt"],
    "dd": ["ḍḍ"],
    "ḍḍ": ["dd"],
    "nn": ["ṇṇ", "ññ"],
    "ṇṇ": ["nn"],
    "ññ": ["nn"],
    "ll": ["ḷḷ"],
    "ḷḷ": ["ll"],
}
_ROMAN = re.compile(r"^[ivxlcdm]+$")
_STRIP = ".,;:!?\u201c\u201d\u2018\u2019'\"()[]*_·…—–- "


def assim(t):
    return "".join(
        _NAS[t[i + 1]] if ch == "ṃ" and i + 1 < len(t) and t[i + 1] in _NAS else ch
        for i, ch in enumerate(t)
    )


def load_keys(db_path):
    con = sqlite3.connect(db_path)
    # Todas las claves de búsqueda directa
    keys = set(r[0] for r in con.execute("SELECT lookup_key FROM lookup"))
    # Añadir palabras que DPD puede descomponer (no son headwords pero
    # el deconstructor las reconoce como compuestos válidos)
    decon = (
        r[0]
        for r in con.execute("SELECT lookup_key FROM lookup WHERE deconstructor != ''")
    )
    keys.update(decon)
    con.close()
    return keys


class Checker:
    def __init__(self, keys):
        self.K = keys

    def _forms(self, s):
        """Variantes de UNA palabra simple (sin - ni ')."""
        fs = {s}
        if s and s[-1] in "mnñṅ":
            fs.add(s[:-1] + "ṃ")  # ṃ final escrito como nasal
        out = set(fs)
        for f in fs:
            out.add(assim(f))  # niggahīta asimilado
        # variantes de consonante simple/doble (kheḷa ↔ kheḷḷa)
        extra = set()
        for f in out:
            for dg, reps in _DIGRAPH.items():
                for m in re.finditer(dg, f):
                    for rep in reps:
                        extra.add(f[: m.start()] + rep + f[m.end() :])
        out.update(extra)
        return out

    @functools.lru_cache(maxsize=100000)
    def _seg_ok(self, s):
        if not s:
            return True
        if self._forms(s) & self.K:
            return True
        # elisión: restaura la vocal final caída
        if any(s + v in self.K for v in "aāiīuūeo"):
            return True
        # deconstructor: intenta descomponer el segmento
        if self._decon_ok(s):
            return True
        return False

    @functools.lru_cache(maxsize=100000)
    def resolve(self, t):
        """¿El token t (limpio, minúsculas) se resuelve contra DPD?"""
        if self._forms(t) & self.K:
            return True
        # elisión: token que termina en vocal caída (ath' → atha)
        if self._seg_ok(t):
            return True
        # guiones editoriales PTS: probar sin ellos (ratana-ttaye → ratanattaye)
        if "-" in t and self._forms(t.replace("-", "")) & self.K:
            return True
        # elisión / compuesto: trocea por ' y por -, exige todas las partes
        if "'" in t or "-" in t:
            segs = [s for s in re.split(r"['-]", t) if s]
            if segs and all(self._seg_ok(s) for s in segs):
                return True
        # deconstructor: intenta partir el compuesto en dos
        if self._decon_ok(t):
            return True
        # iti citativo:  …(ī)ti  →  raíz + iti
        if t.endswith("ti"):
            for stem in (t[:-2], t[:-2] + "i", t[:-3] + "i" if len(t) > 3 else ""):
                if stem and (self._forms(stem) & self.K or self._seg_ok(stem)):
                    return True
        # consonante de enlace final (tasmāt, yāvad, kenacid)
        if len(t) > 2 and t[-1] in "tdṃ" and self._forms(t[:-1]) & self.K:
            return True
        return False

    def _decon_ok(self, t):
        """Intenta descomponer t en dos partes, cada una resuelta en DPD."""
        if len(t) < 5:
            return False
        for i in range(2, len(t) - 2):
            a, b = t[:i], t[i:]
            if self._seg_ok(a) and self._seg_ok(b):
                return True
        return False

    def suggest(self, w):
        """Correcciones a 1 cambio de diacrítico (sobre la forma original y la
        asimilada) que SÍ están en DPD: la clase típica de typo."""
        out = set()
        for base in {w, assim(w)}:
            for i, ch in enumerate(base):
                for a in _SWAP.get(ch, ()):
                    cand = base[:i] + a + base[i + 1 :]
                    if cand in self.K:
                        out.add(cand)
            for dg, reps in _DIGRAPH.items():  # dobles: tt↔ṭṭ, ṇṇ↔nn …
                for m in re.finditer(dg, base):
                    for rep in reps:
                        cand = base[: m.start()] + rep + base[m.end() :]
                        if cand in self.K:
                            out.add(cand)
        out.discard(w)
        return out


def purify(text):
    text = re.sub(r"\[F\.\d+[vr]?\]", " ", text)  # folios
    text = re.sub(r"║\d+║", " ", text)  # secciones
    return text.replace("{", " ").replace("}", " ")


def clean_token(tok):
    t = tok.lower().strip(_STRIP)
    t = re.sub(r"\d+", "", t).strip(_STRIP)  # quita nº de nota pegado
    return t


def context(words, j, form):
    """Contexto en la línea con la palabra marcada «…» para localizarla."""
    left = " ".join(words[max(0, j - 4) : j])
    right = " ".join(words[j + 1 : j + 5])
    return f"{left} «{form}» {right}".strip()


def check_book(jpath, chk):
    """Devuelve (book, total, ok, ocurrencias). Cada ocurrencia, EN ORDEN DEL
    DOCUMENTO: {page, line, form, ctx}."""
    book = json.loads(Path(jpath).read_text(encoding="utf-8"))
    occ = []
    total = ok = 0
    for p in book["pages"]:
        pn = p["page"]
        for li, line in enumerate(purify(p["text"]).split("\n"), 1):
            words = line.split()
            for j, w in enumerate(words):
                t = clean_token(w)
                if len(t) < 2 or _ROMAN.match(t) or any(c.isdigit() for c in t):
                    continue
                total += 1
                if chk.resolve(t):
                    ok += 1
                    continue
                occ.append(
                    {"page": pn, "line": li, "form": t, "ctx": context(words, j, w)}
                )
    return book, total, ok, occ


def main():
    print(f"cargando DPD ({DPD_DB})…", flush=True)
    chk = Checker(load_keys(DPD_DB))
    print(f"{len(chk.K):,} formas DPD\n")
    OUT_DIR.mkdir(exist_ok=True)

    summary = []
    g_typo = g_unk = 0
    for jpath in sorted(JSON_DIR.glob("book_*.json")):
        book, total, ok, occ = check_book(jpath, chk)
        bn = book["book_no"]
        cov = 100 * ok / total if total else 0

        sugg = {}  # cache forma → sugerencias
        for o in occ:
            if o["form"] not in sugg:
                sugg[o["form"]] = chk.suggest(o["form"])
            o["sugg"] = sugg[o["form"]]
        typos = [o for o in occ if o["sugg"]]
        unknown = [o for o in occ if not o["sugg"]]
        g_typo += len(typos)
        g_unk += len(unknown)
        forms_t = {o["form"] for o in typos}
        summary.append((bn, book["name"], total, cov, len(typos), len(unknown)))

        out = [
            f"# {book['name']}  (libro {bn:02d})",
            f"# tokens: {total:,} · cobertura DPD: {cov:.1f}%",
            f"# typos: {len(typos)} ocurrencias ({len(forms_t)} formas) · "
            f"desconocidos: {len(unknown)}",
            "# «forma» marca la palabra; PTS = nº de página del impreso; "
            "L = línea aprox.",
            "",
        ]

        # 1) Localizado por página (para cotejar con el original, en orden)
        out.append("## TYPOS · POR PÁGINA PTS  (forma → corrección DPD)")
        for o in typos:  # ya en orden documento (página, línea)
            out.append(
                f"  PTS {o['page']:>4} L{o['line']:<2}  "
                f"«{o['form']}» → {' / '.join(sorted(o['sugg']))}"
            )
            out.append(f"        {o['ctx']}")

        # 2) Índice por forma (para arreglar todas las instancias de un typo)
        by_form = defaultdict(list)
        for o in typos:
            by_form[o["form"]].append(o["page"])
        out += ["", "## TYPOS · ÍNDICE POR FORMA"]
        for form in sorted(by_form, key=lambda f: -len(by_form[f])):
            pgs = ",".join(str(p) for p in sorted(set(by_form[form])))
            out.append(
                f"  «{form}» → {' / '.join(sorted(sugg[form]))}   "
                f"[{len(by_form[form])}×]  PTS {pgs}"
            )

        # 3) Desconocidos, también localizados por página
        out += ["", "## DESCONOCIDOS · POR PÁGINA PTS  (revisar a mano)"]
        for o in unknown:
            out.append(f"  PTS {o['page']:>4} L{o['line']:<2}  {o['ctx']}")

        (OUT_DIR / f"book_{bn:02d}.txt").write_text("\n".join(out), encoding="utf-8")
        print(
            f"  {bn:02d}: {cov:5.1f}%  typos={len(typos):5d}  "
            f"descon.={len(unknown):5d}  {book['name'][:38]}"
        )

    lines = [
        "# RESUMEN — validación DPD del texto",
        "# libro · cobertura · typos(ocurr.) · desconocidos · obra",
        "",
    ]
    for bn, name, total, cov, nt, nu in summary:
        lines.append(f"{bn:02d}  {cov:5.1f}%  {nt:6d}  {nu:6d}  {name}")
    (OUT_DIR / "RESUMEN.txt").write_text("\n".join(lines), encoding="utf-8")
    print(
        f"\n✓ informes en {OUT_DIR}/  ·  typos={g_typo:,} ocurrencias · "
        f"desconocidos={g_unk:,}"
    )


if __name__ == "__main__":
    main()
