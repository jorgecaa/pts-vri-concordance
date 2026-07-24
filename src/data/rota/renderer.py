"""
renderer.py — Cross-edition comparison renderer.

Compares PTS and ROTA editions for a given PTS page,
produces HTML with the ORIGINAL PTS text (all formatting preserved)
where divergences from ROTA are underlined/highlighted.
"""

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional

from text_normalization import normalize_text

# ---------------------------------------------------------------------------
# Diff computation on NORMALIZED texts
# ---------------------------------------------------------------------------


@dataclass
class DiffSpan:
    """A contiguous span of text that differs between editions."""

    start: int  # character position in normalized PTS text
    end: int  # exclusive
    pts_text: str  # what PTS has here (normalized)
    rota_text: str  # what ROTA has here (normalized)


def compute_diffs(pts_norm: str, rota_norm: str, min_span: int = 3) -> list[DiffSpan]:
    """
    Find all differing spans between normalized PTS and ROTA texts.
    Only spans of at least *min_span* characters are reported.
    """
    matcher = SequenceMatcher(None, pts_norm, rota_norm, autojunk=False)
    diffs: list[DiffSpan] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        length = i2 - i1
        if length < min_span:
            continue
        pts_span = pts_norm[i1:i2]
        rota_span = rota_norm[j1:j2] if j2 > j1 else ""

        # Skip spans that are purely whitespace differences
        if pts_span.strip() == rota_span.strip():
            continue

        diffs.append(
            DiffSpan(
                start=i1,
                end=i2,
                pts_text=pts_span,
                rota_text=rota_span,
            )
        )

    return diffs


# ---------------------------------------------------------------------------
# Map normalized diffs back to RAW PTS text
# ---------------------------------------------------------------------------


def _find_in_raw(raw: str, needle: str, start: int) -> Optional[tuple[int, int]]:
    """
    Find *needle* (text from normalized comparison) inside the raw PTS text,
    accounting for normalization artifacts:
      • hyphenated line breaks joined (``aneka-\\r\\npariyāyena`` vs ``anekapariyāyena``)
      • line breaks turned to spaces
      • apparatus refs removed
      • ║ separators removed

    Returns (start, end) indices in raw text, or None.
    """
    # 1. Exact match
    pos = raw.find(needle, start)
    if pos >= 0:
        return (pos, pos + len(needle))

    # 2. Flexible whitespace: needle chars separated by any whitespace in raw
    pattern = re.escape(needle)
    pattern = pattern.replace(r"\ ", r"\s+")
    m = re.search(pattern, raw[start:])
    if m:
        return (start + m.start(), start + m.end())

    # 3. Try ignoring ║ separators (treat as spaces)
    stripped = raw[start:].replace("║", " ")
    pos2 = stripped.find(needle)
    if pos2 >= 0:
        # Map back: count non-║ chars to find position
        count = 0
        for i, ch in enumerate(raw[start:]):
            if ch == "║":
                continue
            if count == pos2:
                return (start + i, start + i + len(needle))
            count += 1

    # 4. Try ignoring hyphenation line breaks
    joined = re.sub(r"(\w)-\r?\n(\w)", r"\1\2", raw[start:])
    pos3 = joined.find(needle)
    if pos3 >= 0:
        # Approximate: find a matching subsequence in raw
        sub = needle[: min(len(needle), 15)]
        pat = re.escape(sub).replace(r"\ ", r"\s+")
        m3 = re.search(pat, raw[start:])
        if m3:
            return (start + m3.start(), start + m3.end())

    # 5. Try shorter subsequence
    for length in range(len(needle) - 1, max(3, len(needle) - 12), -1):
        sub = needle[:length]
        pat = re.escape(sub).replace(r"\ ", r"\s+")
        m4 = re.search(pat, raw[start:])
        if m4:
            return (start + m4.start(), start + m4.end())

    return None


