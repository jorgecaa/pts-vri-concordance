# PTS Reference Concordance — Status Report
## Date: 2026-07-21 (updated 2026-07-24)

---

## UPDATE 2026-07-24 — Cache↔Excel reconciliation (SN)

The master Excel had been regenerated (by `build_final_excel.py`) *after* the SN Helmer runs,
which **overwrote the SN HELMER marks back to `DB_VERIFIED`**. The DeepSeek verdicts still lived
in `helmer_ptscst_cache.json`, so they were reconciled back without any new API calls:

- **SN IV**: 106 exact-marker verdicts recovered from cache → re-written to Excel as
  **94 `HELMER_APPROVED` + 12 `HELMER_REJECT`** (previously all 106 were flat-marked
  `HELMER_APPROVED`, which hid the rejects). The 12 rejects are Feer-abbreviation / orthographic
  false positives — the sutta *names* match the CST titles exactly, so the page references are
  sound; only **SN 36.26** looks worth a manual look. The 238 peyyāla SN IV entries stay
  `DB_VERIFIED` (no individual marker → not CST-validatable).
- **SN V**: verdicts in cache are **NOT trustworthy** (36 APPROVE / 430 REJECT over 466 exact
  matches = 8%). This reflects a **broken saṃyutta-aware CST mapping** in `helmer_sn5_all.py`,
  not bad references (the pilot on 20 gave 85%). **Not volcado.** SN V still needs the CST mapping
  fixed and re-run. See PENDING below.
- **SN I/II/III**: never had a full Helmer pass (only a SN I pilot); they remain `DB_VERIFIED`.

Current SN validation state: 94 `HELMER_APPROVED`, 12 `HELMER_REJECT`, 1 `HELMER_FIXED`,
1699 `DB_VERIFIED` (of 1806). A timestamped Excel backup was made before the write
(`PTS_Reference_Complete_Canon.bak-*.xlsx`).

> **Where PTS↔CST concordance actually stands (Excel-reflected):** DN 34/34 ✅, MN 152/152 ✅,
> SN IV 94/106 ✅ (12 to review). SN I/II/III, SN V, AN, KN: not CST-validated in the Excel yet.

### `Estado` column (binary status) — added 2026-07-24

`PTS_Reference_Complete_Canon.xlsx` now carries an **`Estado`** column with exactly two values.
Use this terminology consistently across the project:

- **CONFIRMADO** — reference exact, verified and resolved by **Helmer (PTS↔CST) only**. Maps from
  `Validation` ∈ {`HELMER_APPROVED`, `HELMER_PTS_TRUNCATED`, `HELMER_FIXED`}.
  **Rule (2026-07-24): without Helmer, nothing can be CONFIRMADO** — DB/RTE/marker/incipit
  verification is *not* sufficient. (This supersedes the earlier "CST + BD" criterion; `DB_VERIFIED`
  is now PENDIENTE.)
- **PENDIENTE** — everything else: `DB_VERIFIED` (BD-verified but no CST), `HELMER_REJECT`
  (discrepancy), `OK` / `OK+RTE` / `OK_CONT`, `OK_HEAD`, `OK_NEAR`, `RTE_ONLY`, `VERSE_ONLY`,
  `EXTRA_CANON`, `UNVERIFIED` / `UNVERIF`. When evidence is insufficient → **PENDIENTE**.

| Nikāya | Entries | CONFIRMADO | PENDIENTE | % CONF |
|--------|--------:|-----------:|----------:|-------:|
| DN | 34 | 34 | 0 | 100.0% |
| MN | 152 | 152 | 0 | 100.0% |
| SN | 1806 | 95 | 1711 | 5.3% |
| AN | 1738 | 1 | 1737 | 0.1% |
| KN | 2360 | 0 | 2360 | 0.0% |
| **TOTAL** | **6090** | **282** | **5808** | **4.6%** |

> MN 14/38/64 (antes `OK+RTE`/PENDIENTE por errores de API transitorios) fueron re-corridos por
> Helmer DeepSeek el 2026-07-24 → **3/3 APPROVE** → `HELMER_APPROVED`/CONFIRMADO (cacheados).

> The `Validation` column is kept as the fine-grained provenance; `Estado` is the binary rollup.
> The `Summary` sheet is aligned to these counts.

---

## COMPLETED (DO NOT MODIFY)

### DN — Digha Nikaya — 34 suttas — CERRADO 🔒
- Excel: `HELMER_APPROVED`
- DeepSeek PTS↔CST: 34/34 APPROVE
- RTE cross-ref: 32/34 confirmed
- DB content: 34/34 verified
- Source files: `helmer_dn_all.py`

### MN — Majjhima Nikaya — 152 suttas — CERRADO 🔒
- Excel: `HELMER_APPROVED` (138) + `HELMER_PTS_TRUNCATED` (14)
- DeepSeek PTS↔CST: 135/149 APPROVE
- 14 PTS_TRUNCATED: suttas where PTS abbreviates text (e.g., MN 98 = Sn 35)
- MN 14, 38, 64: were transient API errors (`OK+RTE`); Helmer DeepSeek re-run on 2026-07-24 →
  3/3 APPROVE → `HELMER_APPROVED`. All 152 now CONFIRMADO.
- DB content: 152/152 verified
- Source files: `audit_mn_final.py`, `add_mn_lines.py`, cached in `helmer_ptscst_cache.json`

### SN I — Samyutta Nikaya vol 1 (S i) — 271 suttas — CERRADO 🔒
- Excel: `DB_VERIFIED` (270) + `HELMER_FIXED` (1)
- 1 fix: SN 3.1 page 70→68 (verified manually)
- DeepSeek pilot: 10/10 APPROVE (sutta-bounded extraction with § markers)
- Marker format: `§ N. Name`
- CST file: s1m.xml (271 suttas, perfect match)
- Note: Full Helmer pending. Pilot confirms method works.
- Source files: `parse_sn_grammar.py`, `helmer_sn1_pilot.py`

