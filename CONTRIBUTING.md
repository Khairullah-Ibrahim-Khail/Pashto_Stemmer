# Contributing

The most useful contributions to a rule-based stemmer are small and specific:
an affix with a source, or a word it gets wrong. You do not need to be a
programmer to make either.

## Reporting a wrong stem

Open an issue with three lines:

```
word:     خواړه
expected: خواړه
got:      خواړ
```

That is enough. If you can say which affix was wrongly removed, or point to a
grammar, better — but the three lines are the part we need.

Some disagreements are not bugs. The output of a stemmer is a class label, not
a word: `پوهنتون → پوهن` is correct even though `پوهن` is not a word on its own.
`docs/02_annotation_policy.md` sets out what counts as a stem here.

## Adding or changing a rule

1. Add the entry to `pashto_stemmer/suffixes.py` or `prefixes.py`.
2. Give it a source in the `note`: `[T&R ch.4 animate plurals]`,
   `[Penzl §52 suffixes of the doer]`. If you have no published source, say so —
   an honest `author-proposed` is better than a citation nobody can check.
3. Decide `strip_allowed`. An affix that is real but unsafe to remove is
   recorded with `strip_allowed="no"`; 27 entries are in that state today.
4. Run the numbers and put them in the pull request:

```bash
python experiments/reproduce_paper.py
```

Report the before and after for both sets. A rule that costs accuracy can still
be right, and one that gains can still be wrong — but the number has to be on
the table either way. Three rules in this project were removed after being
measured, and one was kept despite costing 0.04 points.

## Challenging the data, not the code

The reference is not above question, and two scripts exist for arguing with it:

```bash
python experiments/audit_annotation.py   # removals matching no documented affix
python experiments/agreement.py          # inter-annotator agreement
```

`audit_annotation.py` currently leaves 33 removals in the held-out set
unexplained. Each is either an annotation error or an affix the inventory
lacks. Resolving any of them is a real contribution.

## Before you open a pull request

```bash
for f in tests/test_*.py; do python "$f"; done
python experiments/reproduce_paper.py
```

Tests must pass. If a result moved, say so in the description and why.

## What will be refused

- Merging the five yeh letters (ی ي ې ۍ ئ). They carry gender, number and
  case; `سړی` and `سړي` are different words.
- Any machine learning. This is a rule-based system by design, and the claim
  that every decision traces to a rule or a dictionary entry has to stay true.
- A citation that cannot be checked.
