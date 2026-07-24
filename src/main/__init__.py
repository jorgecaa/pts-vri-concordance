"""
Tipitaka PTS Browser - Main Application Module

This module contains the main application logic for the Tipitaka PTS Browser,
a tool for browsing and studying Pali Tipitaka texts.

Enhanced version with ROTA edition support, advanced search, dictionary,
apparatus criticus, and citation parsing.
"""

# Try to import robust search module
try:
    from .robust_search import create_robust_search

    ROBUST_SEARCH_AVAILABLE = True
except ImportError:
    ROBUST_SEARCH_AVAILABLE = False
    print("Warning: Robust search module not available. Using basic search.")

__version__ = "1.0.0"
__author__ = "Tipitaka PTS Browser Team"
__license__ = "GPL-3.0"

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import database module and enhanced browser
from .ui_integration import create_enhanced_browser

# Try to import Qt modules
try:
    from PyQt6.QtCore import QObject, pyqtSignal
    from PyQt6.QtWidgets import QApplication

    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    print("Warning: PyQt6 not available. UI functionality will be limited.")


class TipitakaBrowser(QObject if QT_AVAILABLE else object):
    """
    Main application controller for the Tipitaka PTS Browser.

    This class manages the application state, data access, and UI interactions.

    NOTE: This is now a compatibility wrapper around EnhancedTipitakaBrowser
    to maintain backward compatibility with existing QML code.
    """

    # Signals (only if Qt is available)
    if QT_AVAILABLE:
        textLoaded = pyqtSignal(str, str)  # text_id, text_content
        searchResultsReady = pyqtSignal(list)
        dictionaryLookupReady = pyqtSignal(dict)
        settingsChanged = pyqtSignal(dict)

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the Tipitaka Browser application.

        Args:
            data_dir: Directory containing data files. If None, uses default location.
        """
        super().__init__()

        # Set up data directories
        self._setup_directories(data_dir)

        # Create enhanced browser instance
        self._enhanced_browser = create_enhanced_browser(str(self.data_dir))

        # Initialize robust search
        self._robust_search = None
        if ROBUST_SEARCH_AVAILABLE:
            try:
                db_path = self.data_dir / "tipitaka.sqlite"
                if db_path.exists():
                    self._robust_search = create_robust_search(str(db_path))
            except Exception as e:
                print(f"Failed to initialize robust search: {e}")

        # Initialize data structures (for compatibility)
        self._edition_conversions = None
        self._matn_relations = None
        self._database = self._enhanced_browser._database
        self._dictionary = None

        # Application state
        self.current_text = None
        self.current_edition = "PTS"  # Default to PTS edition
        self.search_history = []
        self.bookmarks = []

        # Load data
        self._load_data()

    def _setup_directories(self, data_dir: Optional[str]) -> None:
        """Set up application directories."""
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Default data directory
            self.data_dir = Path(__file__).parent.parent / "data"

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Dictionary directory
        self.dict_dir = self.data_dir / "dictionaries"
        self.dict_dir.mkdir(exist_ok=True)

        # Documents directory
        self.docs_dir = Path(__file__).parent.parent / "docs"
        self.docs_dir.mkdir(exist_ok=True)

    def _load_data(self) -> None:
        """Load application data from files."""
        try:
            # Load edition conversions
            conversions_file = self.data_dir / "edition_conversions.json"
            if conversions_file.exists():
                with open(conversions_file, "r", encoding="utf-8") as f:
                    self._edition_conversions = json.load(f)

            # Load matn relations
            relations_file = self.data_dir / "matn_relations.json"
            if relations_file.exists():
                with open(relations_file, "r", encoding="utf-8") as f:
                    self._matn_relations = json.load(f)

            # Enhanced browser already has database connection
            if self._enhanced_browser._database:
                self._database = self._enhanced_browser._database
                print("Connected to database via EnhancedTipitakaBrowser")

                # Check ROTA edition availability
                rota_books = self._enhanced_browser.get_rota_available_books()
                if rota_books:
                    print(f"ROTA edition available with {len(rota_books)} books")
                else:
                    print("Warning: ROTA edition not available in database")

            # Load dictionary (if available)
            dict_file = self.dict_dir / "critical-pali-dictionary"
            if dict_file.exists():
                # Dictionary loading logic would go here
                pass

        except Exception as e:
            print(f"Error loading data: {e}")

    def get_text(
        self, text_id: str, edition: Optional[str] = None, include_thai: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve text by PTS citation.

        Args:
            text_id: PTS citation string (e.g., "M I 3" or "Sn 25")
            edition: Edition to use ("mula" or "PTS")
            include_thai: Whether to include Thai script text if available

        Returns:
            Dictionary with text content and metadata, or None if not found
        """
        if not edition:
            edition = self.current_edition

        if not self._enhanced_browser:
            return None

        try:
            result = {
                "text": None,
                "thai_text": None,
                "edition": edition,
                "text_id": text_id,
                "metadata": {},
            }

            # Use enhanced browser to get text
            if edition.lower() == "mula":
                # Parse citation for ROTA edition
                parsed = self._enhanced_browser.parse_citation(text_id)
                if parsed:
                    book_no = parsed.get("book_no")
                    # Handle nested parser structure: parsed['parsed']['page']
                    parsed_dict = parsed.get("parsed", {})
                    page_num = parsed_dict.get("page")
                    if book_no and page_num:
                        rota_text = self._enhanced_browser.get_rota_page(
                            book_no, page_num
                        )
                        if rota_text:
                            result["text"] = rota_text.get("text", "")
                            result["metadata"]["book_no"] = book_no
                            result["metadata"]["page_num"] = page_num

                            # Include Thai script if requested and available
                            if include_thai and rota_text.get("encpali"):
                                result["thai_text"] = rota_text.get("encpali")

                            # Add additional metadata if available
                            if rota_text.get("book_name"):
                                result["metadata"]["book_name"] = rota_text.get(
                                    "book_name"
                                )
                            if rota_text.get("page_title"):
                                result["metadata"]["page_title"] = rota_text.get(
                                    "page_title"
                                )
            else:
                # PTS edition – use database with cleaned text
                page_data = self._database.get_page_by_pts_citation(text_id)
                if page_data:
                    result["text"] = page_data.get("text", "")
                    result["metadata"] = {
                        "book_no": page_data.get("book_no"),
                        "page_num": page_data.get("page_num"),
                        "head": page_data.get("head", ""),
                    }

            return result if result["text"] else None
        except Exception as e:
            print(f"Error retrieving text {text_id} ({edition}): {e}")
            return None

    def search_texts(
        self, query: str, limit: int = 50, mode: str = "text"
    ) -> List[Dict[str, Any]]:
        """
        Search for texts containing the query.

        Args:
            query: Search string
            limit: Maximum number of results to return
            mode: Search mode ("exact", "text", "fuzzy")

        Returns:
            List of search results
        """
        # Try robust search first
        if self._robust_search:
            try:
                results = self._robust_search.search(query, mode=mode, limit=limit)
                if results:
                    return results
            except Exception as e:
                print(f"Robust search failed, falling back to basic: {e}")

        # Fall back to enhanced browser
        if not self._enhanced_browser:
            return []

        try:
            # Use enhanced browser for search with multiple modes
            search_results = self._enhanced_browser.enhanced_search(
                query,
                mode=mode,
                limit=limit,
            )

            # Format results for compatibility
            formatted_results = []
            for result in search_results:
                formatted_results.append(
                    {
                        "id": f"{result.get('book_no', 0)}:{result.get('page_num', 0)}",
                        "title": result.get(
                            "book_name", f"Book {result.get('book_no', 0)}"
                        ),
                        "edition": "mula",
                        "snippet": result.get("context", ""),
                        "book_no": result.get("book_no"),
                        "page_num": result.get("page_num"),
                        "word": result.get("matched_word", query),
                        "frequency": result.get("frequency", 1),
                        "score": result.get("score", 0.0),
                        "search_mode": result.get("search_mode", mode),
                    }
                )

            return formatted_results
        except Exception as e:
            print(f"Error searching texts: {e}")
            return []

    def get_search_modes(self) -> List[Dict[str, str]]:
        """
        Get available search modes.

        Returns:
            List of search mode descriptions
        """
        if self._robust_search:
            try:
                return self._robust_search.get_search_modes()
            except Exception as e:
                print(f"Error getting search modes: {e}")

        # Default modes
        return [
            {
                "id": "text",
                "name": "Text Search",
                "description": "Search in text content",
            },
            {
                "id": "exact",
                "name": "Exact Word",
                "description": "Search for exact word matches",
            },
        ]

    def get_available_editions(self, text_id: str) -> List[str]:
        """
        Get available editions for a specific text.

        Args:
            text_id: Text identifier

        Returns:
            List of available editions
        """
        # Per-text edition availability lives in the edition_conversions data
        # (which reference editions — PTS, MYANMAR, VRI, … — exist for this text).
        if self._edition_conversions:
            book = self._edition_conversions.get("books", {}).get(text_id)
            if book and book.get("available_editions"):
                return list(book["available_editions"])

        # Default when the text is unknown or no conversion data is loaded.
        return ["PTS"]

    def lookup_dictionary(self, word: str) -> Optional[Dict[str, Any]]:
        """
        Look up a word in the dictionary.

        Args:
            word: Word to look up

        Returns:
            Dictionary entry or None if not found
        """
        if not self._enhanced_browser:
            # Fallback placeholder if enhanced browser not available
            return {
                "word": word,
                "definition": f"Definition for {word}",
                "etymology": "Pali",
                "examples": [],
                "source": "Placeholder",
            }

        try:
            # Use enhanced browser for dictionary lookup
            entry = self._enhanced_browser.enhanced_dictionary_lookup(word)

            if entry and "error" not in entry:
                # Handle StarDict format (has 'entries' list)
                if "entries" in entry and entry.get("entries"):
                    # Get the first entry as primary
                    primary_entry = entry.get("entries", [{}])[0]

                    # Extract definition from StarDict format
                    definition = primary_entry.get("definition", "")
                    source = primary_entry.get(
                        "source", primary_entry.get("dictionary", "StarDict")
                    )

                    # Try to extract etymology from definition (simple heuristic)
                    etymology = "Pali"
                    if "Sanskrit" in definition:
                        etymology = "Pali (from Sanskrit)"
                    elif "Pāli" in definition:
                        etymology = "Pāli"

                    return {
                        "word": entry.get("word", word),
                        "definition": definition,
                        "etymology": etymology,
                        "examples": [],  # StarDict doesn't have separate examples
                        "source": source,
                        "page": None,  # StarDict doesn't have page numbers
                        "sub_entries": [],  # StarDict doesn't have sub-entries in this format
                        "variants": [],  # StarDict doesn't have variants in this format
                        "cache_hit": entry.get("cache_hit", False),
                        "total_entries": entry.get("total_entries", 1),
                        "dictionaries_searched": entry.get("dictionaries_searched", []),
                    }
                else:
                    # Handle old database dictionary format
                    return {
                        "word": entry.get("word", word),
                        "definition": entry.get("definition", ""),
                        "etymology": entry.get("etymology", "Pali"),
                        "examples": entry.get("examples", []),
                        "source": entry.get("source", "Enhanced Dictionary"),
                        "page": entry.get("page"),
                        "sub_entries": entry.get("sub_entries", []),
                        "variants": entry.get("variants", []),
                        "cache_hit": entry.get("cache_hit", False),
                    }

            # Fallback if not found
            return {
                "word": word,
                "definition": f"Word '{word}' not found in dictionary",
                "etymology": "Pali",
                "examples": [],
                "source": "Not found",
            }
        except Exception as e:
            print(f"Error looking up dictionary entry: {e}")
            return {
                "word": word,
                "definition": f"Error looking up word: {e}",
                "etymology": "Pali",
                "examples": [],
                "source": "Error",
            }

    def add_bookmark(self, text_id: str, position: int, note: str = "") -> bool:
        """
        Add a bookmark.

        Args:
            text_id: Text identifier (PTS citation)
            position: Position in text
            note: Optional note

        Returns:
            True if successful
        """
        try:
            bookmark = {
                "text_id": text_id,
                "position": position,
                "note": note,
                "timestamp": datetime.now().isoformat(),
            }
            self.bookmarks.append(bookmark)
            return True
        except Exception as e:
            print(f"Error adding bookmark: {e}")
            return False

    def get_apparatus_for_page(
        self, book_no: int, page_num: int
    ) -> List[Dict[str, Any]]:
        """
        Get apparatus criticus for a specific page.

        Args:
            book_no: Book number
            page_num: Page number

        Returns:
            List of apparatus entries with variant readings
        """
        if not self._enhanced_browser:
            return []

        try:
            # Get raw apparatus entries from enhanced browser
            entries = self._enhanced_browser.get_apparatus_for_page(
                book_no, page_num, format_type="raw"
            )

            # If entries is a string (e.g. "Apparatus manager not available"), bail out
            if not isinstance(entries, list):
                return []

            # Format entries for API consumption.
            # entries may contain ApparatusEntry dataclasses or plain dicts.
            formatted_entries = []
            for entry in entries:
                if isinstance(entry, dict):
                    formatted_entry = {
                        "location": entry.get("location", ""),
                        "main_text": entry.get("main_text", ""),
                        "variants": entry.get("variants", []),
                        "note": entry.get("note", ""),
                        "variant_type": entry.get("variant_type", "unknown"),
                        "significance": entry.get("significance", "minor"),
                        "manuscripts": entry.get("manuscripts", []),
                    }
                else:
                    # ApparatusEntry dataclass — access fields via getattr
                    entry_variants = getattr(entry, "variants", [])
                    first_variant_type = (
                        entry_variants[0].get("type", "unknown")
                        if entry_variants and isinstance(entry_variants[0], dict)
                        else "unknown"
                    )
                    formatted_entry = {
                        "location": getattr(entry, "location", ""),
                        "main_text": "",
                        "variants": entry_variants,
                        "note": getattr(entry, "note", "") or "",
                        "variant_type": first_variant_type,
                        "significance": getattr(entry, "confidence", "minor"),
                        "manuscripts": [],
                    }
                formatted_entries.append(formatted_entry)

            return formatted_entries
        except Exception as e:
            print(f"Error getting apparatus for page {book_no}:{page_num}: {e}")
            return []

    def get_apparatus_summary(self, book_no: int, page_num: int) -> Dict[str, Any]:
        """
        Get summary of apparatus criticus for a page.

        Args:
            book_no: Book number
            page_num: Page number

        Returns:
            Dictionary with apparatus summary statistics
        """
        if not self._enhanced_browser:
            return {"error": "Enhanced browser not available"}

        try:
            return self._enhanced_browser.get_apparatus_summary(book_no, page_num)
        except Exception as e:
            print(f"Error getting apparatus summary: {e}")
            return {"error": str(e)}

    def get_formatted_apparatus(
        self, book_no: int, page_num: int, format_type: str = "detailed"
    ) -> "str | list":
        """
        Get formatted apparatus criticus text.

        Args:
            book_no: Book number
            page_num: Page number
            format_type: Format type ("detailed", "compact", "minimal")

        Returns:
            Formatted apparatus text
        """
        if not self._enhanced_browser:
            return "Apparatus criticus not available"

        try:
            return self._enhanced_browser.get_apparatus_for_page(
                book_no, page_num, format_type
            )
        except Exception as e:
            print(f"Error getting formatted apparatus: {e}")
            return f"Error: {e}"

    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Save application settings.

        Args:
            settings: Settings dictionary

        Returns:
            True if successful
        """
        try:
            # Ensure default settings are included
            default_settings = {
                "language": "en",
                "font_size": 12,
                "default_edition": "PTS",
                "search_mode": "text",
                "fuzzy_threshold": 0.7,
                "show_line_numbers": True,
                "show_apparatus": True,
                "word_wrap": True,
                "show_thai_script": False,
                "dictionary_sources": ["PTS", "CPD"],
                "max_search_results": 50,
                "cache_enabled": True,
            }

            # Merge with defaults (user settings override defaults)
            merged_settings = {**default_settings, **settings}

            # Save to enhanced browser
            if self._enhanced_browser:
                enhanced_success = self._enhanced_browser.save_settings(merged_settings)
                if not enhanced_success:
                    print("Warning: Enhanced browser failed to save settings")

            # Also save to local file for compatibility
            settings_file = self.data_dir / "settings.json"
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(merged_settings, f, indent=2)

            if QT_AVAILABLE:
                self.settingsChanged.emit(merged_settings)

            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def load_settings(self) -> Dict[str, Any]:
        """
        Load application settings.

        Returns:
            Settings dictionary
        """
        # Try to load from enhanced browser first
        if self._enhanced_browser:
            enhanced_settings = self._enhanced_browser.load_settings()
            if enhanced_settings:
                return enhanced_settings

        # Fallback to local file
        settings_file = self.data_dir / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")

        # Default settings
        return {
            "language": "en",
            "font_size": 12,
            "theme": "light",
            "default_edition": "PTS",
            "show_line_numbers": True,
            "auto_save_bookmarks": True,
            "search_mode": "text",
            "fuzzy_threshold": 0.7,
            "show_apparatus": True,
            "show_thai_script": False,
            "dictionary_sources": ["PTS", "CPD"],
            "max_search_results": 50,
            "cache_enabled": True,
        }


def main():
    """Main entry point for the application."""
    print("Tipitaka PTS Browser - Enhanced Edition")
    print("========================================")
    print(f"Version: {__version__}")
    print("Features: ROTA edition, advanced search, apparatus criticus")
    print()

    # Create application instance
    app = TipitakaBrowser()

    # Check if we can run with GUI
    if QT_AVAILABLE and QApplication.instance() is None:
        run_gui(app)
    else:
        run_cli(app)


def run_gui(app: TipitakaBrowser) -> None:
    """Run the application with GUI."""
    import sys

    from PyQt6.QtWidgets import QApplication

    from .extracted_appimage_gui import ExtractedAppImageWindow

    qt_app = QApplication.instance()
    if qt_app is None:
        qt_app = QApplication(sys.argv)

    qt_app.setApplicationName("Tipitaka PTS Browser")
    qt_app.setApplicationVersion(__version__)

    project_root = Path(__file__).resolve().parents[2]
    window = ExtractedAppImageWindow(project_root)
    window.show()
    sys.exit(qt_app.exec())


def run_cli(app: TipitakaBrowser) -> None:
    """Run the application in command-line mode."""
    print("Running in command-line mode")
    print("Available commands: search, get, editions, dict, apparatus, stats, exit")

    while True:
        try:
            command = input("\n> ").strip().lower()

            if command == "exit":
                print("Goodbye!")
                break

            elif command == "search":
                query = input("Search query: ").strip()
                if query:
                    # Ask for search mode
                    print("Search modes: text, word, fuzzy, exact")
                    mode = input("Search mode (default: text): ").strip().lower()
                    if not mode:
                        mode = "text"

                    if mode not in ["text", "word", "fuzzy", "exact"]:
                        print("Invalid mode. Using 'text'.")
                        mode = "text"

                    results = app._enhanced_browser.enhanced_search(query, mode=mode)
                    if results:
                        print(f"Found {len(results)} results (mode: {mode}):")
                        for i, result in enumerate(results[:5], 1):
                            title = result.get(
                                "book_name", f"Book {result.get('book_no', 0)}"
                            )
                            word = result.get("matched_word", query)
                            score = result.get("score", 0.0)
                            print(f"{i}. {title} - '{word}' (score: {score:.2f})")
                            print(
                                f"   Page: {result.get('book_no', 0)}:{result.get('page_num', 0)}"
                            )
                            context = result.get("context", "")
                            print(
                                f"   {context[:100]}..."
                                if len(context) > 100
                                else f"   {context}"
                            )
                            if result.get("apparatus_count", 0) > 0:
                                apparatus_count = result.get("apparatus_count", 0)
                                print(f"   Apparatus: {apparatus_count} variants")
                    else:
                        print("No results found.")

            elif command == "get":
                text_id = input("PTS citation (e.g., 'M I 3' or 'Sn 25'): ").strip()
                if text_id:
                    # Parse citation
                    parsed = app._enhanced_browser.parse_citation(text_id)
                    if parsed:
                        book_no = parsed.get("book_no", "Unknown")
                        page_num = parsed.get("page_num", "Unknown")
                        print(f"Parsed citation: Book {book_no}, Page {page_num}")

                    text_result = app.get_text(text_id, include_thai=True)
                    if text_result and text_result.get("text"):
                        text = text_result["text"]
                        print("\nText content (first 500 chars):")
                        print(text[:500] + ("..." if len(text) > 500 else ""))

                        # Show Thai script if available
                        if text_result.get("thai_text"):
                            print("\nThai script available (first 200 chars):")
                            print(
                                text_result["thai_text"][:200]
                                + ("..." if len(text_result["thai_text"]) > 200 else "")
                            )

                        # Show apparatus if available
                        if parsed and app._enhanced_browser:
                            book_no_ap = parsed.get("book_no")
                            # parse_and_resolve returns key "page", not "page_num"
                            page_ap = parsed.get("page") or parsed.get("page_num")
                            if book_no_ap and page_ap:
                                apparatus = (
                                    app._enhanced_browser.get_apparatus_for_page(
                                        int(book_no_ap), int(page_ap)
                                    )
                                )
                                if (
                                    apparatus
                                    and isinstance(apparatus, str)
                                    and "not available" not in apparatus
                                ):
                                    print(f"\nApparatus criticus (excerpt):")
                                    print(
                                        apparatus[:400]
                                        + ("..." if len(apparatus) > 400 else "")
                                    )
                                elif apparatus and isinstance(apparatus, list):
                                    print(
                                        f"\nApparatus criticus ({len(apparatus)} entries found)"
                                    )
                    else:
                        print(
                            "Text not found. Try a valid PTS citation like 'M I 3' or 'Sn 25'"
                        )

            elif command == "editions":
                text_id = input("Text ID (optional): ").strip()
                if text_id:
                    editions = app.get_available_editions(text_id)
                    if editions:
                        print(f"Available editions for {text_id}:")
                        for edition in editions:
                            print(f"  - {edition}")
                    else:
                        print("No edition information available.")
                else:
                    # Show all available editions
                    print("Available editions:")
                    print("  - ROTA (Royal Thai Tipitaka - Romanized Pali)")
                    print("  - PTS (Pali Text Society - Legacy)")

                    # Show ROTA books if available
                    if app._enhanced_browser:
                        rota_books = app._enhanced_browser.get_rota_available_books()
                        if rota_books:
                            print(f"\nROTA edition contains {len(rota_books)} books:")
                            for book in rota_books[:10]:
                                print(
                                    f"  - {book.get('book_name', f'Book {book.get('book_no')}')}"
                                )
                            if len(rota_books) > 10:
                                print(f"  ... and {len(rota_books) - 10} more")

            elif command == "dict":
                word = input("Word to look up: ").strip()
                if word:
                    entry = app.lookup_dictionary(word)
                    if entry:
                        print(f"\n{entry.get('word', word)}:")
                        print(f"  Definition: {entry.get('definition', 'Not found')}")
                        if entry.get("etymology"):
                            print(f"  Etymology: {entry.get('etymology')}")
                        if entry.get("sub_entries"):
                            print(f"  Sub-entries: {len(entry.get('sub_entries'))}")
                        if entry.get("variants"):
                            print(f"  Variants: {len(entry.get('variants'))}")
                        if entry.get("cache_hit"):
                            print("  (from cache)")
                    else:
                        print("Word not found in dictionary.")

            elif command == "help":
                print("Available commands:")
                print("  search   - Search for texts (with mode selection)")
                print("  get      - Get specific text by ID")
                print("  editions - List available editions for a text")
                print("  dict     - Look up word in dictionary")
                print("  apparatus - View apparatus criticus for a page")
                print("  stats    - Show application statistics")
                print("  exit     - Exit the application")

            elif command == "apparatus":
                book_no = input("Book number: ").strip()
                page_num = input("Page number: ").strip()
                if book_no and page_num:
                    if app._enhanced_browser:
                        # get_apparatus_for_page returns a formatted string by default
                        apparatus = app._enhanced_browser.get_apparatus_for_page(
                            int(book_no), int(page_num)
                        )
                        if (
                            apparatus
                            and isinstance(apparatus, str)
                            and "not available" not in apparatus
                        ):
                            print(f"\nApparatus criticus for {book_no}:{page_num}:")
                            print(apparatus)
                        elif apparatus and isinstance(apparatus, list):
                            print(
                                f"\nApparatus criticus for {book_no}:{page_num} ({len(apparatus)} entries):"
                            )
                            for i, entry in enumerate(apparatus, 1):
                                loc = getattr(
                                    entry,
                                    "location",
                                    entry.get("location", "?")
                                    if isinstance(entry, dict)
                                    else "?",
                                )
                                print(f"  {i}. {loc}")
                        else:
                            print("No apparatus found for this page.")
                    else:
                        print("Enhanced browser not available.")
                else:
                    print("Please provide both book and page numbers.")

            elif command == "stats":
                if app._enhanced_browser:
                    status = app._enhanced_browser.get_module_status()
                    print("\nApplication Statistics:")
                    print(f"  Database: {status.get('database', 'Unknown')}")
                    print(f"  ROTA Edition: {status.get('rota_edition', 'Unknown')}")
                    print(f"  Dictionary: {status.get('dictionary', 'Unknown')}")
                    print(
                        f"  Citation Parser: {status.get('citation_parser', 'Unknown')}"
                    )
                    print(f"  Apparatus: {status.get('apparatus', 'Unknown')}")

                    # Cache stats
                    cache_stats = app._enhanced_browser.get_apparatus_cache_stats()
                    if cache_stats:
                        print("\nCache Statistics:")
                        print(
                            f"  Apparatus cache: {cache_stats.get('size', 0)} entries"
                        )
                        hits = cache_stats.get("hits", 0)
                        misses = cache_stats.get("misses", 0)
                        print(f"  Hits: {hits}, Misses: {misses}")

                    # Dictionary cache stats
                    dict_stats = app._enhanced_browser.get_dictionary_cache_stats()
                    if dict_stats:
                        print(
                            f"  Dictionary cache: {dict_stats.get('size', 0)} entries"
                        )
                        hits = dict_stats.get("hits", 0)
                        misses = dict_stats.get("misses", 0)
                        print(f"  Hits: {hits}, Misses: {misses}")
                else:
                    print("Enhanced browser not available.")

            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands.")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'exit' to quit.")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
