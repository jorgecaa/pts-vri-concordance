"""
Internationalization (i18n) module for Tipitaka PTS Browser.

Provides translations for Spanish (es) and English (en).
Uses a simple dictionary-based approach compatible with Qt's tr() system.
"""

from __future__ import annotations

from typing import Dict

# ── Translation dictionaries ─────────────────────────────────

_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "es": {
        # Menu
        "&File": "&Archivo",
        "&Export as HTML…": "&Exportar como HTML…",
        "Export as &text…": "Exportar como &texto…",
        "Export as &PDF…": "Exportar como &PDF…",
        "&Settings": "&Configuración",
        "E&xit": "&Salir",
        "&View": "&Ver",
        "&Dark theme": "Tema &oscuro",
        "&Line numbers": "&Números de línea",
        "&Thai script": "Escritura &Tailandesa",
        "&Tools": "&Herramientas",
        "&Dictionary": "&Diccionario",
        "&Help": "A&yuda",
        "&About": "&Acerca de",
        # Toolbar
        "Citation:": "Cita:",
        "Load": "Cargar",
        "Edition:": "Edición:",
        "Search in the Pali Canon…": "Buscar en el Canon Pāli…",
        # Navigation
        "Navigation": "Navegación",
        "Filter navigation…": "Filtrar navegación…",
        "Search Results": "Resultados de búsqueda",
        "Bookmarks": "Marcadores",
        "History": "Historial",
        # Bottom tabs
        "Dictionary": "Diccionario",
        "Search": "Búsqueda",
        "Apparatus": "Apparatus",
        # Dictionary
        "Look up word in dictionary…": "Buscar palabra en diccionario…",
        "Search word or phrase…": "Buscar palabra o frase…",
        "Book:": "Libro:",
        "All": "Todos",
        # Status
        "Ready": "Listo",
        "Loading…": "Cargando…",
        "Select a text to view…": "Selecciona un texto para visualizarlo…",
        "Text not found: {0}": "Texto no encontrado: {0}",
        "Loading {0}…": "Cargando {0}…",
        "Searching: {0}…": "Buscando: {0}…",
        "Search: '{0}' — {1} results": "Búsqueda: '{0}' — {1} resultados",
        "No results found": "Sin resultados",
        "Exported: {0}": "Exportado: {0}",
        # Apparatus
        "Apparatus Criticus": "Apparatus Criticus",
        "No apparatus criticus for this page.": "No hay apparatus criticus para esta página.",
        # Errors
        "Error": "Error",
        "Load Error": "Error de carga",
        "Could not load {0}": "No se pudo cargar {0}",
        "Search Error": "Error de búsqueda",
        "Could not complete search: {0}": "No se pudo completar la búsqueda: {0}",
        "Dictionary Error": "Error de diccionario",
        "Could not look up '{0}'": "No se pudo buscar '{0}'",
        "Could not export the text.": "No se pudo exportar el texto.",
        # About
        "Tipitaka PTS Browser\n\nPali Tipitaka viewer with PTS/ROTA edition.\nVersion 1.1.0 — Refactored UI.": "Tipitaka PTS Browser\n\nVisor del Tipiṭaka en edición PTS/ROTA.\nVersión 1.1.0 — UI refactorizada.",
        # Settings
        "Settings": "Configuración",
        "Settings dialog will be available in Phase 5.": "El diálogo de configuración estará disponible en la Fase 5.",
    },
    "en": {},  # English is the source language, no overrides needed
}

# ── Current language ─────────────────────────────────────────

_current_lang = "es"


def set_language(lang: str):
    """Set the current UI language."""
    global _current_lang
    if lang in _TRANSLATIONS:
        _current_lang = lang


def get_language() -> str:
    """Get the current UI language code."""
    return _current_lang


def tr(text: str, *args) -> str:
    """Translate a string to the current language.

    Args:
        text: The English source string.
        *args: Optional format arguments.

    Returns:
        Translated string with any format args applied.
    """
    translations = _TRANSLATIONS.get(_current_lang, {})
    result = translations.get(text, text)
    if args:
        try:
            result = result.format(*args)
        except (IndexError, KeyError):
            pass
    return result


# ── Convenience aliases ──────────────────────────────────────

_ = tr  # Alias for brevity
