"""
Enhanced apparatus criticus module for Tipitaka PTS Browser.

This module provides comprehensive apparatus criticus display functionality,
including manuscript variant parsing, sigla interpretation, and formatting.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ManuscriptSigla(Enum):
    """Manuscript sigla used in the apparatus criticus."""

    CAMBRIDGE = "Cb"  # Cambridge manuscript
    BANGKOK_A = "Ba"  # Bangkok A manuscript
    BANGKOK_B = "Bai"  # Bangkok B manuscript
    BURMESE = "Bi"  # Burmese manuscript
    COLOMBO = "Ck"  # Colombo manuscript
    FAUSBOLL = "Fsb"  # Fausbøll edition
    SYAMARATTHA = "Sy"  # Syāmaratṭha edition
    ROTA = "Ro"  # ROTA edition
    PTS = "PTS"  # PTS edition


@dataclass
class ApparatusEntry:
    """Represents a single apparatus criticus entry."""

    location: str  # Location identifier (e.g., "M I 3, line 5")
    variants: List[Dict[str, Any]]  # List of variant readings
    note: Optional[str] = None  # Additional notes
    confidence: str = "medium"  # Confidence level: low, medium, high


@dataclass
class VariantReading:
    """Represents a variant reading from a specific manuscript."""

    text: str  # The variant text
    sigla: List[ManuscriptSigla]  # Manuscripts supporting this reading
    type: (
        str  # Type of variant: "addition", "omission", "substitution", "transposition"
    )
    significance: str = "minor"  # Significance: minor, moderate, major


class ApparatusParser:
    """Parser for apparatus criticus text."""

    # Common patterns in apparatus text
    SIGLA_PATTERN = r"(Cb|Ba|Bai|Bi|Ck|Fsb|Sy|Ro|PTS)"
    VARIANT_PATTERN = r"\{([^}]+)\}"
    LINE_REF_PATTERN = r"line\s+(\d+)"
    PAGE_REF_PATTERN = r"p\.\s*(\d+)"
    NOTE_PATTERN = r"\[([^\]]+)\]"

    def __init__(self):
        """Initialize the parser."""
        self.sigla_map = {
            "Cb": ManuscriptSigla.CAMBRIDGE,
            "Ba": ManuscriptSigla.BANGKOK_A,
            "Bai": ManuscriptSigla.BANGKOK_B,
            "Bi": ManuscriptSigla.BURMESE,
            "Ck": ManuscriptSigla.COLOMBO,
            "Fsb": ManuscriptSigla.FAUSBOLL,
            "Sy": ManuscriptSigla.SYAMARATTHA,
            "Ro": ManuscriptSigla.ROTA,
            "PTS": ManuscriptSigla.PTS,
        }

    def parse_apparatus_text(
        self, text: str, book_no: int, page_num: int
    ) -> List[ApparatusEntry]:
        """
        Parse apparatus criticus text into structured entries.

        Args:
            text: Raw apparatus text
            book_no: Book number for context
            page_num: Page number for context

        Returns:
            List of parsed apparatus entries
        """
        if not text or not text.strip():
            return []

        entries = []
        lines = text.strip().split("\n")

        current_entry = None
        current_variants = []
        current_note = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this is a new entry (starts with location info)
            if self._is_new_entry(line):
                # Save previous entry if exists
                if current_entry is not None:
                    entry = ApparatusEntry(
                        location=current_entry,
                        variants=current_variants.copy(),
                        note=current_note,
                    )
                    entries.append(entry)

                # Start new entry
                current_entry = self._extract_location(line, book_no, page_num)
                current_variants = []
                current_note = None

                # Extract variants from the line
                variants = self._extract_variants(line)
                if variants:
                    current_variants.extend(variants)

                # Extract note if present
                note = self._extract_note(line)
                if note:
                    current_note = note

            else:
                # Continuation of current entry
                if current_entry is not None:
                    # Extract additional variants
                    variants = self._extract_variants(line)
                    if variants:
                        current_variants.extend(variants)

                    # Extract additional note
                    note = self._extract_note(line)
                    if note:
                        if current_note:
                            current_note += " " + note
                        else:
                            current_note = note

        # Save the last entry
        if current_entry is not None:
            entry = ApparatusEntry(
                location=current_entry,
                variants=current_variants.copy(),
                note=current_note,
            )
            entries.append(entry)

        return entries

    def _is_new_entry(self, line: str) -> bool:
        """Check if a line starts a new apparatus entry."""
        # New entries typically start with location markers
        patterns = [
            r"^line\s+\d+",
            r"^p\.\s*\d+",
            r"^[A-Z][a-z]+\.?\s+",
            r"^[IVXLCDM]+\s+",
            r"^§\s*\d+",
        ]

        for pattern in patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True

        return False

    def _extract_location(self, line: str, book_no: int, page_num: int) -> str:
        """Extract location information from a line."""
        # Try to extract line number
        line_match = re.search(self.LINE_REF_PATTERN, line, re.IGNORECASE)
        if line_match:
            line_num = line_match.group(1)
            return f"Book {book_no}, Page {page_num}, line {line_num}"

        # Try to extract page reference
        page_match = re.search(self.PAGE_REF_PATTERN, line, re.IGNORECASE)
        if page_match:
            ref_page = page_match.group(1)
            return f"Book {book_no}, Page {page_num} (ref: p. {ref_page})"

        # Default location
        return f"Book {book_no}, Page {page_num}"

    def _extract_variants(self, line: str) -> List[Dict[str, Any]]:
        """Extract variant readings from a line."""
        variants = []

        # Find all variant text in braces
        variant_matches = re.finditer(self.VARIANT_PATTERN, line)
        for match in variant_matches:
            variant_text = match.group(1)

            # Find sigla associated with this variant
            # Look for sigla before the variant
            before_text = line[: match.start()]
            sigla_matches = re.findall(self.SIGLA_PATTERN, before_text)

            # Convert sigla strings to enum values
            sigla_list = []
            for siglum in sigla_matches:
                if siglum in self.sigla_map:
                    sigla_list.append(self.sigla_map[siglum])

            # Determine variant type
            variant_type = self._determine_variant_type(variant_text, line)

            # Determine significance
            significance = self._determine_significance(variant_text, sigla_list)

            variants.append(
                {
                    "text": variant_text,
                    "sigla": [s.value for s in sigla_list],
                    "sigla_objects": sigla_list,
                    "type": variant_type,
                    "significance": significance,
                    "raw": match.group(0),
                }
            )

        return variants

    def _extract_note(self, line: str) -> Optional[str]:
        """Extract notes from a line (text in square brackets)."""
        note_match = re.search(self.NOTE_PATTERN, line)
        if note_match:
            return note_match.group(1).strip()
        return None

    def _determine_variant_type(self, variant_text: str, context: str) -> str:
        """Determine the type of variant."""
        variant_lower = variant_text.lower()
        context_lower = context.lower()

        # Check for omission indicators
        omission_indicators = ["om.", "omit", "deest", "缺少", "ขาด"]
        for indicator in omission_indicators:
            if indicator in context_lower:
                return "omission"

        # Check for addition indicators
        addition_indicators = ["add.", "adds", "insert", "เพิ่ม", "ใส่"]
        for indicator in addition_indicators:
            if indicator in context_lower:
                return "addition"

        # Check for substitution
        substitution_indicators = ["for", "instead", "แทนที่", "แทน"]
        for indicator in substitution_indicators:
            if indicator in context_lower:
                return "substitution"

        # Check for transposition
        transposition_indicators = ["transp.", "transposed", "สลับ", "เปลี่ยนที่"]
        for indicator in transposition_indicators:
            if indicator in context_lower:
                return "transposition"

        # Default based on variant text characteristics
        if len(variant_text) < 5:
            return "minor_change"
        elif "..." in variant_text:
            return "fragment"
        else:
            return "substitution"

    def _determine_significance(
        self, variant_text: str, sigla: List[ManuscriptSigla]
    ) -> str:
        """Determine the significance of a variant."""
        # Major variants often involve key terms or longer passages
        key_terms = ["buddha", "dhamma", "sangha", "nibbana", "arahant"]
        variant_lower = variant_text.lower()

        for term in key_terms:
            if term in variant_lower:
                return "major"

        # Variants supported by multiple important manuscripts are more significant
        important_sigla = {
            ManuscriptSigla.CAMBRIDGE,
            ManuscriptSigla.PTS,
            ManuscriptSigla.ROTA,
        }
        important_count = sum(1 for s in sigla if s in important_sigla)

        if important_count >= 2:
            return "major"
        elif important_count == 1:
            return "moderate"
        else:
            return "minor"


class ApparatusFormatter:
    """Formatter for apparatus criticus display."""

    def __init__(self):
        """Initialize the formatter."""
        self.sigla_descriptions = {
            "Cb": "Cambridge manuscript",
            "Ba": "Bangkok A manuscript",
            "Bai": "Bangkok B manuscript",
            "Bi": "Burmese manuscript",
            "Ck": "Colombo manuscript",
            "Fsb": "Fausbøll edition",
            "Sy": "Syāmaratṭha edition",
            "Ro": "ROTA edition",
            "PTS": "PTS edition",
        }

        self.variant_type_descriptions = {
            "addition": "Addition",
            "omission": "Omission",
            "substitution": "Substitution",
            "transposition": "Transposition",
            "minor_change": "Minor change",
            "fragment": "Fragment",
        }

    def format_entry(self, entry: ApparatusEntry, format_type: str = "detailed") -> str:
        """
        Format an apparatus entry for display.

        Args:
            entry: Apparatus entry to format
            format_type: Format type ("detailed", "compact", "minimal")

        Returns:
            Formatted string
        """
        if format_type == "compact":
            return self._format_compact(entry)
        elif format_type == "minimal":
            return self._format_minimal(entry)
        else:  # detailed
            return self._format_detailed(entry)

    def _format_detailed(self, entry: ApparatusEntry) -> str:
        """Format entry in detailed style."""
        lines = []

        # Location header
        lines.append(f"📍 **{entry.location}**")
        lines.append("")

        # Variants
        if entry.variants:
            lines.append("**Variant Readings:**")
            for i, variant in enumerate(entry.variants, 1):
                variant_text = variant["text"]
                sigla = variant["sigla"]
                variant_type = variant["type"]
                significance = variant["significance"]

                # Format sigla with descriptions
                sigla_desc = []
                for siglum in sigla:
                    desc = self.sigla_descriptions.get(siglum, siglum)
                    sigla_desc.append(f"{siglum} ({desc})")

                sigla_str = ", ".join(sigla_desc)

                # Format based on significance
                if significance == "major":
                    prefix = "⚠️ **"
                    suffix = "**"
                elif significance == "moderate":
                    prefix = "▪️ "
                    suffix = ""
                else:
                    prefix = "◦ "
                    suffix = ""

                lines.append(f"{i}. {prefix}`{variant_text}`{suffix}")
                lines.append(f"   Manuscripts: {sigla_str}")
                lines.append(
                    f"   Type: {self.variant_type_descriptions.get(variant_type, variant_type)}"
                )
                lines.append(f"   Significance: {significance.capitalize()}")
                lines.append("")

        # Note
        if entry.note:
            lines.append("**Note:**")
            lines.append(f"> {entry.note}")
            lines.append("")

        return "\n".join(lines)

    def _format_compact(self, entry: ApparatusEntry) -> str:
        """Format entry in compact style."""
        lines = []

        # Location
        lines.append(f"**{entry.location}**")

        # Variants (compact)
        if entry.variants:
            variant_texts = []
            for variant in entry.variants:
                sigla = "/".join(variant["sigla"])
                variant_texts.append(f"{sigla}: `{variant['text']}`")

            lines.append("Variants: " + "; ".join(variant_texts))

        # Note (abbreviated)
        if entry.note:
            if len(entry.note) > 100:
                note = entry.note[:97] + "..."
            else:
                note = entry.note
            lines.append(f"Note: {note}")

        return " | ".join(lines)

    def _format_minimal(self, entry: ApparatusEntry) -> str:
        """Format entry in minimal style."""
        parts = [entry.location]

        if entry.variants:
            variant_count = len(entry.variants)
            parts.append(f"{variant_count} variant(s)")

        return " • ".join(parts)

    def format_sigla_key(self) -> str:
        """Format a key explaining manuscript sigla."""
        lines = ["**Manuscript Sigla Key:**", ""]

        for siglum, description in sorted(self.sigla_descriptions.items()):
            lines.append(f"• **{siglum}**: {description}")

        return "\n".join(lines)

    def format_variant_types_key(self) -> str:
        """Format a key explaining variant types."""
        lines = ["**Variant Type Key:**", ""]

        for vtype, description in sorted(self.variant_type_descriptions.items()):
            lines.append(
                f"• **{description}** ({vtype}): Different version of the text"
            )

        lines.append("")
        lines.append("**Significance Levels:**")
        lines.append("• **Major**: Affects meaning or key terms")
        lines.append("• **Moderate**: Notable textual difference")
        lines.append("• **Minor**: Minor orthographic or grammatical variation")

        return "\n".join(lines)


class ApparatusManager:
    """Manager for apparatus criticus operations."""

    def __init__(self, database_connection):
        """
        Initialize apparatus manager.

        Args:
            database_connection: SQLite database connection
        """
        self.conn = database_connection
        self.parser = ApparatusParser()
        self.formatter = ApparatusFormatter()
        self._cache = {}

    def get_apparatus_for_page(
        self, book_no: int, page_num: int, decode_func=None
    ) -> List[ApparatusEntry]:
        """
        Get apparatus criticus for a specific page.

        Args:
            book_no: Book number
            page_num: Page number
            decode_func: Function to decode UNITEXT fields

        Returns:
            List of apparatus entries
        """
        cache_key = f"{book_no}:{page_num}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            # Get apparatus text directly by numeric book_no, page_no
            cursor.execute(
                """
                SELECT unitext
                FROM footnotes
                WHERE book_no = ? AND page_no = ?
                """,
                (book_no, page_num),
            )

            apparatus_row = cursor.fetchone()
            if not apparatus_row or not apparatus_row["unitext"]:
                return []

            # Decode the apparatus text
            apparatus_text = apparatus_row["unitext"]
            if decode_func:
                apparatus_text = decode_func(apparatus_text)
            else:
                # Simple decode fallback
                apparatus_text = self._simple_decode(apparatus_text)

            # Parse the apparatus text
            entries = self.parser.parse_apparatus_text(
                apparatus_text, book_no, page_num
            )

            # Cache the results
            self._cache[cache_key] = entries

            return entries

        except Exception as e:
            print(f"Error getting apparatus for page {book_no}:{page_num}: {e}")
            return []

    def _simple_decode(self, text: str) -> str:
        """Text is already decoded in the clean database."""
        return text or ""

    def get_formatted_apparatus(
        self,
        book_no: int,
        page_num: int,
        format_type: str = "detailed",
        include_keys: bool = True,
    ) -> str:
        """
        Get formatted apparatus criticus for a page.

        Args:
            book_no: Book number
            page_num: Page number
            format_type: Format type ("detailed", "compact", "minimal")
            include_keys: Whether to include sigla and variant type keys

        Returns:
            Formatted apparatus text
        """
        entries = self.get_apparatus_for_page(book_no, page_num)

        if not entries:
            return "No apparatus criticus available for this page."

        lines = []

        # Add header
        lines.append(f"## Apparatus Criticus")
        lines.append(f"**Book {book_no}, Page {page_num}**")
        lines.append("")

        # Format each entry
        for i, entry in enumerate(entries, 1):
            formatted = self.formatter.format_entry(entry, format_type)
            lines.append(formatted)
            if i < len(entries):
                lines.append("---")
                lines.append("")

        # Add keys if requested
        if include_keys and format_type == "detailed":
            lines.append("")
            lines.append("---")
            lines.append("")
            lines.append(self.formatter.format_sigla_key())
            lines.append("")
            lines.append(self.formatter.format_variant_types_key())

        return "\n".join(lines)

    def get_apparatus_summary(self, book_no: int, page_num: int) -> Dict[str, Any]:
        """
        Get summary statistics for apparatus on a page.

        Args:
            book_no: Book number
            page_num: Page number

        Returns:
            Dictionary with summary statistics
        """
        entries = self.get_apparatus_for_page(book_no, page_num)

        if not entries:
            return {
                "has_apparatus": False,
                "book_no": book_no,
                "page_num": page_num,
                "message": "No apparatus criticus available",
            }

        total_variants = 0
        sigla_counts = {}
        type_counts = {}
        significance_counts = {"major": 0, "moderate": 0, "minor": 0}

        for entry in entries:
            total_variants += len(entry.variants)

            for variant in entry.variants:
                # Count sigla
                for siglum in variant["sigla"]:
                    sigla_counts[siglum] = sigla_counts.get(siglum, 0) + 1

                # Count types
                vtype = variant["type"]
                type_counts[vtype] = type_counts.get(vtype, 0) + 1

                # Count significance
                significance = variant["significance"]
                significance_counts[significance] = (
                    significance_counts.get(significance, 0) + 1
                )

        return {
            "has_apparatus": True,
            "book_no": book_no,
            "page_num": page_num,
            "entry_count": len(entries),
            "total_variants": total_variants,
            "sigla_counts": sigla_counts,
            "type_counts": type_counts,
            "significance_counts": significance_counts,
            "most_common_sigla": sorted(
                sigla_counts.items(), key=lambda x: x[1], reverse=True
            )[:3],
            "most_common_type": max(type_counts.items(), key=lambda x: x[1])
            if type_counts
            else None,
        }

    def clear_cache(self):
        """Clear the apparatus cache."""
        self._cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_size": len(self._cache),
            "cached_pages": list(self._cache.keys()),
        }


# Utility functions for integration
def create_apparatus_manager(database_path: str):
    """
    Create an apparatus manager for the given database.

    Args:
        database_path: Path to the SQLite database

    Returns:
        ApparatusManager instance or None if failed
    """
    try:
        import sqlite3

        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        return ApparatusManager(conn)
    except Exception as e:
        print(f"Error creating apparatus manager: {e}")
        return None


def get_apparatus_for_page(
    database_path: str, book_no: int, page_num: int, format_type: str = "detailed"
) -> str:
    """
    Convenience function to get formatted apparatus for a page.

    Args:
        database_path: Path to the SQLite database
        book_no: Book number
        page_num: Page number
        format_type: Format type

    Returns:
        Formatted apparatus text
    """
    manager = create_apparatus_manager(database_path)
    if manager:
        return manager.get_formatted_apparatus(book_no, page_num, format_type)
    return "Error: Could not create apparatus manager"


if __name__ == "__main__":
    # Test the apparatus module
    import os
    import sys

    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from config import get_config

    config = get_config()
    data_dir = config.get("paths.data_dir", "data")
    db_path = os.path.join(data_dir, "tipitaka.sqlite")

    if os.path.exists(db_path):
        print(f"Testing apparatus module with database: {db_path}")

        manager = create_apparatus_manager(db_path)
        if manager:
            # Test with a known page (Majjhima Nikāya I, page 3)
            test_book_no = 9  # Majjhima I
            test_page_num = 3

            print(
                f"\n1. Testing apparatus for Book {test_book_no}, Page {test_page_num}:"
            )

            # Get summary
            summary = manager.get_apparatus_summary(test_book_no, test_page_num)
            if summary["has_apparatus"]:
                print(
                    f"   Found {summary['entry_count']} entries with {summary['total_variants']} variants"
                )
                print(f"   Most common manuscripts: {summary['most_common_sigla']}")
                print(f"   Most common variant type: {summary['most_common_type']}")

                # Get formatted apparatus
                print(f"\n2. Formatted apparatus (detailed):")
                formatted = manager.get_formatted_apparatus(
                    test_book_no, test_page_num, "detailed"
                )
                print(formatted[:500] + "..." if len(formatted) > 500 else formatted)

                # Test compact format
                print(f"\n3. Formatted apparatus (compact):")
                compact = manager.get_formatted_apparatus(
                    test_book_no, test_page_num, "compact", include_keys=False
                )
                print(compact[:300] + "..." if len(compact) > 300 else compact)
            else:
                print(f"   No apparatus found for this page")
                print(f"   Trying another page...")

                # Try another page
                test_page_num = 1
                summary = manager.get_apparatus_summary(test_book_no, test_page_num)
                if summary["has_apparatus"]:
                    print(f"   Found apparatus on page {test_page_num}")
                    print(f"   Entry count: {summary['entry_count']}")
                else:
                    print(f"   No apparatus found on page {test_page_num} either")

            # Test cache statistics
            print(f"\n4. Cache statistics:")
            cache_stats = manager.get_cache_stats()
            print(f"   Cache size: {cache_stats['cache_size']}")
            print(
                f"   Cached pages: {cache_stats['cached_pages'][:3]}{'...' if len(cache_stats['cached_pages']) > 3 else ''}"
            )

    else:
        print(f"Database not found at: {db_path}")
        print("Please ensure the database exists and try again.")
