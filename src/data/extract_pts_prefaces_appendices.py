"""
extract_pts_prefaces_appendices.py
==================================

Extracts the supplementary PTS (Pali Text Society) material — volume **prefaces**
and **appendices** ("Various Readings") — from the original Visual FoxPro source
files and loads it into the working ``tipitaka.sqlite`` database, decoding the
text fully (Base64 *and* the legacy 8-bit Pali font).

Background
----------
The whole database is the **PTS roman-script edition** (see ``DATABASE.md`` §1 —
the ``VOL_ID='ROTA'`` label is a misnomer).  The main page text (``palipg``) and
its inline apparatus (``footpg``) were already migrated into the ``pages`` /
``footnotes`` tables.  The *prefaces* and *appendices* were **not** — this script
adds them as the ``pts_prefaces`` and ``pts_appendices`` tables.

Source files (Wine install, "PaliText V2.5", Dhammakaya Foundation):
  * ``Dbf1/preface.dbf``  + ``Dbf1/appendix.dbf``  → edition ``mula``        (canon)
  * ``Dbf2/preface.dbf``  + ``Dbf2/appendix.dbf``  → edition ``atthakatha``  (commentaries)

Text encoding
-------------
``NEWCONTENT`` memo fields come in two forms, handled by :func:`decode_newcontent`:

1. ``Base64(BOM + UTF-8)`` — the normal, clean form (proper Unicode Pāli).
2. **Plain 8-bit text in a legacy Latin-Pāli font** — the high bytes
   (0x80–0xFF) are Pāli/Sanskrit diacritics.  This font is **different** from the
   ``ENCPALI`` Thai-script PUA font whose map ``main/database.py::get_thai_text``
   derives (there 0x82=Ā; here 0xA3=Ā).  :data:`LATIN_PALI_FONT` below was derived
   empirically by aligning the garbled words against the clean canon vocabulary,
   confirmed by the font's structural pattern (odd byte = uppercase, even = lower).

Re-running this script is idempotent: it drops and rebuilds the two tables, then
re-applies the font fix.

Usage
-----
    python3 extract_pts_prefaces_appendices.py [path/to/tipitaka.sqlite]
"""

from __future__ import annotations

import base64
import re
import sqlite3
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "tipitaka.sqlite"

# FoxPro source directories (relative to the AppDir root, two levels up from data/)
APPDIR = HERE.parent.parent
SOURCES = {
    "mula": APPDIR / "Tipitaka" / "Dbf1",        # canon
    "atthakatha": APPDIR / "Tipitaka" / "Dbf2",  # commentaries (Aṭṭhakathā)
}

# --------------------------------------------------------------------------- #
# Legacy Latin-Pāli 8-bit font map (latin1 byte → Unicode character)
#
# Derived empirically (substitution against the clean canon vocabulary) and
# confirmed by the font's odd/even = upper/lower structure.  Covers every Pāli
# diacritic plus the Sanskrit ś/ṛ/ṣ that appear in editorial notes.
#
# NOT covered (left as-is): typographic quotes / marks (0xBD–0xC3, 0xD1, …) that
# occur only inside English editorial prose, and U+00F1 (ñ) which is already
# correct in the Base64 rows.
# --------------------------------------------------------------------------- #

LATIN_PALI_FONT: dict[int, str] = {
    0xA1: "Ñ", 0xA2: "ñ",
    0xA3: "Ā", 0xA4: "ā",
    0xA5: "Ī", 0xA6: "ī",
    0xA7: "Ś", 0xA8: "ś",   # Sanskrit
    0xA9: "Ū", 0xAA: "ū",
    0xAB: "Ḍ", 0xAC: "ḍ",
    0xAF: "Ḷ", 0xB0: "ḷ",
    0xB1: "Ṃ", 0xB2: "ṃ",
    0xB3: "Ṅ", 0xB4: "ṅ",
    0xB5: "Ṇ", 0xB6: "ṇ",
    0xB7: "Ṛ", 0xB8: "ṛ",   # Sanskrit
    0xB9: "Ṣ", 0xBA: "ṣ",   # Sanskrit
    0xBB: "Ṭ", 0xBC: "ṭ",
}


