# tipitaka.sqlite — Developer Reference

Documentation for the SQLite database that backs the Tipitaka PTS Browser. The data
originates from the Dhammakaya Foundation's **PaliText V2.5** (a Visual FoxPro 9 application),
but this file has since been **rebuilt into a clean, application-friendly schema**: legacy
`Dbf1__*` / `Dbf__*` tables were renamed and normalised, the FoxPro encodings were decoded to
plain UTF-8, logically-deleted rows and app/system tables were dropped, and several new tables
were added (commentaries, translations, cross-references, a navigation tree, and an FTS5 index).

> **This document describes the current rebuilt schema.** If you find references to
> `Dbf1__palipg`, BOM+Base64 `UNITEXT`, `_deleted`, or offset-encoded page keys elsewhere, they
> describe the *old* FoxPro-derived layout and no longer apply to page/text access. (The
> offset-encoding scheme still survives in the word-concordance tables — see §7.)

> **Edition identity.** The `edition` value `'mula'` is the **Pali Text Society (PTS)**
> roman-script canon, and `'atthakatha'` is the PTS commentaries (Aṭṭhakathā). The historical
> source-app label for this text was `'ROTA'`, which led an earlier revision to call it the
> *Syāmaraṭṭha / Royal Thai* edition — **that was wrong.** It is PTS: pagination matches the PTS
> volumes exactly (MN I = 524 pp., DN I = 253, SN I = 240, Sn = 223…), the preface pages read
> *"… Pali Text Society … First Published 1879 …"*, and the appendix pages are the PTS *"Various
> Readings"* apparatus. Treat any lingering `'ROTA'`/`'ROTB'` label as **PTS**.

---

## Contents

