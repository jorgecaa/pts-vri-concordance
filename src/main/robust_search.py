"""
Robust search implementation for Tipitaka PTS Browser.

This module provides search functionality that works with the actual
database structure, handling the specific schema of the Tipitaka SQLite database.
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
    volume: str
    pages: int
    description: str = ""


@dataclass
class SearchResult:
    """Search result with comprehensive information."""

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


class RobustSearch:
    """Robust search functionality for actual database structure."""

    def __init__(self, db_path: str):
        """
        Initialize robust search.

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

    def _decode_base64_text(self, encoded_text: str) -> str:
        """
        Decode Base64 encoded text with UTF-8 BOM handling.

        Args:
            encoded_text: Base64 encoded text

        Returns:
            Decoded text string
        """
        if not encoded_text:
            return ""

        try:
            # Remove whitespace
            encoded_text = encoded_text.strip()

            # Decode Base64
            return encoded_text or ""  # already decoded

            # Remove UTF-8 BOM if present
            if decoded_bytes.startswith(b"\xef\xbb\xbf"):
                decoded_bytes = decoded_bytes[3:]

            # Decode as UTF-8
            return decoded_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            print(f"Error decoding Base64 text: {e}")
            # Try to return as-is if not Base64
            return encoded_text

    def _extract_numeric_key(self, key: str) -> int:
        """
        Extract numeric value from database key.

        Args:
            key: Database key string

        Returns:
            Extracted integer value
        """
        if not key:
            return 0

        try:
            # Try direct integer conversion first
            return int(key)
        except ValueError:
            # Extract numbers from string
            numbers = re.findall(r"\d+", key)
            if numbers:
                return int(numbers[0])
            return 0

    @lru_cache(maxsize=100)
    def get_book_info(self, book_no: int) -> Optional[BookInfo]:
        """
        Get book information from database.

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

            # Get book information from books table
            cursor.execute(
                """
                SELECT
                    BOOK_NO,
                    BOOK_NAME,
                    S_NAME,
                    VOL_ID,
                    BEGPAGE,
                    ENDPAGE
                FROM books
                WHERE BOOK_NO = ? 
                LIMIT 1
            """,
                (book_no,),
            )

            row = cursor.fetchone()
            if row:
                pages = 0
                if row["end_page"] and row["beg_page"]:
                    try:
                        pages = int(row["end_page"]) - int(row["beg_page"]) + 1
                    except:
                        pass

                book_info = BookInfo(
                    book_no=row["book_no"],
                    title=row["book_name"] or f"Book {book_no}",
                    abbreviation=row["s_name"] or "",
                    volume=row["edition"] or "",
                    pages=pages,
                    description=f"Volume {row['VOL_ID']}" if row["edition"] else "",
                )
                self._book_cache[book_no] = book_info
                return book_info

            # Fallback: try to get book name from palipg table
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
                volume="",
                pages=0,
                description="",
            )
            self._book_cache[book_no] = book_info
            return book_info

        except Exception as e:
            print(f"Error getting book info for book {book_no}: {e}")
            return None

    def search_word_exact(self, word: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for exact word matches using word index.

        Args:
            word: Word to search for
            limit: Maximum number of results

        Returns:
            List of search results
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            # First, find the word in words table
            cursor.execute(
                """
                SELECT SKID, STR1, STR1M, NFOUND
                FROM word_list
                WHERE (STR1 = ? OR STR1M = ?) 
                LIMIT 5
            """,
                (word, word),
            )

            word_rows = cursor.fetchall()
            if not word_rows:
                return []

            results = []

            for word_row in word_rows:
                word_key = word_row["SKID"]
                word_str = word_row["STR1"] or word_row["STR1M"] or word
                total_found = self._extract_numeric_key(word_row["NFOUND"])

                # Get occurrences from wordsat table
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
                    # Extract location information
                    book_key = occ["book_key"]
                    page_key = occ["page_key"]

                    # Try to convert keys to book_no and page_num
                    book_no = self._extract_numeric_key(book_key)
                    page_num = self._extract_numeric_key(page_key)

                    line_num = self._extract_numeric_key(occ["LINE"])
                    word_len = self._extract_numeric_key(occ["WORDLEN"])
                    col_pos = self._extract_numeric_key(occ["ATCOL"])

                    # Get book information
                    book_info = self.get_book_info(book_no)

                    # Get page text for context
                    cursor.execute(
                        """
                        SELECT unitext, HEAD, book_no, page_no
                        FROM pages
                        WHERE book_no = ? AND page_no = ? 
                        LIMIT 1
                    """,
                        (book_no, page_num),
                    )

                    page_row = cursor.fetchone()
                    if not page_row:
                        continue

                    page_text = page_row["unitext"] or ""  # already decoded
                    page_title = page_row["head"] or ""

                    # Extract context
                    context_before, context_after, matched_word = self._extract_context(
                        page_text, line_num, col_pos, word_len
                    )

                    # Check if apparatus is available
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
                        score=1.0,
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

    def search_text_content(
        self, query: str, limit: int = 20, fuzzy: bool = False
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
                # Use LIKE for fuzzy matching
                search_pattern = f"%{query}%"
                cursor.execute(
                    """
                    SELECT book_no, page_no, unitext, head
                    FROM pages
                    WHERE unitext LIKE ? 
                    ORDER BY book_no, page_no
                    LIMIT ?
                """,
                    (search_pattern, limit),
                )
            else:
                # For exact matching, we need to decode and search in Python
                # This is less efficient but works with Base64 encoded text
                cursor.execute(
                    """
                    SELECT book_no, page_no, unitext, head
                    FROM pages
                    WHERE 1=1
                    ORDER BY book_no, page_no
                    LIMIT ?
                """,
                    (limit,),
                )

            page_rows = cursor.fetchall()
            results = []

            for row in page_rows:
                book_no = row["book_no"]
                page_num = row["page_no"]
                page_text = row["unitext"] or ""  # already decoded
                page_title = row["head"] or ""

                # Get book information
                book_info = self.get_book_info(book_no)

                # Search for query in decoded text
                occurrences = self._find_text_occurrences(page_text, query, fuzzy)

                for occ in occurrences[:3]:  # Limit occurrences per page
                    line_num, col_pos, word_len, matched_word = occ

                    # Extract context
                    context_before, context_after, _ = self._extract_context(
                        page_text, line_num, col_pos, word_len
                    )

                    # Check apparatus availability
                    apparatus_available = self._check_apparatus_available(
                        book_no, page_num
                    )

                    # Calculate score
                    score = self._calculate_relevance_score(query, matched_word, fuzzy)

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
            print(f"Error in text content search: {e}")
            return []

    def _extract_context(
        self,
        text: str,
        line_num: int,
        col_pos: int,
        word_len: int,
        context_chars: int = 50,
    ) -> Tuple[str, str, str]:
        """
        Extract context around a word in text.

        Args:
            text: Full text
            line_num: Line number (1-based)
            col_pos: Column position (1-based)
            word_len: Word length
            context_chars: Number of characters before/after to include

        Returns:
            Tuple of (context_before, context_after, matched_word)
        """
        # Split text into lines
        lines = text.split("\n")
        if line_num < 1 or line_num > len(lines):
            return ("", "", "")

        # Get the target line
        target_line = lines[line_num - 1]

        # Adjust for 1-based indexing
        col_pos_idx = max(0, col_pos - 1)

        # Ensure word fits in line
        if col_pos_idx + word_len > len(target_line):
            word_len = len(target_line) - col_pos_idx

        # Extract the word
        matched_word = target_line[col_pos_idx : col_pos_idx + word_len]

        # Build context before
        context_start = max(0, col_pos_idx - context_chars)
        context_before = target_line[context_start:col_pos_idx]

        # Build context after
        context_end = col_pos_idx + word_len + context_chars
        context_after = target_line[col_pos_idx + word_len : context_end]

        return context_before, context_after, matched_word

    def _find_text_occurrences(
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
                # Case-insensitive search
                query_lower = query.lower()
                line_lower = line.lower()

                start = 0
                while True:
                    match_pos = line_lower.find(query_lower, start)
                    if match_pos == -1:
                        break

                    # Get the actual matched word from original line
                    matched_word = line[match_pos : match_pos + len(query)]

                    occurrences.append(
                        (
                            line_idx + 1,  # line_num (1-based)
                            match_pos + 1,  # col_pos (1-based)
                            len(query),  # word_len
                            matched_word,  # matched_word
                        )
                    )

                    start = match_pos + len(query)
            else:
                # Exact search
                start = 0
                while True:
                    match_pos = line.find(query, start)
                    if match_pos == -1:
                        break

                    occurrences.append((line_idx + 1, match_pos + 1, len(query), query))

                    start = match_pos + len(query)

        return occurrences

    def _calculate_relevance_score(
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

        # For fuzzy matches, calculate similarity
        if query.lower() == matched_word.lower():
            return 1.0

        # Simple character overlap similarity
        query_chars = set(query.lower())
        matched_chars = set(matched_word.lower())

        if not query_chars or not matched_chars:
            return 0.0

        intersection = len(query_chars.intersection(matched_chars))
        union = len(query_chars.union(matched_chars))

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

            # First, get the BOOK and PAGE keys for this book_no and page_num
            cursor.execute(
                """
                SELECT BOOK, PAGE
                FROM pages
                WHERE book_no = ? AND page_no = ? 
                LIMIT 1
            """,
                (book_no, page_num),
            )

            page_row = cursor.fetchone()
            if not page_row:
                return False

            book_key = page_row["book_key"]
            page_key = page_row["page_key"]

            # Check if apparatus exists for these keys
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM footnotes
                WHERE BOOK = ? AND PAGE = ? 
            """,
                (book_key, page_key),
            )

            row = cursor.fetchone()
            return row and row["count"] > 0

        except Exception:
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
        self, query: str, mode: str = "text", limit: int = 20, **kwargs
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
            return self.search_word_exact(query, limit=limit)
        elif mode == "fuzzy":
            return self.search_text_content(query, limit=limit, fuzzy=True)
        else:  # "text" mode
            return self.search_text_content(query, limit=limit, fuzzy=False)

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
                "description": "Search for exact word matches using word index",
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


def create_robust_search(db_path: str) -> RobustSearch:
    """
    Factory function to create RobustSearch instance.

    Args:
        db_path: Path to SQLite database

    Returns:
        RobustSearch instance
    """
    return RobustSearch(db_path)
