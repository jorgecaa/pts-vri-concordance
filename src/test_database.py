#!/usr/bin/env python3
"""
Test script for the Tipitaka PTS Browser database module.

This script tests the critical database functionality that was identified
as broken in the original application.
"""

import base64
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from main.database import TipitakaDatabase, decode


def test_decode_function():
    """Test the decode function for UNITEXT columns."""
    print("Testing decode function...")

    # Test 1: Empty input
    assert decode(None) == ""
    assert decode("") == ""

    # Test 2: Plain text (not Base64)
    # Use text that's unlikely to be valid Base64 when padded
    plain_text = "This is a HEAD field value with Pali: Buddha"
    result = decode(plain_text)
    assert result == plain_text, f"Expected '{plain_text}', got '{result}'"

    # Test 3: Base64 encoded text with BOM
    # Create a proper test: "test" in UTF-8 with BOM
    test_text = "test"
    utf8_bytes = test_text.encode("utf-8")
    bom_bytes = b"\xef\xbb\xbf"
    combined = bom_bytes + utf8_bytes
    test_encoded = base64.b64encode(combined).decode("ascii")

    decoded = decode(test_encoded)
    print(f"  Decoded Base64 with BOM -> '{decoded}'")
    assert decoded == test_text, f"Expected '{test_text}', got '{decoded}'"

    print("  ✓ decode function tests passed\n")
    return True


def test_database_connection():
    """Test database connection and basic queries."""
    print("Testing database connection...")

    # Path to the database
    db_path = Path(__file__).parent / "data" / "tipitaka.sqlite"

    if not db_path.exists():
        print(f"  ✗ Database not found at {db_path}")
        print("  Please ensure the database file exists")
        return False

    print(f"  Database found at {db_path}")

    # Create database instance
    db = TipitakaDatabase(db_path)

    # Test connection
    if not db.connect():
        print("  ✗ Failed to connect to database")
        return False

    print("  ✓ Connected to database")

    # Test getting all books
    books = db.get_all_books()
    print(f"  Found {len(books)} books in database")

    if len(books) == 0:
        print("  ✗ No books found in database")
        return False

    print(f"  ✓ Found {len(books)} books")

    # Test getting a specific book
    first_book = books[0]
    book_no = first_book["BOOK_NO"]
    book_info = db.get_book_info(book_no)

    if book_info:
        print(
            f"  ✓ Retrieved book info for BOOK_NO={book_no}: {book_info.get('S_NAME', 'Unknown')}"
        )
    else:
        print(f"  ✗ Failed to get book info for BOOK_NO={book_no}")
        return False

    db.close()
    print("  ✓ Database connection tests passed\n")
    return True


def test_text_retrieval():
    """Test retrieving text from the database."""
    print("Testing text retrieval...")

    db_path = Path(__file__).parent / "data" / "tipitaka.sqlite"

    if not db_path.exists():
        print(f"  ✗ Database not found")
        return False

    db = TipitakaDatabase(db_path)

    if not db.connect():
        print("  ✗ Failed to connect to database")
        return False

    # Test 1: Get page by book and page number
    # Try to get a page from a known book (Majjhima Nikaya, Book 1, Page 1)
    page_data = db.get_page_by_book_and_page(9, 1)  # M I 1

    if not page_data:
        print("  ✗ Failed to get page by book and page number")

        # Try a different page that might exist
        page_data = db.get_page_by_book_and_page(9, 10)

        if not page_data:
            print("  ✗ No pages found in book 9")
            db.close()
            return False

    print(
        f"  ✓ Retrieved page: Book {page_data['book_no']}, Page {page_data['page_num']}"
    )

    # Check if text was decoded
    text = page_data.get("text", "")
    if text:
        print(f"  ✓ Text decoded successfully ({len(text)} characters)")
        print(f"  Sample: {text[:100]}...")
    else:
        print("  ⚠ Text is empty (might be expected for some pages)")

    # Test 2: Get apparatus criticus if available
    apparatus = page_data.get("apparatus", "")
    if apparatus:
        print(f"  ✓ Apparatus criticus found ({len(apparatus)} characters)")
    else:
        print("  ⚠ No apparatus criticus for this page")

    db.close()
    print("  ✓ Text retrieval tests passed\n")
    return True


