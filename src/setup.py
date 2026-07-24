#!/usr/bin/env python3
"""
Setup script for Tipitaka PTS Browser.

This script handles package installation and distribution.
"""

import os
import sys
from pathlib import Path

from setuptools import find_packages, setup

# Read the README file for long description
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = (
        "Tipitaka PTS Browser - A tool for browsing and studying Pali Tipitaka texts"
    )

# Read version from main package
version_path = Path(__file__).parent / "main" / "__init__.py"
version = "1.0.0"
if version_path.exists():
    with open(version_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                version = line.split("=")[1].strip().strip("\"'")
                break

setup(
    name="tipitaka-pts-browser",
    version=version,
    description="A tool for browsing and studying Pali Tipitaka texts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Tipitaka PTS Browser Team",
    author_email="tipitaka@example.com",
    url="https://github.com/example/tipitaka-pts-browser",
    license="GPL-3.0",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Religion",
        "Topic :: Education",
        "Topic :: Religion",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
    ],
    keywords="tipitaka pali buddhism text browser education",
    packages=find_packages(include=["main", "main.*"]),
    package_dir={"": "."},
    include_package_data=True,
    install_requires=[
        "PyQt6>=6.5.0",
        "PyQt6-Qt6>=6.5.0",
        "PyQt6-sip>=13.5.0",
        "rapidfuzz>=3.0.0",
        "python-Levenshtein>=0.21.0",
        "charset-normalizer>=3.0.0",
        "royalthai>=0.1.0",
        "wcwidth>=0.2.0",
    ],
    extras_require={
        "dev": [
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pytest>=7.0.0",
            "pytest-qt>=4.0.0",
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "full": [
            "pandas>=2.0.0",
            "numpy>=1.24.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "tipitaka-pts-browser=main.__init__:main",
            "tipitaka-cli=main.__init__:run_cli",
        ],
        "gui_scripts": [
            "tipitaka-gui=main.__init__:main",
        ],
    },
    python_requires=">=3.8",
    project_urls={
        "Bug Reports": "https://github.com/example/tipitaka-pts-browser/issues",
        "Source": "https://github.com/example/tipitaka-pts-browser",
        "Documentation": "https://tipitaka-pts-browser.readthedocs.io/",
    },
)