def _apply_diffs_to_raw(
    pts_raw: str, diffs: list[DiffSpan], highlight_class: str
) -> str:
    """
    Wrap divergent spans in the **raw PTS text** with HTML ``<span>``.

    All original PTS formatting is preserved verbatim (line breaks,
    hyphenation, ║ separators, spacing). Only the characters that differ
    from ROTA get highlighted.
    """
    raw_spans: list[
        tuple[int, int, bool, str]
    ] = []  # (start, end, is_diff, rota_tooltip)
    search_from = 0

    for d in diffs:
        found = _find_in_raw(pts_raw, d.pts_text, search_from)
        if found is not None:
            s, e = found
            # Safe text before this diff
            if s > search_from:
                raw_spans.append((search_from, s, False, ""))
            # Diff span
            raw_spans.append((s, e, True, d.rota_text))
            search_from = e
        # If not found, skip

    # Remaining safe text
    if search_from < len(pts_raw):
        raw_spans.append((search_from, len(pts_raw), False, ""))

    # Build HTML preserving raw text exactly
    parts: list[str] = []
    for s, e, is_diff, tooltip in raw_spans:
        segment = pts_raw[s:e]
        if is_diff:
            escaped = _escape_html(segment)
            tip = _escape_attr(tooltip)
            parts.append(
                f'<span class="{highlight_class}" title="ROTA: {tip}">{escaped}</span>'
            )
        else:
            parts.append(_escape_html(segment))

    # Convert line breaks to <br> for HTML display
    return "".join(parts).replace("\n", "<br>")


# ---------------------------------------------------------------------------
# Public rendering API
# ---------------------------------------------------------------------------


def render_highlighted(
    pts_raw: str,
    rota_raw: str,
    *,
    highlight_class: str = "divergence",
    min_span: int = 3,
) -> str:
    """
    Produce HTML of the **original PTS text** with all formatting preserved
    but divergences from ROTA wrapped in ``<span class="divergence">``.

    Detection uses normalized comparison; highlighting is applied to the
    raw PTS text so ║ separators, hyphenation, line breaks, and spacing
    all remain exactly as in the source.
    """
    pts_norm = normalize_text(pts_raw)
    rota_norm = normalize_text(rota_raw)
    diffs = compute_diffs(pts_norm, rota_norm, min_span=min_span)

    if not diffs:
        return _escape_html(pts_raw).replace("\n", "<br>")

    return _apply_diffs_to_raw(pts_raw, diffs, highlight_class)


def render_side_by_side(pts_raw: str, rota_raw: str, *, min_span: int = 3) -> str:
    """
    Produce HTML with PTS and ROTA texts side by side,
    divergences highlighted in both columns.
    """
    pts_norm = normalize_text(pts_raw)
    rota_norm = normalize_text(rota_raw)
    diffs = compute_diffs(pts_norm, rota_norm, min_span=min_span)

    matcher = SequenceMatcher(None, pts_norm, rota_norm, autojunk=False)

    pts_parts: list[str] = []
    rota_parts: list[str] = []
    j_cursor = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            pts_parts.append(_escape_html(pts_norm[i1:i2]))
            rota_parts.append(_escape_html(rota_norm[j1:j2]))
        elif tag in ("replace", "delete"):
            if i2 > i1:
                pts_parts.append(
                    f'<span class="divergence">{_escape_html(pts_norm[i1:i2])}</span>'
                )
            else:
                pts_parts.append(
                    '<span class="divergence" title="(missing in PTS)">[—]</span>'
                )
            if j2 > j1:
                rota_parts.append(
                    f'<span class="divergence">{_escape_html(rota_norm[j1:j2])}</span>'
                )
            else:
                rota_parts.append(
                    '<span class="divergence" title="(missing in ROTA)">[—]</span>'
                )
        elif tag == "insert":
            pts_parts.append(
                '<span class="divergence" title="(missing in PTS)">[—]</span>'
            )
            rota_parts.append(
                f'<span class="divergence">{_escape_html(rota_norm[j1:j2])}</span>'
            )

    pts_html = "".join(pts_parts).replace("\n", "<br>")
    rota_html = "".join(rota_parts).replace("\n", "<br>")

    return (
        f'<table class="side-by-side"><tr>'
        f'<td class="pts-col">{pts_html}</td>'
        f'<td class="rota-col">{rota_html}</td>'
        f"</tr></table>"
    )


def render_summary(pts_raw: str, rota_raw: str, *, min_span: int = 3) -> dict:
    """Produce a summary dict of the comparison."""
    pts_norm = normalize_text(pts_raw)
    rota_norm = normalize_text(rota_raw)
    diffs = compute_diffs(pts_norm, rota_norm, min_span=min_span)

    total_pts = len(pts_norm)
    total_rota = len(rota_norm)
    diff_chars = sum(d.end - d.start for d in diffs)
    matching = total_pts - diff_chars if total_pts > 0 else 0

    return {
        "pts_length": total_pts,
        "rota_length": total_rota,
        "diff_count": len(diffs),
        "diff_chars": diff_chars,
        "matching_chars": matching,
        "similarity_pct": (matching / total_pts * 100) if total_pts > 0 else 0,
        "diffs": [
            {"pts_text": d.pts_text[:80], "rota_text": d.rota_text[:80]} for d in diffs
        ],
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _escape_attr(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "\\n")
    )