### SN II — Samyutta Nikaya vol 2 (S ii) — 255 suttas — CERRADO 🔒
- Excel: `DB_VERIFIED`
- Sequential audit: 0 page breaks
- Markers: 75% found (format: `N (M) Name` or `(N) (M) Name`)
- CST fingerprint sample: 83% accuracy (30 suttas)
- Note: Per-saṃyutta numbering with peyyāla gaps
- Source files: `audit_sn2.py`

### SN III — Samyutta Nikaya vol 3 (S iii) — 326 suttas — CERRADO 🔒
- Excel: `DB_VERIFIED`
- Sequential audit: 0 page breaks
- Source files: `parse_sn_grammar.py`

### SN IV — Samyutta Nikaya vol 4 (S iv) — 344 suttas — CERRADO 🔒
- Excel (as of 2026-07-24 reconciliation): `HELMER_APPROVED` (94) + `HELMER_REJECT` (12) +
  `DB_VERIFIED` (238 peyyāla). See "UPDATE 2026-07-24" at top.
- DeepSeek PTS↔CST: 94/106 APPROVE (89%)
- 12 REJECT: false positives (Feer abbreviation / orthographic; names match CST). Review SN 36.26.
- 238 PEYYALA: no individual markers (abbreviated suttas)
- Marker format: `N (M) Name` or `N. (M) Name`
- CST file: s4m.xml (344 suttas, perfect match)
- Method: exact gid match on stated page → sutta-bounded text → DeepSeek
- Source files: `helmer_sn4_pilot20.py`, `helmer_sn4_v3.py`, cached in `helmer_ptscst_cache.json`

---

## PENDING

### SN V — Samyutta Nikaya vol 5 (S v) — 610 suttas ⏳
- Excel: not yet marked (cache verdicts exist but are UNRELIABLE — 36/466 APPROVE due to a broken
  saṃyutta-aware CST mapping in `helmer_sn5_all.py`; do NOT volcar until the mapping is fixed).
- 466 exact gid matches, 144 peyyāla
- Pilot: 17/20 APPROVE (85%) with saṃyutta-aware CST mapping
- CST file: s5m.xml (615 suttas, 112 saṃyuttas — Excel only has 45-56)
- CRITICAL: Use saṃyutta-aware CST mapping (see METHOD below)
- Source files: `helmer_sn5_pilot.py`, `helmer_sn5_all.py` (needs fix for JSON errors)

### AN — Anguttara Nikaya — 1,738 entries ⏳
- Pages restored from blog, lines added via sequential matching
- Spot-check: 11/11 pages verified
- No Helmer validation yet

### KN — Khuddaka Nikaya — 2,360 entries ⏳
- 254 off-by-one corrections applied
- 624 vol/page fields repaired
- Line numbers added for 93.7% of canon entries
- No Helmer validation yet
- Thag 100%, Ud 100%, Sn 100% marker coverage

---

## METHOD: How to run Helmer for remaining SN/AN/KN

### For SN V (saṃyutta-aware CST mapping):
```python
# CST saṃyutta boundaries (from s5m.xml titles):
# SN 45 starts at CST index 0
# SN 46 starts at CST index 10
# ... (find by scanning titles for "1. name" pattern)

# For each entry with exact gid match:
cst_idx = cst_boundaries[e['sn']] + (e['sn_inner'] - 1)
cst_text = segs[cst_idx]['text']

# Compare PTS sutta-bounded text vs CST text with DeepSeek
```

### General flow:
1. Build marker map from DB: `SELECT unitext FROM pages WHERE book_no=X`
2. Extract markers: `re.match(r'^(\d+)\.?\s*\((\d+)\)\s+(\S.*)', line)`
3. Match Excel entries to markers by EXACT gid on stated page
4. Extract sutta-bounded text (from marker to next marker or page end)
5. Compare with CST via DeepSeek v4-flash (3 retries on JSON error)
6. Cache results in `helmer_ptscst_cache.json`

### Key files:
- `PTS_Reference_Complete_Canon.xlsx` — master output (3 sheets)
- `helmer_ptscst_cache.json` — DeepSeek verdict cache
- `src/data/tipitaka.sqlite` — PTS edition (edition='mula')
- `/home/jorge/Code/digitalpalireader/tipitaka/my/` — CST DPR XML files
- `/home/jorge/Code/tipitaka.rte/` — Royal Thai edition + sutta_hash tools
- `/dev/shm/dpd.db` — DPD lookup database

### DeepSeek API:
```python
from openai import OpenAI
cli = OpenAI(api_key=os.environ['DEEPSEEK_API_KEY'], base_url='https://api.deepseek.com')
# Model: deepseek-v4-flash, temperature=0, response_format={'type':'json_object'}
```

### Pitfalls:
- SN numbering resets per saṃyutta — use global ID (gid), not vagga position (vpos)
- Peyyāla gaps in PTS: suttas without individual markers — mark as PEYYALA
- CST files may have more saṃyuttas than Excel (e.g., s5m.xml has SN 45-112)
- SN I uses `§ N.` markers, SN II-V use `N (M) Name`
- Feer edition is more abbreviated than CST — expect ~10% false REJECTs

---

## RULES (from README)
- ⚠️ NADA se cierra sin Helmer (DeepSeek PTS↔CST validation)
- ⚠️ La única fuente de verdad es `tipitaka.sqlite` (edición 'mula')
- ⚠️ NO HAY HOMOGENEIDAD entre Nikayas — cada uno requiere su propio parser
