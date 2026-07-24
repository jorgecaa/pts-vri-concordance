"""
Shared text normalization for PTS and ROTA editions.

Both editions are normalized to the SAME format so their texts can be
compared directly, character by character.

Usage:
    >>> from text_normalization import normalize_text
    >>> normalized = normalize_text(raw_edition_text)
"""

import re


def _remove_rota_apparatus_blocks(text: str) -> str:
    """Remove ROTA apparatus blocks delimited by * * * ... and ───────."""
    lines = text.split("\n")
    result: list[str] = []
    inside = False

    for line in lines:
        if not inside and re.match(r"^\s*(?:\*\s+){2,}\*\s*$", line):
            inside = True
            continue
        if inside and re.match(r"^\s*-{10,}\s*$", line):
            inside = False
            continue
        if not inside:
            result.append(line)

    return "\n".join(result)


def normalize_text(text: str) -> str:
    """
    Normalize text from ANY edition (PTS or ROTA) to a common format.

    Pipeline:
      1. Strip ROTA apparatus blocks (* * * * … ───────────────)
      2. Remove PTS paragraph separators (║, ║ ║)
      3. Remove ROTA page markers ([page NNN], [Local page NNN])
      4. Join hyphenated line breaks (aneka-\\npariyāyena → anekapariyāyena)
      5. Remove inline apparatus references:
         • PTS style: vādā1, dhammo3, ca.1
         • ROTA style: [^1], [^2]
      6. Collapse all line breaks to spaces
      7. Normalize whitespace (single spaces)

    Result: plain flowing text, comparable across editions.
    """
    if not text:
        return ""

    # 1. Strip ROTA apparatus blocks
    text = _remove_rota_apparatus_blocks(text)

    # 2. Remove PTS paragraph separators
    text = text.replace("║ ║", " ")
    text = text.replace("║║", " ")
    text = text.replace("║", " ")

    # 3. Remove ROTA page markers
    text = re.sub(r"\[Local page \d{3}\]", " ", text)
    text = re.sub(r"\[page \d{3}\]", " ", text)

    # 4. Join hyphenated line breaks
    text = re.sub(r"(\w)-\r?\n(\w)", r"\1\2", text)

    # 5. Remove inline apparatus references
    # PTS style: vādā1  dhammo3  ca.1
    text = re.sub(r"(?<=\w)\d{1,2}(?=[ \r\n]|$)", "", text)
    text = re.sub(r"\.\d{1,2}(?=[ \r\n]|$)", ".", text)
    # ROTA style: [^1]
    text = re.sub(r"\s*\[\^\d+\]\s*", " ", text)

    # 6. Collapse all line breaks to spaces
    text = re.sub(r"\r?\n", " ", text)

    # 7. Normalize whitespace
    text = re.sub(r"\s{2,}", " ", text)

    return text.strip()
