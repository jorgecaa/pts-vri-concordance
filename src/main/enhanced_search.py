"""
Enhanced search module for Tipitaka PTS Browser.

This module provides improved search functionality with:
1. Better book information and titles
2. Context snippets with highlighting
3. Multiple search modes
4. Apparatus criticus integration
"""

import re
import sqlite3
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class BookInfo:
    """Information about a book in the Tipitaka."""

    book_no: int
    title: str
    abbreviation: str
    nikaya: str
    volume: str
    pages: int
    description: str = ""


@dataclass
class SearchResult:
    """Enhanced search result with comprehensive information."""

    word: str
    book_no: int
    page_num: int
    line_num: int
    col_pos: int
    word_len: int
    context_before: str
    context_after: str
    matched_word: str
    frequency: int
    score: float
    book_info: BookInfo
    page_title: str
    is_cross_ref: bool = False
    in_footnote: bool = False
    apparatus_available: bool = False
    search_mode: str = "text"


class EnhancedSearch:
    """Enhanced search functionality with better results."""

    def __init__(self, db_path: str):
        """
        Initialize enhanced search.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self.conn = None
        self._book_cache = {}
        self._connect()

    def _connect(self) -> bool:
        """Connect to database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False

    def _decode_key(self, key: str) -> int:
        """Decode database key to integer."""
        if not key:
            return 0
        try:
            # Remove any non-numeric characters and convert
            return int("".join(filter(str.isdigit, key)))
        except:
            return 0

    def _decode_text(self, encoded_text: str) -> str:
        """Decode Base64 encoded text with BOM."""
        if not encoded_text:
            return ""

        try:
            
            # Remove any whitespace
            encoded_text = encoded_text.strip()

            # Decode Base64
            return encoded_text or ""  # already decoded

            # Check for UTF-8 BOM and remove it
            if decoded_bytes.startswith(b"\xef\xbb\xbf"):
                decoded_bytes = decoded_bytes[3:]

            # Decode as UTF-8
            return decoded_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            print(f"Error decoding text: {e}")
            return encoded_text

    @lru_cache(maxsize=100)
    def get_book_info(self, book_no: int) -> Optional[BookInfo]:
        """
        Get comprehensive book information.

        Args:
            book_no: Book number

        Returns:
            BookInfo object or None if not found
        """
        if book_no in self._book_cache:
            return self._book_cache[book_no]

        if not self.conn:
            return None

        try:
            cursor = self.conn.cursor()

            # Try to get book information from multiple sources
            cursor.execute(
                """
                SELECT
                    b.book_no as book_no,
                    b.book_name as title,
                    b.s_name as abbreviation,
                    b.edition as volume,
                    (b.end_page - b.beg_page + 1) as pages
                FROM books b
                WHERE b.book_no = ? 
                LIMIT 1
            """,
                (book_no,),
            )

            row = cursor.fetchone()
            if row:
                book_info = BookInfo(
                    book_no=row["book_no"],
                    title=row["title"] or f"Book {book_no}",
                    abbreviation=row["abbreviation"] or "",
                    nikaya="",  # Not available in this table
                    volume=row["volume"] or "",
                    pages=row["pages"] or 0,
                    description="",  # Not available in this table
                )
                self._book_cache[book_no] = book_info
                return book_info

            # If not found in books, try to infer from pages
            cursor.execute(
                """
                SELECT DISTINCT HEAD
                FROM pages
                WHERE book_no = ?  AND HEAD IS NOT NULL AND HEAD != ''
                LIMIT 1
            """,
                (book_no,),
            )

            row = cursor.fetchone()
            if row:
                book_info = BookInfo(
                    book_no=book_no,
                    title=row["head"],
                    abbreviation="",
                    nikaya="",
                    volume="",
                    pages=0,
                    description="",
                )
                self._book_cache[book_no] = book_info
                return book_info

            # Default book info
            book_info = BookInfo(
                book_no=book_no,
                title=f"Book {book_no}",
                abbreviation="",
                nikaya="",
                volume="",
                pages=0,
                description="",
            )
            self._book_cache[book_no] = book_info
            return book_info

        except Exception as e:
            print(f"Error getting book info: {e}")
            return None

    def _extract_context_with_highlight(
        self,
        text: str,
        line_num: int,
        col_pos: int,
        word_len: int,
        context_chars: int = 100,
    ) -> Tuple[str, str]:
        """
        Extract context around a word with highlighting markers.

        Args:
            text: Full text
            line_num: Line number (1-based)
            col_pos: Column position (1-based)
            word_len: Word length
            context_chars: Number of characters before/after to include

        Returns:
            Tuple of (context_before, context_after) with highlighting markers
        """
        # Split text into lines
        lines = text.split("\n")
        if line_num < 1 or line_num > len(lines):
            return ("", "")

        # Get the target line
        target_line = lines[line_num - 1]

        # Adjust for 1-based indexing
        col_pos = max(0, col_pos - 1)

        # Ensure word fits in line
        if col_pos + word_len > len(target_line):
            word_len = len(target_line) - col_pos

        # Extract the word
        matched_word = target_line[col_pos : col_pos + word_len]

        # Build context before
        context_before = target_line[max(0, col_pos - context_chars) : col_pos]

        # Build context after
        context_after = target_line[
            col_pos + word_len : col_pos + word_len + context_chars
        ]

        return context_before, context_after, matched_word

    def search_by_word_exact(
        self, query: str, limit: int = 50, include_context: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for exact word matches using word index.

        Args:
            query: Word to search for
            limit: Maximum number of results
            include_context: Whether to include context snippets

        Returns:
            List of enhanced search results
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            # Search for the word in word table
            cursor.execute(
                """
                SELECT SKID, STR1, STR1M, NFOUND
                FROM word_list
                WHERE (STR1 = ? OR STR1M = ?) 
                LIMIT 10
            """,
                (query, query),
            )

            word_rows = cursor.fetchall()
            if not word_rows:
                return []

            results = []

            for word_row in word_rows:
                word_key = word_row["SKID"]
                word_str = word_row["STR1"]
                word_str_m = word_row["STR1M"]
                total_found = (
                    self._decode_key(word_row["NFOUND"]) if word_row["NFOUND"] else 0
                )

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
                    book_no = self._decode_key(occ["book_key"])
                    page_num = self._decode_key(occ["page_key"])
                    line_num = self._decode_key(occ["LINE"])
                    word_len = self._decode_key(occ["WORDLEN"])
                    col_pos = self._decode_key(occ["ATCOL"])

                    # Get book information
                    book_info = self.get_book_info(book_no)

                    # Get page text for context
                    cursor.execute(
                        """
                        SELECT unitext, HEAD
                        FROM pages
                        WHERE book_no = ? AND page_no = ? 
                        LIMIT 1
                    """,
                        (book_no, page_num),
                    )

                    page_row = cursor.fetchone()
                    if not page_row:
                        continue

                    page_text = self._decode_text(page_row["unitext"])
                    page_title = page_row["head"] or ""

                    # Extract context if requested
                    context_before = ""
                    context_after = ""
                    matched_word = word_str

                    if include_context and page_text:
                        context_before, context_after, matched_word = (
                            self._extract_context_with_highlight(
                                page_text, line_num, col_pos, word_len
                            )
                        )

                    # Check if apparatus is available for this page
                    apparatus_available = self._check_apparatus_available(
                        book_no, page_num
                    )

                    # Create search result
                    result = SearchResult(
                        word=word_str,
                        book_no=book_no,
                        page_num=page_num,
                        line_num=line_num,
                        col_pos=col_pos,
                        word_len=word_len,
                        context_before=context_before,
                        context_after=context_after,
                        matched_word=matched_word,
                        frequency=total_found,
                        score=1.0,  # Exact match gets perfect score
                        book_info=book_info,
                        page_title=page_title,
                        is_cross_ref=occ["ISCROSS"] == "L",
                        in_footnote=bool(occ["FOOTPOST"]),
                        apparatus_available=apparatus_available,
                        search_mode="exact",
                    )

                    results.append(result)

            return self._format_results(results)

        except Exception as e:
            print(f"Error in exact word search: {e}")
            return []

    def search_by_text(
        self, query: str, limit: int = 50, fuzzy: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for text in page contents.

        Args:
            query: Text to search for
            limit: Maximum number of results
            fuzzy: Whether to use fuzzy matching

        Returns:
            List of search results
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            if fuzzy:
                # Fuzzy search using LIKE with wildcards
                search_query = f"%{query}%"
                cursor.execute(
                    """
                    SELECT book_no, page_no, unitext, head
                    FROM pages
                    WHERE unitext LIKE ? 
                    ORDER BY book_no, page_no
                    LIMIT ?
                """,
                    (search_query, limit),
                )
            else:
                # Exact phrase search (simplified - for production use FTS)
                search_query = f"%{query}%"
                cursor.execute(
                    """
                    SELECT book_no, page_no, unitext, head
                    FROM pages
                    WHERE unitext LIKE ? 
                    ORDER BY book_no, page_no
                    LIMIT ?
                """,
                    (search_query, limit),
                )

            page_rows = cursor.fetchall()
            results = []

            for row in page_rows:
                book_no = row["book_no"]
                page_num = row["page_no"]
                page_text = self._decode_text(row["unitext"])
                page_title = row["head"] or ""

                # Get book information
                book_info = self.get_book_info(book_no)

                # Find occurrences of query in text
                occurrences = self._find_occurrences_in_text(page_text, query, fuzzy)

                for occ in occurrences[:3]:  # Limit to 3 occurrences per page
                    line_num, col_pos, word_len, matched_word = occ

                    # Extract context
                    context_before, context_after, _ = (
                        self._extract_context_with_highlight(
                            page_text, line_num, col_pos, word_len
                        )
                    )

                    # Check apparatus availability
                    apparatus_available = self._check_apparatus_available(
                        book_no, page_num
                    )

                    # Calculate score
                    score = self._calculate_score(query, matched_word, fuzzy)

                    result = SearchResult(
                        word=query,
                        book_no=book_no,
                        page_num=page_num,
                        line_num=line_num,
                        col_pos=col_pos,
                        word_len=word_len,
                        context_before=context_before,
                        context_after=context_after,
                        matched_word=matched_word,
                        frequency=len(occurrences),
                        score=score,
                        book_info=book_info,
                        page_title=page_title,
                        apparatus_available=apparatus_available,
                        search_mode="fuzzy" if fuzzy else "text",
                    )

                    results.append(result)

            return self._format_results(results)

        except Exception as e:
            print(f"Error in text search: {e}")
            return []

    def _find_occurrences_in_text(
        self, text: str, query: str, fuzzy: bool = False
    ) -> List[Tuple[int, int, int, str]]:
        """
        Find occurrences of query in text.

        Args:
            text: Text to search in
            query: Query to find
            fuzzy: Whether to use fuzzy matching

        Returns:
            List of (line_num, col_pos, word_len, matched_word) tuples
        """
        if not text or not query:
            return []

        occurrences = []
        lines = text.split("\n")

        for line_idx, line in enumerate(lines):
            if fuzzy:
                # Simple fuzzy matching - case insensitive contains
                if query.lower() in line.lower():
                    match_start = line.lower().find(query.lower())
                    occurrences.append(
                        (
                            line_idx + 1,  # line_num (1-based)
                            match_start + 1,  # col_pos (1-based)
                            len(query),  # word_len
                            line[
                                match_start : match_start + len(query)
                            ],  # matched_word
                        )
                    )
            else:
                # Exact matching
                start = 0
                while True:
                    match_start = line.find(query, start)
                    if match_start == -1:
                        break
                    occurrences.append(
                        (line_idx + 1, match_start + 1, len(query), query)
                    )
                    start = match_start + len(query)

        return occurrences

    def _calculate_score(
        self, query: str, matched_word: str, fuzzy: bool = False
    ) -> float:
        """
        Calculate relevance score for a match.

        Args:
            query: Original query
            matched_word: Matched word
            fuzzy: Whether match was fuzzy

        Returns:
            Relevance score (0.0-1.0)
        """
        if not fuzzy:
            return 1.0

        # Simple fuzzy scoring based on character overlap
        query_lower = query.lower()
        matched_lower = matched_word.lower()

        if query_lower == matched_lower:
            return 1.0

        # Calculate Jaccard similarity of character sets
        set1 = set(query_lower)
        set2 = set(matched_lower)

        if not set1 or not set2:
            return 0.0

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def _check_apparatus_available(self, book_no: int, page_num: int) -> bool:
        """
        Check if apparatus criticus is available for a page.

        Args:
            book_no: Book number
            page_num: Page number

        Returns:
            True if apparatus data exists
        """
        if not self.conn:
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM footnotes
                WHERE book_no = ? AND page_no = ? 
            """,
                (book_no, page_num),
            )

            row = cursor.fetchone()
            return row and row["count"] > 0
        except:
            return False

    def _format_results(self, results: List[SearchResult]) -> List[Dict[str, Any]]:
        """
        Format search results for API consumption.

        Args:
            results: List of SearchResult objects

        Returns:
            List of formatted result dictionaries
        """
        formatted = []

        for result in results:
            # Build snippet with highlighting
            snippet = ""
            if result.context_before or result.context_after:
                snippet = f"...{result.context_before}<b>{result.matched_word}</b>{result.context_after}..."

            # Build title with book information
            title_parts = []
            if result.book_info.abbreviation:
                title_parts.append(result.book_info.abbreviation)
            elif result.book_info.title:
                title_parts.append(result.book_info.title)

            if result.page_title:
                title_parts.append(f"p.{result.page_num}: {result.page_title}")
            else:
                title_parts.append(f"Page {result.page_num}")

            title = " - ".join(title_parts)

            # Format the result
            formatted_result = {
                "id": f"{result.book_no}:{result.page_num}:{result.line_num}:{result.col_pos}",
                "title": title,
                "edition": "mula",
                "snippet": snippet,
                "book_no": result.book_no,
                "page_num": result.page_num,
                "line_num": result.line_num,
                "col_pos": result.col_pos,
                "word": result.matched_word,
                "frequency": result.frequency,
                "score": result.score,
                "search_mode": result.search_mode,
                "book_info": {
                    "book_no": result.book_info.book_no,
                    "title": result.book_info.title,
                    "abbreviation": result.book_info.abbreviation,
                    "nikaya": result.book_info.nikaya,
                    "volume": result.book_info.volume,
                    "pages": result.book_info.pages,
                    "description": result.book_info.description,
                },
                "page_title": result.page_title,
                "is_cross_ref": result.is_cross_ref,
                "in_footnote": result.in_footnote,
                "apparatus_available": result.apparatus_available,
                "context_before": result.context_before,
                "context_after": result.context_after,
            }

            formatted.append(formatted_result)

        return formatted

    def search(
        self, query: str, mode: str = "text", limit: int = 50, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Unified search method supporting multiple modes.

        Args:
            query: Search query
            mode: Search mode ("exact", "text", "fuzzy")
            limit: Maximum number of results
            **kwargs: Additional search parameters

        Returns:
            List of formatted search results
        """
        if mode == "exact":
            return self.search_by_word_exact(query, limit=limit)
        elif mode == "fuzzy":
            return self.search_by_text(query, limit=limit, fuzzy=True)
        else:  # "text" mode
            return self.search_by_text(query, limit=limit, fuzzy=False)

    def get_search_modes(self) -> List[Dict[str, str]]:
        """
        Get available search modes.

        Returns:
            List of mode descriptions
        """
        return [
            {
                "id": "exact",
                "name": "Exact Word",
                "description": "Search for exact word matches",
            },
            {
                "id": "text",
                "name": "Text Search",
                "description": "Search in text content",
            },
            {
                "id": "fuzzy",
                "name": "Fuzzy Search",
                "description": "Search with approximate matching",
            },
        ]

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


def create_enhanced_search(db_path: str) -> EnhancedSearch:
    """
    Factory function to create EnhancedSearch instance.

    Args:
        db_path: Path to SQLite database

    Returns:
        EnhancedSearch instance
    """
    return EnhancedSearch(db_path)
