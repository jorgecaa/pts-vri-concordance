"""
Database module for Tipitaka PTS Browser — Clean Schema.

Uses tipitaka.sqlite (clean schema) with decoded Pali text and metadata.
The whole database is the Pali Text Society edition; the two `edition` values
are 'mula' (canon) and 'atthakatha' (commentaries), each available in roman
script (unitext) and Thai script (encpali).
"""

import base64
import functools
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .citation_parser import PTSCitationParser

# ── Canon ↔ commentary book mapping ──────────────────────────
# ROTA (mula / canon) book_no → ROTB (atthakatha / commentary) book_no.
# Authoritative copy; the GUI imports this so the two never diverge.
ROTA_TO_ROTB: Dict[int, int] = {
    1: 1, 2: 1, 3: 1, 4: 1, 5: 1,        # Vinaya → Samantapāsādikā
    6: 9, 7: 9, 8: 9,                     # Dīgha → Sumaṅgala-Vilāsinī
    9: 12, 10: 13, 11: 14,               # Majjhima → Papañcasūdanī
    12: 17, 13: 17, 14: 18, 15: 18, 16: 19,  # Saṃyutta → Sāratthappakāsinī
    17: 20, 18: 21, 19: 22, 20: 23, 21: 24,  # Aṅguttara → Manorathapūraṇī
    22: 25,  # Khp → Paramatthajotikā
    23: 26,  # Dhp → Dhammapada-aṭṭhakathā
    24: 27,  # Ud → Paramatthadīpanī
    25: 32,  # It → Itivuttaka-vaṇṇanā
    26: 30,  # Sn → Paramatthadīpanī
    27: 34, 28: 35, 29: 36,              # Vv, Pv, Thag
    30: 54, 31: 54, 32: 54, 33: 54, 34: 54, 35: 54,  # Jātaka
    43: 47, 44: 48,                      # Abhidhamma
}

# Reverse: commentary book_no → [canon book_no, …] (a commentary often spans
# several canonical volumes). Used for the commentary → canon direction.
ROTB_TO_ROTA: Dict[int, List[int]] = {}
for _mula, _comm in ROTA_TO_ROTB.items():
    ROTB_TO_ROTA.setdefault(_comm, []).append(_mula)

# ── Regex support for SQLite ─────────────────────────────────


@functools.lru_cache(maxsize=256)
def _compile_regex(pattern: str):
    """Cache-compiled regex (case-insensitive). Returns None on bad pattern."""
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error:
        return None


def _sqlite_regexp(pattern: str, value) -> int:
    """REGEXP implementation for SQLite: 1 if `value` matches `pattern`."""
    if value is None:
        return 0
    rx = _compile_regex(pattern)
    if rx is None:
        return 0
    return 1 if rx.search(value) else 0

# ── Decoding Utilities ───────────────────────────────────────


def decode_unitext(raw: Optional[str]) -> str:
    """Decode UNITEXT field from Base64(BOM + UTF-8-bytes) to Pali text.

    All text columns (UNITEXT in pages, footnotes, etc.) are stored with:
        1. Pali text encoded as UTF-8 bytes.
        2. A UTF-8 BOM (0xEF 0xBB 0xBF) prepended to those bytes.
        3. The combined bytes Base64-encoded and stored as ASCII.

    HEAD fields are plain UTF-8 (not Base64-encoded). The try/except
    handles this transparently: returns raw string if decoding fails.
    """
    if not raw:
        return ""
    try:
        decoded_bytes = base64.b64decode(raw.strip() + "==")
        if decoded_bytes[:3] == b"\xef\xbb\xbf":
            decoded_bytes = decoded_bytes[3:]
        return decoded_bytes.decode("utf-8", errors="replace")
    except Exception:
        return raw


def decode_encpali(raw: Optional[str]) -> str:
    """Decode ENCPALI field from Base64 to Thai-script text."""
    if not raw:
        return ""
    try:
        decoded_bytes = base64.b64decode(raw.strip() + "==")
        return decoded_bytes.decode("utf-8", errors="replace")
    except Exception:
        return raw


def lru_cache_text(maxsize: int = 128):
    """LRU cache decorator for text decoding methods."""

    def decorator(func):
        cache = {}
        order = []

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            if key in cache:
                return cache[key]
            result = func(*args, **kwargs)
            order.append(key)
            cache[key] = result
            if len(order) > maxsize:
                oldest = order.pop(0)
                cache.pop(oldest, None)
            return result

        wrapper.cache_clear = lambda: (cache.clear(), order.clear())
        return wrapper

    return decorator


