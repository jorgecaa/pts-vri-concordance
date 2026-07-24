"""
Enhanced dictionary module for Tipitaka PTS Browser with proper encoding handling.

This module provides improved dictionary lookup functionality that properly handles
the encoding in dictionary tables and provides more comprehensive search capabilities.
"""

import base64
import re
from typing import Any, Dict, List, Optional, Tuple

from rapidfuzz import fuzz, process


def decode_text_value(val: Optional[str]) -> str:
    """Decode a UNITEXT or similar encoded text field.

    Text columns are stored using a two-layer encoding:
    1. UTF-8 bytes with BOM (0xEF 0xBB 0xBF) prepended
    2. Base64-encoded

    Args:
        val: Encoded string value or None

    Returns:
        Decoded Unicode string
    """
    if not val:
        return ""

    # Text is already decoded in clean database
    return val


def decode_dict_entry_text(text: str) -> str:
    """Decode dictionary entry text with special handling for PTS dictionary formatting.

    Args:
        text: Dictionary entry text (may be encoded or contain special formatting)

    Returns:
        Decoded and formatted text
    """
    # First try to decode as Base64+BOM
    decoded = decode_text_value(text)

    # Clean up common formatting issues in PTS dictionary
    cleaned = decoded

    # Replace common formatting markers
    formatting_replacements = [
        (r"\\r\\n", "\n"),  # Windows line endings
        (r"\\n", "\n"),  # Unix line endings
        (r"\r\n", "\n"),  # Actual Windows line endings
        (r"\\t", "    "),  # Tabs
        (r"&nbsp;", " "),  # HTML non-breaking space
        (r"&amp;", "&"),  # HTML ampersand
        (r"&lt;", "<"),  # HTML less than
        (r"&gt;", ">"),  # HTML greater than
        (r"&quot;", '"'),  # HTML quote
        (r"&#(\d+);", lambda m: chr(int(m.group(1)))),  # HTML numeric entities
    ]

    for pattern, replacement in formatting_replacements:
        cleaned = re.sub(pattern, replacement, cleaned)

    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n", "\n\n", cleaned)

    return cleaned.strip()


def parse_pts_headword(headword: str) -> Dict[str, Any]:
    """Parse a PTS dictionary headword with sub-entry notation.

    PTS dictionary uses '^' character for sub-entry disambiguation.
    Example: 'a-^1', 'abhi-kankha^1', 'dhamma^1', 'dhamma^2'

    Args:
        headword: Headword string from TTITLE column

    Returns:
        Dictionary with parsed components
    """
    if not headword:
        return {"base": "", "subentry": 0, "full": ""}

    # Check for sub-entry notation
    if "^" in headword:
        parts = headword.split("^")
        base = parts[0].strip()
        try:
            subentry = int(parts[1]) if parts[1] else 0
        except ValueError:
            subentry = 0
    else:
        base = headword.strip()
        subentry = 0

    return {
        "base": base,
        "subentry": subentry,
        "full": headword,
        "has_subentry": subentry > 0,
    }