def fix_font(text: str) -> str:
    """Map legacy Latin-Pāli font bytes (0x80–0xFF) to proper Unicode."""
    if not text:
        return text
    return "".join(
        LATIN_PALI_FONT.get(ord(c), c) if 0x80 <= ord(c) <= 0xFF else c
        for c in text
    )


def decode_newcontent(value: str | None) -> str:
    """Decode a preface/appendix ``NEWCONTENT`` memo to clean Unicode text.

    The DBF must be read with ``encoding='latin1'`` so this receives a 1:1,
    lossless string of the original bytes.  Strategy:

    * strict Base64 of ``BOM + UTF-8`` → return decoded UTF-8;
    * otherwise treat as plain text and apply the legacy Latin-Pāli font map.

    Strict validation (``validate=True`` + strict UTF-8) cleanly separates the
    two cases: a plain-text row fails Base64 (or yields non-UTF-8 garbage) and
    falls through to the font-mapping branch.
    """
    if not value:
        return ""
    raw = value.encode("latin1")
    compact = re.sub(rb"\s+", b"", raw)
    try:
        decoded = base64.b64decode(compact, validate=True)
        if decoded[:3] == b"\xef\xbb\xbf":
            decoded = decoded[3:]
        return decoded.decode("utf-8")
    except Exception:
        # Plain text in the legacy font.
        try:
            plain = raw.decode("utf-8")
        except UnicodeDecodeError:
            plain = raw.decode("latin1")
        return fix_font(plain)


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #

def _to_int(value) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def build_tables(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        DROP TABLE IF EXISTS pts_prefaces;
        DROP TABLE IF EXISTS pts_appendices;
        CREATE TABLE pts_prefaces (
            edition TEXT NOT NULL, book_no INTEGER, page_no INTEGER, text TEXT
        );
        CREATE TABLE pts_appendices (
            edition TEXT NOT NULL, book_no INTEGER, page_no INTEGER,
            target_book INTEGER, target_page INTEGER, text TEXT
        );
        """
    )


def extract(con: sqlite3.Connection) -> dict[tuple[str, str], int]:
    from dbfread import DBF  # local import: only needed when (re)extracting

    stats: dict[tuple[str, str], int] = {}
    cur = con.cursor()

    for edition, dbf_dir in SOURCES.items():
        # ---- prefaces ----
        rows = []
        for rec in DBF(str(dbf_dir / "preface.dbf"), load=False,
                       encoding="latin1", char_decode_errors="ignore"):
            text = decode_newcontent(rec.get("NEWCONTENT"))
            if text.strip():
                rows.append((edition, _to_int(rec.get("FCBOOK")),
                             _to_int(rec.get("FCPAGE")), text))
        cur.executemany("INSERT INTO pts_prefaces VALUES (?,?,?,?)", rows)
        stats[(edition, "prefaces")] = len(rows)

        # ---- appendices ----
        rows = []
        for rec in DBF(str(dbf_dir / "appendix.dbf"), load=False,
                       encoding="latin1", char_decode_errors="ignore"):
            text = decode_newcontent(rec.get("NEWCONTENT"))
            if text.strip():
                rows.append((edition, _to_int(rec.get("FCBOOK")),
                             _to_int(rec.get("FCPAGE")),
                             _to_int(rec.get("BOOK")), _to_int(rec.get("PAGE")),
                             text))
        cur.executemany("INSERT INTO pts_appendices VALUES (?,?,?,?,?,?)", rows)
        stats[(edition, "appendices")] = len(rows)

    cur.executescript(
        """
        CREATE INDEX idx_pts_prefaces ON pts_prefaces(edition, book_no, page_no);
        CREATE INDEX idx_pts_appendices ON pts_appendices(edition, book_no, page_no);
        """
    )
    con.commit()
    return stats


def main(db_path: Path) -> None:
    if not db_path.exists():
        sys.exit(f"Database not found: {db_path}")
    con = sqlite3.connect(str(db_path))
    try:
        build_tables(con)
        stats = extract(con)
        for (edition, table), count in sorted(stats.items()):
            print(f"  {edition:<11} {table:<11} {count}")
    finally:
        con.close()


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB)
