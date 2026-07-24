# Tipitaka PTS Browser - User Guide
## Enhanced Edition with ROTA Support

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Interface Overview](#interface-overview)
4. [Working with Texts](#working-with-texts)
5. [Search Features](#search-features)
6. [Dictionary Usage](#dictionary-usage)
7. [Apparatus Criticus](#apparatus-criticus)
8. [Settings and Configuration](#settings-and-configuration)
9. [Tips and Tricks](#tips-and-tricks)
10. [Troubleshooting](#troubleshooting)

## Introduction

Welcome to the Tipitaka PTS Browser Enhanced Edition! This application is designed for scholars, students, and practitioners who study Pali Tipitaka texts. The enhanced edition includes:

- **ROTA Edition Support**: Access to the Royal Thai Tipitaka (Syāmaraṭṭha edition)
- **Advanced Search**: Multiple search modes with fuzzy matching
- **Apparatus Criticus**: View manuscript variants and textual differences
- **Enhanced Dictionary**: Comprehensive Pali dictionary with sub-entries
- **Modern Interface**: Clean, intuitive Qt-based interface

### System Requirements
- **Operating System**: Linux, Windows, or macOS
- **Memory**: 2GB RAM minimum, 4GB recommended
- **Storage**: 500MB for application and data
- **Display**: 1024x768 resolution minimum

## Getting Started

### First Launch
When you first launch the application, you'll see the main window with:
- Left panel: Navigation and search results
- Center panel: Text display
- Right panel: Dictionary and apparatus criticus

### Loading Your First Text
1. **Using PTS Citations**: Enter a standard PTS citation in the search bar:
   - Examples: "M I 3" (Majjhima Nikāya, Volume I, Page 3)
   - "Sn 25" (Sutta Nipāta, Page 25)
   - "S.IV.100" (Saṃyutta Nikāya, Volume IV, Page 100)

2. **Select Edition**: Choose between:
   - **ROTA**: Royal Thai Tipitaka (Romanized Pali with diacritics)
   - **PTS**: Pali Text Society edition (legacy)

3. **Press Enter** or click the search button to load the text.

### Quick Start Example
Try loading these sample texts to get started:
- "M I 1" - First page of Majjhima Nikāya
- "D 1" - First page of Dīgha Nikāya
- "Sn 1" - First page of Sutta Nipāta

## Interface Overview

### Main Window Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Menu Bar: File, Search, View, Bookmarks, Tools, Help               │
├─────────────────────────────────────────────────────────────────────┤
│  Toolbar: Navigation, Edition selector, Search, Dictionary, etc.    │
├───────┬──────────────────────────────────────────────┬──────────────┤
│       │                                              │              │
│ Left  │               Main Text Area                 │   Right      │
│ Panel │                                              │    Panel     │
│       │                                              │              │
│       │                                              │              │
├───────┴──────────────────────────────────────────────┴──────────────┤
│  Status Bar: Current text, edition, word count, apparatus info      │
└─────────────────────────────────────────────────────────────────────┘
```

### Left Panel
- **ROTA Books**: List of available books in the ROTA edition
- **Search Results**: Results from your searches with relevance scores

### Center Panel (Main Text Area)
- Displays the selected text
- Line numbers (configurable)
- Word wrap (configurable)
- Context menu for quick actions

### Right Panel
- **Dictionary**: Quick lookup and results
- **Apparatus Criticus**: List of manuscript variants for current page

### Toolbar Icons
- ◀ **Previous**: Navigate back in history
- ▶ **Next**: Navigate forward (when available)
- 📖 **Dictionary**: Open dictionary window
- 🔬 **Apparatus**: Open apparatus criticus window
- 📊 **Statistics**: View application statistics
- ⭐ **Bookmark**: Add current position as bookmark

## Working with Texts

### Loading Texts
There are several ways to load texts:

1. **Direct Citation Entry**
   - Type a PTS citation in the main search bar
   - Press Enter or click the search icon

2. **From Search Results**
   - Perform a search
   - Click any result to load that text

3. **From ROTA Books List**
   - Browse the ROTA books in the left panel
   - Click any book to load its first page

4. **From Bookmarks**
   - Access saved bookmarks from the Bookmarks menu
   - Click any bookmark to return to that position

### Navigation
- **Forward/Back**: Use the ◀ ▶ buttons or Alt+Left/Right arrows
- **Scroll**: Mouse wheel or scroll bars
- **Zoom**: Ctrl+Plus/Minus or from View menu
- **Line Navigation**: Click line numbers or use Page Up/Down

### Text Selection and Copy
- **Select Text**: Click and drag with mouse
- **Copy**: Ctrl+C or right-click → Copy
- **Select All**: Ctrl+A
- **Context Menu**: Right-click for additional options:
  - Look up in dictionary
  - Search for selected text
  - Add bookmark at cursor position
  - Get word statistics

### Text Display Options
From the View menu or settings:
- **Font Size**: Adjust text size (Ctrl+Plus/Minus, Ctrl+0 to reset)
- **Line Numbers**: Show/hide line numbers
- **Word Wrap**: Enable/disable text wrapping
- **Apparatus Display**: Show/hide apparatus criticus panel

## Search Features

### Search Modes
The application offers four search modes:

1. **Text Search** (Default)
   - Searches through the full text content
   - Returns passages containing the search terms
   - Best for finding specific phrases or concepts

2. **Word Search**
   - Searches for individual words
   - More precise than text search
   - Useful for finding specific vocabulary

3. **Fuzzy Search**
   - Finds approximate matches
   - Adjustable threshold (0.1-1.0)
   - Useful for finding variant spellings or damaged text

4. **Exact Search**
   - Matches the exact search string
   - Case-sensitive
   - Most precise but least flexible

### Performing a Search
1. **Enter your query** in the search field
2. **Select search mode** from the dropdown (Text, Word, Fuzzy, Exact)
3. **Adjust fuzzy threshold** if using fuzzy search (from Settings)
4. **Press Enter** or click the search button

### Search Results
Results appear in the left panel with:
- **Title**: Book name and location
- **Score**: Relevance score (0.0-1.0)
- **Snippet**: Context around the match
- **Apparatus Count**: Number of variants at that location

Click any result to:
- Load the text at that location
- See the matched text highlighted
- View apparatus variants for that page

### Advanced Search Tips
- **Phrase Search**: Use quotes for exact phrases: `"anicca vata sankhara"`
- **Boolean Operators**: Not currently supported
- **Wildcards**: Not currently supported
- **Multiple Words**: Space-separated words are searched independently

### Search History
- Recent searches are saved automatically
- Access from Search → Search History menu
- Clear history from Search → Clear Search Cache

## Dictionary Usage

### Quick Lookup
1. **From Text Selection**:
   - Select a word in the text
   - Right-click → "Look Up in Dictionary"
   - Or use the dictionary icon in the toolbar

2. **Direct Entry**:
   - Type a word in the dictionary field (right panel)
   - Press Enter
   - Or use the dedicated dictionary window

### Dictionary Window
Access via 📖 icon or Tools → Dictionary:
- **Search Field**: Enter any Pali word
- **Results**: Detailed dictionary entry including:
  - Headword and variants
  - Definition and etymology
  - Examples from texts
  - Sub-entries (if available)
  - Source information

### Dictionary Features
- **Fuzzy Matching**: Finds similar words if exact match not found
- **Sub-entry Support**: Handles notations like "a-^1", "dhamma^2"
- **Cache System**: Recently looked-up words load faster
- **Multiple Sources**: PTS Dictionary and Critical Pali Dictionary (CPD)

### Using Dictionary Results
- **Copy Definitions**: Select and copy text
- **Navigate to Examples**: Click on example citations to load those texts
- **View Variants**: See different manuscript readings
- **Track History**: Recent lookups are saved

## Apparatus Criticus

### What is Apparatus Criticus?
The apparatus criticus shows manuscript variants - different readings of the same text found in various historical manuscripts. This is crucial for textual criticism and understanding textual transmission.

### Viewing Apparatus
1. **Automatic Display**: When `Show Apparatus` is enabled (View menu), variants appear:
   - In the right panel as a list
   - As a summary bar above the text (if variants exist)

2. **Detailed View**: Click the 🔬 icon or Tools → Apparatus to open the full apparatus window.

### Understanding Variant Display
Each variant shows:
- **Sigla**: Manuscript abbreviation (e.g., Cb, Ba, Bb)
- **Type**: Type of variant (addition, omission, substitution, etc.)
- **Text**: The variant reading
- **Notes**: Additional information (if available)

### Common Sigla (Manuscript Abbreviations)
- **Cb**: Cambridge manuscript
- **Ba**: Bangkok A manuscript
- **Bb**: Bangkok B manuscript
- **Bc**: Bangkok C manuscript
- **L**: London manuscript
- **P**: Paris manuscript
- **R**: Rome manuscript
- **S**: Sri Lanka manuscript
- **T**: Thai manuscript
- **U**: Uppsala manuscript
- **V**: Vatican manuscript

### Interacting with Variants
- **Click any variant** to see detailed information
- **Copy variant text** for notes or analysis
- **Compare variants** side by side
- **Filter by sigla** (planned feature)

### Apparatus Statistics
- **Total Variants**: Number of variants for current page
- **By Type**: Distribution of variant types
- **By Manuscript**: Which manuscripts have variants

## Settings and Configuration

### Accessing Settings
- **Menu**: File → Settings
- **Shortcut**: Ctrl+Comma (,) or Ctrl+P
- **Toolbar**: Settings icon (if available)

### General Settings
- **Language**: Interface language (English, Spanish, French, German)
- **Default Edition**: Which edition to use by default (ROTA or PTS)
- **Font Size**: Base font size for text display

### Search Settings
- **Default Search Mode**: Which search mode to use by default
- **Fuzzy Threshold**: Sensitivity for fuzzy search (0.1-1.0)
- **Max Results**: Maximum number of search results to display

### Display Settings
- **Show Line Numbers**: Toggle line number display
- **Show Apparatus**: Toggle apparatus criticus display
- **Word Wrap**: Toggle text wrapping

### Dictionary Settings
- **Dictionary Sources**: Which dictionaries to search
  - PTS Dictionary
  - Critical Pali Dictionary (CPD)
- **Cache Settings**: Enable/disable dictionary caching

### Advanced Settings
- **Auto-save Bookmarks**: Automatically save bookmark changes
- **Enable Caching**: Enable performance caching
- **Clear All Caches**: Remove all cached data

### Saving and Applying Settings
- **Apply**: Save settings and apply immediately
- **Cancel**: Discard changes
- **Reset to Defaults**: Restore factory settings

### Configuration Files
Settings are stored in:
- **Linux**: `~/.local/share/tipitaka-pts-browser/settings.json`
- **Windows**: `%APPDATA%\tipitaka-pts-browser\settings.json`
- **macOS**: `~/Library/Application Support/tipitaka-pts-browser/settings.json`

You can edit this file directly for advanced configuration.

## Tips and Tricks

### Keyboard Shortcuts Reference

| Shortcut | Action |
|----------|--------|
| `Ctrl+F` | Focus search field |
| `Ctrl+S` | Perform search |
| `Ctrl+D` | Open dictionary |
| `Ctrl+B` | Add bookmark |
| `Ctrl+,` or `Ctrl+P` | Open settings |
| `Ctrl+Q` | Quit application |
| `Ctrl+Plus` | Increase font size |
| `Ctrl+Minus` | Decrease font size |
| `Ctrl+0` | Reset font size |
| `Alt+Left` | Navigate back |
| `Alt+Right` | Navigate forward |
| `F1` | Help |
| `F5` | Refresh display |
| `Esc` | Close dialog/popup |

### Efficient Study Workflow
1. **Start with a Citation**: Load a specific text using PTS notation
2. **Use Search**: Find related passages or concepts
3. **Check Dictionary**: Look up unfamiliar terms
4. **Examine Apparatus**: Consider textual variants
5. **Bookmark Insights**: Save important findings
6. **Compare Editions**: Switch between ROTA and PTS views

### Research Techniques
- **Textual Analysis**: Use apparatus criticus to study manuscript traditions
- **Word Studies**: Search for specific terms across the canon
- **Comparative Reading**: Compare similar passages in different texts
- **Citation Tracking**: Follow references through the citation system

### Performance Tips
- **Enable Caching**: Significantly improves search and dictionary performance
- **Limit Results**: Reduce max search results for faster searches
- **Clear Cache Periodically**: Frees memory and ensures fresh data
- **Use Appropriate Search Mode**: Choose the simplest mode that meets your needs

### Data Management
- **Backup Your Data**: Regularly backup the data directory
- **Organize Bookmarks**: Use descriptive notes for bookmarks
- **Export Important Texts**: Use copy/paste to save passages
- **Maintain Database**: Keep the SQLite database optimized

## Troubleshooting

### Common Issues and Solutions

#### Application Won't Start
1. **Check Dependencies**:
   ```bash
   # On Ubuntu/Debian
   sudo apt install python3-pyqt6 python3-pyqt6.qtmultimedia
   
   # Check Python version
   python3 --version
   ```

2. **Check Database File**:
   - Ensure `tipitaka.sqlite` exists in the data directory
   - Verify file permissions: `chmod 644 tipitaka.sqlite`

3. **Check Logs**:
   ```bash
   TIPITAKA_DEBUG=1 tipitaka-pts-browser
   # Check ~/.local/share/tipitaka-pts-browser/tipitaka.log
   ```

#### Text Not Displaying
1. **Check Edition Selection**:
   - Ensure you've selected the correct edition (ROTA/PTS)
   - Try switching editions

2. **Check Citation Format**:
   - Use standard PTS format: "M I 3", "Sn 25", "S.IV.100"
   - Avoid extra spaces or punctuation

3. **Database Issues**:
   ```bash
   sqlite3 tipitaka.sqlite "SELECT COUNT(*) FROM Dbf1__palipg;"
   # Should return 15561 or similar
   ```

#### Search Not Working
1. **Check Search Mode**:
   - Try different search modes (Text, Word, Fuzzy, Exact)
   - Adjust fuzzy threshold for fuzzy search

2. **Clear Search Cache**:
   - Go to Search → Clear Search Cache
   - Or Tools → Clear All Caches

3. **Database Index**:
   - Search requires the word index table `Dbf1__wordat`
   - Verify it exists: `SELECT COUNT(*) FROM Dbf1__wordat;`

#### Dictionary Lookup Failing
1. **Check Dictionary Sources**:
   - Verify dictionary sources are enabled in Settings
   - Try both PTS and CPD dictionaries

2. **Clear Dictionary Cache**:
   - Tools → Clear All Caches
   - Or restart the application

3. **Word Format**:
   - Use dictionary form of words (nominative singular for nouns)
   - Try removing diacritics for difficult words

#### Slow Performance
1. **Enable Caching**:
   - Ensure caching is enabled in Settings
   - Clear and rebuild cache if needed

2. **Reduce Search Results**:
   - Lower "Max Results" in search settings
   - Use more specific search terms

3. **System Resources**:
   - Close other applications
   - Ensure adequate free memory

#### Apparatus Criticus Not Showing
1. **Check Display Setting**:
   - Verify "Show Apparatus" is enabled in View menu
   - Check if current page has variants (not all do)

2. **Database Content**:
   - Apparatus data comes from `Dbf1__footpg` table
   - Verify it contains data for your current book/page

3. **Cache Issues**:
   - Clear apparatus cache: Tools → Clear All Caches
   - Reload the page

### Error Messages

#### "Database not found"
- **Solution**: Place `tipitaka.sqlite` in the data directory
- **Default locations**:
  - Linux: `~/.local/share/tipitaka-pts-browser/`
  - Windows: `%APPDATA%\tipitaka-pts-browser\`
  - Or in the application's `data/` folder

#### "Unable to decode text"
- **Solution**: This usually indicates encoding issues with UNITEXT
- **Workaround**: Try the PTS edition instead of ROTA
- **Advanced**: Check database encoding with a SQLite browser

#### "Citation not found"
- **Solution**:
  1. Verify citation format
  2. Check if the citation exists in the database
  3. Try similar citations (adjacent pages)

#### "Memory allocation failed"
- **Solution**:
  1. Close other applications
  2. Reduce max search results
  3. Clear all caches
  4. Restart the application

### Getting Help

#### Application Logs
Enable detailed logging:
```bash
TIPITAKA_DEBUG=1 tipitaka-pts-browser
```
Logs are saved to: `~/.local/share/tipitaka-pts-browser/tipitaka.log`

#### Database Verification
Check database integrity:
```bash
sqlite3 tipitaka.sqlite "PRAGMA integrity_check;"
sqlite3 tipitaka.sqlite "VACUUM;"
```

#### Community Support
- **GitHub Issues**: Report bugs and request