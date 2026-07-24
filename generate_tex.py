#!/usr/bin/env python3
"""
Generate LaTeX documents from extracted commentary JSON files.

Usage:
  python generate_tex.py [--diplomatic] [book_NN.json ...]

Opciones:
  --diplomatic   No normaliza el niggahīta (conserva la ortografía PTS antigua
                 m/n final). Por defecto se normaliza a `ṃ` (norma moderna).

Mejoras editoriales respecto a la versión inicial:
  #2 aparato crítico: cada nota se ancla a su lema con \\footnote numerado,
     en vez de un volcado único al pie de página.
  #3 versos (gāthā): los bloques sangrados se componen en `verse`, no en prosa.
  #5 índice (ToC): cabeceras de sección reales (\\addcontentsline), no \\section*.
  #6/#9 cornisas y citación: sigla + volumen PTS desde book_meta.
  #7 niggahīta: normalización opcional m/n final → ṃ (por defecto activada).
  #8 tipografía: 11pt, caja tipo libro (B5), Book Antiqua → TeX Gyre Pagella.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from book_meta import book_title  # noqa: E402

TEX_PREAMBLE = r"""\documentclass[11pt,b5paper,twoside]{book}
\usepackage{fontspec}
\usepackage[b5paper,inner=2.4cm,outer=1.9cm,top=2.2cm,bottom=2.4cm]{geometry}
\usepackage{fancyhdr}
\usepackage{microtype}
\usepackage{xcolor}
\usepackage{hyperref}
\hypersetup{hidelinks,pdftitle={PDF_TITLE}}

% ── Fuente ───────────────────────────────────────────────
% Book Antiqua si está instalada; si no, TeX Gyre Pagella (clon métrico de
% Palatino/Book Antiqua, full Unicode para diacríticos pāli). Latin Modern
% como último recurso.
\IfFontExistsTF{Book Antiqua}{%
  \setmainfont{Book Antiqua}%
}{%
  \IfFontExistsTF{TeX Gyre Pagella}{%
    \setmainfont{TeX Gyre Pagella}%
  }{}%
}

% ── Partición de palabras ────────────────────────────────
% Sin patrones de pāli, XeLaTeX usaría los ingleses y partiría mal las palabras
% (p. ej. «Pāṭikav-aggo»). Se prohíbe inventar guiones y se permite cortar solo
% en los guiones de compuesto ya presentes; la justificación se resuelve
% estirando espacios.
\hyphenpenalty=10000
\exhyphenpenalty=100
\tolerance=2500
\setlength{\emergencystretch}{3em}

% ── Estilo de página ─────────────────────────────────────
\setlength{\parindent}{1.1em}
\pagestyle{fancy}
% Cabecera FIJA con el nombre de la obra (sin \leftmark/\rightmark, que la clase
% book contamina con «Contents» tras el índice). Número de página en el borde.
\fancyhf{}
\fancyhead[LE,RO]{\thepage}
\fancyhead[C]{\small\itshape RUNHEAD}
\renewcommand{\headrulewidth}{0.4pt}

% Las páginas en blanco insertadas para empezar en recto (openright) deben quedar
% realmente vacías, sin cabecera ni número.
\makeatletter
\renewcommand*{\cleardoublepage}{%
  \clearpage
  \if@twoside\ifodd\c@page\else
    \hbox{}\thispagestyle{empty}\newpage
    \if@twocolumn\hbox{}\newpage\fi
  \fi\fi}
\makeatother

