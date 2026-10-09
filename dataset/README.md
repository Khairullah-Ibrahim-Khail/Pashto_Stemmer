# Datasets

Two annotated evaluation sets, plus the individual annotation passes and the
audit output. Every figure quoted below is recomputed by a script in
`experiments/`; nothing here is stated from memory.

## The two evaluation sets

| file | rows | columns | what it is |
|---|---|---|---|
| `pashto_gold_corrected_v2.csv` | 2,912 | `word,stem` | the development set, the released reference |
| `test_500_news_corrected.csv` | 500 | `no,word,frequency,gold_stem,note,expert_stem` | the held-out set, sampled from news text |
| `test_500_news.csv` | 500 | same | the held-out set before its audit revision |

Of the development set, 2,717 types are within the stemming task and 195 have a
reference that is a different word rather than a truncation — an Arabic broken
plural or a suppletive verb form — which no truncating stemmer can reach. For
the held-out set the split is 499 and 1. `experiments/reproduce_paper.py`
applies that partition and prints both.

## Annotation, and a note on the columns

Both sets were annotated independently by the same three native speakers — the
author, a Pashto-medium school principal and a university teacher of Pashto —
and adjudicated by the author.

Two of the three development-set passes are released in `annotations/`, so the
agreement between them can be recomputed:

```
python experiments/agreement.py
```

On the 2,725 types both annotated they chose the same stem for **96.88%**
(Cohen's κ **0.969**); on the binary judgement of whether the word carries an
affix at all, **98.24%** (κ **0.965**). The adjudicated reference is 93.64%
identical to the school principal's pass and 94.98% to the university
teacher's.

`test_500_news.csv` and `test_500_news_corrected.csv` carry two reference
columns, `gold_stem` and `expert_stem`, whose contents are identical in all 500
rows. They record the one adjudicated reference under two names; `expert_stem`
is not a second, separate pass. We leave both in place rather than rewrite a
released file.

## The annotation history

| File | What it is |
|---|---|
| `annotations/annotator_school_principal.csv` | one independent pass, the school principal |
| `annotations/annotator_university_teacher.csv` | one independent pass, the university teacher |
| `pashto_gold_corrected_v2.csv` | the released reference, adjudicated by the author |
| `pashto_gold_changes(1).md` | the 42 policy corrections, each with its reason |
| `verb_rows_to_update.csv` | the verb forms considered for revision |
| `keep_whole_candidates.csv` | the 257-word keep-whole list, reported in the paper as a negative result |

116 verb forms in the reference were revised for consistency with the verb
analysis, and 81 of those match the reading the system itself produces — 3.0%
of the stemming types. The paper states this dependency rather than leaving it
to be found.

## Audit output

`experiments/audit_annotation.py` writes `unsupported_removals_*.csv`: every
removal in an annotated set that matches no documented affix. Each is either an
annotation error or a gap in the inventory, and the `verdict` column is left
empty for whoever rules on it.
