# Annotation guidelines — superseded

This file described the **first** annotation round, in which annotators were
given a template pre-filled with the stemmer's output and asked to correct what
was wrong. That protocol was abandoned, for the obvious reason: showing an
annotator the system's answer anchors them to it, and an evaluation built that
way measures agreement with the system rather than correctness.

The annotations released with this project were **not** produced that way. Each
annotator worked from the word list alone, with the stem column empty, and did
not see any system output or another annotator's work.

The policy actually followed is:

**[docs/02_annotation_policy.md](../docs/02_annotation_policy.md)**

Three further points in the old file are wrong under the current policy and are
recorded here so that nobody follows them by accident:

- It said proper nouns stay whole, so `افغانستان → افغانستان`. The released
  reference strips `‑ستان` like any other affix: `افغانستان → افغان`.
- It said verbs are lemmatized to the infinitive, `کوي → کول`. Mapping a
  form to a different word is lemmatization, and this project keeps the two
  tasks apart, so the dictionary that does it is off by default. The
  infinitive itself is **not** reduced further: the released reference has
  `لوستل → لوستل`, and of its 124 words ending in `‑ل` not one has the bare
  `‑ل` removed. (An earlier version of this note claimed the opposite.)
- It said to write `ي` as `ی`. No yeh letter is ever rewritten. All five
  (`ی ي ې ۍ ئ`) are distinct and are preserved everywhere.

The file is kept, rather than deleted, because the paper reports that the first
annotation pass had to be audited and revised, and this is what that pass was
working from.
