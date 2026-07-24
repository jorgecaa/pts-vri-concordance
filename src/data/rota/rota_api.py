"""
rota_api.py – API to query Pali Text Society (PTS) edition texts.

Usage
-----
    >>> from rota_api import RotaAPI
    >>> api = RotaAPI("/path/to/rota")
    >>> text = api.get_page("D", 1, 2)     # Dīgha Nikāya, vol 1, PTS page 2
    >>> print(text[:200])

The main lookup function receives (NIKAYA, VOLUME, PAGE):
  - NIKAYA: "D" (Dīgha), "M" (Majjhima), "S" (Saṃyutta), "A" (Aṅguttara)
  - VOLUME: integer (1, 2, 3, …)
  - PAGE:   integer (PTS page number)

Returns the full text surrounding that PTS page marker.
"""

import os
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Index handling
# ---------------------------------------------------------------------------


def _build_index_if_missing(rota_dir: str) -> str:
    """Ensure index.tsv exists; build it via build_index.sh if not."""
    index_path = os.path.join(rota_dir, "index.tsv")
    if not os.path.exists(index_path):
        import subprocess

        script = os.path.join(rota_dir, "build_index.sh")
        subprocess.run(["bash", script], check=True, capture_output=True)
    return index_path


def _load_index(index_path: str) -> dict[str, tuple[str, int]]:
    """Load the TSV index into a dict: label -> (filename, line_offset)."""
    idx: dict[str, tuple[str, int]] = {}
    with open(index_path, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 3:
                label, filename, offset = parts
                idx[label] = (filename, int(offset))
    return idx


# ---------------------------------------------------------------------------
# Critical apparatus cleaning
# ---------------------------------------------------------------------------

# Matches lines like "* * * * * *" or "* * *" (3+ asterisks separated by spaces)
_APPARATUS_START_RE = re.compile(r"^\s*(?:\*\s+){2,}\*\s*$")
# Matches separator lines like "-------------------------------------------------"
_APPARATUS_END_RE = re.compile(r"^\s*-{10,}\s*$")

# Inline footnote references: [^1], [^2], etc.
_FOOTNOTE_REF_RE = re.compile(r"\s*\[\^\d+\]\s*")


def clean_apparatus(text: str) -> str:
    """
    Remove critical-apparatus blocks and inline footnote references.

    An apparatus block is delimited by:
      - a start marker: a line of 3+ asterisks, e.g. ``* * * * * *``
      - an end   marker: a long dash line,  e.g. ``------------------``

    Everything from (and including) the start marker through the end
    marker is stripped.  Multiple blocks per page are handled.

    Inline footnote references like ``[^1]``, ``[^2]`` are also removed.
    """
    lines = text.split("\n")
    result: list[str] = []
    inside = False

    for line in lines:
        if not inside and _APPARATUS_START_RE.match(line):
            inside = True
            continue
        if inside and _APPARATUS_END_RE.match(line):
            inside = False
            continue
        if not inside:
            # Remove inline footnote references like [^1], [^2]
            line = _FOOTNOTE_REF_RE.sub(" ", line)
            # Collapse multiple spaces created by removal
            line = re.sub(r" {2,}", " ", line)
            result.append(line)

    cleaned = "\n".join(result)
    # Collapse any triple+ blank lines left behind into at most one blank line
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


# Shared normalization — delegates to the common module
try:
    from .text_normalization import normalize_text
except ImportError:
    import sys as _sys

    _mod_file = _sys.modules[__name__].__file__
    if _mod_file:
        _rota_dir = __import__("os").path.dirname(_mod_file)
        if _rota_dir not in _sys.path:
            _sys.path.insert(0, _rota_dir)
    from text_normalization import normalize_text

# ---------------------------------------------------------------------------
# Local page detection
# ---------------------------------------------------------------------------

_LOCAL_PAGE_RE = re.compile(r"^\s*\[page\s+(\d{3})\]\s*$")


def _find_local_pages(lines: list[str], start_line: int) -> tuple[int, int]:
    """
    Given all lines of a file and the line offset of a PTS marker,
    find the local page boundaries (start, end) that contain that marker.

    Returns (local_page_start_line, next_local_page_start_line).
    The text for the PTS page is lines[start:end].
    """
    # Search backwards from start_line to find the local page header
    local_start = start_line
    for i in range(start_line, -1, -1):
        if _LOCAL_PAGE_RE.match(lines[i]):
            local_start = i
            break

    # Search forwards for the next local page header
    local_end = len(lines)
    for i in range(start_line + 1, len(lines)):
        if _LOCAL_PAGE_RE.match(lines[i]):
            local_end = i
            break

    return local_start, local_end


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------


class RotaAPI:
    """API to look up PTS-referenced text from the rota collection."""

    NIKAYA_MAP = {
        "D": "D",  # Dīgha Nikāya
        "M": "M",  # Majjhima Nikāya
        "S": "S",  # Saṃyutta Nikāya
        "A": "A",  # Aṅguttara Nikāya
    }

    def __init__(self, rota_dir: str):
        self.rota_dir = rota_dir
        index_path = _build_index_if_missing(rota_dir)
        self.index = _load_index(index_path)
        # Cache loaded file lines
        self._file_cache: dict[str, list[str]] = {}

    def _load_file(self, filename: str) -> list[str]:
        """Load a text file into lines, cached."""
        if filename not in self._file_cache:
            fpath = os.path.join(self.rota_dir, filename)
            with open(fpath, encoding="utf-8") as f:
                self._file_cache[filename] = f.read().splitlines()
        return self._file_cache[filename]

    def get_page(self, nikaya: str, volume: int, page: int) -> str:
        """
        Retrieve the text for a given PTS reference.

        Parameters
        ----------
        nikaya : str  – "D", "M", "S", or "A"
        volume : int  – volume number (e.g. 1, 2, 3…)
        page   : int  – PTS page number

        Returns
        -------
        str – the text content for that PTS page

        Raises
        ------
        KeyError if the reference is not found.
        """
        nikaya_upper = nikaya.upper()
        if nikaya_upper not in self.NIKAYA_MAP:
            raise ValueError(f"Unknown nikaya '{nikaya}'. Must be one of: D, M, S, A")

        label = f"{nikaya_upper}_{volume}_{page}"
        if label not in self.index:
            raise KeyError(
                f"PTS reference not found: {label}. "
                f"Available examples: {list(self.index.keys())[:5]}"
            )

        filename, line_offset = self.index[label]
        lines = self._load_file(filename)

        # Find the next PTS marker to determine segment end
        _PTS_TAG_RE = re.compile(r"< PTS\.\s+[A-Za-z]+\s+[IVX0-9]+\s*,\s*\d+\s*>")
        next_marker_line = None
        for i in range(line_offset + 1, len(lines)):
            if _PTS_TAG_RE.search(lines[i]):
                next_marker_line = i
                break

        # Segment end: just before the next PTS marker
        seg_end = next_marker_line if next_marker_line is not None else len(lines)

        # Find the local page number at the segment start
        local_page = None
        for i in range(line_offset, -1, -1):
            m = _LOCAL_PAGE_RE.match(lines[i])
            if m:
                local_page = m.group(1)
                break

        # Extract text from the PTS marker line to the next PTS marker.
        # Include the marker line (stripping the PTS tag) and all lines
        # up to (but not including) the line of the next PTS marker.
        # This correctly spans multiple local pages if needed.
        text_lines = list(lines[line_offset:seg_end])
        # Strip the PTS tag from the first line
        text_lines[0] = _PTS_TAG_RE.sub("", text_lines[0])
        # Clean up: remove leading/trailing empty lines and page separators
        while text_lines and not text_lines[0].strip():
            text_lines.pop(0)
        while text_lines and not text_lines[-1].strip():
            text_lines.pop()
        # Remove separator lines like "-------------------------"
        text_lines = [ln for ln in text_lines if not re.match(r"^\s*-{3,}\s*$", ln)]

        result = "\n".join(text_lines)
        result = clean_apparatus(result)

        if local_page:
            result = f"[Local page {local_page}]\n{result}"

        return result

    # ------------------------------------------------------------------
    # Normalized text (comparable across editions)
    # ------------------------------------------------------------------

    def get_normalized(self, nikaya: str, volume: int, page: int) -> str:
        """
        Get ROTA text fully normalized for cross-edition comparison.

        Removes hyphenation line breaks, normalizes whitespace,
        strips apparatus refs and footnote refs.

        Args:
            nikaya: "D", "M", "S", or "A"
            volume: volume number
            page:   PTS page number

        Returns:
            Normalized text.
        """
        raw = self.get_page(nikaya, volume, page)
        return normalize_text(raw)

    def list_available(self, nikaya: str | None = None) -> list[str]:
        """List all available PTS references, optionally filtered by nikaya."""
        refs = sorted(self.index.keys())
        if nikaya:
            prefix = f"{nikaya.upper()}_"
            refs = [r for r in refs if r.startswith(prefix)]
        return refs

    def get_exact_line(self, nikaya: str, volume: int, page: int) -> str:
        """
        Get only the exact line containing the PTS marker.
        """
        nikaya_upper = nikaya.upper()
        label = f"{nikaya_upper}_{volume}_{page}"
        filename, line_offset = self.index[label]
        lines = self._load_file(filename)
        return lines[line_offset] if line_offset < len(lines) else ""

    def get_context(
        self,
        nikaya: str,
        volume: int,
        page: int,
        lines_before: int = 3,
        lines_after: int = 10,
    ) -> str:
        """
        Get the PTS marker line with surrounding context.
        """
        nikaya_upper = nikaya.upper()
        label = f"{nikaya_upper}_{volume}_{page}"
        filename, line_offset = self.index[label]
        lines = self._load_file(filename)

        start = max(0, line_offset - lines_before)
        end = min(len(lines), line_offset + lines_after + 1)

        context_lines = []
        for i in range(start, end):
            marker = " >>> " if i == line_offset else "     "
            context_lines.append(f"{marker}[L{i + 1}] {lines[i]}")

        return "\n".join(context_lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    rota_path = os.path.dirname(os.path.abspath(__file__))
    api = RotaAPI(rota_path)

    if len(sys.argv) < 2:
        print("Usage: python rota_api.py <NIKAYA> <VOLUME> <PAGE>")
        print("  NIKAYA: D, M, S, A")
        print("  VOLUME: integer (or Roman numeral: I, II, III...)")
        print("  PAGE: integer")
        print()
        print("Examples:")
        print("  python rota_api.py D 1 2     # Digha Nikaya Vol 1, page 2")
        print("  python rota_api.py M I 5     # Majjhima Nikaya Vol 1, page 5")
        print()
        print("To list available references:")
        print("  python rota_api.py list [NIKAYA]")
        sys.exit(1)

    if sys.argv[1] == "list":
        nik = sys.argv[2].upper() if len(sys.argv) > 2 else None
        refs = api.list_available(nik)
        for ref in refs:
            print(ref)
        sys.exit(0)

    if len(sys.argv) < 4:
        print("Error: need 3 arguments: NIKAYA VOLUME PAGE")
        print("Usage: python rota_api.py <NIKAYA> <VOLUME> <PAGE>")
        sys.exit(1)

    nikaya = sys.argv[1]
    vol_str = sys.argv[2]
    pg_str = sys.argv[3]

    # Handle Roman numerals for volume
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
    if vol_str.upper() in roman_map:
        volume = roman_map[vol_str.upper()]
    else:
        volume = int(vol_str)
    page = int(pg_str)

    text = api.get_page(nikaya, volume, page)
    print(text)
