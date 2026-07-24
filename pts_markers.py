#!/usr/bin/env python3
"""
pts_markers — per-Nikāya sutta-start marker grammars for the PTS canon (edition='mula').

Parsing of the page-line format uses **pyparsing** exclusively (project rule; grammar in
docs/grammar.md, best practices in doc/pyparsing/pyparsing/ai/best_practices.md). No regex is
used for format analysis here.

Each `find_markers_*(text)` returns a list of `(line_no, tag)` for the lines that start a sutta
(1-based line numbers), matching the previous regex behaviour exactly (verified by an
equivalence test over every real page — see scratchpad/dev_markers.py).
"""
import pyparsing as pp

# Line-oriented format: newlines are significant, so only spaces/tabs are skippable.
pp.ParserElement.set_default_whitespace_chars(" \t")

# ── Primitive tokens ────────────────────────────────────────────────────────────
_num = pp.Word(pp.nums).set_name("num")               # a run of digits  (regex \d+)
_dot = pp.Literal(".").set_name("dot")
_sp = pp.White(" \t").set_name("ws")                  # REQUIRED whitespace (regex \s+)
_nonspace = pp.CharsNotIn(" \t", exact=1).set_name("nonspace")   # one non-space char (regex \S)

# "evam ... sutam" with the *same* char classes the old regex used ([Ee], [mM]) — this
# deliberately does NOT match the diacritic "ṃ" (so "Evam me sutaṃ" is NOT matched, exactly
# as the legacy regex `[Ee]va[mM].*suta[mM]` behaved).
_evam = pp.Combine(pp.Char("Ee") + "va" + pp.Char("mM")).set_name("evam")
_sutam = pp.Combine("suta" + pp.Char("mM")).set_name("sutam")
_evam_sutam = (_evam + pp.SkipTo(_sutam) + _sutam).set_name("evam_sutam")  # searched, not anchored

# ── Anchored line patterns (used with .matches, i.e. must match from line start) ──
# DN: number(.number)?.?  <ws>  evam        e.g. "1.1. Evam" / "1. Evam"
# The numeric prefix is a Combine so the optional inner digits/dot don't consume the
# whitespace that the required <ws> must see next.
_dn_evam_num = (pp.Combine(_num + _dot + pp.Opt(_num) + pp.Opt(_dot))
                + _sp + _evam).set_name("dn_evam_num")
# DN title fallback: lowercase roman numeral + optional dot + ws + content
_dn_title = (pp.Combine(pp.Word("ivxlc") + pp.Opt(_dot))("roman")
             + _sp + _nonspace).set_name("dn_title")

# MN: a line that is ONLY a number and optional dot (the sutta number on its own line)
_mn_num_only = (_num + pp.Opt(_dot)).set_name("mn_num_only")
# number + dot + ws + content   (regex ^\d+\.\s+\S) — shared by MN/SN/AN/KN
_num_dot_txt = (pp.Combine(_num + _dot) + _sp + _nonspace).set_name("num_dot_txt")

# SN: global-id marker "N (M)" / "N. (M)"   (regex ^\d+\.?\s*\(\d+)
_sn_id = (_num + pp.Opt(_dot) + pp.Literal("(") + _num).set_name("sn_id")
# SN section marker "§ N"   (regex ^§\s+\d+)
_sn_section = (pp.Literal("§") + _sp + _num).set_name("sn_section")

# KN Thag/Thig verse-end marker "║ N ║"   (regex [║]\s*\d+\s*[║], searched)
_verse_end = (pp.Literal("║") + _num + pp.Literal("║")).set_name("verse_end")

# "all-caps / punctuation only" line detectors (header lines to skip); parse_all → whole line.
_allcaps = pp.Word(pp.alphas.upper() + " \t-.║").set_name("allcaps")
_allcaps_pipe = pp.Word(pp.alphas.upper() + " \t-.║|").set_name("allcaps_pipe")


def _matches(expr, s, parse_all=False):
    return expr.matches(s, parse_all=parse_all)


def _found(expr, s):
    """True if `expr` matches anywhere in `s` (regex-search semantics)."""
    return next(expr.scan_string(s), None) is not None


