"""
extract_translation_sujato.py
=============================

Builds `translation_sujato(book_no, page_no, text)` — Bhikkhu Sujato's English
(SuttaCentral), anchored per PTS page via the segment → `pts-vp-pli` mapping
(carry-forward). Used ONLY as a fallback where no legacy translation exists.

Usage:
    python3 extract_translation_sujato.py [db] [sc-reference-dir]
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

NIK = {
    ("dn", 1): 6, ("dn", 2): 7, ("dn", 3): 8,
    ("mn", 1): 9, ("mn", 2): 10, ("mn", 3): 11,
    ("sn", 1): 12, ("sn", 2): 13, ("sn", 3): 14, ("sn", 4): 15, ("sn", 5): 16,
    ("an", 1): 17, ("an", 2): 18, ("an", 3): 19, ("an", 4): 20, ("an", 5): 21,
}
_PTS = re.compile(r"pts-vp-pli(\d+)\.(\d+)")


def _trans_path(ref_file: Path) -> Path:
    return Path(str(ref_file)
                .replace("/reference/pli/ms/", "/translation/en/sujato/")
                .replace("_reference.json", "_translation-en-sujato.json"))


def build(con: sqlite3.Connection, sc_dir: Path) -> dict[int, int]:
    pages: dict[tuple[int, int], list[str]] = defaultdict(list)
    for coll in {c for c, _ in NIK}:
        for ref_file in sorted((sc_dir / coll).rglob("*_reference.json")):
            tfile = _trans_path(ref_file)
            if not tfile.exists():
                continue
            try:
                ref = json.loads(ref_file.read_text(encoding="utf-8"))
                trans = json.loads(tfile.read_text(encoding="utf-8"))
            except Exception:
                continue
            seg_page = {}
            for seg, refs in ref.items():
                m = _PTS.search(refs)
                if m:
                    book = NIK.get((coll, int(m.group(1))))
                    if book:
                        seg_page[seg] = (book, int(m.group(2)))
            cur = None
            for seg, en in trans.items():
                if seg in seg_page:
                    cur = seg_page[seg]
                if cur and en and en.strip():
                    pages[cur].append(re.sub(r"\s+", " ", en).strip())

    con.executescript(
        """
        DROP TABLE IF EXISTS translation_sujato;
        CREATE TABLE translation_sujato (
            book_no INTEGER NOT NULL, page_no INTEGER NOT NULL, text TEXT,
            PRIMARY KEY (book_no, page_no)
        );
        """
    )
    rows = [(b, p, " ".join(s)) for (b, p), s in pages.items() if s]
    con.executemany("INSERT INTO translation_sujato VALUES (?,?,?)", rows)
    con.commit()
    stats = defaultdict(int)
    for b, _p, _t in rows:
        stats[b] += 1
    return dict(stats)


def main(db: Path, sc: Path) -> None:
    for p in (db, sc):
        if not p.exists():
            sys.exit(f"No existe: {p}")
    con = sqlite3.connect(str(db))
    try:
        stats = build(con, sc)
        print(f"translation_sujato (fallback): {sum(stats.values())} páginas")
    finally:
        con.close()


if __name__ == "__main__":
    db = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB
    sc = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_SC
    main(db, sc)
