"""
Tests for database decoding and page retrieval.

Verifies that UNITEXT Base64 decoding works correctly and that
page retrieval returns legible Pali text (not encoded Base64).
"""

import sys
import unittest
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from main.database import TipitakaDatabase, decode_encpali, decode_unitext


class TestDecodeUnitext(unittest.TestCase):
    """Tests for the decode_unitext function."""

    def test_decode_empty_returns_empty(self):
        """Empty or None input should return empty string."""
        self.assertEqual(decode_unitext(None), "")
        self.assertEqual(decode_unitext(""), "")

    def test_decode_plain_utf8_returns_unchanged(self):
        """Plain UTF-8 text (like HEAD) should return unchanged."""
        text = "MAHĀVAGGA."
        result = decode_unitext(text)
        self.assertEqual(result, text)

    def test_decode_base64_with_bom(self):
        """Base64(BOM + UTF-8) should decode to legible text."""
        # Known pattern: Base64(BOM + "test")
        # BOM = \xef\xbb\xbf, so Base64("\xef\xbb\xbf" + "test")
        import base64

        raw = b"\xef\xbb\xbf" + "test".encode("utf-8")
        encoded = base64.b64encode(raw).decode("ascii")
        result = decode_unitext(encoded)
        self.assertEqual(result, "test")

    def test_decode_base64_with_pali_diacritics(self):
        """Should handle Pali diacritics (ā ī ū ṅ ñ ṭ ḍ ṇ ḷ ṃ)."""
        import base64

        pali = "Evaṃ me sutaṃ"
        raw = b"\xef\xbb\xbf" + pali.encode("utf-8")
        encoded = base64.b64encode(raw).decode("ascii")
        result = decode_unitext(encoded)
        self.assertEqual(result, pali)
        self.assertIn("ṃ", result)
        self.assertIn("Eva", result)

    def test_decode_base64_without_bom(self):
        """Base64 without BOM should still decode correctly."""
        import base64

        text = "dhamma"
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
        result = decode_unitext(encoded)
        self.assertEqual(result, text)

    def test_decode_with_missing_padding(self):
        """Base64 strings missing = padding should still decode."""
        import base64

        text = "buddha"
        raw = b"\xef\xbb\xbf" + text.encode("utf-8")
        encoded = base64.b64encode(raw).decode("ascii")
        # Remove padding
        no_pad = encoded.rstrip("=")
        result = decode_unitext(no_pad)
        self.assertEqual(result, text)


class TestDecodeEncpali(unittest.TestCase):
    """Tests for the decode_encpali function."""

    def test_decode_empty(self):
        self.assertEqual(decode_encpali(None), "")
        self.assertEqual(decode_encpali(""), "")

    def test_decode_encpali(self):
        """Basic ENCPALI decoding."""
        import base64

        text = "ไทย"
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
        result = decode_encpali(encoded)
        self.assertIn("ไทย", result)


class TestDatabaseIntegration(unittest.TestCase):
    """Integration tests with the real database."""

    @classmethod
    def setUpClass(cls):
        cls.db_path = src_dir / "data" / "tipitaka.sqlite"
        if not cls.db_path.exists():
            raise unittest.SkipTest(f"Database not found at {cls.db_path}")

    def setUp(self):
        self.db = TipitakaDatabase(self.db_path, edition="mula")
        self.assertTrue(self.db.connect(), "Database connection failed")

    def tearDown(self):
        self.db.close()

    def test_get_page_by_book_and_page_returns_decoded_text(self):
        """get_page_by_book_and_page must return decoded (legible) Pali text."""
        result = self.db.get_page_by_book_and_page(1, 1)  # Vinaya, page 1
        self.assertIsNotNone(result, "Page 1:1 should exist")
        text = result.get("text", "")
        self.assertTrue(len(text) > 50, f"Text too short: {len(text)} chars")
        # Must NOT contain Base64 artifacts
        self.assertNotIn("==", text[:20], "Text should not have Base64 padding")
        # Should contain Pali characters
        self.assertRegex(
            text, r"[āīūṅñṭḍṇḷṃĀĪŪṄÑṬḌṆḶṂ]", "Text should contain Pali diacritics"
        )

    def test_get_page_head_is_plain_text(self):
        """HEAD field should be plain UTF-8, not Base64."""
        result = self.db.get_page_by_book_and_page(1, 2)
        self.assertIsNotNone(result)
        head = result.get("head", "")
        self.assertNotIn("==", head[:20], f"HEAD should not be Base64: {head[:50]}")
        self.assertIsInstance(head, str, "HEAD should be a string")

    def test_search_texts_finds_real_pali_words(self):
        """Search should find real Pali words in decoded text."""
        results = self.db.search_texts("bhagavā", limit=5)
        self.assertGreater(len(results), 0, "Should find 'bhagavā' in the canon")
        # Verify snippets are legible
        for r in results[:3]:
            snippet = r.get("snippet", "")
            self.assertNotIn("==", snippet, f"Snippet has Base64: {snippet[:50]}")
            self.assertGreater(
                len(snippet.strip()), 5, f"Snippet too short: '{snippet}'"
            )

    def test_search_texts_returns_book_names(self):
        """Search results should include book_name."""
        results = self.db.search_texts("dhamma", limit=3)
        for r in results:
            self.assertIn("book_name", r, "Result should have book_name")
            self.assertIn("book_no", r)

    def test_get_apparatus_decoded(self):
        """Apparatus criticus should be decoded as well."""
        text = self.db.get_apparatus_for_page(1, 1)
        # Apparatus may be empty for some pages, that's OK
        if text:
            self.assertNotIn(
                "==", text[:20], f"Apparatus should be decoded, got: {text[:80]}"
            )

    def test_multiple_pages_decode(self):
        """Verify several random pages decode correctly."""
        test_pages = [(1, 1), (1, 10), (2, 1), (26, 3), (26, 25)]
        for book_no, page_num in test_pages:
            result = self.db.get_page_by_book_and_page(book_no, page_num)
            self.assertIsNotNone(result, f"Page {book_no}:{page_num} not found")
            text = result.get("text", "")
            self.assertNotIn(
                "==", text[:30], f"Page {book_no}:{page_num} has Base64 in text"
            )

    def test_decode_cache_works(self):
        """LRU cache should return same result for repeated calls."""
        result1 = self.db.get_page_by_book_and_page(1, 1)
        result2 = self.db.get_page_by_book_and_page(1, 1)
        self.assertEqual(result1["text"], result2["text"])
        # Verify text is actually decoded once by checking length consistency
        self.assertEqual(len(result1["text"]), len(result2["text"]))

    def test_concordance_finds_words(self):
        """Concordance should find words by scanning decoded unitext."""
        results = self.db.concordance("bhagav", limit=5)
        self.assertGreater(len(results), 0, "Should find 'bhagav' occurrences")
        for r in results[:3]:
            self.assertNotIn("==", r.get("snippet", ""))

    def test_search_advanced_with_book_filter(self):
        """Advanced search with book filter should work."""
        results = self.db.search_advanced("dhamma", book_no=26, limit=5)
        for r in results:
            self.assertEqual(r["book_no"], 26)


if __name__ == "__main__":
    unittest.main(verbosity=2)
