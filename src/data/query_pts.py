#!/usr/bin/env python3
"""
query_pts.py — Query tipitaka.sqlite by standard PTS citation.

Usage
-----
    python query_pts.py "M I 3"
    python query_pts.py "S I 100" -a
    python query_pts.py "D II 50"
    python query_pts.py "Sn 25" --apparatus
    python query_pts.py --list            # print all supported abbreviations

Options
-------
    -a, --apparatus   Show the apparātus criticus (manuscript variants)
    -l, --list        List all supported book abbreviations and exit

Citation format
---------------
    <abbreviation> [<volume>] <page>

    The abbreviation follows the standard PTS (Pali Text Society) convention:
      Vin (I–V)   D (I–III)   M (I–III)   S (I–V)    A (I–V)
      Khp  Dhp  Ud  It  Sn  Vv  Pv  Th  Thī  Ja (I–VI)
      Nidd (I–II)  Patis (I–II)  Ap  Bv  Cp
      Dhs  Vibh  Dhtk  Pp  Kv  Yam (I–II)  Pat (I–III)

    Abbreviations are case-insensitive.  Both "M" and "MN" work for
    Majjhima Nikāya; both "S" and "SN" work for Saṃyutta Nikāya, etc.

Database background
-------------------
    The database contains the ROTA edition (Syāmaraṭṭha-Tipiṭaka,
    Dhammakaya Foundation).  ROTA page numbers differ from the London
    PTS page numbers, but the volume structure and approximate page ranges
    are the same.  The page number in a citation is therefore interpreted
    as a ROTA page within the specified volume.

    Key tables used here:
      • Dbf1__palipg  — one row per page; columns BOOKNUM, RPAGENUM, UNITEXT
      • Dbf1__footpg  — one row per page apparatus; linked via BOOK+PAGE keys
      • Dbf1__book    — book metadata (BOOK_NO, S_NAME)

    The UNITEXT column is stored as BOM + Base64(UTF-8).  See decode() below.

Apparatus criticus
------------------
    Hidden by default.  Activate with -a / --apparatus.
    Manuscript sigla used in the apparatus:
      Cb = Cambridge  ·  Ba = Bangkok A  ·  Bai = Bangkok B
      Bi = Burmese   ·  Ck = Colombo    ·  Fsb = Fausbøll
"""

import sys
import re
import base64
import sqlite3

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Path to the SQLite database produced by dbf2sqlite.py.
# Change this if you move the database elsewhere.
DB = "/home/jorge/Code/ptsdb/PaliText-V2.5-Dhammakaya-Foundation/tipitaka.sqlite"

# ---------------------------------------------------------------------------
# Roman numeral helpers
# ---------------------------------------------------------------------------

# Map from uppercase Roman numeral string → integer.
# Used to parse the volume part of a citation like "S IV 100".
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}

# Reverse mapping (integer → Roman numeral string).
# Used to generate human-readable error messages.
ROMAN_INV = {v: k for k, v in ROMAN.items()}

# ---------------------------------------------------------------------------
# Book map: (normalized_abbreviation, volume_int) → BOOK_NO
#
# BOOK_NO is the integer primary key stored in Dbf1__book.BOOK_NO and used
# as Dbf1__palipg.BOOKNUM.  It uniquely identifies one physical volume.
#
# The key is a tuple:
#   abbr  — lowercase abbreviation string (e.g. "m", "sn", "dhp")
#   vol   — integer volume number (1–6), or 0 for works without volumes
#
# Multiple abbreviations can map to the same BOOK_NO (aliases).
# For example ("m", 1) and ("mn", 1) both map to BOOK_NO=9 (Majjhima I).
# ---------------------------------------------------------------------------