class TipitakaDatabase:
    """Database access layer for the clean Tipitaka database."""

    def __init__(self, db_path: Union[str, Path], edition: str = "mula"):
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        self.edition = edition
        self._citation_parser = PTSCitationParser()
        # Lazily-built per-book anchor index, keyed (edition, book_no).
        self._anchor_cache: Dict[tuple, Dict[str, Any]] = {}
        # Cache for get_head_sections, keyed (edition, book_no) — it scans every
        # page of the book, so the commentary breadcrumb must not recompute it
        # on every sync.
        self._head_sections_cache: Dict[tuple, List[Dict[str, Any]]] = {}

    # ── Connection ────────────────────────────────────────────

    def connect(self) -> bool:
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            # Enable `col REGEXP ?` (case-insensitive) — not built into Python sqlite3.
            try:
                self.connection.create_function(
                    "regexp", 2, _sqlite_regexp, deterministic=True
                )
            except TypeError:  # deterministic= unsupported on older Python
                self.connection.create_function("regexp", 2, _sqlite_regexp)
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False

    def close(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None

    def _ensure_connected(self) -> bool:
        if self.connection:
            return True
        return self.connect()

    # ── Pages ─────────────────────────────────────────────────

    def get_page_by_pts_citation(self, citation: str) -> Optional[Dict[str, Any]]:
        parsed = self._citation_parser.parse_and_resolve(citation)
        if not parsed:
            return None
        book_no = parsed.get("book_no")
        page = parsed.get("page")
        if not book_no or page is None:
            return None
        return self.get_page_by_book_and_page(int(book_no), int(page))

    @lru_cache_text(maxsize=128)
    def get_page_by_book_and_page(
        self, book_no: int, page_num: int
    ) -> Optional[Dict[str, Any]]:
        # Cached fast-path for the *current* edition (cache cleared by
        # set_edition; the key intentionally omits edition — see set_edition).
        return self._fetch_page(self.edition, book_no, page_num)

    def get_page_for_edition(
        self, edition: str, book_no: int, page_num: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch a page from an explicit edition without touching self.edition.

        Used by the parallel commentary pane so it can render `atthakatha`
        while the main pane stays on `mula` — and without thrashing the LRU
        cache of get_page_by_book_and_page.
        """
        return self._fetch_page(edition, book_no, page_num)

    def _fetch_page(
        self, edition: str, book_no: int, page_num: int
    ) -> Optional[Dict[str, Any]]:
        if not self._ensure_connected():
            return None
        try:
            cur = self.connection.cursor()
            cur.execute(
                """SELECT book_no, page_no, unitext, encpali, head, head_old, book_key, page_key
                   FROM pages
                   WHERE edition=? AND book_no=? AND page_no=?""",
                (edition, book_no, page_num),
            )
            row = cur.fetchone()
            if not row:
                return None

            raw_unitext = row["unitext"] or ""
            decoded_text = decode_unitext(raw_unitext)
            raw_encpali = row["encpali"] or ""
            decoded_encpali = decode_encpali(raw_encpali) if raw_encpali else ""

            apparatus = self._apparatus_for_edition(edition, book_no, page_num)
            book_info = self._book_info_for_edition(edition, book_no)

            return {
                "book_no": row["book_no"],
                "page_num": row["page_no"],
                "text": decoded_text,
                "encpali": decoded_encpali,
                "head": row["head"] or "",
                "head_old": row["head_old"] or "",
                "apparatus": apparatus,
                "book_info": book_info,
                "book_key": row["book_key"],
                "page_key": row["page_key"],
            }
        except Exception as e:
            print(f"Error getting page: {e}")
            return None

    def get_apparatus_for_page(self, book_no: int, page_num: int) -> str:
        return self._apparatus_for_edition(self.edition, book_no, page_num)

    def get_apparatus_entries(
        self, book_no: int, page_num: int, edition: Optional[str] = None
    ) -> Dict[int, str]:
        """Structured critical apparatus for a page: {note_no: note_text}.

        The footnotes blob is a run of `&N`-marked entries (the same `&N`
        markers that appear as superscripts in the page body). We split on
        those markers so each note can be rendered as a numbered, linkable
        entry instead of one opaque bold blob. Preamble before the first
        marker (rare) is attached as note 0.
        """
        raw = self._apparatus_for_edition(edition or self.edition, book_no, page_num)
        if not raw:
            return {}
        raw = raw.replace("\r", "")
        parts = re.split(r"&(\d+)", raw)
        entries: Dict[int, str] = {}
        preamble = parts[0].strip()
        if preamble:
            entries[0] = preamble
        for num, body in zip(parts[1::2], parts[2::2]):
            entries[int(num)] = body.strip()
        return entries

    def _apparatus_for_edition(
        self, edition: str, book_no: int, page_num: int
    ) -> str:
        if not self._ensure_connected():
            return ""
        try:
            cur = self.connection.cursor()
            cur.execute(
                """SELECT unitext FROM footnotes
                   WHERE edition=? AND book_no=? AND page_no=?""",
                (edition, book_no, page_num),
            )
            row = cur.fetchone()
            if row and row["unitext"]:
                return decode_unitext(row["unitext"])
            return ""
        except Exception:
            return ""

    # ── Prefaces & appendices (PTS front-matter / "Various Readings") ──
    # These tables store already-decoded, font-fixed plain text (unlike pages,
    # whose unitext is Base64). See data/extract_pts_prefaces_appendices.py.

    def get_cross_refs(self, book_no: int, page_no: int) -> Dict[str, str]:
        """VRI / Thai (Syāmaraṭṭha) references for a PTS page.

        Canon DN/MN/SN/AN only; sourced from SuttaCentral (see
        data/extract_sc_references.py). Returns {} when unavailable.
        """
        if not self._ensure_connected():
            return {}
        try:
            cur = self.connection.cursor()
            cur.execute(
                "SELECT vri, thai FROM pts_xref WHERE book_no=? AND page_no=?",
                (book_no, page_no),
            )
            row = cur.fetchone()
            return {"vri": row["vri"] or "", "thai": row["thai"] or ""} if row else {}
        except Exception:
            return {}

    def get_contents(self, book_no: int) -> List[Dict[str, Any]]:
        """PTS-anchored table of contents (section + title + page) for a book.

        Canon DN/MN/SN/AN only; built from SuttaCentral (see
        data/extract_contents.py). Empty when unavailable.
        """
        if not self._ensure_connected():
            return []
        try:
            cur = self.connection.cursor()
            cur.execute(
                "SELECT page_no, section, title FROM contents"
                " WHERE book_no=? ORDER BY seq",
                (book_no,),
            )
            return [
                {"page_no": r["page_no"],
                 "section": r["section"] or "",
                 "title": r["title"] or ""}
                for r in cur.fetchall()
            ]
        except Exception:
            return []

    def get_translation(self, book_no: int, page_no: int) -> Dict[str, str]:
        """Legacy English translation for the sutta containing this PTS page.

        Shown on *every* page of a translated sutta (not just its first), but
        never leaks into a neighbouring untranslated sutta: the containing
        sutta's page range is taken from `contents`. Returns {author, text} or
        {} (partial coverage). See data/extract_translation_legacy.py.
        """
        if not self._ensure_connected():
            return {}
        try:
            cur = self.connection.cursor()
            # range of the sutta containing this page, from contents
            r = cur.execute(
                "SELECT page_no FROM contents WHERE book_no=? AND page_no<=?"
                " ORDER BY page_no DESC LIMIT 1",
                (book_no, page_no),
            ).fetchone()
            if r:
                start = r["page_no"]
                nxt = cur.execute(
                    "SELECT MIN(page_no) AS n FROM contents"
                    " WHERE book_no=? AND page_no>?",
                    (book_no, start),
                ).fetchone()["n"] or 10**9
                row = cur.execute(
                    "SELECT author, text FROM translation_en"
                    " WHERE book_no=? AND page_no>=? AND page_no<?"
                    " ORDER BY page_no LIMIT 1",
                    (book_no, start, nxt),
                ).fetchone()
            else:  # no contents for this book → exact-page fallback
                row = cur.execute(
                    "SELECT author, text FROM translation_en"
                    " WHERE book_no=? AND page_no=?",
                    (book_no, page_no),
                ).fetchone()
            if row and row["text"]:
                return {"author": row["author"] or "", "text": row["text"],
                        "scope": "sutta"}

            # Fallback: Bhikkhu Sujato, per PTS page (only where no legacy exists).
            sj = cur.execute(
                "SELECT text FROM translation_sujato WHERE book_no=? AND page_no=?",
                (book_no, page_no),
            ).fetchone()
            if sj and sj["text"]:
                return {"author": "Bhikkhu Sujato", "text": sj["text"],
                        "scope": "page"}
            return {}
        except Exception:
            return {}

    def get_nav_sections(self, book_no: int) -> List[Dict[str, Any]]:
        """Navigable sections (title + page) for a book, from the nav tree.

        `nav_tree` has no edition column; it carries the canon's section
        hierarchy. Returns the page-anchored nodes ordered by page.
        """
        if not self._ensure_connected():
            return []
        try:
            cur = self.connection.cursor()
            cur.execute(
                "SELECT text, page_no FROM nav_tree"
                " WHERE book_no=? AND page_no > 0"
                " ORDER BY page_no, key",
                (book_no,),
            )
            return [
                {"text": r["text"], "page_no": r["page_no"]}
                for r in cur.fetchall()
                if r["text"]
            ]
        except Exception as e:
            print(f"Error getting nav sections: {e}")
            return []

    def get_prefaces(self, book_no: int) -> List[Dict[str, Any]]:
        """Volume preface pages for the current edition, ordered by page."""
        if not self._ensure_connected():
            return []
        try:
            cur = self.connection.cursor()
            cur.execute(
                """SELECT page_no, text FROM pts_prefaces
                   WHERE edition=? AND book_no=?
                   ORDER BY page_no""",
                (self.edition, book_no),
            )
            return [dict(r) for r in cur.fetchall()]
        except Exception as e:
            print(f"Error getting prefaces: {e}")
            return []

    def get_appendices(self, book_no: int) -> List[Dict[str, Any]]:
        """Volume appendix pages ("Various Readings") for the current edition."""
        if not self._ensure_connected():
            return []
        try:
            cur = self.connection.cursor()
            cur.execute(
                """SELECT page_no, text FROM pts_appendices
                   WHERE edition=? AND book_no=?
                   ORDER BY page_no""",
                (self.edition, book_no),
            )
            return [dict(r) for r in cur.fetchall()]
        except Exception as e:
            print(f"Error getting appendices: {e}")
            return []

    # ── Books ─────────────────────────────────────────────────

    def get_book_info(self, book_no: int) -> Optional[Dict[str, Any]]:
        return self._book_info_for_edition(self.edition, book_no)

    def _book_info_for_edition(
        self, edition: str, book_no: int
    ) -> Optional[Dict[str, Any]]:
        if not self._ensure_connected():
            return None
        try:
            cur = self.connection.cursor()
            cur.execute(
                """SELECT edition, book_no, s_name, book_name, beg_page, end_page
                   FROM books
                   WHERE edition=? AND book_no=?""",
                (edition, book_no),
            )
            row = cur.fetchone()
            if row:
                info = dict(row)
                # book_name may also be Base64-encoded
                raw_name = info.get("book_name") or ""
                info["book_name"] = decode_unitext(raw_name)
                return info
            return None
        except Exception as e:
            print(f"Error getting book info: {e}")
            return None

    def get_all_books(self) -> List[Dict[str, Any]]:
        if not self._ensure_connected():
            return []
        try:
            cur = self.connection.cursor()
            cur.execute(
                """SELECT edition, book_no, s_name, book_name, beg_page, end_page
                   FROM books
                   WHERE edition=?
                   ORDER BY book_no""",
                (self.edition,),
            )
            return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error getting all books: {e}")
            return []

    # ── Search ────────────────────────────────────────────────

    def build_fts5_index(self, progress_callback=None) -> int:
        """Build (or rebuild) the global FTS5 full-text index.

        Indexes ALL editions and content types in a single index — canon and
        commentary pages, plus the PTS prefaces and appendices — each row tagged
        with `edition` and `kind` ('page' | 'preface' | 'appendix') for
        filtering.  `decode_unitext` handles both the Base64 (canon) and the
        plain-UTF-8 (commentary) page text transparently.
        Returns the number of documents indexed.
        """
        if not self._ensure_connected():
            return 0
        try:
            cur = self.connection.cursor()
            cur.execute("DROP TABLE IF EXISTS pali_fts")
            cur.execute(
                "CREATE VIRTUAL TABLE pali_fts USING fts5("
                "  unitext, head,"
                "  edition UNINDEXED, kind UNINDEXED,"
                "  book_no UNINDEXED, page_no UNINDEXED,"
                "  tokenize='unicode61 remove_diacritics 0'"
                ")"
            )

            count = 0

            # Canon + commentary pages.
            cur.execute("SELECT edition, book_no, page_no, unitext, head FROM pages")
            page_rows = cur.fetchall()
            total = len(page_rows)
            for i, row in enumerate(page_rows):
                decoded = decode_unitext(row["unitext"] or "")
                if decoded.strip():
                    cur.execute(
                        "INSERT INTO pali_fts"
                        "(unitext, head, edition, kind, book_no, page_no)"
                        " VALUES (?,?,?,?,?,?)",
                        (decoded, row["head"] or "", row["edition"], "page",
                         row["book_no"], row["page_no"]),
                    )
                    count += 1
                if progress_callback and i % 500 == 0:
                    progress_callback(i, total)

            # PTS prefaces & appendices (text already decoded/plain).
            for kind, table in (("preface", "pts_prefaces"),
                                ("appendix", "pts_appendices")):
                try:
                    cur.execute(
                        f"SELECT edition, book_no, page_no, text FROM {table}"
                    )
                except Exception:
                    continue  # table may not exist in older DB copies
                for row in cur.fetchall():
                    txt = row["text"] or ""
                    if txt.strip():
                        cur.execute(
                            "INSERT INTO pali_fts"
                            "(unitext, head, edition, kind, book_no, page_no)"
                            " VALUES (?,?,?,?,?,?)",
                            (txt, "", row["edition"], kind,
                             row["book_no"], row["page_no"]),
                        )
                        count += 1

            self.connection.commit()
            return count
        except Exception as e:
            print(f"Error building FTS5 index: {e}")
            return 0

    def has_fts5(self) -> bool:
        """Check if the FTS5 index exists and is populated."""
        if not self._ensure_connected():
            return False
        try:
            cur = self.connection.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='pali_fts'"
            )
            if not cur.fetchone():
                return False
            cur.execute("SELECT COUNT(*) FROM pali_fts")
            return cur.fetchone()[0] > 0
        except Exception:
            return False

    def count_texts(self, query: str) -> int:
        """Total number of FTS hits for `query` in the current edition."""
        if not self._ensure_connected() or not self.has_fts5():
            return 0
        try:
            cur = self.connection.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM pali_fts WHERE pali_fts MATCH ? AND edition = ?",
                (self._build_fts_query(query), self.edition),
            )
            return cur.fetchone()[0]
        except Exception:
            return 0

    def _search_fts5(
        self, query: str, limit: int, book_no: int = 0, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search using FTS5 full-text index with snippet generation."""
        if not self._ensure_connected() or not self.has_fts5():
            return []

        results: List[Dict[str, Any]] = []
        book_cache: Dict[int, Any] = {}

        try:
            cur = self.connection.cursor()

            # Build FTS5 query: escape special chars, add prefix matching
            fts_query = self._build_fts_query(query)

            if book_no > 0:
                sql = (
                    "SELECT book_no, page_no, head, kind,"
                    " snippet(pali_fts, 0, '⟦', '⟧', '…', 16) AS snippet"
                    " FROM pali_fts"
                    " WHERE pali_fts MATCH ? AND edition = ? AND book_no = ?"
                    " ORDER BY rank LIMIT ? OFFSET ?"
                )
                cur.execute(sql, (fts_query, self.edition, book_no, limit, offset))
            else:
                sql = (
                    "SELECT book_no, page_no, head, kind,"
                    " snippet(pali_fts, 0, '⟦', '⟧', '…', 16) AS snippet"
                    " FROM pali_fts"
                    " WHERE pali_fts MATCH ? AND edition = ?"
                    " ORDER BY rank LIMIT ? OFFSET ?"
                )
                cur.execute(sql, (fts_query, self.edition, limit, offset))

            for row in cur.fetchall():
                bn = row["book_no"]
                pn = row["page_no"]

                if bn not in book_cache:
                    book_cache[bn] = self.get_book_info(bn)

                results.append(
                    {
                        "word": query,
                        "book_no": bn,
                        "page_num": pn,
                        "snippet": row["snippet"] or "",
                        "snippet_html": row["snippet"] or "",
                        "book_info": book_cache.get(bn),
                        "edition": self.edition,
                        "kind": row["kind"],
                        "book_name": (
                            (book_cache[bn].get("s_name") or "").strip()
                            if book_cache.get(bn)
                            else ""
                        ),
                    }
                )

            return results
        except Exception as e:
            print(f"FTS5 search error: {e}")
            return []

    def _build_fts_query(self, query: str) -> str:
        """Build a safe FTS5 query string from user input.

        Escapes special FTS5 characters and adds prefix matching.
        Multi-word queries become implicit AND.
        """
        # Remove FTS5 special characters
        safe = query.strip()
        for char in '"*(){}[]^~:|':
            safe = safe.replace(char, " ")

        # Split into words, add prefix matching (*) to each
        words = safe.split()
        if not words:
            return safe

        # Add prefix wildcard to each word for substring matching
        terms = [f'"{w}"*' if " " not in w else f'"{w}"' for w in words]
        return " ".join(terms)

    def _search_decoded_pages(
        self, query: str, limit: int, book_no: int = 0
    ) -> List[Dict[str, Any]]:
        """Core search: uses FTS5 if available, falls back to scan."""
        # Try FTS5 first (near-instant)
        if self.has_fts5():
            results = self._search_fts5(query, limit, book_no)
            if results:
                return results

        # Fallback: scan decoded unitext
        if not self._ensure_connected():
            return []

        results: List[Dict[str, Any]] = []
        book_cache: Dict[int, Any] = {}
        query_lower = query.lower()

        try:
            cur = self.connection.cursor()
            if book_no > 0:
                cur.execute(
                    "SELECT book_no, page_no, unitext, head FROM pages"
                    " WHERE edition=? AND book_no=? ORDER BY page_no",
                    (self.edition, book_no),
                )
            else:
                cur.execute(
                    "SELECT book_no, page_no, unitext, head FROM pages"
                    " WHERE edition=? ORDER BY book_no, page_no",
                    (self.edition,),
                )

            for row in cur.fetchall():
                raw = row["unitext"] or ""
                decoded = decode_unitext(raw)
                decoded_lower = decoded.lower()

                if query_lower not in decoded_lower:
                    continue

                bn = row["book_no"]
                pn = row["page_no"]

                if bn not in book_cache:
                    book_cache[bn] = self.get_book_info(bn)

                idx = decoded_lower.find(query_lower)
                start = max(0, idx - 60)
                end = min(len(decoded), idx + len(query) + 60)
                snippet = (
                    ("…" if start > 0 else "")
                    + decoded[start:end].replace("\n", " ")
                    + ("…" if end < len(decoded) else "")
                )

                results.append(
                    {
                        "word": query,
                        "book_no": bn,
                        "page_num": pn,
                        "snippet": snippet,
                        "snippet_html": snippet,
                        "book_info": book_cache.get(bn),
                        "edition": self.edition,
                        "book_name": (
                            (book_cache[bn].get("s_name") or "").strip()
                            if book_cache.get(bn)
                            else ""
                        ),
                    }
                )

                if len(results) >= limit:
                    break

            return results
        except Exception as e:
            print(f"Error in _search_decoded_pages: {e}")
            return []

    def search_texts(
        self, query: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search for texts containing the query string (paginated).

        Uses FTS5 full-text index when available for near-instant results.
        Falls back to scanning decoded unitext if FTS5 hasn't been built.
        """
        if self.has_fts5():
            results = self._search_fts5(query, limit, offset=offset)
            if results or offset:
                return results
        return self._search_decoded_pages(query, limit)

    # ── Dictionary ────────────────────────────────────────────

    def get_dictionary_entry(self, word: str) -> Optional[Dict[str, Any]]:
        if not self._ensure_connected():
            return None
        try:
            cur = self.connection.cursor()

            # PTS Pali-English Dictionary
            cur.execute(
                """SELECT ttitle, tdetail, page_no
                   FROM dict_pts WHERE ttitle=?""",
                (word,),
            )
            row = cur.fetchone()
            if row:
                return {
                    "word": row["ttitle"],
                    "definition": row["tdetail"],
                    "page": row["page_no"],
                    "source": "PTS Dictionary",
                }

            # Bilingual Thai-English Dictionary
            cur.execute(
                """SELECT ttitle, tdetail, etitle, edetail
                   FROM dict_pali_english WHERE ttitle=?""",
                (word,),
            )
            row = cur.fetchone()
            if row:
                return {
                    "word": row["ttitle"],
                    "definition": row["tdetail"] or row["edetail"] or row["etitle"],
                    "english": row["etitle"],
                    "source": "Bilingual Dictionary",
                }

            # Word frequency lookup
            cur.execute(
                """SELECT skid, str1, nfound, nfootfound
                   FROM word_list WHERE edition=? AND str1=?""",
                (self.edition, word),
            )
            row = cur.fetchone()
            if row:
                return {
                    "word": word,
                    "definition": f"Word in {self.edition} vocabulary",
                    "source": f"{self.edition} Vocabulary",
                    "main_text_occurrences": row["nfound"],
                    "footnote_occurrences": row["nfootfound"],
                }

            return None
        except Exception as e:
            print(f"Error looking up dictionary: {e}")
            return None

    def search_dictionary(self, query: str, limit: int = 20) -> list:
        """Search dictionary with prefix matching. Returns list of matches."""
        if not self._ensure_connected():
            return []
        try:
            cur = self.connection.cursor()
            results = []
            cur.execute(
                "SELECT ttitle, tdetail, page_no FROM dict_pts WHERE ttitle LIKE ? LIMIT ?",
                (f"{query}%", limit),
            )
            for row in cur.fetchall():
                results.append(
                    {
                        "word": row["ttitle"],
                        "definition": (row["tdetail"] or "")[:200],
                        "source": "PTS",
                    }
                )
            if len(results) < limit:
                cur.execute(
                    "SELECT ttitle, tdetail, etitle FROM dict_pali_english WHERE ttitle LIKE ? LIMIT ?",
                    (f"{query}%", limit - len(results)),
                )
                for row in cur.fetchall():
                    results.append(
                        {
                            "word": row["ttitle"],
                            "definition": (row["tdetail"] or row["etitle"] or "")[:200],
                            "source": "Bilingual",
                        }
                    )
            return results
        except Exception:
            return []

    def _fts_match_pages(self, word: str) -> List[sqlite3.Row]:
        """All FTS5 page hits (book_no, page_no) for `word` in the current edition.

        The native concordance tables (word_list/word_occurrences) are unusable —
        word_list.str1 is in an opaque legacy encoding and the migration left the
        keys unreliable — so the concordance is served from the global FTS5 index
        instead (fast, and consistent with the rest of search).
        """
        if not self._ensure_connected() or not self.has_fts5():
            return []
        try:
            cur = self.connection.cursor()
            cur.execute(
                "SELECT book_no, page_no FROM pali_fts"
                " WHERE pali_fts MATCH ? AND edition = ? AND kind = 'page'",
                (self._build_fts_query(word), self.edition),
            )
            return cur.fetchall()
        except Exception:
            return []

    def get_word_frequency(self, word: str) -> dict | None:
        """Get word frequency (derived from the FTS-based concordance)."""
        stats = self.word_stats(word)
        if not stats:
            return None
        return {
            "word": word,
            "occurrences": stats["occurrences"],
            "footnote_occurrences": None,
        }

    def concordance(self, word: str, limit: int = 30) -> list:
        """Word concordance with snippets, served from the FTS5 index.

        Returns list of {book_no, page_no, book_name, snippet}.
        """
        if self.has_fts5():
            raw_results = self._search_fts5(word, limit)
        else:
            raw_results = self._search_decoded_pages(word, limit)
        return [
            {
                "book_no": r["book_no"],
                "page_no": r["page_num"],
                "book_name": r.get("book_name", ""),
                "snippet": r["snippet"],
            }
            for r in raw_results
        ]

    def word_stats(self, word: str) -> dict | None:
        """Word statistics: pages, books, and total occurrences.

        Page/book counts come straight from the FTS5 index (instant); the exact
        occurrence count is tallied by decoding only the matched pages.
        """
        if not self._ensure_connected():
            return None
        try:
            matches = self._fts_match_pages(word)
            if matches:
                books = {m["book_no"] for m in matches}
                word_lower = word.lower()
                occ = 0
                cur = self.connection.cursor()
                for m in matches:
                    cur.execute(
                        "SELECT unitext FROM pages"
                        " WHERE edition=? AND book_no=? AND page_no=?",
                        (self.edition, m["book_no"], m["page_no"]),
                    )
                    row = cur.fetchone()
                    if row:
                        occ += decode_unitext(row["unitext"] or "").lower().count(
                            word_lower
                        )
                return {
                    "word": word,
                    "pages": len(matches),
                    "books": len(books),
                    "occurrences": occ,
                }

            # Fallback (no FTS): scan decoded pages.
            cur = self.connection.cursor()
            word_lower = word.lower()
            pages = 0
            books_set: set = set()
            occ = 0
            cur.execute(
                "SELECT book_no, unitext FROM pages WHERE edition=?",
                (self.edition,),
            )
            for row in cur.fetchall():
                c = decode_unitext(row["unitext"] or "").lower().count(word_lower)
                if c:
                    pages += 1
                    books_set.add(row["book_no"])
                    occ += c
            return {
                "word": word,
                "pages": pages,
                "books": len(books_set),
                "occurrences": occ,
            }
        except Exception:
            return None

    @staticmethod
    def _regex_literal(pattern: str) -> str:
        """Longest alphabetic (incl. diacritics) run in `pattern`, for FTS prefilter.

        Regex metacharacters and digits break runs, so what remains is a literal
        substring guaranteed to appear in any match — usable as an FTS token.
        """
        best = cur = ""
        i, n = 0, len(pattern)
        while i < n:
            ch = pattern[i]
            if ch == "\\":  # escape sequence (\b, \w, \d, …): not a literal
                cur = ""
                i += 2
                continue
            if ch.isalpha():
                cur += ch
                if len(cur) > len(best):
                    best = cur
            else:
                cur = ""
            i += 1
        return best if len(best) >= 3 else ""

    def _regex_candidates(self, pattern: str, book_no: int = 0):
        """Yield candidate (book_no, page_no, unitext) pages for a regex search.

        Uses the FTS literal prefilter when possible, else scans the edition.
        """
        cur = self.connection.cursor()
        literal = self._regex_literal(pattern)
        if literal and self.has_fts5():
            sql = (
                "SELECT book_no, page_no FROM pali_fts"
                " WHERE pali_fts MATCH ? AND edition=? AND kind='page'"
            )
            params = [self._build_fts_query(literal), self.edition]
            if book_no > 0:
                sql += " AND book_no=?"
                params.append(book_no)
            cand = cur.execute(sql, params).fetchall()
            c2 = self.connection.cursor()
            for r in cand:
                pg = c2.execute(
                    "SELECT unitext FROM pages"
                    " WHERE edition=? AND book_no=? AND page_no=?",
                    (self.edition, r["book_no"], r["page_no"]),
                ).fetchone()
                if pg:
                    yield r["book_no"], r["page_no"], pg["unitext"]
        else:
            sql = "SELECT book_no, page_no, unitext FROM pages WHERE edition=?"
            params = [self.edition]
            if book_no > 0:
                sql += " AND book_no=?"
                params.append(book_no)
            for r in cur.execute(sql, params):
                yield r["book_no"], r["page_no"], r["unitext"]

    def count_regex(self, pattern: str, book_no: int = 0, cap: int = 2000) -> int:
        """Count regex matches (capped at `cap`)."""
        if not self._ensure_connected():
            return 0
        try:
            rx = re.compile(pattern, re.IGNORECASE)
        except re.error:
            return 0
        n = 0
        for _bn, _pn, uni in self._regex_candidates(pattern, book_no):
            if rx.search(decode_unitext(uni or "")):
                n += 1
                if n >= cap:
                    break
        return n

    def search_regex(
        self,
        pattern: str,
        limit: int = 50,
        book_no: int = 0,
        ignorecase: bool = True,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Regex search over page text of the current edition (paginated).

        Prefilters candidate pages via FTS5 when the pattern contains a literal
        token (fast path); otherwise scans the edition's pages. Result shape
        matches the other search methods.
        """
        if not self._ensure_connected():
            return []
        try:
            rx = re.compile(pattern, re.IGNORECASE if ignorecase else 0)
        except re.error as e:
            print(f"Invalid regex: {e}")
            return []

        cur = self.connection.cursor()
        book_cache: Dict[int, Any] = {}
        results: List[Dict[str, Any]] = []
        seen = [0]  # total matches encountered (for offset paging)

        def emit(bn: int, pn: int, text: str) -> bool:
            m = rx.search(text)
            if not m:
                return False
            seen[0] += 1
            if not (offset < seen[0] <= offset + limit):
                return True  # matched but outside the requested page
            if bn not in book_cache:
                book_cache[bn] = self.get_book_info(bn)
            s, e = m.start(), m.end()
            start, end = max(0, s - 50), min(len(text), e + 50)
            # Wrap the match in ⟦…⟧ markers (same convention as the FTS snippet)
            # so the UI can emphasise it.
            body = (text[start:s] + "⟦" + text[s:e] + "⟧" + text[e:end]).replace(
                "\n", " "
            )
            snippet = (
                ("…" if start > 0 else "") + body + ("…" if end < len(text) else "")
            )
            results.append(
                {
                    "word": pattern,
                    "book_no": bn,
                    "page_num": pn,
                    "snippet": snippet,
                    "snippet_html": snippet,
                    "book_info": book_cache.get(bn),
                    "edition": self.edition,
                    "book_name": (
                        (book_cache[bn].get("s_name") or "").strip()
                        if book_cache.get(bn)
                        else ""
                    ),
                }
            )
            return True

        for bn, pn, uni in self._regex_candidates(pattern, book_no):
            emit(bn, pn, decode_unitext(uni or ""))
            if seen[0] >= offset + limit:
                break
        return results

    def search_advanced(self, query: str, book_no: int = 0, limit: int = 100) -> list:
        """Advanced search with optional book filter.

        Scans decoded unitext using LRU cache for repeated access.
        """
        raw_results = self._search_decoded_pages(query, limit, book_no)
        return [
            {
                "book_no": r["book_no"],
                "page_no": r["page_num"],
                "book_name": r.get("book_name", ""),
                "snippet": r["snippet"],
            }
            for r in raw_results
        ]

    def search_highlight(self, query: str, book_no: int = 0, limit: int = 30) -> list:
        """Search with HTML-highlighted snippets."""
        results = self.search_advanced(query, book_no, limit)
        for r in results:
            # Highlight query in snippet
            import re

            snippet = r["snippet"]
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            snippet = pattern.sub(
                lambda m: f'<b style="background:#ff0">{m.group()}</b>', snippet
            )
            r["snippet_html"] = snippet
        return results

    # ── TOC & Chapters ────────────────────────────────────────

    def get_table_of_contents(self, book_no: int) -> List[Dict[str, Any]]:
        if not self._ensure_connected():
            return []
        try:
            cur = self.connection.cursor()
            cur.execute(
                """SELECT name, beg_page, end_page
                   FROM toc
                   WHERE edition=? AND book_no=?
                   ORDER BY beg_page""",
                (self.edition, book_no),
            )
            entries = []
            for row in cur.fetchall():
                name = (row["name"] or "").strip()
                if not name:
                    continue
                entries.append(
                    {
                        "name": name,
                        "beg_page": row["beg_page"],
                        "end_page": row["end_page"],
                    }
                )
            return entries
        except Exception as e:
            print(f"Error getting TOC: {e}")
            return []

    def get_chapter_marks(
        self, book_no: int, edition: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if not self._ensure_connected():
            return []
        try:
            cur = self.connection.cursor()
            cur.execute(
                """SELECT wordmark, page_no
                   FROM chapter_marks
                   WHERE edition=? AND book_no=?
                   ORDER BY page_no""",
                (edition or self.edition, book_no),
            )
            marks = []
            for row in cur.fetchall():
                wm = (row["wordmark"] or "").strip()
                if not wm or len(wm) < 2:
                    continue
                marks.append(
                    {
                        "wordmark": wm,
                        "page_no": row["page_no"],
                    }
                )
            return marks
        except Exception as e:
            print(f"Error getting chapter marks: {e}")
            return []

    def get_head_sections(
        self, book_no: int, edition: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Build virtual TOC from page HEAD fields for books without proper TOC.

        Scans pages looking for HEAD changes that indicate section boundaries.
        Cleans up embedded page numbers and PTS references. `edition` defaults
        to the current edition; pass it explicitly to read another edition
        (e.g. the commentary tree while the main pane stays on the canon).
        """
        if not self._ensure_connected():
            return []
        cache_key = (edition or self.edition, book_no)
        cached = self._head_sections_cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            import re

            cur = self.connection.cursor()
            cur.execute(
                """SELECT page_no, head FROM pages
                   WHERE edition=? AND book_no=?
                   AND head IS NOT NULL AND head != ''
                   ORDER BY page_no""",
                (edition or self.edition, book_no),
            )

            def clean_head(raw: str) -> str:
                """Extract meaningful section title from HEAD field."""
                # Collapse whitespace FIRST: commentary heads carry ~150 spaces
                # of padding, and the trailing-ref regex below backtracks
                # catastrophically over long whitespace runs (multi-second hang).
                h = re.sub(r"\s+", " ", raw).strip()
                # Remove leading page number
                h = re.sub(r"^\d+\s+", "", h)
                # Remove trailing PTS refs and numbers
                h = re.sub(
                    r"\s*\[?[A-Z]?\.?\s*[ivxlc]+\]?\.?\s*\d*\.?\s*\]?\s*\d*\s*$", "", h
                )
                # Remove remaining numbers at end
                h = re.sub(r"\s+\d+\s*$", "", h)
                # Remove artifact chars
                h = h.strip(" _-[]()")
                return h.strip()

            def is_meaningful(title: str) -> bool:
                if not title or len(title) < 3:
                    return False
                if title.isdigit():
                    return False
                if not re.search(r"[A-Za-z\u0100-\u1ef9]", title):
                    return False
                return True

            sections = []
            seen = set()
            last_title = None

            for row in cur.fetchall():
                raw = (row["head"] or "").strip()
                page = row["page_no"]
                title = clean_head(raw)

                if not is_meaningful(title):
                    continue
                if title == last_title:
                    continue
                last_title = title

                # Normalize for dedup
                norm = re.sub(
                    r"[\u0101\u012b\u016b\u1e41\u1e43\u1e47\u1e6d\u1e0d\u00f1\u1e37\u0100\u012a\u016a\u1e40\u1e42\u1e46\u1e6c\u1e0c\u00d1\u1e36]",
                    "",
                    title.lower(),
                )
                norm = re.sub(r"\s+", " ", norm).strip()
                if norm in seen:
                    continue
                seen.add(norm)

                sections.append(
                    {
                        "name": title[:80],
                        "beg_page": page,
                        "end_page": page,
                    }
                )

            # Limit if too many
            if len(sections) > 80:
                step = max(1, len(sections) // 40)
                sections = [sections[0]] + sections[1:-1:step] + [sections[-1]]

            self._head_sections_cache[cache_key] = sections
            return sections
        except Exception:
            return []

    def get_thai_text(self, book_no: int, page_num: int) -> str:
        """Get Thai-script text via mathematical composition f(g(x)).

        g: PUA bytes → IAST string (alignment)
        f: IAST string → Thai Unicode (standard Royal Thai transliteration)
        """
        if not self._ensure_connected():
            return ""
        try:
            import re
            from collections import Counter

            cur = self.connection.cursor()
            cur.execute(
                "SELECT encpali, unitext FROM pages WHERE edition=? AND book_no=? AND page_no=?",
                (self.edition, book_no, page_num),
            )
            row = cur.fetchone()
            if not row or not row["encpali"] or not row["unitext"]:
                return ""

            # Decode ENCPALI → PUA text (using shared decoder)
            enc_text = decode_encpali(row["encpali"])
            if not enc_text:
                return ""
            # Decode UNITEXT → Romanized Pali
            pali_text = decode_unitext(row["unitext"])

            # === Build g: PUA byte → IAST char via token-level alignment ===
            byte_to_iast = Counter()
            enc_tokens = re.findall(r"\S+|\s+", enc_text)
            pali_tokens = re.findall(r"\S+|\s+", pali_text)

            for etok, utok in zip(enc_tokens, pali_tokens):
                if etok.isspace() or utok.isspace():
                    continue
                ej = uj = 0
                ecs, ucs = list(etok), list(utok)
                while ej < len(ecs) and uj < len(ucs):
                    ecp = ord(ecs[ej])
                    if 0xE000 <= ecp <= 0xE0FF:
                        byte_to_iast[(ecp & 0xFF, ucs[uj])] += 1
                        ej += 1
                        uj += 1
                    elif 0x20 <= ecp <= 0x7E and ecs[ej] == ucs[uj]:
                        ej += 1
                        uj += 1
                    else:
                        ej += 1

            g = {}
            for (b, iast), c in byte_to_iast.most_common():
                if b not in g:
                    g[b] = iast

            # === Apply g: map PUA text → IAST string ===
            iast_chars = []
            for ch in enc_text:
                cp = ord(ch)
                if 0xE000 <= cp <= 0xE0FF:
                    iast_chars.append(g.get(cp & 0xFF, "□"))
                else:
                    iast_chars.append(ch)
            iast_text = "".join(iast_chars)

            # === Apply f: IAST string → Thai Unicode ===
            CONS = {
                "k": "ก",
                "kh": "ข",
                "g": "ค",
                "gh": "ฆ",
                "ṅ": "ง",
                "c": "จ",
                "ch": "ฉ",
                "j": "ช",
                "jh": "ฌ",
                "ñ": "ญ",
                "ṭ": "ฏ",
                "ṭh": "ฐ",
                "ḍ": "ฑ",
                "ḍh": "ฒ",
                "ṇ": "ณ",
                "t": "ต",
                "th": "ถ",
                "d": "ท",
                "dh": "ธ",
                "n": "น",
                "p": "ป",
                "ph": "ผ",
                "b": "พ",
                "bh": "ภ",
                "m": "ม",
                "y": "ย",
                "r": "ร",
                "l": "ล",
                "v": "ว",
                "s": "ส",
                "h": "ห",
                "ḷ": "ฬ",
            }
            for k, v in list(CONS.items()):
                CONS[k.upper()] = v

            VOWEL_SIGN = {
                "ā": "า",
                "i": "ิ",
                "ī": "ี",
                "u": "ุ",
                "ū": "ู",
                "Ā": "า",
                "I": "ิ",
                "Ī": "ี",
                "U": "ุ",
                "Ū": "ู",
            }
            VOWEL_PRE = {"e": "เ", "o": "โ", "E": "เ", "O": "โ"}
            NIGGAHITA = {"ṃ": "ํ", "Ṃ": "ํ"}
            STANDALONE = {
                "a": "อ",
                "ā": "อา",
                "i": "อิ",
                "ī": "อี",
                "u": "อุ",
                "ū": "อู",
                "e": "เอ",
                "o": "โอ",
                "A": "อ",
                "Ā": "อา",
                "I": "อิ",
                "Ī": "อี",
                "U": "อุ",
                "Ū": "อู",
                "E": "เอ",
                "O": "โอ",
            }

            result = []
            i = 0
            while i < len(iast_text):
                ch = iast_text[i]

                if ch in " \n\r\t.-,;:()[]{}|║\"'":
                    result.append(ch)
                    i += 1
                    continue
                if ch in NIGGAHITA:
                    result.append(NIGGAHITA[ch])
                    i += 1
                    continue
                if ch.isdigit():
                    result.append(ch)
                    i += 1
                    continue

                # Aspirated consonant
                if i + 1 < len(iast_text) and ch + iast_text[i + 1] in CONS:
                    tc = CONS[ch + iast_text[i + 1]]
                    i += 2
                    if i < len(iast_text) and iast_text[i] in VOWEL_SIGN:
                        result.append(tc + VOWEL_SIGN[iast_text[i]])
                        i += 1
                    elif i < len(iast_text) and iast_text[i] in VOWEL_PRE:
                        pre = VOWEL_PRE[iast_text[i]]
                        i += 1
                        if i < len(iast_text) and iast_text[i] in VOWEL_SIGN:
                            result.append(pre + tc + VOWEL_SIGN[iast_text[i]])
                            i += 1
                        else:
                            result.append(pre + tc)
                    elif i < len(iast_text) and iast_text[i].lower() == "a":
                        result.append(tc)
                        i += 1
                    else:
                        result.append(tc)
                    continue

                # Simple consonant
                if ch in CONS:
                    tc = CONS[ch]
                    i += 1
                    if i < len(iast_text) and iast_text[i] in VOWEL_SIGN:
                        result.append(tc + VOWEL_SIGN[iast_text[i]])
                        i += 1
                    elif i < len(iast_text) and iast_text[i] in VOWEL_PRE:
                        pre = VOWEL_PRE[iast_text[i]]
                        i += 1
                        if i < len(iast_text) and iast_text[i] in VOWEL_SIGN:
                            result.append(pre + tc + VOWEL_SIGN[iast_text[i]])
                            i += 1
                        else:
                            result.append(pre + tc)
                    elif i < len(iast_text) and iast_text[i].lower() == "a":
                        result.append(tc)
                        i += 1
                    else:
                        result.append(tc)
                    continue

                # Standalone vowel
                if ch in STANDALONE:
                    result.append(STANDALONE[ch])
                    i += 1
                    continue

                result.append(ch)
                i += 1

            return "".join(result)
        except Exception:
            return ""

    def get_nav_tree(self) -> list:
        """Get hierarchical navigation tree from nav_tree table.

        Returns list of root nodes with nested children.
        Each node: {key, text, book_no, page_no, children: [...]}
        """
        if not self._ensure_connected():
            return []
        try:
            cur = self.connection.cursor()
            # Get all nodes ordered
            cur.execute(
                "SELECT key, parent, text, book_no, page_no FROM nav_tree ORDER BY key"
            )
            nodes = {}
            roots = []
            for row in cur.fetchall():
                node = {
                    "key": row["key"],
                    "parent": row["parent"],
                    "text": row["text"] or "",
                    "book_no": row["book_no"],
                    "page_no": row["page_no"],
                    "children": [],
                }
                nodes[node["key"]] = node

            # Build tree
            for key, node in nodes.items():
                parent_key = node["parent"]
                if parent_key and parent_key in nodes:
                    nodes[parent_key]["children"].append(node)
                else:
                    roots.append(node)

            return roots
        except Exception:
            return []

    def get_nav_children(self, parent_key: str) -> list:
        """Get direct children of a nav tree node."""
        if not self._ensure_connected():
            return []
        try:
            cur = self.connection.cursor()
            cur.execute(
                "SELECT key, text, book_no, page_no FROM nav_tree WHERE parent=? ORDER BY key",
                (parent_key,),
            )
            return [dict(row) for row in cur.fetchall()]
        except Exception:
            return []

    # ── Canon ↔ commentary alignment (page HEAD anchors) ──────
    #
    # Both editions print, in the running HEAD of (almost) every page, a
    # bracketed canonical reference — canon Dīgha "[D. i. 1. 2", commentary
    # "[D. I. 1. 4.]". The numeric tail (roman-volume, sutta, section) is the
    # SAME coordinate on both sides, so a sutta page can be aligned to the page
    # of its commentary by matching that tuple. The sigla is ignored: the
    # commentary book is already fixed by ROTA_TO_ROTB, so matching happens
    # within that one book and the sigla carries no extra information.

    # Bracketed running-head segment: "[ … " (recto, open) or " … ]" (verso).
    _ANCHOR_SEG = re.compile(r"\[([^\]]*)|([^\[]*)\]")
    # roman-volume . sutta [ . section ] inside such a segment.
    _ANCHOR_REF = re.compile(r"([ivxlcdmIVXLCDM]{1,6})\.?\s*(\d+)\.?\s*(\d+)?")

    def _parse_head_anchor(self, head: Optional[str]):
        """Extract the canonical reference tuple (vol, sutta, section) from a
        page HEAD, or None. Reads only the bracketed running-head segment so
        stray digits elsewhere in the HEAD never leak in."""
        if not head:
            return None
        for seg in self._ANCHOR_SEG.findall(head):
            s = seg[0] or seg[1] or ""
            m = self._ANCHOR_REF.search(s)
            if not m:
                continue
            vol = self._citation_parser.parse_roman_numeral(m.group(1))
            # Reject implausible volumes (a stray "c"/"d"/"m" parses as a large
            # roman). Real canonical volumes/saṃyuttas are small.
            if not vol or vol > 60:
                continue
            sutta = int(m.group(2))
            section = int(m.group(3)) if m.group(3) else 0
            return (vol, sutta, section)
        return None

    def build_anchor_index(
        self, edition: str, book_no: int
    ) -> Dict[str, Any]:
        """Anchor index for ONE book (built once per book, then cached).

        Per-book (not per-edition) so the first commentary toggle scans only the
        ~hundreds of pages of the two books involved, not the whole 578 MB DB.
        Returns {"pages": [(page_no, ref), … sorted],
                 "refmin": {ref: first_page}, "sorted_refs": [ref, … sorted]}.
        """
        key = (edition, book_no)
        cached = self._anchor_cache.get(key)
        if cached is not None:
            return cached
        idx: Dict[str, Any] = {"pages": [], "refmin": {}, "sorted_refs": []}
        if self._ensure_connected():
            try:
                cur = self.connection.cursor()
                cur.execute(
                    "SELECT page_no, head, head_old FROM pages "
                    "WHERE edition=? AND book_no=? ORDER BY page_no",
                    (edition, book_no),
                )
                for page_no, head, head_old in cur:
                    ref = self._parse_head_anchor(head) or self._parse_head_anchor(
                        head_old
                    )
                    if not ref:
                        continue
                    idx["pages"].append((page_no, ref))
                    if ref not in idx["refmin"] or page_no < idx["refmin"][ref]:
                        idx["refmin"][ref] = page_no
                idx["sorted_refs"] = sorted(idx["refmin"].keys())
            except Exception as e:
                print(f"Error building anchor index: {e}")
        self._anchor_cache[key] = idx
        return idx

    @staticmethod
    def _ref_at_page(book_idx: Optional[Dict[str, Any]], page: int):
        """Canonical ref governing `page`: the anchor at or before it."""
        if not book_idx:
            return None
        best = None
        for pg, ref in book_idx["pages"]:
            if pg <= page:
                best = ref
            else:
                break
        return best

    @staticmethod
    def _page_for_ref(book_idx: Optional[Dict[str, Any]], ref):
        """(page, exact) for a ref in a book index: exact hit, else the nearest
        preceding anchor; (None, False) when the book has no usable anchor."""
        if not book_idx or not ref:
            return None, False
        if ref in book_idx["refmin"]:
            return book_idx["refmin"][ref], True
        import bisect

        sr = book_idx["sorted_refs"]
        i = bisect.bisect_right(sr, ref) - 1
        if i >= 0:
            return book_idx["refmin"][sr[i]], False
        return None, False

    def _commentary_breadcrumb(self, comm_book: int, ref) -> str:
        """Human breadcrumb for a commentary location: cleaned work title +
        the canonical reference it glosses (e.g. "Sumaṅgalavilāsinī · ad §1.2")."""
        title = ""
        info = self._book_info_for_edition("atthakatha", comm_book)
        if info and info.get("s_name"):
            title = info["s_name"]
        if not title.strip():
            secs = self.get_head_sections(comm_book, edition="atthakatha")
            if secs:
                title = secs[0]["name"]
        title = re.sub(r"\s+", " ", title or "").strip(" .")
        # Drop a trailing stray single letter (encpali leftover, e.g. "… . P").
        title = re.sub(r"[ .]+[A-Za-z]$", "", title).strip(" .")
        if not title:
            title = f"Comentario · libro {comm_book}"
        if ref:
            vol, sutta, section = ref
            tail = f"{vol}.{sutta}" + (f".{section}" if section else "")
            return f"{title} · ad §{tail}"
        return title

    def _fallback_commentary_page(
        self, comm_book: int, mula_book: int, mula_page: int
    ) -> int:
        """No anchor available: estimate the commentary page proportionally
        within the book, then snap back to the start of the enclosing
        HEAD-section so the reader lands at a clean boundary."""
        mb = self._book_info_for_edition("mula", mula_book)
        cb = self._book_info_for_edition("atthakatha", comm_book)
        cb_beg = (cb or {}).get("beg_page") or 1
        cb_end = (cb or {}).get("end_page") or cb_beg
        est = cb_beg
        if mb and cb:
            mb_beg = mb.get("beg_page") or 1
            mb_end = mb.get("end_page") or mb_beg
            if mb_end > mb_beg and cb_end > cb_beg:
                frac = (mula_page - mb_beg) / (mb_end - mb_beg)
                frac = min(max(frac, 0.0), 1.0)
                est = round(cb_beg + frac * (cb_end - cb_beg))
        begs = sorted(
            s["beg_page"]
            for s in self.get_head_sections(comm_book, edition="atthakatha")
        )
        snapped = max((b for b in begs if b <= est), default=cb_beg)
        return snapped or 1

    def map_canon_to_commentary(
        self, mula_book: int, mula_page: int
    ) -> Optional[Dict[str, Any]]:
        """Map a canon (book, page) to its commentary location.

        Returns {"book", "page", "approx": bool, "reason": str,
                 "breadcrumb": str} or None when no commentary is mapped.
        """
        comm_book = ROTA_TO_ROTB.get(mula_book)
        if comm_book is None:
            return None
        canon_idx = self.build_anchor_index("mula", mula_book)
        comm_idx = self.build_anchor_index("atthakatha", comm_book)
        ref = self._ref_at_page(canon_idx, mula_page)
        if ref and comm_idx:
            page, exact = self._page_for_ref(comm_idx, ref)
            if page:
                return {
                    "book": comm_book,
                    "page": page,
                    "approx": not exact,
                    "reason": "exacta" if exact else "ancla más cercana",
                    "breadcrumb": self._commentary_breadcrumb(comm_book, ref),
                }
        page = self._fallback_commentary_page(comm_book, mula_book, mula_page)
        return {
            "book": comm_book,
            "page": page,
            "approx": True,
            "reason": "sin ancla canónica — alineación aproximada por sección",
            "breadcrumb": self._commentary_breadcrumb(comm_book, None),
        }

    def map_commentary_to_canon(
        self, comm_book: int, comm_page: int
    ) -> Optional[Dict[str, Any]]:
        """Reverse direction: commentary (book, page) → canon location."""
        canon_books = ROTB_TO_ROTA.get(comm_book)
        if not canon_books:
            return None
        comm_idx = self.build_anchor_index("atthakatha", comm_book)
        ref = self._ref_at_page(comm_idx, comm_page)
        if ref:
            for cb in canon_books:
                page, exact = self._page_for_ref(
                    self.build_anchor_index("mula", cb), ref
                )
                if page:
                    return {
                        "book": cb,
                        "page": page,
                        "approx": not exact,
                        "reason": "exacta" if exact else "ancla más cercana",
                    }
        # Fallback: first canonical volume, its first page.
        cb = canon_books[0]
        info = self._book_info_for_edition("mula", cb)
        return {
            "book": cb,
            "page": (info or {}).get("beg_page") or 1,
            "approx": True,
            "reason": "sin ancla canónica",
        }

    # ── Editions ──────────────────────────────────────────────

    def get_editions(self) -> List[Dict[str, Any]]:
        if not self._ensure_connected():
            return []
        try:
            cur = self.connection.cursor()
            cur.execute("SELECT id, name, description FROM editions")
            return [dict(row) for row in cur.fetchall()]
        except Exception:
            return []

    def set_edition(self, edition: str) -> None:
        if edition == self.edition:
            return
        self.edition = edition
        # The page cache is keyed on (self, book_no, page_num) and does NOT
        # include the edition, so it must be cleared when the edition changes;
        # otherwise stale pages from the previous edition are returned.
        clear = getattr(self.get_page_by_book_and_page, "cache_clear", None)
        if callable(clear):
            clear()
