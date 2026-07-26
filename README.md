# A Concordance of the Pāli Canon: Pali Text Society ↔ Chaṭṭha Saṅgāyana

**Jorge Contreras** · released under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) (public domain dedication)

A row-by-row concordance between two editions of the Pāli Canon. Each entry names one textual unit
and gives its locus in both witnesses: the roman-script edition of the **Pali Text Society** (`Ee`)
and the **Chaṭṭha Saṅgāyana** edition published by the Vipassana Research Institute (`Be`, commonly
"CST").

**6,098 entries. 5,232 of them are collatable, and every one has been collated.** The remaining 866
are accounted for individually rather than left blank — see [Scope](#scope-and-what-is-not-here).

| Nikāya | Entries | Confirmed | Other |
|---|--:|--:|--:|
| Dīgha | 34 | 34 | — |
| Majjhima | 152 | 152 | — |
| Saṃyutta | 1,814 | 1,814 | — |
| Aṅguttara | 1,737 | 1,737 | — |
| Khuddaka | 2,361 | 1,495 | 866 |
| **Total** | **6,098** | **5,232** | **866** |

## The file

`PTS-CST_Concordance_of_the_Pali_Canon.xlsx` — three sheets:

- **About** — authorship, licence, sources, method, conventions and caveats, so the file can be read
  without this document.
- **Concordance** — the 6,098 entries.
- **Summary** — counts by Nikāya.

### Columns

| Column | Meaning |
|---|---|
| `Nikāya` | DN, MN, SN, AN, KN |
| `Work` | siglum of the work, following the *Critical Pāli Dictionary* |
| `Section` | the work spelled out, where one siglum covers more than one |
| `Number` | traditional numbering of the entry |
| `Title` | name of the unit as the source table gives it |
| `Ee volume`, `Ee page` | PTS volume (roman) and page |
| `PTS reference` | the citation proper |
| `CST reference` | the locus in the VRI XML |
| `Verses` | strophe range, for works in verse |
| `Type` | `Sutta`, or `Section Header` for a rubric of the printed edition |
| `Status` | `Confirmed` or `Pending` |
| `Evidence` | how the entry was established |
| `Notes` | an editorial fact, where there is one |

### `Evidence` values

| Value | Entries | Meaning |
|---|--:|---|
| `Collated (automatic agreement)` | 3,168 | both sides of the pair agreed under the collation gate |
| `Collated (printed markers)` | 2,062 | established from the markers the printed edition itself supplies — colophons, chapter headings, running numbers, uddānas — with structural cross-checks, rather than through the collation gate. A small minority of these (ten entries in DN and MN) were disagreements arbitrated by hand against the printed edition |
| `Out of scope` | 548 | the Jātaka — see below |
| `No Ee text available` | 294 | no PTS text for that work in the source used |
| `Deest in Ee` | 14 | the PTS edition does not print the passage |
| `Section rubric` | 10 | not a citable unit |
| `Cross-reference in Ee` | 2 | PTS refers the reader elsewhere instead of reprinting |

## Sources

- **Ee** — the PTS roman-script edition, from a digitised text whose pagination follows the printed
  volumes.
- **Be** — the Chaṭṭha Saṅgāyana Tipiṭaka in the VRI XML files (`romn/*.mul.xml`), canonical text
  only.

No other edition was used. In particular this concordance does not draw on the Mahāsaṅgīti, Thai
(BUDSIR) or Sinhalese editions, and does not use the commentaries.

## Citation conventions

Sigla follow the ***Critical Pāli Dictionary*** and its *Epilegomena* (Copenhagen, 1948), continued
by Cone's *Dictionary of Pāli*. Three consequences:

1. **Edition sigla**: `Ee` (*editio Europaea*, PTS), `Be` (Burmese, the CST), `Ce` (Sinhalese),
   `Se` (Siamese). This is the vocabulary in which one writes `deest in Ee`.
2. **The unit of citation follows the genre of the text.** Prose is cited by volume, page and line
   — `M I 1,5`. Verse works are cited by **strophe or section** — `Dhp 21-32`, `Vv 12`, `Cp 3.15` —
   because the strophe is stable across editions and the page is not.
3. **One siglum per work**, with the volume inside the reference rather than in the siglum. This is
   not cosmetic: a single label covering two works makes any count of that label meaningless.

### The CST reference

The `CST reference` is the paragraph number of the VRI XML, in one of five forms:

| Form | Example | When |
|---|---|---|
| `file:n` | `s0301m:21` | one paragraph |
| `file:a-b` | `s0101m:1-149` | a run of paragraphs |
| `file:n.item` | `s0302m:73.4` | a numbered item **inside** one paragraph |
| `file:cN` | `s0501m:c5` | a chapter, where the numbering restarts inside it |
| `file:cN.item` | `s0512m:c3.15` | an item within such a chapter |

The last three exist because **the numbered unit is not always the paragraph**. In the Khuddaka the
paragraph numbering restarts inside each chapter; and some paragraphs contain several numbered units
— the peyyāla of `s0302m:73` numbers its members `(2)`…`(12)` in its own text, and its uddāna counts
twelve.

## Method

**There is no universal parser, and none was attempted.** Each Nikāya — often each volume — has its
own marker conventions, and a rule fitted to the majority fails silently on the minority. Alignment
rests on the markers the printed edition itself supplies: running numbers, colophons, chapter
headings, uddānas.

The two `Collated` values in the `Evidence` column name two different routes, and the difference is
worth stating plainly. `automatic agreement` means the pair passed a collation gate. `printed
markers` means the entry rests on what the printed edition itself supplies — a colophon naming the
unit and its ordinal, a chapter heading, a running number, an uddāna that counts the members of a
group — checked against the CST structure. The second route carries most of the Khuddaka and of the
Aṅguttara, and it is not a weaker one: in works where content cannot discriminate, the printed
marker is the *only* evidence that can.

Two independent checks were required before an entry was accepted:

- **identity** — the name or printed marker of the unit against the CST title;
- **location** — the page, or the page and line.

**Content similarity was used as corroboration, never as the sole criterion.** This is the central
methodological point. In several works an adjacent unit scores as high as the correct one:

- in the **Udāna** almost every sutta opens with the same formula;
- in the **Vimānavatthu** the units come in deliberately repeated pairs, and a neighbour scores
  0.97 against 0.95 for the correct unit;
- in the **Niddesa**, exegetical prose that repeats itself, an unrelated chapter reaches 0.85.

A similarity threshold in those works would confirm the wrong pair with high confidence. What
decides there is the printed marker, or the name — the only signal that sees the `Paṭhama-`/`Dutiya-`
ordinal distinguishing two textually identical poems.

## Verification

Two automated batteries cover the whole table. Neither reports a contradiction.

| Battery | Entries | Passed | Contradictions | Undecided |
|---|--:|--:|--:|--:|
| DN / MN / SN / AN | 3,737 | 3,151 | **0** | 586 |
| KN | 1,495 | 1,495 | **0** | 0 |

**DN/MN/SN/AN** — the PTS reference carries page *and line*, so the battery verifies that the CST
text begins where the entry says. Measured, at the declared line against other lines of the same
page: median 0.90–1.00 versus 0.12–0.19. It **verifies rather than searches**: searching the page
finds the formula somewhere else, because in the Aṅguttara the openings repeat.

**KN** — that reference does not exist here, and content is where it discriminates least. So the
battery asks a different question: *when you cannot verify the point, verify the order and the
measure.* Two independent orderings — how PTS prints and how the CST numbers — must agree, and the
two texts must advance together. A misassigned entry breaks one of them even when its text resembles
its neighbour's, and both checks are blind to how the alignment was made.

### The batteries were themselves tested

A battery that approves everything may be a battery that detects nothing. Each was given **ten
deliberate defects** — swapped neighbours, one-place shifts, seven-place shifts, duplicated
references, broken references — and **each detected ten of ten**.

That test changed the batteries twice. Both had been treating a shared reference as legitimate
merely because it was a range; since in DN and MN *every* reference is a range, no duplication was
being detected there at all. The rule that replaced it is the one this project uses throughout:
**an exception is declared, not inferred.**

### Entries the tests could not decide

The 586 undecided entries are **not counted as confirmed**. Most are passages that both editions
print in abbreviated form — the CST leaving `…pe…` where PTS leaves `║ pe ║` — so there is nothing
to collate. Those entries were established on structural evidence: an uddāna that counts the
members, the order of the series. A textual test can neither confirm nor deny that, and it says so
rather than reporting a pass.

## Scope, and what is not here

| | Entries | Why |
|---|--:|---|
| **Jātaka** | 548 | The PTS text available is Fausbøll's edition, which is *the Jātaka together with its commentary*; the canonical text is the verses alone. Collating it would mean working on commentary. The figure includes the work's own section rubric. |
| **Milindapañha** | 248 | No PTS text in the source used; the CST classes it outside the canon. |
| **Nettippakaraṇa** | 37 | No PTS text in the source used. |
| **Peṭakopadesa** | 9 | No PTS text in the source used; outside the canon. |
| **Not printed in Ee** | 14 | The Therāpadāna's 56th vagga (11) and three of its 34th. |
| **Section rubrics** | 10 | Rubrics of the printed edition, kept as attested structure but not entries. An eleventh belongs to the Jātaka and is counted in that row. |

Entries in the last two groups are *recorded*, not left blank. That an edition does not print a
passage is a fact about that witness, and the apparatus criticus has a word for it — `deest`. The
distinction matters: negative evidence is not the absence of evidence.

## Known limitations

**What was inspected is a digitised text, not the printed volume.** Where an entry says a passage is
not printed in a witness, the internal evidence is strong — a vagga uddāna announcing ten items where
the edition prints seven, a colophon closing the work — but the distinction between *deest in Ee*
and *absent from the copy used* is one this edition can state and not close.

**Two works are cited in a pagination that is not the one collated.** The Buddhavaṃsa and the
Cariyāpiṭaka are cited in the single volume in which PTS printed them together (Bv 1–68, Cp 73–101);
the copy used for collation is a different setting, and the two series diverge progressively. Their
page was therefore not verified, and this is stated on every one of those 64 entries.

**The Khuddaka is uneven by nature.** Its works were closed one at a time, each with its own régime;
where the evidence was weaker than elsewhere, the `Evidence` and `Notes` columns say so.

## How to cite

> Contreras, Jorge. *A Concordance of the Pāli Canon: Pali Text Society ↔ Chaṭṭha Saṅgāyana.* 2026.
> CC0 1.0 Universal.

## Licence

To the extent possible under law, Jorge Contreras has waived all copyright and related or
neighbouring rights to this work. See
[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

No warranty of any kind is given. The underlying texts are themselves in the public domain.