1. [At a glance](#1-at-a-glance)
2. [Editions](#2-editions)
3. [Encoding reference](#3-encoding-reference)
4. [Core text tables](#4-core-text-tables) — `pages`, `footnotes`
5. [Structure & navigation](#5-structure--navigation) — `books`, `toc`, `contents`, `chapter_marks`, `nav_tree`
6. [Supplementary & external references](#6-supplementary--external-references) — `pts_prefaces`, `pts_appendices`, `pts_xref`, `translation_en`, `translation_sujato`
7. [Word-concordance tables](#7-word-concordance-tables) — `word_list`, `word_occurrences`, `word_counts`
8. [Dictionary tables](#8-dictionary-tables) — `dict_pts`, `dict_pali_english`
9. [Full-text search (`pali_fts`)](#9-full-text-search-pali_fts)
10. [Relationships and joins](#10-relationships-and-joins)
11. [Inline markup in text](#11-inline-markup-in-text)
12. [Complete book / volume listing](#12-complete-book--volume-listing)
13. [Query recipes](#13-query-recipes)
14. [Known data quirks](#14-known-data-quirks)
15. [Table summary](#15-table-summary)

---

## 1. At a glance

| Item | Value |
|------|-------|
| File | `src/data/tipitaka.sqlite` |
| Size on disk | ≈ 343 MB |
| Tables | 23 (+ FTS5 shadow tables) |
| Editions | `mula` (PTS canon, books 1–53) and `atthakatha` (PTS commentaries, books 1–58) |
| Source | Dhammakaya Foundation, PaliText V2.5 (VFP9), rebuilt to this schema |
| Script | Romanised Pāli (IAST) — **stored as plain UTF-8** |
| Full text | `pali_fts` (FTS5) over pages, prefaces, appendices |

Text access is now direct: filter by `edition`, `book_no`, `page_no` and read `unitext` — no
Base64, no BOM, no `_deleted` filter, no offset-key decoding. The offset encoding survives only
in the word-concordance tables (§7), which most consumers can ignore in favour of `pali_fts`.

---

## 2. Editions

The `editions` table is the registry; every text/structure table carries a matching `edition`
column (`'mula'` or `'atthakatha'`).

```
id           name                 description
'mula'       'PTS — Canon'        Pali Text Society roman-script Tipiṭaka (canonical mūla text)
'atthakatha' 'PTS — Aṭṭhakathā'   Pali Text Society roman-script commentaries (Aṭṭhakathā)
```

- `mula`: 53 books, 15,554 pages.
- `atthakatha`: 58 books, 16,634 pages. The commentary book→work mapping (sigla, mūla text
  commented) lives in the repo's `book_meta.py` and is documented in `../../README-COMMY.md`.
- **`book_no` is only unique *within* an edition** — always constrain `edition` in joins and
  lookups, or a query for "book 26" will mix Suttanipāta (mula) with a commentary volume.

---

## 3. Encoding reference

The rebuild decoded almost everything to standard Unicode. Summary:

| Field | Encoding |
|-------|----------|
| `pages.unitext`, `pages.head`, `pages.head_old` | **Plain UTF-8** |
| `footnotes.unitext` | **Plain UTF-8** (critical apparatus) |
| `toc.name`, `contents.section`, `contents.title` | **Plain UTF-8** (decoded section/sutta titles) |
| `pts_prefaces.text`, `pts_appendices.text` | **Plain UTF-8** (line breaks are `\r`) |
| `chapter_marks.wordmark` | **Plain UTF-8** (romanised Pāli) |
| `dict_pts.ttitle` / `.tdetail` | **Plain UTF-8** (`ttitle` uses `^` sub-entry notation, e.g. `a-^1`) |
| `translation_en.text`, `translation_sujato.text`, `nav_tree.text` | **Plain UTF-8** |
| `pts_xref.vri`, `pts_xref.thai` | **Plain UTF-8** reference strings |
| `pages.encpali` | ⚠️ **Legacy** Base64 → Unicode PUA (Thai-font glyphs). Undocumented, **do not use**; `unitext` has the same text in real Unicode. |
| `books.book_name` | ⚠️ **Garbled** cp850/cp874 Thai bytes — not recoverable. Use `s_name` instead. |
| `dict_pali_english.ttitle`, `.tdetail` | ⚠️ Thai/legacy bytes — partially garbled. Use `etitle`/`edetail` (English) for reliable text. |
| `word_list.*`, `word_occurrences.*` keys | ⚠️ **Offset-encoded** (see §7). |

So the once-mandatory `decode()` helper is **no longer needed** for reading text: `SELECT
unitext FROM pages …` returns display-ready Pāli.

---

## 4. Core text tables

### 4.1 `pages` — one row per page (32,188 rows)

Main text, one row per printed page, for both editions.

| Column | Type | Notes |
|--------|------|-------|
| `edition` | TEXT | `'mula'` or `'atthakatha'` |
| `book_no` | INTEGER | Book within the edition (see §12) |
| `page_no` | INTEGER | PTS page number within the book |
| `book_key` | TEXT | Legacy 2-char offset key (join key to `word_occurrences`) |
| `page_key` | TEXT | Legacy 2-char offset key (join key to `word_occurrences`) |
| `head` | TEXT | Running header from the printed page (plain UTF-8) |
| `head_old` | TEXT | Prior/raw header variant |
| `footnline` | INTEGER | Number of apparatus lines on this page (0 = none) |
| `unitext` | TEXT | **Primary text** — plain UTF-8 Pāli |
| `encpali` | TEXT | Legacy PUA encoding — **ignore** (§3) |
| `wordnextpa` | TEXT | First word of the next page (cross-page concordance aid) |
| `commentwdc` | TEXT | Commentary reference code (legacy) |

> ⚠️ **`head` is not reliable as ground truth.** It is the printed running header and can be
> empty, carry a stray `^`/page number, or (in some volumes) name the wrong sutta. For
> content-based work, validate against `unitext` (the page body), not `head`. See `../../README.md`
> and `../../STATUS.md` in the concordance pipeline for the hard-won details.

Indexed by `(edition, book_no)` and `(edition, book_no, page_no)`.

### 4.2 `footnotes` — apparatus criticus (28,644 rows)

Variant manuscript readings for pages that have them (not every page does).

| Column | Type | Notes |
|--------|------|-------|
| `edition` | TEXT | `'mula'` / `'atthakatha'` |
| `book_no`, `page_no` | INTEGER | Match the `pages` row |
| `book_key`, `page_key` | TEXT | Legacy offset keys |
| `nline` | INTEGER | Number of apparatus lines |
| `beginline` | INTEGER | Starting line offset on the page |
| `unitext` | TEXT | **Apparatus text** — plain UTF-8, e.g. `1 So Pj. Bai; Ckb yo ve [Dhp. 222].` |

Join to `pages` on `(edition, book_no, page_no)`. Footnote reference numbers embedded in
`pages.unitext` (digits glued to words, e.g. `vantaṃ1`) point into this apparatus.

---

## 5. Structure & navigation

### 5.1 `books` — volume directory (111 rows = 53 mula + 58 atthakatha)

| Column | Type | Notes |
|--------|------|-------|
| `edition` | TEXT | |
| `book_no` | INTEGER | Unique within edition |
| `book_name` | TEXT | ⚠️ Garbled Thai — do not display (§3) |
| `s_name` | TEXT | PTS abbreviation, e.g. `MN I`, `Sn` (populated for `mula`; `NULL` for `atthakatha`) |
| `beg_page`, `end_page` | INTEGER | PTS page range |

### 5.2 `toc` — table of contents (3,763 rows)

Decoded section headings per book, with page ranges. Names are real Unicode now.

| Column | Notes |
|--------|-------|
| `edition`, `book_no` | |
| `name` | Section title, e.g. `I. URAGAVAGGA` |
| `beg_page`, `end_page` | `end_page` is often `0` (= unknown/open) |

### 5.3 `contents` — per-sutta contents (2,068 rows, 15 books)

Finer-grained than `toc`: one row per sutta/section, populated for the sutta nikāyas.

| Column | Notes |
|--------|-------|
| `book_no`, `seq` | Book and 0-based sequence within it |
| `page_no` | Starting page |
| `section` | Vagga/section name, e.g. `Sīlakkhandhavagga` |
| `title` | Sutta title, e.g. `Brahmajālasutta` |

> Note: `contents` has **no `edition` column** — its rows are `mula` canon.

### 5.4 `chapter_marks` — unit-start markers (9,322 rows)

Marks where discrete textual units (suttas, sections) begin in the page stream.

| Column | Notes |
|--------|-------|
| `edition`, `book_no`, `page_no` | Location |
| `wordmark` | Romanised Pāli first word(s) of the unit, e.g. `atthāya kulaputtā` (plain UTF-8) |

### 5.5 `nav_tree` — hierarchical navigation (3,878 rows)

The browsable tree used by the GUI (Piṭaka → Nikāya → book → …).

| Column | Notes |
|--------|-------|
| `key` | Node id, e.g. `11_` |
| `parent` | Parent node id (root is `0_`) |
| `text` | Display label, e.g. `Vinayapiṭaka` |
| `book_no`, `page_no` | Target location (nullable for interior nodes) |

---

## 6. Supplementary & external references

### 6.1 `pts_prefaces` (519 rows)

Front matter per volume. `edition, book_no, page_no, text` — `text` is plain UTF-8 (line breaks
`\r`).

### 6.2 `pts_appendices` (1,097 rows)

Appendix material (chiefly the PTS "Various Readings" tables).

| Column | Notes |
|--------|-------|
| `edition`, `book_no`, `page_no` | Source location of the appendix page |
| `target_book`, `target_page` | The canonical PTS book/page the appendix refers to |
| `text` | Plain UTF-8 |

### 6.3 `pts_xref` — cross-edition references (3,054 rows)

Maps PTS `(book_no, page_no)` to the corresponding **VRI** (CST) and **Thai** edition
references — useful for citation conversion.

| Column | Notes |
|--------|-------|
| `book_no`, `page_no` | PTS (mula) location |
| `vri` | VRI/CST reference string, e.g. `1.1–2` |
| `thai` | Thai edition reference, e.g. `9.1` |

### 6.4 `translation_en` (1,085 rows) & `translation_sujato` (5,161 rows)

Aligned English translations keyed to PTS `(book_no, page_no)`.

- `translation_en`: `author, text` — multiple translators (Bhikkhu Bodhi, I.B. Horner,
  Thanissaro Bhikkhu, Rhys Davids, etc.).
- `translation_sujato`: `text` — Bhikkhu Sujato's translation (single source, no `author`).

---

## 7. Word-concordance tables

These preserve the original FoxPro **offset encoding** (each key char = byte value + `0x24`).
They power an exact word concordance but are awkward to use directly; for ordinary search prefer
`pali_fts` (§9) or a `LIKE`/substring scan of decoded `pages.unitext`.

Decoder for the numeric keys:

```python
def decode_key(s: str) -> int:
    r = 0
    for ch in s:
        r = r * 256 + (ord(ch) - 0x24)
    return r
```

| Table | Rows | Purpose | Key columns |
|-------|-----:|---------|-------------|
| `word_list` | 569,425 | Unique word forms per edition | `skid` (word id), `str1` (form, may contain PUA), `nfound`/`nfootfound` (offset-encoded counts), `type` |
| `word_occurrences` | 5,509,915 | Every occurrence → location | `word_key`→`word_list.skid`, `book_key`/`page_key`→`pages`, `line` |
| `word_counts` | 1,354,730 | Per-book frequency | `word_key`, `book_key`, `total` |

All carry an `edition` column. Join `word_occurrences.(book_key, page_key)` back to
`pages.(book_key, page_key)` to resolve the running text.

---

## 8. Dictionary tables

### 8.1 `dict_pts` — PTS Pāli–English Dictionary (16,232 rows)

Rhys Davids & Stede, digitised. **Plain UTF-8 and directly usable.**

| Column | Notes |
|--------|-------|
| `ttitle` | Headword with sub-entry notation, e.g. `a-^1`, `a-^2` (the `^` disambiguates homonyms) |
| `tdetail` | Entry body, e.g. `the prep. … shortened before double consonant …` |
| `page_no`, `word_no` | Position in the printed dictionary |

### 8.2 `dict_pali_english` — bilingual dictionary (16,262 rows)

| Column | Notes |
|--------|-------|
| `ttitle` | Thai/legacy headword — ⚠️ partly garbled |
| `etitle` | English headword, e.g. `A-1` (reliable) |
| `tdetail` / `edetail` | Thai / English detail (`edetail` reliable) |
| `key` | Numeric primary key |
| `number` | Entry number string |

The GUI also ships external StarDict dictionaries (`dictionaries/cpd.*`, `PTSPED-2021.*`) and
`critical.db`; those are separate from this SQLite file.

---

## 9. Full-text search (`pali_fts`)

An **FTS5** virtual table over the text corpus — the easiest way to search.

Columns: `unitext`, `head`, `edition`, `kind`, `book_no`, `page_no`.
`kind` ∈ {`page` (32,163), `appendix` (1,097), `preface` (519)}.

```python
cur.execute("""
    SELECT book_no, page_no, edition, kind
    FROM pali_fts
    WHERE pali_fts MATCH ?          -- e.g. 'mettā', 'sammā NEAR diṭṭhi'
      AND edition='mula' AND kind='page'
    LIMIT 20
""", ("mettā",))
```

The `pali_fts_config/content/data/docsize/idx` tables are FTS5 internals — never query or edit
them directly.

---

## 10. Relationships and joins

```
editions (id) ── edition column on every text/structure table
books (edition, book_no)
   ├── pages (edition, book_no, page_no) ── footnotes (edition, book_no, page_no)
   ├── toc / contents / chapter_marks / nav_tree      (by book_no [+ edition])
   ├── pts_prefaces / pts_appendices                  (edition, book_no, page_no)
   ├── pts_xref / translation_en / translation_sujato (book_no, page_no; mula)
   └── pali_fts                                       (edition, book_no, page_no, kind)

word_list (edition, skid)
   ├── word_occurrences (word_key → skid; book_key/page_key → pages)
   └── word_counts      (word_key → skid)
```

| Goal | Join |
|------|------|
| Page text + apparatus | `pages p LEFT JOIN footnotes f USING (edition, book_no, page_no)` |
| Page + English translation | `pages p LEFT JOIN translation_en t ON t.book_no=p.book_no AND t.page_no=p.page_no` (mula) |
| PTS page → VRI/Thai ref | `pages p LEFT JOIN pts_xref x ON x.book_no=p.book_no AND x.page_no=p.page_no` |
| Book metadata | `pages p JOIN books b USING (edition, book_no)` |
| Sutta boundaries | `contents WHERE book_no=? ORDER BY seq` |

---

## 11. Inline markup in text

After reading `pages.unitext` (already plain UTF-8), expect this typesetting markup:

- **Footnote reference numbers** — digits glued to a word mark a variant reading keyed to
  `footnotes.unitext`, e.g. `taṃ2 nipako8 satimā`. Strip with:
  ```python
  import re
  clean = re.sub(r'(?<=\w)\d+', '', text)
  ```
- **Variant braces `{word}`** — a reading attested in at least one manuscript, e.g. `{sammā}diṭṭhi`.
- **Folio markers `[F.N]`** — palm-leaf folio boundaries in the source manuscripts.
- **`head`** — the printed running header (section title + page number), sometimes with a stray
  `^` or leftover font artifacts; treat as a hint, not authority (§4.1).

---

## 12. Complete book / volume listing

`mula` edition, from the `books` table (`book_no`, `s_name`, PTS page range):

| # | s_name | Pages | Collection |
|---|--------|-------|------------|
| 1 | Vin I | 1–360 | Vinaya — Mahāvagga |
| 2 | Vin II | 1–308 | Vinaya — Cullavagga |
| 3 | Vin III | 1–266 | Vinaya — Suttavibhaṅga I |
| 4 | Vin IV | 1–351 | Vinaya — Suttavibhaṅga II |
| 5 | Vin V | 1–226 | Vinaya — Parivāra |
| 6 | DN I | 1–253 | Dīgha Nikāya I |
| 7 | DN I ¹ | 1–358 | Dīgha Nikāya II |
| 8 | DN III | 1–293 | Dīgha Nikāya III |
| 9 | MN I | 1–524 | Majjhima Nikāya I |
| 10 | MN II | 1–266 | Majjhima Nikāya II |
| 11 | MN III | 1–302 | Majjhima Nikāya III |
| 12 | SN I | 1–240 | Saṃyutta Nikāya I |
| 13 | SN II | 1–286 | Saṃyutta Nikāya II |
| 14 | SN III | 1–279 | Saṃyutta Nikāya III |
| 15 | SN IV | 1–403 | Saṃyutta Nikāya IV |
| 16 | SN V | 1–478 | Saṃyutta Nikāya V |
| 17 | AN I | 1–304 | Aṅguttara Nikāya I |
| 18 | AN II | 1–257 | Aṅguttara Nikāya II |
| 19 | AN III | 1–452 | Aṅguttara Nikāya III |
| 20 | AN IV | 1–466 | Aṅguttara Nikāya IV |
| 21 | AN V | 1–361 | Aṅguttara Nikāya V |
| 22 | Khp | 1–9 | Khuddakapāṭha |
| 23 | Dhp | 1–120 | Dhammapada |
| 24 | Ud | 1–94 | Udāna |
| 25 | It | 1–124 | Itivuttaka |
| 26 | Sn | 1–223 | Suttanipāta |
| 27 | Vv | 1–135 | Vimānavatthu |
| 28 | Pv | 1–95 | Petavatthu |
| 29 | Th & Th | 1–174 | Theragāthā & Therīgāthā |
| 30 | Th & Th | 1–511 | Jātaka I (with Nidānakathā) |
| 31 | Ja II | 1–451 | Jātaka II |
| 32 | Ja III | 1–543 | Jātaka III |
| 33 | Ja IV | 1–499 | Jātaka IV |
| 34 | Ja V | 1–511 | Jātaka V |
| 35 | Ja VI | 1–596 | Jātaka VI |
| 36 | Nidd I | 1–510 | Mahāniddesa |
| 37 | Nidd II | 1–73 | Cūḷaniddesa |
| 38 | Patis I | 1–196 | Paṭisambhidāmagga I |
| 39 | Patis II | 1–246 | Paṭisambhidāmagga II |
| 40 | Ap | 1–615 | Apadāna |
| 41 | Bv | 1–102 | Buddhavaṃsa |
| 42 | Cp | 1–37 | Cariyāpiṭaka |
| 43 | Dhs | 1–264 | Dhammasaṅgaṇī |
| 44 | Vibh | 1–436 | Vibhaṅga |
| 45 | Dhātuk ² | 1–113 | Dhātukathā |
| 46 | Pp | 1–74 | Puggalapaññatti |
| 47 | Kv | 1–628 | Kathāvatthu |
| 48 | Yam I | 1–378 | Yamaka I |
| 49 | Yam II | 1–215 | Yamaka II |
| 50 | Dukap | 1–353 | Duka-Paṭṭhāna |
| 51 | Tikap I | 1–7 | Tika-Paṭṭhāna I |
| 52 | Tikap II | 69–229 | Tika-Paṭṭhāna II |
| 53 | Tikap III | 317–344 | Tika-Paṭṭhāna III |

¹ Book 7's `s_name` is `DN I` in the data but it is actually **DN vol. II** — a source data-entry
error. Look it up by `book_no=7` and label it manually.
² Book 45's `s_name` contains a stray glyph (`Dhātuk` with a `¤`-like artifact); the volume is
Dhātukathā.

The `atthakatha` edition has 58 books (`book_no` 1–58) with `s_name = NULL`; for their titles,
sigla, and the mūla text each commentary covers, see `book_meta.py` / `../../README-COMMY.md`.

---

## 13. Query recipes

All examples assume `edition='mula'` unless noted. No `decode()` and no `_deleted` filter are
needed anymore.

### 13.1 Fetch a page + apparatus by PTS reference

```python
import sqlite3
con = sqlite3.connect("src/data/tipitaka.sqlite")
cur = con.cursor()

def get_page(book_no, page_no, edition="mula"):
    cur.execute("""
        SELECT p.head, p.unitext, p.footnline, f.unitext
        FROM pages p
        LEFT JOIN footnotes f USING (edition, book_no, page_no)
        WHERE p.edition=? AND p.book_no=? AND p.page_no=?
    """, (edition, book_no, page_no))
    row = cur.fetchone()
    if not row:
        return {}
    return {"head": row[0], "text": row[1],
            "footnlines": row[2], "apparatus": row[3] or ""}

print(get_page(26, 25)["text"])   # Suttanipāta p.25
```

### 13.2 Resolve a PTS abbreviation to book_no

```python
def book_no_from_abbr(abbr, edition="mula"):
    cur.execute("SELECT book_no, s_name FROM books WHERE edition=?", (edition,))
    for bn, sn in cur.fetchall():
        if sn and sn.strip().lower() == abbr.strip().lower():
            return bn
    return None
```

### 13.3 Full-text search

```python
cur.execute("""
    SELECT book_no, page_no FROM pali_fts
    WHERE pali_fts MATCH ? AND edition='mula' AND kind='page'
""", ("mettā",))
```

### 13.4 Iterate all pages of a book (clean text)

```python
import re
cur.execute("SELECT page_no, unitext FROM pages WHERE edition='mula' AND book_no=26 ORDER BY page_no")
for page_no, unitext in cur.fetchall():
    clean = re.sub(r'(?<=\w)\d+', '', unitext)   # drop footnote ref numbers
    print(f"── p.{page_no} ──\n{clean}")
```

### 13.5 Page with its English translation and VRI/Thai reference

```python
cur.execute("""
    SELECT p.unitext, t.author, t.text, x.vri, x.thai
    FROM pages p
    LEFT JOIN translation_en t ON t.book_no=p.book_no AND t.page_no=p.page_no
    LEFT JOIN pts_xref       x ON x.book_no=p.book_no AND x.page_no=p.page_no
    WHERE p.edition='mula' AND p.book_no=6 AND p.page_no=1
""")
```

### 13.6 Sutta contents of a book

```python
cur.execute("SELECT seq, page_no, section, title FROM contents WHERE book_no=6 ORDER BY seq")
for seq, page_no, section, title in cur.fetchall():
    print(f"  {title:<24} ({section}) — p.{page_no}")
```

---

## 14. Known data quirks

| Quirk | Details |
|-------|---------|
| **`book_no` not globally unique** | It repeats across `mula` and `atthakatha`. Always constrain `edition`. |
| **Book 7 mislabelled** | `s_name='DN I'` but it is DN vol. II. Label manually. |
| **Book 45 s_name glyph** | Contains a stray artifact (`Dhātuk`+`¤`); it is Dhātukathā. |
| **Tikap page numbering** | Books 51–53 continue a shared sequence (start at 1, 69, 317), so `page_no` for 52–53 does not begin at 1. |
| **`head` unreliable** | Printed running header; may be empty, carry a stray `^`, or name the wrong sutta. Validate against `unitext`. |
| **`encpali` legacy** | Base64→PUA (Thai font). Ignore; use `unitext`. |
| **`books.book_name` garbled** | cp850/cp874 Thai bytes, unrecoverable. Use `s_name`. |
| **`dict_pali_english` Thai side garbled** | Use `etitle`/`edetail` for reliable text. |
| **Word-key tables offset-encoded** | `word_list`/`word_occurrences`/`word_counts` keys aren't plain strings/ints (§7); prefer `pali_fts` for search. |
| **`contents` has no `edition`** | Its rows are `mula` canon only. |

---

## 15. Table summary

| Table | Rows | Purpose |
|-------|-----:|---------|
| `pages` | 32,188 | Main Pāli text (both editions) |
| `footnotes` | 28,644 | Apparatus criticus |
| `books` | 111 | Volume directory (53 mula + 58 aṭṭhakathā) |
| `editions` | 2 | Edition registry |
| `toc` | 3,763 | Section table of contents |
| `contents` | 2,068 | Per-sutta contents (15 mula books) |
| `chapter_marks` | 9,322 | Unit-start markers |
| `nav_tree` | 3,878 | Navigation hierarchy |
| `pts_prefaces` | 519 | Volume front matter |
| `pts_appendices` | 1,097 | Appendix / Various Readings pages |
| `pts_xref` | 3,054 | PTS → VRI/Thai reference map |
| `translation_en` | 1,085 | English translations (multiple authors) |
| `translation_sujato` | 5,161 | Bhikkhu Sujato translation |
| `dict_pts` | 16,232 | PTS Pāli–English Dictionary |
| `dict_pali_english` | 16,262 | Bilingual dictionary |
| `word_list` | 569,425 | Lexicon (offset-encoded) |
| `word_occurrences` | 5,509,915 | Concordance (offset-encoded) |
| `word_counts` | 1,354,730 | Per-book word frequency (offset-encoded) |
| `pali_fts` (+ 5 shadow tables) | 33,779 | FTS5 full-text index |

---

*Rebuilt from the Dhammakaya Foundation PaliText V2.5 source into this application schema.
For the concordance/validation pipeline that consumes this DB, see `../../README.md`,
`../../STATUS.md`, and `../../CLAUDE.md`.*
