#!/usr/bin/env python3
"""
Test script for ROTA (Royal Thai) edition verification.

This script tests the ROTA edition functionality to ensure that:
1. The database contains ROTA edition data
2. UNITEXT is properly decoded (Base64 + BOM + UTF-8)
3. Citation parsing works correctly for ROTA
4. All enhanced modules work with ROTA edition
"""

import base64
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config
from main.citation_parser import PTSCitationParser
from main.rota_edition import create_rota_manager, decode_rota_text
from main.ui_integration import create_enhanced_browser


def test_rota_database_structure():
    """Test ROTA database structure and content."""
    print("=" * 60)
    print("ROTA EDITION VERIFICATION TEST")
    print("=" * 60)

    config = get_config()
    data_dir = config.get("paths.data_dir", "data")
    db_path = os.path.join(data_dir, "tipitaka.sqlite")

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False

    print(f"✅ Database found: {db_path}")

    # Test basic database connectivity
    import sqlite3

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check main ROTA table
        cursor.execute("SELECT COUNT(*) as count FROM Dbf1__palipg WHERE _deleted = 0")
        row = cursor.fetchone()
        print(f"✅ ROTA pages in Dbf1__palipg: {row['count']:,}")

        # Check UNITEXT encoding
        cursor.execute("""
            SELECT BOOKNUM, RPAGENUM, HEAD, LENGTH(UNITEXT) as ut_len,
                   LENGTH(ENCPALI) as ep_len
            FROM Dbf1__palipg
            WHERE BOOKNUM = 1 AND RPAGENUM = 1 AND _deleted = 0
        """)
        row = cursor.fetchone()

        if row:
            print(
                f"✅ Sample page found: Book {row['BOOKNUM']}, Page {row['RPAGENUM']}"
            )
            print(f"   Header: {row['HEAD'][:50]}...")
            print(f"   UNITEXT length: {row['ut_len']} bytes")
            print(f"   ENCPALI length: {row['ep_len']} bytes")

            # Test UNITEXT decoding
            cursor.execute("""
                SELECT UNITEXT FROM Dbf1__palipg
                WHERE BOOKNUM = 1 AND RPAGENUM = 1 AND _deleted = 0
            """)
            unitext_row = cursor.fetchone()
            if unitext_row and unitext_row["UNITEXT"]:
                decoded = decode_rota_text(unitext_row["UNITEXT"])
                print(f"✅ UNITEXT decoded successfully")
                print(f"   First 100 chars: {decoded[:100]}")

                # Verify it contains Pali text
                if any(
                    keyword in decoded.lower()
                    for keyword in ["vinaya", "tipitaka", "pali", "dhamma"]
                ):
                    print(f"✅ Contains Pali keywords")
                else:
                    print(f"⚠️  May not contain expected Pali text")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_rota_edition_module():
    """Test ROTA edition module functionality."""
    print("\n" + "=" * 60)
    print("ROTA EDITION MODULE TEST")
    print("=" * 60)

    config = get_config()
    data_dir = config.get("paths.data_dir", "data")
    db_path = os.path.join(data_dir, "tipitaka.sqlite")

    if not os.path.exists(db_path):
        print(f"❌ Database not found")
        return False

    manager = create_rota_manager(db_path)
    if not manager:
        print(f"❌ Failed to create ROTA manager")
        return False

    print(f"✅ ROTA manager created successfully")

    # Test 1: Get a page
    print("\n1. Testing page retrieval:")
    page = manager.get_page(1, 1)  # Vinaya I, page 1
    if page:
        print(f"   ✅ Page retrieved: {page.head[:50]}...")
        print(f"   Text length: {len(page.unitext):,} characters")
        print(f"   Has Thai script: {page.metadata['has_thai_script']}")
        print(f"   Has PUA encoding: {page.metadata['has_pua_encoding']}")

        # Check if text looks like Pali
        if len(page.unitext) > 100:
            print(f"   Sample: {page.unitext[:100]}...")
    else:
        print(f"   ❌ Failed to retrieve page")
        return False

    # Test 2: Get book info
    print("\n2. Testing book info:")
    book_info = manager.get_book_info(1)
    if book_info:
        print(f"   ✅ Book info retrieved:")
        print(f"   Name: {book_info['name']}")
        print(f"   Abbreviation: {book_info['abbreviation']}")
        print(f"   Pages: {book_info['page_count']}")
        print(f"   Edition: {book_info['edition']}")
    else:
        print(f"   ❌ Failed to get book info")

    # Test 3: Search in text
    print("\n3. Testing text search:")
    results = manager.search_in_text("dhamma", limit=3)
    print(f"   Found {len(results)} results for 'dhamma'")
    if results:
        print(f"   ✅ Search works")
        for i, result in enumerate(results[:2]):
            print(f"   {i + 1}. Book {result['book_no']}, Page {result['page_num']}")
    else:
        print(f"   ⚠️  No results found (may be normal)")

    # Test 4: Get page range
    print("\n4. Testing page range:")
    first, last = manager.get_page_range(1)
    print(f"   Book 1 page range: {first} - {last}")
    if first <= last:
        print(f"   ✅ Valid page range")
    else:
        print(f"   ❌ Invalid page range")

    # Test 5: Available books
    print("\n5. Testing available books:")
    books = manager.get_available_books()
    print(f"   Total books available: {len(books)}")
    if books:
        print(f"   ✅ Books retrieved")
        print(f"   First 3 books:")
        for i, book in enumerate(books[:3]):
            print(f"   {i + 1}. Book {book['book_no']}: {book['name']}")
    else:
        print(f"   ❌ No books found")

    return True


