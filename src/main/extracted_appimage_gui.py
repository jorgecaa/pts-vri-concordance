"""
Tipitaka PTS Browser — Clean, intuitive reading interface.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QEvent, Qt, QTimer, QUrl
from PyQt6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QFont,
    QFontDatabase,
    QFontMetrics,
    QHelpEvent,
    QIcon,
    QKeySequence,
    QPalette,
    QShortcut,
    QTextCursor,
    QTextDocument,
)
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QCompleter,
    QDockWidget,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTextBrowser,
    QToolTip,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError:  # WebEngine optional — DPD panel just stays unavailable
    QWebEngineView = None

# Local DPD webapp (dpd-webapp.service, uvicorn). Same backend the official DPD
# Chrome extension talks to; /search_html returns a full, self-contained page.
DPD_WEBAPP_URL = "http://127.0.0.1:8080"


class DpdThemeManager:
    """Owns the DPD dictionary panel's theming, end to end.

    The webapp's dpd.css is driven by CSS variables (--light, --dark, --primary,
    --primary-alt, --primary-text, --freq0..10, …); a theme just overrides those
    on the page root. "default"/"dark" reuse the webapp's own styling (dark = its
    native `dark-mode` class); the site-flavoured themes set explicit colours,
    like the extension.

    It also owns the button-contrast fix: the webapp colours button text with
    --dark / --light, which can become invisible against the --primary /
    --primary-alt button background on some themes. This class injects a
    dedicated CSS rule whose colour is computed per theme (luminance-based
    contrast, ported from the extension's getContrastText) so buttons always
    have a readable colour.
    """

    # Order = menu order. label first, then theme colours.
    THEMES: dict[str, dict] = {
        "auto": {"label": "Automático (según la app)"},
        "default": {"label": "DPD (claro)"},
        "dark": {"label": "DPD (oscuro)"},
        "dpr": {
            "label": "Digital Pāḷi Reader",
            "bg": "#FFFFDD",
            "text": "hsl(198, 100%, 5%)",
            "primary": "hsl(198, 100%, 50%)",
            "font": '"Noto Sans", sans-serif',
        },
        "suttacentral": {
            "label": "SuttaCentral",
            "bg": "#fff8f3",
            "text": "rgb(32, 27, 19)",
            "primary": "#c68b05",
            "font": '"Skolar Sans PE Variable", sans-serif',
        },
        "suttacentral_dark": {
            "label": "SuttaCentral (oscuro)",
            "bg": "#414141",
            "text": "#cccccc",
            "primary": "#c68b05",
            "font": '"Skolar Sans PE Variable", sans-serif',
        },
        "tbw_light": {
            "label": "The Buddha's Words",
            "bg": "#ffffff",
            "text": "#000000",
            "primary": "hsl(198, 100%, 50%)",
            "font": "URWPalladioITU, serif",
        },
        "tbw_dark": {
            "label": "The Buddha's Words (oscuro)",
            "bg": "#141516",
            "text": "#ffffff",
            "primary": "hsl(198, 100%, 50%)",
            "font": "URWPalladioITU, serif",
        },
        "vri": {
            "label": "Vipassana Research Institute",
            "bg": "#ffffff",
            "text": "#4f4d47",
            "primary": "#b78730",
            "font": "'Maitree', 'Gill Sans', Calibri, sans-serif",
            "fontSize": "16px",
        },
        # tipitaka.lk is a Vuetify app; bg/text below are its exact Vuetify
        # light/dark application colours (from the site's own app.css /
        # chunk-vendors.css). The accent is Vuetify's default primary — the
        # site's custom primary is injected at runtime (vuetify-theme-stylesheet)
        # and isn't present in the linked CSS, so it can't be read statically.
        "tipitakalk": {
            "label": "Tipiṭaka.lk (claro)",
            "bg": "#ffffff",
            "text": "rgba(0, 0, 0, 0.87)",
            "primary": "#1976d2",
            "font": '"Roboto", sans-serif',
            "fontSize": "16px",
        },
        "tipitakalk_dark": {
            "label": "Tipiṭaka.lk (oscuro)",
            "bg": "#121212",
            "text": "#ffffff",
            "primary": "#2196f3",
            "font": '"Roboto", sans-serif',
            "fontSize": "16px",
        },
    }

    # Colour helpers + applyTheme, ported from the extension's themes.js but
    # targeting the webapp page root (document.documentElement) instead of the
    # injected panel element, with chrome.* / host-site detection removed.
    # Idempotent: safe to re-inject on every page load.
    _JS = r"""
(function () {
  function parseHSL(colorStr) {
    var el = document.createElement('div');
    el.style.color = colorStr; document.body.appendChild(el);
    var c = getComputedStyle(el).color; document.body.removeChild(el);
    var m = c.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (!m) return { h: 198, s: 100, l: 50 };
    var r = m[1] / 255, g = m[2] / 255, b = m[3] / 255;
    var mx = Math.max(r, g, b), mn = Math.min(r, g, b), h, s, l = (mx + mn) / 2;
    if (mx === mn) { h = s = 0; }
    else {
      var d = mx - mn;
      s = l > 0.5 ? d / (2 - mx - mn) : d / (mx + mn);
      if (mx === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
      else if (mx === g) h = ((b - r) / d + 2) / 6;
      else h = ((r - g) / d + 4) / 6;
    }
    return { h: Math.round(h * 360), s: Math.round(s * 100), l: Math.round(l * 100) };
  }
  function hsl(h, s, l, a) {
    return a != null ? 'hsla(' + h + ',' + s + '%,' + l + '%,' + a + ')'
                     : 'hsl(' + h + ',' + s + '%,' + l + '%)';
  }
  function freq(p) {
    var o = {};
    for (var i = 0; i <= 10; i++) o['--freq' + i] = hsl(p.h, p.s, 50, i === 10 ? 1 : i / 10);
    return o;
  }
  // Luminance-based contrast colour for button text (extension's getContrastText).
  function contrastText(colorStr) {
    var el = document.createElement('div');
    el.style.color = colorStr; document.body.appendChild(el);
    var c = getComputedStyle(el).color; document.body.removeChild(el);
    var m = c.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (!m) return '#ffffff';
    var r = +m[1], g = +m[2], b = +m[3];
    if (r < 30 && g < 30 && b < 30) return '#ffffff';
    var lum = 0.2126 * (r / 255) + 0.7152 * (g / 255) + 0.0722 * (b / 255);
    return lum > 0.35 ? '#000000' : '#ffffff';
  }
  // Dedicated rule so DPD buttons always get a readable colour: the webapp uses
  // --dark / --light for button text, which can vanish on the --primary /
  // --primary-alt button background; we override with a computed-contrast var
  // (falling back to the native colour when no theme is active).
  function ensureButtonStyle() {
    if (document.getElementById('dpd-btn-contrast')) return;
    var st = document.createElement('style');
    st.id = 'dpd-btn-contrast';
    st.textContent =
      'a.dpd-button{color:var(--dpd-btn-text,var(--dark))!important;}' +
      'a.dpd-button.active,a.dpd-button:hover,a.dpd-button.play:hover' +
      '{color:var(--dpd-btn-text-active,var(--light))!important;}';
    document.head.appendChild(st);
  }
  window.__dpdSetProps = window.__dpdSetProps || [];
  window.__dpdApplyTheme = function (key, themes) {
    ensureButtonStyle();
    var root = document.documentElement;
    window.__dpdSetProps.forEach(function (p) { root.style.removeProperty(p); });
    window.__dpdSetProps = [];
    root.style.removeProperty('font-family');
    root.style.removeProperty('font-size');
    if (key === 'default' || key === 'dark') {
      root.classList.toggle('dark-mode', key === 'dark');
      return;
    }
    root.classList.remove('dark-mode');
    var t = themes[key];
    if (!t) return;
    function set(k, v) { root.style.setProperty(k, v); window.__dpdSetProps.push(k); }
    var bg = parseHSL(t.bg), tx = parseHSL(t.text), pr = parseHSL(t.primary);
    var primaryStr = hsl(pr.h, pr.s, pr.l);
    var primaryAltStr = hsl((pr.h + 7) % 360, pr.s, Math.max(0, pr.l - 10));
    set('--light', hsl(bg.h, bg.s, bg.l));
    set('--light-shade', hsl(bg.h, bg.s, Math.max(0, bg.l + (bg.l > 50 ? -2 : 2))));
    set('--dark', hsl(tx.h, tx.s, tx.l));
    set('--dark-shade', hsl(tx.h, tx.s, tx.l + (tx.l > 50 ? -2 : 2)));
    set('--primary', primaryStr);
    set('--primary-alt', primaryAltStr);
    set('--primary-text', hsl((pr.h + 7) % 360, Math.max(0, pr.s - 21), Math.max(0, pr.l - 2)));
    set('--dpd-btn-text', contrastText(primaryStr));
    set('--dpd-btn-text-active', contrastText(primaryAltStr));
    var f = freq(pr);
    Object.keys(f).forEach(function (k) { set(k, f[k]); });
    if (t.font) root.style.fontFamily = t.font;
    if (t.fontSize) root.style.fontSize = t.fontSize;
  };
})();
"""

    def __init__(self, view) -> None:
        self._view = view  # QWebEngineView, or None when WebEngine is missing
        self.theme = "auto"  # "auto" follows the app's light/dark flag

    def items(self) -> list[tuple[str, str]]:
        """(key, menu label) pairs, in menu order."""
        return [(k, s["label"]) for k, s in self.THEMES.items()]

    def apply(self, app_is_dark: bool) -> None:
        """(Re)apply the current theme to the panel. Call after each navigation."""
        if self._view is None:
            return
        import json

        key = self.theme
        if key == "auto":
            key = "dark" if app_is_dark else "default"
        self._view.page().runJavaScript(
            self._JS
            + f"\nwindow.__dpdApplyTheme({json.dumps(key)}, "
            + f"{json.dumps(self.THEMES)});"
        )


from .citation_parser import PTSCitationParser
from .database import ROTA_TO_ROTB, TipitakaDatabase
from .export import export_html, export_text
from .i18n import get_language, set_language
from .ui_widgets import LineNumberWidget, show_error_dialog

# ── Book metadata ────────────────────────────────────────────

_BOOKS = {
    1: ("Vinaya Piṭaka", "Mahāvagga", "Vin I"),
    2: ("Vinaya Piṭaka", "Cūḷavagga", "Vin II"),
    3: ("Vinaya Piṭaka", "Suttavibhaṅga I", "Vin III"),
    4: ("Vinaya Piṭaka", "Suttavibhaṅga II", "Vin IV"),
    5: ("Vinaya Piṭaka", "Parivāra", "Vin V"),
    6: ("Dīgha Nikāya", "Sīlakkhandha Vagga", "DN I"),
    7: ("Dīgha Nikāya", "Mahā Vagga", "DN II"),
    8: ("Dīgha Nikāya", "Pāthika Vagga", "DN III"),
    9: ("Majjhima Nikāya", "Mūlapaṇṇāsa", "MN I"),
    10: ("Majjhima Nikāya", "Majjhimapaṇṇāsa", "MN II"),
    11: ("Majjhima Nikāya", "Uparipaṇṇāsa", "MN III"),
    12: ("Saṃyutta Nikāya", "Sagāthā Vagga", "SN I"),
    13: ("Saṃyutta Nikāya", "Nidāna Vagga", "SN II"),
    14: ("Saṃyutta Nikāya", "Khandha Vagga", "SN III"),
    15: ("Saṃyutta Nikāya", "Saḷāyatana Vagga", "SN IV"),
    16: ("Saṃyutta Nikāya", "Mahā Vagga", "SN V"),
    17: ("Aṅguttara Nikāya", "Ekaka Nipāta", "AN I"),
    18: ("Aṅguttara Nikāya", "Duka Nipāta", "AN II"),
    19: ("Aṅguttara Nikāya", "Tika Nipāta", "AN III"),
    20: ("Aṅguttara Nikāya", "Catukka Nipāta", "AN IV"),
    21: ("Aṅguttara Nikāya", "Pañcaka Nipāta", "AN V"),
    22: ("Khuddaka Nikāya", "Khuddakapāṭha", "Khp"),
    23: ("Khuddaka Nikāya", "Dhammapada", "Dhp"),
    24: ("Khuddaka Nikāya", "Udāna", "Ud"),
    25: ("Khuddaka Nikāya", "Itivuttaka", "It"),
    26: ("Khuddaka Nikāya", "Suttanipāta", "Sn"),
    27: ("Khuddaka Nikāya", "Vimānavatthu", "Vv"),
    28: ("Khuddaka Nikāya", "Petavatthu", "Pv"),
    29: ("Khuddaka Nikāya", "Theragāthā & Therīgāthā", "Th & Thī"),
    # Source mislabels book 30 as "Th & Th"; it is actually Jātaka vol. I
    # (Nidānakathā + Ekanipāta). The Jātaka sequence runs 30→35 = Ja I→VI.
    30: ("Khuddaka Nikāya", "Jātaka I (Nidānakathā, Ekanipāta)", "Ja I"),
    31: ("Khuddaka Nikāya", "Jātaka II", "Ja II"),
    32: ("Khuddaka Nikāya", "Jātaka III", "Ja III"),
    33: ("Khuddaka Nikāya", "Jātaka IV", "Ja IV"),
    34: ("Khuddaka Nikāya", "Jātaka V", "Ja V"),
    35: ("Khuddaka Nikāya", "Jātaka VI", "Ja VI"),
    36: ("Khuddaka Nikāya", "Mahāniddesa", "Nidd I"),
    37: ("Khuddaka Nikāya", "Cūḷaniddesa", "Nidd II"),
    38: ("Khuddaka Nikāya", "Paṭisambhidāmagga I", "Paṭis I"),
    39: ("Khuddaka Nikāya", "Paṭisambhidāmagga II", "Paṭis II"),
    40: ("Khuddaka Nikāya", "Apadāna", "Ap"),
    41: ("Khuddaka Nikāya", "Buddhavaṃsa", "Bv"),
    42: ("Khuddaka Nikāya", "Cariyāpiṭaka", "Cp"),
    43: ("Abhidhamma Piṭaka", "Dhammasaṅgaṇī", "Dhs"),
    44: ("Abhidhamma Piṭaka", "Vibhaṅga", "Vibh"),
    45: ("Abhidhamma Piṭaka", "Dhātukathā", "Dhātuk"),
    46: ("Abhidhamma Piṭaka", "Puggalapaññatti", "Pp"),
    47: ("Abhidhamma Piṭaka", "Kathāvatthu", "Kv"),
    48: ("Abhidhamma Piṭaka", "Yamaka I", "Yam I"),
    49: ("Abhidhamma Piṭaka", "Yamaka II", "Yam II"),
    50: ("Abhidhamma Piṭaka", "Paṭṭhāna — Duka", "Dukap"),
    51: ("Abhidhamma Piṭaka", "Paṭṭhāna — Tika I", "Tikap I"),
    52: ("Abhidhamma Piṭaka", "Paṭṭhāna — Tika II", "Tikap II"),
    53: ("Abhidhamma Piṭaka", "Paṭṭhāna — Tika III", "Tikap III"),
}

_COLLECTIONS = [
    ("Vinaya Piṭaka", "Reglas monásticas", [1, 2, 3, 4, 5]),
    ("Dīgha Nikāya", "Discursos largos", [6, 7, 8]),
    ("Majjhima Nikāya", "Discursos medios", [9, 10, 11]),
    ("Saṃyutta Nikāya", "Discursos temáticos", [12, 13, 14, 15, 16]),
    ("Aṅguttara Nikāya", "Discursos numéricos", [17, 18, 19, 20, 21]),
    ("Khuddaka Nikāya", "Colección menor", [22, 23, 24, 25, 26]),
]


class TipitakaMainWindow(QMainWindow):
    """Intuitive, reading-focused Tipitaka browser."""

    def __init__(self, root_dir: Path) -> None:
        super().__init__()
        self._root_dir = root_dir
        self._db: TipitakaDatabase | None = None
        # Cache of parsed DPD validation reports, keyed (edition, book_no).
        self._dpd_reports: dict = {}
        # Apparatus notes for the page on screen: {note_no: text} (hover tips).
        self._page_notes: dict = {}
        # Per-volume sigla parsed from the PTS preface, keyed (edition, book_no).
        self._preface_sigla_cache: dict = {}

        for candidate in (
            root_dir / "src" / "data" / "tipitaka.sqlite",
            root_dir / "usr" / "_internal" / "tipitaka.sqlite",
        ):
            if candidate.exists():
                self._db = TipitakaDatabase(candidate, edition="mula")
                self._db.connect()
                break

        # Clean book names sourced from the DB (the `books` table names are
        # mojibake; nav_tree + s_name are clean). Used by _book_meta().
        self._book_titles, self._book_siglas = self._load_book_index()

        self._parser = PTSCitationParser()
        self._current_book = 0
        self._current_page = 0
        self._dark = False
        self._edition = "mula"  # mula (Tipiṭaka) or atthakatha (Aṭṭhakathā)
        self._nav_books: set = set()  # book_nos with a navigable section tree
        self._contents_books: set = set()  # book_nos with a PTS-anchored contents
        self._show_translation = True  # show English translation under each page
        # Parallel commentary pane state (canon pane always stays on `mula`).
        self._comm_visible = False
        self._comm_book = None
        self._comm_page = None
        self._comm_body = ""

        self.setWindowTitle("Tipitaka PTS Browser")
        for icon_path in (
            root_dir / "src" / "data" / "icons" / "pts-logo.png",
            root_dir / "usr" / "_internal" / "data" / "icons" / "pts-logo.png",
        ):
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
                break
        self.resize(1050, 720)
        self._apply_theme()
        self._build_ui()
        self._apply_fonts()
        self._load_books()

    # ═══ THEME ═════════════════════════════════════════════════

    def _apply_theme(self):
        p = self.palette()
        if self._dark:
            p.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
            p.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
            p.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            p.setColor(QPalette.ColorRole.Text, QColor(232, 224, 208))
            p.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
            p.setColor(QPalette.ColorRole.ButtonText, QColor(210, 210, 210))
            p.setColor(QPalette.ColorRole.Highlight, QColor(42, 80, 120))
            p.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        else:
            p.setColor(QPalette.ColorRole.Window, QColor(250, 250, 248))
            p.setColor(QPalette.ColorRole.WindowText, QColor(30, 30, 30))
            p.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
            p.setColor(QPalette.ColorRole.Text, QColor(30, 30, 30))
            p.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
            p.setColor(QPalette.ColorRole.ButtonText, QColor(30, 30, 30))
            p.setColor(QPalette.ColorRole.Highlight, QColor(52, 152, 219))
            p.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        self.setPalette(p)

    def _toggle_theme(self):
        self._dark = not self._dark
        self._apply_theme()
        self._restyle()
        self._apply_dpd_theme()  # "auto" DPD theme follows the app light/dark

    def _restyle(self):
        """Apply widget-specific styling based on current theme."""
        d = self._dark
        text_bg = "#1a1a1a" if d else "#fffffa"
        text_fg = "#e8e0d0" if d else "#1a1a1a"
        sidebar_bg = "#252525" if d else "#f5f5f5"
        sidebar_border = "#444" if d else "#ddd"
        input_bg = "#333" if d else "#fff"
        input_fg = "#ddd" if d else "#333"
        input_border = "#555" if d else "#ccc"
        toolbar_bg = "#2d2d2d" if d else "#fafafa"
        btn_hover = "#444" if d else "#e8e8e8"
        btn_fg = "#ccc" if d else "#555"

        if hasattr(self, "_text"):
            self._text.setStyleSheet(
                f"QTextBrowser {{ background: {text_bg}; color: {text_fg}; "
                f"border: none; padding: 24px 40px; font-size: 15pt; }}"
            )
        if hasattr(self, "_sidebar"):
            self._sidebar.setStyleSheet(
                f"QWidget#sidebar {{ background: {sidebar_bg}; "
                f"border-right: 1px solid {sidebar_border}; }}"
                f"QTreeWidget {{ background: transparent; border: none; "
                f"color: {'#ddd' if d else '#333'}; font-size: 11pt; }}"
                f"QTreeWidget::item:selected {{ background: {'#264f78' if d else '#3498db'}; color: #fff; }}"
                f"QTreeWidget::item:hover {{ background: {'#333' if d else '#e8f4fd'}; }}"
            )
        if hasattr(self, "_toolbar"):
            self._toolbar.setStyleSheet(
                f"QWidget#toolbar {{ background: {toolbar_bg}; "
                f"border-bottom: 1px solid {sidebar_border}; }}"
                f"QLineEdit {{ border: 1px solid {input_border}; border-radius: 6px; "
                f"padding: 6px 12px; background: {input_bg}; color: {input_fg}; "
                f"font-size: 13pt; }}"
                f"QPushButton {{ background: transparent; border: 1px solid transparent; "
                f"border-radius: 4px; padding: 5px 12px; color: {btn_fg}; font-size: 12pt; }}"
                f"QPushButton:hover {{ background: {btn_hover}; }}"
                f"QComboBox {{ border: 1px solid {input_border}; border-radius: 4px; "
                f"padding: 4px 8px; background: {input_bg}; color: {input_fg}; font-size: 12pt; }}"
            )

    # ═══ UI BUILD ══════════════════════════════════════════════

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_toolbar())
        root.addWidget(self._build_warning_banner())
        root.addWidget(self._build_body())

        self._build_dpd_dock()
        self._build_menu()
        self._restyle()

        # In-page find shortcuts.
        QShortcut(QKeySequence.StandardKey.Find, self, self._open_find)
        QShortcut(QKeySequence.StandardKey.FindNext, self, self._find_next)
        QShortcut(QKeySequence.StandardKey.FindPrevious, self, self._find_prev)
        esc = QShortcut(
            QKeySequence(Qt.Key.Key_Escape), self._find_bar, self._close_find
        )
        esc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)

        # Copy-with-citation (Ctrl+Shift+C) + clean Ctrl+C on the readers, plus a
        # right-click menu with both. The clean copy strips the invisible
        # line-number labels injected by _render_pali_numbered.
        cite_sc = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        cite_sc.activated.connect(lambda: self._copy_with_citation())
        for br in (self._text, self._comm_text):
            br.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            br.customContextMenuRequested.connect(
                lambda pos, b=br: self._text_context_menu(b, pos)
            )
            cp = QShortcut(QKeySequence.StandardKey.Copy, br)
            cp.setContext(Qt.ShortcutContext.WidgetShortcut)
            cp.activated.connect(lambda b=br: self._plain_clean_copy(b))

    # ═══ IN-PAGE FIND (Ctrl+F) ════════════════════════════════

    def _find_target(self):
        """The visible text view (reader text, or search-results pane)."""
        return self._text if self._stack.currentIndex() == 0 else self._results

    def _open_find(self):
        sel = self._find_target().textCursor().selectedText()
        if sel:
            self._find_input.setText(sel)
        self._find_bar.setVisible(True)
        self._find_input.setFocus()
        self._find_input.selectAll()

    def _close_find(self):
        self._find_bar.setVisible(False)
        self._find_target().setFocus()

    def _do_find(self, backward: bool = False):
        q = self._find_input.text()
        if not q:
            return
        view = self._find_target()
        flags = (
            QTextDocument.FindFlag.FindBackward
            if backward
            else QTextDocument.FindFlag(0)
        )
        if not view.find(q, flags):  # wrap around
            cur = view.textCursor()
            cur.movePosition(
                QTextCursor.MoveOperation.End
                if backward
                else QTextCursor.MoveOperation.Start
            )
            view.setTextCursor(cur)
            view.find(q, flags)

    def _find_next(self):
        self._do_find(False)

    def _find_prev(self):
        self._do_find(True)

    def _find_incremental(self):
        # re-search from the start of the current match as the user types
        view = self._find_target()
        cur = view.textCursor()
        cur.setPosition(cur.selectionStart())
        view.setTextCursor(cur)
        self._do_find(False)

    def _build_warning_banner(self) -> QWidget:
        """Permanent, prominent warning about the reliability of the text."""
        banner = QLabel(
            "⚠ Transliteración con numerosos errores — verifique siempre "
            "con las ediciones impresas (PTS)."
        )
        banner.setWordWrap(False)
        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner.setMaximumHeight(26)
        banner.setStyleSheet(
            "background-color: #c00000; color: #ffffff;"
            "font-weight: bold; font-size: 9pt;"
            "padding: 3px 10px; border-bottom: 1px solid #7a0000;"
        )
        return banner

    def _build_toolbar(self) -> QWidget:
        bar = QWidget(objectName="toolbar")
        bar.setFixedHeight(44)
        self._toolbar = bar
        L = QHBoxLayout(bar)
        L.setContentsMargins(10, 5, 10, 5)
        L.setSpacing(8)

        # Sidebar toggle
        btn = QPushButton("☰  Índice")
        btn.setFixedHeight(34)
        btn.setToolTip("Mostrar/ocultar índice")
        btn.clicked.connect(self._toggle_sidebar)
        L.addWidget(btn)

        # Navigation label
        self._nav_label = QLabel("")
        self._nav_label.setStyleSheet("font-size: 12pt; padding: 0 6px;")
        L.addWidget(self._nav_label)

        L.addStretch()

        # Search (se expande con el espacio disponible, sin estar encajonada)
        self._search = QLineEdit()
        self._search.setPlaceholderText(
            " Ir a cita (p.ej. «S III 1») · buscar texto · /patrón/ regex"
        )
        self._search.setMinimumWidth(220)
        self._search.returnPressed.connect(self._do_search)
        c = QCompleter(
            [
                "dhamma",
                "bhikkhu",
                "bhagavā",
                "nibbāna",
                "dukkha",
                "sati",
                "paññā",
                "sīla",
                "samādhi",
                "mettā",
            ],
            self,
        )
        c.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._search.setCompleter(c)
        L.addWidget(self._search)

        L.addSpacing(12)

        # Prev / Next
        for arrow, tip, fn in [
            ("◂", "Página anterior", self._prev),
            ("▸", "Página siguiente", self._next),
        ]:
            btn = QPushButton(arrow)
            btn.setFixedSize(34, 34)
            btn.setToolTip(tip)
            btn.clicked.connect(fn)
            L.addWidget(btn)

        # Theme
        btn = QPushButton("🌓")
        btn.setFixedSize(34, 34)
        btn.setToolTip("Modo claro/oscuro")
        btn.clicked.connect(self._toggle_theme)
        L.addWidget(btn)

        # Toggle main edition: Mūla ↔ Aṭṭhakathā (cambia el contenido principal)
        self._edition_btn = QPushButton("Aṭṭh")
        self._edition_btn.setFixedHeight(34)
        self._edition_btn.setToolTip(
            "Alternar entre Mūla (canon) y Aṭṭhakathā (comentario)\n"
            "— el contenido principal cambia automáticamente"
        )
        self._edition_btn.clicked.connect(self._toggle_edition)
        self._edition_btn.setStyleSheet(
            "QPushButton { font-weight: bold; padding: 0 10px; color: #19647E; }"
        )
        L.addWidget(self._edition_btn)

        # Commentary parallel pane toggle
        self._comm_btn = QPushButton("Comentario")
        self._comm_btn.setFixedHeight(34)
        self._comm_btn.setToolTip("Ver el comentario (Aṭṭhakathā) en paralelo")
        self._comm_btn.clicked.connect(self._toggle_commentary)
        self._comm_btn.setStyleSheet(
            "QPushButton { font-weight: bold; padding: 0 10px; }"
        )
        L.addWidget(self._comm_btn)

        return bar

    # ═══ DPD DICTIONARY PANEL ═════════════════════════════════
    # Replicates the official DPD Chrome extension: double-click a Pāli word in
    # the text → its DPD entry appears in a docked side panel (NOT a popup),
    # with the same collapsible grammar/examples, because we load the webapp's
    # own /search_html page in an embedded Chromium view (QWebEngineView).

    def _build_dpd_dock(self):
        self._dpd_dock = QDockWidget("Diccionario DPD", self)
        self._dpd_dock.setObjectName("dpd_dock")
        self._dpd_dock.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )
        if QWebEngineView is None:
            self._dpd_view = None
            placeholder = QLabel(
                "QtWebEngine no está disponible.\n"
                "Instala PyQt6-WebEngine para el panel DPD."
            )
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setWordWrap(True)
            self._dpd_dock.setWidget(placeholder)
        else:
            self._dpd_view = QWebEngineView()
            # Re-apply the selected DPD theme after every navigation (each lookup
            # reloads /search_html), so the theme — and the button-contrast fix —
            # survive. DpdThemeManager owns all of that.
            self._dpd_view.loadFinished.connect(lambda ok: self._apply_dpd_theme())
            self._dpd_view.setUrl(QUrl(f"{DPD_WEBAPP_URL}/"))
            self._dpd_dock.setWidget(self._dpd_view)
        self._dpd_themer = DpdThemeManager(self._dpd_view)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._dpd_dock)
        self._dpd_dock.resize(420, self._dpd_dock.height())
        self._dpd_dock.hide()  # appears on first lookup

    @staticmethod
    def _clean_dpd_word(word: str) -> str:
        """Normalise a selected word the way the DPD extension does."""
        import re

        w = re.sub(r"[’‘“”]", "'", word)
        w = re.sub(r"[.,;:!?()\[\]{}\\/\"]", "", w)
        return w.strip()

    def _apply_dpd_theme(self):
        """Re-apply the panel theme (delegates to DpdThemeManager)."""
        themer = getattr(self, "_dpd_themer", None)
        if themer is not None:
            themer.apply(self._dark)

    def _set_dpd_theme(self, key: str):
        self._dpd_themer.theme = key
        self._apply_dpd_theme()

    def _lookup_selected_dpd(self):
        """Send the word selected in the reader or commentary to the DPD panel."""
        if self._stack.currentIndex() != 0:  # only from the reader view
            return
        word = ""
        comm = getattr(self, "_comm_text", None)
        if comm is not None and comm.textCursor().hasSelection():
            word = self._clean_dpd_word(comm.textCursor().selectedText())
        if not word:
            word = self._clean_dpd_word(self._text.textCursor().selectedText())
        if not word or self._dpd_view is None:
            return
        if not self._dpd_dock.isVisible():
            self._dpd_dock.show()
        self._dpd_view.setUrl(
            QUrl(
                f"{DPD_WEBAPP_URL}/search_html?q={QUrl.toPercentEncoding(word).data().decode()}"
            )
        )

    def _build_body(self) -> QSplitter:
        split = QSplitter(Qt.Orientation.Horizontal)

        # ── Sidebar ───────────────────────────────────────
        sidebar = QWidget(objectName="sidebar")
        sidebar.setFixedWidth(260)
        self._sidebar = sidebar
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(8, 8, 8, 8)
        sl.setSpacing(6)

        title = QLabel("Índice del Tipiṭaka")
        title.setStyleSheet("font-weight: bold; font-size: 12pt; padding: 4px 0;")
        sl.addWidget(title)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(14)
        self._tree.itemClicked.connect(self._on_tree_click)
        self._tree.itemExpanded.connect(self._on_tree_expanded)
        sl.addWidget(self._tree, 1)

        split.addWidget(sidebar)

        # ── Main area: stacked text / search results ──────
        self._stack = QStackedWidget()

        # Page 0: Text view
        reader = QWidget()
        rl = QVBoxLayout(reader)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        self._text = QTextBrowser()
        self._text.setOpenExternalLinks(False)
        self._text.setOpenLinks(False)  # our anchorClicked handler does it all
        self._text.setReadOnly(True)
        self._text.setFrameShape(QFrame.Shape.NoFrame)
        # Render the welcome screen as real HTML (setPlaceholderText would show
        # the raw markup). Welcome cards are clickable via the same load: links.
        self._text.anchorClicked.connect(self._on_result_link)
        # Re-flow the Pāli-sized reading column on viewport resize.
        self._text.viewport().installEventFilter(self)
        self._text.setHtml(self._welcome_html())

        # In-page find bar (Ctrl+F), hidden until invoked.
        self._find_bar = QWidget()
        self._find_bar.setVisible(False)
        fl = QHBoxLayout(self._find_bar)
        fl.setContentsMargins(12, 4, 12, 4)
        self._find_input = QLineEdit()
        self._find_input.setPlaceholderText("Buscar en esta página…")
        self._find_input.returnPressed.connect(self._find_next)
        self._find_input.textChanged.connect(self._find_incremental)
        fl.addWidget(self._find_input, 1)
        for label, slot in (
            ("‹", self._find_prev),
            ("›", self._find_next),
            ("✕", self._close_find),
        ):
            b = QPushButton(label)
            b.setFixedWidth(30)
            b.clicked.connect(slot)
            fl.addWidget(b)
        rl.addWidget(self._find_bar)

        # ── Reader split: canon (left) | commentary (right, hidden) ──
        self._reader_split = QSplitter(Qt.Orientation.Horizontal)
        self._reader_split.addWidget(self._text)

        self._comm_panel = QWidget()
        cpl = QVBoxLayout(self._comm_panel)
        cpl.setContentsMargins(0, 0, 0, 0)
        cpl.setSpacing(0)
        comm_head = QWidget()
        comm_head.setFixedHeight(30)
        chl = QHBoxLayout(comm_head)
        chl.setContentsMargins(12, 2, 8, 2)
        comm_title = QLabel("Aṭṭhakathā (comentario)")
        comm_title.setStyleSheet("color: #8B0000; font-weight: bold; font-size: 10pt;")
        chl.addWidget(comm_title)
        chl.addStretch()
        comm_close = QPushButton("×")
        comm_close.setFixedSize(24, 24)
        comm_close.setToolTip("Ocultar el comentario")
        comm_close.clicked.connect(self._hide_commentary)
        chl.addWidget(comm_close)
        cpl.addWidget(comm_head)

        self._comm_text = QTextBrowser()
        self._comm_text.setOpenExternalLinks(False)
        self._comm_text.setOpenLinks(False)
        self._comm_text.setReadOnly(True)
        self._comm_text.setFrameShape(QFrame.Shape.NoFrame)
        # Links inside the commentary (e.g. "‹ ir al sutta") reuse the reader's
        # link handler; resize re-flows the prose column.
        self._comm_text.anchorClicked.connect(self._on_result_link)
        self._comm_text.viewport().installEventFilter(self)
        cpl.addWidget(self._comm_text, 1)

        self._comm_panel.setVisible(False)
        self._reader_split.addWidget(self._comm_panel)
        self._reader_split.setSizes([640, 420])
        rl.addWidget(self._reader_split, 1)

        info = QWidget()
        info.setFixedHeight(26)
        il = QHBoxLayout(info)
        il.setContentsMargins(12, 2, 12, 2)
        self._info_label = QLabel("")
        self._info_label.setStyleSheet("color: #888; font-size: 10pt;")
        il.addWidget(self._info_label)
        il.addStretch()
        self._page_label = QLabel("")
        self._page_label.setStyleSheet(
            "color: #666; font-weight: bold; font-size: 10pt;"
        )
        il.addWidget(self._page_label)
        rl.addWidget(info)
        self._stack.addWidget(reader)

        # Page 1: Search results
        results_page = QWidget()
        rp = QVBoxLayout(results_page)
        rp.setContentsMargins(0, 0, 0, 0)
        rp.setSpacing(0)

        # Results header
        rh = QWidget()
        rh.setFixedHeight(40)
        rhl = QHBoxLayout(rh)
        rhl.setContentsMargins(16, 6, 12, 6)
        self._results_header = QLabel("")
        self._results_header.setStyleSheet("font-size: 13pt; font-weight: bold;")
        rhl.addWidget(self._results_header)
        rhl.addStretch()
        close_btn = QPushButton("×")
        close_btn.setFixedSize(28, 28)
        close_btn.setToolTip("Cerrar resultados")
        close_btn.clicked.connect(self._clear_search)
        rhl.addWidget(close_btn)
        rp.addWidget(rh)

        # Results list with rich cards
        self._results = QTextBrowser()
        self._results.setOpenExternalLinks(False)
        self._results.setOpenLinks(False)
        self._results.setReadOnly(True)
        self._results.setFrameShape(QFrame.Shape.NoFrame)
        self._results.anchorClicked.connect(self._on_result_link)
        rp.addWidget(self._results, 1)

        self._stack.addWidget(results_page)

        split.addWidget(self._stack)
        split.setSizes([260, 790])
        return split

    def _build_menu(self):
        m = self.menuBar()
        f = m.addMenu("&Archivo")
        a = QAction("Exportar &HTML…", self)
        a.triggered.connect(self._export_html)
        f.addAction(a)
        a = QAction("Exportar &texto…", self)
        a.triggered.connect(self._export_text)
        f.addAction(a)
        f.addSeparator()
        a = QAction("&Salir", self)
        a.setShortcut(QKeySequence.StandardKey.Quit)
        a.triggered.connect(self.close)
        f.addAction(a)

        v = m.addMenu("&Ver")
        a = QAction("Tema &oscuro", self, checkable=True)
        a.toggled.connect(lambda c: self._toggle_theme())
        v.addAction(a)
        a = QAction("Panel de &índice", self, checkable=True)
        a.setChecked(True)
        a.toggled.connect(lambda c: self._sidebar.setVisible(c))
        v.addAction(a)
        # DPD dictionary panel: reuse the dock's own checkable toggle action so
        # the menu state stays in sync when the panel is closed via its ✕.
        dpd_toggle = self._dpd_dock.toggleViewAction()
        dpd_toggle.setText("&Diccionario DPD (doble clic en palabra)")
        v.addAction(dpd_toggle)
        # DPD panel themes (multi-theme, like the extension).
        theme_menu = v.addMenu("Tema del &diccionario DPD")
        grp = QActionGroup(self)
        grp.setExclusive(True)
        for key, label in self._dpd_themer.items():
            act = QAction(label, self, checkable=True)
            act.setChecked(key == self._dpd_themer.theme)
            act.triggered.connect(lambda _checked, k=key: self._set_dpd_theme(k))
            grp.addAction(act)
            theme_menu.addAction(act)
        v.addSeparator()
        a = QAction("&Traducción inglesa", self, checkable=True)
        a.setChecked(self._show_translation)
        a.toggled.connect(self._toggle_translation)
        v.addAction(a)
        v.addSeparator()
        a = QAction("&Prefacio del volumen", self)
        a.triggered.connect(lambda: self._show_supplement("preface"))
        v.addAction(a)
        a = QAction("A&péndice (Various Readings)", self)
        a.triggered.connect(lambda: self._show_supplement("appendix"))
        v.addAction(a)

        h = m.addMenu("A&yuda")
        a = QAction("&Acerca de…", self)
        a.triggered.connect(
            lambda: QMessageBox.about(
                self,
                "Acerca de",
                "Tipitaka PTS Browser\n\n"
                "Edición de la Pali Text Society (texto romano y tailandés).\n"
                "Canon + comentarios (Aṭṭhakathā), con prefacios y apéndices "
                "(Various Readings).\n\n"
                "Búsqueda de texto completo, concordancia y expresiones "
                "regulares (/patrón/).",
            )
        )
        h.addAction(a)
        a = QAction("&Leyenda de siglas (aparato)…", self)
        a.triggered.connect(self._show_sigla_legend)
        h.addAction(a)

    def _show_sigla_legend(self):
        """Show the sigla legend: the volume's own (from its Preface) + catalogue."""
        import html as _html

        def table(d):
            return "".join(
                f"<tr><td style='padding:2px 14px 2px 0;font-weight:bold;"
                f"vertical-align:top'>{_html.escape(k)}</td>"
                f"<td style='padding:2px 0'>{_html.escape(v)}</td></tr>"
                for k, v in d.items()
            )

        parts = ["<b>Siglas del aparato crítico</b>"]
        vol = self._preface_sigla(self._current_book)
        if vol:
            _, name, _ = self._book_meta(self._current_book)
            parts.append(
                "<br><span style='color:#888'>Según el Prefacio de "
                f"<i>{_html.escape(name)}</i>:</span>"
                f"<br><table>{table(vol)}</table>"
            )
        parts.append(
            "<br><span style='color:#888'>Catálogo general "
            "(<i>src/main/apparatus.py</i>):</span>"
            f"<br><table>{table(self._SIGLA_DESCR)}</table>"
            "<br><span style='color:#aaa;font-size:9pt'>Las siglas de un solo "
            "carácter suelen ser específicas de cada volumen: ver su Prefacio "
            "(menú Ver → Prefacio del volumen).</span>"
        )
        QMessageBox.information(self, "Leyenda de siglas", "".join(parts))

    # ═══ WELCOME ══════════════════════════════════════════════

    def _welcome_html(self) -> str:
        """Welcome screen with browse-by-collection cards."""
        parts = [
            "<div style='max-width:700px;margin:40px auto;text-align:center'>",
            "<h1 style='color:#8B0000;font-size:22pt;margin-bottom:8px'>Tipiṭaka</h1>",
            "<p style='color:#888;font-size:12pt;margin-bottom:30px'>"
            "Canon Pāli · Pali Text Society (romano y tailandés)</p>",
        ]
        for name, desc, books in _COLLECTIONS:
            parts.append(
                f"<a href='load:{books[0]}:1' style='text-decoration:none;color:inherit'>"
                f"<table style='width:320px;margin:6px auto;border:1px solid #ddd'>"
                f"<tr><td style='padding:14px'>"
                f"<b style='font-size:13pt;color:#2980b9'>{name}</b><br>"
                f"<span style='color:#888;font-size:10pt'>{desc}</span>"
                f"</td></tr></table></a>"
            )
        parts.append(
            "<p style='color:#aaa;font-size:10pt;margin-top:24px'>"
            "Selecciona una colección o busca una palabra en la barra superior</p>"
            "</div>"
        )
        return "".join(parts)

    # ═══ FONTS ════════════════════════════════════════════════

    def _apply_fonts(self):
        families = QFontDatabase.families()
        # Document default (apparatus, translation, welcome) stays a serif.
        chosen = None
        for fam in (
            "Gentium Plus",
            "Gentium",
            "FreeSerif",
            "Noto Serif",
            "Liberation Serif",
        ):
            if fam in families:
                chosen = QFont(fam, 15)
                break
        if chosen is None:
            chosen = QFont()
            chosen.setStyleHint(QFont.StyleHint.Serif)
            chosen.setPointSize(15)
        self._text.setFont(chosen)
        # The Pāli body itself renders in Roboto with 6px word spacing (see
        # _show_page). Keep a matching font so the reading column is measured
        # with exactly the metrics it will be drawn with.
        pali = QFont("Roboto", 16) if "Roboto" in families else QFont(chosen)
        pali.setPointSize(16)
        pali.setWordSpacing(6)
        self._pali_font = pali
        # Commentary is dense scholastic prose, not airy canonical verse: a
        # serif body at a smaller size with normal word spacing. Used both to
        # render and to measure the commentary column.
        comm = QFont(chosen)
        comm.setPointSize(14)
        self._comm_font = comm
        if getattr(self, "_comm_text", None) is not None:
            self._comm_text.setFont(comm)

    # ═══ LOAD BOOKS ═══════════════════════════════════════════

    def _load_books(self):
        # Delegate to the DB-driven loader so the full canon (all books,
        # clean names) is shown from startup, not just the 26 curated ones.
        self._load_edition_books()

    # ═══ NAVIGATION ═══════════════════════════════════════════

    def _on_tree_click(self, item: QTreeWidgetItem, col: int):
        bn = item.data(0, Qt.ItemDataRole.UserRole)
        if bn is None:
            return
        # Section nodes carry a target page; book nodes open at page 1.
        page = item.data(0, Qt.ItemDataRole.UserRole + 1)
        self._load_book_page(bn, int(page) if page else 1)

    def _toggle_sidebar(self):
        self._sidebar.setVisible(not self._sidebar.isVisible())

    def _toggle_translation(self, on: bool):
        self._show_translation = on
        if self._current_book and self._current_page:
            self._load_book_page(self._current_book, self._current_page)

    def _toggle_commentary(self):
        if not self._db:
            return
        if self._comm_visible:
            self._hide_commentary()
        else:
            self._comm_visible = True
            self._comm_panel.setVisible(True)
            self._comm_btn.setText("Ocultar com.")
            self._comm_btn.setToolTip("Ocultar el comentario")
            self._comm_btn.setStyleSheet(
                "QPushButton { font-weight: bold; padding: 0 10px;"
                " background: #8B0000; color: white; border-radius: 4px; }"
            )
            self._sync_commentary()

    def _toggle_edition(self):
        if not self._db or not self._current_book:
            return
        if self._edition == "mula":
            m = self._db.map_canon_to_commentary(
                self._current_book, self._current_page or 1
            )
            if m:
                self._db.set_edition("atthakatha")
                self._edition = "atthakatha"
                self._edition_btn.setText("Mula")
                self._edition_btn.setStyleSheet(
                    "QPushButton { font-weight: bold; padding: 0 10px; "
                    "background: #19647E; color: white; border-radius: 4px; }"
                )
                self._edition_btn.setToolTip("Volver al canon")
                self._load_book_page(m["book"], m["page"])
        else:
            m = self._db.map_commentary_to_canon(
                self._current_book, self._current_page or 1
            )
            self._db.set_edition("mula")
            self._edition = "mula"
            self._edition_btn.setText("Atth")
            self._edition_btn.setStyleSheet(
                "QPushButton { font-weight: bold; padding: 0 10px; "
                "color: #19647E; }"
            )
            self._edition_btn.setToolTip("Ir al comentario")
            if m:
                self._load_book_page(m["book"], m["page"])
            else:
                self._load_book_page(self._current_book, self._current_page or 1)
        self._load_edition_books()

    def _hide_commentary(self):
        self._comm_visible = False
        self._comm_panel.setVisible(False)
        self._comm_btn.setText("Comentario")
        self._comm_btn.setToolTip("Ver el comentario (Aṭṭhakathā) en paralelo")
        self._comm_btn.setStyleSheet(
            "QPushButton { font-weight: bold; padding: 0 10px; }"
        )

    def _sync_commentary(self):
        """Align the commentary pane to the canon page now showing."""
        if not (self._db and self._comm_visible and self._current_book):
            return
        m = self._db.map_canon_to_commentary(
            self._current_book, self._current_page or 1
        )
        if not m:
            self._comm_book = self._comm_page = None
            self._comm_body = (
                "<div style='color:#888;padding:24px;text-align:center'>"
                "No hay comentario (Aṭṭhakathā) mapeado para este libro.</div>"
            )
            self._render_comm_centered()
            return
        data = self._db.get_page_for_edition("atthakatha", m["book"], m["page"])
        self._comm_book, self._comm_page = m["book"], m["page"]
        self._render_commentary(data or {}, m)

    def _render_commentary(self, data: dict, m: dict) -> None:
        """Render the commentary page with its own prose typography + header."""
        import html

        body = self._render_pali(data.get("text", ""))
        body = self._highlight_lemmas(body, m.get("book"), m.get("page"))

        badge = ""
        if m.get("approx"):
            badge = (
                "<span style='background:#fdecea;color:#8B0000;font-size:8.5pt;"
                "padding:1px 7px;border-radius:9px;margin-left:8px'>"
                "≈ aproximado</span>"
            )
        parts = [
            "<div style='color:#8B0000;font-size:11pt;font-weight:bold;"
            f"margin-bottom:2px'>{html.escape(m.get('breadcrumb', ''))}{badge}</div>",
            "<div style='color:#aaa;font-size:9pt;margin-bottom:14px'>"
            f"p. {m.get('page')} · {html.escape(m.get('reason', ''))}</div>",
            # Serif prose body: no Roboto, no word-spacing (inherits the
            # commentary serif font set in _apply_fonts).
            "<div style='line-height:1.6;font-size:14pt;text-align:justify'>"
            f"{body}</div>",
        ]
        self._comm_body = "".join(parts)
        self._render_comm_centered()

    # A single Pāli word or hyphenated compound (no '<' so HTML tags are safe),
    # optionally closed by an elision apostrophe.
    _LEMMA_WORD = r"[A-Za-zĀ-ỿ][A-Za-zĀ-ỿ\-]*['’]?"
    _RX_TATTHA = re.compile(r"(\bTattha\s+)(" + _LEMMA_WORD + r")")
    _RX_TI = re.compile(r"(?<![A-Za-zĀ-ỿ])(" + _LEMMA_WORD + r")(\s+ti\b)")

    def _highlight_lemmas(self, body_html: str, book_no, page_no) -> str:
        """Bold the lemmas — the canonical head-words an aṭṭhakathā glosses.

        Heuristic (data here has no per-page lemma index): the two reliable
        structural markers in commentarial prose are the gloss introducer
        "Tattha <lemma>" and the quotative "<lemma> ti" that closes a quoted
        head-word. We bold that single word/compound in each. Conservative by
        design (one token only) and easy to tune; runs on the rendered HTML,
        whose only non-text is inline tags that contain no " ti" / "Tattha".
        """
        b = "<b style='color:#5b3a29'>"
        body_html = self._RX_TATTHA.sub(r"\1" + b + r"\2</b>", body_html)
        body_html = self._RX_TI.sub(b + r"\1</b>\2", body_html)
        return body_html

    # ═══ BOOK NAMES ════════════════════════════════════════════

    def _load_book_index(self):
        """Build clean book-name maps from the DB.

        Returns (titles, siglas):
          - titles[book_no] -> readable title from nav_tree (ROTA numbering)
          - siglas[book_no] -> PTS sigla from books.s_name (ROTA)
        The `books.book_name` column is mojibake, so it is never used.
        """
        titles: dict = {}
        siglas: dict = {}
        if not self._db:
            return titles, siglas
        try:
            cur = self._db.connection.cursor()
            for bn, text in cur.execute(
                "SELECT book_no, text FROM nav_tree "
                "WHERE book_no IS NOT NULL AND text LIKE '%Vol%'"
            ):
                if bn not in titles and text:
                    titles[bn] = text.strip().rstrip(".").strip()
            for bn, s in cur.execute(
                "SELECT book_no, s_name FROM books WHERE edition='mula'"
            ):
                if s:
                    siglas[bn] = s.strip()
        except Exception:
            pass
        return titles, siglas

    def _book_meta(self, book_no: int):
        """Resolve (pitaka, name, sigla) for a book, edition-aware.

        Priority: curated _BOOKS → nav_tree title → s_name sigla → fallback.
        """
        if self._edition == "mula":
            if book_no in _BOOKS:
                return _BOOKS[book_no]
            title = self._book_titles.get(book_no)
            sigla = self._book_siglas.get(book_no, "")
            if title:
                return ("", title, sigla)
            if sigla:
                return ("", sigla, sigla)
            return ("", f"Libro {book_no}", "")
        # ROTB commentaries have no clean per-book title in this DB.
        return ("Aṭṭhakathā", f"Comentario · libro {book_no}", "")

    def _add_book_item(self, parent, book_no: int, label: str):
        """Create a book node; give it an expand arrow if it has a contents tree."""
        item = QTreeWidgetItem(parent, [label])
        item.setData(0, Qt.ItemDataRole.UserRole, book_no)
        if book_no in self._contents_books or book_no in self._nav_books:
            # Placeholder child → shows the expand arrow; replaced on expand.
            ph = QTreeWidgetItem(item, ["…"])
            ph.setData(0, Qt.ItemDataRole.UserRole + 2, "placeholder")
        return item

    def _mk_node(self, parent, bn, page, label):
        node = QTreeWidgetItem(parent, [label])
        node.setData(0, Qt.ItemDataRole.UserRole, bn)
        if page:
            node.setData(0, Qt.ItemDataRole.UserRole + 1, page)
        return node

    def _on_tree_expanded(self, item: QTreeWidgetItem):
        """Lazy-load a book's contents on first expand.

        Prefers the clean PTS-anchored `contents` (vagga → sutta) for DN/MN/SN/AN;
        falls back to the flat `nav_tree` sections for other books.
        """
        if not (
            item.childCount() == 1
            and item.child(0).data(0, Qt.ItemDataRole.UserRole + 2) == "placeholder"
        ):
            return
        item.takeChildren()
        bn = item.data(0, Qt.ItemDataRole.UserRole)
        if bn is None or not self._db:
            return

        if bn in self._contents_books:
            section = None
            sec_node = item
            for r in self._db.get_contents(bn):
                if r["section"] and r["section"] != section:
                    section = r["section"]
                    sec_node = self._mk_node(item, bn, r["page_no"], section)
                self._mk_node(
                    sec_node,
                    bn,
                    r["page_no"],
                    f"{r['title']}   · p. {r['page_no']}",
                )
        else:
            for sec in self._db.get_nav_sections(bn):
                self._mk_node(
                    item,
                    bn,
                    sec["page_no"],
                    f"{sec['text']}   · p. {sec['page_no']}",
                )

    def _load_edition_books(self):
        """Load book tree for the current edition from database."""
        self._tree.clear()
        if not self._db:
            return

        # Books that have a navigable section tree (canon only; nav_tree has no
        # edition column). Used to decide which book nodes are expandable.
        self._nav_books = set()
        self._contents_books = set()
        if self._edition == "mula":
            try:
                cur = self._db.connection.cursor()
                for (bn,) in cur.execute(
                    "SELECT DISTINCT book_no FROM nav_tree WHERE page_no > 0"
                ):
                    if bn is not None:
                        self._nav_books.add(int(bn))
                for (bn,) in cur.execute("SELECT DISTINCT book_no FROM contents"):
                    if bn is not None:
                        self._contents_books.add(int(bn))
            except Exception:
                pass

        # Get all books for current edition
        books = self._db.get_all_books()
        if not books:
            # Fallback to static ROTA list
            for name, desc, bns in _COLLECTIONS:
                coll = QTreeWidgetItem(self._tree, [name])
                coll.setExpanded(True)
                for bn in bns:
                    if bn in _BOOKS:
                        _, vol_name, pts_ref = _BOOKS[bn]
                        self._add_book_item(coll, bn, f"{vol_name}  ({pts_ref})")
            return

        # Group books by prefix for ROTB (commentaries grouped by source text)
        if self._edition == "atthakatha":
            self._load_rotb_tree(books)
        else:
            self._load_rota_tree(books)

    def _load_rota_tree(self, books):
        """Build ROTA tree: curated collections first, then any remaining
        books (Khuddaka cont., Abhidhamma) so the full canon is reachable."""
        covered = set()
        for name, desc, bns in _COLLECTIONS:
            coll = QTreeWidgetItem(self._tree, [name])
            coll.setExpanded(True)
            for bn in bns:
                if bn in _BOOKS:
                    _, vol_name, pts_ref = _BOOKS[bn]
                    label = f"{vol_name}  ({pts_ref})" if pts_ref else vol_name
                    self._add_book_item(coll, bn, label)
                    covered.add(bn)

        # Append every other ROTA book that the curated groups don't cover.
        rest = [b.get("book_no") for b in books if b.get("book_no") not in covered]
        if rest:
            other = QTreeWidgetItem(self._tree, ["Khuddaka · Abhidhamma"])
            other.setExpanded(True)
            for bn in rest:
                _, vol_name, sigla = self._book_meta(bn)
                label = (
                    f"{vol_name}  ({sigla})"
                    if sigla and sigla != vol_name
                    else vol_name
                )
                self._add_book_item(other, bn, label)

    def _load_rotb_tree(self, books):
        """Build ROTB tree: group commentaries by source."""
        # Get all ROTB books with their names
        seen = set()
        items = []
        for b in books:
            bn = b.get("book_no", 0)
            if bn in seen:
                continue
            seen.add(bn)
            # Get head from first page as book name
            if self._db:
                page = self._db.get_page_by_book_and_page(bn, 1)
                head = (page.get("head", "") or "").strip()[:50] if page else ""
            else:
                head = f"Libro {bn}"
            if head:
                items.append((bn, head))

        # Simple flat list for ROTB — commentaries are their own hierarchy
        root = QTreeWidgetItem(self._tree, ["Aṭṭhakathā (Comentarios)"])
        root.setExpanded(True)
        for bn, name in items:
            self._add_book_item(root, bn, name)

    def _page_bounds(self):
        """(beg_page, end_page) for the current book, or (None, None)."""
        if not (self._db and self._current_book):
            return None, None
        info = self._db.get_book_info(self._current_book)
        if not info:
            return None, None
        return info.get("beg_page"), info.get("end_page")

    def _prev(self):
        if not (self._current_book and self._current_page):
            return
        beg, _ = self._page_bounds()
        low = beg if isinstance(beg, int) else 1
        if self._current_page > low:
            self._load_book_page(self._current_book, self._current_page - 1)

    def _next(self):
        if not (self._current_book and self._current_page):
            return
        _, end = self._page_bounds()
        if isinstance(end, int) and self._current_page >= end:
            return
        self._load_book_page(self._current_book, self._current_page + 1)

    # ═══ LOADING ══════════════════════════════════════════════

    def _load_book_page(self, book_no: int, page: int):
        if not self._db:
            return
        data = self._db.get_page_by_book_and_page(book_no, page)
        if not data:
            self._info_label.setText(f"Libro {book_no}, p. {page} no encontrado")
            return
        self._show_page(data, book_no, page)

    @staticmethod
    def _markup_pali_line(line: str, link_notes: bool = False) -> str:
        """Markup one source line of Pāli (no line-break handling).

        Handles: apparatus markers &N (→ superscript, or a bidirectional
        note/ref link when link_notes), footnote-reference numbers glued to a
        word, variant readings {word}, folio markers [F.N], Feer separators,
        and whole-line dash rules. Kept side-effect free so both the flowing
        renderer (_render_pali) and the line-numbered renderer share it.
        """
        import html
        import re

        line = "".join(c for c in line if not (0xE000 <= ord(c) <= 0xF8FF))
        # A whole line of hyphens is a decorative rule, not text.
        if re.fullmatch(r"[ \t]*-{4,}[ \t]*", line):
            return (
                "<hr style='border:none;border-top:1px solid #bbb;"
                "width:38%;margin:6px auto'>"
            )
        # decode embedded HTML entities (e.g. &#x27; → ') so they don't show raw
        line = html.unescape(line)
        # quote=False keeps apostrophes raw (avoids re-creating &#x27;, whose
        # "27" the footnote-number regex would otherwise corrupt)
        t = html.escape(line, quote=False)
        # apparatus footnote markers "&N" (e.g. &1, &2)
        if link_notes:
            # The superscript is the interactive element: hover → source
            # tooltip, click → jump to the full apparatus (see eventFilter /
            # _on_result_link). No back-anchor — that caused the erratic jumps.
            t = re.sub(
                r"&amp;(\d+)",
                r"<sup><a href='note:\1' "
                r"style='color:#8B0000;font-weight:bold;text-decoration:none'>"
                r"\1</a></sup>",
                t,
            )
        else:
            t = re.sub(
                r"&amp;(\d+)", r"<sup style='color:#000;font-weight:bold'>\1</sup>", t
            )
        # footnote reference numbers (digits glued to a word, optionally with a
        # full stop in between, e.g. "hoti.4") — before inserting any markup that
        # contains hex colours with digits. The letter (and optional ".") are kept
        # via the capture group; only the digits become superscript.
        t = re.sub(
            r"([^\W\d_]\.?)(\d+)",
            r"\1<sup style='color:#000;font-weight:bold'>\2</sup>",
            t,
        )
        # variant readings {word}
        t = re.sub(r"\{([^}]+)\}", r"<i style='color:#c0392b'>\1</i>", t)
        # folio markers [F.N]
        t = re.sub(r"\[F\.([^\]]+)\]", r"<sup style='color:#aaa'>[F.\1]</sup>", t)
        # Feer separators (box-drawing ║ → proper double bar ‖)
        t = t.replace("║", "<span style='color:#c0c0c0'> ‖ </span>")
        t = t.replace("|", "<span style='color:#c0c0c0'>|</span>")
        return t

    @classmethod
    def _render_pali(cls, text: str) -> str:
        """Render decoded Pāli as flowing HTML (lines joined with <br>).

        Used for the apparatus and commentary prose, where per-line numbering
        is not wanted. The canonical reader body uses _render_pali_numbered.
        """
        if not text:
            return ""
        lines = text.replace("\r", "").split("\n")
        return "<br>".join(cls._markup_pali_line(ln) for ln in lines)

    # Invisible separators (U+2063 invisible separator) wrap every line-number
    # label so the number can be (a) stripped from copied text and (b) read
    # back to recover the PTS line of a selection, without ever colliding with
    # real Pāli digits. See _clean_selection / _copy_with_citation.
    _LN_OPEN = "⁣"
    _LN_CLOSE = "⁣"
    # Qt frame/table boundaries surface as noncharacters (U+FDD0–U+FDEF) and
    # object replacements (U+FFFC / U+FEFF) inside selectedText()/toPlainText();
    # strip them before parsing labels or copying.
    _NONCHAR_RX = re.compile("[﷐-﷯￼﻿]")

    def _render_pali_numbered(self, text: str, book_no: int, page_no: int) -> str:
        """Render the canonical body with marginal PTS line numbers.

        One source line (split on the stored newlines) = one PTS line, matching
        footnotes.beginline and the L<n> of the DPD reports. Every line carries
        an invisible-wrapped number (for citation/clean-copy); the number is
        shown in the margin only for line 1 and every fifth line.
        """
        if not text:
            self._page_lines = []
            return ""
        lines = text.replace("\r", "").split("\n")
        self._page_lines = lines
        flags = self._dpd_flags_for_page(book_no, page_no)
        out = []
        for i, ln in enumerate(lines, 1):
            body = self._markup_pali_line(ln, link_notes=True)
            if flags:
                body = self._apply_dpd_flags(body, flags)
            shown = i == 1 or i % 5 == 0
            colour = "#b0b0b0" if shown else "transparent"
            label = (
                f"<span style='color:{colour};font-family:monospace;"
                f"font-size:9pt'>{self._LN_OPEN}{i:>3}{self._LN_CLOSE}</span> "
            )
            out.append(label + body)
        return "<br>".join(out)

    # ═══ DPD VALIDATION FLAGS (margin typo hints) ═════════════

    def _load_dpd_report(self, edition: str, book_no: int) -> dict:
        """Parse dpd_check/<report>.txt into {page: {core_form: correction}}.

        The reports ([validate_text.py]) list one suspect token per line as
        `PTS <page> L<line> «form» → correction`. We index by PTS page and key
        on the form's alphabetic core (trailing footnote digits stripped, since
        those render as separate superscripts in the body).
        """
        key = (edition, book_no)
        if key in self._dpd_reports:
            return self._dpd_reports[key]
        import re

        result: dict = {}
        names = []
        if edition == "atthakatha":  # existing reports cover the aṭṭhakathā
            names.append(f"book_{book_no:02d}.txt")
        names.append(f"{edition}_{book_no:02d}.txt")  # e.g. future mula_NN.txt
        path = None
        for n in names:
            p = self._root_dir / "dpd_check" / n
            if p.exists():
                path = p
                break
        if path is not None:
            rx = re.compile(r"^\s*PTS\s+(\d+)\s+L(\d+)\s+«(.+?)»\s+→\s+(.+?)\s*$")
            try:
                for raw in path.read_text(encoding="utf-8").splitlines():
                    m = rx.match(raw)
                    if not m:
                        continue
                    page = int(m.group(1))
                    core = re.sub(r"\d+$", "", m.group(3)).strip("’'.,;:!?()")
                    if core:
                        result.setdefault(page, {})[core] = m.group(4).strip()
            except Exception:
                pass
        self._dpd_reports[key] = result
        return result

    def _dpd_flags_for_page(self, book_no: int, page_no: int) -> dict:
        return self._load_dpd_report(self._edition, book_no).get(page_no, {})

    @staticmethod
    def _apply_dpd_flags(html_line: str, flags: dict) -> str:
        """Wrap DPD-flagged forms in the rendered line with a wavy underline."""
        import html
        import re

        for core, corr in flags.items():
            pattern = re.compile(
                r"(?<![0-9A-Za-zĀ-ỿ])(" + re.escape(core) + r")(?![0-9A-Za-zĀ-ỿ])"
            )
            title = html.escape(f"posible typo — DPD sugiere: {corr}", quote=True)
            # Qt's rich-text engine ignores CSS3 (wavy) decorations but honours
            # background-color + solid underline: a highlighter-style flag.
            html_line = pattern.sub(
                "<span style='background-color:#fdecc8;"
                "text-decoration:underline;text-decoration-color:#c0392b' "
                f"title='{title}'>\\1</span>",
                html_line,
                count=1,
            )
        return html_line

    def _markup_apparatus_note(self, text: str) -> str:
        """Render a single apparatus note (sigla + variant readings) as HTML."""
        return self._render_pali(text)

    # ═══ FOOTNOTE HOVER TOOLTIPS ══════════════════════════════

    def _note_tooltip(self, event):
        """Show the apparatus note as a tooltip when hovering its superscript."""
        browser = self._text
        anchor = browser.anchorAt(event.pos())
        if anchor.startswith("note:"):
            try:
                n = int(anchor.split(":", 1)[1])
            except ValueError:
                n = None
            note = getattr(self, "_page_notes", {}).get(n)
            if note:
                QToolTip.showText(
                    event.globalPos(), self._format_note_tooltip(n, note), browser
                )
                return
        QToolTip.hideText()

    # Sigla → source description (from apparatus.py's ManuscriptSigla comments).
    _SIGLA_DESCR = {
        "Cb": "manuscrito de Cambridge",
        "Ba": "manuscrito de Bangkok A",
        "Bai": "manuscrito de Bangkok B",
        "Bi": "manuscrito birmano",
        "Ck": "manuscrito de Colombo",
        "Fsb": "edición de Fausbøll",
        "Sy": "edición Syāmaraṭṭha",
        "Ro": "edición ROTA",
        "PTS": "edición PTS",
    }

    def _sigla_expansions(self, text: str) -> list:
        """Expansions for known sigla in a note.

        Merges the built-in catalogue with the volume-specific sigla parsed
        from this book's PTS preface (the latter wins on collision, and is
        where descriptions like "The MS. in Burmese characters in the Phayre
        Collection at the India Office" come from).
        """
        import re

        combined = dict(self._SIGLA_DESCR)
        combined.update(self._preface_sigla(self._current_book))
        combined.update(self._appendix_sigla(self._current_book))
        out = []
        for sig in sorted(combined, key=len, reverse=True):  # "Bai" before "Ba"
            if re.search(r"(?<![A-Za-z])" + re.escape(sig) + r"(?![A-Za-z])", text):
                out.append(f"{sig}: {combined[sig]}")
        return out

    # ── Volume-specific sigla, parsed from the PTS preface ──
    # The abbreviation list in each volume's Preface is the authoritative
    # source for its witness/edition sigla. Formats vary; we parse the common
    # tabular layout ("<siglum>  <2+ spaces>  <description>", one per line,
    # with an optional wrapped continuation), gated on a witness keyword so
    # ordinary prose lines are not mistaken for entries.
    _SIGLA_KW = re.compile(
        r"\b(MSS?|manuscript|edition|characters|collection|recension|printed|"
        r"palm|leaf|Si[nṃ]halese|Singhalese|Burmese|Siamese|Cambodian|"
        r"Devanagari|codex|copy|text of|Phayre|reading)\b",
        re.I,
    )
    _SIGLA_STOP = {
        "The", "See", "And", "But", "For", "Page", "Part", "Vol", "This",
        "Note", "In", "Of", "As", "A", "I", "No",
    }
    _SIGLA_HEAD = re.compile(
        r"^\s{1,10}([A-Z][A-Za-z]{0,3}[0-9]?(?:\s*,\s*[A-Z][A-Za-z]{0,3}[0-9]?){0,5})"
        r"\s{2,}=?\s*(\S.+)$"
    )
    _SIGLA_JUNK = re.compile(
        r"(\.\s*\.\s*\.|CONTENTS|INDEX|\bPAGE\b|NIPĀTA|vagga)", re.I
    )
    # Inline prose form: "T.=Turnour MS. …, Ph.=Phayre MS. …". Gated on a
    # witness keyword inside the description so ordinary "x=y" prose is skipped.
    _SIGLA_INLINE = re.compile(
        r"(?<![A-Za-z])([A-Z][A-Za-z]{0,3}\.?)\s*=\s*"
        r"(\S[^=;]{4,90}?"
        r"(?:MSS?|edition|manuscript|characters?|recension|text|writing|Collection)"
        r"\b[^=;]{0,45})"
    )
    # Colon form: "A: India Office MS. of the Phayre Collection (Burmese writing)."
    # — the layout used by the "Various Readings" appendices' witness lists.
    _SIGLA_COLON = re.compile(r"^\s*([A-Z][A-Za-z]{0,2}\.?)\s*:\s+(\S.+)$")

    @classmethod
    def _parse_preface_sigla(cls, text: str) -> dict:
        import re

        out: dict = {}
        last = None
        for ln in re.split(r"[\r\n]", text):
            mc = cls._SIGLA_COLON.match(ln)
            # Single-letter witness sigla (A, B, C…) are valid here even though
            # they are in _SIGLA_STOP for prose; the ": " + keyword gate is enough.
            if (
                mc
                and cls._SIGLA_KW.search(mc.group(2))
                and not cls._SIGLA_JUNK.search(mc.group(2))
            ):
                desc = mc.group(2).strip()[:220]
                out[mc.group(1)] = desc
                last = None if desc.rstrip().endswith(".") else [mc.group(1)]
                continue
            m = cls._SIGLA_HEAD.match(ln)
            if (
                m
                and cls._SIGLA_KW.search(m.group(2))
                and not cls._SIGLA_JUNK.search(m.group(2))
            ):
                sigs = [s.strip() for s in m.group(1).split(",")]
                if all(s and s not in cls._SIGLA_STOP for s in sigs):
                    desc = m.group(2).strip().lstrip("=").strip()[:220]
                    for s in sigs:
                        out[s] = desc
                    last = None if desc.rstrip().endswith(".") else sigs
                    continue
            # a wrapped continuation of the previous entry (indented, not a new entry)
            if (
                last
                and re.match(r"^\s+\S", ln)
                and not cls._SIGLA_JUNK.search(ln)
                and not cls._SIGLA_COLON.match(ln)
                and not cls._SIGLA_HEAD.match(ln)
            ):
                add = ln.strip()
                for s in last:
                    # join word-wrap hyphens ("posses-" + "sion") without a space
                    joined = (
                        out[s][:-1] + add if out[s].endswith("-") else out[s] + " " + add
                    )
                    out[s] = joined.strip()[:220]
                if add.rstrip().endswith("."):
                    last = None
            else:
                last = None
        # Second pass: inline "X=description" definitions the tabular pass missed.
        flat = re.sub(r"[\r\n]", " ", text)
        for sig, desc in cls._SIGLA_INLINE.findall(flat):
            sig = sig.strip()
            if sig in cls._SIGLA_STOP or sig in out:
                continue
            out[sig] = re.sub(r"\s{2,}", " ", desc).strip()[:160]
        return out

    # `pts_prefaces.book_no` is reliably aligned with `pages.book_no` for the
    # canon volumes 1–22; from Dhammapada (23) on the source (`preface.dbf`) is
    # misindexed by a cumulative PTS-volume↔ROTA-book drift. The Khuddaka/
    # Abhidhamma volumes below were re-indexed by hand (verified from each
    # preface's own title page — see the migration in the repo history / memory
    # `tipitaka-gui-filologia`); only these have a trustworthy preface, so we
    # restrict the sigla to them and a wrong-volume description can never show.
    _PREFACE_TRUSTED = set(range(1, 23)) | {27, 28, 29, 30, 38, 40, 41, 42, 44, 46, 47, 51}

    def _preface_sigla(self, book_no) -> dict:
        if (
            not (self._db and book_no)
            or self._edition != "mula"
            or book_no not in self._PREFACE_TRUSTED
        ):
            return {}
        key = (self._edition, book_no)
        cache = self._preface_sigla_cache
        if key not in cache:
            text = "\n".join(r.get("text", "") for r in self._db.get_prefaces(book_no))
            cache[key] = self._parse_preface_sigla(text)
        return cache[key]

    # The richest witness sigla (e.g. "A: India Office MS. of the Phayre
    # Collection (Burmese writing)") live in the "Various Readings" APPENDICES,
    # not the prefaces. These books' appendices were re-indexed and verified
    # (see migration); the Vinaya/DN volumes carry the A/B/C/D witness lists.
    _APPENDIX_TRUSTED = {1, 2, 3, 4, 5, 7, 8, 9, 11}

    def _appendix_sigla(self, book_no) -> dict:
        if (
            not (self._db and book_no)
            or self._edition != "mula"
            or book_no not in self._APPENDIX_TRUSTED
        ):
            return {}
        key = ("appx", self._edition, book_no)
        cache = self._preface_sigla_cache
        if key not in cache:
            text = "\n".join(r.get("text", "") for r in self._db.get_appendices(book_no))
            cache[key] = self._parse_preface_sigla(text)
        return cache[key]

    def _format_note_tooltip(self, n: int, text: str) -> str:
        import html

        body = html.escape(text).replace("\n", "<br>")
        parts = [
            "<div style='max-width:380px'>",
            f"<b style='color:#8B0000'>Nota {n}</b><br>{body}",
        ]
        sig = self._sigla_expansions(text)
        if sig:
            parts.append(
                "<hr style='margin:4px 0'>"
                "<span style='color:#666;font-size:9pt'>"
                "<b>Siglas</b><br>"
                + "<br>".join(html.escape(x) for x in sig)
                + "</span>"
            )
        parts.append("</div>")
        return "".join(parts)

    def _column_px(self, font, sample: str, chars: int, browser) -> int:
        """Optimal reading-column width in px for a font + target line length.

        Targets `chars` characters per line at the given font (the classic
        readable measure), clamped to the browser's viewport so the column
        never overflows on narrow windows.
        """
        fm = QFontMetrics(font)
        per_char = fm.horizontalAdvance(sample) / len(sample)
        ideal = int(per_char * chars)
        avail = max(browser.viewport().width() - 8, 200)
        return min(ideal, avail)

    def _pali_column_px(self) -> int:
        """Canon column: ~60 chars of airy Pāli verse in the Roboto Pāli font."""
        # Representative Pāli phrase (real word lengths + spaces) so the average
        # advance reflects both the Roboto glyphs and the 6px word spacing.
        return self._column_px(
            getattr(self, "_pali_font", self._text.font()),
            "evaṁ me sutaṁ ekaṁ samayaṁ bhagavā sāvatthiyaṁ viharati",
            60,
            self._text,
        )

    def _comm_column_px(self) -> int:
        """Commentary column: ~78 chars of dense serif prose (no word spacing)."""
        return self._column_px(
            getattr(self, "_comm_font", self._text.font()),
            "tattha brahmajālanti idaṁ suttaṁ atthavasena vuccati nāma",
            78,
            self._comm_text,
        )

    def _render_centered(self) -> None:
        """Wrap the cached page body in a centred, Pāli-sized column.

        Qt's rich-text engine ignores `margin:auto` / percentage margins on a
        <div>, but honours a centred fixed-width <table>; centring yields equal
        left/right margins that grow as the window widens past the Pāli measure.
        """
        body = getattr(self, "_page_body", "")
        if not body:
            return
        px = self._pali_column_px()
        self._text.setHtml(
            f"<table align='center' width='{px}' cellspacing='0' cellpadding='0'>"
            f"<tr><td>{body}</td></tr></table>"
        )

    def _render_comm_centered(self) -> None:
        """Wrap the cached commentary body in its own centred prose column."""
        body = getattr(self, "_comm_body", "")
        if not body:
            return
        px = self._comm_column_px()
        self._comm_text.setHtml(
            f"<table align='center' width='{px}' cellspacing='0' cellpadding='0'>"
            f"<tr><td>{body}</td></tr></table>"
        )

    def eventFilter(self, obj, event):  # noqa: N802 (Qt signature)
        if obj is self._text.viewport():
            et = event.type()
            # Re-flow the Pāli column on resize so the measure stays correct.
            if et == QEvent.Type.Resize and getattr(self, "_page_body", ""):
                self._render_centered()
            # Double-click a word → look it up in the DPD panel. Defer so Qt's
            # default handler selects the word first; then we read the selection.
            elif et == QEvent.Type.MouseButtonDblClick:
                QTimer.singleShot(0, self._lookup_selected_dpd)
            # Hover a footnote superscript → tooltip with the apparatus note.
            elif et == QEvent.Type.ToolTip:
                self._note_tooltip(event)
                return True
        elif getattr(self, "_comm_text", None) is not None and (
            obj is self._comm_text.viewport()
        ):
            et = event.type()
            if et == QEvent.Type.Resize and getattr(self, "_comm_body", ""):
                self._render_comm_centered()
            elif et == QEvent.Type.MouseButtonDblClick:
                QTimer.singleShot(0, self._lookup_selected_dpd)
        return super().eventFilter(obj, event)

    def _show_page(self, data: dict, book_no: int, page: int):
        import html
        import re

        t = self._render_pali_numbered(data.get("text", ""), book_no, page)

        parts = []

        # Running page header (head / head_old), e.g. "MAHĀVAGGA [I.1.2-2.2.]"
        head = (data.get("head") or data.get("head_old") or "").strip()
        if head:
            parts.append(
                "<div style='color:#999;font-size:10pt;text-align:center;"
                f"margin-bottom:14px'>{html.escape(head)}</div>"
            )

        # Cross-edition references (VRI / Syāmaraṭṭha) for this PTS page.
        if self._edition == "mula":
            xr = self._db.get_cross_refs(book_no, page)
            bits = []
            if xr.get("vri"):
                bits.append(f"VRI {xr['vri']}")
            if xr.get("thai"):
                bits.append(f"Thai {xr['thai']}")
            if bits:
                parts.append(
                    "<div style='color:#999;font-size:9.5pt;text-align:center;"
                    "margin-bottom:12px'>≈ " + "  ·  ".join(bits) + "</div>"
                )

        parts.append(
            "<div style='line-height:1.5;font-size:16pt;word-spacing:6px;"
            f'font-family:"Roboto"\'>{t}</div>'
        )

        # Critical apparatus / footnotes — structured, numbered, and linked
        # back to the &N superscripts in the body (click ↔ scroll).
        entries = self._db.get_apparatus_entries(book_no, page, edition=self._edition)
        self._page_notes = entries  # for the hover tooltips on body superscripts
        if entries:
            rows = []
            for n in sorted(entries):
                note_html = self._markup_apparatus_note(entries[n])
                if n == 0:  # preamble (no marker) — render without a number
                    rows.append(
                        "<div style='margin:2px 0'>" + note_html + "</div>"
                    )
                    continue
                # Named anchor = the scroll target for a body superscript click;
                # the number itself is a plain label (not a back-link).
                rows.append(
                    f"<a name='note:{n}'></a><div style='margin:2px 0'>"
                    "<span style='color:#8B0000;font-weight:bold'>"
                    f"{n}.</span> {note_html}</div>"
                )
            parts.append(
                "<hr style='margin-top:18px;border:none;border-top:1px solid #ccc'>"
                "<div style='color:#444;font-size:10pt;margin-top:6px;"
                "font-weight:bold'>Aparato crítico / notas</div>"
                "<div style='font-size:11.5pt;color:#222;line-height:1.6'>"
                + "".join(rows)
                + "</div>"
            )

        # Legacy English translation (anchored to the sutta's start page).
        if self._show_translation and self._edition == "mula":
            tr = self._db.get_translation(book_no, page)
            if tr.get("text"):
                author = tr.get("author") or "—"
                scope = (
                    "traducción del sutta"
                    if tr.get("scope") == "sutta"
                    else "esta página"
                )
                body = html.escape(tr["text"]).replace("\n", "<br>")
                parts.append(
                    "<hr style='margin-top:26px;border:none;border-top:1px solid #ddd'>"
                    "<div style='color:#888;font-size:10pt;margin:6px 0 4px'>"
                    f"English ({scope}) — {html.escape(author)} "
                    "<span style='color:#bbb'>· SuttaCentral</span></div>"
                    "<div style='font-size:12.5pt;line-height:1.7;color:#33424f'>"
                    f"{body}</div>"
                )

        # Inline access to the volume's PTS front-matter / Various Readings.
        parts.append(
            "<div style='margin-top:24px;font-size:10pt;color:#2980b9'>"
            "<a href='pref:' style='color:#2980b9;text-decoration:none'>📖 Prefacio</a>"
            " &nbsp;·&nbsp; "
            "<a href='appx:' style='color:#2980b9;text-decoration:none'>"
            "📑 Apéndice (Various Readings)</a></div>"
        )

        # The Pāli source dictates the layout: the column width is computed from
        # the Pāli reading measure (see _render_centered) and everything else —
        # apparatus, translation, links — adapts to that same centred column.
        self._page_body = "".join(parts)
        self._render_centered()

        self._current_book = book_no
        self._current_page = page

        # Unified location indicator: the top bar is the single source of
        # truth for "where am I"; the bottom shows only edition + page.
        pitaka, vol, ref = self._book_meta(book_no)
        crumbs = [c for c in (pitaka, vol) if c]
        breadcrumb = "  ›  ".join(crumbs) if crumbs else f"Libro {book_no}"
        if ref and ref not in breadcrumb:
            breadcrumb += f"  ({ref})"
        self._nav_label.setText(breadcrumb)
        self._page_label.setText(f"p. {page}")
        self._info_label.setText(
            "Aṭṭhakathā (comentario)" if self._edition == "atthakatha" else "Tipiṭaka"
        )

        # Keep the parallel commentary aligned to the page now showing.
        self._sync_commentary()

    def _show_supplement(self, kind: str, book_no: int = None):
        """Render a volume's PTS preface or appendix ("Various Readings").

        Uses `book_no` when given (e.g. from a search result), else the volume
        currently open.
        """
        import html

        book = book_no or self._current_book
        if not (self._db and book):
            QMessageBox.information(
                self,
                "Sin volumen",
                "Abre primero un volumen para ver su prefacio o apéndice.",
            )
            return

        if kind == "preface":
            rows = self._db.get_prefaces(book)
            title = "Prefacio del volumen"
        else:
            rows = self._db.get_appendices(book)
            title = "Apéndice — Various Readings"

        if not rows:
            self._info_label.setText(f"{title}: no disponible para este volumen")
            return

        back = f"load:{book}:{1}"
        parts = [
            f"<div style='margin-bottom:12px;font-size:10pt'>"
            f"<a href='{back}' style='color:#2980b9;text-decoration:none'>"
            "‹ Volver al texto</a></div>",
            "<div style='color:#8B0000;font-size:13pt;text-align:center;"
            f"margin-bottom:16px'>{html.escape(title)}</div>",
        ]
        for r in rows:
            text = (r.get("text") or "").replace("\r\n", "\n").replace("\r", "\n")
            parts.append(
                f"<div style='color:#bbb;font-size:9pt'>p. {r.get('page_no')}</div>"
                "<div style='font-family:monospace;font-size:11pt;line-height:1.5;"
                f"white-space:pre-wrap;margin-bottom:18px'>{html.escape(text)}</div>"
            )
        self._text.setHtml("".join(parts))

        self._current_book = book
        pitaka, vol, _ = self._book_meta(book)
        crumb = vol or pitaka or f"Libro {book}"
        self._nav_label.setText(f"{crumb}  ›  {title}")
        self._info_label.setText(
            "Aṭṭhakathā (comentario)" if self._edition == "atthakatha" else "Tipiṭaka"
        )

    # ═══ SEARCH ═══════════════════════════════════════════════

    _PAGE_SIZE = 30

    def _do_search(self):
        import re

        q = self._search.text().strip()
        if not q or not self._db:
            return

        # PTS citation jump (e.g. "S III 1", "MN I 91", "D ii 100", "Sn 25").
        # Citations are canonical → resolve in the mūla edition.
        if not (q.startswith("/") and q.endswith("/")):
            if self._edition != "mula":
                self._db.set_edition("mula")
            data = self._db.get_page_by_pts_citation(q)
            if data:
                if self._edition != "mula":
                    self._edition = "mula"
                    self._load_edition_books()
                self._load_book_page(data["book_no"], data["page_num"])
                self._stack.setCurrentIndex(0)
                self._info_label.setText(f"→ {q}")
                return
            if self._edition != "mula":  # not a citation → restore edition
                self._db.set_edition(self._edition)

        # Resolve the search mode once so paging stays consistent.
        if len(q) >= 2 and q.startswith("/") and q.endswith("/"):
            mode, pat = "regex", q[1:-1]
        else:
            mode, pat = "text", q
            # Auto-regex: plain search finds nothing but the text looks like a
            # pattern (\b, [..], anchors).
            if (
                re.search(r"[\\\[\]()^$*+?{}|]", q)
                and self._db.count_texts(q) == 0
                and self._db.count_regex(q) > 0
            ):
                mode, pat = "regex", q
        self._search_state = (mode, pat, q)
        self._run_search(0)

    def _run_search(self, page: int):
        if not getattr(self, "_search_state", None) or not self._db:
            return
        mode, pat, q = self._search_state
        ps, off = self._PAGE_SIZE, page * self._PAGE_SIZE
        self._info_label.setText(f"Buscando «{q}»…")
        try:
            if mode == "regex":
                total = self._db.count_regex(pat)
                results = self._db.search_regex(pat, limit=ps, offset=off)
            else:
                total = self._db.count_texts(q)
                results = self._db.search_texts(q, limit=ps, offset=off)
            self._show_results(q, results, page, total)
        except Exception as e:
            self._info_label.setText(f"Error: {e}")

    def _show_results(self, query: str, results: list, page: int = 0, total: int = 0):
        """Display a page of search results with citations, cross-refs and paging."""
        if not results:
            self._results_header.setText(f"«{query}» — sin resultados")
            self._results.setHtml(
                "<div style='padding:40px;text-align:center;color:#888'>"
                "<p style='font-size:14pt'>No se encontraron resultados</p>"
                "<p>Prueba con otra palabra o revisa la ortografía Pāli.</p>"
                "</div>"
            )
            self._stack.setCurrentIndex(1)
            self._info_label.setText(f"«{query}» — sin resultados")
            return

        import html

        ps = self._PAGE_SIZE
        first = page * ps + 1
        last = page * ps + len(results)
        self._results_header.setText(f"«{query}» — {first}–{last} de {total}")
        parts = ['<div style="padding:14px 24px;max-width:820px">']
        for r in results:
            book_no = r.get("book_no", 0)
            pg = r.get("page_num", "?")
            pitaka, vol, ref = self._book_meta(book_no)
            kind = r.get("kind")

            sigla = ref or vol or f"Bk {book_no}"
            if kind == "preface":
                cite, scheme = f"{sigla} · Praef. p. {pg}", f"pref:{book_no}"
            elif kind == "appendix":
                cite, scheme = f"{sigla} · v.l. p. {pg}", f"appx:{book_no}"
            else:
                cite, scheme = f"{sigla} {pg}", f"load:{book_no}:{pg}"
            work = " · ".join(x for x in (pitaka, vol) if x)

            # Cross-edition references (VRI / Thai) for canon pages.
            xref = ""
            if self._edition == "mula" and kind not in ("preface", "appendix"):
                xr = self._db.get_cross_refs(book_no, pg) if isinstance(pg, int) else {}
                bits = []
                if xr.get("vri"):
                    bits.append(f"VRI {xr['vri']}")
                if xr.get("thai"):
                    bits.append(f"Thai {xr['thai']}")
                if bits:
                    xref = (
                        "  <span style='color:#999;font-size:9pt'>≈ "
                        + "  ·  ".join(bits)
                        + "</span>"
                    )

            snip = html.escape(r.get("snippet", "").replace("\n", " ").strip())
            snip = snip.replace("⟦", "<b style='color:#8B0000'>").replace("⟧", "</b>")
            snip = snip.replace("…", "<span style='color:#bbb'>…</span>")

            parts.append(
                "<div style='margin:0;padding:12px 0;"
                "border-bottom:1px solid #ececec'>"
                f"<a href='{scheme}' style='text-decoration:none'>"
                "<span style='font-variant:small-caps;font-weight:bold;"
                f"color:#2471a3;font-size:11.5pt'>{html.escape(cite)}</span></a>"
                + (
                    "  <span style='color:#aaa;font-size:9.5pt;"
                    f"font-style:italic'>{html.escape(work)}</span>"
                    if work
                    else ""
                )
                + xref
                + '<div style=\'font-family:"Gentium Plus",Gentium,'
                '"Noto Serif",serif;font-size:13pt;line-height:1.75;'
                f"color:#2b2b2b;margin-top:4px'>{snip}</div>"
                "</div>"
            )
        parts.append(self._pagination_html(page, total))
        parts.append("</div>")
        self._results.setHtml("".join(parts))

        self._stack.setCurrentIndex(1)
        self._info_label.setText(f"«{query}» — {first}–{last} de {total}")

    def _pagination_html(self, page: int, total: int) -> str:
        """Google-style numbered page bar (links use the 'srch:N' scheme)."""
        ps = self._PAGE_SIZE
        npages = (total + ps - 1) // ps
        if npages <= 1:
            return ""

        def lk(p, label=None, cur=False):
            label = label if label is not None else str(p + 1)
            if cur:
                return (
                    f"<span style='padding:3px 8px;font-weight:bold;"
                    f"color:#8B0000'>{label}</span>"
                )
            return (
                f"<a href='srch:{p}' style='padding:3px 8px;color:#2980b9;"
                f"text-decoration:none'>{label}</a>"
            )

        items = []
        if page > 0:
            items.append(lk(page - 1, "‹ Ant."))
        # windowed page numbers (current ±5), with first/last
        lo, hi = max(0, page - 5), min(npages, page + 6)
        if lo > 0:
            items.append(lk(0, "1"))
            if lo > 1:
                items.append("<span style='color:#bbb'>…</span>")
        for p in range(lo, hi):
            items.append(lk(p, cur=(p == page)))
        if hi < npages:
            if hi < npages - 1:
                items.append("<span style='color:#bbb'>…</span>")
            items.append(lk(npages - 1, str(npages)))
        if page < npages - 1:
            items.append(lk(page + 1, "Sig. ›"))
        return (
            "<div style='text-align:center;margin:22px 0 8px;"
            "font-size:11pt'>" + " ".join(items) + "</div>"
        )

    def _on_result_link(self, url):
        """Handle click on a search result link."""
        href = url.toString()
        if href.startswith("load:"):
            parts = href[5:].split(":")
            if len(parts) >= 2:
                self._load_book_page(int(parts[0]), int(parts[1]))
                self._stack.setCurrentIndex(0)  # Back to text view
        elif href.startswith("pref:") or href.startswith("appx:"):
            scheme, _, arg = href.partition(":")
            book = int(arg) if arg.isdigit() else None
            self._stack.setCurrentIndex(0)
            self._show_supplement(
                "preface" if scheme == "pref" else "appendix", book_no=book
            )
        elif href.startswith("srch:"):  # pagination link
            self._run_search(int(href[5:]))
        elif href.startswith("note:") or href.startswith("ref:"):
            # Bidirectional apparatus link: body superscript ↔ its note.
            self._text.scrollToAnchor(href)

    def _clear_search(self):
        """Close search results and return to text view."""
        self._search.clear()
        self._stack.setCurrentIndex(0)
        self._info_label.setText("")

    # ═══ COPY WITH CITATION ═══════════════════════════════════

    def _clean_selection(self, browser) -> str:
        """Selected text with line-number labels and block breaks normalised."""
        import re

        txt = browser.textCursor().selectedText()
        txt = self._NONCHAR_RX.sub("", txt)
        txt = re.sub(self._LN_OPEN + r"\s*\d+\s*" + self._LN_CLOSE, "", txt)
        txt = txt.replace(" ", "\n").replace(" ", "\n")
        txt = re.sub(r"[ \t]+", " ", txt)
        return txt.strip()

    def _line_at_cursor(self, browser) -> int | None:
        """PTS line number of the selection start (nearest preceding label)."""
        import re

        pos = browser.textCursor().selectionStart()
        doc_text = self._NONCHAR_RX.sub("", browser.toPlainText())
        first = last = None
        for m in re.finditer(self._LN_OPEN + r"\s*(\d+)\s*" + self._LN_CLOSE, doc_text):
            if first is None:
                first = int(m.group(1))
            if m.start() <= pos:
                last = int(m.group(1))
            else:
                break
        return last if last is not None else first

    def _selection_citation(self, browser) -> str:
        """PTS citation (sigla page,line) for the current selection."""
        if browser is self._comm_text:
            return f"Aṭṭh {self._comm_page}" if self._comm_page else ""
        if not self._current_book:
            return ""
        _, vol, ref = self._book_meta(self._current_book)
        sigla = ref or vol or f"Bk {self._current_book}"
        page = self._current_page or "?"
        line = self._line_at_cursor(browser)
        return f"{sigla} {page},{line}" if line else f"{sigla} {page}"

    def _plain_clean_copy(self, browser):
        """Ctrl+C that strips the invisible line-number labels."""
        text = self._clean_selection(browser)
        if text:
            QApplication.clipboard().setText(text)

    def _copy_with_citation(self, browser=None):
        if browser is None:
            browser = (
                self._comm_text
                if self._comm_text.textCursor().hasSelection()
                else self._text
            )
        text = self._clean_selection(browser)
        if not text:
            return
        cite = self._selection_citation(browser)
        QApplication.clipboard().setText(f"«{text}» ({cite})" if cite else f"«{text}»")
        self._info_label.setText(f"Copiado con cita: {cite}" if cite else "Copiado")

    def _text_context_menu(self, browser, pos):
        menu = browser.createStandardContextMenu()
        menu.addSeparator()
        a1 = menu.addAction("Copiar con cita")
        a1.triggered.connect(lambda: self._copy_with_citation(browser))
        a2 = menu.addAction("Copiar (sin números de línea)")
        a2.triggered.connect(lambda: self._plain_clean_copy(browser))
        menu.exec(browser.viewport().mapToGlobal(pos))

    # ═══ EXPORT ═══════════════════════════════════════════════

    def _get_page_data(self) -> dict:
        if self._db and self._current_book and self._current_page:
            return (
                self._db.get_page_by_book_and_page(
                    self._current_book, self._current_page
                )
                or {}
            )
        return {}

    def _export_html(self):
        p, _ = QFileDialog.getSaveFileName(
            self, "Exportar HTML", "tipitaka.html", "HTML (*.html)"
        )
        if p:
            export_html(self._get_page_data(), p)

    def _export_text(self):
        p, _ = QFileDialog.getSaveFileName(
            self, "Exportar texto", "tipitaka.txt", "Texto (*.txt)"
        )
        if p:
            export_text(self._get_page_data(), p)


class ExtractedAppImageWindow(TipitakaMainWindow):
    pass
