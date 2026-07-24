"""Tests for main.database — require data/tipitaka.sqlite."""

import base64
import sys
import unittest
from pathlib import Path

# Ensure 'src/' is on the path regardless of where the test is invoked from.
sys.path.insert(0, str(Path(__file__).parent.parent))

DB_PATH = Path(__file__).parent.parent / "data" / "tipitaka.sqlite"


def setUpModule():
    if not DB_PATH.exists():
        raise unittest.SkipTest(f"Database not found: {DB_PATH}")


class TestDecode(unittest.TestCase):
    """Unit tests for the decode_unitext() helper — no DB required."""

    def setUp(self):
        from main.database import decode_unitext

        self.decode = decode_unitext

    def _enc(self, text: str, bom: bool = True) -> str:
        payload = text.encode("utf-8")
        if bom:
            payload = b"\xef\xbb\xbf" + payload
        return base64.b64encode(payload).decode()

    def test_bom_payload(self):
        self.assertEqual(self.decode(self._enc("nirodho hotīti")), "nirodho hotīti")

    def test_no_bom_payload(self):
        self.assertEqual(self.decode(self._enc("plain", bom=False)), "plain")

    def test_plain_string_passthrough(self):
        self.assertEqual(self.decode("Vin I 1"), "Vin I 1")

    def test_none_returns_empty(self):
        self.assertEqual(self.decode(None), "")

    def test_empty_returns_empty(self):
        self.assertEqual(self.decode(""), "")


class TestTipitakaDatabase(unittest.TestCase):
    """Integration tests against the real SQLite database."""

    @classmethod
    def setUpClass(cls):
        from main.database import TipitakaDatabase

        cls.db = TipitakaDatabase(DB_PATH, edition="mula")
        cls.db.connect()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    # ── Books ──────────────────────────────────────────────────────────

    def test_get_all_books_count(self):
        books = self.db.get_all_books()
        self.assertGreater(len(books), 40)  # ~53 books in ROTA

    def test_get_all_books_fields(self):
        book = self.db.get_all_books()[0]
        self.assertIn("s_name", book)
        self.assertIn("book_no", book)
        self.assertEqual(book["edition"], "mula")

    # ── Page retrieval ─────────────────────────────────────────────────

    def test_page_vinaya_i_1(self):
        page = self.db.get_page_by_book_and_page(1, 1)
        self.assertIsNotNone(page)
        # Decoded text should contain Pali diacritics
        self.assertIn("vinaya", page["text"].lower())

    def test_page_dn_i_1(self):
        page = self.db.get_page_by_book_and_page(6, 1)
        self.assertIsNotNone(page)
        self.assertIn("namo", page["text"].lower())

    def test_page_nonexistent_returns_none(self):
        self.assertIsNone(self.db.get_page_by_book_and_page(999, 999))

    # ── PTS citations ──────────────────────────────────────────────────

    def test_pts_citation_vin_i_1(self):
        page = self.db.get_page_by_pts_citation("Vin I 1")
        self.assertIsNotNone(page)
        self.assertIn("vinaya", page["text"].lower())

    def test_pts_citation_m_i_3(self):
        self.assertIsNotNone(self.db.get_page_by_pts_citation("M I 3"))

    def test_pts_citation_invalid_returns_none(self):
        self.assertIsNone(self.db.get_page_by_pts_citation("XYZ 999"))

    # ── Apparatus criticus ─────────────────────────────────────────────

    def test_apparatus_returns_string(self):
        page = self.db.get_page_by_book_and_page(1, 2)
        self.assertIsNotNone(page)
        self.assertIsInstance(page["apparatus"], str)

    # ── search_texts ───────────────────────────────────────────────────

    def test_search_finds_results(self):
        results = self.db.search_texts("nirodho", limit=5)
        self.assertGreater(len(results), 0)

    def test_search_result_fields(self):
        r = self.db.search_texts("dukkha", limit=1)[0]
        for key in ("word", "book_no", "page_num", "snippet", "edition", "book_name"):
            self.assertIn(key, r)

    def test_search_snippet_contains_term(self):
        r = self.db.search_texts("bhikkhu", limit=1)[0]
        self.assertIn("bhikkhu", r["snippet"].lower())

    def test_search_no_results_returns_empty(self):
        self.assertEqual(self.db.search_texts("xyzzy_not_in_pali"), [])

    def test_search_case_insensitive(self):
        lower = self.db.search_texts("nirodho", limit=50)
        upper = self.db.search_texts("NIRODHO", limit=50)
        self.assertEqual(len(lower), len(upper))

    # ── Table of contents ──────────────────────────────────────────────

    def test_toc_book_1(self):
        toc = self.db.get_table_of_contents(1)
        self.assertGreater(len(toc), 0)

    def test_toc_fields(self):
        entry = self.db.get_table_of_contents(1)[0]
        self.assertIn("name", entry)
        self.assertIn("beg_page", entry)
        self.assertIn("end_page", entry)

    def test_toc_name_is_string(self):
        entry = self.db.get_table_of_contents(1)[0]
        self.assertIsInstance(entry["name"], str)

    def test_toc_pages_ordered(self):
        toc = self.db.get_table_of_contents(1)
        pages = [e["beg_page"] for e in toc]
        self.assertEqual(pages, sorted(pages))

    # ── Chapter marks ─────────────────────────────────────────────────

    def test_chapter_marks_book_1(self):
        marks = self.db.get_chapter_marks(1)
        self.assertGreater(len(marks), 0)

    def test_chapter_marks_fields(self):
        m = self.db.get_chapter_marks(1)[0]
        self.assertIn("wordmark", m)
        self.assertIn("page_no", m)
        self.assertIsInstance(m["wordmark"], str)

    def test_chapter_marks_ordered(self):
        marks = self.db.get_chapter_marks(1)
        pages = [m["page_no"] for m in marks]
        self.assertEqual(pages, sorted(pages))

    # ── Dictionary ─────────────────────────────────────────────────────

    def test_dict_nirodha(self):
        entry = self.db.get_dictionary_entry("nirodha")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["source"], "PTS Dictionary")
        self.assertIn("nirodha", entry["word"])

    def test_dict_unknown_returns_none(self):
        self.assertIsNone(self.db.get_dictionary_entry("xyzzy_not_a_word"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
