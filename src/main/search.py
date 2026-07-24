"""
Search module for Tipitaka PTS Browser with improved word index decoding.

This module provides enhanced search functionality that properly handles
the word index encoding in the database.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from rapidfuzz import fuzz, process


def decode_word_key(key_char: str) -> int:
    """Decode a word key from the offset encoding used in wordsat.

    The original VFP9 system stored multi-byte integers as printable-ASCII
    strings by adding 0x24 (decimal 36) to each byte of a 2- or 3-byte
    big-endian integer.

    Args:
        key_char: String containing 2-3 characters of offset-encoded data

    Returns:
        Decoded integer value
    """
    if not key_char:
        return 0

    result = 0
    for ch in key_char:
        result = result * 256 + (ord(ch) - 0x24)
    return result


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

    try:
        # Base64 decode with padding
        return val or ""  # text already decoded in clean database

        # Check for BOM marker
        if raw[:3] != b"\xef\xbb\xbf":
            # No BOM, return original
            return val

        # Strip BOM and decode as UTF-8
        return raw[3:].decode("utf-8", errors="replace")
    except Exception:
        # Not Base64 encoded, return as-is
        return val


class WordIndexSearcher:
    """Enhanced search using the word index with proper decoding."""

    def __init__(self, database_connection):
        """
        Initialize the searcher with a database connection.

        Args:
            database_connection: SQLite database connection
        """
        self.conn = database_connection
        self._word_cache = {}  # Cache for decoded word mappings

    def _get_word_from_key(self, word_key: str) -> Optional[str]:
        """
        Get the actual word text from a word key.

        Args:
            word_key: 3-character offset-encoded word key

        Returns:
            Word text or None if not found
        """
        if word_key in self._word_cache:
            return self._word_cache[word_key]

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT STR1, STR1M
                FROM word_list
                WHERE SKID = ? 
                """,
                (word_key,),
            )

            row = cursor.fetchone()
            if row:
                # Try to decode STR1 (may contain PUA characters)
                word_str = row["STR1"]
                # For now, return as-is - may need additional decoding
                self._word_cache[word_key] = word_str
                return word_str

        except Exception as e:
            print(f"Error getting word from key {word_key}: {e}")

        return None

    def search_by_word(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for occurrences of a specific word using the word index.

        This is more efficient than full-text search for exact word matches.

        Args:
            query: Word to search for
            limit: Maximum number of results

        Returns:
            List of search results with location information
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            # First, find the word key(s) that match the query
            # We need to search in words for matching words
            cursor.execute(
                """
                SELECT SKID, STR1, STR1M, NFOUND
                FROM word_list
                WHERE (STR1 LIKE ? OR STR1M LIKE ?)
                  
                ORDER BY LENGTH(STR1) ASC
                LIMIT 10
                """,
                (f"%{query}%", f"%{query}%"),
            )

            word_rows = cursor.fetchall()
            if not word_rows:
                return []

            results = []

            for word_row in word_rows:
                word_key = word_row["SKID"]
                word_str = word_row["STR1"]
                word_str_m = word_row["STR1M"]

                # Get occurrences from word_occurrences table
                cursor.execute(
                    """
                    SELECT BOOK, PAGE, LINE, WORDLEN, ATCOL, ISCROSS, FOOTPOST
                    FROM wordsat
                    WHERE WORD = ? 
                    ORDER BY BOOK, PAGE, LINE, ATCOL
                    LIMIT ?
                    """,
                    (word_key, limit),
                )

                occurrences = cursor.fetchall()

                for occ in occurrences:
                    # Decode location information
                    book_no = decode_word_key(occ["book_key"])
                    page_num = decode_word_key(occ["page_key"])
                    line_num = decode_word_key(occ["LINE"])
                    word_len = decode_word_key(occ["WORDLEN"])
                    col_pos = decode_word_key(occ["ATCOL"])

                    # Get the page text for context
                    cursor.execute(
                        """
                        SELECT unitext, HEAD, book_no, page_no
                        FROM pages
                        WHERE book_no = ? AND page_no = ? 
                        """,
                        (book_no, page_num),
                    )

                    page_row = cursor.fetchone()
                    if page_row:
                        page_text = decode_text_value(page_row["unitext"])

                        # Extract context around the word
                        context = self._extract_context(
                            page_text, line_num, col_pos, word_len
                        )

                        results.append(
                            {
                                "word": word_str,
                                "word_normalized": word_str_m,
                                "book_no": book_no,
                                "page_num": page_num,
                                "line_num": line_num,
                                "col_pos": col_pos,
                                "word_len": word_len,
                                "is_cross_ref": occ["ISCROSS"] == "L",
                                "in_footnote": bool(occ["FOOTPOST"]),
                                "context": context,
                                "page_title": page_row["head"],
                                "occurrence_count": decode_word_key(word_row["NFOUND"])
                                if word_row["NFOUND"]
                                else 0,
                            }
                        )

            return results

        except Exception as e:
            print(f"Error in search_by_word: {e}")
            return []

    def _extract_context(
        self,
        text: str,
        line_num: int,
        col_pos: int,
        word_len: int,
        context_chars: int = 100,
    ) -> str:
        """
        Extract context around a word position in text.

        Args:
            text: Full text
            line_num: Line number (1-based)
            col_pos: Column position (1-based)
            word_len: Word length
            context_chars: Number of characters to include before and after

        Returns:
            Context string with the word highlighted
        """
        # Simple implementation - in reality would need to parse line breaks
        # For now, just extract from the full text

        # Convert to character position (approximate)
        # This is simplified - actual implementation would need to handle line breaks
        start_pos = max(0, col_pos - context_chars)
        end_pos = min(len(text), col_pos + word_len + context_chars)

        context = text[start_pos:end_pos]

        # Highlight the word (simplified)
        word_start = col_pos - start_pos
        word_end = word_start + word_len

        if 0 <= word_start < len(context) and word_end <= len(context):
            highlighted = (
                context[:word_start]
                + "**"
                + context[word_start:word_end]
                + "**"
                + context[word_end:]
            )
            return highlighted

        return context

    def fuzzy_search(
        self, query: str, threshold: float = 0.8, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Perform fuzzy search across words in the dictionary.

        Args:
            query: Search query
            threshold: Minimum similarity threshold (0.0 to 1.0)
            limit: Maximum number of results

        Returns:
            List of similar words with similarity scores
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            # Get all words from dictionary
            cursor.execute(
                """
                SELECT SKID, STR1, STR1M, NFOUND
                FROM word_list
                WHERE 1=1
                LIMIT 10000  # Limit for performance
                """
            )

            all_words = cursor.fetchall()

            # Prepare word list for fuzzy matching
            word_list = []
            for row in all_words:
                word_str = row["STR1"]
                if word_str and len(word_str) > 1:  # Skip very short words
                    word_list.append(
                        (row["SKID"], word_str, row["STR1M"], row["NFOUND"])
                    )

            # Perform fuzzy matching
            matches = process.extract(
                query, [w[1] for w in word_list], scorer=fuzz.ratio, limit=limit
            )

            results = []
            for matched_word, score, index in matches:
                if score >= threshold * 100:  # Convert to percentage
                    word_key, word_str, word_str_m, nfound = word_list[index]

                    # Get occurrence count
                    cursor.execute(
                        """
                        SELECT COUNT(*) as count
                        FROM wordsat
                        WHERE WORD = ? 
                        """,
                        (word_key,),
                    )

                    count_row = cursor.fetchone()
                    occurrence_count = count_row["count"] if count_row else 0

                    results.append(
                        {
                            "word": word_str,
                            "word_normalized": word_str_m,
                            "similarity": score / 100.0,  # Convert to 0.0-1.0
                            "occurrence_count": occurrence_count,
                            "word_key": word_key,
                        }
                    )

            return sorted(results, key=lambda x: x["similarity"], reverse=True)

        except Exception as e:
            print(f"Error in fuzzy_search: {e}")
            return []

    def search_with_context(
        self,
        query: str,
        book_no: Optional[int] = None,
        page_num: Optional[int] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search for query in text with surrounding context.

        Args:
            query: Search query
            book_no: Optional book number to restrict search
            page_num: Optional page number to restrict search
            limit: Maximum number of results

        Returns:
            List of search results with context
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            # Build query based on parameters
            sql = """
                SELECT p.book_no, p.page_no, p.unitext, p.HEAD,
                       p.book_key, p.page_key, p.SKID
                FROM pages p
            """
            params = []

            if book_no is not None:
                sql += " AND p.book_no = ?"
                params.append(book_no)

            if page_num is not None:
                sql += " AND p.page_no = ?"
                params.append(page_num)

            sql += " ORDER BY p.book_no, p.page_no LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            pages = cursor.fetchall()

            results = []
            for page in pages:
                text = decode_text_value(page["unitext"])

                # Simple text search for the query
                if query.lower() in text.lower():
                    # Find all occurrences
                    occurrences = []
                    start = 0
                    while True:
                        pos = text.lower().find(query.lower(), start)
                        if pos == -1:
                            break

                        # Extract context around match
                        context_start = max(0, pos - 50)
                        context_end = min(len(text), pos + len(query) + 50)
                        context = text[context_start:context_end]

                        # Highlight the match
                        match_start = pos - context_start
                        match_end = match_start + len(query)
                        highlighted = (
                            context[:match_start]
                            + "**"
                            + context[match_start:match_end]
                            + "**"
                            + context[match_end:]
                        )

                        occurrences.append({"position": pos, "context": highlighted})

                        start = pos + 1

                    if occurrences:
                        results.append(
                            {
                                "book_no": page["book_no"],
                                "page_num": page["page_no"],
                                "page_title": page["head"],
                                "occurrences": occurrences,
                                "total_matches": len(occurrences),
                                "book_key": page["book_key"],
                                "page_key": page["page_key"],
                                "page_id": page["SKID"],
                            }
                        )

            return results

        except Exception as e:
            print(f"Error in search_with_context: {e}")
            return []


class AdvancedSearch:
    """Advanced search functionality with multiple search modes."""

    def __init__(self, database_connection):
        """
        Initialize advanced search.

        Args:
            database_connection: SQLite database connection
        """
        self.conn = database_connection
        self.word_searcher = WordIndexSearcher(database_connection)

    def search(self, query: str, mode: str = "text", **kwargs) -> List[Dict[str, Any]]:
        """
        Perform search with specified mode.

        Args:
            query: Search query
            mode: Search mode - "text", "word", "fuzzy", or "exact"
            **kwargs: Additional parameters for specific search modes

        Returns:
            List of search results
        """
        if mode == "word":
            return self.word_searcher.search_by_word(query, **kwargs)
        elif mode == "fuzzy":
            threshold = kwargs.get("threshold", 0.8)
            return self.word_searcher.fuzzy_search(query, threshold, **kwargs)
        elif mode == "exact":
            # Exact word match using word index
            return self._exact_word_search(query, **kwargs)
        else:  # "text" mode (default)
            return self.word_searcher.search_with_context(query, **kwargs)

    def _exact_word_search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for exact word matches using word index.

        Args:
            query: Exact word to search for
            limit: Maximum number of results

        Returns:
            List of exact matches
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            # Find exact word match
            cursor.execute(
                """
                SELECT SKID, STR1, STR1M, NFOUND
                FROM word_list
                WHERE STR1 = ? 
                """,
                (query,),
            )

            word_row = cursor.fetchone()
            if not word_row:
                return []

            word_key = word_row["SKID"]

            # Get all occurrences
            cursor.execute(
                """
                SELECT wa.book_key, wa.page_key, wa.LINE, wa.WORDLEN, wa.ATCOL,
                       p.HEAD, p.book_no, p.page_no
                FROM wordsat wa
                LEFT JOIN pages p ON
                    wa.book_key = p.book_key AND wa.page_key = p.page_key 
                WHERE wa.WORD = ? 
                ORDER BY wa.book_key, wa.page_key, wa.LINE, wa.ATCOL
                LIMIT ?
                """,
                (word_key, limit),
            )

            occurrences = cursor.fetchall()

            results = []
            for occ in occurrences:
                book_no = (
                    occ["book_no"] if occ.get("book_no") else decode_word_key(occ["book_key"])
                )
                page_num = (
                    occ["page_no"] if occ["page_no"] else decode_word_key(occ["page_key"])
                )

                results.append(
                    {
                        "word": query,
                        "book_no": book_no,
                        "page_num": page_num,
                        "line_num": decode_word_key(occ["LINE"]),
                        "col_pos": decode_word_key(occ["ATCOL"]),
                        "word_len": decode_word_key(occ["WORDLEN"]),
                        "page_title": occ["head"] or f"Book {book_no}, Page {page_num}",
                        "exact_match": True,
                    }
                )

            return results

        except Exception as e:
            print(f"Error in exact_word_search: {e}")
            return []

    def search_by_book(
        self, query: str, book_no: int, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search within a specific book.

        Args:
            query: Search query
            book_no: Book number to search within
            limit: Maximum number of results

        Returns:
            List of search results within the specified book
        """
        return self.word_searcher.search_with_context(
            query, book_no=book_no, limit=limit
        )

    def get_word_statistics(self, word: str) -> Dict[str, Any]:
        """
        Get statistics for a word.

        Args:
            word: Word to get statistics for

        Returns:
            Dictionary with word statistics
        """
        if not self.conn:
            return {}

        try:
            cursor = self.conn.cursor()

            # Find the word
            cursor.execute(
                """
                SELECT SKID, STR1, STR1M, NFOUND, NFOOTFOUND
                FROM word_list
                WHERE STR1 = ? 
                """,
                (word,),
            )

            word_row = cursor.fetchone()
            if not word_row:
                return {"word": word, "found": False}

            word_key = word_row["SKID"]

            # Get total occurrences from word_occurrences table
            cursor.execute(
                """
                SELECT COUNT(*) as total_count
                FROM wordsat
                WHERE WORD = ? 
                """,
                (word_key,),
            )

            total_count_row = cursor.fetchone()
            total_count = total_count_row["total_count"] if total_count_row else 0

            # Get occurrences by book
            cursor.execute(
                """
                SELECT wa.BOOK, COUNT(*) as book_count,
                       b.book_no, b.s_name
                FROM wordsat wa
                LEFT JOIN books b ON
                    wa.book_key = b.book_key 
                WHERE wa.WORD = ? 
                GROUP BY wa.BOOK
                ORDER BY book_count DESC
                """,
                (word_key,),
            )

            book_counts = cursor.fetchall()
            books = []
            for bc in book_counts:
                books.append(
                    {
                        "book_no": bc["book_no"]
                        if bc["book_no"]
                        else decode_word_key(bc["book_key"]),
                        "book_name": bc["s_name"]
                        or f"Book {decode_word_key(bc['BOOK'])}",
                        "count": bc["book_count"],
                    }
                )

            # Get occurrences in footnotes
            cursor.execute(
                """
                SELECT COUNT(*) as footnote_count
                FROM wordsat
                WHERE WORD = ? AND FOOTPOST != '' 
                """,
                (word_key,),
            )

            footnote_row = cursor.fetchone()
            footnote_count = footnote_row["footnote_count"] if footnote_row else 0

            # Get cross-reference occurrences
            cursor.execute(
                """
                SELECT COUNT(*) as crossref_count
                FROM wordsat
                WHERE WORD = ? AND ISCROSS = 'L' 
                """,
                (word_key,),
            )

            crossref_row = cursor.fetchone()
            crossref_count = crossref_row["crossref_count"] if crossref_row else 0

            return {
                "word": word,
                "found": True,
                "word_key": word_key,
                "normalized_form": word_row["STR1M"],
                "total_occurrences": total_count,
                "main_text_occurrences": decode_word_key(word_row["NFOUND"])
                if word_row["NFOUND"]
                else 0,
                "footnote_occurrences": decode_word_key(word_row["NFOOTFOUND"])
                if word_row["NFOOTFOUND"]
                else 0,
                "footnote_count": footnote_count,
                "crossref_count": crossref_count,
                "books": books,
            }

        except Exception as e:
            print(f"Error getting word statistics: {e}")
            return {"word": word, "found": False, "error": str(e)}


# Utility functions for integration with existing codebase
def create_search_instance(database_path: str):
    """
    Create a search instance for the given database.

    Args:
        database_path: Path to the SQLite database

    Returns:
        AdvancedSearch instance or None if failed
    """
    try:
        import sqlite3

        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        return AdvancedSearch(conn)
    except Exception as e:
        print(f"Error creating search instance: {e}")
        return None


def search_database(database_path: str, query: str, mode: str = "text", **kwargs):
    """
    Convenience function to search the database.

    Args:
        database_path: Path to the SQLite database
        query: Search query
        mode: Search mode
        **kwargs: Additional search parameters

    Returns:
        List of search results
    """
    searcher = create_search_instance(database_path)
    if searcher:
        return searcher.search(query, mode, **kwargs)
    return []


if __name__ == "__main__":
    # Test the search module
    import os
    import sys

    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from config import get_config

    config = get_config()
    data_dir = config.get("paths.data_dir", "data")
    db_path = os.path.join(data_dir, "tipitaka.sqlite")

    if os.path.exists(db_path):
        print(f"Testing search module with database: {db_path}")

        searcher = create_search_instance(db_path)
        if searcher:
            # Test different search modes
            test_query = "dhamma"

            print(f"\n1. Testing text search for '{test_query}':")
            results = searcher.search(test_query, mode="text", limit=3)
            print(f"   Found {len(results)} results")
            for i, result in enumerate(results[:2]):
                print(f"   {i + 1}. {result.get('page_title', 'Unknown')}")
                print(
                    f"      Book {result.get('book_no')}, Page {result.get('page_num')}"
                )

            print(f"\n2. Testing exact word search for '{test_query}':")
            results = searcher.search(test_query, mode="exact", limit=3)
            print(f"   Found {len(results)} exact matches")
            for i, result in enumerate(results[:2]):
                print(f"   {i + 1}. {result.get('word', 'Unknown')}")
                print(
                    f"      Book {result.get('book_no')}, Page {result.get('page_num')}"
                )

            print(f"\n3. Testing word statistics for '{test_query}':")
            stats = searcher.get_word_statistics(test_query)
            if stats.get("found"):
                print(f"   Total occurrences: {stats.get('total_occurrences')}")
                print(f"   In footnotes: {stats.get('footnote_count')}")
                print(f"   As cross-references: {stats.get('crossref_count')}")
            else:
                print(f"   Word not found")
    else:
        print(f"Database not found at: {db_path}")
        print("Please ensure the database exists and try again.")
