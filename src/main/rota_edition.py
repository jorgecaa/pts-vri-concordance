"""
ROTA Edition Module for Tipitaka PTS Browser.

This module provides specialized handling for the ROTA (Royal Thai) edition
of the Tipitaka, which is the primary edition stored in the database.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union


class ROTAEdition(Enum):
    """ROTA edition identifiers."""

    ROTA = "ROTA"  # Royal Thai Tipitaka (Syāmaraṭṭha-Tipiṭaka)
    ROTA_ROMAN = "ROTA_ROMAN"  # Romanized version
    ROTA_THAI = "ROTA_THAI"  # Thai script version (in ENCPALI)


@dataclass
class ROTAPage:
    """Represents a page from the ROTA edition."""

    book_no: int
    page_num: int
    book_key: str  # Original BOOK field (offset-encoded)
    page_key: str  # Original PAGE field (offset-encoded)
    head: str  # Page header/title
    unitext: str  # Decoded UNITEXT (Romanized Pali)
    encpali: Optional[str] = None  # Decoded ENCPALI (Thai script if available)
    footnotes: Optional[str] = None  # Apparatus criticus if available
    metadata: Optional[Dict[str, Any]] = None


class ROTADecoder:
    """Decoder for ROTA edition text fields."""

    @staticmethod
    def decode_unitext(encoded_text: Optional[str]) -> str:
        """Text already decoded in clean database."""
        return encoded_text or ""

    @staticmethod
    def decode_encpali(encoded_text: Optional[str]) -> str:
        """Text already decoded in clean database."""
        return encoded_text or ""

    @staticmethod
    def is_thai_script(text: str) -> bool:
        """
        Check if text contains Thai script characters.

        Args:
            text: Text to check

        Returns:
            True if text contains Thai characters
        """
        # Thai Unicode range: U+0E00 to U+0E7F
        thai_pattern = re.compile(r"[\u0e00-\u0e7f]")
        return bool(thai_pattern.search(text))

    @staticmethod
    def is_pua_encoding(text: str) -> bool:
        """
        Check if text contains PUA (Private Use Area) characters.

        Args:
            text: Text to check

        Returns:
            True if text contains PUA characters
        """
        # PUA ranges: U+E000-U+F8FF, U+F0000-U+FFFFD, U+100000-U+10FFFD
        pua_pattern = re.compile(
            r"[\ue000-\uf8ff\U000f0000-\U000ffffd\U00100000-\U0010fffd]"
        )
        return bool(pua_pattern.search(text))


class ROTAManager:
    """Manager for ROTA edition operations."""

    def __init__(self, database_connection):
        """
        Initialize ROTA manager.

        Args:
            database_connection: SQLite database connection
        """
        self.conn = database_connection
        self.decoder = ROTADecoder()
        self._cache = {}
        self._book_cache = {}

    def get_page(self, book_no: int, page_num: int) -> Optional[ROTAPage]:
        """
        Get a page from the ROTA edition.

        Args:
            book_no: Book number (book_no)
            page_num: Page number (page_no)

        Returns:
            ROTAPage object or None if not found
        """
        cache_key = f"{book_no}:{page_num}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        if not self.conn:
            return None

        try:
            cursor = self.conn.cursor()

            cursor.execute(
                """
                SELECT book_key, page_key, head, unitext, encpali
                FROM pages
                WHERE book_no = ? AND page_no = ?
                """,
                (book_no, page_num),
            )

            row = cursor.fetchone()
            if not row:
                return None

            # Decode text fields
            unitext = self.decoder.decode_unitext(row["unitext"])
            encpali = self.decoder.decode_encpali(row["encpali"])

            # Get apparatus criticus if available
            footnotes = self._get_apparatus(row["book_key"], row["page_key"])

            # Create page object
            page = ROTAPage(
                book_no=book_no,
                page_num=page_num,
                book_key=row["book_key"],
                page_key=row["page_key"],
                head=row["head"] or "",
                unitext=unitext,
                encpali=encpali if encpali else None,
                footnotes=footnotes,
                metadata={
                    "has_thai_script": self.decoder.is_thai_script(encpali)
                    if encpali
                    else False,
                    "has_pua_encoding": self.decoder.is_pua_encoding(encpali)
                    if encpali
                    else False,
                    "unitext_length": len(unitext),
                    "encpali_length": len(encpali) if encpali else 0,
                },
            )

            # Cache the result
            self._cache[cache_key] = page

            return page

        except Exception as e:
            print(f"Error getting ROTA page {book_no}:{page_num}: {e}")
            return None

    def _get_apparatus(self, book_key: str, page_key: str) -> Optional[str]:
        """Get apparatus criticus for a page."""
        try:
            cursor = self.conn.cursor()

            cursor.execute(
                """
                SELECT unitext
                FROM footnotes
                WHERE BOOK = ? AND PAGE = ?
                """,
                (book_key, page_key),
            )

            row = cursor.fetchone()
            if row and row["unitext"]:
                return self.decoder.decode_unitext(row["unitext"])

            return None

        except Exception as e:
            print(f"Error getting apparatus: {e}")
            return None

    def get_book_info(self, book_no: int) -> Optional[Dict[str, Any]]:
        """
        Get information about a book in the ROTA edition.

        Args:
            book_no: Book number

        Returns:
            Dictionary with book information
        """
        if book_no in self._book_cache:
            return self._book_cache[book_no]

        if not self.conn:
            return None

        try:
            cursor = self.conn.cursor()

            # Get book metadata
            cursor.execute(
                """
                SELECT book_no, s_name, book_name, edition
                FROM books
                WHERE book_no = ?
                """,
                (book_no,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            # Get page count for this book
            cursor.execute(
                """
                SELECT COUNT(*) as page_count,
                       MIN(page_no) as first_page,
                       MAX(page_no) as last_page
                FROM pages
                WHERE book_no = ?
                """,
                (book_no,),
            )

            count_row = cursor.fetchone()

            book_info = {
                "book_no": book_no,
                "name": row["s_name"] or f"Book {book_no}",
                "abbreviation": row["book_name"] or "",
                "volume": 0,  # Not available in current schema
                "edition": "mula",
                "page_count": count_row["page_count"] if count_row else 0,
                "first_page": count_row["first_page"] if count_row else 1,
                "last_page": count_row["last_page"] if count_row else 1,
                "is_rota_edition": True,
            }

            self._book_cache[book_no] = book_info
            return book_info

        except Exception as e:
            print(f"Error getting book info for {book_no}: {e}")
            return None

    def search_in_text(
        self, query: str, book_no: Optional[int] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for text in ROTA edition.

        Args:
            query: Search query
            book_no: Optional book number to restrict search
            limit: Maximum number of results

        Returns:
            List of search results
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            # Build query
            sql = """
                SELECT p.book_no, p.page_no, p.HEAD, p.unitext, p.book_key, p.page_key
                FROM pages p
            """
            params = []

            if book_no is not None:
                sql += " AND p.book_no = ?"
                params.append(book_no)

            sql += " ORDER BY p.book_no, p.page_no LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                unitext = self.decoder.decode_unitext(row["unitext"])

                # Simple case-insensitive search
                if query.lower() in unitext.lower():
                    # Extract context around match
                    context = self._extract_context(unitext, query)

                    results.append(
                        {
                            "book_no": row["book_no"],
                            "page_num": row["page_no"],
                            "page_title": row["head"]
                            or f"Book {row['book_no']}, Page {row['page_no']}",
                            "context": context,
                            "book_key": row["book_key"],
                            "page_key": row["page_key"],
                            "match_count": unitext.lower().count(query.lower()),
                        }
                    )

            return results

        except Exception as e:
            print(f"Error searching ROTA text: {e}")
            return []

    def _extract_context(self, text: str, query: str, context_chars: int = 100) -> str:
        """Extract context around search match."""
        query_lower = query.lower()
        text_lower = text.lower()

        pos = text_lower.find(query_lower)
        if pos == -1:
            return text[:context_chars] + "..." if len(text) > context_chars else text

        start = max(0, pos - context_chars)
        end = min(len(text), pos + len(query) + context_chars)

        context = text[start:end]

        # Highlight the match
        match_start = pos - start
        match_end = match_start + len(query)

        if 0 <= match_start < len(context) and match_end <= len(context):
            highlighted = (
                context[:match_start]
                + "**"
                + context[match_start:match_end]
                + "**"
                + context[match_end:]
            )
            return highlighted

        return context

    def get_page_range(self, book_no: int) -> Tuple[int, int]:
        """
        Get page range for a book.

        Args:
            book_no: Book number

        Returns:
            Tuple of (first_page, last_page)
        """
        if not self.conn:
            return (1, 1)

        try:
            cursor = self.conn.cursor()

            cursor.execute(
                """
                SELECT MIN(page_no) as first_page, MAX(page_no) as last_page
                FROM pages
                WHERE book_no = ?
                """,
                (book_no,),
            )

            row = cursor.fetchone()
            if row and row["first_page"] is not None and row["last_page"] is not None:
                return (row["first_page"], row["last_page"])

            return (1, 1)

        except Exception as e:
            print(f"Error getting page range for book {book_no}: {e}")
            return (1, 1)

    def get_available_books(self) -> List[Dict[str, Any]]:
        """Get list of all available books in ROTA edition."""
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            cursor.execute(
                """
                SELECT DISTINCT p.book_no, b.s_name, b.book_name
                FROM pages p
                LEFT JOIN books b ON p.book_no = b.book_no
                ORDER BY p.book_no
                """
            )

            rows = cursor.fetchall()
            books = []

            for row in rows:
                book_no = row["book_no"]
                book_info = self.get_book_info(book_no)

                if book_info:
                    books.append(book_info)

            return books

        except Exception as e:
            print(f"Error getting available books: {e}")
            return []

    def clear_cache(self):
        """Clear all caches."""
        self._cache.clear()
        self._book_cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "page_cache_size": len(self._cache),
            "book_cache_size": len(self._book_cache),
            "cached_pages": list(self._cache.keys())[:10],  # First 10
            "cached_books": list(self._book_cache.keys()),
        }


# Utility functions
def create_rota_manager(database_path: str) -> Optional[ROTAManager]:
    """
    Create a ROTA manager instance.

    Args:
        database_path: Path to SQLite database

    Returns:
        ROTAManager instance or None if failed
    """
    try:
        import sqlite3

        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        return ROTAManager(conn)
    except Exception as e:
        print(f"Error creating ROTA manager: {e}")
        return None


def decode_rota_text(encoded_text: str) -> str:
    """
    Convenience function to decode ROTA text.

    Args:
        encoded_text: Base64 encoded text from UNITEXT

    Returns:
        Decoded text
    """
    decoder = ROTADecoder()
    return decoder.decode_unitext(encoded_text)


if __name__ == "__main__":
    # Test the module
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from config import get_config

    config = get_config()
    data_dir = config.get("paths.data_dir", "data")
    db_path = os.path.join(data_dir, "tipitaka.sqlite")

    if os.path.exists(db_path):
        print("Testing ROTA Edition Module")
        print("=" * 50)

        manager = create_rota_manager(db_path)
        if manager:
            # Test getting a page
            print("\n1. Testing page retrieval (Book 1, Page 1):")
            page = manager.get_page(1, 1)
            if page:
                print(f"   Found page: {page.head[:50]}...")
                print(f"   Text length: {len(page.unitext)} characters")
                print(f"   Has Thai script: {page.metadata['has_thai_script']}")
                print(f"   Has PUA encoding: {page.metadata['has_pua_encoding']}")

            # Test book info
            print("\n2. Testing book info (Book 1):")
            book_info = manager.get_book_info(1)
            if book_info:
                print(f"   Book name: {book_info['name']}")
                print(f"   Abbreviation: {book_info['abbreviation']}")
                print(f"   Pages: {book_info['page_count']}")
                print(
                    f"   Page range: {book_info['first_page']}-{book_info['last_page']}"
                )

            # Test search
            print("\n3. Testing search in ROTA text:")
            search_results = manager.search_in_text("dhamma", limit=3)
            print(f"   Found {len(search_results)} results for 'dhamma'")
            for i, result in enumerate(search_results[:2]):
                print(
                    f"   {i + 1}. Book {result['book_no']}, Page {result['page_num']}"
                )
                print(f"      Context: {result['context'][:100]}...")

            # Test page range
            print("\n4. Testing page range (Book 1):")
            first, last = manager.get_page_range(1)
            print(f"   Page range: {first} - {last}")

            # Test available books
            print("\n5. Testing available books:")
            books = manager.get_available_books()
            print(f"   Total books available: {len(books)}")
            for i, book in enumerate(books[:3]):
                print(f"   {i + 1}. Book {book['book_no']}: {book['name']}")

            # Test cache stats
            print("\n6. Testing cache statistics:")
            cache_stats = manager.get_cache_stats()
            print(f"   Page cache size: {cache_stats['page_cache_size']}")
            print(f"   Book cache size: {cache_stats['book_cache_size']}")

            print("\nROTA Edition Module test complete!")
    else:
        print(f"Database not found at: {db_path}")
        print("Please ensure the database exists and try again.")
