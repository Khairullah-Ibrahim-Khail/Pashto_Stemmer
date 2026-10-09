# External word lists

Two independently annotated Pashto word lists, used as a generalisation check
after the system was finalised. **Neither was produced by this project**, and
neither follows this project's annotation policy.

| file | types | columns |
|---|---|---|
| `pashto_5k_stemmed.csv` | 5,000 | `original,stem` |
| `pashto_10k_stemmed.csv` | 10,000 | `original,stem` |

```
python experiments/evaluate_external.py
```

| dataset | types | exact | ye-folded |
|---|---:|---:|---:|
| 5,000 types | 5,000 | 71.96% | 80.14% |
| — Aslamzai & Saad (2015) | | 51.24% | 57.36% |
| 10,000 types | 10,000 | 70.39% | 77.69% |
| — Aslamzai & Saad (2015) | | 47.95% | 53.68% |

## Two things to know before quoting these numbers

**Their reference column is ye-normalised; their word column is not.** Both
files write the stem with `ی` while the word keeps `ي`, so a stem that
correctly preserves the word's own letter is scored wrong. That is the whole
7–8 point gap between the two columns. The same folded comparison is worth only
1.51 points on our development set and 0.80 on our held-out set, because those
are internally consistent — which is what locates the problem in their spelling
rather than in the stemming.

**They follow a different annotation policy.** Of the words shared with our
development reference, the two agree 70.8% (5k) and 64.1% (10k). The
differences are systematic, especially for verbs: `اخلی` is stemmed to `اخ`
here and `اخیستل` in our reference, `بدلولو` to `بدلول` rather than `بدل`.
These lists test whether the system generalises, not whether it is correct
under our policy.

## A warning about machine-generated references

A third list was tested and rejected. Its stem column turned out to have been
produced by this stemmer: of 19,948 rows our output differed on 9, all of them
Arabic broken plurals routed through the irregular-verb dictionary. It scored
99.95%, which measured nothing except that the system reproduces itself. It
also agreed with the human-annotated 10k list only 70.4% of the time on shared
words, while matching our output almost perfectly — the signature of a
machine-generated reference.

If you add another list here, check it against the system before reporting
anything: an accuracy above roughly 95% on unseen Pashto word types is not a
result, it is a sign that the reference came from the thing being measured.
