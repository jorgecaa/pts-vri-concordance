"""
Comprehensive PTS citation parser module for Tipitaka PTS Browser.

This module provides full PTS citation parsing functionality with support for:
1. Standard PTS citation formats (e.g., "M I 3", "Sn 25")
2. Alternative formats (e.g., "M.I.3", "S.IV.100")
3. Volume mapping to database BOOK_NO values
4. Error handling and validation
5. Integration with the existing database system
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union

# ---------------------------------------------------------------------------
# Roman numeral helpers
# ---------------------------------------------------------------------------

# Map from uppercase Roman numeral string → integer
ROMAN_TO_INT = {
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

# Reverse mapping (integer → Roman numeral string)
INT_TO_ROMAN = {v: k for k, v in ROMAN_TO_INT.items()}

# ---------------------------------------------------------------------------
# Book abbreviation mapping
# ---------------------------------------------------------------------------

# Standard PTS abbreviations and their aliases
BOOK_ABBREVIATIONS = {
    # Vinaya Piṭaka
    "vin": ["vin", "vinaya"],
    "vin1": ["vin1", "vin.i", "vin i"],
    "vin2": ["vin2", "vin.ii", "vin ii"],
    "vin3": ["vin3", "vin.iii", "vin iii"],
    "vin4": ["vin4", "vin.iv", "vin iv"],
    "vin5": ["vin5", "vin.v", "vin v"],
    # Dīgha Nikāya
    "d": ["d", "dn", "dīgha", "digha"],
    "d1": ["d1", "d.i", "d i", "dn1", "dn.i", "dn i"],
    "d2": ["d2", "d.ii", "d ii", "dn2", "dn.ii", "dn ii"],
    "d3": ["d3", "d.iii", "d iii", "dn3", "dn.iii", "dn iii"],
    # Majjhima Nikāya
    "m": ["m", "mn", "majjhima"],
    "m1": ["m1", "m.i", "m i", "mn1", "mn.i", "mn i"],
    "m2": ["m2", "m.ii", "m ii", "mn2", "mn.ii", "mn ii"],
    "m3": ["m3", "m.iii", "m iii", "mn3", "mn.iii", "mn iii"],
    # Saṃyutta Nikāya
    "s": ["s", "sn", "saṃyutta", "samyutta"],
    "s1": ["s1", "s.i", "s i", "sn1", "sn.i", "sn i"],
    "s2": ["s2", "s.ii", "s ii", "sn2", "sn.ii", "sn ii"],
    "s3": ["s3", "s.iii", "s iii", "sn3", "sn.iii", "sn iii"],
    "s4": ["s4", "s.iv", "s iv", "sn4", "sn.iv", "sn iv"],
    "s5": ["s5", "s.v", "s v", "sn5", "sn.v", "sn v"],
    # Aṅguttara Nikāya
    "a": ["a", "an", "aṅguttara", "anguttara"],
    "a1": ["a1", "a.i", "a i", "an1", "an.i", "an i"],
    "a2": ["a2", "a.ii", "a ii", "an2", "an.ii", "an ii"],
    "a3": ["a3", "a.iii", "a iii", "an3", "an.iii", "an iii"],
    "a4": ["a4", "a.iv", "a iv", "an4", "an.iv", "an iv"],
    "a5": ["a5", "a.v", "a v", "an5", "an.v", "an v"],
    # Khuddaka Nikāya (no volume number)
    "khp": ["khp", "khuddakapāṭha", "khuddakapatha"],
    "dhp": ["dhp", "dhammapada"],
    "ud": ["ud", "udāna", "udana"],
    "it": ["it", "itivuttaka"],
    "sn": ["sn", "sutta nipāta", "sutta nipata", "snp"],
    "vv": ["vv", "vimānavatthu", "vimanavatthu"],
    "pv": ["pv", "petavatthu"],
    "th": ["th", "theragāthā", "theragatha"],
    "thī": ["thī", "therīgāthā", "therigatha", "thi"],
    # Jātaka
    "ja": ["ja", "jātaka", "jataka"],
    "ja1": ["ja1", "ja.i", "ja i"],
    "ja2": ["ja2", "ja.ii", "ja ii"],
    "ja3": ["ja3", "ja.iii", "ja iii"],
    "ja4": ["ja4", "ja.iv", "ja iv"],
    "ja5": ["ja5", "ja.v", "ja v"],
    "ja6": ["ja6", "ja.vi", "ja vi"],
    # Abhidhamma Piṭaka & late Khuddaka
    "nidd": ["nidd", "niddesa"],
    "nidd1": ["nidd1", "nidd.i", "nidd i"],
    "nidd2": ["nidd2", "nidd.ii", "nidd ii"],
    "patis": ["patis", "paṭisambhidāmagga", "patisambhidamagga"],
    "patis1": ["patis1", "patis.i", "patis i"],
    "patis2": ["patis2", "patis.ii", "patis ii"],
    "ap": ["ap", "apadāna", "apadana"],
    "bv": ["bv", "buddhavaṃsa", "buddhavamsa"],
    "cp": ["cp", "cariyāpiṭaka", "cariyapitaka"],
    "dhs": ["dhs", "dhammasaṅgaṇī", "dhammasangani"],
    "vibh": ["vibh", "vibhaṅga", "vibhanga"],
    "dhtk": ["dhtk", "dhātukathā", "dhatukatha", "dhntk"],
    "pp": ["pp", "puggalapaññatti", "puggalapannatti"],
    "kv": ["kv", "kathāvatthu", "kathavatthu"],
    "yam": ["yam", "yamaka"],
    "yam1": ["yam1", "yam.i", "yam i"],
    "yam2": ["yam2", "yam.ii", "yam ii"],
    "pat": ["pat", "paṭṭhāna", "patthana"],
    "pat1": ["pat1", "pat.i", "pat i"],
    "pat2": ["pat2", "pat.ii", "pat ii"],
    "pat3": ["pat3", "pat.iii", "pat iii"],
}

# ---------------------------------------------------------------------------
# Book map: (normalized_abbreviation, volume_int) → BOOK_NO
# ---------------------------------------------------------------------------

BOOK_MAP: Dict[Tuple[str, int], int] = {
    # Vinaya Piṭaka
    ("vin", 1): 1,  # Pārājika
    ("vin", 2): 2,  # Pācittiya
    ("vin", 3): 3,  # Mahāvagga
    ("vin", 4): 4,  # Cūḷavagga
    ("vin", 5): 5,  # Parivāra
    # Dīgha Nikāya
    ("d", 1): 6,
    ("dn", 1): 6,
    ("d", 2): 7,
    ("dn", 2): 7,
    ("d", 3): 8,
    ("dn", 3): 8,
    # Majjhima Nikāya
    ("m", 1): 9,
    ("mn", 1): 9,
    ("m", 2): 10,
    ("mn", 2): 10,
    ("m", 3): 11,
    ("mn", 3): 11,
    # Saṃyutta Nikāya
    ("s", 1): 12,
    ("sn", 1): 12,
    ("s", 2): 13,
    ("sn", 2): 13,
    ("s", 3): 14,
    ("sn", 3): 14,
    ("s", 4): 15,
    ("sn", 4): 15,
    ("s", 5): 16,
    ("sn", 5): 16,
    # Aṅguttara Nikāya
    ("a", 1): 17,
    ("an", 1): 17,
    ("a", 2): 18,
    ("an", 2): 18,
    ("a", 3): 19,
    ("an", 3): 19,
    ("a", 4): 20,
    ("an", 4): 20,
    ("a", 5): 21,
    ("an", 5): 21,
    # Khuddaka Nikāya (no volume number)
    ("khp", 0): 22,  # Khuddakapāṭha
    ("dhp", 0): 23,  # Dhammapada
    ("ud", 0): 24,  # Udāna
    ("it", 0): 25,  # Itivuttaka
    ("sn", 0): 26,
    ("snp", 0): 26,  # Sutta Nipāta
    ("vv", 0): 27,  # Vimānavatthu
    ("pv", 0): 28,  # Petavatthu
    ("th", 0): 29,  # Theragāthā & Therīgāthā (combined)
    # Jātaka (corrected: starts at BOOK_NO=30)
    ("ja", 1): 30,
    ("ja", 2): 31,
    ("ja", 3): 32,
    ("ja", 4): 33,
    ("ja", 5): 34,
    ("ja", 6): 35,
    # Abhidhamma Piṭaka & late Khuddaka (corrected offsets)
    ("nidd", 1): 36,  # Mahā Niddesa I
    ("nidd", 2): 37,  # Mahā Niddesa II
    ("patis", 1): 38,  # Paṭisambhidāmagga I
    ("patis", 2): 39,  # Paṭisambhidāmagga II
    ("ap", 0): 40,  # Apadāna
    ("bv", 0): 41,  # Buddhavaṃsa
    ("cp", 0): 42,  # Cariyāpiṭaka
    ("dhs", 0): 43,  # Dhammasaṅgaṇī
    ("vibh", 0): 44,  # Vibhaṅga
    ("dhtk", 0): 45,
    ("dhntk", 0): 45,  # Dhātukathā
    ("pp", 0): 46,  # Puggalapaññatti
    ("kv", 0): 47,  # Kathāvatthu
    ("yam", 1): 48,
    ("yam", 2): 49,  # Yamaka I–II
    ("pat", 1): 50,  # Paṭṭhāna (Dukapaṭṭhāna)
    ("pat", 2): 51,  # Paṭṭhāna (Tikapaṭṭhāna I)
    ("pat", 3): 52,  # Paṭṭhāna (Tikapaṭṭhāna II)
    # Note: BOOK_NO 53 exists but not in this mapping (Tikapaṭṭhāna III would be 53)
}


class PTSCitationParser:
    """Parser for PTS-style citations."""

    def __init__(self):
        """Initialize the parser with abbreviation mappings."""
        self._build_abbreviation_index()

    def _build_abbreviation_index(self):
        """Build reverse index from abbreviation to canonical form."""
        self._abbr_to_canonical = {}
        for canonical, aliases in BOOK_ABBREVIATIONS.items():
            for alias in aliases:
                self._abbr_to_canonical[alias.lower()] = canonical

    def normalize_abbreviation(self, abbr: str) -> Optional[str]:
        """
        Normalize a book abbreviation to its canonical form.

        Args:
            abbr: Book abbreviation (e.g., "M", "MN", "m.i")

        Returns:
            Canonical abbreviation or None if not found
        """
        abbr_lower = abbr.lower().strip()

        # Direct lookup
        if abbr_lower in self._abbr_to_canonical:
            return self._abbr_to_canonical[abbr_lower]

        # Try removing dots and spaces
        abbr_clean = re.sub(r"[.\s]+", "", abbr_lower)
        if abbr_clean in self._abbr_to_canonical:
            return self._abbr_to_canonical[abbr_clean]

        return None

    def parse_roman_numeral(self, roman: str) -> Optional[int]:
        """
        Parse a Roman numeral string to integer.

        Args:
            roman: Roman numeral string (e.g., "I", "IV", "XII")

        Returns:
            Integer value or None if invalid
        """
        roman_upper = roman.upper().strip()
        return ROMAN_TO_INT.get(roman_upper)

    def format_roman_numeral(self, number: int) -> Optional[str]:
        """
        Format an integer as Roman numeral.

        Args:
            number: Integer to format

        Returns:
            Roman numeral string or None if out of range
        """
        return INT_TO_ROMAN.get(number)

    def parse_citation(self, citation: str) -> Optional[Dict[str, Any]]:
        """
        Parse a PTS-style citation string.

        Supports formats:
          1. Three-token with Roman volume: "M I 3" → {"abbr": "m", "volume": 1, "page": 3}
          2. Two-token without volume: "Sn 25" → {"abbr": "sn", "volume": 0, "page": 25}
          3. Dot/comma-delimited: "M.I.3" or "M.I,3" → {"abbr": "m", "volume": 1, "page": 3}
          4. Numbered volume: "M1 3" → {"abbr": "m", "volume": 1, "page": 3}

        Args:
            citation: Raw citation string

        Returns:
            Parsed citation dictionary or None if unparseable
        """
        if not citation or not citation.strip():
            return None

        citation = citation.strip()

        # Try format 1: <abbr> <ROMAN_VOL> <page>
        parts = citation.split()
        if len(parts) == 3:
            abbr, vol_str, page_str = parts
            volume = self.parse_roman_numeral(vol_str)
            if volume is not None:
                try:
                    page = int(page_str)
                    normalized_abbr = self.normalize_abbreviation(abbr)
                    if normalized_abbr:
                        return {
                            "abbreviation": normalized_abbr,
                            "volume": volume,
                            "page": page,
                            "original": citation,
                            "format": "standard",
                        }
                except ValueError:
                    pass

        # Try format 2: <abbr> <page> (works without volume)
        if len(parts) == 2:
            abbr, page_str = parts
            try:
                page = int(page_str)
                normalized_abbr = self.normalize_abbreviation(abbr)
                if normalized_abbr:
                    return {
                        "abbreviation": normalized_abbr,
                        "volume": 0,  # No volume specified
                        "page": page,
                        "original": citation,
                        "format": "no_volume",
                    }
            except ValueError:
                pass

        # Try format 3: dot/comma-delimited, e.g., "M.I.3" or "M.I,3"
        # Remove spaces and try to match pattern
        citation_no_spaces = citation.replace(" ", "")
        pattern = r"^([a-zA-Zāṃṭḍñḷṇśūī]+)[.,]?([ivxIVX\d]+)[.,]?(\d+)$"
        match = re.match(pattern, citation_no_spaces)

        if match:
            abbr = match.group(1)
            vol_str = match.group(2)
            page_str = match.group(3)

            # Try to parse volume as Roman numeral first
            volume = self.parse_roman_numeral(vol_str)
            if volume is None:
                # Try as Arabic numeral
                try:
                    volume = int(vol_str)
                except ValueError:
                    volume = 0

            try:
                page = int(page_str)
                normalized_abbr = self.normalize_abbreviation(abbr)
                if normalized_abbr:
                    return {
                        "abbreviation": normalized_abbr,
                        "volume": volume,
                        "page": page,
                        "original": citation,
                        "format": "delimited",
                    }
            except ValueError:
                pass

        # Try format 4: abbreviation with embedded volume number, e.g., "M1 3"
        pattern = r"^([a-zA-Zāṃṭḍñḷṇśūī]+)(\d+)\s+(\d+)$"
        match = re.match(pattern, citation.replace(".", "").replace(",", ""))

        if match:
            abbr = match.group(1)
            vol_str = match.group(2)
            page_str = match.group(3)

            try:
                volume = int(vol_str)
                page = int(page_str)
                normalized_abbr = self.normalize_abbreviation(abbr)
                if normalized_abbr:
                    return {
                        "abbreviation": normalized_abbr,
                        "volume": volume,
                        "page": page,
                        "original": citation,
                        "format": "embedded_volume",
                    }
            except ValueError:
                pass

        return None

    def get_book_no(self, abbreviation: str, volume: int) -> Optional[int]:
        """
        Get database BOOK_NO for a given abbreviation and volume.

        Args:
            abbreviation: Canonical book abbreviation
            volume: Volume number (0 for works without volumes)

        Returns:
            BOOK_NO integer or None if not found
        """
        # Handle special cases for abbreviations with embedded volume
        base_abbr = abbreviation.rstrip("0123456789")
        if base_abbr != abbreviation:
            # This is an abbreviation with embedded volume like "m1"
            try:
                embedded_volume = int(abbreviation[len(base_abbr) :])
                abbreviation = base_abbr
                volume = embedded_volume
            except ValueError:
                pass

        # Try exact match first
        key = (abbreviation, volume)
        if key in BOOK_MAP:
            return BOOK_MAP[key]

        # Try without volume for works that don't have volumes
        if volume == 0:
            # Check if this abbreviation exists with volume 0
            for (abbr, vol), book_no in BOOK_MAP.items():
                if abbr == abbreviation and vol == 0:
                    return book_no

        # Try alternative abbreviations
        for (abbr, vol), book_no in BOOK_MAP.items():
            if vol == volume:
                # Check if this abbreviation is an alias
                canonical = self.normalize_abbreviation(abbr)
                if canonical == abbreviation:
                    return book_no

        return None

    def parse_and_resolve(self, citation: str) -> Optional[Dict[str, Any]]:
        """
        Parse a citation and resolve it to database BOOK_NO.

        Args:
            citation: PTS citation string

        Returns:
            Dictionary with parsed citation and resolved BOOK_NO,
            or None if invalid or not found
        """
        parsed = self.parse_citation(citation)
        if not parsed:
            return None

        abbreviation = parsed["abbreviation"]
        volume = parsed["volume"]
        page = parsed["page"]

        book_no = self.get_book_no(abbreviation, volume)
        if book_no is None:
            return None

        return {
            **parsed,
            "book_no": book_no,
            "resolved": True,
        }

    def format_citation(
        self, abbreviation: str, volume: int, page: int, format_style: str = "standard"
    ) -> str:
        """
        Format a citation in standard PTS style.

        Args:
            abbreviation: Book abbreviation
            volume: Volume number (0 for works without volumes)
            page: Page number
            format_style: Output format ("standard", "delimited", or "compact")

        Returns:
            Formatted citation string
        """
        # Get canonical abbreviation for display
        canonical = self.normalize_abbreviation(abbreviation)
        if not canonical:
            canonical = abbreviation.upper()

        if volume == 0:
            # Works without volume numbers
            if format_style == "delimited":
                return f"{canonical}.{page}"
            elif format_style == "compact":
                return f"{canonical}{page}"
            else:
                return f"{canonical} {page}"
        else:
            # Works with volume numbers
            roman_volume = self.format_roman_numeral(volume)
            if not roman_volume:
                roman_volume = str(volume)

            if format_style == "delimited":
                return f"{canonical}.{roman_volume}.{page}"
            elif format_style == "compact":
                return f"{canonical}{roman_volume}.{page}"
            else:
                return f"{canonical} {roman_volume} {page}"

    def get_all_abbreviations(self) -> Dict[str, List[str]]:
        """
        Get all supported abbreviations.

        Returns:
            Dictionary mapping canonical abbreviations to their aliases
        """
        return BOOK_ABBREVIATIONS.copy()

    def get_book_info(
        self, abbreviation: str, volume: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Get information about a book.

        Args:
            abbreviation: Book abbreviation
            volume: Volume number

        Returns:
            Dictionary with book information or None if not found
        """
        book_no = self.get_book_no(abbreviation, volume)
        if book_no is None:
            return None

        # Get canonical abbreviation
        canonical = self.normalize_abbreviation(abbreviation)
        if not canonical:
            canonical = abbreviation

        # Get full name if available
        full_names = {
            "vin": "Vinaya Piṭaka",
            "d": "Dīgha Nikāya",
            "dn": "Dīgha Nikāya",
            "m": "Majjhima Nikāya",
            "mn": "Majjhima Nikāya",
            "s": "Saṃyutta Nikāya",
            "sn": "Saṃyutta Nikāya",
            "a": "Aṅguttara Nikāya",
            "an": "Aṅguttara Nikāya",
            "khp": "Khuddakapāṭha",
            "dhp": "Dhammapada",
            "ud": "Udāna",
            "it": "Itivuttaka",
            "snp": "Sutta Nipāta",
            "vv": "Vimānavatthu",
            "pv": "Petavatthu",
            "th": "Theragāthā",
            "thī": "Therīgāthā",
            "ja": "Jātaka",
            "nidd": "Niddesa",
            "patis": "Paṭisambhidāmagga",
            "ap": "Apadāna",
            "bv": "Buddhavaṃsa",
            "cp": "Cariyāpiṭaka",
            "dhs": "Dhammasaṅgaṇī",
            "vibh": "Vibhaṅga",
            "dhtk": "Dhātukathā",
            "pp": "Puggalapaññatti",
            "kv": "Kathāvatthu",
            "yam": "Yamaka",
            "pat": "Paṭṭhāna",
        }

        full_name = full_names.get(canonical, canonical.upper())

        return {
            "abbreviation": canonical,
            "volume": volume,
            "book_no": book_no,
            "full_name": full_name,
            "has_volume": volume > 0,
            "standard_citation": self.format_citation(canonical, volume, 1),
        }

    def validate_citation(self, citation: str) -> Dict[str, Any]:
        """
        Validate a citation and provide detailed feedback.

        Args:
            citation: Citation string to validate

        Returns:
            Dictionary with validation results
        """
        parsed = self.parse_citation(citation)

        if not parsed:
            return {
                "valid": False,
                "citation": citation,
                "error": "Could not parse citation format",
                "suggestions": [
                    "Use format: <abbreviation> <volume> <page> (e.g., 'M I 3')",
                    "For works without volumes: <abbreviation> <page> (e.g., 'Sn 25')",
                    "Alternative format: <abbreviation>.<volume>.<page> (e.g., 'M.I.3')",
                ],
            }

        abbreviation = parsed["abbreviation"]
        volume = parsed["volume"]
        page = parsed["page"]

        book_no = self.get_book_no(abbreviation, volume)

        if book_no is None:
            return {
                "valid": False,
                "citation": citation,
                "parsed": parsed,
                "error": f"Book not found: {abbreviation} volume {volume}",
                "suggestions": self._get_suggestions(abbreviation, volume),
            }

        return {
            "valid": True,
            "citation": citation,
            "parsed": parsed,
            "book_no": book_no,
            "formatted": self.format_citation(abbreviation, volume, page),
            "book_info": self.get_book_info(abbreviation, volume),
        }

    def _get_suggestions(self, abbreviation: str, volume: int) -> List[str]:
        """Get suggestions for similar abbreviations."""
        suggestions = []

        # Check if abbreviation exists with different volume
        for (abbr, vol), book_no in BOOK_MAP.items():
            if abbr == abbreviation and vol != volume:
                suggestions.append(f"Try volume {vol} instead of {volume}")
                break

        # Check for similar abbreviations
        abbr_lower = abbreviation.lower()
        for canonical, aliases in BOOK_ABBREVIATIONS.items():
            for alias in aliases:
                if abbr_lower in alias or alias in abbr_lower:
                    suggestions.append(f"Did you mean '{canonical}'?")
                    break

        if not suggestions:
            suggestions.append("Check the list of supported abbreviations")

        return suggestions


