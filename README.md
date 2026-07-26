# A Concordance of the Pāli Canon: PTS ↔ Chaṭṭha Saṅgāyana

**Jorge Contreras** · [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/)

Each entry names one textual unit of the Pāli Canon and gives its locus in two editions: the
roman-script edition of the **Pali Text Society** (`Ee`) and the **Chaṭṭha Saṅgāyana** edition in
the VRI XML files (`Be`).

**6,098 entries · 5,232 collated · 866 not collated, each for a stated reason.**

| Nikāya | Entries | Collated |
|---|--:|--:|
| Dīgha | 34 | 34 |
| Majjhima | 152 | 152 |
| Saṃyutta | 1,814 | 1,814 |
| Aṅguttara | 1,737 | 1,737 |
| Khuddaka | 2,361 | 1,495 |

## Reading a row

`PTS-CST_Concordance_of_the_Pali_Canon.xlsx` — sheets **About**, **Concordance**, **Summary**.

`Work` uses the sigla of the *Critical Pāli Dictionary*: one siglum per work, the volume inside the
reference. `PTS reference` cites prose by volume, page and line (`M I 1,5`) and verse by strophe or
section (`Dhp 21-32`, `Cp 3.15`), because the strophe is stable across editions and the page is not.

`CST reference` is the paragraph of the VRI XML, in six forms — `file:n`, `file:a-b`, `file:n.item`,
`file:cN`, `file:cN.item`, `file:cN.a-b`. The forms with `c` and with `.item` exist because the
numbered unit is not always the paragraph: in the Khuddaka the numbering restarts inside each
chapter, and some paragraphs contain several numbered units.

## How entries were established

| `Evidence` | Entries | |
|---|--:|---|
| Collated (automatic agreement) | 3,168 | two judges agreed: a local gate (title stem, Jaccard of the incipit, CollateX divergences) and a language model (`gemini-flash-lite-latest`, temperature 0) shown both texts. Neither could confirm alone; a disagreement went to human arbitration |
| Collated (printed markers) | 2,062 | the markers the printed edition supplies — colophons, chapter headings, running numbers, uddānas — checked against the CST structure. The label also covers the disagreements that were arbitrated by hand; the data does not record which entries those were |
| Out of scope | 548 | the Jātaka |
| No Ee text available | 294 | Milindapañha 248, Nettippakaraṇa 37, Peṭakopadesa 9 |
| Deest in Ee | 14 | the PTS edition does not print the passage |
| Section rubric | 10 | a rubric of the printed edition, not a citable unit |
| Cross-reference in Ee | 2 | PTS refers the reader elsewhere instead of reprinting |

**A language model took part in 3,168 entries, always as one of two concurring judges and never as
the sole one.** It was not used anywhere else in this work.

There is no universal parser: each Nikāya, often each volume, has its own marker conventions. Two
independent checks were required — the identity of the unit and its location. **Content similarity
was corroboration, never the sole criterion**: in the Udāna nearly every sutta opens with the same
formula, in the Vimānavatthu the units come in repeated pairs where a neighbour scores 0.97 against
0.94 for the correct unit, and in the Niddesa an unrelated chapter reaches 0.88. A similarity
threshold there confirms the wrong pair.

## Verification

| Battery | Entries | Passed | Contradictions | Undecided |
|---|--:|--:|--:|--:|
| DN / MN / SN / AN | 3,737 | 3,151 | 0 | 586 |
| KN | 1,495 | 1,495 | 0 | 0 |

The first verifies that the CST text begins at the page and line the entry declares. The second
verifies order and measure — the printed sequence and the CST sequence must agree, and the two texts
must advance together — because in the Khuddaka the reference carries no line and content
discriminates least.

Each battery was tested by mutation: ten deliberate defects — swapped neighbours, shifts, duplicated
and broken references — and each detected ten of ten. The undecided entries are **not** counted as
collated; most are passages both editions print abbreviated, where there is nothing to compare.

## Not covered

- **Jātaka** (548). The available PTS text is Fausbøll's edition, *the Jātaka together with its
  commentary*; the canonical text is the verses alone.
- **Milindapañha (248), Nettippakaraṇa (37), Peṭakopadesa (9).** No PTS text in the source used.
- **14 entries not printed in Ee** and **10 section rubrics**. Recorded rather than left blank: that
  an edition omits a passage is a fact about that witness — *deest* in the language of an apparatus.

No other edition was consulted: not the Mahāsaṅgīti, the Thai (BUDSIR) or the Sinhalese, and not the
commentaries.

## Limitations

**What was inspected is a digitised text, not the printed volume.** Where an entry says a passage is
absent from a witness, the internal evidence is strong — a vagga uddāna announcing ten items where
the edition prints seven — but the distinction between *deest in Ee* and *absent from the copy used*
is one this edition states and does not close.

**The Buddhavaṃsa and Cariyāpiṭaka are cited in a pagination other than the one collated** (Bv 1–68,
Cp 73–101, the single volume in which PTS printed them together). The two settings diverge
progressively, so the page of those 64 entries was not verified. Each of them says so.

## Citation

> Contreras, Jorge. *A Concordance of the Pāli Canon: PTS ↔ Chaṭṭha Saṅgāyana.* 2026. CC0 1.0.

To the extent possible under law, Jorge Contreras has waived all copyright and related rights to
this work. No warranty is given. The underlying texts are in the public domain.
