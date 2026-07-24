"""
Reusable UI widgets for Tipitaka PTS Browser.

Extracted from extracted_appimage_gui.py to keep the main window
class focused on orchestration rather than widget implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from PyQt6.QtCore import (
    QObject,
    Qt,
    QUrl,
    pyqtProperty,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QFontMetrics,
    QPainter,
)
from PyQt6.QtQml import QQmlContext
from PyQt6.QtQuickWidgets import QQuickWidget
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

# ── Line Number Widget ───────────────────────────────────────


class LineNumberWidget(QWidget):
    """Shows line numbers synchronized with a QTextBrowser."""

    def __init__(self, text_browser: QTextBrowser, parent=None):
        super().__init__(parent)
        self.text_browser = text_browser
        self.line_number_interval = 5
        self.line_number_width = 60
        self.line_numbers_visible = True
        self.setFixedWidth(self.line_number_width)

        v_scrollbar = text_browser.verticalScrollBar()
        v_scrollbar.valueChanged.connect(self.update)
        text_browser.document().contentsChanged.connect(self.update)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.line_numbers_visible:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#f0f0f0"))
        painter.setPen(QColor("#a0a0a0"))
        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())

        line_number_font = QFont("Monospace", 10)
        line_number_font.setWeight(QFont.Weight.Bold)
        painter.setFont(line_number_font)
        painter.setPen(QColor("#000000"))

        doc = self.text_browser.document()
        if not doc:
            painter.end()
            return

        font_metrics = QFontMetrics(line_number_font)
        line_height = font_metrics.height()
        scroll_value = self.text_browser.verticalScrollBar().value()

        block = doc.begin()
        line_number = 0

        while block.isValid():
            text = block.text()
            if text.strip():
                line_number += 1
                if line_number % self.line_number_interval == 0:
                    layout = doc.documentLayout()
                    if layout:
                        block_rect = layout.blockBoundingRect(block)
                        y_pos = block_rect.top() - scroll_value
                        if -50 <= y_pos <= self.height() + 50:
                            number_text = str(line_number)
                            text_width = font_metrics.horizontalAdvance(number_text)
                            bg_x = self.width() - text_width - 10
                            painter.fillRect(
                                bg_x,
                                int(y_pos),
                                text_width + 8,
                                line_height,
                                QColor("#ffffff"),
                            )
                            painter.drawText(
                                5,
                                int(y_pos),
                                self.line_number_width - 10,
                                line_height,
                                Qt.AlignmentFlag.AlignRight
                                | Qt.AlignmentFlag.AlignVCenter,
                                number_text,
                            )
            block = block.next()
        painter.end()

    def sizeHint(self):
        return self.minimumSize()


class PaliTextView(QWidget):
    """Text view with line numbers, wraps a QTextBrowser."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_numbers_visible = True

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.text_browser = QTextBrowser(self)
        self.text_browser.setOpenExternalLinks(False)
        self.text_browser.setFrameShape(QFrame.Shape.NoFrame)
        self.text_browser.setReadOnly(True)

        self.line_numbers = LineNumberWidget(self.text_browser, self)
        layout.addWidget(self.line_numbers)
        layout.addWidget(self.text_browser, 1)

    def setHtml(self, html):
        self.text_browser.setHtml(html)

    def setPlainText(self, text):
        self.text_browser.setPlainText(text)

    def setReadOnly(self, ro):
        self.text_browser.setReadOnly(ro)

    def setPlaceholderText(self, t):
        self.text_browser.setPlaceholderText(t)

    def setOpenExternalLinks(self, e):
        self.text_browser.setOpenExternalLinks(e)

    def setFrameShape(self, s):
        self.text_browser.setFrameShape(s)

    def font(self):
        return self.text_browser.font()

    def setFont(self, f):
        self.text_browser.setFont(f)

    def document(self):
        return self.text_browser.document()

    def toPlainText(self):
        return self.text_browser.toPlainText()

    def verticalScrollBar(self):
        return self.text_browser.verticalScrollBar()

    def set_line_numbers_visible(self, visible: bool):
        self.line_numbers_visible = visible
        self.line_numbers.line_numbers_visible = visible
        self.line_numbers.update()


# ── Navigation Panel ─────────────────────────────────────────


