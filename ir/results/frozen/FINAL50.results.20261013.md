# Frozen result — 50 queries

Date: 2026-10-13. This is the result the paper reports.

The collection reached 50 queries in three stages: 30, then 39, then 50. The
stemmer did not change between the last two stages, so the 39-query and
50-query numbers are the same experiment on a larger sample.

## How the judgements were made

Every document was judged by three native Pashto speakers working together.
They read it, discussed whether it answered the query, and recorded a label
only when all three agreed. The labels are therefore adjudicated, not
independent, and there is no inter-annotator agreement coefficient for them:
that is a property of the design, not an omission.

The pool for each query is the top 25 documents from each of the two runs,
unioned and shuffled under a fixed seed, so no judge could tell which system
retrieved a document or at what rank.

## Reproduce

    python verify_integrity.py     # must print 12/12
    python stats_tests.py          # must print 9/9
    python run_experiment.py       # the two runs and the four metrics
    python significance.py         # the table below
    python test_gating.py          # the two gating decisions
    python per_query.py            # the per-query breakdown

## Headline

    50 queries, 1,891 judgements, 1,184 relevant
    
    metric        unstemmed   stemmed      diff      t       p     w/l   sign p
    ---------------------------------------------------------------------------
    MAP              0.5785    0.6854   +0.1070   3.60   0.001   39/11    0.000
    nDCG@10          0.7162    0.7583   +0.0420   1.23   0.226   24/13    0.099
    P@10             0.6780    0.7240   +0.0460   1.41   0.165   20/11    0.150
    Recall@10        0.3011    0.3502   +0.0490   2.09   0.042   20/11    0.150
    
      MAP bootstrap 95% CI  [+0.0503, +0.1643]  (10,000 resamples, seed 20261010)
      Cohen's d 0.509; 31 queries needed for 80% power at alpha .05, and this collection has 50

MAP is significant under both tests, and recall at rank 10 under the t-test.
nDCG@10 and P@10 improve by a similar margin and neither clears what 50
queries can resolve.

## How the result moved as the collection grew

    queries   MAP unstemmed -> stemmed      p       recall@10 p
    30        0.5792 -> 0.6367            0.196     not reported
    39        0.5407 -> 0.6517            0.005     0.083
    50        0.5785 -> 0.6854            0.001     0.042

No decision changed at any stage. The gating conclusions below came out the
same at 39 queries and at 50, which is the evidence that they are not
artefacts of a small sample.

## The gating decisions, re-tested at 50

    configuration                 MAP     nDCG@10    P@10   Recall@10
    no stemming                0.5785     0.7162  0.6780      0.3011
    released (-tun gated)      0.6854     0.7583  0.7240      0.3502
    -tun stripped              0.6739     0.7448  0.7140      0.3475
    -stan gated                0.6848     0.7573  0.7220      0.3499
    both changed               0.6733     0.7439  0.7120      0.3473

Gating the place-forming suffix is worth 0.0115 MAP and is the only
configuration that wins all four measures. Gating the similar -stan measures
marginally worse (-0.0007) and is not done.

Why the first merge is harmful and the second is not: of the 1,809 documents
containing روغتون 'hospital', 696 (38%) also contain روغتیا 'health'; but of
the 5,377 containing روغتیا, only 696 (13%) contain روغتون. The overlap is
one-directional, so conflation adds 4,681 documents about health that never
mention a hospital and no hospital document the unstemmed index did not
already reach. On q110 the judgements agree: of the 43 retrieved documents
containing روغتون, 32 were judged relevant; of the 13 containing only روغتیا,
none were.

## Integrity

      pass  1  every judged query has query text  -- missing []
      pass  2  no query id was reused for different text  -- drifted []
      pass  3  every judged docid exists in the corpus  -- 0 unknown, e.g. []
      pass  4  every grade is 0 or 1  -- saw []
      pass  5  every query has at least one relevant document  -- empty []
      pass  6  no duplicate query-document rows  -- 0 duplicates
      pass  7  archived judgements match current document text  -- 0 of 8,191 rows drifted across 6 archives
      pass  8  pool depth covers the evaluation depth  -- pool 25 per run vs eval depth 10
      pass  9  retrieval depth exceeds the pool  -- top-k 1000 vs pool 25
      pass  10 the stemmer imports and actually changes words  -- 4/5 probe words changed
      pass  11 stemming conflates the vocabulary  -- 16,496 -> 10,607 types (35.7% fewer)
      pass  12 the tokenizer uses the project Normalizer
    12/12 checks pass
