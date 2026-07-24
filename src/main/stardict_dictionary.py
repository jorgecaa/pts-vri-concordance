"""
StarDict-based dictionary module for Tipitaka PTS Browser.

This module provides dictionary lookup functionality using StarDict format files
instead of the SQLite database. StarDict format supports rich formatting and
is more up-to-date than the database dictionary.
"""

import gzip
import html
import os
import re
import struct
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Tuple


class StarDictReader:
    """Reader for StarDict dictionary files."""

    def __init__(self, dict_path: str):
        """
        Initialize StarDict reader.

        Args:
            dict_path: Path to dictionary directory or .ifo file
        """
        self.dict_path = Path(dict_path)
        self.info = {}
        self.idx_offset = 0
        self.syn_offset = 0
        self.idx_entries = []
        self.syn_entries = {}

        # Determine if we have a directory or .ifo file
        if self.dict_path.is_dir():
            ifo_files = list(self.dict_path.glob("*.ifo"))
            if ifo_files:
                self.ifo_path = ifo_files[0]
            else:
                raise FileNotFoundError(f"No .ifo file found in {dict_path}")
        else:
            self.ifo_path = self.dict_path

        # Load dictionary info
        self._load_info()

        # Load index
        self._load_index()

        # Load synonyms if available
        self._load_synonyms()

    def _load_info(self):
        """Load .ifo file information."""
        with open(self.ifo_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    key, value = line.split("=", 1)
                    self.info[key.strip()] = value.strip()

        # Parse important values
        self.bookname = self.info.get("bookname", "Unknown Dictionary")
        self.wordcount = int(self.info.get("wordcount", 0))
        self.idxfilesize = int(self.info.get("idxfilesize", 0))
        self.synwordcount = int(self.info.get("synwordcount", 0))
        self.sametypesequence = self.info.get("sametypesequence", "")

        # Get base path for other files
        self.base_path = self.ifo_path.with_suffix("")

    def _load_index(self):
        """Load .idx file."""
        idx_path = self.base_path.with_suffix(".idx")
        if not idx_path.exists():
            # Try .idx.gz
            idx_path = self.base_path.with_suffix(".idx.gz")
            if not idx_path.exists():
                raise FileNotFoundError(
                    f"Index file not found: {self.base_path}.idx[.gz]"
                )

        # Check if compressed
        if idx_path.suffix == ".gz":
            with gzip.open(idx_path, "rb") as f:
                idx_data = f.read()
        else:
            with open(idx_path, "rb") as f:
                idx_data = f.read()

        # Parse index entries
        offset = 0
        self.idx_entries = []

        while offset < len(idx_data):
            # Find null terminator for word
            null_pos = idx_data.find(b"\x00", offset)
            if null_pos == -1:
                break

            word = idx_data[offset:null_pos].decode("utf-8")
            offset = null_pos + 1

            # Read data offset and size (4 bytes each)
            if len(idx_data) - offset < 8:
                break

            data_offset = struct.unpack("!I", idx_data[offset : offset + 4])[0]
            data_size = struct.unpack("!I", idx_data[offset + 4 : offset + 8])[0]
            offset += 8

            self.idx_entries.append(
                {"word": word, "offset": data_offset, "size": data_size}
            )

    def _load_synonyms(self):
        """Load .syn file if available."""
        syn_path = self.base_path.with_suffix(".syn")
        if not syn_path.exists():
            # Try .syn.gz
            syn_path = self.base_path.with_suffix(".syn.gz")
            if not syn_path.exists():
                return

        # Check if compressed
        if syn_path.suffix == ".gz":
            with gzip.open(syn_path, "rb") as f:
                syn_data = f.read()
        else:
            with open(syn_path, "rb") as f:
                syn_data = f.read()

        # Parse synonym entries
        offset = 0
        self.syn_entries = {}

        while offset < len(syn_data):
            if len(syn_data) - offset < 8:
                break

            # Read synonym offset (4 bytes) and word (null-terminated)
            syn_offset = struct.unpack("!I", syn_data[offset : offset + 4])[0]
            offset += 4

            null_pos = syn_data.find(b"\x00", offset)
            if null_pos == -1:
                break

            word = syn_data[offset:null_pos].decode("utf-8")
            offset = null_pos + 1

            self.syn_entries[word] = syn_offset

    def lookup(
        self, word: str, exact: bool = True, raw_html: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Look up a word in the dictionary.

        Args:
            word: Word to look up
            exact: Whether to require exact match
            raw_html: If True, preserve HTML formatting in definitions

        Returns:
            List of dictionary entries
        """
        results = []

        if exact:
            # Exact match
            for entry in self.idx_entries:
                if entry["word"].lower() == word.lower():
                    results.append(self._get_entry(entry, raw_html=raw_html))
                    break
        else:
            # Partial match
            for entry in self.idx_entries:
                if word.lower() in entry["word"].lower():
                    results.append(self._get_entry(entry, raw_html=raw_html))

        return results

    def _get_entry(self, idx_entry: Dict, raw_html: bool = False) -> Dict[str, Any]:
        """Get dictionary entry for an index entry.

        Args:
            idx_entry: Index entry with offset and size
            raw_html: If True, preserve HTML formatting (don't convert to plain text)
        """
        # Read dictionary file
        dict_path = self.base_path.with_suffix(".dict")
        if not dict_path.exists():
            # Try .dict.dz (dictzip) or .dict.gz
            dict_path = self.base_path.with_suffix(".dict.dz")
            if not dict_path.exists():
                dict_path = self.base_path.with_suffix(".dict.gz")
                if not dict_path.exists():
                    raise FileNotFoundError(
                        f"Dictionary file not found: {self.base_path}.dict[.dz|.gz]"
                    )

        # Read data from dictionary file
        if dict_path.suffix in [".dz", ".gz"]:
            with gzip.open(dict_path, "rb") as f:
                f.seek(idx_entry["offset"])
                data = f.read(idx_entry["size"])
        else:
            with open(dict_path, "rb") as f:
                f.seek(idx_entry["offset"])
                data = f.read(idx_entry["size"])

        # Parse data based on sametypesequence
        definition = self._parse_definition(data, raw_html=raw_html)

        return {
            "headword": idx_entry["word"],
            "definition": definition,
            "source": self.bookname,
            "data_size": idx_entry["size"],
        }

    def _parse_definition(self, data: bytes, raw_html: bool = False) -> str:
        """Parse definition data based on sametypesequence.

        Args:
            data: Raw definition bytes from .dict file
            raw_html: If True, preserve HTML formatting
        """
        if not self.sametypesequence:
            # Default: assume 'm' (plain text)
            return data.decode("utf-8", errors="replace")

        # Handle HTML content (common in StarDict dictionaries)
        if "h" in self.sametypesequence:
            html_content = data.decode("utf-8", errors="replace")
            if raw_html:
                # Return raw HTML for display in QTextBrowser
                return html_content
            # Convert HTML to plain text with basic formatting
            plain_text = self._html_to_text(html_content)
            return plain_text

        # Handle plain text
        return data.decode("utf-8", errors="replace")

    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text with basic formatting."""
        # Unescape HTML entities
        text = html.unescape(html_content)

        # Replace common HTML tags with formatting
        replacements = [
            (r"<br\s*/?>", "\n"),
            (r"<p>", "\n"),
            (r"</p>", "\n"),
            (r"<h[1-6]>", "\n"),
            (r"</h[1-6]>", "\n"),
            (r"<li>", "\n• "),
            (r"</li>", ""),
            (r"<ul>", "\n"),
            (r"</ul>", "\n"),
            (r"<ol>", "\n"),
            (r"</ol>", "\n"),
            (r"<em>", "*"),
            (r"</em>", "*"),
            (r"<i>", "*"),
            (r"</i>", "*"),
            (r"<b>", "**"),
            (r"</b>", "**"),
            (r"<strong>", "**"),
            (r"</strong>", "**"),
            (r"<code>", "`"),
            (r"</code>", "`"),
            (r"<[^>]+>", ""),  # Remove any remaining tags
        ]

        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Clean up whitespace
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()

    def get_word_list(self, limit: int = 100) -> List[str]:
        """Get list of words in dictionary."""
        return [entry["word"] for entry in self.idx_entries[:limit]]

    def get_stats(self) -> Dict[str, Any]:
        """Get dictionary statistics."""
        return {
            "bookname": self.bookname,
            "wordcount": self.wordcount,
            "synwordcount": self.synwordcount,
            "has_synonyms": self.synwordcount > 0,
            "sametypesequence": self.sametypesequence,
        }


class StarDictManager:
    """Manager for multiple StarDict dictionaries."""

    def __init__(self, dicts_dir: str):
        """
        Initialize StarDict manager.

        Args:
            dicts_dir: Directory containing StarDict dictionaries
        """
        self.dicts_dir = Path(dicts_dir)
        self.dictionaries = {}
        self._load_dictionaries()

    def _load_dictionaries(self):
        """Load all StarDict dictionaries in the directory."""
        if not self.dicts_dir.exists():
            print(f"Warning: Dictionary directory not found: {self.dicts_dir}")
            return

        # Find all .ifo files
        ifo_files = list(self.dicts_dir.glob("*.ifo"))

        for ifo_file in ifo_files:
            try:
                dict_name = ifo_file.stem
                reader = StarDictReader(ifo_file)
                self.dictionaries[dict_name] = reader
                print(
                    f"Loaded dictionary: {reader.bookname} ({reader.wordcount} words)"
                )
            except Exception as e:
                print(f"Error loading dictionary {ifo_file}: {e}")

    def lookup(
        self,
        word: str,
        dict_names: Optional[List[str]] = None,
        exact: bool = True,
        limit_per_dict: int = 5,
        raw_html: bool = False,
    ) -> Dict[str, Any]:
        """
        Look up a word in specified dictionaries.

        Args:
            word: Word to look up
            dict_names: List of dictionary names to search (None for all)
            exact: Whether to require exact match
            limit_per_dict: Maximum results per dictionary
            raw_html: If True, preserve HTML formatting in definitions

        Returns:
            Dictionary with lookup results
        """
        if not self.dictionaries:
            return {
                "word": word,
                "error": "No dictionaries loaded",
                "results": [],
                "total_results": 0,
            }

        if dict_names is None:
            dict_names = list(self.dictionaries.keys())

        all_results = []

        for dict_name in dict_names:
            if dict_name not in self.dictionaries:
                continue

            dict_reader = self.dictionaries[dict_name]
            results = dict_reader.lookup(word, exact, raw_html=raw_html)

            # Limit results per dictionary
            if limit_per_dict and len(results) > limit_per_dict:
                results = results[:limit_per_dict]

            for result in results:
                result["dictionary"] = dict_name
                all_results.append(result)

        return {
            "word": word,
            "results": all_results,
            "total_results": len(all_results),
            "dictionaries_searched": dict_names,
            "exact_match": exact,
        }

    def get_available_dictionaries(self) -> List[Dict[str, Any]]:
        """Get list of available dictionaries with stats."""
        dict_list = []

        for name, reader in self.dictionaries.items():
            stats = reader.get_stats()
            dict_list.append(
                {
                    "name": name,
                    "bookname": stats["bookname"],
                    "wordcount": stats["wordcount"],
                    "has_synonyms": stats["has_synonyms"],
                }
            )

        return dict_list

    def search_by_definition(
        self, query: str, dict_names: Optional[List[str]] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search dictionary entries by definition content.

        Note: This is a simple linear search and may be slow for large dictionaries.

        Args:
            query: Search query
            dict_names: Dictionaries to search (None for all)
            limit: Maximum number of results

        Returns:
            List of matching entries
        """
        if not self.dictionaries:
            return []

        if dict_names is None:
            dict_names = list(self.dictionaries.keys())

        results = []
        query_lower = query.lower()

        for dict_name in dict_names:
            if dict_name not in self.dictionaries:
                continue

            dict_reader = self.dictionaries[dict_name]

            # Search through a subset of entries for performance
            for idx_entry in dict_reader.idx_entries[:1000]:  # Limit search scope
                entry = dict_reader._get_entry(idx_entry)
                definition = entry.get("definition", "").lower()

                if query_lower in definition:
                    entry["dictionary"] = dict_name
                    results.append(entry)

                    if len(results) >= limit:
                        return results

        return results


def create_stardict_manager(dicts_dir: str) -> Optional[StarDictManager]:
    """
    Create a StarDict manager instance.

    Args:
        dicts_dir: Directory containing StarDict dictionaries

    Returns:
        StarDictManager instance or None if failed
    """
    try:
        return StarDictManager(dicts_dir)
    except Exception as e:
        print(f"Error creating StarDict manager: {e}")
        return None


def lookup_word_stardict(dicts_dir: str, word: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to look up a word using StarDict.

    Args:
        dicts_dir: Directory containing StarDict dictionaries
        word: Word to look up
        **kwargs: Additional lookup parameters

    Returns:
        Dictionary entry
    """
    manager = create_stardict_manager(dicts_dir)
    if manager:
        return manager.lookup(word, **kwargs)

    return {
        "word": word,
        "error": "Failed to create StarDict manager",
        "results": [],
        "total_results": 0,
    }


if __name__ == "__main__":
    # Test the StarDict module
    import sys

    # Test with the dictionaries in the data directory
    test_dir = Path(__file__).parent.parent / "data" / "dictionaries"

    if test_dir.exists():
        print(f"Testing StarDict module with directory: {test_dir}")

        manager = create_stardict_manager(str(test_dir))
        if manager:
            print(f"\nAvailable dictionaries:")
            for dict_info in manager.get_available_dictionaries():
                print(f"  - {dict_info['bookname']}: {dict_info['wordcount']} words")

            # Test lookups
            test_words = ["dhamma", "buddha", "sangha", "nibbana"]

            for word in test_words:
                print(f"\nLooking up: '{word}'")
                result = manager.lookup(word, exact=True)

                if result["total_results"] > 0:
                    print(f"  Found {result['total_results']} entries:")
                    for entry in result["results"][:2]:  # Show first 2
                        print(f"    - {entry['headword']} ({entry['dictionary']})")
                        preview = (
                            entry["definition"][:100] + "..."
                            if len(entry["definition"]) > 100
                            else entry["definition"]
                        )
                        print(f"      {preview}")
                else:
                    print(f"  No exact matches found")

                    # Try fuzzy search
                    fuzzy_result = manager.lookup(word, exact=False, limit_per_dict=2)
                    if fuzzy_result["total_results"] > 0:
                        print(
                            f"  Found {fuzzy_result['total_results']} partial matches"
                        )
    else:
        print(f"Test directory not found: {test_dir}")