BOOK_MAP: dict[tuple[str, int], int] = {
    # ── Vinaya Piṭaka ────────────────────────────────────────────────────
    ("vin", 1): 1,   # Pārājika
    ("vin", 2): 2,   # Pācittiya
    ("vin", 3): 3,   # Mahāvagga
    ("vin", 4): 4,   # Cūḷavagga
    ("vin", 5): 5,   # Parivāra

    # ── Dīgha Nikāya ─────────────────────────────────────────────────────
    ("d",  1): 6,  ("dn", 1): 6,
    ("d",  2): 7,  ("dn", 2): 7,
    ("d",  3): 8,  ("dn", 3): 8,

    # ── Majjhima Nikāya ──────────────────────────────────────────────────
    ("m",  1): 9,  ("mn", 1): 9,
    ("m",  2): 10, ("mn", 2): 10,
    ("m",  3): 11, ("mn", 3): 11,

    # ── Saṃyutta Nikāya ──────────────────────────────────────────────────
    ("s",  1): 12, ("sn", 1): 12,
    ("s",  2): 13, ("sn", 2): 13,
    ("s",  3): 14, ("sn", 3): 14,
    ("s",  4): 15, ("sn", 4): 15,
    ("s",  5): 16, ("sn", 5): 16,

    # ── Aṅguttara Nikāya ─────────────────────────────────────────────────
    ("a",  1): 17, ("an", 1): 17,
    ("a",  2): 18, ("an", 2): 18,
    ("a",  3): 19, ("an", 3): 19,
    ("a",  4): 20, ("an", 4): 20,
    ("a",  5): 21, ("an", 5): 21,

    # ── Khuddaka Nikāya (no volume number) ───────────────────────────────
    ("khp", 0): 22,                  # Khuddakapāṭha
    ("dhp", 0): 23,                  # Dhammapada
    ("ud",  0): 24,                  # Udāna
    ("it",  0): 25,                  # Itivuttaka
    ("snp", 0): 26, ("sn", 0): 26,  # Sutta Nipāta  (bare "Sn" without vol)
    ("vv",  0): 27,                  # Vimānavatthu
    ("pv",  0): 28,                  # Petavatthu
    ("th",  0): 29,                  # Theragāthā
    ("thī", 0): 30, ("thi", 0): 30, # Therīgāthā

    # ── Jātaka ───────────────────────────────────────────────────────────
    # Note: Ja I (BOOK_NO=31) is missing from the database; Ja starts at II.
    ("ja", 1): 31, ("ja", 2): 32, ("ja", 3): 33,
    ("ja", 4): 34, ("ja", 5): 35, ("ja", 6): 36,

    # ── Abhidhamma Piṭaka & late Khuddaka ────────────────────────────────
    ("nidd",  1): 37, ("nidd",  2): 38,  # Niddesa I–II
    ("patis", 1): 39, ("patis", 2): 40,  # Paṭisambhidāmagga I–II
    ("ap",    0): 41,                    # Apadāna
    ("bv",    0): 42,                    # Buddhavaṃsa
    ("cp",    0): 43,                    # Cariyāpiṭaka
    ("dhs",   0): 44,                    # Dhammasaṅgaṇī
    ("vibh",  0): 45,                    # Vibhaṅga
    ("dhtk",  0): 46, ("dhntk", 0): 46, # Dhātukathā
    ("pp",    0): 47,                    # Puggalapaññatti
    ("kv",    0): 48,                    # Kathāvatthu
    ("yam",   1): 49, ("yam",   2): 50, # Yamaka I–II
    ("pat",   1): 51, ("pat",   2): 52, ("pat", 3): 53,  # Paṭṭhāna I–III
}

# Human-readable label for each BOOK_NO, used in the output header.
BOOK_LABEL: dict[int, str] = {
    1:  "Vin I",    2:  "Vin II",   3:  "Vin III",  4:  "Vin IV",   5:  "Vin V",
    6:  "D I",      7:  "D II",     8:  "D III",
    9:  "M I",      10: "M II",     11: "M III",
    12: "S I",      13: "S II",     14: "S III",    15: "S IV",     16: "S V",
    17: "A I",      18: "A II",     19: "A III",    20: "A IV",     21: "A V",
    22: "Khp",      23: "Dhp",      24: "Ud",       25: "It",       26: "Sn",
    27: "Vv",       28: "Pv",       29: "Th",       30: "Thī",
    31: "Ja I",     32: "Ja II",    33: "Ja III",   34: "Ja IV",    35: "Ja V",    36: "Ja VI",
    37: "Nidd I",   38: "Nidd II",  39: "Patis I",  40: "Patis II",
    41: "Ap",       42: "Bv",       43: "Cp",
    44: "Dhs",      45: "Vibh",     46: "Dhtk",     47: "Pp",       48: "Kv",
    49: "Yam I",    50: "Yam II",
    51: "Paṭṭh I",  52: "Paṭṭh II", 53: "Paṭṭh III",
}

