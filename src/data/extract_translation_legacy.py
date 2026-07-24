"""
extract_translation_legacy.py
=============================

Populates `translation_en` with SuttaCentral's *legacy* English translations
(Rhys Davids, Horner, Bodhi, Ñāṇamoli, Woodward…) — **excluding Bhikkhu
Sujato** — for DN/MN/SN/AN.

Legacy translations are per-sutta HTML (not segment-aligned), so they are
anchored to each sutta's **PTS start page** (from SuttaCentral's reference
data). The whole-sutta translation is shown when the reader is on that page.

Coverage is partial and authors vary by text. Result is self-contained in
tipitaka.sqlite.

Usage:
    python3 extract_translation_legacy.py [db] [sc-data-root]
"""

from __future__ import annotations

import html as htmlmod
import json
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "tipitaka.sqlite"
DEFAULT_SCDATA = Path("/home/jorge/Code/Software/suttacentral/server/sc-data")

NIK = {
    ("dn", 1): 6, ("dn", 2): 7, ("dn", 3): 8,
    ("mn", 1): 9, ("mn", 2): 10, ("mn", 3): 11,
    ("sn", 1): 12, ("sn", 2): 13, ("sn", 3): 14, ("sn", 4): 15, ("sn", 5): 16,
    ("an", 1): 17, ("an", 2): 18, ("an", 3): 19, ("an", 4): 20, ("an", 5): 21,
}
_PTS = re.compile(r"pts-vp-pli(\d+)\.(\d+)")
_AUTHOR = re.compile(r"author'\s*content='([^']*)'")


def _strip_html(s: str) -> str:
    s = re.sub(r"(?is)<head.*?</head>", "", s)
    # drop inline reference anchors like <a class='ref bps'>BPS 1</a>
    s = re.sub(r"(?is)<a\b[^>]*class=['\"][^'\"]*\bref\b[^'\"]*['\"][^>]*>.*?</a>", "", s)
    s = re.sub(r"(?is)</(p|h1|h2|h3|li|div|blockquote)>", "\n", s)
    s = re.sub(r"(?is)<br\s*/?>", "\n", s)
    s = re.sub(r"(?is)<[^>]+>", "", s)
    s = htmlmod.unescape(s)
    # drop credit/editorial lines mentioning Sujato (these are legacy
    # translations he only digitised or lightly edited, not his translations)
    s = re.sub(r"(?im)^.*\bSujato\b.*$", "", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n[ \t]+", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _start_pages(ref_root: Path) -> dict[str, tuple[int, int]]:
    """sutta id → (book_no, start PTS page) from SC reference data."""
    out: dict[str, tuple[int, int]] = {}
    base = ref_root / "sc_bilara_data" / "reference" / "pli" / "ms" / "sutta"
    for coll in {c for c, _ in NIK}:
        for fn in (base / coll).rglob("*_reference.json"):
            sid = fn.name[: -len("_reference.json")]
            try:
                data = json.loads(fn.read_text(encoding="utf-8"))
            except Exception:
                continue
            best = None
            for refs in data.values():
                m = _PTS.search(refs)
                if m:
                    pg = int(m.group(2))
                    if best is None or pg < best[1]:
                        best = (int(m.group(1)), pg)
            if best:
                book = NIK.get((coll, best[0]))
                if book:
                    out[sid] = (book, best[1])
    return out


def build(con: sqlite3.Connection, scdata: Path) -> dict[int, int]:
    starts = _start_pages(scdata)
    legacy_base = scdata / "html_text" / "en" / "pli" / "sutta"  # sibling of sc_bilara_data

    # (book, page) → (author, text); first non-Sujato translation found wins
    chosen: dict[tuple[int, int], tuple[str, str]] = {}
    for coll in {c for c, _ in NIK}:
        for fn in sorted((legacy_base / coll).rglob("*.html")):
            sid = fn.stem
            loc = starts.get(sid)
            if not loc or loc in chosen:
                continue
            raw = fn.read_text(encoding="utf-8", errors="replace")
            am = _AUTHOR.search(raw)
            author = am.group(1).strip() if am else ""
            if "sujato" in author.lower() or "sujato" in str(fn).lower():
                continue
            text = _strip_html(raw)
            if text:
                chosen[loc] = (author or "—", text)

    con.executescript(
        """
        DROP TABLE IF EXISTS translation_en;
        CREATE TABLE translation_en (
            book_no INTEGER NOT NULL,
            page_no INTEGER NOT NULL,
            author  TEXT,
            text    TEXT,
            PRIMARY KEY (book_no, page_no)
        );
        """
    )
    rows = [(b, p, a, t) for (b, p), (a, t) in chosen.items()]
    con.executemany("INSERT INTO translation_en VALUES (?,?,?,?)", rows)
    con.commit()

    from collections import Counter
    stats = Counter(b for b, _p, _a, _t in rows)
    return dict(stats), Counter(a for _b, _p, a, _t in rows)


def main(db: Path, scdata: Path) -> None:
    for p in (db, scdata):
        if not p.exists():
            sys.exit(f"No existe: {p}")
    con = sqlite3.connect(str(db))
    try:
        stats, authors = build(con, scdata)
        print(f"translation_en (legacy): {sum(stats.values())} suttas (anclados a su 1ª pág)")
        for bk in sorted(stats):
            print(f"  book {bk:2}: {stats[bk]}")
        print("Autores:", dict(authors))
    finally:
        con.close()


if __name__ == "__main__":
    db = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB
    sc = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_SCDATA
    main(db, sc)
