# Datasets

Two files. Both are word-type lists with one annotated stem per word.

## pashto_gold(1).csv — the gold standard

2,912 word types with their stems. **Checked by Pashto language teachers**, and
the cleanest of the annotation passes made during this project.

| column | contents |
|---|---|
| `word` | the word as it appears in the corpus |
| `stem` | the annotated stem |

Measured against the documented affix inventory, **90.9% of the rows are
explained** by an affix in the inventory or by the irregular-verb dictionary:

| | rows | |
|---|---|---|
| kept whole | 1,331 | 45.7% |
| suffix removal, affix in the inventory | 1,141 | 39.2% |
| irregular-verb lemma | 175 | 6.0% |
| a different word, not a truncation | 216 | 7.4% |
| removal not in the inventory | 49 | 1.7% |

The 49 are almost all **combinations** of affixes already present (`یتوب` =
`یت` + `توب`, `یتونو` = `یت` + `ونو`), which is the multi-affix case. Two are
genuinely new and worth adding: `یی` (امریکایی → امریکا, 12 rows) and `یان`
(پوځیان → پوځ).

One thing to note when citing this set. For 216 rows the answer is a different
word rather than a truncation — `کلونو → کال`, `نجونو → نجلۍ`,
`وایی → ویل`. Those are **lemmas**, reached through the verb and irregular
plural dictionaries rather than by removing an affix. Place names are kept
whole here (`افغانستان → افغانستان`).

## test_500_news.csv — held-out test set

500 word types sampled at random from a Pashto news corpus, with no overlap
with the gold set, annotated with the stem column initially empty so that
nothing anchored the annotator to any system's output. **Never used for
tuning.**

| column | contents |
|---|---|
| `word`, `frequency` | the word and its corpus frequency |
| `gold_stem` | the annotated stem |
| `expert_stem` | a second independent pass, kept for comparison |

This is the set to quote for generalization. The gold set above shares its
annotation conventions with the rule development, so agreement with it partly
measures consistency rather than correctness.

## Archived

Earlier annotation passes, audit output and superseded worksheets are in
`archive/old_datasets/` and `archive/old_analysis/`. They are kept for
provenance and are not part of the release.

## A note on the columns, and on what is and is not independent

`test_500_news.csv` and `test_500_news_corrected.csv` both carry two columns
named `gold_stem` and `expert_stem`. **They are identical in all 500 rows.**
They are one annotation stored twice, not two passes, and the name
`expert_stem` should not be read as a second expert's judgement. The held-out
set was annotated by one person. We leave both columns in place rather than
rewriting a released file, and say so here.

The development set is different. `pashto_gold_corrected_v2.csv` is the result
of three independent annotations — by the author, a Pashto-medium school
principal and a university teacher of Pashto — adjudicated by the author. The
individual passes were not kept as separate files, so inter-annotator agreement
cannot be computed from what is released here.

## The annotation history

| File | What it is |
|---|---|
| `pashto_gold(1).csv` | the first annotation, before the rule inventory was settled |
| `pashto_gold_corrected.csv` | after the first round of policy corrections |
| `pashto_gold_corrected_v2.csv` | the released reference |
| `pashto_gold_changes(1).md` | the 42 policy corrections, each with its reason |
| `verb_rows_to_update.csv` | the verb forms considered for revision |
| `keep_whole_candidates.csv` | the 257-word keep-whole list, reported in the paper as a negative result |

166 of 2,908 shared rows (5.7%) differ between the first annotation and the
released reference. The paper reports accuracy on the subset that was never
revised, which `experiments/reproduce_paper.py` recomputes.

## Audit output

`experiments/audit_annotation.py` writes `unsupported_removals_*.csv`: every
removal in an annotated set that matches no documented affix. Each is either an
annotation error or a gap in the inventory, and the `verdict` column is left
empty for whoever rules on it.