# ---------------------------------------------------------------------------
# UNITEXT / FOOTNOTE decoder
# ---------------------------------------------------------------------------

def decode(val: str | None) -> str:
    """Decode a UNITEXT or footnote column value from tipitaka.sqlite.

    All text columns (UNITEXT in palipg, footpg, etc.) are stored using a
    two-layer encoding applied by the original VFP9 application:

        1. The Pali text is encoded as UTF-8 bytes.
        2. A UTF-8 BOM (0xEF 0xBB 0xBF) is prepended to those bytes.
        3. The combined byte string is Base64-encoded and stored as ASCII.

    To reverse this:
        a. Base64-decode the string value.
        b. Strip the leading 3-byte BOM.
        c. Decode the remaining bytes as UTF-8.

    The HEAD field in palipg is a plain UTF-8 string (not Base64-encoded).
    The try/except handles this transparently: if decoding fails, the raw
    string is returned unchanged.

    Args:
        val: Value from a UNITEXT-type column, or None.

    Returns:
        Decoded Unicode string, or "" for None/empty input.
    """
    if not val:
        return ""
    try:
        # Base64 padding: SQLite values may lack trailing '=' characters.
        # Adding "==" is always safe — base64 ignores redundant padding.
        raw = base64.b64decode(val.strip() + "==")

        # Strip the BOM (three bytes: 0xEF 0xBB 0xBF).
        if raw[:3] == b"\xef\xbb\xbf":
            raw = raw[3:]

        return raw.decode("utf-8", errors="replace")
    except Exception:
        # Not Base64 (e.g. the HEAD field) — return as plain UTF-8 string.
        return val

# ---------------------------------------------------------------------------
# PTS citation parser
# ---------------------------------------------------------------------------

def parse_citation(citation: str) -> tuple[str, int, int] | None:
    """Parse a PTS-style citation string into (abbreviation, volume, page).

    Supports three formats:
      1. Three-token with Roman volume:  "M I 3"  →  ("m", 1, 3)
      2. Two-token without volume:       "Sn 25"  →  ("sn", 0, 25)
      3. Dot/comma-delimited fallback:   "M.I.3"  →  ("m", 1, 3)

    Volume 0 is the sentinel for works that have no volume division
    (Dhp, Sn, Khp, etc.).

    Args:
        citation: Raw citation string, e.g. "S IV 100" or "Dhp 1".

    Returns:
        Tuple (abbr_lower, volume_int, page_int), or None if unparseable.

    Examples:
        >>> parse_citation("M I 3")
        ('m', 1, 3)
        >>> parse_citation("Sn 25")
        ('sn', 0, 25)
        >>> parse_citation("S.IV.100")
        ('s', 4, 100)
    """
    parts = citation.strip().split()
    if not parts:
        return None

    abbr = parts[0].lower()

    # Format 1: <abbr> <ROMAN_VOL> <page>
    if len(parts) == 3 and parts[1].upper() in ROMAN:
        try:
            return abbr, ROMAN[parts[1].upper()], int(parts[2])
        except ValueError:
            return None

    # Format 2: <abbr> <page>  (works without a volume, e.g. "Sn 25")
    if len(parts) == 2:
        try:
            return abbr, 0, int(parts[1])
        except ValueError:
            return None

    # Format 3: dot/comma-delimited, e.g. "M.I.3" or "M.I,3"
    # The character class covers standard Pali diacritic letters used in abbrs.
    m = re.match(
        r"^([a-zA-Zāṃṭḍñḷṇśūī]+)\.?([ivxIVX]+)\.?,?(\d+)$",
        citation.replace(" ", ""),
    )
    if m:
        abbr = m.group(1).lower()
        vol_str = m.group(2).upper()
        if vol_str in ROMAN:
            return abbr, ROMAN[vol_str], int(m.group(3))

    return None

# ---------------------------------------------------------------------------
# Main query function
# ---------------------------------------------------------------------------

