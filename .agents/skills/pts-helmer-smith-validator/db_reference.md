# PTS Reference Validation — Database Quick Reference

## Connection

```python
import sqlite3
con = sqlite3.connect('src/data/tipitaka.sqlite')
```

## Text encoding

**No decoding needed.** In the current schema `pages.unitext`, `pages.head`, and
`footnotes.unitext` are **plain UTF-8** — read them directly. (The legacy BOM+Base64 decoder is
obsolete; do not wrap these fields in it. The only base64/PUA field left is `pages.encpali`,
which you should ignore — use `unitext`.) Full schema: `src/data/DATABASE.md`.

## Key Queries

### Page by book + page number
```sql
SELECT page_no, head, unitext 
FROM pages 
WHERE edition='mula' AND book_no=? AND page_no=?
```

### Page range for a book
```sql
SELECT MIN(page_no), MAX(page_no), COUNT(*) 
FROM pages 
WHERE edition='mula' AND book_no=?
```

### Search for text in heads
```sql
SELECT page_no, head 
FROM pages 
WHERE edition='mula' AND book_no=? AND lower(head) LIKE '%keyword%'
ORDER BY page_no
```

### Table of contents for a book
```sql
-- section headings with page ranges:
SELECT name, beg_page, end_page FROM toc WHERE edition='mula' AND book_no=? ORDER BY beg_page
-- per-sutta list (sutta nikāyas only):
SELECT seq, page_no, section, title FROM contents WHERE book_no=? ORDER BY seq
```

## PTS Volume → DB Book Mapping (Mula Edition, Khuddaka only)

| PTS Abbreviation | DB book_no | Page Range | Notes |
|-----------------|------------|------------|-------|
| Kh, Khp | 22 | 1–9 | |
| Dh, Dhp | 23 | 1–120 | |
| Ud | 24 | 1–94 | |
| It | 25 | 1–124 | |
| Sn, Snp | 26 | 1–223 | |
| Vv | 27 | 1–135 | |
| Pv | 28 | 1–95 | |
| Th, Thag | 29 | 1–122 | Shares vol. with Thī |
| Thī, Thig | 29 | 123–174 | Shares vol. with Thag |
| Ja i | 30 | 1–511 | Jātaka I (Nidānakathā + Ja 1–150) |
| Ja ii | 31 | 1–451 | Jātaka II (Ja 151–300) |
| Ja iii | 32 | 1–543 | Jātaka III (Ja 301–438) |
| Ja iv | 33 | 1–499 | Jātaka IV (Ja 439–510) |
| Ja v | 34 | 1–511 | Jātaka V (Ja 511–537) |
| Ja vi | 35 | 1–596 | Jātaka VI (Ja 538–547) |
| Nidd i | 36 | 1–510 | Mahāniddesa |
| Nidd ii | 37 | 1–73 | Cūḷaniddesa |
| Paṭis i | 38 | 1–196 | |
| Paṭis ii | 39 | 1–246 | |
| Ap i, Ap ii | 40 | 1–615 | Single volume in DB |
| Bv | 41 | 1–102 | Buddhavaṃsa |
| Bv & Cp | 41 | 73–101 | Cariyāpiṭaka bound with Bv |
| Cp | 42 | 1–37 | Separate Cp volume (alternative) |
| Nett | — | — | Extra-canonical: not in mula DB |
| Peṭ, Pet | — | — | Extra-canonical: not in mula DB |
| Mil | — | — | Extra-canonical: not in mula DB |

## Known Quirks

1. **Book 30 = Ja I + commentary pages**: The Nidānakathā and early Jātakas share book 30 with Udāna-aṭṭhakathā pages. Always filter `edition='mula'`.

2. **Book 41 = Bv + Cp + Niddesa commentary**: Contains Buddhavaṃsa (pp. 1–68), Cariyāpiṭaka (pp. 73–101), and Saddhammapajjotikā (Niddesa commentary) interleaved. Filter by edition AND check the head field.

3. **Corrupt heads**: Some `head` values contain garbled characters (legacy encoding corruption). The `unitext` is always reliable.

4. **Jātaka page 1**: Each Ja volume's page 1 contains the nipāta title ("II. DUKANIPĀTA"), not the first jātaka. The first jātaka of the volume usually starts at page 3.
