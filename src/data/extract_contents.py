"""
extract_contents.py
===================

Builds the `contents` table — a clean, PTS-anchored table of contents for the
four main nikāyas (DN, MN, SN, AN) — to drive the navigation sidebar.

Two SuttaCentral-derived sources are joined by sutta id:
  * **start page**  ← SC bilara `reference` data (`pts-vp-pli{vol}.{page}`,
    minimum page of the sutta = its PTS start). Reliable for all four nikāyas,
    including AN where the index's page refs are unusable.
  * **title / vagga** ← `index_suttas.csv` (SuttaCentral structure via the
    tipitaka.critical project).

Result lands in tipitaka.sqlite as `contents(book_no, seq, page_no, section,
title)`; no runtime dependency on the source checkouts.

Usage:
    python3 extract_contents.py [db] [sc-reference-dir] [index_suttas.csv]
"""

from __future__ import annotations

import csv
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
DEFAULT_INDEX = Path("/home/jorge/Code/tipitaka.critical/index_suttas.csv")

# (collection, PTS volume) → our book_no
NIK = {
    ("dn", 1): 6, ("dn", 2): 7, ("dn", 3): 8,
    ("mn", 1): 9, ("mn", 2): 10, ("mn", 3): 11,
    ("sn", 1): 12, ("sn", 2): 13, ("sn", 3): 14, ("sn", 4): 15, ("sn", 5): 16,
    ("an", 1): 17, ("an", 2): 18, ("an", 3): 19, ("an", 4): 20, ("an", 5): 21,
}
_PTS = re.compile(r"pts-vp-pli(\d+)\.(\d+)")


def _pretty_id(sutta_id: str) -> str:
    """'an1.1-10' → 'AN 1.1–10'; 'dn1' → 'DN 1'."""
    m = re.match(r"([a-z]+)(.*)", sutta_id)
    if not m:
        return sutta_id
    return f"{m.group(1).upper()} {m.group(2).replace('-', '–')}".strip()


def _root_title(ref_file: Path) -> str:
    """Most-specific heading (last ``…:0.N`` segment) of a sutta's root text.

    DN/MN/SN → the sutta name; AN ranges → the vagga name. The root file mirrors
    the reference path under .../root/... with a _root-pli-ms.json suffix.
    """
    root_file = Path(str(ref_file).replace("/reference/", "/root/")
                     .replace("_reference.json", "_root-pli-ms.json"))
    if not root_file.exists():
        return ""
    try:
        data = json.loads(root_file.read_text(encoding="utf-8"))
    except Exception:
        return ""
    # heading segments have a key suffix like "0.1", "0.2", … — take the last.
    zero = [v for k, v in data.items()
            if re.search(r":0\.\d+$", k)]
    return zero[-1].strip() if zero else ""


def build(con: sqlite3.Connection, sc_dir: Path, index_csv: Path) -> dict[int, int]:
    # 1) title / group per sutta id, from the index
    meta: dict[str, tuple[str, str, str]] = {}
    with index_csv.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            meta[row["id"]] = (row["collection"], row["title"], row["vagga"])

    # 2) start page + real title per sutta, from SC reference + root data
    rows = []
    for coll in {c for c, _ in NIK}:
        for fn in (sc_dir / coll).rglob("*_reference.json"):
            sid = fn.name[: -len("_reference.json")]
            try:
                data = json.loads(fn.read_text(encoding="utf-8"))
            except Exception:
                continue
            best = None
            for refs in data.values():
                for part in refs.split(","):
                    m = _PTS.match(part.strip())
                    if m:
                        vol, pg = int(m.group(1)), int(m.group(2))
                        if best is None or pg < best[1]:
                            best = (vol, pg)
            if not best:
                continue
            book = NIK.get((coll, best[0]))
            if not book:
                continue

            _c, idx_title, idx_vagga = meta.get(sid, (coll, "", ""))
            # group: saṃyutta/nipāta (index title) for SN/AN, else the vagga
            section = (idx_title if coll in ("sn", "an") else idx_vagga) or ""
            # entry title: the real per-sutta name from the root text
            title = _root_title(fn) or idx_title or _pretty_id(sid)
            rows.append((book, best[1], section, title))

    rows.sort(key=lambda r: (r[0], r[1]))

    # collapse consecutive duplicates (same section+title) keeping the first page
    collapsed = []
    for r in rows:
        if collapsed and collapsed[-1][0] == r[0] and \
           collapsed[-1][2] == r[2] and collapsed[-1][3] == r[3]:
            continue
        collapsed.append(r)
    rows = collapsed

    con.executescript(
        """
        DROP TABLE IF EXISTS contents;
        CREATE TABLE contents (
            book_no INTEGER NOT NULL,
            seq     INTEGER NOT NULL,
            page_no INTEGER NOT NULL,
            section TEXT,
            title   TEXT,
            PRIMARY KEY (book_no, seq)
        );
        """
    )
    by_book = defaultdict(int)
    out = []
    for book, page, section, label in rows:
        out.append((book, by_book[book], page, section, label))
        by_book[book] += 1
    con.executemany("INSERT INTO contents VALUES (?,?,?,?,?)", out)
    con.execute("CREATE INDEX idx_contents_book ON contents(book_no, seq)")
    con.commit()
    return dict(by_book)


def main(db: Path, sc: Path, idx: Path) -> None:
    for p in (db, sc, idx):
        if not p.exists():
            sys.exit(f"No existe: {p}")
    con = sqlite3.connect(str(db))
    try:
        stats = build(con, sc, idx)
        print(f"contents: {sum(stats.values())} entradas")
        for bk in sorted(stats):
            print(f"  book {bk:2}: {stats[bk]}")
    finally:
        con.close()


if __name__ == "__main__":
    db = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB
    sc = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_SC
    idx = Path(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_INDEX
    main(db, sc, idx)