def query(citation: str, show_apparatus: bool = False) -> None:
    """Fetch and display a single ROTA page identified by a PTS citation.

    Workflow:
      1. Parse the citation string to (abbr, volume, page).
      2. Look up the corresponding BOOK_NO in BOOK_MAP.
      3. Query Dbf1__palipg for the row where BOOKNUM=book_no AND
         RPAGENUM=page AND _deleted=0.
      4. Decode the UNITEXT column (BOM+Base64 → UTF-8).
      5. Query Dbf1__footpg for the apparatus criticus on the same page.
         The join key is the pair (BOOK, PAGE) — two single-character fields
         that encode the book and page as offset keys in the original VFP9
         database.  These are NOT the same as BOOKNUM/RPAGENUM.
      6. Print the page text, then optionally the apparatus.

    Inline footnote numbers:
      The UNITEXT contains Arabic digits inline in the text that serve as
      superscript references into the apparatus, e.g. "taṃ2 nipako8".
      When the apparatus is not shown, these digits are stripped with a
      lookbehind regex so that numbers that are part of valid content
      (standalone numerals, verse numbers) are preserved.

    Args:
        citation:       PTS-style citation string, e.g. "M I 3" or "Sn 25".
        show_apparatus: If True, print the full apparatus criticus after the
                        page text.  If False, print only a count notice.
    """
    # ── Step 1: parse the citation ─────────────────────────────────────────
    parsed = parse_citation(citation)
    if parsed is None:
        print(f"[!] Unrecognised citation: {citation!r}")
        print("    Expected format: 'M I 3'  'S IV 100'  'Sn 25'  'Dhp 1'")
        return

    abbr, vol, page = parsed

    # ── Step 2: resolve BOOK_NO ────────────────────────────────────────────
    book_no = BOOK_MAP.get((abbr, vol))
    if book_no is None:
        # Give a helpful error: check whether the abbreviation is valid at all
        # and whether the user merely forgot / mistyped the volume number.
        candidates = [(a, v) for (a, v) in BOOK_MAP if a == abbr]
        if candidates:
            vols = sorted({v for _, v in candidates if v > 0})
            if vols:
                print(
                    f"[!] '{abbr.upper()}' requires a volume number "
                    f"(I–{ROMAN_INV[max(vols)]}).  "
                    f"Example: '{abbr.upper()} I {page}'"
                )
            else:
                print(
                    f"[!] '{abbr.upper()}' has no volume.  "
                    f"Example: '{abbr.upper()} {page}'"
                )
        else:
            print(f"[!] Unknown abbreviation: '{abbr}'.  Use --list for options.")
        return

    label = BOOK_LABEL.get(book_no, f"Book {book_no}")

    # ── Step 3: query the page ─────────────────────────────────────────────
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # BOOKNUM  = integer book identifier (matches BOOK_MAP values / BOOK_NO)
    # RPAGENUM = readable page number within the volume (the one users cite)
    # UNITEXT  = BOM+Base64-encoded page text
    # BOOK, PAGE = single-character offset keys used to link palipg ↔ footpg
    #   (these are VFP9 legacy keys; do not use them for direct page lookup)
    cur.execute(
        """
        SELECT BOOKNUM, RPAGENUM, UNITEXT, BOOK, PAGE
        FROM Dbf1__palipg
        WHERE BOOKNUM = ? AND RPAGENUM = ? AND _deleted = 0
        """,
        (book_no, page),
    )
    row = cur.fetchone()

    if row is None:
        # Page is out of range for this volume — show the valid range.
        cur.execute(
            """
            SELECT MIN(RPAGENUM), MAX(RPAGENUM)
            FROM Dbf1__palipg
            WHERE BOOKNUM = ? AND _deleted = 0
            """,
            (book_no,),
        )
        minp, maxp = cur.fetchone()
        print(f"[!] Page {page} is out of range for {label}.")
        print(f"    Available ROTA page range: {minp}–{maxp}")
        con.close()
        return

    booknum, rpagenum, unitext, book_char, page_char = row

    # ── Step 4: decode the page text ──────────────────────────────────────
    text = decode(unitext)

    # ── Step 5: fetch the apparatus criticus ──────────────────────────────
    # Dbf1__footpg stores one apparatus row per page, linked to palipg via
    # the legacy offset-key pair (BOOK, PAGE).  Both are single characters
    # whose ordinal value encodes position within the original .DBF file.
    # We always need them to join across tables; do not try to compute them.
    cur.execute(
        """
        SELECT UNITEXT
        FROM Dbf1__footpg
        WHERE BOOK = ? AND PAGE = ? AND _deleted = 0
        """,
        (book_char, page_char),
    )
    foot_row = cur.fetchone()
    apparatus = decode(foot_row[0]) if foot_row else ""

    con.close()

    # ── Step 6: format and print ───────────────────────────────────────────
    width = 72

    if not show_apparatus:
        # Strip inline footnote reference digits from the page text.
        # These are Arabic digits that appear immediately after a non-space,
        # non-digit character, e.g. "taṃ2" → "taṃ", "nipako8" → "nipako".
        # The lookbehind `(?<=[^\s\d])` ensures that:
        #   • Standalone numbers (verse numbers, ordinals) are NOT stripped.
        #   • Only digits that are "glued" to a word character are removed.
        text = re.sub(r"(?<=[^\s\d])\d+", "", text)

    # Compact page header
    print(f"── {label}  p. {rpagenum} ──")
    print()
    print(text)

    if apparatus and show_apparatus:
        # Full apparatus block
        print()
        print("─" * width)
        print("  Apparātus criticus")
        print(
            "  (Cb = Cambridge  ·  Ba = Bangkok A  ·  Bai = Bangkok B  ·  "
            "Bi = Burmese  ·  Ck = Colombo  ·  Fsb = Fausbøll)"
        )
        print("─" * width)
        for line in apparatus.splitlines():
            print(f"  {line}")
    elif apparatus and not show_apparatus:
        # Compact notice so the user knows apparatus exists
        n = sum(1 for line in apparatus.splitlines() if line.strip())
        print(f"  [{n} manuscript variant(s) — use -a to show the apparatus]")

