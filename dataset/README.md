# Datasets

Two annotated evaluation sets, plus the individual annotation passes and the
audit output. Every figure quoted below is recomputed by a script in
`experiments/`; nothing here is stated from memory.

## The two evaluation sets

| file | rows | columns | what it is |
|---|---|---|---|
| `pashto_gold_corrected_v2.csv` | 2,912 | `word,stem` | the development set, the released reference |
| `test_500_news_corrected.csv` | 500 | `no,word,frequency,stem,note` | the held-out set, sampled from news text |
| `test_500_news.csv` | 500 | same | the held-out set before its audit revision |

Of the development set, 2,717 types are within the stemming task and 195 have a
reference that is a different word rather than a truncation — an Arabic broken
plural or a suppletive verb form — which no truncating stemmer can reach. For
the held-out set the split is 499 and 1. `experiments/reproduce_paper.py`
applies that partition and prints both.

## Annotation, and a note on the columns

Both sets were annotated by the same three native speakers — the author, a
Pashto-medium school principal and a university teacher of Pashto.

On the development set each worked separately and the author adjudicated the
differences. Two of those three passes are released in `annotations/`, so the
agreement between them can be recomputed:

```
python experiments/agreement.py
```

On the 2,725 types both annotated they chose the same stem for **96.88%**
(Cohen's κ **0.969**); on the binary judgement of whether the word carries an
affix at all, **98.24%** (κ **0.965**). The adjudicated reference is 93.64%
identical to the school principal's pass and 94.98% to the university
teacher's.

On the held-out set all three agreed on the result, which is released as a
single `stem` column, so no coefficient is computed for it.

An earlier release of these two files carried the reference twice, as
`gold_stem` and `expert_stem`, with identical contents in all 500 rows. The
duplicate invited the reading that `expert_stem` was a second, independent
pass, which it never was, so the files now carry one `stem` column like the
development set. No label changed.

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

## External word lists

`external/` holds two independently annotated lists, 5,000 and 10,000 types,
that were **not** produced by this project and do not follow its annotation
policy. They are a generalisation check, reported in the paper as Table IX and
reproduced by `experiments/evaluate_external.py`. See
[external/README.md](external/README.md) for what to watch for before quoting
their numbers.

## Audit output

`experiments/audit_annotation.py` writes `unsupported_removals_*.csv`: every
removal in an annotated set that matches no documented affix. Each is either an
annotation error or a gap in the inventory.

The held-out file has been gone through in full. Of its 54 rows, 29 take
material off one end of the word: **19 are gaps in the inventory**, mostly case
and gender variants of affixes already held (`ولو` beside `ول`, `ګرو` beside
`ګر`, `یزې` beside `یزه`); **8 are annotation errors**, clustering on English
loans and proper names; **2 are ambiguous**. The remaining **25 take material
off both ends** and are all verbs (`وښيي → ښي`, `رارسېدو → رسېد`): the ending
is in the inventory, the perfective or directional prefix is not, because those
prefixes were measured and dropped. Every row carries a `verdict` and a `why`.

Of the development file's 108 rows, the 15 two-ended ones are classified on the
same grounds; the other 93 are not yet classified. Rerunning the audit
preserves any verdict already written, so the work is safe to do in stages.

An earlier version of the audit script reported only one-ended removals, and so
silently dropped 26 held-out and 15 development rows — exactly the rows the
inventory cannot explain. The counts above are the corrected ones.
