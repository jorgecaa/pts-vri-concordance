"""
UI Integration Module for Tipitaka PTS Browser.

This module provides integration between the enhanced functionality modules
(search, dictionary, citation parser, apparatus, ROTA edition) and the QML user interface.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .apparatus import ApparatusManager, create_apparatus_manager
from .citation_parser import (
    PTSCitationParser,
    parse_pts_citation,
    validate_pts_citation,
)
from .database import TipitakaDatabase
from .rota_edition import ROTAManager, create_rota_manager, decode_rota_text

# Import enhanced modules
from .search import AdvancedSearch, create_search_instance

# Import StarDict dictionary module
try:
    from .stardict_dictionary import StarDictManager, create_stardict_manager

    STARDICT_AVAILABLE = True
except ImportError:
    STARDICT_AVAILABLE = False
    print("Warning: StarDict module not available, falling back to database dictionary")
    from .dictionary import DictionaryManager, create_dictionary_instance


class EnhancedTipitakaBrowser:
    """
    Enhanced browser with all new functionality integrated.

    This class extends the existing TipitakaBrowser functionality with
    the enhanced modules for search, dictionary, citation parsing, and apparatus.
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize enhanced browser.

        Args:
            data_dir: Directory containing data files
        """
        # Set up data directories
        self._setup_directories(data_dir)

        # Initialize enhanced modules
        self._search_instance = None
        self._dictionary_instance = None
        self._citation_parser = None
        self._apparatus_manager = None
        self._rota_manager = None
        self._database = None

        # Load data
        self._load_data()

        # Application state
        self.current_text = None
        self.current_edition = "PTS"
        self.search_history = []
        self.bookmarks = []
        self.recent_searches = []
        self.recent_lookups = []

    def _setup_directories(self, data_dir: Optional[str]) -> None:
        """Set up application directories."""
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Default data directory
            self.data_dir = Path(__file__).parent.parent / "data"

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Database path
        self.db_path = self.data_dir / "tipitaka.sqlite"

    def _load_data(self) -> None:
        """Load application data and initialize modules."""
        try:
            # Connect to database
            if self.db_path.exists():
                self._database = TipitakaDatabase(self.db_path)
                if self._database.connect():
                    # Initialize enhanced modules
                    self._search_instance = create_search_instance(str(self.db_path))

                    # Initialize dictionary - prefer StarDict over database
                    dicts_dir = self.data_dir / "dictionaries"
                    if STARDICT_AVAILABLE and dicts_dir.exists():
                        print("Using StarDict dictionaries")
                        self._dictionary_instance = create_stardict_manager(
                            str(dicts_dir)
                        )
                    else:
                        print("Using database dictionary (StarDict not available)")
                        self._dictionary_instance = create_dictionary_instance(
                            str(self.db_path)
                        )

                    self._citation_parser = PTSCitationParser()
                    self._apparatus_manager = create_apparatus_manager(
                        str(self.db_path)
                    )
                    self._rota_manager = create_rota_manager(str(self.db_path))
                else:
                    print("Warning: Failed to connect to database")
                    self._database = None
            else:
                print(f"Warning: Database not found at {self.db_path}")

        except Exception as e:
            print(f"Error loading data: {e}")

    # =========================================================================
    # ROTA Edition Functionality
    # =========================================================================

    def get_rota_page(self, book_no: int, page_num: int) -> Dict[str, Any]:
        """
        Get a page from the ROTA edition.

        Args:
            book_no: Book number
            page_num: Page number

        Returns:
            Dictionary with page data
        """
        if not self._rota_manager:
            return {"error": "ROTA manager not available"}

        try:
            page = self._rota_manager.get_page(book_no, page_num)
            if not page:
                return {"error": f"Page not found: Book {book_no}, Page {page_num}"}

            # Convert to dictionary
            return {
                "success": True,
                "book_no": page.book_no,
                "page_num": page.page_num,
                "head": page.head,
                "text": page.unitext,
                "thai_text": page.encpali,
                "footnotes": page.footnotes,
                "metadata": page.metadata,
                "edition": "mula",
                "has_thai_script": page.metadata.get("has_thai_script", False)
                if page.metadata
                else False,
            }

        except Exception as e:
            print(f"Error getting ROTA page: {e}")
            return {"error": str(e)}

    def get_rota_book_info(self, book_no: int) -> Dict[str, Any]:
        """
        Get information about a book in ROTA edition.

        Args:
            book_no: Book number

        Returns:
            Dictionary with book information
        """
        if not self._rota_manager:
            return {"error": "ROTA manager not available"}

        try:
            info = self._rota_manager.get_book_info(book_no)
            if not info:
                return {"error": f"Book not found: {book_no}"}

            return {"success": True, **info}

        except Exception as e:
            print(f"Error getting ROTA book info: {e}")
            return {"error": str(e)}

    def search_rota_text(
        self, query: str, book_no: Optional[int] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search in ROTA edition text.

        Args:
            query: Search query
            book_no: Optional book number to restrict search
            limit: Maximum number of results

        Returns:
            List of search results
        """
        if not self._rota_manager:
            return []

        try:
            return self._rota_manager.search_in_text(query, book_no, limit)
        except Exception as e:
            print(f"Error searching ROTA text: {e}")
            return []

    def get_rota_page_range(self, book_no: int) -> Dict[str, Any]:
        """
        Get page range for a book in ROTA edition.

        Args:
            book_no: Book number

        Returns:
            Dictionary with page range
        """
        if not self._rota_manager:
            return {"error": "ROTA manager not available"}

        try:
            first, last = self._rota_manager.get_page_range(book_no)
            return {
                "success": True,
                "book_no": book_no,
                "first_page": first,
                "last_page": last,
                "total_pages": last - first + 1,
            }
        except Exception as e:
            print(f"Error getting ROTA page range: {e}")
            return {"error": str(e)}

    def get_rota_available_books(self) -> List[Dict[str, Any]]:
        """
        Get list of all available books in ROTA edition.

        Returns:
            List of book information dictionaries
        """
        if not self._rota_manager:
            return []

        try:
            return self._rota_manager.get_available_books()
        except Exception as e:
            print(f"Error getting ROTA available books: {e}")
            return []

    def decode_rota_text(self, encoded_text: str) -> str:
        """
        Decode ROTA text from Base64 encoding.

        Args:
            encoded_text: Base64 encoded text

        Returns:
            Decoded text
        """
        return decode_rota_text(encoded_text)

    # =========================================================================
    # Enhanced Search Functionality
    # =========================================================================

    def enhanced_search(
        self, query: str, mode: str = "text", **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Perform enhanced search with multiple modes.

        Args:
            query: Search query
            mode: Search mode ("text", "word", "fuzzy", "exact")
            **kwargs: Additional search parameters

        Returns:
            List of search results
        """
        if not self._search_instance:
            return []

        try:
            results = self._search_instance.search(query, mode, **kwargs)

            # Add to search history
            self._add_to_search_history(query, mode, len(results))

            return results

        except Exception as e:
            print(f"Error in enhanced search: {e}")
            return []

    def search_by_word_index(self, word: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search using word index with proper decoding.

        Args:
            word: Word to search for
            limit: Maximum number of results

        Returns:
            List of search results with word index information
        """
        if not self._search_instance:
            return []

        try:
            return self._search_instance.search(word, mode="word", limit=limit)
        except Exception as e:
            print(f"Error in word index search: {e}")
            return []

    def fuzzy_search_words(
        self, query: str, threshold: float = 0.7, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Perform fuzzy search across words.

        Args:
            query: Search query
            threshold: Similarity threshold (0.0-1.0)
            limit: Maximum number of results

        Returns:
            List of fuzzy matches
        """
        if not self._search_instance:
            return []

        try:
            return self._search_instance.search(
                query, mode="fuzzy", threshold=threshold, limit=limit
            )
        except Exception as e:
            print(f"Error in fuzzy search: {e}")
            return []

    def get_word_statistics(self, word: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a word.

        Args:
            word: Word to analyze

        Returns:
            Dictionary with word statistics
        """
        if not self._search_instance:
            return {"word": word, "error": "Search not available"}

        try:
            return self._search_instance.get_word_statistics(word)
        except Exception as e:
            print(f"Error getting word statistics: {e}")
            return {"word": word, "error": str(e)}

    # =========================================================================
    # Enhanced Dictionary Functionality
    # =========================================================================

    def enhanced_dictionary_lookup(self, word: str, **kwargs) -> Dict[str, Any]:
        """
        Perform enhanced dictionary lookup.

        Args:
            word: Word to look up
            **kwargs: Additional lookup parameters

        Returns:
            Comprehensive dictionary entry
        """
        if not self._dictionary_instance:
            return {"word": word, "error": "Dictionary not available"}

        try:
            # Handle both StarDictManager and old DictionaryManager interfaces
            if hasattr(self._dictionary_instance, "lookup"):
                # StarDictManager interface
                result = self._dictionary_instance.lookup(word, **kwargs)

                # Convert to expected format
                if result.get("total_results", 0) > 0:
                    entries = []
                    for r in result.get("results", []):
                        entries.append(
                            {
                                "headword": r.get("headword", word),
                                "definition": r.get("definition", ""),
                                "source": r.get(
                                    "dictionary", r.get("source", "StarDict")
                                ),
                                "dictionary": r.get("dictionary", "Unknown"),
                            }
                        )

                    entry = {
                        "word": word,
                        "total_entries": result.get("total_results", 0),
                        "entries": entries,
                        "primary_entry": entries[0] if entries else None,
                        "cache_hit": False,
                        "dictionaries_searched": result.get(
                            "dictionaries_searched", []
                        ),
                    }
                else:
                    entry = {
                        "word": word,
                        "total_entries": 0,
                        "entries": [],
                        "primary_entry": None,
                        "error": "Word not found in dictionary",
                    }
            else:
                # Old DictionaryManager interface
                entry = self._dictionary_instance.get_entry(word, **kwargs)

            # Add to recent lookups
            self._add_to_recent_lookups(word, entry.get("total_entries", 0))

            return entry

        except Exception as e:
            print(f"Error in enhanced dictionary lookup: {e}")
            return {"word": word, "error": str(e)}

    def search_dictionary_by_definition(
        self, query: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search dictionary entries by definition content.

        Args:
            query: Search query for definitions
            limit: Maximum number of results

        Returns:
            List of dictionary entries
        """
        if not self._dictionary_instance:
            return []

        try:
            # This requires access to the underlying DictionaryLookup
            import sqlite3

            from .dictionary import DictionaryLookup

            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            lookup = DictionaryLookup(conn)

            return lookup.search_by_definition(query, limit)

        except Exception as e:
            print(f"Error searching dictionary by definition: {e}")
            return []

    def get_dictionary_cache_stats(self) -> Dict[str, Any]:
        """
        Get dictionary cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self._dictionary_instance:
            return {"error": "Dictionary not available"}

        try:
            return self._dictionary_instance.get_cache_stats()
        except Exception as e:
            print(f"Error getting dictionary cache stats: {e}")
            return {"error": str(e)}

    # =========================================================================
    # Enhanced Citation Parser Functionality
    # =========================================================================

    def parse_citation(self, citation: str) -> Dict[str, Any]:
        """
        Parse a PTS citation with enhanced validation.

        Args:
            citation: Citation string to parse

        Returns:
            Parsed citation with validation results
        """
        if not self._citation_parser:
            return {"citation": citation, "error": "Citation parser not available"}

        try:
            return self._citation_parser.validate_citation(citation)
        except Exception as e:
            print(f"Error parsing citation: {e}")
            return {"citation": citation, "error": str(e)}

    def get_text_by_citation(self, citation: str) -> Dict[str, Any]:
        """
        Get text by PTS citation with enhanced parsing.

        Args:
            citation: PTS citation string

        Returns:
            Dictionary with text and metadata
        """
        # First parse the citation
        parsed = self.parse_citation(citation)

        if not parsed.get("valid", False):
            return parsed

        # Get book_no and page from parsed citation
        book_no = parsed.get("book_no")
        page = parsed.get("parsed", {}).get("page")

        if not book_no or not page:
            return {"citation": citation, "error": "Could not resolve citation"}

        # Get text from ROTA edition
        if not self._rota_manager:
            return {"citation": citation, "error": "ROTA edition not available"}

        try:
            # Use ROTA edition method
            page_data = self.get_rota_page(book_no, page)

            if "error" in page_data:
                return {"citation": citation, "error": page_data["error"]}

            # Add apparatus if available
            apparatus = self.get_apparatus_for_page(book_no, page)

            return {
                "citation": citation,
                "parsed": parsed,
                "text": page_data.get("text", ""),
                "book_info": self.get_rota_book_info(book_no),
                "apparatus": apparatus,
                "edition": "mula",
                "success": True,
                **page_data,
            }

        except Exception as e:
            print(f"Error getting text by citation: {e}")
            return {"citation": citation, "error": str(e)}

    def format_citation(
        self, abbreviation: str, volume: int, page: int, format_style: str = "standard"
    ) -> str:
        """
        Format a citation in standard PTS style.

        Args:
            abbreviation: Book abbreviation
            volume: Volume number (0 for works without volumes)
            page: Page number
            format_style: Output format

        Returns:
            Formatted citation string
        """
        if not self._citation_parser:
            return f"{abbreviation} {volume} {page}"

        try:
            return self._citation_parser.format_citation(
                abbreviation, volume, page, format_style
            )
        except Exception as e:
            print(f"Error formatting citation: {e}")
            return f"{abbreviation} {volume} {page}"

    # =========================================================================
    # Enhanced Apparatus Criticus Functionality
    # =========================================================================

    def get_apparatus_for_page(
        self, book_no: int, page_num: int, format_type: str = "detailed"
    ) -> Union[str, List[Dict[str, Any]]]:
        """
        Get apparatus criticus for a page.

        Args:
            book_no: Book number
            page_num: Page number
            format_type: Format type ("detailed", "compact", "minimal", "raw")

        Returns:
            Formatted apparatus text or raw entries
        """
        if not self._apparatus_manager:
            return "Apparatus manager not available"

        try:
            if format_type == "raw":
                # Return raw entries for programmatic use
                return self._apparatus_manager.get_apparatus_for_page(book_no, page_num)
            else:
                # Return formatted text for display
                return self._apparatus_manager.get_formatted_apparatus(
                    book_no, page_num, format_type
                )

        except Exception as e:
            print(f"Error getting apparatus: {e}")
            return f"Error loading apparatus: {e}"

    def get_apparatus_summary(self, book_no: int, page_num: int) -> Dict[str, Any]:
        """
        Get summary statistics for apparatus on a page.

        Args:
            book_no: Book number
            page_num: Page number

        Returns:
            Dictionary with apparatus summary
        """
        if not self._apparatus_manager:
            return {"has_apparatus": False, "error": "Apparatus manager not available"}

        try:
            return self._apparatus_manager.get_apparatus_summary(book_no, page_num)
        except Exception as e:
            print(f"Error getting apparatus summary: {e}")
            return {"has_apparatus": False, "error": str(e)}

    def get_apparatus_cache_stats(self) -> Dict[str, Any]:
        """
        Get apparatus cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self._apparatus_manager:
            return {"error": "Apparatus manager not available"}

        try:
            return self._apparatus_manager.get_cache_stats()
        except Exception as e:
            print(f"Error getting apparatus cache stats: {e}")
            return {"error": str(e)}

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _add_to_search_history(self, query: str, mode: str, result_count: int) -> None:
        """Add search to history."""
        import datetime

        entry = {
            "query": query,
            "mode": mode,
            "result_count": result_count,
            "timestamp": datetime.datetime.now().isoformat(),
        }

        self.search_history.append(entry)

        # Keep history manageable
        if len(self.search_history) > 100:
            self.search_history = self.search_history[-100:]

    def _add_to_recent_lookups(self, word: str, entry_count: int) -> None:
        """Add dictionary lookup to recent lookups."""
        import datetime

        entry = {
            "word": word,
            "entry_count": entry_count,
            "timestamp": datetime.datetime.now().isoformat(),
        }

        self.recent_lookups.append(entry)

        # Keep recent lookups manageable
        if len(self.recent_lookups) > 50:
            self.recent_lookups = self.recent_lookups[-50:]

    def clear_caches(self) -> Dict[str, Any]:
        """
        Clear all module caches.

        Returns:
            Dictionary with cache clearing results
        """
        results = {}

        # Clear dictionary cache
        if self._dictionary_instance:
            try:
                self._dictionary_instance.clear_cache()
                results["dictionary"] = "Cache cleared"
            except Exception as e:
                results["dictionary"] = f"Error: {e}"

        # Clear apparatus cache
        if self._apparatus_manager:
            try:
                self._apparatus_manager.clear_cache()
                results["apparatus"] = "Cache cleared"
            except Exception as e:
                results["apparatus"] = f"Error: {e}"

        # Clear ROTA cache
        if self._rota_manager:
            try:
                self._rota_manager.clear_cache()
                results["rota"] = "Cache cleared"
            except Exception as e:
                results["rota"] = f"Error: {e}"

        # Clear search cache (if implemented)
        if self._search_instance:
            # Note: Search module doesn't have clear_cache method yet
            results["search"] = "No cache to clear"

        return results

    def get_module_status(self) -> Dict[str, Any]:
        """
        Get status of all enhanced modules.

        Returns:
            Dictionary with module status information
        """
        status = {
            "database": {
                "available": self._database is not None,
                "path": str(self.db_path) if self.db_path else None,
                "exists": self.db_path.exists() if self.db_path else False,
            },
            "search": {
                "available": self._search_instance is not None,
                "search_history_count": len(self.search_history),
            },
            "dictionary": {
                "available": self._dictionary_instance is not None,
                "recent_lookups_count": len(self.recent_lookups),
            },
            "citation_parser": {
                "available": self._citation_parser is not None,
            },
            "apparatus": {
                "available": self._apparatus_manager is not None,
            },
            "rota_edition": {
                "available": self._rota_manager is not None,
            },
        }

        # Add cache stats if available
        if self._dictionary_instance:
            try:
                cache_stats = self._dictionary_instance.get_cache_stats()
                status["dictionary"]["cache_stats"] = cache_stats
            except:
                pass

        if self._apparatus_manager:
            try:
                cache_stats = self._apparatus_manager.get_cache_stats()
                status["apparatus"]["cache_stats"] = cache_stats
            except:
                pass

        if self._rota_manager:
            try:
                cache_stats = self._rota_manager.get_cache_stats()
                status["rota_edition"]["cache_stats"] = cache_stats
            except:
                pass

        return status

    # =========================================================================
    # Backward Compatibility Methods
    # =========================================================================

    def search_texts(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Backward compatible search method.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of search results in old format
        """
        # Use enhanced search with text mode
        results = self.enhanced_search(query, mode="text", limit=limit)

        # Convert to old format if needed
        formatted_results = []
        for result in results:
            formatted_results.append(
                {
                    "id": f"{result.get('book_no', 0)}:{result.get('page_num', 0)}",
                    "title": result.get(
                        "page_title", f"Book {result.get('book_no', 0)}"
                    ),
                    "edition": "PTS",
                    "snippet": result.get("context", result.get("preview", ""))[:200],
                    "book_no": result.get("book_no"),
                    "page_num": result.get("page_num"),
                }
            )

        return formatted_results

    def lookup_dictionary(self, word: str) -> Optional[Dict[str, Any]]:
        """
        Backward compatible dictionary lookup.

        Args:
            word: Word to look up

        Returns:
            Dictionary entry in old format
        """
        entry = self.enhanced_dictionary_lookup(word)

        if "error" in entry:
            return None

        # Get first PTS entry if available
        pts_entries = entry.get("pts_entries", [])
        if pts_entries:
            first_entry = pts_entries[0]
            return {
                "word": first_entry.get("headword", word),
                "definition": first_entry.get("definition", ""),
                "etymology": "Pali",
                "examples": [],
                "source": first_entry.get("source", "PTS Dictionary"),
                "page": first_entry.get("page"),
            }

        # Get first bilingual entry if available
        bilingual_entries = entry.get("bilingual_entries", [])
        if bilingual_entries:
            first_entry = bilingual_entries[0]
            return {
                "word": first_entry.get("headword", word),
                "definition": first_entry.get("definition", ""),
                "etymology": "Pali",
                "examples": [],
                "source": first_entry.get("source", "Bilingual Dictionary"),
            }

        # Get first fuzzy match if available
        fuzzy_matches = entry.get("fuzzy_matches", [])
        if fuzzy_matches:
            first_match = fuzzy_matches[0]
            return {
                "word": first_match.get("headword", word),
                "definition": first_match.get(
                    "preview",
                    f"Similar word found: {first_match.get('headword', word)}",
                ),
                "etymology": "Pali",
                "examples": [],
                "source": first_match.get("source", "Fuzzy Match"),
            }

        # Fallback
        return {
            "word": word,
            "definition": f"Word '{word}' not found in dictionary",
            "etymology": "Pali",
            "examples": [],
            "source": "Not found",
        }

    def get_text(self, text_id: str, edition: Optional[str] = None) -> Optional[str]:
        """
        Backward compatible text retrieval.

        Args:
            text_id: PTS citation string
            edition: Edition to use

        Returns:
            Text content or None if not found
        """
        result = self.get_text_by_citation(text_id)

        if result.get("success", False):
            return result.get("text", "")

        return None

    def get_available_editions(self, text_id: str) -> List[str]:
        """
        Backward compatible editions method.

        Args:
            text_id: Text identifier

        Returns:
            List of available editions
        """
        # ROTA is the primary edition available
        return ["mula"]

    def add_bookmark(self, text_id: str, position: int, note: str = "") -> bool:
        """
        Backward compatible bookmark method.

        Args:
            text_id: Text identifier
            position: Position in text
            note: Optional note

        Returns:
            True if successful
        """
        import datetime

        bookmark = {
            "text_id": text_id,
            "position": position,
            "note": note,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self.bookmarks.append(bookmark)
        return True

    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Backward compatible settings method.

        Args:
            settings: Settings dictionary

        Returns:
            True if successful
        """
        try:
            import json

            settings_file = self.data_dir / "settings.json"
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)

            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def load_settings(self) -> Dict[str, Any]:
        """
        Backward compatible settings method.

        Returns:
            Settings dictionary
        """
        settings_file = self.data_dir / "settings.json"
        if settings_file.exists():
            try:
                import json

                with open(settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")

        # Default settings
        return {
            "language": "en",
            "font_size": 12,
            "theme": "light",
            "default_edition": "mula",
            "show_line_numbers": True,
            "auto_save_bookmarks": True,
            "enhanced_search_enabled": True,
            "show_apparatus": True,
            "dictionary_cache_enabled": True,
            "rota_edition_enabled": True,
            "show_thai_script": False,  # Default to Romanized text
        }


# Factory function for backward compatibility
def create_enhanced_browser(data_dir: Optional[str] = None) -> EnhancedTipitakaBrowser:
    """
    Create an enhanced browser instance.

    Args:
        data_dir: Data directory path

    Returns:
        EnhancedTipitakaBrowser instance
    """
    return EnhancedTipitakaBrowser(data_dir)


# Test function
def test_enhanced_functionality():
    """Test all enhanced functionality."""
    import os
    import sys

    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from config import get_config

    config = get_config()
    data_dir = config.get("paths.data_dir", "data")

    print("Testing Enhanced Tipitaka Browser Functionality")
    print("=" * 60)

    browser = create_enhanced_browser(data_dir)

    # Test module status
    print("\n1. Module Status:")
    status = browser.get_module_status()
    for module, info in status.items():
        available = info.get("available", False)
        status_symbol = "✓" if available else "✗"
        print(
            f"   {status_symbol} {module.capitalize()}: {'Available' if available else 'Not available'}"
        )

    # Test citation parsing
    print("\n2. Citation Parsing:")
    test_citations = ["M I 3", "Sn 25", "invalid"]
    for citation in test_citations:
        result = browser.parse_citation(citation)
        if result.get("valid", False):
            print(
                f"   ✓ '{citation}' → Book {result.get('book_no')}, Page {result.get('parsed', {}).get('page')}"
            )
        else:
            print(f"   ✗ '{citation}' → {result.get('error', 'Invalid')}")

    # Test enhanced search
    print("\n3. Enhanced Search:")
    search_results = browser.enhanced_search("dhamma", mode="text", limit=3)
    print(f"   Found {len(search_results)} results for 'dhamma'")

    # Test dictionary lookup
    print("\n4. Dictionary Lookup:")
    dict_entry = browser.enhanced_dictionary_lookup("dhamma")
    if "error" not in dict_entry:
        print(f"   Found {dict_entry.get('total_entries', 0)} dictionary entries")
        print(f"   Sources: {', '.join(dict_entry.get('sources_checked', []))}")
    else:
        print(f"   Error: {dict_entry.get('error')}")

    # Test apparatus
    print("\n5. Apparatus Criticus:")
    apparatus_summary = browser.get_apparatus_summary(9, 3)  # Majjhima I, page 3
    if apparatus_summary.get("has_apparatus", False):
        print(f"   Found {apparatus_summary.get('entry_count', 0)} apparatus entries")
        print(f"   Total variants: {apparatus_summary.get('total_variants', 0)}")
    else:
        print(
            f"   No apparatus found or error: {apparatus_summary.get('error', 'Unknown')}"
        )

    # Test backward compatibility
    print("\n6. Backward Compatibility:")
    old_search = browser.search_texts("buddha", limit=2)
    print(f"   Old search format: {len(old_search)} results")

    old_dict = browser.lookup_dictionary("buddha")
    if old_dict:
        print(f"   Old dictionary format: Found '{old_dict.get('word')}'")

    print("\nTesting complete!")


if __name__ == "__main__":
    test_enhanced_functionality()