# ---------------------------------------------------------------------------
# Command-line interface helpers
# ---------------------------------------------------------------------------

def print_list() -> None:
    """Print a grouped list of all supported book abbreviations."""
    print("Supported abbreviations:\n")
    groups = [
        ("Vinaya",         ["Vin I", "Vin II", "Vin III", "Vin IV", "Vin V"]),
        ("Dīgha Nikāya",   ["D I", "D II", "D III"]),
        ("Majjhima Nik.",  ["M I", "M II", "M III"]),
        ("Saṃyutta Nik.",  ["S I", "S II", "S III", "S IV", "S V"]),
        ("Aṅguttara Nik.", ["A I", "A II", "A III", "A IV", "A V"]),
        ("Khuddaka",       ["Khp", "Dhp", "Ud", "It", "Sn", "Vv", "Pv",
                            "Th", "Thī", "Ja I–VI"]),
        ("Abhidhamma",     ["Dhs", "Vibh", "Dhtk", "Pp", "Kv",
                            "Yam I–II", "Pat I–III"]),
    ]
    for name, items in groups:
        print(f"  {name:<22} {' · '.join(items)}")
    print()
    print("Examples:")
    print("  python query_pts.py 'M I 3'")
    print("  python query_pts.py 'S IV 100'")
    print("  python query_pts.py 'Sn 25'")
    print("  python query_pts.py 'Sn 25' -a        # with apparatus criticus")
    print("  python query_pts.py 'Dhp 1' --apparatus")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Show help/list when called with no arguments or the --list flag.
    if len(sys.argv) < 2 or sys.argv[1] in ("--list", "--lista", "-l"):
        print(__doc__)
        print_list()
        sys.exit(0)

    args = sys.argv[1:]

    # Extract the apparatus flag from the argument list before joining the
    # remaining tokens into the citation string.
    show_ap = False
    if "-a" in args:
        show_ap = True
        args.remove("-a")
    if "--apparatus" in args:
        show_ap = True
        args.remove("--apparatus")
    if "--aparato" in args:   # keep Spanish alias for backwards compatibility
        show_ap = True
        args.remove("--aparato")

    # Whatever remains after flag extraction is the citation.
    # e.g. ["M", "I", "3"] → "M I 3"
    citation = " ".join(args)
    query(citation, show_apparatus=show_ap)