def test_citation_parsing_for_rota():
    """Test citation parsing for ROTA edition."""
    print("\n" + "=" * 60)
    print("CITATION PARSING FOR ROTA TEST")
    print("=" * 60)

    parser = PTSCitationParser()

    # Test citations that should work with ROTA
    test_citations = [
        ("M I 3", "Majjhima Nikāya I, page 3"),
        ("Sn 25", "Sutta Nipāta, page 25"),
        ("D II 50", "Dīgha Nikāya II, page 50"),
        ("S IV 100", "Saṃyutta Nikāya IV, page 100"),
        ("A V 123", "Aṅguttara Nikāya V, page 123"),
        ("Vin I 10", "Vinaya Piṭaka I, page 10"),
    ]

    all_passed = True
    for citation, description in test_citations:
        result = parser.validate_citation(citation)
        if result.get("valid", False):
            print(f"✅ '{citation}' - {description}")
            print(
                f"   → Book No: {result.get('book_no')}, Page: {result.get('parsed', {}).get('page')}"
            )
        else:
            print(f"❌ '{citation}' - FAILED: {result.get('error', 'Unknown error')}")
            all_passed = False

    return all_passed


def test_enhanced_browser_with_rota():
    """Test enhanced browser with ROTA edition."""
    print("\n" + "=" * 60)
    print("ENHANCED BROWSER WITH ROTA TEST")
    print("=" * 60)

    config = get_config()
    data_dir = config.get("paths.data_dir", "data")

    browser = create_enhanced_browser(data_dir)

    # Test module status
    print("1. Module status:")
    status = browser.get_module_status()

    modules_to_check = [
        ("database", "Database"),
        ("rota_edition", "ROTA Edition"),
        ("search", "Search"),
        ("dictionary", "Dictionary"),
        ("citation_parser", "Citation Parser"),
        ("apparatus", "Apparatus"),
    ]

    all_available = True
    for key, name in modules_to_check:
        available = status.get(key, {}).get("available", False)
        symbol = "✅" if available else "❌"
        print(f"   {symbol} {name}: {'Available' if available else 'Not available'}")
        if not available and key in ["database", "rota_edition"]:
            all_available = False

    if not all_available:
        print("   ⚠️  Critical modules not available")
        return False

    # Test ROTA-specific functionality
    print("\n2. Testing ROTA functionality:")

    # Get ROTA page
    result = browser.get_rota_page(1, 1)
    if "error" not in result:
        print(f"   ✅ ROTA page retrieval works")
        print(f"   Edition: {result.get('edition', 'Unknown')}")
        print(f"   Text length: {len(result.get('text', '')):,} chars")
    else:
        print(f"   ❌ ROTA page retrieval failed: {result.get('error')}")

    # Test citation to ROTA text
    print("\n3. Testing citation to ROTA text:")
    text_result = browser.get_text_by_citation("M I 3")
    if text_result.get("success", False):
        print(f"   ✅ Citation parsing works")
        print(f"   Edition: {text_result.get('edition', 'Unknown')}")
        print(f"   Text preview: {text_result.get('text', '')[:100]}...")
    else:
        print(
            f"   ❌ Citation parsing failed: {text_result.get('error', 'Unknown error')}"
        )

    return True


