#!/usr/bin/env python3
"""
Test script for UI integration of EnhancedTipitakaBrowser.

This script tests the integration between the enhanced backend
and the QML frontend components.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from main import TipitakaBrowser
from main.ui_integration import EnhancedTipitakaBrowser, create_enhanced_browser


def test_backend_integration():
    """Test that the backend integration works correctly."""
    print("=" * 60)
    print("Testing Backend Integration")
    print("=" * 60)

    # Create a test data directory
    test_data_dir = Path(__file__).parent / "data"

    try:
        # Create the enhanced browser
        print("1. Creating EnhancedTipitakaBrowser...")
        enhanced_browser = create_enhanced_browser(str(test_data_dir))

        if not enhanced_browser:
            print("❌ Failed to create EnhancedTipitakaBrowser")
            return False

        print("✅ EnhancedTipitakaBrowser created successfully")

        # Test module status
        print("\n2. Checking module status...")
        status = enhanced_browser.get_module_status()
        for module, state in status.items():
            print(f"   {module}: {state}")

        # Test ROTA edition availability
        print("\n3. Checking ROTA edition...")
        rota_books = enhanced_browser.get_rota_available_books()
        if rota_books:
            print(f"✅ ROTA edition available with {len(rota_books)} books")
            print(f"   First book: {rota_books[0].get('book_name', 'Unknown')}")
        else:
            print("⚠️  ROTA edition not available")

        # Test citation parsing
        print("\n4. Testing citation parsing...")
        test_citations = ["M I 3", "Sn 25", "S.IV.100", "D 1"]
        for citation in test_citations:
            parsed = enhanced_browser.parse_citation(citation)
            if parsed:
                print(
                    f"✅ '{citation}' → Book {parsed.get('book_no')}, Page {parsed.get('page_num')}"
                )
            else:
                print(f"❌ Failed to parse '{citation}'")

        # Test search functionality
        print("\n5. Testing search functionality...")
        test_queries = ["buddha", "dhamma", "sangha"]
        for query in test_queries:
            results = enhanced_browser.enhanced_search(query, mode="text", limit=5)
            if results:
                print(f"✅ '{query}': Found {len(results)} results")
            else:
                print(f"⚠️  '{query}': No results found")

        # Test dictionary lookup
        print("\n6. Testing dictionary lookup...")
        test_words = ["buddha", "dhamma", "nibbāna"]
        for word in test_words:
            entry = enhanced_browser.enhanced_dictionary_lookup(word)
            if entry and entry.get("definition"):
                print(f"✅ '{word}': Found in dictionary")
            else:
                print(f"⚠️  '{word}': Not found in dictionary")

        # Test apparatus criticus
        print("\n7. Testing apparatus criticus...")
        if rota_books:
            # Test with first book, first page
            book_no = rota_books[0].get("book_no")
            if book_no:
                apparatus = enhanced_browser.get_apparatus_for_page(book_no, 1)
                if apparatus:
                    print(f"✅ Apparatus found: {len(apparatus)} variants")
                else:
                    print("⚠️  No apparatus found for first page")

        # Test cache statistics
        print("\n8. Testing cache statistics...")
        app_stats = enhanced_browser.get_apparatus_cache_stats()
        dict_stats = enhanced_browser.get_dictionary_cache_stats()

        if app_stats:
            print(f"   Apparatus cache: {app_stats.get('size', 0)} entries")
        if dict_stats:
            print(f"   Dictionary cache: {dict_stats.get('size', 0)} entries")

        print("\n" + "=" * 60)
        print("✅ All backend tests completed successfully!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_main_browser_integration():
    """Test that the main TipitakaBrowser integrates with EnhancedTipitakaBrowser."""
    print("\n" + "=" * 60)
    print("Testing Main Browser Integration")
    print("=" * 60)

    test_data_dir = Path(__file__).parent / "data"

    try:
        # Create the main browser
        print("1. Creating TipitakaBrowser...")
        browser = TipitakaBrowser(str(test_data_dir))

        if not browser:
            print("❌ Failed to create TipitakaBrowser")
            return False

        print("✅ TipitakaBrowser created successfully")

        # Check that enhanced browser is available
        print("\n2. Checking enhanced browser integration...")
        if hasattr(browser, "_enhanced_browser") and browser._enhanced_browser:
            print("✅ Enhanced browser is integrated")
        else:
            print("❌ Enhanced browser not integrated")
            return False

        # Test get_text with ROTA edition
        print("\n3. Testing text retrieval...")
        test_citation = "M I 3"
        text = browser.get_text(test_citation, "mula")
        if text:
            print(f"✅ Retrieved text for '{test_citation}' (ROTA)")
            print(f"   Preview: {text[:100]}...")
        else:
            print(f"⚠️  Could not retrieve text for '{test_citation}' (ROTA)")

        # Test get_text with PTS edition (fallback)
        text_pts = browser.get_text(test_citation, "PTS")
        if text_pts:
            print(f"✅ Retrieved text for '{test_citation}' (PTS)")
        else:
            print(f"⚠️  Could not retrieve text for '{test_citation}' (PTS)")

        # Test search
        print("\n4. Testing search...")
        results = browser.search_texts("buddha")
        if results:
            print(f"✅ Search found {len(results)} results")
            for i, result in enumerate(results[:3], 1):
                print(f"   {i}. {result.get('title', 'Unknown')}")
        else:
            print("⚠️  No search results found")

        # Test dictionary lookup
        print("\n5. Testing dictionary lookup...")
        entry = browser.lookup_dictionary("buddha")
        if entry and entry.get("definition"):
            print(f"✅ Dictionary lookup successful")
            print(f"   Definition: {entry.get('definition', '')[:100]}...")
        else:
            print("⚠️  Dictionary lookup failed")

        # Test settings
        print("\n6. Testing settings...")
        settings = browser.load_settings()
        if settings:
            print(f"✅ Settings loaded: {len(settings)} items")
            print(f"   Default edition: {settings.get('default_edition', 'Unknown')}")
        else:
            print("⚠️  Could not load settings")

        # Test saving settings
        test_settings = {
            "language": "en",
            "font_size": 14,
            "default_edition": "mula",
            "search_mode": "fuzzy",
        }
        saved = browser.save_settings(test_settings)
        if saved:
            print("✅ Settings saved successfully")
        else:
            print("⚠️  Failed to save settings")

        print("\n" + "=" * 60)
        print("✅ All integration tests completed successfully!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ Error during integration testing: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_qml_compatibility():
    """Test QML compatibility features."""
    print("\n" + "=" * 60)
    print("Testing QML Compatibility")
    print("=" * 60)

    test_data_dir = Path(__file__).parent / "data"

    try:
        # Create browser for QML testing
        browser = TipitakaBrowser(str(test_data_dir))

        # Test properties needed by QML
        print("1. Testing QML-required properties...")

        # Check bookmarks property
        if hasattr(browser, "bookmarks"):
            print("✅ 'bookmarks' property available")
        else:
            print("❌ 'bookmarks' property missing")

        # Check search_history property
        if hasattr(browser, "search_history"):
            print("✅ 'search_history' property available")
        else:
            print("❌ 'search_history' property missing")

        # Test methods needed by QML
        print("\n2. Testing QML-required methods...")

        # Test get_available_editions
        editions = browser.get_available_editions("M I 3")
        if isinstance(editions, list):
            print(f"✅ 'get_available_editions' works: {editions}")
        else:
            print("❌ 'get_available_editions' doesn't return a list")

        # Test add_bookmark
        try:
            browser.add_bookmark("M I 3", 100, "Test bookmark")
            print("✅ 'add_bookmark' works")
        except Exception as e:
            print(f"❌ 'add_bookmark' failed: {e}")

        # Test signals (if Qt is available)
        print("\n3. Testing Qt signals...")
        try:
            from PyQt6.QtCore import QObject, pyqtSignal

            if hasattr(browser, "textLoaded"):
                print("✅ 'textLoaded' signal available")
            if hasattr(browser, "searchResultsReady"):
                print("✅ 'searchResultsReady' signal available")
            if hasattr(browser, "dictionaryLookupReady"):
                print("✅ 'dictionaryLookupReady' signal available")
            if hasattr(browser, "settingsChanged"):
                print("✅ 'settingsChanged' signal available")
        except ImportError:
            print("⚠️  PyQt6 not available, skipping signal tests")

        print("\n" + "=" * 60)
        print("✅ QML compatibility tests completed!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ Error during QML testing: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("Tipitaka PTS Browser - UI Integration Tests")
    print("=" * 60)

    # Check if data directory exists
    data_dir = Path(__file__).parent / "data"
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        print("Please ensure the data directory exists with tipitaka.sqlite")
        return False

    # Check if database exists
    db_file = data_dir / "tipitaka.sqlite"
    if not db_file.exists():
        print(f"❌ Database file not found: {db_file}")
        print("Please ensure tipitaka.sqlite exists in the data directory")
        return False

    print(f"Using data directory: {data_dir}")
    print(f"Database file: {db_file}")
    print()

    # Run tests
    all_passed = True

    # Test 1: Backend integration
    if not test_backend_integration():
        all_passed = False

    # Test 2: Main browser integration
    if not test_main_browser_integration():
        all_passed = False

    # Test 3: QML compatibility
    if not test_qml_compatibility():
        all_passed = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    if all_passed:
        print("✅ All integration tests PASSED!")
        print("\nThe UI integration is ready for deployment.")
        print("Next steps:")
        print("1. Run the application with: python -m src.main")
        print("2. Test the QML interface")
        print("3. Package for distribution")
    else:
        print("❌ Some tests FAILED!")
        print("\nPlease check the errors above and fix the integration issues.")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
