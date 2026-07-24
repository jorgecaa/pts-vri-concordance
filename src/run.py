#!/usr/bin/env python3
"""
Tipitaka PTS Browser — Run script.

Usage:
  python run.py              # GUI mode (default)
  python run.py test         # Run tests
  python run.py check        # Check dependencies
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def run_gui():
    """Launch the Tipitaka browser GUI."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QApplication

    # Import the GUI (and, transitively, QtWebEngineWidgets) before constructing
    # QApplication — QtWebEngine requires this. Also share GL contexts, which it
    # recommends when embedding a QWebEngineView (the DPD dictionary panel).
    from main.extracted_appimage_gui import TipitakaMainWindow

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationName("Tipitaka PTS Browser")
    app.setApplicationVersion("1.3.0")

    icon_path = Path(__file__).parent / "data" / "icons" / "pts-logo.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    root_dir = Path(__file__).parent.parent
    try:
        window = TipitakaMainWindow(root_dir)
        window.show()
    except Exception as e:
        print(f"Error starting GUI: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(app.exec())


def run_tests():
    """Run the test suite with pytest."""
    try:
        import pytest

        test_dir = Path(__file__).parent / "tests"
        sys.exit(pytest.main([str(test_dir), "-v"]))
    except ImportError:
        print("pytest not installed. Install with: pip install pytest")
        sys.exit(1)


def check_dependencies():
    """Check if all required dependencies are installed."""
    deps = {
        "PyQt6": "PyQt6",
        "rapidfuzz": "rapidfuzz",
        "charset-normalizer": "charset_normalizer",
    }
    missing = []
    for name, imp in deps.items():
        try:
            __import__(imp)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name}")
            missing.append(name)

    import shutil

    if shutil.which("xelatex"):
        print("  ✓ xelatex (TeX Live)")
    else:
        print("  — xelatex (optional, for PDF generation)")

    if missing:
        print(f"\nMissing: {', '.join(missing)}")
        print(f"Install: pip install {' '.join(missing)}")
        sys.exit(1)
    else:
        print("\nAll dependencies installed.")


def main():
    parser = argparse.ArgumentParser(description="Tipitaka PTS Browser")
    parser.add_argument(
        "mode",
        nargs="?",
        default="gui",
        choices=["gui", "test", "check"],
        help="Run mode (default: gui)",
    )
    args = parser.parse_args()

    if args.mode == "test":
        run_tests()
    elif args.mode == "check":
        check_dependencies()
    else:
        run_gui()


if __name__ == "__main__":
    main()