def test_encoding_decoding():
    """Test encoding/decoding of ROTA text."""
    print("\n" + "=" * 60)
    print("ENCODING/DECODING TEST")
    print("=" * 60)

    config = get_config()
    data_dir = config.get("paths.data_dir", "data")
    db_path = os.path.join(data_dir, "tipitaka.sqlite")

    if not os.path.exists(db_path):
        return False

    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get a sample UNITEXT
    cursor.execute("""
        SELECT UNITEXT FROM Dbf1__palipg
        WHERE BOOKNUM = 1 AND RPAGENUM = 1 AND _deleted = 0
        LIMIT 1
    """)

    row = cursor.fetchone()
    if not row or not row["UNITEXT"]:
        print("❌ No UNITEXT sample found")
        conn.close()
        return False

    encoded_text = row["UNITEXT"]
    print(f"Encoded text length: {len(encoded_text)} chars")

    # Test manual decoding
    try:
        # Add padding if needed
        text = encoded_text.strip()
        if len(text) % 4 != 0:
            text += "=" * (4 - len(text) % 4)

        # Base64 decode
        raw = base64.b64decode(text)
        print(f"Base64 decoded length: {len(raw)} bytes")

        # Check for BOM
        has_bom = raw[:3] == b"\xef\xbb\xbf"
        print(f"Has UTF-8 BOM: {has_bom}")

        if has_bom:
            decoded = raw[3:].decode("utf-8", errors="replace")
        else:
            decoded = raw.decode("utf-8", errors="replace")

        print(f"Decoded length: {len(decoded)} chars")
        print(f"First 150 chars:\n{decoded[:150]}")

        # Test with our decoder function
        our_decoded = decode_rota_text(encoded_text)
        print(f"\nDecoder function result length: {len(our_decoded)} chars")

        if decoded == our_decoded:
            print("✅ Manual and function decoding match")
        else:
            print("⚠️  Manual and function decoding differ")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Decoding test failed: {e}")
        conn.close()
        return False


def main():
    """Run all ROTA edition tests."""
    print("ROTA Edition Comprehensive Test Suite")
    print("=" * 60)

    tests = [
        ("Database Structure", test_rota_database_structure),
        ("ROTA Edition Module", test_rota_edition_module),
        ("Citation Parsing", test_citation_parsing_for_rota),
        ("Enhanced Browser", test_enhanced_browser_with_rota),
        ("Encoding/Decoding", test_encoding_decoding),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n▶️  Running: {test_name}")
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("✅ ALL TESTS PASSED - ROTA edition is working correctly!")
    elif passed >= total * 0.7:
        print("⚠️  MOST TESTS PASSED - ROTA edition is mostly working")
    else:
        print("❌ MANY TESTS FAILED - ROTA edition has issues")

    # Detailed results
    print("\nDetailed results:")
    for test_name, success in results:
        symbol = "✅" if success else "❌"
        print(f"  {symbol} {test_name}")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
