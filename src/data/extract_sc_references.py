"""
extract_sc_references.py
========================

Builds the `pts_xref` table — a compact (book_no, page_no) → VRI / Thai
cross-reference — from SuttaCentral's bilara reference data.

SuttaCentral records, per text *segment*, the locus in many editions:
  * ``pts-vp-pli{vol}.{page}``  → PTS volume + page  (matches our pagination)
  * ``vri{vol}.{paragraph}``    → VRI (Chaṭṭha Saṅgāyana) paragraph
  * ``sya{vol}.{n}``            → Syāmaraṭṭha (Royal Thai)

We invert that to PTS-page granularity for the four main nikāyas (DN, MN, SN,
AN), where our book↔(collection, PTS volume) mapping is exact. A PTS page spans
several segments, so each page yields a *range* of VRI/Thai references.

The result is self-contained in tipitaka.sqlite (no runtime dependency on the
SuttaCentral checkout).

Usage:
    python3 extract_sc_references.py [path/to/tipitaka.sqlite] [path/to/sc-reference]
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "tipitaka.sqlite"
DEFAULT_SC = Path(
    "/home/jorge/Code/Software/suttacentral/server/sc-data/sc_bilara_data/"
    "reference/pli/ms/sutta"
)

# our book_no → (SuttaCentral collection, PTS volume number)
# (verified by matching PTS page ranges; SN vol 1 has no pts-vp-pli refs in SC)
BOOK_TO_SC = {
    6: ("dn", 1), 7: ("dn", 2), 8: ("dn", 3),
    9: ("mn", 1), 10: ("mn", 2), 11: ("mn", 3),
    12: ("sn", 1), 13: ("sn", 2), 14: ("sn", 3), 15: ("sn", 4), 16: ("sn", 5),
    17: ("an", 1), 18: ("an", 2), 19: ("an", 3), 20: ("an", 4), 21: ("an", 5),
}

_PTS = re.compile(r"pts-vp-pli(\d+)\.(\d+)")
_VRI = re.compile(r"vri(\d+)\.(\d+)")
_SYA = re.compile(r"sya(\d+)\.(\d+)")


def _fmt(refs: set[tuple[int, int]]) -> str:
    """Format {(vol, n), …} as 'vol.min–max' for the dominant volume."""
    if not refs:
        return ""
    # dominant volume = the one with most entries
    by_vol: dict[int, list[int]] = defaultdict(list)
    for vol, n in refs:
        by_vol[vol].append(n)
    vol = max(by_vol, key=lambda v: len(by_vol[v]))
    ns = sorted(by_vol[vol])
    return f"{vol}.{ns[0]}" if ns[0] == ns[-1] else f"{vol}.{ns[0]}–{ns[-1]}"


def build(con: sqlite3.Connection, sc_dir: Path) -> dict[str, int]:
    # (collection, pts_vol, page) → {vri set}, {sya set}
    vri_map: dict[tuple, set] = defaultdict(set)
    sya_map: dict[tuple, set] = defaultdict(set)

    for coll, _vol in {(c, v) for c, v in BOOK_TO_SC.values()}:
        for fn in (sc_dir / coll).rglob("*_reference.json"):
            try:
                data = json.loads(fn.read_text(encoding="utf-8"))
            except Exception:
                continue
            for refs in data.values():
                parts = [p.strip() for p in refs.split(",")]
                pts = [(int(m[0]), int(m[1])) for m in
                       (_PTS.match(p) and _PTS.match(p).groups() for p in parts) if m]
                if not pts:
                    continue
                vri = {(int(m.group(1)), int(m.group(2)))
                       for p in parts if (m := _VRI.match(p))}
                sya = {(int(m.group(1)), int(m.group(2)))
                       for p in parts if (m := _SYA.match(p))}
                for vol, page in pts:
                    key = (coll, vol, page)
                    vri_map[key] |= vri
                    sya_map[key] |= sya

    con.executescript(
        """
        DROP TABLE IF EXISTS pts_xref;
        CREATE TABLE pts_xref (
            book_no INTEGER NOT NULL,
            page_no INTEGER NOT NULL,
            vri  TEXT,
            thai TEXT,
            PRIMARY KEY (book_no, page_no)
        );
        """
    )
    rows = []
    for book_no, (coll, vol) in BOOK_TO_SC.items():
        pages = {k[2] for k in vri_map if k[0] == coll and k[1] == vol}
        pages |= {k[2] for k in sya_map if k[0] == coll and k[1] == vol}
        for page in sorted(pages):
            vri = _fmt(vri_map.get((coll, vol, page), set()))
            thai = _fmt(sya_map.get((coll, vol, page), set()))
            if vri or thai:
                rows.append((book_no, page, vri, thai))
    con.executemany("INSERT INTO pts_xref VALUES (?,?,?,?)", rows)
    con.commit()

    stats = defaultdict(int)
    for book_no, *_ in rows:
        stats[book_no] += 1
    return stats


def main(db_path: Path, sc_dir: Path) -> None:
    if not db_path.exists():
        sys.exit(f"DB not found: {db_path}")
    if not sc_dir.exists():
        sys.exit(f"SuttaCentral reference dir not found: {sc_dir}")
    con = sqlite3.connect(str(db_path))
    try:
        stats = build(con, sc_dir)
        total = sum(stats.values())
        print(f"pts_xref: {total} páginas con referencia VRI/Thai")
        for bn in sorted(stats):
            print(f"  book {bn:2}: {stats[bn]} páginas")
    finally:
        con.close()


if __name__ == "__main__":
    db = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB
    sc = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_SC
    main(db, sc)
