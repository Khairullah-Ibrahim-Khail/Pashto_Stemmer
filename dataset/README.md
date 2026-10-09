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