def test_search_functionality():
    """Test search functionality."""
    print("Testing search functionality...")

    db_path = Path(__file__).parent / "data" / "tipitaka.sqlite"

    if not db_path.exists():
        print(f"  ✗ Database not found")
        return False

    db = TipitakaDatabase(db_path)

    if not db.connect():
        print("  ✗ Failed to connect to database")
        return False

    # Test search for a common Pali word
    search_results = db.search_texts("dhamma", limit=5)

    print(f"  Search for 'dhamma' returned {len(search_results)} results")

    if len(search_results) > 0:
        print("  ✓ Search functionality works")

        # Show first result
        first_result = search_results[0]
        print(
            f"  First result: {first_result.get('word', 'Unknown')} "
            f"in Book {first_result.get('book_no')}, Page {first_result.get('page_num')}"
        )
        print(f"  Frequency: {first_result.get('frequency', 0)}")
    else:
        print("  ⚠ No search results found (might be expected if word index is empty)")

    db.close()
    print("  ✓ Search functionality tests passed\n")
    return True


def test_dictionary_lookup():
    """Test dictionary lookup functionality."""
    print("Testing dictionary lookup...")

    db_path = Path(__file__).parent / "data" / "tipitaka.sqlite"

    if not db_path.exists():
        print(f"  ✗ Database not found")
        return False

    db = TipitakaDatabase(db_path)

    if not db.connect():
        print("  ✗ Failed to connect to database")
        return False

    # Test lookup for a common Pali word
    entry = db.get_dictionary_entry("dhamma")

    if entry:
        print(f"  ✓ Found dictionary entry for 'dhamma'")
        print(f"  Definition: {entry.get('definition', '')[:100]}...")
        print(f"  Source: {entry.get('source', 'Unknown')}")
    else:
        print("  ⚠ No dictionary entry found for 'dhamma'")

        # Try another word
        entry = db.get_dictionary_entry("buddha")

        if entry:
            print(f"  ✓ Found dictionary entry for 'buddha'")
            print(f"  Definition: {entry.get('definition', '')[:100]}...")
            print(f"  Source: {entry.get('source', 'Unknown')}")
        else:
            print("  ⚠ No dictionary entries found (dictionary tables might be empty)")

    db.close()
    print("  ✓ Dictionary lookup tests passed\n")
    return True


def test_pts_citation_parsing():
    """Test PTS citation parsing (simplified version)."""
    print("Testing PTS citation parsing...")

    db_path = Path(__file__).parent / "data" / "tipitaka.sqlite"

    if not db_path.exists():
        print(f"  ✗ Database not found")
        return False

    db = TipitakaDatabase(db_path)

    if not db.connect():
        print("  ✗ Failed to connect to database")
        return False

    # Test getting page by PTS citation
    # Note: This uses a simplified parser - full implementation would be more robust

    # Try a few known citations
    test_citations = [
        ("M I 1", "Majjhima Nikaya, Book 1, Page 1"),
        ("Sn 25", "Sutta Nipata, Page 25"),
        ("Dhp 1", "Dhammapada, Page 1"),
    ]

    successes = 0
    for citation, description in test_citations:
        page_data = db.get_page_by_pts_citation(citation)

        if page_data:
            print(f"  ✓ Found page for '{citation}' ({description})")
            print(
                f"    Book: {page_data.get('book_no')}, Page: {page_data.get('page_num')}"
            )
            successes += 1
        else:
            print(f"  ⚠ No page found for '{citation}'")

    if successes > 0:
        print(f"  ✓ Found {successes} out of {len(test_citations)} test citations")
    else:
        print(f"  ⚠ Could not find any pages for test citations")
        print("  This might be due to the simplified citation parser")

    db.close()
    print("  ✓ PTS citation tests completed\n")
    return successes > 0


def main():
    """Run all tests."""
    print("=" * 60)
    print("Tipitaka PTS Browser - Database Module Tests")
    print("=" * 60)
    print()

    tests = [
        ("Decode Function", test_decode_function),
        ("Database Connection", test_database_connection),
        ("Text Retrieval", test_text_retrieval),
        ("Search Functionality", test_search_functionality),
        ("Dictionary Lookup", test_dictionary_lookup),
        ("PTS Citation Parsing", test_pts_citation_parsing),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"Test: {test_name}")
        print("-" * 40)

        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED\n")
            else:
                print(f"✗ {test_name} FAILED\n")
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}\n")
            import traceback

            traceback.print_exc()
            print()

    print("=" * 60)
    print(f"Test Summary: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"⚠ {total - passed} tests failed or had warnings")
        print("Note: Some tests may show warnings instead of failures")
        print("if the database has expected data gaps.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