% ── Marcador de página PTS (alineación con el impreso) ───
% Número de página del comentario PTS alineado a la DERECHA en gris claro, sin
% regla; marca dónde empieza cada página del impreso de forma discreta.
\definecolor{ptslabel}{gray}{0.55}
\newcommand{\ptspage}[1]{%
  \par\addvspace{0.45\baselineskip}\nointerlineskip
  {\footnotesize\color{ptslabel}\hfill #1\par}%
  \nobreak\noindent\ignorespaces}

% Marca de revisión: [?] delante de palabras que el DPD no reconoce (--mark-dpd)
\definecolor{dpdq}{gray}{0.55}
\newcommand{\dpdflag}{{\thinspace\scriptsize\color{dpdq}[?]}}

% ── Metadatos ────────────────────────────────────────────
\title{TITLE_PLACEHOLDER}
\author{Aṭṭhakathā — Edición PTS (texto romanizado)}
\date{}

\begin{document}
\frenchspacing
\maketitle
\tableofcontents
\clearpage
"""

TEX_FOOTER = r"""
\end{document}
"""


# ── Normalización del niggahīta (#7) ──────────────────────
# En pāli una palabra solo termina en vocal o en ṃ; el `m`/`n` final del
# impreso PTS antiguo es niggahīta. Se convierte a ṃ ante espacio o
# puntuación de cierre, NUNCA ante apóstrofo (elisión: mam' = mama).
_NIGGAHITA_RE = re.compile(r"([aiueoāīūeo])([mn])(?=[\s.,;:!?”\)\]]|$)")


def normalize_niggahita(text: str) -> str:
    return _NIGGAHITA_RE.sub(lambda m: m.group(1) + "ṃ", text)


# ── Enlace del aparato a sus lemas (#2) ───────────────────
_LETTER_CLASS = r"[^\W\d_]"  # cualquier letra Unicode (incl. diacríticos pāli)


def link_footnotes(text: str, notes: dict):
    """Sustituye los números de nota pegados a una palabra (`mayā1`) por un
    token que luego se expande a \\footnote. Solo actúa sobre números que
    existen en el aparato de la página, evitando falsos positivos.

    Devuelve (texto_con_tokens, conjunto_de_notas_usadas).
    """
    if not notes:
        return text, set()
    used = set()
    L = _LETTER_CLASS

    # Enmascarar folios [F.N] y secciones ║N║ para que sus dígitos no se
    # confundan con anclas de nota (\x10 se restaura antes de escapar).
    holds = []

    def _hold(m):
        holds.append(m.group())
        return "\x10"

    text = re.sub(r"\[F\.\d+[vr]?\]|║\d+║", _hold, text)

    # números más largos primero (que '1' no coincida dentro de '12')
    for n in sorted(notes, key=lambda x: -len(str(x))):
        token = f"\x00FN{n}\x00"
        # Anclas posibles de la nota n:
        #   · pegada al final de palabra      → `mayā1`
        #   · apertura de rango (tras espacio) → `,3yathā`
        #   · cierre de rango (tras puntuación)→ `pasaṃsito,3`
        pat = re.compile(
            rf"(?<={L}){n}(?![\d.])"
            rf"|(?<=\s){n}(?={L})"
            rf"|(?<=[,;:.”’\)]){n}(?=\s|$|[,;:.])"
        )
        cnt = [0]

        def _sub(m):
            cnt[0] += 1
            # primera aparición → nota; las demás son delimitadores de rango → fuera
            return token if cnt[0] == 1 else ""

        text = pat.sub(_sub, text)
        if cnt[0]:
            used.add(n)

    # restaurar folios/secciones en orden
    it = iter(holds)
    text = re.sub("\x10", lambda m: next(it), text)
    return text, used


# ── Escape LaTeX ──────────────────────────────────────────
# Centinelas privados (\x01–\x07) para proteger los marcadores que SÍ deben
# convertirse en comandos LaTeX, de modo que las llaves sueltas/no balanceadas
# del texto fuente se puedan escapar sin romper la sintaxis. \x00 delimita los
# tokens de nota al pie y también debe sobrevivir al filtrado.
_SENTINELS = "\x00\x01\x02\x03\x04\x05\x06\x07\x08"  # \x08 = marca DPD [?]


def escape_tex(text: str) -> str:
    """Escapa caracteres especiales de LaTeX y convierte marcadores.

    Robusto frente a llaves sueltas (`{` sin cierre) presentes en la fuente,
    que de otro modo romperían `\\section*{...}` u otros argumentos.
    """
    t = "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32 or ch in _SENTINELS)
    # 1. Proteger marcadores con centinelas ANTES de tocar las llaves
    t = t.replace("\\", "\x07")  # backslash literal → textbackslash al final
    t = re.sub(r"\{([^{}]*)\}", "\x01\\1\x02", t)  # {variante} → cursiva
    t = re.sub(r"\[F\.(\d+[vr]?)\]", "\x03\\1\x04", t)  # folio
    t = re.sub(r"║(\d+)║", "\x05\\1\x06", t)  # sección
    # 2. Escapar llaves literales restantes y demás caracteres especiales
    t = t.replace("{", "\\{").replace("}", "\\}")
    # Corchetes literales → {[} {]}: evita que un `[` tras `\\` (salto de verso)
    # se lea como argumento opcional `\\[dimen]`. Los folios ya van protegidos.
    t = t.replace("[", "{[}").replace("]", "{]}")
    for c in "&%#$_":
        t = t.replace(c, "\\" + c)
    t = t.replace("~", "\\textasciitilde{}").replace("^", "\\textasciicircum{}")
    # 3. Restaurar los marcadores como comandos LaTeX reales
    t = t.replace("\x07", "\\textbackslash{}")
    t = t.replace("\x01", "\\textit{").replace("\x02", "}")
    t = t.replace("\x03", "\\textsuperscript{[F.").replace("\x04", "]}")
    t = t.replace("\x05", "\\textsuperscript{\\textbf{").replace("\x06", "}}")
    t = t.replace("\x08", "\\dpdflag{}")  # marca de revisión [?]
    t = t.replace("—", "---").replace("–", "--")
    return t


# ── Siglas de manuscrito en el aparato → sufijo en superíndice ────────────
# Convención PTS: la sigla de un testigo es una letra-base con su sufijo
# (letra/dígito) en superíndice: Bm→B^m, B2→B², Sˢᵖ. NO hay marca en la fuente;
# es tipografía que se reconstruye. Para no estropear referencias de texto
# (Sp=Samantapāsādikā, Vin., Dhp., …) ni palabras (So, Cf, See…), se exige que
# la base sea una clase de testigo y se excluyen los tokens de NON_SIGLA.
# >>> Ambos conjuntos son REVISABLES según el prefacio de cada volumen PTS. <<<
MS_BASES = "BSCKDMVP"
# El sufijo de una sigla es un CLUSTER de subediciones consonánticas (S acumula:
# Scdg, Scdgh, Scgt…), o un dígito, o una vocal corta (Ca, Ba, Si). Como ninguna
# palabra pāli es solo-consonantes, los clusters no chocan con palabras; solo hay
# que excluir las referencias de TEXTO que también son consonánticas (Dhs, Spk…).
_SUB = "bcdghkmnpst"  # alfabeto de subediciones (consonantes minúsculas)
_SUBU = "BCDGHKMNPST"  # ídem en MAYÚSCULA (SK, SH, SM, BM…); sin I/V/X/L para no
#                        chocar con numerales romanos (VI, VII, XI, CC…)
NON_SIGLA = {
    # palabras (inglés del editor / pāli)
    "So",
    "See",
    "Be",
    "By",
    "Do",
    "Cf",
    "Ch",
    # abreviaturas de TEXTO / ediciones (no son manuscritos). Sp SÍ es sigla (Sᵖ);
    # NO confundir con Spk (Sāratthappakāsinī), que se mantiene excluido.
    "Sv",
    "Sn",
    "Sum",
    "Spk",
    "Ps",
    "Pj",
    "Pv",
    "Bv",
    "Cp",
    "Kkh",
    "Dh",
    "Dhp",
    "Dhs",
    "Mp",
    "Mil",
    "Vv",
    "Vbh",
    "Vism",
    "Vin",
    "Pit",
    "Pps",
    "Pts",
    "PTS",
    "Skt",
    "Khp",
    "Dpv",
    "MS",
    "MSS",  # +manuscript(s)
    # abreviaturas COLECTIVAS (letra-base duplicada = toda esa clase), no
    # base+superíndice:
    "SS",  # = todos los manuscritos cingaleses
    "BB",  # = todos los manuscritos birmanos
}
# base (mayúscula del set) + sufijo: cluster consonántico (minús. o MAYÚS.),
# vocal a/i, o dígitos
_SIGLUM_RE = re.compile(
    rf"\b([{MS_BASES}])((?:[{_SUB}]{{1,6}}|[{_SUBU}]{{1,3}}|[ai])\d{{0,2}}|\d{{1,2}})\b"
)


def superscript_sigla(t: str) -> str:
    """Pone en \\textsuperscript el sufijo de las siglas de manuscrito."""

    def _repl(m):
        base, suf = m.group(1), m.group(2)
        if not suf or (base + suf) in NON_SIGLA:
            return m.group(0)
        return f"{base}\\textsuperscript{{{suf}}}"

    return _SIGLUM_RE.sub(_repl, t)


def escape_apparatus(text: str) -> str:
    t = escape_tex(text).replace("\n", " ").strip()
    return superscript_sigla(t)


# Palabras-tipo con que terminan los títulos de sección pali (vaṇṇanā = comentario,
# vatthu = relato, niddeso = exposición, vaggo = capítulo, kathā/paricchedo…). Sirve
# para TODAS las familias de comentarios, sea el título en mayúscula (Dīgha-a, Vism),
# en minúscula entre corchetes (Majjhima-a) o numerado (Dhammapada-a), y de paso
# excluye versos y running headers (que terminan en nº de página).
# palabra-tipo final (con colofón opcional: «… niṭṭhitā/samattā» = fin de sección)
_TITLE_KW = (
    r"(?:vaṇṇanā|vaṇṇana|vatthu|niddeso|niddesa|paricchedo|kathā|vagg[oa]|"
    r"kaṇḍaṃ|kaṇḍo|bhāṇavāro)"
)
_COLOPHON = r"(?:niṭṭhit[āoaṃ]+|samatt[āoaṃ]+|samāptā)"
# tras la palabra-tipo/colofón puede ir pegado un nº de nota (p. ej. «niṭṭhitā.10»)
_TITLE_END = re.compile(
    rf"{_TITLE_KW}(?:\s+{_COLOPHON})?\.?\d{{0,3}}[.\]\)\s]*$", re.IGNORECASE
)
_COLOPHON_TAIL = re.compile(rf"\s+{_COLOPHON}\.?$", re.IGNORECASE)
# referencia de nikāya en la cornisa (p. ej. 'D. I.' 'M. II.') → no es título
_NIKAYA_REF = re.compile(r"\b[A-Z]\.\s*[IVXLC]+\.")


def is_title_line(line: str) -> bool:
    """¿Es esta línea del CUERPO un título de sección pali genuino?

    Los títulos reales aparecen CENTRADOS y terminan en una palabra-tipo
    (`…-VAṆṆANĀ`, `[… vaṇṇanā]`, `N. …-vatthu`). NO vienen del `head` (la cornisa
    del impreso, con rótulos en inglés y la referencia `[D. I. 1.`).
    """
    s = line.strip()
    if not (5 <= len(s) <= 80):
        return False
    if (len(line) - len(line.lstrip(" "))) < 8:  # debe ir centrado/sangrado
        return False
    if _NIKAYA_REF.search(s):  # es una cornisa, no un título
        return False
    return bool(_TITLE_END.search(s))


def clean_title(t: str) -> str:
    """Limpia el título para la sección/ToC: corchetes, colofón final, punto."""
    t = t.strip().strip("[]() ").rstrip(" .")
    t = re.sub(r"\.?\d{1,3}$", "", t).rstrip(" .")  # nº de nota pegado al final
    t = _COLOPHON_TAIL.sub("", t)  # quita «niṭṭhitā»/«samattā» del colofón
    return t.rstrip(" .")


def title_key(t: str) -> str:
    """Clave normalizada (solo letras, mayúsculas) para deduplicar títulos."""
    return re.sub(r"[^A-Za-zĀāĪīŪūṄṅÑñṬṭḌḍṆṇḶḷṂṃ]", "", t).upper()


# Palabras que delatan portada (inglés del editor) u homenaje — no son secciones.
_FRONTMATTER = {
    "THE",
    "OF",
    "FOR",
    "BY",
    "AND",
    "ON",
    "IN",
    "EDITED",
    "PUBLISHED",
    "LONDON",
    "OXFORD",
    "SOCIETY",
    "PRESS",
    "VOL",
    "PART",
    "COMMENTARY",
    "UNIVERSITY",
    "TRANSLATED",
    "INTRODUCTION",
    "PREFACE",
    "CONTENTS",
    "MA",
    "NAMO",
    "TASSA",
    "BHAGAVATO",
    "ARAHATO",
    "SAMMĀSAMBUDDHASSA",
    "SAMBUDDHASSA",
    "NĀMA",
}


def looks_frontmatter(t: str) -> bool:
    words = re.findall(r"[A-ZĀĪŪṄÑṬḌṆḶṂ]+", t.upper())
    return any(w in _FRONTMATTER for w in words)


# ── Composición del cuerpo: prosa vs verso (#3) ───────────
def render_body(text: str, notes: dict, normalize: bool, flagger=None) -> str:
    """Devuelve el cuerpo de una página en LaTeX, distinguiendo prosa y verso.

    Heurística de verso: en la fuente las líneas de gāthā van sangradas (≥3
    espacios); la prosa empieza en la columna 0. Una línea no sangrada que
    precede a una sangrada y empieza por 'N.' se trata también como verso
    (primer pāda de la estrofa).

    Si `flagger` está dado, POSPONE una marca [?] a cada palabra que el DPD no
    reconoce (centinela \x08 → \dpdflag en escape_tex).
    """
    if normalize:
        text = normalize_niggahita(text)
    if flagger is not None:
        text = re.sub(
            r"\S+",
            lambda m: (m.group() + "\x08") if flagger(m.group()) else m.group(),
            text,
        )
    text, used = link_footnotes(text, notes)

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    raw = text.split("\n")
    indents = [len(l) - len(l.lstrip(" ")) for l in raw]
    is_verse = [bool(l.strip()) and ind >= 3 for l, ind in zip(raw, indents)]
    for i, l in enumerate(raw):
        if l.strip() and not is_verse[i] and i + 1 < len(raw) and is_verse[i + 1]:
            if re.match(r"^\s*\d+\.", l):
                is_verse[i] = True

    blocks = []  # (mode, [lines])
    mode = None
    buf = []

    def flush():
        nonlocal buf, mode
        if buf:
            blocks.append((mode, buf))
            buf = []

    for i, l in enumerate(raw):
        s = l.strip()
        if not s:
            flush()
            mode = None
            continue
        m = "verse" if is_verse[i] else "prose"
        if mode and m != mode:
            flush()
        mode = m
        buf.append(s)
    flush()

    # Un único renglón sangrado y largo casi nunca es gāthā: suele ser una
    # glosa en prosa sangrada. Se reclasifica como prosa.
    blocks = [
        ("prose", ls) if k == "verse" and len(ls) == 1 and len(ls[0]) > 70 else (k, ls)
        for k, ls in blocks
    ]

    out = []
    for kind, lines in blocks:
        if kind == "verse":
            # El `{}` sella el salto de verso: impide que un `*` o `[` al inicio
            # del pāda siguiente se lea como `\\*` / `\\[dimen]`.
            esc = [escape_tex(ln) for ln in lines]
            out.append("\\begin{verse}\n" + " \\\\{}\n".join(esc) + "\n\\end{verse}")
        else:
            out.append(escape_tex(" ".join(lines)))
    body = "\n\n".join(out)

    # Expandir tokens de nota → \footnote[n]{...}. El número EXPLÍCITO es el del
    # aparato original (que ya reinicia en 1 cada página PTS); al usar siempre el
    # argumento opcional, el contador automático no avanza y no se acumulan miles.
    for n in used:
        note_tex = escape_apparatus(notes[n])
        body = body.replace(f"\x00FN{n}\x00", f"\\footnote[{n}]{{{note_tex}}}")
    return body


def generate_tex(
    json_path: str, output_dir: str = None, normalize: bool = True, flagger=None
):
    with open(json_path, encoding="utf-8") as f:
        book = json.load(f)

    bn = book["book_no"]
    total = book["total_pages"]
    pages = book["pages"]
    title = book.get("name") or book_title(bn)
    # Cornisa: SOLO el nombre de la obra (sin sigla/volumen construidos).
    runhead = book.get("work") or book.get("name") or book_title(bn)

    out_dir = Path(output_dir) if output_dir else Path(json_path).parent
    tex_path = out_dir / f"book_{bn:02d}.tex"
    print(f"  {Path(json_path).name} → {tex_path.name}  ({total} págs)")

    with open(tex_path, "w", encoding="utf-8") as f:
        preamble = (
            TEX_PREAMBLE.replace("TITLE_PLACEHOLDER", escape_tex(title))
            .replace("PDF_TITLE", escape_tex(title))
            .replace("RUNHEAD", escape_tex(runhead))
        )
        f.write(preamble)

        # Las secciones salen de los TÍTULOS PALI del cuerpo (centrados, en
        # mayúscula), NO del `head` (cornisa del impreso con rótulos en inglés).
        seen = set()
        work_key = title_key(book.get("work", ""))
        name_key = title_key(book.get("name", ""))

        def skip_title(t: str) -> bool:
            # clave sobre el título YA LIMPIO, para que el inicio de sección y su
            # colofón («X-vaṇṇanā» y «X-vaṇṇanā niṭṭhitā») se dedupliquen entre sí.
            k = title_key(clean_title(t))
            if len(k) < 4 or k in seen:
                return True
            # Un título pali genuino lleva algún diacrítico pali; las líneas de
            # portada en inglés (editor, ciudad, editorial) no → se descartan.
            if not any(c in "āīūṅñṭḍṇḷṃĀĪŪṄÑṬḌṆḶṂ" for c in t):
                return True
            if looks_frontmatter(t):  # homenaje (NAMO TASSA … SAMMĀSAMBUDDHASSA)
                return True
            # Título de la OBRA (no es una sección): coincidencia exacta con el
            # nombre canónico, o termina en «-(a)ṭṭhakathā». NO se filtra por
            # subcadena del mūla (rompería secciones de p. ej. Niddesa-a).
            if k in (work_key, name_key):
                return True
            if work_key and len(work_key) >= 8 and k[:8] == work_key[:8]:
                return True
            if clean_title(t).lower().endswith("ṭṭhakathā"):
                return True
            return False

        def emit_section(raw: str):
            seen.add(title_key(clean_title(raw)))
            t = escape_tex(clean_title(raw))
            f.write(f"\n\\section*{{{t}}}\n")
            f.write(f"\\addcontentsline{{toc}}{{section}}{{{t}}}\n")

        for i, page in enumerate(pages):
            pn = page["page"]
            text = page.get("text", "")
            notes = {int(k): v for k, v in (page.get("notes") or {}).items()}

            # Marcador de página PTS: SOLO el número de página del comentario PTS
            # (el que viene en la BD). No se inventa sigla/volumen.
            f.write(f"\n\\ptspage{{PTS {pn}}}")

            # Recorre las líneas; al hallar un título pali genuino, lo saca del
            # flujo del cuerpo y emite una sección + entrada de índice.
            buf = []
            for ln in text.split("\n"):
                if is_title_line(ln) and not skip_title(ln):
                    if buf:
                        f.write(render_body("\n".join(buf), notes, normalize, flagger))
                        f.write("\n\n")
                        buf = []
                    emit_section(ln.strip())
                    continue
                buf.append(ln)
            if buf:
                f.write(render_body("\n".join(buf), notes, normalize, flagger))
            f.write("\n\n")

            if (i + 1) % 100 == 0:
                print(f"    {i + 1}/{total} páginas")

        f.write(TEX_FOOTER)

    print(f"    ✓ {tex_path}")


if __name__ == "__main__":
    import glob

    args = sys.argv[1:]
    normalize = True
    if "--diplomatic" in args:
        normalize = False
        args.remove("--diplomatic")

    # --mark-dpd: antepone [?] a las palabras que el DPD no reconoce (proofreading)
    flagger = None
    if "--mark-dpd" in args:
        args.remove("--mark-dpd")
        import importlib

        import validate_text

        importlib.reload(validate_text)
        from validate_text import _ROMAN, Checker, clean_token, load_keys

        print("cargando DPD para marcado [?]…", flush=True)
        _chk = Checker(load_keys("/dev/shm/dpd.db"))

        # Cargar palabras del Mahāsaṅgīti (edición meticulosamente curada)
        ms_path = "/dev/shm/ms_words.txt"
        if Path(ms_path).exists():
            _ms_words = set(Path(ms_path).read_text(encoding="utf-8").splitlines())
        else:
            _ms_words = set()

        def flagger(tok):
            if "{" in tok or "«" in tok or tok.startswith("--"):
                return False
            t = clean_token(tok)
            if len(t) < 2 or _ROMAN.match(t) or any(c.isdigit() for c in t):
                return False
            if _chk.resolve(t):
                return False
            # elisión: probar restaurando vocal final (ath → atha)
            if any(t + v in _chk.K for v in "aāiīuūeo"):
                return False
            # guiones PTS: probar sin ellos
            if "-" in t and _chk.resolve(t.replace("-", "")):
                return False
            if t in _ms_words:
                return False
            if t[-1] in "mnñṅ" and t[:-1] + "ṃ" in _ms_words:
                return False
            return True

        print(f"  {len(_chk.K):,} formas DPD, {len(_ms_words):,} MS\n")

    files = args if args else sorted(glob.glob("rotb_commentary/book_*.json"))
    print(
        f"Generando {len(files)} archivos .tex"
        f"{'' if normalize else ' (modo diplomático)'}"
        f"{' (con marca DPD [?])' if flagger else ''}\n"
    )
    for fp in files:
        try:
            generate_tex(fp, normalize=normalize, flagger=flagger)
        except Exception as e:
            print(f"  ERROR en {fp}: {e}")

    print("\nPara compilar:")
    print("  xelatex book_09.tex   (×2 para el índice)")