class DictionaryLookup:
    """Enhanced dictionary lookup with proper encoding handling."""

    def __init__(self, database_connection):
        """
        Initialize dictionary lookup.

        Args:
            database_connection: SQLite database connection
        """
        self.conn = database_connection
        self._entry_cache = {}  # Cache for decoded dictionary entries

    def lookup_pts_dictionary(
        self, word: str, exact_match: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Look up a word in the PTS Pāli-English dictionary.

        Args:
            word: Word to look up
            exact_match: Whether to require exact match or allow partial matches

        Returns:
            List of dictionary entries
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            if exact_match:
                # Exact match search
                cursor.execute(
                    """
                    SELECT TTITLE, TDETAIL, PAGE_NO, WORD_NO
                    FROM dict_pts
                    WHERE TTITLE = ? 
                    ORDER BY TTITLE
                    """,
                    (word,),
                )
            else:
                # Partial match search
                cursor.execute(
                    """
                    SELECT TTITLE, TDETAIL, PAGE_NO, WORD_NO
                    FROM dict_pts
                    WHERE TTITLE LIKE ? 
                    ORDER BY TTITLE
                    LIMIT 50
                    """,
                    (f"%{word}%",),
                )

            rows = cursor.fetchall()
            results = []

            for row in rows:
                headword = row["TTITLE"]
                detail = row["TDETAIL"]
                page_no = row["PAGE_NO"]
                word_no = row["WORD_NO"]

                # Parse headword
                parsed_headword = parse_pts_headword(headword)

                # Decode and clean the detail text
                decoded_detail = decode_dict_entry_text(detail)

                # Extract first paragraph for preview
                preview = decoded_detail.split("\n")[0]
                if len(preview) > 200:
                    preview = preview[:200] + "..."

                results.append(
                    {
                        "headword": headword,
                        "parsed_headword": parsed_headword,
                        "definition": decoded_detail,
                        "preview": preview,
                        "page": page_no,
                        "word_no": word_no,
                        "source": "PTS Dictionary",
                        "match_type": "exact" if exact_match else "partial",
                    }
                )

            return results

        except Exception as e:
            print(f"Error looking up PTS dictionary: {e}")
            return []

    def lookup_bilingual_dictionary(
        self, word: str, language: str = "thai"
    ) -> List[Dict[str, Any]]:
        """
        Look up a word in the bilingual dictionary.

        Args:
            word: Word to look up
            language: Language to search in ('thai' or 'english')

        Returns:
            List of dictionary entries
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            if language.lower() == "thai":
                # Search in Thai headwords
                cursor.execute(
                    """
                    SELECT TTITLE, ETITLE, TDETAIL, EDETAIL, KEY, NUMBER
                    FROM dict_pali_english
                    WHERE TTITLE LIKE ? 
                    ORDER BY TTITLE
                    LIMIT 50
                    """,
                    (f"%{word}%",),
                )
            else:
                # Search in English headwords
                cursor.execute(
                    """
                    SELECT TTITLE, ETITLE, TDETAIL, EDETAIL, KEY, NUMBER
                    FROM dict_pali_english
                    WHERE ETITLE LIKE ? 
                    ORDER BY ETITLE
                    LIMIT 50
                    """,
                    (f"%{word}%",),
                )

            rows = cursor.fetchall()
            results = []

            for row in rows:
                thai_headword = row["TTITLE"]
                english_headword = row["ETITLE"]
                thai_detail = row["TDETAIL"]
                english_detail = row["EDETAIL"]
                key = row["KEY"]
                number = row["NUMBER"]

                # Clean up details
                thai_definition = (
                    decode_dict_entry_text(thai_detail) if thai_detail else ""
                )
                english_definition = (
                    decode_dict_entry_text(english_detail) if english_detail else ""
                )

                # Use appropriate definition based on search language
                if language.lower() == "thai":
                    definition = thai_definition or english_definition
                    headword = thai_headword
                    other_headword = english_headword
                else:
                    definition = english_definition or thai_definition
                    headword = english_headword
                    other_headword = thai_headword

                # Extract preview
                preview = definition.split("\n")[0]
                if len(preview) > 200:
                    preview = preview[:200] + "..."

                results.append(
                    {
                        "headword": headword,
                        "other_headword": other_headword,
                        "definition": definition,
                        "preview": preview,
                        "key": key,
                        "number": number,
                        "source": "Bilingual Dictionary",
                        "language": language,
                        "has_thai": bool(thai_headword),
                        "has_english": bool(english_headword),
                    }
                )

            return results

        except Exception as e:
            print(f"Error looking up bilingual dictionary: {e}")
            return []

    def fuzzy_search_dictionary(
        self, word: str, threshold: float = 0.7, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Perform fuzzy search across dictionary headwords.

        Args:
            word: Word to search for
            threshold: Minimum similarity threshold (0.0 to 1.0)
            limit: Maximum number of results

        Returns:
            List of similar dictionary entries
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            # Get all headwords from PTS dictionary
            cursor.execute(
                """
                SELECT TTITLE, TDETAIL, PAGE_NO
                FROM dict_pts
                WHERE 1=1
                LIMIT 5000  # Limit for performance
                """
            )

            pts_words = cursor.fetchall()

            # Get all headwords from bilingual dictionary (English)
            cursor.execute(
                """
                SELECT ETITLE, EDETAIL, KEY
                FROM dict_pali_english
                WHERE ETITLE IS NOT NULL AND ETITLE != '' 
                LIMIT 5000  # Limit for performance
                """
            )

            bilingual_words = cursor.fetchall()

            # Combine word lists
            word_list = []
            for row in pts_words:
                headword = row["TTITLE"]
                if headword and len(headword) > 1:
                    word_list.append(("pts", headword, row["TDETAIL"], row["PAGE_NO"]))

            for row in bilingual_words:
                headword = row["ETITLE"]
                if headword and len(headword) > 1:
                    word_list.append(
                        ("bilingual", headword, row["EDETAIL"], row["KEY"])
                    )

            # Perform fuzzy matching
            matches = process.extract(
                word, [w[1] for w in word_list], scorer=fuzz.ratio, limit=limit
            )

            results = []
            for matched_word, score, index in matches:
                if score >= threshold * 100:  # Convert to percentage
                    source, headword, detail, ref = word_list[index]

                    # Parse and decode based on source
                    if source == "pts":
                        parsed = parse_pts_headword(headword)
                        definition = decode_dict_entry_text(detail)
                        source_name = "PTS Dictionary"
                        reference = f"Page {ref}"
                    else:
                        parsed = {"base": headword, "subentry": 0, "full": headword}
                        definition = decode_dict_entry_text(detail)
                        source_name = "Bilingual Dictionary"
                        reference = f"Key {ref}"

                    # Extract preview
                    preview = definition.split("\n")[0]
                    if len(preview) > 200:
                        preview = preview[:200] + "..."

                    results.append(
                        {
                            "headword": headword,
                            "parsed_headword": parsed,
                            "definition": definition,
                            "preview": preview,
                            "similarity": score / 100.0,
                            "source": source_name,
                            "reference": reference,
                            "match_type": "fuzzy",
                        }
                    )

            return sorted(results, key=lambda x: x["similarity"], reverse=True)

        except Exception as e:
            print(f"Error in fuzzy dictionary search: {e}")
            return []

    def get_comprehensive_entry(self, word: str) -> Dict[str, Any]:
        """
        Get comprehensive dictionary entry combining all sources.

        Args:
            word: Word to look up

        Returns:
            Comprehensive dictionary entry with all available information
        """
        results = {
            "word": word,
            "pts_entries": [],
            "bilingual_entries": [],
            "fuzzy_matches": [],
            "has_exact_match": False,
            "sources_checked": [],
        }

        # Look up in PTS dictionary
        pts_results = self.lookup_pts_dictionary(word, exact_match=True)
        if pts_results:
            results["pts_entries"] = pts_results
            results["has_exact_match"] = True
            results["sources_checked"].append("PTS Dictionary (exact)")

        # Look up in bilingual dictionary (English)
        bilingual_results = self.lookup_bilingual_dictionary(word, language="english")
        if bilingual_results:
            results["bilingual_entries"] = bilingual_results
            results["has_exact_match"] = True
            results["sources_checked"].append("Bilingual Dictionary (English)")

        # If no exact matches, try fuzzy search
        if not results["has_exact_match"]:
            fuzzy_results = self.fuzzy_search_dictionary(word, threshold=0.7, limit=10)
            if fuzzy_results:
                results["fuzzy_matches"] = fuzzy_results
                results["sources_checked"].append("Fuzzy Search")

        # Also try partial matches in PTS dictionary
        if not pts_results:
            pts_partial = self.lookup_pts_dictionary(word, exact_match=False)
            if pts_partial:
                results["pts_entries"] = pts_partial
                results["sources_checked"].append("PTS Dictionary (partial)")

        # Get word statistics if available
        results["total_entries"] = (
            len(results["pts_entries"])
            + len(results["bilingual_entries"])
            + len(results["fuzzy_matches"])
        )

        return results

    def search_by_definition(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search dictionary entries by definition content.

        Args:
            query: Search query for definition content
            limit: Maximum number of results

        Returns:
            List of dictionary entries matching the query
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            # Search in PTS dictionary definitions
            cursor.execute(
                """
                SELECT TTITLE, TDETAIL, PAGE_NO
                FROM dict_pts
                WHERE TDETAIL LIKE ? 
                ORDER BY TTITLE
                LIMIT ?
                """,
                (f"%{query}%", limit),
            )

            pts_rows = cursor.fetchall()
            results = []

            for row in pts_rows:
                headword = row["TTITLE"]
                detail = row["TDETAIL"]
                page_no = row["PAGE_NO"]

                # Decode and clean
                definition = decode_dict_entry_text(detail)

                # Find query in definition (case-insensitive)
                query_lower = query.lower()
                definition_lower = definition.lower()

                if query_lower in definition_lower:
                    # Highlight the query in preview
                    preview = definition
                    if len(preview) > 300:
                        # Try to show context around the query
                        pos = definition_lower.find(query_lower)
                        if pos >= 0:
                            start = max(0, pos - 100)
                            end = min(len(definition), pos + len(query) + 100)
                            preview = definition[start:end]
                            if start > 0:
                                preview = "..." + preview
                            if end < len(definition):
                                preview = preview + "..."

                    parsed_headword = parse_pts_headword(headword)

                    results.append(
                        {
                            "headword": headword,
                            "parsed_headword": parsed_headword,
                            "definition": definition,
                            "preview": preview,
                            "page": page_no,
                            "source": "PTS Dictionary",
                            "match_type": "definition",
                            "match_field": "TDETAIL",
                        }
                    )

            return results

        except Exception as e:
            print(f"Error searching by definition: {e}")
            return []


class DictionaryManager:
    """Manager for dictionary operations with caching and advanced features."""

    def __init__(self, database_connection):
        """
        Initialize dictionary manager.

        Args:
            database_connection: SQLite database connection
        """
        self.conn = database_connection
        self.lookup = DictionaryLookup(database_connection)
        self._cache = {}
        self._search_history = []

    def get_entry(self, word: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get dictionary entry with caching.

        Args:
            word: Word to look up
            use_cache: Whether to use cache

        Returns:
            Dictionary entry
        """
        cache_key = word.lower()

        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        entry = self.lookup.get_comprehensive_entry(word)

        # Add to cache
        if use_cache:
            self._cache[cache_key] = entry

        # Add to search history
        self._search_history.append(
            {
                "word": word,
                "timestamp": self._get_timestamp(),
                "has_results": entry["total_entries"] > 0,
            }
        )

        # Keep history manageable
        if len(self._search_history) > 100:
            self._search_history = self._search_history[-100:]

        return entry

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime

        return datetime.now().isoformat()

    def clear_cache(self):
        """Clear the dictionary cache."""
        self._cache.clear()

    def get_search_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get search history.

        Args:
            limit: Maximum number of history entries to return

        Returns:
            List of search history entries
        """
        return self._search_history[-limit:] if self._search_history else []

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_size": len(self._cache),
            "history_size": len(self._search_history),
            "cache_keys": list(self._cache.keys())[:10],  # First 10 keys
        }


# Utility functions for integration with existing codebase
def create_dictionary_instance(database_path: str):
    """
    Create a dictionary instance for the given database.

    Args:
        database_path: Path to the SQLite database

    Returns:
        DictionaryManager instance or None if failed
    """
    try:
        import sqlite3

        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        return DictionaryManager(conn)
    except Exception as e:
        print(f"Error creating dictionary instance: {e}")
        return None


def lookup_word(database_path: str, word: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to look up a word in the dictionary.

    Args:
        database_path: Path to the SQLite database
        word: Word to look up
        **kwargs: Additional lookup parameters

    Returns:
        Dictionary entry
    """
    dict_manager = create_dictionary_instance(database_path)
    if dict_manager:
        return dict_manager.get_entry(word, **kwargs)
    return {"word": word, "error": "Failed to create dictionary instance"}


if __name__ == "__main__":
    # Test the dictionary module
    import os
    import sys

    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from config import get_config

    config = get_config()
    data_dir = config.get("paths.data_dir", "data")
    db_path = os.path.join(data_dir, "tipitaka.sqlite")

    if os.path.exists(db_path):
        print(f"Testing dictionary module with database: {db_path}")

        dict_manager = create_dictionary_instance(db_path)
        if dict_manager:
            # Test different lookup methods
            test_words = ["dhamma", "buddha", "sangha"]

            for test_word in test_words:
                print(f"\n1. Testing comprehensive lookup for '{test_word}':")
                entry = dict_manager.get_entry(test_word)
                print(f"   Found {entry.get('total_entries', 0)} entries")
                print(
                    f"   Sources checked: {', '.join(entry.get('sources_checked', []))}"
                )

                if entry.get("pts_entries"):
                    print(f"   PTS entries: {len(entry['pts_entries'])}")
                    for i, pts_entry in enumerate(entry["pts_entries"][:2]):
                        print(f"     {i + 1}. {pts_entry.get('headword', 'Unknown')}")
                        print(
                            f"        Preview: {pts_entry.get('preview', '')[:100]}..."
                        )

                if entry.get("bilingual_entries"):
                    print(f"   Bilingual entries: {len(entry['bilingual_entries'])}")

                if entry.get("fuzzy_matches"):
                    print(f"   Fuzzy matches: {len(entry['fuzzy_matches'])}")

            print(f"\n2. Testing fuzzy dictionary search for 'dharma':")
            dict_lookup = DictionaryLookup(dict_manager.conn)
            fuzzy_results = dict_lookup.fuzzy_search_dictionary(
                "dharma", threshold=0.6, limit=5
            )
            print(f"   Found {len(fuzzy_results)} fuzzy matches")
            for i, result in enumerate(fuzzy_results[:3]):
                print(f"   {i + 1}. {result.get('headword', 'Unknown')}")
                print(f"      Similarity: {result.get('similarity', 0):.2f}")
                print(f"      Source: {result.get('source', 'Unknown')}")

            print(f"\n3. Testing search by definition for 'doctrine':")
            definition_results = dict_lookup.search_by_definition("doctrine", limit=5)
            print(
                f"   Found {len(definition_results)} entries with 'doctrine' in definition"
            )
            for i, result in enumerate(definition_results[:3]):
                print(f"   {i + 1}. {result.get('headword', 'Unknown')}")
                print(f"      Preview: {result.get('preview', '')[:100]}...")

            print(f"\n4. Testing cache statistics:")
            cache_stats = dict_manager.get_cache_stats()
            print(f"   Cache size: {cache_stats.get('cache_size', 0)}")
            print(f"   History size: {cache_stats.get('history_size', 0)}")
            print(f"   Cache keys (first 10): {cache_stats.get('cache_keys', [])}")

    else:
        print(f"Database not found at: {db_path}")
        print("Please ensure the database exists and try again.")
