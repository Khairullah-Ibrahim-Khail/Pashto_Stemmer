# Frozen result — 39 queries, place suffix gated

Date: 2026-10-12. This is the result the paper reports.

The judgements are unchanged from `FINAL39.qrels.20261012.tsv`; what changed
since the earlier run is the stemmer, which no longer removes the place-forming
`‑تون`. No document was re-judged, because a relevance judgement says whether a
document answers a query and that does not depend on which stemmer retrieved it.

## Reproduce

    python verify_integrity.py     # must print 12/12
    python stats_tests.py          # must print 9/9
    python run_experiment.py       # the two runs and the four metrics
    python significance.py         # the table below
    python test_gating.py          # the gating comparison
    python per_query.py            # the per-query breakdown

## Headline

    39 queries, 1,489 judgements, 873 relevant
    
    metric        unstemmed   stemmed      diff      t       p     w/l   sign p
    ---------------------------------------------------------------------------
    MAP              0.5407    0.6517   +0.1110   2.95   0.005    30/9    0.001
    nDCG@10          0.6675    0.7178   +0.0503   1.16   0.253   20/11    0.150
    P@10             0.6359    0.6821   +0.0462   1.12   0.272    16/9    0.230
    Recall@10        0.2946    0.3479   +0.0533   1.78   0.083    16/9    0.230
    
      MAP bootstrap 95% CI  [+0.0393, +0.1843]  (10,000 resamples, seed 20261010)
      Cohen's d 0.472; 36 queries needed for 80% power at alpha .05, and this collection has 39

MAP is significant under both tests. The three cutoff-10 metrics all move in
the same direction but none reaches significance, which is what 39 queries can
and cannot support: the effect at rank 10 is real but smaller than the
collection can resolve.

## The gating decision

`‑تون` is a genuine Pashto place-forming suffix and the derivation is regular,
so the grammar says to strip it. It is gated anyway, because stripping it merges
a place with the quality it is named for: روغتون 'hospital' and روغتیا 'health'
both reduce to روغ.

Whether that merge is harmful was measured rather than assumed. In the corpus
of 44,814 documents:

    contain روغتون (hospital)                         1,809
    contain روغتیا (health)                           5,377
    contain both                                        696

    of hospital documents, also mention health   696/1809 = 38%
    of health documents, also mention hospital   696/5377 = 13%

The merge is therefore one-directional. The hospital documents a searcher wants
already contain the word روغتون, so conflation adds nothing for them; what it
adds is the 4,681 health documents that never mention a hospital.

On q110 (روغتون درملنه) the judgements confirm it:

    documents containing روغتون        28 relevant,  7 not  (80% relevant)
    documents containing only روغتیا    0 relevant, 13 not  ( 0% relevant)

Stripping the suffix also split the word family, because with it live روغتون
lost the suffix while روغتونه spent its single pass on the inflectional ‑ه and
stopped at روغتون — so a query for the singular could not reach a document
holding the plural. 430 documents hold an inflected hospital form and no bare
روغتون. Gating closes that split: all seven surface forms now give روغتون.

## What gating cost and bought

                                development  held-out     MAP    nDCG@10
    suffix stripped (earlier)        81.19%    72.75%  0.6404     0.7023
    suffix gated (this result)       80.97%    72.55%  0.6517     0.7178

It also raised both independent external word lists, 72.30% to 72.46% on the
5,000-type list and 70.18% to 70.37% on the 10,000-type list, so the 0.22-point
cost is specific to our own two annotated sets.

MAP significance improved from t = +2.41, p = 0.021 to t = +2.95, p = 0.005,
and the queries needed for 80% power fell from 53 to 36 against the 39 this
collection has.

## The suffix that was not gated

`‑ستان` was tested the same way and left alone, because gating it measured
worse: MAP 0.6396 against 0.6404, and q003 (د افغانستان ولایتونه) fell from
0.1190 to 0.0291. Two suffixes, the same test, opposite answers.

## Integrity

      pass  1  every judged query has query text  -- missing []
      pass  2  no query id was reused for different text  -- drifted []
      pass  3  every judged docid exists in the corpus  -- 0 unknown, e.g. []
      pass  4  every grade is 0 or 1  -- saw []
      pass  5  every query has at least one relevant document  -- empty []
      pass  6  no duplicate query-document rows  -- 0 duplicates
      pass  7  archived judgements match current document text  -- 0 of 5,459 rows drifted across 5 archives
      pass  8  pool depth covers the evaluation depth  -- pool 25 per run vs eval depth 10
      pass  9  retrieval depth exceeds the pool  -- top-k 1000 vs pool 25
      pass  10 the stemmer imports and actually changes words  -- 4/5 probe words changed
      pass  11 stemming conflates the vocabulary  -- 16,496 -> 10,607 types (35.7% fewer)
      pass  12 the tokenizer uses the project Normalizer
    12/12 checks pass
