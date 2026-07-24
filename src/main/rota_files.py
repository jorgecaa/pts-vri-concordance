"""
ROTA Edition — API-backed text reader for the Syāmaraṭṭha-Tipiṭaka (Royal Thai).

Uses the rota_api module to serve cleaned text (apparatus blocks and
footnote references removed) from the new file-based rota collection.

File format (new):
    Page boundaries: [page 001], [page 002], …
    PTS cross-refs:  < PTS. D I , 2 >
    Footnote refs:   [^1], [^2], …
    Apparatus blocks: * * * * * * … Footnote: … -----------------
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ROTAPage:
    """A single page from the ROTA edition."""

    book_no: int
    page_num: int
    raw_text: str  # full text with PTS tags preserved
    display_text: str  # cleaned text (no apparatus, no footnote refs)
    lines: List[str] = field(default_factory=list)
    pts_refs: List[Dict[str, Any]] = field(default_factory=list)
    footnotes: List[str] = field(default_factory=list)
    title: str = ""
    has_text: bool = False


# Book number → PTS abbreviation mapping
# Based on the standard Tipitaka book numbering
BOOK_TO_PTS = {
    # Vinaya (1-8) – not exposed via D/M/S/A API
    # Dīgha Nikāya (9-11)
    9: ("D", 1),
    10: ("D", 2),
    11: ("D", 3),
    # Majjhima Nikāya (12-14)
    12: ("M", 1),
    13: ("M", 2),
    14: ("M", 3),
    # Saṃyutta Nikāya (15-19)
    15: ("S", 1),
    16: ("S", 2),
    17: ("S", 3),
    18: ("S", 4),
    19: ("S", 5),
    # Aṅguttara Nikāya (20-24)
    20: ("A", 1),
    21: ("A", 2),
    22: ("A", 3),
    23: ("A", 4),
    24: ("A", 5),
}


class ROTAFilesReader:
    """Read ROTA edition text via the rota_api module."""

    # PTS tag pattern for extracting references
    _PTS_TAG_RE = re.compile(r"<\s*PTS\.\s+([A-Za-z]+)\s+([IVX0-9]+)\s*,\s*(\d+)\s*>")

    def __init__(self, rota_dir: Optional[str] = None):
        if rota_dir:
            self.rota_dir = Path(rota_dir)
        else:
            self.rota_dir = Path(__file__).parent.parent / "data" / "rota"

        self._cache: Dict[str, ROTAPage] = {}
        self._book_index: Dict[int, str] = {}
        self._api = None
        self._scan_files()

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _scan_files(self) -> None:
        """Scan rota directory for .txt files and map book numbers."""
        if not self.rota_dir.exists():
            return
        # New naming: 09_Sutta_DN_Siilakhanda.txt, 12_Sutta_MN_Muu.txt, etc.
        for fname in sorted(self.rota_dir.glob("*.txt")):
            m = re.match(r"(\d+)_", fname.name)
            if m:
                book_no = int(m.group(1))
                if book_no <= 24:  # Only sutta pitaka + vinaya (API covers D/M/S/A)
                    self._book_index[book_no] = str(fname)

    def get_available_books(self) -> List[int]:
        return sorted(self._book_index.keys())

    def has_book(self, book_no: int) -> bool:
        return book_no in self._book_index

    # ------------------------------------------------------------------
    # Lazy API init
    # ------------------------------------------------------------------

    def _get_api(self):
        if self._api is None:
            # rota_api lives in src/data/rota/, not in the main package
            api_dir = str(self.rota_dir)
            import sys

            if api_dir not in sys.path:
                sys.path.insert(0, api_dir)
            from rota_api import RotaAPI

            self._api = RotaAPI(api_dir)
        return self._api

    # ------------------------------------------------------------------
    # PTS citation → ROTA segment (primary access method)
    # ------------------------------------------------------------------

    def get_page_by_pts_citation(
        self, abbreviation: str, volume: str, page: int
    ) -> Optional[ROTAPage]:
        """
        Find text by PTS citation using the rota API.

        Args:
            abbreviation: PTS book abbreviation (D, M, S, A)
            volume: Roman numeral or integer
            page: PTS page number

        Returns:
            ROTAPage with cleaned display_text.
        """
        # Resolve volume to int
        roman_map = {
            "I": 1,
            "II": 2,
            "III": 3,
            "IV": 4,
            "V": 5,
            "VI": 6,
            "VII": 7,
            "VIII": 8,
            "IX": 9,
            "X": 10,
            "XI": 11,
            "XII": 12,
        }
        vol_upper = volume.upper()
        vol_int = roman_map.get(vol_upper)
        if vol_int is None:
            try:
                vol_int = int(volume)
            except ValueError:
                print(f"Invalid volume: {volume}")
                return None

        try:
            api = self._get_api()
            text = api.get_page(abbreviation, vol_int, page)
        except Exception as e:
            print(f"ROTA API error: {e}")
            return None

        if not text:
            return None

        # Extract PTS refs from the text
        pts_refs = []
        for m in self._PTS_TAG_RE.finditer(text):
            pts_refs.append(
                {
                    "abbreviation": m.group(1),
                    "volume": m.group(2),
                    "page": int(m.group(3)),
                    "citation": f"{m.group(1)} {m.group(2)} {m.group(3)}",
                }
            )

        # Extract local page number from header
        local_page = 0
        m = re.match(r"\[Local page (\d{3})\]", text)
        if m:
            local_page = int(m.group(1))
            # Strip the header line
            text = re.sub(r"^\[Local page \d{3}\]\n?", "", text)

        # Build display text (strip PTS tags)
        display = self._PTS_TAG_RE.sub("", text).strip()
        # Clean up extra whitespace
        display = re.sub(r" {2,}", " ", display)

        # Title: first non-empty line
        title = ""
        for line in display.split("\n"):
            s = line.strip()
            if s:
                title = s
                break

        # Try to find book_no from the abbreviation
        book_no = self._find_book_no(abbreviation, vol_int)

        return ROTAPage(
            book_no=book_no or 0,
            page_num=local_page,
            raw_text=text.strip(),
            display_text=display,
            lines=text.split("\n"),
            pts_refs=pts_refs,
            footnotes=[],
            title=title,
            has_text=bool(display),
        )

    def _find_book_no(self, abbreviation: str, volume: int) -> Optional[int]:
        """Find book number from PTS abbreviation and volume."""
        for bno, (abbr, vol) in BOOK_TO_PTS.items():
            if abbr == abbreviation and vol == volume:
                return bno
        return None

    # ------------------------------------------------------------------
    # Page access (book_no, page_num)
    # ------------------------------------------------------------------

    def get_page(self, book_no: int, page_num: int) -> Optional[ROTAPage]:
        """
        Get a page by internal book number and local page number.

        Uses the rota API which maps book_no → PTS (nikaya, volume) and
        looks up the closest PTS page that contains the local page.
        """
        cache_key = f"{book_no}:{page_num:03d}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Check if we have this book
        if book_no not in BOOK_TO_PTS:
            return None

        nikaya, volume = BOOK_TO_PTS[book_no]

        try:
            api = self._get_api()

            # Get available PTS pages for this nikaya/volume
            available = api.list_available(nikaya)
            prefix = f"{nikaya}_{volume}_"
            pts_pages = sorted(
                [int(k.split("_")[2]) for k in available if k.startswith(prefix)]
            )

            if not pts_pages:
                return None

            # Iterate through available PTS pages to find the target local page.
            # A PTS page may span multiple local pages, so check if the target
            # local page appears anywhere in the text (not just the header).
            # If the target page is the START of a PTS page, prefer that one.
            best_match = None
            for pts_page in pts_pages:
                text = api.get_page(nikaya, volume, pts_page)
                if not text:
                    continue

                # Check if the target local page is contained in this PTS page
                header_m = re.search(r"\[Local page (\d{3})\]", text)
                if not header_m:
                    continue
                start_local = int(header_m.group(1))

                # Also check for continuation pages like [page 004]
                all_locals = re.findall(r"\[page (\d{3})\]", text)
                all_locals_int = [start_local] + [int(x) for x in all_locals]

                is_match = page_num == start_local or page_num in all_locals_int
                is_exact_start = page_num == start_local

                if is_match:
                    if is_exact_start:
                        # Prefer exact start — return immediately
                        best_match = (pts_page, text)
                        break
                    elif best_match is None:
                        best_match = (pts_page, text)

            if best_match is None:
                return None

            pts_page, text = best_match
            pts_refs = []
            for m2 in self._PTS_TAG_RE.finditer(text):
                pts_refs.append(
                    {
                        "abbreviation": m2.group(1),
                        "volume": m2.group(2),
                        "page": int(m2.group(3)),
                        "citation": f"{m2.group(1)} {m2.group(2)} {m2.group(3)}",
                    }
                )

            # Strip header
            body = re.sub(r"^\[Local page \d{3}\]\n?", "", text)
            display = self._PTS_TAG_RE.sub("", body).strip()
            display = re.sub(r" {2,}", " ", display)

            title = ""
            for line in body.split("\n"):
                s = line.strip()
                if s:
                    title = s
                    break

            page = ROTAPage(
                book_no=book_no,
                page_num=page_num,
                raw_text=body.strip(),
                display_text=display,
                lines=body.split("\n"),
                pts_refs=pts_refs,
                footnotes=[],
                title=title,
                has_text=bool(display),
            )
            self._cache[cache_key] = page
            return page

        except Exception as e:
            print(f"Error reading ROTA page {book_no}:{page_num}: {e}")

        return None

    # ------------------------------------------------------------------
    # Page range
    # ------------------------------------------------------------------

    def get_page_range(self, book_no: int) -> Tuple[int, int]:
        """Get the range of local page numbers for a book."""
        file_path = self._book_index.get(book_no)
        if not file_path or not os.path.exists(file_path):
            return (0, 0)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            markers = [
                int(m.group(1)) for m in re.finditer(r"\[page\s+(\d{3})\]", content)
            ]
            if not markers:
                return (0, 0)
            return (min(markers), max(markers))
        except Exception:
            return (0, 0)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_in_text(
        self, query: str, book_no: Optional[int] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search in ROTA text."""
        results: List[Dict[str, Any]] = []
        query_lower = query.lower()
        books = [book_no] if book_no else self.get_available_books()

        for bno in books:
            if bno not in BOOK_TO_PTS:
                continue
            nikaya, volume = BOOK_TO_PTS[bno]

            try:
                api = self._get_api()
                # Get all available PTS pages for this book
                available = api.list_available(nikaya)
                prefix = f"{nikaya}_{volume}_"
                pages = [
                    int(k.split("_")[2]) for k in available if k.startswith(prefix)
                ]

                for pts_page in pages:
                    text = api.get_page(nikaya, volume, pts_page)
                    if not text:
                        continue
                    if query_lower in text.lower():
                        pos = text.lower().find(query_lower)
                        ctx_s = max(0, pos - 80)
                        ctx_e = min(len(text), pos + len(query) + 80)
                        results.append(
                            {
                                "book_no": bno,
                                "page_num": pts_page,
                                "context": text[ctx_s:ctx_e].strip(),
                            }
                        )
                        if len(results) >= limit:
                            return results
            except Exception as e:
                print(f"Error searching book {bno}: {e}")

        return results

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def clear_cache(self) -> None:
        self._cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        return {
            "cached_pages": len(self._cache),
            "available_books": len(self._book_index),
            "book_numbers": sorted(self._book_index.keys()),
        }


def create_rota_files_reader(rota_dir: Optional[str] = None) -> ROTAFilesReader:
    return ROTAFilesReader(rota_dir)


def get_rota_page(
    book_no: int, page_num: int, rota_dir: Optional[str] = None
) -> Optional[ROTAPage]:
    return create_rota_files_reader(rota_dir).get_page(book_no, page_num)
