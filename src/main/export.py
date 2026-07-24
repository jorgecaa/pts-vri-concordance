"""
Export module for Tipitaka PTS Browser.

Supports exporting Pali texts to HTML and plain text formats.
PDF export uses weasyprint if available.
"""

from __future__ import annotations

import html as _html
from pathlib import Path
from typing import Any, Dict, Optional


def export_html(
    page_data: Dict[str, Any],
    output_path: str | Path,
    title: str = "",
    include_apparatus: bool = True,
) -> bool:
    """Export a page as styled HTML file.

    Args:
        page_data: Dict with 'text', 'head', 'book_no', 'page_num', 'apparatus'
        output_path: Where to save the HTML file
        title: Optional title override (uses head field if empty)
        include_apparatus: Whether to include apparatus criticus

    Returns:
        True if successful
    """
    try:
        text = page_data.get("text", "")
        head = page_data.get("head", "")
        apparatus = page_data.get("apparatus", "")
        book_no = page_data.get("book_no", "")
        page_num = page_data.get("page_num", "")

        display_title = title or head or f"Book {book_no}, Page {page_num}"

        # Build HTML document
        html_parts = [
            "<!DOCTYPE html>",
            '<html lang="pi">',
            "<head>",
            '<meta charset="UTF-8">',
            f"<title>{_html.escape(display_title)}</title>",
            "<style>",
            "  body {",
            "    font-family: 'Gentium Plus', 'FreeSerif', 'Noto Serif', serif;",
            "    font-size: 14pt;",
            "    line-height: 1.8;",
            "    max-width: 800px;",
            "    margin: 40px auto;",
            "    padding: 0 20px;",
            "    color: #1a1a1a;",
            "    background: #fff;",
            "  }",
            "  h1 { font-size: 18pt; color: #8B0000; border-bottom: 2px solid #8B0000;",
            "       padding-bottom: 8px; }",
            "  .text { white-space: pre-wrap; }",
            "  .folio { color: #7f8c8d; font-size: 10pt; }",
            "  .variant { color: #c0392b; font-style: italic; }",
            "  .apparatus {",
            "    margin-top: 30px;",
            "    padding-top: 20px;",
            "    border-top: 2px solid #ccc;",
            "    font-size: 10pt;",
            "    font-family: monospace;",
            "    line-height: 1.4;",
            "    color: #555;",
            "  }",
            "  .apparatus h2 { font-size: 12pt; color: #555; }",
            "  .meta { color: #999; font-size: 10pt; margin-bottom: 30px; }",
            "  @media print {",
            "    body { font-size: 12pt; }",
            "    .apparatus { page-break-before: always; }",
            "  }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{_html.escape(display_title)}</h1>",
            f'<p class="meta">Book {book_no} · Page {page_num}</p>',
            '<div class="text">',
            _format_text_for_export(text),
            "</div>",
        ]

        if include_apparatus and apparatus:
            html_parts.append('<div class="apparatus">')
            html_parts.append("<h2>Apparatus Criticus</h2>")
            html_parts.append(f"<pre>{_html.escape(apparatus)}</pre>")
            html_parts.append("</div>")

        html_parts.append("</body></html>")
        html_content = "\n".join(html_parts)

        Path(output_path).write_text(html_content, encoding="utf-8")
        return True
    except Exception as e:
        print(f"Error exporting HTML: {e}")
        return False


def export_text(
    page_data: Dict[str, Any],
    output_path: str | Path,
    include_apparatus: bool = False,
) -> bool:
    """Export a page as plain UTF-8 text.

    Args:
        page_data: Dict with 'text', 'head', 'apparatus'
        output_path: Where to save the text file
        include_apparatus: Whether to include apparatus criticus

    Returns:
        True if successful
    """
    try:
        text = page_data.get("text", "")
        head = page_data.get("head", "")
        apparatus = page_data.get("apparatus", "")

        lines = []
        if head:
            lines.append(head)
            lines.append("=" * len(head))
            lines.append("")

        lines.append(text)
        lines.append("")

        if include_apparatus and apparatus:
            lines.append("─" * 40)
            lines.append("APPARATUS CRITICUS")
            lines.append("─" * 40)
            lines.append(apparatus)

        Path(output_path).write_text("\n".join(lines), encoding="utf-8")
        return True
    except Exception as e:
        print(f"Error exporting text: {e}")
        return False


def export_pdf(
    page_data: Dict[str, Any],
    output_path: str | Path,
    title: str = "",
    include_apparatus: bool = True,
) -> bool:
    """Export a page as PDF (requires weasyprint).

    Args:
        page_data: Dict with 'text', 'head', 'book_no', 'page_num', 'apparatus'
        output_path: Where to save the PDF file
        title: Optional title override
        include_apparatus: Whether to include apparatus criticus

    Returns:
        True if successful
    """
    try:
        from weasyprint import HTML

        # Generate HTML first
        html_path = Path(output_path).with_suffix(".temp.html")
        if not export_html(page_data, html_path, title, include_apparatus):
            return False

        HTML(filename=str(html_path)).write_pdf(str(output_path))
        html_path.unlink()  # Clean up temp file
        return True
    except ImportError:
        print("weasyprint not installed. Install with: pip install weasyprint")
        return False
    except Exception as e:
        print(f"Error exporting PDF: {e}")
        return False


def _format_text_for_export(text: str) -> str:
    """Format Pali text with inline styling for export."""
    import re as _re

    escaped = _html.escape(text)

    # Variant readings {word}
    escaped = _re.sub(
        r"\{([^}]+)\}",
        r'<span class="variant">\1</span>',
        escaped,
    )
    # Folio markers [F.N]
    escaped = _re.sub(
        r"\[F\.(\d+[vr]?)\]",
        r'<span class="folio">[F.\1]</span>',
        escaped,
    )
    # Line breaks
    escaped = escaped.replace("\n", "<br>")

    return escaped