# Utility functions for integration
def create_citation_parser():
    """Create a citation parser instance."""
    return PTSCitationParser()


def parse_pts_citation(citation: str) -> Optional[Dict[str, Any]]:
    """
    Parse a PTS citation string.

    Args:
        citation: Citation string

    Returns:
        Parsed citation or None if invalid
    """
    parser = PTSCitationParser()
    return parser.parse_and_resolve(citation)


def validate_pts_citation(citation: str) -> Dict[str, Any]:
    """
    Validate a PTS citation.

    Args:
        citation: Citation string

    Returns:
        Validation results
    """
    parser = PTSCitationParser()
    return parser.validate_citation(citation)


if __name__ == "__main__":
    # Test the citation parser
    parser = PTSCitationParser()

    test_citations = [
        "M I 3",
        "Sn 25",
        "S.IV.100",
        "D II 50",
        "A V 123",
        "dhp 1",
        "M1 10",
        "invalid citation",
        "MN I 5",
        "SN 100",
    ]

    print("Testing PTS Citation Parser")
    print("=" * 50)

    for citation in test_citations:
        print(f"\nCitation: '{citation}'")
        result = parser.validate_citation(citation)

        if result["valid"]:
            print(f"  ✓ Valid")
            print(f"  Parsed: {result['parsed']}")
            print(f"  Book No: {result['book_no']}")
            print(f"  Formatted: {result['formatted']}")
            if result["book_info"]:
                print(f"  Book: {result['book_info']['full_name']}")
        else:
            print(f"  ✗ Invalid: {result['error']}")
            if "suggestions" in result:
                for suggestion in result["suggestions"]:
                    print(f"    Suggestion: {suggestion}")

    print(f"\n\nAll supported abbreviations:")
    abbreviations = parser.get_all_abbreviations()
    for canonical, aliases in sorted(abbreviations.items()):
        print(
            f"  {canonical}: {', '.join(aliases[:3])}{'...' if len(aliases) > 3 else ''}"
        )