class NavPanel(QWidget):
    """Left panel with navigation tree, bookmarks, and search results."""

    textSelected = pyqtSignal(str)  # emits text_id (citation or #book:NO:PAGE)

    ITEM_KIND = int(Qt.ItemDataRole.UserRole) + 1
    BOOK_NO = int(Qt.ItemDataRole.UserRole) + 2
    PAGE_NO = int(Qt.ItemDataRole.UserRole) + 3
    CHILDREN_KEY = int(Qt.ItemDataRole.UserRole) + 4

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Navigation tree with search filter
        nav_group = QGroupBox("Navegación")
        nav_layout = QVBoxLayout(nav_group)

        self.nav_filter = QLineEdit()
        self.nav_filter.setPlaceholderText("Filtrar navegación…")
        self.nav_filter.textChanged.connect(self._filter_nav_tree)
        nav_layout.addWidget(self.nav_filter)

        self.nav_tree = QTreeWidget()
        self.nav_tree.setHeaderLabels(["Texto"])
        self.nav_tree.setColumnWidth(0, 300)
        self.nav_tree.itemClicked.connect(self._on_nav_clicked)
        self.nav_tree.itemExpanded.connect(self._on_item_expanded)
        nav_layout.addWidget(self.nav_tree)
        layout.addWidget(nav_group)

        # Search results
        search_group = QGroupBox("Resultados de búsqueda")
        search_layout = QVBoxLayout(search_group)
        self.search_results_list = QListWidget()
        self.search_results_list.itemClicked.connect(self._on_search_result_clicked)
        search_layout.addWidget(self.search_results_list)
        layout.addWidget(search_group)

        # Bookmarks
        bm_group = QGroupBox("Marcadores")
        bm_layout = QVBoxLayout(bm_group)
        self.bookmarks_list = QListWidget()
        self.bookmarks_list.itemClicked.connect(self._on_bookmark_clicked)
        bm_layout.addWidget(self.bookmarks_list)
        layout.addWidget(bm_group)

        self._all_tree_items: list[QTreeWidgetItem] = []
        self._tree_data: list = []

    def _on_nav_clicked(self, item: QTreeWidgetItem, column: int):
        book_no = item.data(0, self.BOOK_NO)
        page_no = item.data(0, self.PAGE_NO)
        if book_no is not None and page_no is not None:
            self.textSelected.emit(f"#book:{book_no}:{page_no}")
        elif book_no is not None:
            self.textSelected.emit(f"#book:{book_no}:1")

    def _on_item_expanded(self, item: QTreeWidgetItem):
        """Lazy-load children when a node is expanded."""
        children_key = item.data(0, self.CHILDREN_KEY)
        if children_key and item.childCount() == 0:
            # Children not yet loaded — load from stored tree data
            self._load_children(item, children_key)

    def _load_children(self, parent_item: QTreeWidgetItem, children_data: list):
        """Populate children into a tree item from stored data."""
        for node in children_data:
            text = (node.get("text") or "").strip()
            if not text:
                continue
            display = text[:100] if len(text) > 100 else text
            child = QTreeWidgetItem(parent_item, [display])
            book_no = node.get("book_no")
            page_no = node.get("page_no")
            grandchildren = node.get("children", [])

            if book_no is not None:
                child.setData(0, self.BOOK_NO, book_no)
                if page_no is not None:
                    child.setData(0, self.PAGE_NO, page_no)
                    child.setData(0, self.ITEM_KIND, "sutta")
                else:
                    child.setData(0, self.ITEM_KIND, "book")
            else:
                child.setData(0, self.ITEM_KIND, "group")

            if grandchildren:
                child.setData(0, self.CHILDREN_KEY, grandchildren)
                # Add placeholder so the expand arrow appears
                QTreeWidgetItem(child, ["…"])

            self._all_tree_items.append(child)

    def _on_search_result_clicked(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            text_id = data.get("text_id", "")
            if text_id:
                self.textSelected.emit(text_id)

    def _on_bookmark_clicked(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            text_id = data.get("text_id", "")
            if text_id:
                self.textSelected.emit(text_id)

    def _filter_nav_tree(self, filter_text: str):
        """Filter visible items in the navigation tree."""
        ft = filter_text.lower().strip()
        for i in range(self.nav_tree.topLevelItemCount()):
            self._filter_item(self.nav_tree.topLevelItem(i), ft)

    def _filter_item(self, item: QTreeWidgetItem, ft: str):
        """Recursively show/hide items based on filter."""
        if not ft:
            item.setHidden(False)
            for i in range(item.childCount()):
                self._filter_item(item.child(i), ft)
            return

        text = item.text(0).lower()
        child_match = False
        for i in range(item.childCount()):
            if self._filter_item(item.child(i), ft):
                child_match = True

        matches = ft in text or child_match
        item.setHidden(not matches)
        if matches and child_match:
            item.setExpanded(True)
        return matches

    def set_navigation_tree(self, tree_data: list):
        """Populate navigation tree with lazy loading support."""
        self.nav_tree.clear()
        self._all_tree_items.clear()
        self._tree_data = tree_data

        for root in tree_data:
            for tipitaka in root.get("children", []):
                if "tipitaka" in tipitaka.get("text", "").lower():
                    for pitaka in tipitaka.get("children", []):
                        text = (pitaka.get("text") or "").strip()
                        if not text:
                            continue
                        display = text[:100] if len(text) > 100 else text
                        item = QTreeWidgetItem(self.nav_tree, [display])
                        item.setData(0, self.ITEM_KIND, "pitaka")
                        children = pitaka.get("children", [])
                        if children:
                            item.setData(0, self.CHILDREN_KEY, children)
                            QTreeWidgetItem(item, ["…"])
                        item.setExpanded(True)
                        self._all_tree_items.append(item)
                    break

    def set_search_results(self, results: list):
        """Display search results in the list."""
        self.search_results_list.clear()
        for r in results:
            title = r.get("book_name", "") or f"Book {r.get('book_no', '?')}"
            snippet = r.get("snippet", "")
            label = f"{title} p.{r.get('page_num', '?')}\n{snippet[:150]}"
            item = QListWidgetItem(label)
            text_id = f"#book:{r.get('book_no')}:{r.get('page_num')}"
            r["text_id"] = text_id
            item.setData(Qt.ItemDataRole.UserRole, r)
            self.search_results_list.addItem(item)

    def set_bookmarks(self, bookmarks: list):
        """Display bookmarks."""
        self.bookmarks_list.clear()
        for bm in bookmarks:
            text_id = bm.get("text_id", "")
            note = bm.get("note", "")
            label = f"{text_id} — {note}" if note else text_id
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, bm)
            self.bookmarks_list.addItem(item)


# ── Dictionary Panel ─────────────────────────────────────────


class DictPanel(QWidget):
    """Bottom panel for dictionary lookup."""

    lookupRequested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout()
        self.dict_input = QLineEdit()
        self.dict_input.setPlaceholderText("Buscar palabra en diccionario…")
        self.dict_input.returnPressed.connect(self._on_lookup)
        dict_btn = QPushButton("Buscar")
        dict_btn.clicked.connect(self._on_lookup)
        row.addWidget(self.dict_input)
        row.addWidget(dict_btn)
        layout.addLayout(row)

        self.dict_output = QTextBrowser()
        self.dict_output.setReadOnly(True)
        self.dict_output.setOpenExternalLinks(False)
        layout.addWidget(self.dict_output)

    def _on_lookup(self):
        word = self.dict_input.text().strip()
        if word:
            self.lookupRequested.emit(word)

    def set_result(self, html: str):
        self.dict_output.setHtml(html)

    def lookup_word(self, word: str):
        self.dict_input.setText(word)
        self.lookupRequested.emit(word)


# ── Search Panel ─────────────────────────────────────────────


class SearchPanel(QWidget):
    """Bottom panel for advanced text search."""

    searchRequested = pyqtSignal(str, int)  # query, book_no filter (0=all)
    resultSelected = pyqtSignal(str)  # text_id

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Input row
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar palabra o frase…")
        self.search_input.returnPressed.connect(self._on_search)
        search_btn = QPushButton("Buscar")
        search_btn.clicked.connect(self._on_search)
        search_row.addWidget(self.search_input)
        search_row.addWidget(search_btn)
        layout.addLayout(search_row)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Libro:"))
        self.book_filter = QComboBox()
        self.book_filter.addItem("Todos", 0)
        self.book_filter.setMinimumWidth(150)
        filter_row.addWidget(self.book_filter)
        filter_row.addStretch()
        self.result_count = QLabel("")
        filter_row.addWidget(self.result_count)
        layout.addLayout(filter_row)

        # Results
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self._on_result_clicked)
        layout.addWidget(self.results_list)

    def _on_search(self):
        query = self.search_input.text().strip()
        if query:
            book_no = self.book_filter.currentData()
            self.searchRequested.emit(query, book_no)

    def _on_result_clicked(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            text_id = data.get("text_id", "")
            if text_id:
                self.resultSelected.emit(text_id)

    def set_books(self, books: list):
        """Populate book filter combo."""
        self.book_filter.clear()
        self.book_filter.addItem("Todos", 0)
        for b in books:
            sn = (b.get("s_name") or "").strip()
            bn = b.get("book_no", 0)
            if sn:
                self.book_filter.addItem(f"{bn}: {sn}", bn)

    def set_results(self, results: list, query: str = ""):
        """Display search results."""
        self.results_list.clear()
        for r in results:
            title = r.get("book_name", "") or f"Book {r.get('book_no', '?')}"
            snippet = r.get("snippet", "")
            label = f"{title} p.{r.get('page_num', '?')}\n{snippet[:200]}"
            item = QListWidgetItem(label)
            text_id = f"#book:{r.get('book_no')}:{r.get('page_num')}"
            r["text_id"] = text_id
            item.setData(Qt.ItemDataRole.UserRole, r)
            self.results_list.addItem(item)
        self.result_count.setText(f"{len(results)} resultados")


# ── Apparatus Panel ──────────────────────────────────────────


class ApparatusPanel(QWidget):
    """Panel for displaying apparatus criticus (manuscript variants).

    Supports two modes:
      - set_apparatus(html)        : raw HTML display (backward-compatible)
      - set_apparatus_structured(text) : parses PTS apparatus text and
        renders colour-coded entries with sigla tooltips and filters.
    """

    variantSelected = pyqtSignal(dict)
    siglaFilterChanged = pyqtSignal(str, bool)  # sigla, checked

    # ── Manuscript sigla → full name ─────────────────────────
    SIGLA_NAMES: dict[str, str] = {
        # ── User-specified ──
        "Cb": "Cambridge",
        "Ba": "Bangkok A",
        "Bb": "Bangkok B",
        "Bc": "Bangkok C",
        "L": "London",
        "P": "Paris",
        "R": "Rome",
        "S": "Sri Lanka (Sinhalese)",
        "T": "Thai",
        "U": "Uppsala",
        "V": "Vatican",
        # ── Common PTS / ROTA sigla ──
        "A": "Manuscript A (Sinhalese)",
        "B": "Manuscript B (Burmese)",
        "C": "Manuscript C (Sinhalese)",
        "D": "Manuscript D (Sinhalese)",
        "B1": "Burmese sub-MS 1",
        "B2": "Burmese sub-MS 2",
        "Bp": "Burmese printed edition",
        "Sp": "Sāratthadīpanī-ṭīkā",
        "Sum": "Sumaṅgalavilāsinī",
        "Ch": "Chinese translation",
        "S1": "Sinhalese sub-MS 1",
        "Buddh": "Buddhaghosa commentary",
        "Buddhaghosa": "Buddhaghosa commentary",
        "Faus": "Fausbøll edition",
        "H": "H manuscript",
        "K": "K manuscript",
        "M": "M manuscript",
        "G": "G manuscript",
        "J": "J manuscript",
        "E": "E manuscript",
        "F": "F manuscript",
        "MSS": "Manuscripts",
    }

    # ── Colour palette ───────────────────────────────────────
    COLOR_ADDITION = "#27ae60"  # green
    COLOR_OMISSION = "#e74c3c"  # red
    COLOR_VARIANT = "#2980b9"  # blue
    COLOR_NOTE = "#7f8c8d"  # gray
    COLOR_ENTRY_NUMBER = "#8e44ad"  # purple

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("Apparatus Criticus")
        header.setStyleSheet(
            "font-weight: bold; font-size: 11pt; color: #2c3e50;"
            " padding: 6px 8px; background: #f5f5f5;"
            " border-bottom: 1px solid #ccc;"
        )
        layout.addWidget(header)

        # ── Filter row (hidden until structured data loaded) ──
        self._filter_container = QWidget()
        self._filter_layout = QHBoxLayout(self._filter_container)
        self._filter_layout.setContentsMargins(4, 2, 4, 2)
        self._filter_layout.setSpacing(4)
        filter_label = QLabel("Filtrar:")
        filter_label.setStyleSheet("font-size: 9pt; color: #666;")
        self._filter_layout.addWidget(filter_label)
        self._filter_layout.addStretch()
        self._filter_container.hide()
        layout.addWidget(self._filter_container)

        self._filter_checkboxes: dict[str, QCheckBox] = {}
        self._all_entries: list[dict] = []

        self.apparatus_view = QTextBrowser()
        self.apparatus_view.setReadOnly(True)
        self.apparatus_view.setOpenExternalLinks(False)
        self.apparatus_view.setPlaceholderText(
            "El apparatus criticus de la página actual\n"
            "aparecerá aquí al cargar un texto."
        )
        layout.addWidget(self.apparatus_view)

    # ── Backward-compatible API ──────────────────────────────

    def set_apparatus(self, html: str):
        """Display pre-formatted HTML (backward-compatible)."""
        self._filter_container.hide()
        self._all_entries = []
        if html:
            self.apparatus_view.setHtml(html)
        else:
            self.apparatus_view.setPlainText(
                "No hay apparatus criticus para esta página."
            )

    # ── Structured API ───────────────────────────────────────

    def set_apparatus_structured(self, text: str):
        """Parse decoded apparatus text and render with formatting."""
        if not text or not text.strip():
            self.set_apparatus("")
            return

        entries = self._parse_entries(text)
        self._all_entries = entries
        self._rebuild_filters(entries)
        self._render_entries(entries)

    # ── Parsing ──────────────────────────────────────────────

    def _parse_entries(self, text: str) -> list[dict]:
        """Split apparatus text into numbered entries and classify."""
        import re

        # Split on numbered entry markers at line starts or after whitespace
        # Pattern: whitespace + digits + whitespace (entry boundary)
        parts = re.split(r"(?:(?<=^)|(?<=\n)|(?<=  ))(\d+)\s+(?=[A-Za-z(])", text)

        entries: list[dict] = []

        if not parts:
            return entries

        # parts[0] is text before first number (often empty)
        i = 1 if parts[0].strip() == "" else 0

        while i < len(parts):
            if i + 1 >= len(parts):
                break
            # parts[i] is the entry number, parts[i+1] is entry body
            num_str = parts[i]
            body = parts[i + 1].strip()
            try:
                entry_no = int(num_str)
            except ValueError:
                i += 1
                continue

            entry_type = self._classify_entry(body)
            sigla = self._extract_sigla(body)
            entries.append(
                {
                    "number": entry_no,
                    "text": body,
                    "type": entry_type,
                    "sigla": sigla,
                }
            )
            i += 2

        return entries

    _ADD_PATTERN = None
    _OMIT_PATTERN = None

    @classmethod
    def _get_add_pattern(cls):
        if cls._ADD_PATTERN is None:
            import re

            cls._ADD_PATTERN = re.compile(
                r"\b(adds?|inserts?|after\s+.+\s+(?:adds?|inserts?))\b",
                re.IGNORECASE,
            )
        return cls._ADD_PATTERN

    @classmethod
    def _get_omit_pattern(cls):
        if cls._OMIT_PATTERN is None:
            import re

            cls._OMIT_PATTERN = re.compile(
                r"\b(omits?|omit|is\s+wanting|omitted)\b",
                re.IGNORECASE,
            )
        return cls._OMIT_PATTERN

    @staticmethod
    def _classify_entry(body: str) -> str:
        """Classify entry as: addition, omission, note, variant."""
        import re

        # Notes / editorial comments
        if re.search(r"\bBuddhaghosa\b", body, re.IGNORECASE):
            return "note"
        if re.search(r"\bBuddh\.?\s*:", body):
            return "note"
        if re.search(r"\b\(sic\)\b", body):
            return "note"
        # If the entry is mostly parenthetical
        if body.startswith("(") and body.endswith(")"):
            return "note"
        # If entry is editorial (no sigla, just commentary)
        if re.match(r"^(From|It is evident|The|As to|In)\s", body):
            return "note"

        # Additions
        if ApparatusPanel._get_add_pattern().search(body):
            return "addition"

        # Omissions
        if ApparatusPanel._get_omit_pattern().search(body):
            return "omission"

        # Default: alternative readings
        return "variant"

    # Compound sigla → component letters they imply
    _COMPOUND_SIGLA: dict[str, list[str]] = {
        "ACD": ["A", "C", "D"],
        "ABC": ["A", "B", "C"],
        "ABD": ["A", "B", "D"],
        "BCD": ["A", "B", "C", "D"],  # sic: 'BCD' = all four
        "AB": ["A", "B"],
        "AC": ["A", "C"],
        "AD": ["A", "D"],
        "BC": ["B", "C"],
        "BD": ["B", "D"],
        "CD": ["C", "D"],
    }

    @staticmethod
    def _extract_sigla(body: str) -> list[str]:
        """Extract manuscript sigla from an entry body."""
        import re

        # Known sigla (ordered by length descending to match greedily)
        known = [
            "Buddhaghosa",
            "Buddh",
            "MSS",
            "B1",
            "B2",
            "S1",
            "Sp",
            "Bp",
            "Sum",
            "Ch",
            "Cks",
            "Ck",
            "Cs",
            "Bm",
            "Bd",
            "Bi",
            "Ba",
            "Bds",
            "Bai",
            "Bmr",
            "Cv",
            "Sk",
            "Skgn",
            "Br",
            "Cf",
            "So",
            "Si",
            "Sd",
            "SS",
            "Ssp",
            "Ca",
            "Bid",
            "Faus",
        ]

        # Individual letter sigla (checked after multi-char to avoid
        # matching 'A' inside 'Ba', 'Ca', etc.)
        letters = [
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "J",
            "K",
            "L",
            "M",
            "P",
            "R",
            "S",
            "T",
            "U",
            "V",
        ]

        found: list[str] = []

        # ── Pass 1: known multi-char sigla ──
        for siglum in known:
            pattern = re.compile(
                r"\b" + re.escape(siglum) + r"\b",
                re.IGNORECASE,
            )
            if pattern.search(body):
                found.append(siglum)

        # ── Pass 2: detect compound sigla (uppercase runs of 2-4 letters)
        #   and add their component letters.
        #   Avoid false positives: skip runs that contain a dot (A.D.),
        #   are part of known sigla, or look like abbreviations.
        #   Allow trailing period (BC. → match BC).
        compound_re = re.compile(r"(?<![.A-Za-z])([A-Z]{2,4})\.?(?![A-Za-z])")
        extra_letters: set[str] = set()
        for m in compound_re.finditer(body):
            compound = m.group(1)
            # Skip known sigla already matched
            if compound in known:
                continue
            # Skip sequences that include digits or look like dates
            if re.search(r"\d", compound):
                continue
            # Check the compound mapping
            if compound in ApparatusPanel._COMPOUND_SIGLA:
                for letter in ApparatusPanel._COMPOUND_SIGLA[compound]:
                    extra_letters.add(letter)
            else:
                # Unknown compound — add as a siglum itself
                if compound not in found:
                    found.append(compound)

        # ── Pass 3: individual letters (standalone, not inside compounds) ──
        for letter in letters:
            if letter in extra_letters:
                # Already covered by a compound — still add for filtering
                if letter not in found:
                    found.append(letter)
                continue
            # Match letter as standalone (not part of a longer word or compound).
            # Use \b for Unicode-aware word boundary (avoids matching
            # 'S' inside 'Sāriputta', 'A' inside 'Anno', etc.).
            # Also allow trailing period (B. → match B).
            pattern = re.compile(
                r"\b" + re.escape(letter) + r"\.?\b",
            )
            if pattern.search(body):
                found.append(letter)

        # Sort by appearance order in the text
        def _find_pos(s: str) -> int:
            m = re.search(
                r"(?<![A-Za-z])" + re.escape(s) + r"(?![A-Za-z])",
                body,
                re.IGNORECASE,
            )
            return m.start() if m else 99999

        found.sort(key=_find_pos)
        return found

    # ── Filter UI ────────────────────────────────────────────

    def _rebuild_filters(self, entries: list[dict]):
        """(Re)build the row of filter checkboxes from all sigla found."""

        # Clear old checkboxes (keep the "Filtrar:" label)
        for cb in self._filter_checkboxes.values():
            cb.deleteLater()
        self._filter_checkboxes.clear()

        # Collect unique sigla across all entries
        all_sigla: list[str] = []
        seen: set[str] = set()
        for entry in entries:
            for s in entry.get("sigla", []):
                if s not in seen:
                    seen.add(s)
                    all_sigla.append(s)

        if not all_sigla:
            self._filter_container.hide()
            return

        # Remove stretch and re-add at end
        while self._filter_layout.count() > 1:
            item = self._filter_layout.takeAt(1)
            w = item.widget()
            if w:
                w.deleteLater()

        for siglum in all_sigla:
            name = self.SIGLA_NAMES.get(siglum, siglum)
            cb = QCheckBox(siglum)
            cb.setChecked(True)
            cb.setToolTip(name)
            cb.setStyleSheet("font-size: 8.5pt; padding: 1px 3px; spacing: 2px;")
            cb.toggled.connect(
                lambda checked, s=siglum: self._on_filter_toggled(s, checked)
            )
            self._filter_checkboxes[siglum] = cb
            self._filter_layout.addWidget(cb)

        self._filter_layout.addStretch()
        self._filter_container.show()

    def _on_filter_toggled(self, siglum: str, checked: bool):
        """Re-render entries when a filter checkbox is toggled."""
        self.siglaFilterChanged.emit(siglum, checked)
        self._render_entries(self._all_entries)

    def _entry_passes_filter(self, entry: dict) -> bool:
        """Check whether an entry should be visible given active filters."""
        entry_sigla = set(entry.get("sigla", []))
        if not entry_sigla:
            # Entries with no detected sigla (pure notes) always shown
            return True
        for siglum, cb in self._filter_checkboxes.items():
            if siglum in entry_sigla and not cb.isChecked():
                return False
        return True

    # ── Rendering ────────────────────────────────────────────

    def _render_entries(self, entries: list[dict]):
        """Build HTML from parsed entries and set on the text browser."""
        import html as _html

        if not entries:
            self.apparatus_view.setPlainText(
                "No hay apparatus criticus para esta página."
            )
            return

        visible_entries = [e for e in entries if self._entry_passes_filter(e)]

        if not visible_entries:
            self.apparatus_view.setHtml(
                "<div style='color:#999; font-style:italic; padding:8px;'>"
                "Todos los manuscritos están filtrados.</div>"
            )
            return

        colour_map = {
            "addition": self.COLOR_ADDITION,
            "omission": self.COLOR_OMISSION,
            "variant": self.COLOR_VARIANT,
            "note": self.COLOR_NOTE,
        }

        label_map = {
            "addition": "[+] Adición",
            "omission": "[−] Omisión",
            "variant": "[~] Variante",
            "note": "[i] Nota",
        }

        parts: list[str] = []
        parts.append(
            "<div style='"
            "font-family: 'Noto Sans', 'FreeSerif', 'Gentium', serif;"
            "font-size: 11pt; line-height: 1.7;"
            "padding: 4px 8px;"
            "'>"
        )

        for entry in visible_entries:
            entry_type = entry["type"]
            colour = colour_map.get(entry_type, self.COLOR_VARIANT)
            number = entry["number"]
            body = entry["text"]

            # Escape and format body text
            escaped_body = _html.escape(body)
            # Convert newlines within an entry to <br>
            escaped_body = escaped_body.replace("\n", "<br>")

            # Highlight sigla within the body
            highlighted = self._highlight_sigla(escaped_body, entry.get("sigla", []))

            # Entry number badge
            num_span = (
                f"<span style='"
                f"display:inline-block; min-width:22px;"
                f"color:{self.COLOR_ENTRY_NUMBER}; font-weight:bold;"
                f"font-size:10pt; margin-right:4px;'"
                f">{number}</span>"
            )

            # Type badge
            type_badge = (
                f"<span style='"
                f"display:inline-block;"
                f"background:{colour}; color:#fff;"
                f"font-size:7.5pt; padding:1px 5px; border-radius:3px;"
                f"margin-right:6px; vertical-align:middle;'"
                f">{label_map.get(entry_type, '')}</span>"
            )

            # Sigla list (compact)
            sigla_spans = ""
            for s in entry.get("sigla", []):
                name = self.SIGLA_NAMES.get(s, s)
                sigla_spans += (
                    f"<span style='"
                    f"background:#eee; color:#333;"
                    f"font-size:8pt; padding:0px 4px; border-radius:2px;"
                    f"margin-right:3px;'"
                    f" title='{_html.escape(name)}'"
                    f">{_html.escape(s)}</span>"
                )

            parts.append(
                f"<div style='"
                f"border-left:3px solid {colour};"
                f"padding: 4px 0 4px 8px;"
                f"margin-bottom: 6px;"
                f"background: {colour}08;"
                f"font-family: 'Noto Sans', 'FreeSerif', 'Gentium', serif;"
                f"font-size: 10.5pt; line-height: 1.65;"
                f"'>"
                f"{num_span}{type_badge}{sigla_spans}"
                f"<div style='margin-top:2px;'>{highlighted}</div>"
                f"</div>"
            )

        parts.append("</div>")
        self.apparatus_view.setHtml("".join(parts))

    def _highlight_sigla(self, html_body: str, sigla: list[str]) -> str:
        """Wrap known sigla in <span> tags with tooltips inside escaped HTML."""
        import re

        # Sort by length (longest first) to avoid partial replacements
        for s in sorted(sigla, key=len, reverse=True):
            name = self.SIGLA_NAMES.get(s, s)
            escaped_s = re.escape(s)
            # Replace siglum as a whole word with a styled span + tooltip
            replacement = (
                f"<span style='"
                f"background:#e8e8e8; color:#2c3e50;"
                f"font-weight:bold; font-size:9.5pt;"
                f"padding:0 3px; border-radius:2px;"
                f"cursor:help;'"
                f" title='{name}'"
                f">\\1</span>"
            )
            # Use word-boundary match within the already-escaped HTML
            html_body = re.sub(
                rf"\b({escaped_s})\b",
                replacement,
                html_body,
            )

        return html_body


# ── Settings Management ──────────────────────────────────────


@dataclass
class SettingsState:
    font_family: str = "Sans Serif"
    font_size: int = 16
    line_spacing: float = 1.5
    layout_preset: str = "balanced"
    show_line_numbers: bool = True
    word_wrap: bool = True
    default_edition: str = "mula"
    search_mode: str = "text"
    max_search_results: int = 50
    show_thai_script: bool = False
    dictionary_sources: list = None

    def __post_init__(self):
        if self.dictionary_sources is None:
            self.dictionary_sources = ["PTS", "CPD"]


class SettingsBridge(QObject):
    """Bridge between QML settings dialog and Python backend."""

    settingsApplied = pyqtSignal()
    closeRequested = pyqtSignal()

    def __init__(
        self,
        parent_window: QWidget | None = None,
        default_font: str = "Sans Serif",
    ) -> None:
        super().__init__()
        fonts = sorted(QFontDatabase.families())
        self._parent_window = parent_window
        self._fonts = fonts
        self._state = SettingsState(
            font_family=default_font
            if default_font in fonts
            else (fonts[0] if fonts else "Sans Serif"),
        )

    @pyqtProperty("QVariant", constant=True)
    def availableFonts(self):
        return self._fonts

    @pyqtProperty(str, constant=False)
    def currentFontFamily(self):
        return self._state.font_family

    @pyqtProperty(int, constant=False)
    def currentFontSize(self):
        return self._state.font_size

    @pyqtProperty(float, constant=False)
    def currentLineSpacing(self):
        return self._state.line_spacing

    @pyqtProperty(str, constant=False)
    def currentLayoutPreset(self):
        return self._state.layout_preset

    @pyqtProperty(str, constant=False)
    def currentAiServiceName(self):
        return "gpt-5.4"

    @pyqtProperty(str, constant=False)
    def currentAiEndpointUrl(self):
        return "https://example.invalid/chat/completions"

    @pyqtProperty(str, constant=False)
    def currentAiToken(self):
        return ""

    @pyqtSlot()
    def cancelSettings(self):
        self.closeRequested.emit()

    @pyqtSlot(str, int, float, str, str, str, str)
    def applySettings(
        self,
        font_family: str,
        font_size: int,
        line_spacing: float,
        layout_preset: str,
        ai_service_name: str,
        ai_endpoint_url: str,
        ai_token: str,
    ):
        self._state = SettingsState(
            font_family=font_family,
            font_size=font_size,
            line_spacing=line_spacing,
            layout_preset=layout_preset,
        )
        self.settingsApplied.emit()
        self.closeRequested.emit()

    def state(self) -> SettingsState:
        return self._state


# ── QML Dialog Wrapper ───────────────────────────────────────


class QmlDialog(QDialog):
    """Wrapper to host a QML-based dialog inside a PyQt6 widget."""

    def __init__(
        self,
        qml_path,
        title: str,
        width: int,
        height: int,
        parent: QWidget | None = None,
        context_properties: dict | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(width, height)
        self.widget = QQuickWidget(self)
        self.widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        self.widget.setClearColor(self.palette().window().color())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget)
        if context_properties:
            ctx = self.widget.rootContext()
            for key, value in context_properties.items():
                ctx.setContextProperty(key, value)
        self.widget.setSource(QUrl.fromLocalFile(str(qml_path)))

    def root_context(self) -> QQmlContext:
        return self.widget.rootContext()

    def root_object(self):
        return self.widget.rootObject()


# ── Main Toolbar ─────────────────────────────────────────────


class MainToolbar:
    """Builder for the main application toolbar."""

    @staticmethod
    def build(
        window, on_citation_entered, on_edition_changed, on_thai_toggled, on_search
    ) -> QWidget:
        """Create and return the main toolbar with styled buttons."""
        toolbar = QWidget(window)
        toolbar.setObjectName("toolbar_container")
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Navigation: prev / next
        prev_btn = QPushButton("◀")
        prev_btn.setToolTip("Página anterior (Alt+←)")
        prev_btn.setFixedWidth(32)
        prev_btn.setAccessibleName("Página anterior")
        layout.addWidget(prev_btn)

        next_btn = QPushButton("▶")
        next_btn.setToolTip("Página siguiente (Alt+→)")
        next_btn.setFixedWidth(32)
        next_btn.setAccessibleName("Página siguiente")
        layout.addWidget(next_btn)

        layout.addWidget(_vsep())

        # Citation input
        layout.addWidget(QLabel("Cita:"))
        citation_input = QLineEdit()
        citation_input.setPlaceholderText("M I 3, Sn 25, Vin I 1…")
        citation_input.setFixedWidth(180)
        citation_input.setAccessibleName("Citación PTS")
        citation_input.setAccessibleDescription(
            "Introduce una citación PTS como M I 3 para cargar un texto"
        )
        citation_input.returnPressed.connect(on_citation_entered)
        layout.addWidget(citation_input)

        go_btn = QPushButton("Cargar")
        go_btn.setToolTip("Cargar texto por citación PTS (Enter)")
        go_btn.setAccessibleName("Cargar texto")
        go_btn.clicked.connect(on_citation_entered)
        layout.addWidget(go_btn)

        layout.addWidget(_vsep())

        # Edition selector
        layout.addWidget(QLabel("Edición:"))
        edition_combo = QComboBox()
        edition_combo.addItems(["ROTA – Tipiṭaka", "ROTB – Aṭṭhakathā"])
        edition_combo.setToolTip("Cambiar entre Tipiṭaka (ROTA) y Comentarios (ROTB)")
        edition_combo.setAccessibleName("Selección de edición")
        edition_combo.currentIndexChanged.connect(on_edition_changed)
        layout.addWidget(edition_combo)

        layout.addWidget(_vsep())

        # Thai script toggle
        thai_toggle = QPushButton("ไทย")
        thai_toggle.setCheckable(True)
        thai_toggle.setToolTip(
            "Mostrar/ocultar texto en escritura tailandesa junto al Pāli romanizado"
        )
        thai_toggle.setFixedWidth(40)
        thai_toggle.setAccessibleName("Alternar escritura tailandesa")
        thai_toggle.toggled.connect(on_thai_toggled)
        layout.addWidget(thai_toggle)

        layout.addStretch()

        # Search
        search_field = QLineEdit()
        search_field.setPlaceholderText("Buscar en el Canon Pāli…")
        search_field.setFixedWidth(220)
        search_field.setAccessibleName("Búsqueda en textos")
        search_field.setAccessibleDescription(
            "Busca palabras en el Tipiṭaka. Usa FTS5 para resultados instantáneos."
        )
        search_field.returnPressed.connect(lambda: on_search(search_field.text()))
        layout.addWidget(search_field)

        search_btn = QPushButton("⌕")
        search_btn.setToolTip("Buscar en el Canon Pāli (FTS5)")
        search_btn.setFixedWidth(32)
        search_btn.setAccessibleName("Buscar")
        search_btn.clicked.connect(lambda: on_search(search_field.text()))
        layout.addWidget(search_btn)

        # Store references for external access
        toolbar.prev_btn = prev_btn
        toolbar.next_btn = next_btn
        toolbar.citation_input = citation_input
        toolbar.edition_combo = edition_combo
        toolbar.thai_toggle = thai_toggle
        toolbar.search_field = search_field

        return toolbar


def _vsep() -> QFrame:
    """Create a vertical separator line."""
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.VLine)
    sep.setFrameShadow(QFrame.Shadow.Sunken)
    sep.setFixedWidth(1)
    return sep


# ── Error Dialog ─────────────────────────────────────────────


def show_error_dialog(parent: QWidget, title: str, message: str, details: str = ""):
    """Show an error dialog with copy-to-clipboard option."""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    if details:
        msg.setDetailedText(details)
    copy_btn = msg.addButton("Copiar error", QMessageBox.ButtonRole.ActionRole)
    msg.addButton(QMessageBox.StandardButton.Ok)
    msg.exec()
