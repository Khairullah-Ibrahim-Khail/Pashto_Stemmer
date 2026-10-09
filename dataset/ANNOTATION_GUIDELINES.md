# Gold-Standard Annotation Guidelines — Pashto Stemmer

Goal: produce trustworthy ground-truth **stems** for the most frequent Pashto
words so we can report real accuracy and Paice over/under-stemming indices.

The file `gold_annotation_template.csv` is **pre-filled** with the stemmer's
best guess. You only need to correct what is wrong — minimal typing.

## Columns

| Column | Meaning | What to do |
|---|---|---|
| `word` | the normalized surface word | do not change |
| `frequency` | corpus frequency | do not change |
| `proposed_stem` | the stemmer's output | do not change (reference) |
| `correct_stem` | **the true light stem** | edit ONLY if `proposed_stem` is wrong |
| `pos` | guessed part of speech (N/ADJ/V) | fix if clearly wrong |
| `is_irregular` | 1 if a suppletive/irregular verb form | set 1/0 |
| `is_compound` | 1 if a closed compound | set 1/0 |
| `confidence` | stemmer confidence | review low ones first |
| `notes` | free text | optional |

## What is a "light stem" here?

Reduce a word to its **most basic form that is still a real Pashto word**,
removing inflection (number, gender, case, verb agreement) and clearly
productive derivation. Do **not** reduce to an abstract triliteral root.

Examples of the target:
- \کورونه (houses) → کور
- \خبرونه (news) → خبر
- \ښکلي / ښکلې (beautiful, m/f) → ښکلی
- \غواړي / وغوښت (wants / wanted) → غوښتل  (infinitive lemma for verbs)
- \افغانستان (Afghanistan) → افغانستان  (proper nouns stay whole)
- \او، په، د (function words) → unchanged (stopwords)

## Conventions

1. **Verbs** are lemmatized to the **infinitive** (ends in ـل): کوي → کول.
2. **Proper nouns** (names of people, countries, cities, organizations) are
   left **unchanged**.
3. **Stopwords / function words** are left **unchanged**.
4. Keep the distinct feminine yeh letters (ې ۍ); write ي as ی (already
   normalized in the file).
5. If a word is ambiguous, choose the reading that fits general news text and
   add a note.

## After annotating

Save the file (UTF-8) and run:

```bash
python experiments/evaluate_gold.py dataset/gold_annotation_template.csv
```

This prints exact-match **accuracy** and **Paice UI/OI/SW** for our stemmer
and the baseline, using your `correct_stem` column as ground truth.