# ── Per-Nikāya finders ───────────────────────────────────────────────────────────
def find_markers_dn(text):
    """DN: content-start lines (evam / numbered-evam), else title-line fallback."""
    lines = text.split("\n")
    markers = []
    for i, line in enumerate(lines):
        s = line.strip()
        if _found(_evam_sutam, s):
            markers.append((i + 1, "evam"))
        elif _matches(_dn_evam_num, s):
            markers.append((i + 1, "evam_num"))
    if not markers:
        for i, line in enumerate(lines):
            s2 = line.strip().lstrip("[").rstrip("]").strip().lower()
            if _matches(_dn_title, s2):
                markers.append((i + 1, "title"))
    return markers


def find_markers_mn(text):
    lines = text.split("\n")
    markers = []
    for i, line in enumerate(lines):
        s = line.strip()
        if len(s) <= 5 and _matches(_mn_num_only, s, parse_all=True):
            markers.append((i + 1, "num"))
        elif _matches(_num_dot_txt, s):
            markers.append((i + 1, "num_txt"))
    return markers


def find_markers_sn(text):
    lines = text.split("\n")
    markers = []
    for i, line in enumerate(lines):
        s = line.strip()
        if _matches(_sn_id, s):
            markers.append((i + 1, "sn_id"))
        elif _matches(_sn_section, s):
            markers.append((i + 1, "section"))
        elif len(s) > 5 and _matches(_num_dot_txt, s):
            markers.append((i + 1, "num"))
    return markers


def find_markers_an(text):
    lines = text.split("\n")
    markers = []
    for i, line in enumerate(lines):
        s = line.strip()
        if _matches(_num_dot_txt, s):
            markers.append((i + 1, "num"))
    return markers


def find_markers_kn(text, vol):
    lines = text.split("\n")
    markers = []

    # Thag/Thig: ║N║ verse-end markers, else first content line
    if vol in ("Th", "Th & Th", "Thi", "Thī"):
        for i, line in enumerate(lines):
            if _found(_verse_end, line):
                markers.append((i + 1, "verse_end"))
        if not markers:
            for i, line in enumerate(lines):
                s = line.strip()
                if s and len(s) >= 8 and not _matches(_allcaps, s, parse_all=True):
                    markers.append((i + 1, "content"))
                    break
        return markers

    # Ud/It/Sn/Dh/Kh/Vv/Pv: numbered markers and evam me sutam
    for i, line in enumerate(lines):
        s = line.strip()
        if _matches(_num_dot_txt, s):
            markers.append((i + 1, "num"))
        elif _found(_evam_sutam, s):
            markers.append((i + 1, "evam"))

    # Ja/Ap/Bv/Cp/Patis/Nidd: numbered markers (only if nothing found above)
    if not markers:
        for i, line in enumerate(lines):
            s = line.strip()
            if _matches(_num_dot_txt, s):
                markers.append((i + 1, "num"))

    # Fallback: first content line
    if not markers:
        for i, line in enumerate(lines):
            s = line.strip()
            if s and len(s) >= 6 and not _matches(_allcaps_pipe, s, parse_all=True):
                markers.append((i + 1, "content"))
                break

    return markers


if __name__ == "__main__":
    # Mini validation with pyparsing's run_tests (best-practices §Testing: valid inputs only).
    # Prefix expressions match from the start but need not consume the whole line → parse_all=False.
    print("── _sn_id ──")
    _sn_id.run_tests([
        "1 (1) Aniccam       # global id, no dot",
        "2 (2) Dukkham",
        "12. (3) Foo         # with dot after id",
    ], parse_all=False)
    print("── _num_dot_txt ──")
    _num_dot_txt.run_tests(["82. Bhikkhu"], parse_all=False)
    print("── _mn_num_only (whole line) ──")
    _mn_num_only.run_tests(["1.", "82"], parse_all=True)
    print("── _dn_evam_num ──")
    _dn_evam_num.run_tests([
        "1.1. Evam me        # numbered (vagga.sutta)",
        "1. Evam             # single number",
    ], parse_all=False)
    print("── _sn_section ──")
    _sn_section.run_tests(["§ 1 Foo"], parse_all=False)
