#!/usr/bin/env python3
"""
Basic tests for Tipitaka PTS Browser.

This module contains basic unit tests for the application's core functionality.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

# Import the application module
try:
    from main import TipitakaBrowser

    MODULE_AVAILABLE = True
except ImportError:
    MODULE_AVAILABLE = False
    TipitakaBrowser = Mock


@unittest.skipIf(not MODULE_AVAILABLE, "Main module not available")
class TestTipitakaBrowser(unittest.TestCase):
    """Test cases for TipitakaBrowser class."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp(prefix="tipitaka_test_")
        self.data_dir = Path(self.temp_dir) / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Create test data files
        self._create_test_data()

        # Create browser instance
        self.browser = TipitakaBrowser(data_dir=str(self.data_dir))

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_data(self):
        """Create test data files."""
        # Create edition conversions file
        conversions = {
            "books": {
                "dn01": {
                    "available_editions": ["PTS", "MYANMAR", "VRI"],
                    "conversions": {
                        "MYANMAR": {"PTS": "dn01_my"},
                        "VRI": {"PTS": "dn01_vri"},
                    },
                },
                "mn01": {
                    "available_editions": ["PTS", "MYANMAR"],
                    "conversions": {"MYANMAR": {"PTS": "mn01_my"}},
                },
            }
        }

        with open(
            self.data_dir / "edition_conversions.json", "w", encoding="utf-8"
        ) as f:
            json.dump(conversions, f)

        # Create matn relations file
        relations = {
            "dn01": {
                "related": ["dn02", "dn03"],
                "commentaries": ["dn01_com"],
                "subcommentaries": ["dn01_sub"],
            }
        }

        with open(self.data_dir / "matn_relations.json", "w", encoding="utf-8") as f:
            json.dump(relations, f)

        # Create settings file
        settings = {
            "language": "en",
            "font_size": 12,
            "theme": "light",
            "default_edition": "PTS",
        }

        with open(self.data_dir / "settings.json", "w", encoding="utf-8") as f:
            json.dump(settings, f)

    def test_initialization(self):
        """Test that browser initializes correctly."""
        self.assertIsNotNone(self.browser)
        self.assertEqual(self.browser.current_edition, "PTS")
        self.assertEqual(len(self.browser.bookmarks), 0)
        self.assertEqual(len(self.browser.search_history), 0)

    def test_get_available_editions(self):
        """Test getting available editions for a text."""
        editions = self.browser.get_available_editions("dn01")
        self.assertIsInstance(editions, list)
        self.assertIn("PTS", editions)
        self.assertIn("MYANMAR", editions)
        self.assertIn("VRI", editions)

        # Test with non-existent text
        editions = self.browser.get_available_editions("nonexistent")
        self.assertEqual(editions, ["PTS"])  # Default

    def test_save_and_load_settings(self):
        """Test saving and loading settings."""
        # Test loading default settings
        settings = self.browser.load_settings()
        self.assertIsInstance(settings, dict)
        self.assertEqual(settings["language"], "en")
        self.assertEqual(settings["font_size"], 12)

        # Test saving new settings
        new_settings = {
            "language": "es",
            "font_size": 14,
            "theme": "dark",
            "default_edition": "MYANMAR",
        }

        result = self.browser.save_settings(new_settings)
        self.assertTrue(result)

        # Verify settings were saved
        settings_file = self.data_dir / "settings.json"
        self.assertTrue(settings_file.exists())

        with open(settings_file, "r", encoding="utf-8") as f:
            saved_settings = json.load(f)

        self.assertEqual(saved_settings["language"], "es")
        self.assertEqual(saved_settings["font_size"], 14)

    def test_add_bookmark(self):
        """Test adding bookmarks."""
        initial_count = len(self.browser.bookmarks)

        # Add a bookmark
        result = self.browser.add_bookmark(
            text_id="dn01", position=100, note="Important passage"
        )

        self.assertTrue(result)
        self.assertEqual(len(self.browser.bookmarks), initial_count + 1)

        # Verify bookmark content
        bookmark = self.browser.bookmarks[-1]
        self.assertEqual(bookmark["text_id"], "dn01")
        self.assertEqual(bookmark["position"], 100)
        self.assertEqual(bookmark["note"], "Important passage")
        self.assertIn("timestamp", bookmark)

    def test_lookup_dictionary(self):
        """Test dictionary lookup."""
        # Test with a word
        result = self.browser.lookup_dictionary("dhamma")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["word"], "dhamma")
        self.assertIn("definition", result)
        self.assertEqual(result["etymology"], "Pali")

        # Test with empty string
        result = self.browser.lookup_dictionary("")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["word"], "")

    def test_search_texts(self):
        """Test text search functionality."""
        # This is a mock test since we don't have a real database
        results = self.browser.search_texts("test query")
        self.assertIsInstance(results, list)

    def test_get_text_with_database(self):
        """get_text returns a structured dict via the database layer (PTS path)."""
        browser = TipitakaBrowser(data_dir=str(self.data_dir))

        # Mock the database seam that the PTS path depends on.
        mock_db = Mock()
        mock_db.get_page_by_pts_citation.return_value = {
            "text": "This is test text content",
            "book_no": 9,
            "page_num": 3,
            "head": "",
        }
        browser._database = mock_db

        result = browser.get_text("dn01", "PTS")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["text"], "This is test text content")
        self.assertEqual(result["edition"], "PTS")
        mock_db.get_page_by_pts_citation.assert_called_once_with("dn01")

    def test_directory_structure(self):
        """Test that directory structure is created correctly."""
        # Check that directories exist
        self.assertTrue(self.browser.data_dir.exists())
        self.assertTrue(self.browser.dict_dir.exists())
        self.assertTrue(self.browser.docs_dir.exists())

        # Check directory relationships
        self.assertEqual(self.browser.dict_dir, self.browser.data_dir / "dictionaries")


class TestCLIFunctions(unittest.TestCase):
    """Test command-line interface functions."""

    def test_cli_commands(self):
        """Test CLI command parsing."""
        # This would test the CLI interaction functions
        # For now, just a placeholder
        pass


if __name__ == "__main__":
    unittest.main()
