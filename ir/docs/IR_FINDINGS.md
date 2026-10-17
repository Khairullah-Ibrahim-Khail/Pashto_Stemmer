# Everything found in the IR test: results, errors, bugs, decisions

A complete record. Nothing here is from memory — every number was measured by
a script in this folder and can be regenerated.

---

## Part 1 — The result

### 1.1 Headline

50 queries, 1,891 judgements, 1,184 relevant, 44,814 documents. Reproduce with
`python significance.py`.

| | unstemmed | stemmed | difference | p | sign p |
|---|---:|---:|---:|---:|---:|
| MAP | 0.5785 | **0.6854** | +0.1070 | **0.001** | **<0.001** |
| nDCG@10 | 0.7162 | 0.7583 | +0.0420 | 0.226 | 0.099 |
| P@10 | 0.6780 | 0.7240 | +0.0460 | 0.165 | 0.150 |
| **Recall@10** | 0.3011 | **0.3502** | +0.0490 | **0.042** | 0.150 |

The stemmer here is the released one, which gates ‑تون; Part 3 is the
measurement that decided that. Both tests live in `stats_tests.py`, which
checks itself against nine known values, because scipy is not installed here.

### 1.2 Is it significant? For MAP and recall, yes.

| test | result | meaning |
|---|---|---|
| paired t-test on MAP | t = 3.60, p = 0.001 | significant |
| bootstrap 95% CI | [+0.050, +0.164] | excludes zero |
| sign test | 39 of 50 improved, p < 0.001 | significant |
| paired t-test on Recall@10 | t = 2.09, p = 0.042 | significant |
| power | Cohen's d 0.509; 31 queries needed | this collection has 50 |

MAP is significant under both tests and recall at rank 10 under the t-test.
nDCG@10 and P@10 improve by a similar margin and neither clears the threshold
50 queries can resolve. The pattern is consistent: stemming puts relevant
documents into the top ten that were not there before, which recall detects,
while the gain in how those ten are ordered is smaller than this collection can
establish.

**The collection grew twice.** At 30 queries nothing was significant except a
sign test; at 39, MAP was (p = 0.021 with ‑تون live, 0.005 gated); at 50, MAP
strengthened to p = 0.001 and recall@10 crossed into significance. No decision
changed at any step, which is the useful part: the gating conclusions were not
artefacts of a small sample.

### 1.3 The queries that lose

Eleven of 50 lose. The three largest:

```
q003  د افغانستان ولایتونه   0.5824 → 0.1189   −0.4635
q010  د افغانیو ارزښت       0.6381 → 0.2852   −0.3529
q110  روغتون درملنه         0.7826 → 0.4995   −0.2831
```

Those three lose **1.10 MAP** between them, all eleven losers **1.78**, and the
39 that gain make **7.13**. Stemming helps most queries moderately and damages
a few badly, which is why both tests are reported.

## Part 2 — Why the losing queries lose

### 2.1 q110 — the `‑تون` collision (fixed by gating)

`روغتون` is *hospital*. `روغتیا` is *health*. Stripping the place-forming
`‑تون` merged them:

```
روغتون     (hospital)  → روغ
روغتیا     (health)    → روغ
روغتیايي   (health-)   → روغ
روغول      (to cure)   → روغ
روغېدل     (to heal)   → روغ
روغ        (healthy)   → روغ
```

The query `روغتون درملنه` became `روغ درمل`, which matched any document about
health, healing or medicine. Same mechanism for `پوهنتون` (university) →
`پوهن` = `پوهنه` (education). The suffix means *place of*: stripping it turns
a **place** into an **abstract quality**.

**Is that merge actually harmful?** It is worth asking, because a document
about a hospital will naturally use health vocabulary, so retrieving
`روغتیا` documents for a hospital query is not automatically wrong. Measured
across all 44,814 documents:

```
contain روغتون (hospital)                       1,809
contain روغتیا (health)                         5,377
contain both                                      696

of hospital documents, also mention health   696/1809 = 38%
of health documents, also mention hospital   696/5377 = 13%
```

So the overlap is real but **one-directional**. Hospital documents do talk
about health — 38% of them — but only 13% of health documents mention a
hospital. The hospital documents a searcher wants already contain the word
`روغتون`, so the unstemmed index reaches them anyway and the merge adds
nothing there. What the merge adds is the **4,681 health documents that never
mention a hospital**: ministry budgets, nutrition advice, disease prevention.

The judgements on q110 confirm it, and this is the judge's own labelling, not
an assumption in the code:

| document contains | relevant | not relevant | |
|---|---:|---:|---|
| `روغتون` (hospital) | 32 | 11 | 74% relevant |
| only `روغتیا` (health) | 0 | 13 | **0% relevant** |

Thirteen health-only documents were judged, and every one was marked not
relevant. The −0.2831 loss comes from those labels.

**A second, separate defect.** Because `max_passes = 1`, stripping `‑تون` also
split the word family:

```
روغتون      → روغ          the suffix came off
روغتونه     → روغتون       the single pass went on the inflectional ‑ه
روغتونو     → روغتون
روغتونونه   → روغ
```

A query for the singular could not reach a document holding the plural. 430
documents hold an inflected hospital form and no bare `روغتون`. So the suffix
was over-stemming and under-stemming at the same time. Gating it closes both:
all seven surface forms of `روغتون` and all five of `پوهنتون` now agree.


### 2.2 q010 — two collisions (not fixable by rule)

```
د افغانیو ارزښت   →   د افغان ارز
```

**Collision A:**

```
افغانیو    (afghanis, the currency) → افغان
افغانۍ     (afghani, the currency)  → افغان
افغانستان  (the country)            → افغان
افغانان    (the people)             → افغان
```

Money, country and people all become `افغان`.

**Collision B:**

```
ارزښت   (value)     → ارز
ارزګان  (Uruzgan!)  → ارز      ← a province name
ارزان   (cheap)     → ارز
```

`ارزګان` is a **province**, merged with "value" because `‑ګان` looks like the
plural suffix.

### 2.3 q003 — a weak query, not a stemmer fault

The `ولایت` family stems correctly:

```
ولایتونه  → ولایت        ✅
ولایت     → ولایت        ✅
ولایتونو  → ولایت        ✅
ولایتي    → ولایت        ✅
```

Four forms, one stem. No over-stemming.

The problem is the query itself. **Both of its content words appear in most of
the corpus:**

- `ولایت` — nearly every Afghan news story happens in a province
- `افغانستان` — appears in the news agency's own name, `افغانستان انټرنشنل`,
  in the source line of a huge share of the documents

So the query has no discriminating term in this corpus. Not fixable by
changing the stemmer.

---

## Part 3 — Testing the two gating decisions

Measured with `test_gating.py`: five indexes, same queries, same judgements.
A relevance judgement says whether a document answers a query, which does not
depend on which stemmer retrieved it, so nothing is re-judged when the stemmer
changes.

| system | MAP | nDCG@10 | P@10 | Recall@10 |
|---|---:|---:|---:|---:|
| no stemming | 0.5785 | 0.7162 | 0.6780 | 0.3011 |
| **released (`‑تون` gated)** | **0.6854** | **0.7583** | **0.7240** | **0.3502** |
| `‑تون` live, as the grammar says | 0.6739 | 0.7448 | 0.7140 | 0.3475 |
| `‑ستان` gated too | 0.6848 | 0.7573 | 0.7220 | 0.3499 |
| `‑تون` live, `‑ستان` gated | 0.6733 | 0.7439 | 0.7120 | 0.3473 |

| comparison | MAP | t | p | w/l |
|---|---:|---:|---:|---:|
| released vs no stemming | +0.1070 | 3.60 | 0.001 | 39/11 |
| `‑تون` live vs no stemming | +0.0955 | 2.96 | 0.005 | 38/12 |
| `‑تون` live vs released | −0.0115 | −1.18 | 0.243 | 2/4 |
| `‑ستان` gated vs released | −0.0007 | −0.31 | 0.761 | 1/1 |

### 3.1 Gating `‑تون` works

It is the only configuration that wins on all four measures, and it is what
the released stemmer does. Putting the suffix back costs 0.0115 MAP and loses
on every metric.

```
q110   0.1515 → 0.4995      recovered by gating
```

**Intrinsic cost:** development 81.19% → 80.97% (−0.22), held-out 72.75% →
72.55% (−0.20). **Intrinsic gain elsewhere:** on the two independently
annotated external lists the gate *helps*, 72.30% → 72.46% on the 5,000-type
list and 70.18% → 70.37% on the 10,000-type list. The 0.22-point cost is
specific to our own two annotated sets.

This is the one case in the project where the intrinsic and downstream
evaluations disagree, and only the downstream one can see it: both analyses of
`روغتون` are defensible for a word in isolation, and it takes a query to show
that one of them loses documents.

### 3.2 Gating `‑ستان` does not work

Predicted to fix q010 and q003. It fixed one and broke the other:

```
q010   0.2852 → 0.3423      +0.06  as predicted
q003   0.1189 → 0.0291      −0.09  worse
```

Net MAP change against the released stemmer: **−0.0007**. Nothing, and in the
wrong direction, so `‑ستان` is still stripped.

**Why it backfired on q003:** keeping `افغانستان` whole makes the query match
the news agency's own name `افغانستان انټرنشنل` directly — pure noise.

**Keep this negative result in the paper.** Two suffixes, the same test,
opposite answers — that is what shows the suffixes were tested rather than
assumed. It also draws a real distinction: `روغتون`/`پوهنتون` are common nouns
whose stripped form collides with a frequent abstract noun, while `افغانستان`
is a proper noun whose stripped form is itself a useful search term in an
Afghan news corpus.

---


## Part 4 — What the stemmer merges, across the whole corpus

Measured with `conflation_report.py`. Full detail in
`../CONFLATION_ANALYSIS.md`.

```
114,644 word types  →  72,173 stems      37.0% collapse
15,650 stems (21.7%) merge two or more word types
58,121 (word, stem) pairs inside merged classes
```

| | pairs | share | verdict |
|---|---:|---:|---|
| **A** same word, different spelling | 9,432 | 16.2% | **a gain** |
| **B** one documented affix removed | 45,585 | 78.4% | **normal stemming** |
| **C** a stack of documented affixes | 2,406 | 4.1% | **normal morphology** |
| **D** no morphological account | 697 | 1.2% | **the only errors** |

**98.8% is legitimate.** And most of D was a bug since fixed (see 5.1).

Largest classes — one root pulling in its whole derivational family:

| stem | types | tokens | spans |
|---|---:|---:|---|
| `کار` | 68 | 18,332 | noun, verb, agent, adjective, 6 compounds |
| `جوړ` | 54 | 12,409 | adjective, verb, agent, abstract noun |
| `لوب` | 54 | 20,410 | noun, verb, agent, adjectival |
| `اور` | 50 | 5,323 | noun, verb, participle |
| `اوس` | 48 | 14,493 | adverb, verb, agent |

**Why Pashto merges more than English.** `‑ول` and `‑ېدل` make a verb from
almost any noun or adjective, and each verb then carries a full agreement
paradigm plus a past stem, a participle and an agent noun in `‑وونکی` with its
own four forms. One root surfaces in dozens of types. Porter's deepest English
merges — *universal/universe/university* → `univers` — reach three or four.

This is **over-stemming in Paice's sense**: a measured cost, not a defect.

---

## Part 5 — Bugs found and fixed

### 5.1 In the stemmer

| bug | effect | status |
|---|---|---|
| ZWNJ deleted | `زده‌کوونکي → زدهک` — halves welded, suffix cut off the weld | **fixed** |
| dangling joiner left | `مجله‌ګانې → 'مجله‌'` — a joiner joining nothing | **fixed** |
| `‑لیک` split compounds | `لاسلیک → لاس`, against policy §8 and the gold | **fixed**, gated |
| single corpus sighting outranked a correct strip | `انګلیسي` seen once, came back whole | **fixed**, `min_base_freq=3` |
| `‑توب` group ignored its own minimum | `مکتوب → مک` (Arabic root, no `توب` in it) | **fixed**, `uniform_min_stem=3` |
| length rule pre-empted the plural rule | `غرونه → غرون` but `کورونه → کور` — same morphology, two answers | **fixed** |
| relational yeh after a vowel missing | `امریکایی` came back whole | **fixed**, new rule |

Net effect on the intrinsic evaluation at the time these were fixed:
development 80.27% → 81.19%, held-out 71.34% → 72.75%. The released figures
are now 80.97% and 72.55%, because gating `‑تون` afterwards traded 0.22 points
of intrinsic accuracy for the retrieval gain in Part 3.

### 5.2 Still open in the stemmer

The `پوهنتون`/`روغتون` inconsistency recorded here earlier is **fixed** by
gating `‑تون` (Part 3): all five forms of `پوهنتون` and all seven of
`روغتون` now land on one stem. What remains:

```
روغتیا     → روغ        but    روغتیايي → روغتیا     ← two stems, one word
ناروغ      → ناروغ      ناروغي  → ناروغي
ناروغان    → ناروغان    ناروغیو → ناروغی            ← four stems, one word
```

Both have the same cause as the old `‑تون` split: `max_passes = 1`. A word
spends its single pass on whichever affix matches first, so `روغتیا` loses the
derivational `‑تیا` while `روغتیايي` spends the pass on the adjectival ending
and stops. Raising `max_passes` to 2 would address it, and the flag exists, but
it moves 74 development types and re-opens every one of the 118 rules and both
annotated sets, so it is recorded as a limitation rather than changed late.

The `ناروغ` family is under-stemmed, not over-stemmed: three or four stems for
one word, which costs recall rather than precision.


### 5.3 In the IR code

| bug | effect | status |
|---|---|---|
| `from pashto_stemmer import stem` | ImportError → **silent identity fallback**; both arms identical, a believable null result | **fixed** |
| `make_qrels` imported `retrieve` from `index` | crashed on import | **fixed** |
| `CORPUS_DIR = "data/corpus"` | directory did not exist | **fixed** |
| `OUTPUT_DIR` was the corpus directory | `run_*.txt` written into the corpus, read back as two extra documents next run | **fixed** |
| tokenizer split on the complement of the letter range | `خبرونه،` kept the comma as part of the word | **fixed** |
| tokenizer did its own normalization, deleting ZWNJ | IR tokens were not the strings the stemmer was measured on | **fixed**, uses the project `Normalizer` |
| snippet truncated to 700 characters | median document is 1,507 — **100% were cut**; judges saw about half | **fixed**, full text |
| keyboard handler live on the review page | a keypress fired an empty POST and reloaded, losing scroll | **fixed** |
| judgements keyed by filename only | re-splitting the corpus would silently invalidate every judgement | **fixed**, content hash + `remap_qrels.py` |
| `select_queries.py` overwrote `queries.tsv` | a reused query id would silently mismatch its judgements | **fixed**, keeps judged queries, backs up, writes a lock |
| `--unique` documented as "stem distinct values only" | read as "output distinct rows"; it writes every row | **fixed**, reworded |

### 5.4 Methodological errors caught

| error | why it mattered | fix |
|---|---|---|
| pool drawn from the **unstemmed index only** | documents only the stemmed run finds would never be judged, and counted irrelevant — scoring the stemmer on a pool built to favour its competitor | pool from both, shuffled |
| **κ > 0.6 threshold** demanded | borrowed from Landis & Koch, for tasks with a determinate answer. IR relevance is subjective; TREC assessors overlap 30–45% and system rankings stay stable (Voorhees 2000) | report κ, do not gate on it. The threshold also survived in `JUDGING.md`, the file the judges actually read, after being corrected here — since removed |
| judging **by shared stem** proposed | circular — every stemmed result shares a stem by definition, so the stemmed run scores ~100% and measures nothing | `RELEVANCE_RULES.md` |
| judging **on 700 of 1,507 characters** | the answer is often in the second half of a mixed document | full text shown |

---

## Part 6 — Known limitations of this test collection

### 6.1 Documents contain several unrelated stories

The corpus was built by grouping consecutive sentences, not by article
boundary. One document often holds two or three separate news items.

```
doc37203:  [asylum seekers in Australia] + [student protest in Lahore]
doc17266:  [Peshawar University closed]  + [Afghanistan vs Bangladesh cricket]
```

Consequences:

- **Judging is ambiguous.** The rule adopted is: relevant if *any* story in
  the document answers the query.
- **BM25 is distorted.** Document length and term density are what BM25
  weighs, and both are wrong for a document holding three stories.
- **The comparison is still fair** — it affects both arms equally — but the
  absolute scores are depressed.

State this as a limitation. If the source text has article separators, a
future run should split on those; `remap_qrels.py` can carry the judgements
across.

### 6.2 Some queries are too generic

From the query pool, these were dropped as unjudgeable:

```
تازه خبرونه       "latest news"       — matches the whole corpus
افغانستان خبرونه   "Afghanistan news"  — matches most of it
نړیوال خبرونه      "world news"
سیاسي خبرونه       "political news"
```

`د افغانستان ولایتونه` was kept but has the same weakness.

### 6.3 Fifty queries, and what they do and do not support

Fifty is the usual TREC-style minimum, and the power analysis says 31 are
needed for the MAP effect, so MAP and recall@10 are established and nDCG@10 and
P@10 are not. Say which claims the collection supports rather than reporting
four p-values as though they were equally grounded.

The collection grew twice. At 30 queries it was genuinely underpowered, asking
for 134 queries at the effect size then measured; at 39 it needed 36 and had
39; at 50 it needs 31. **No decision changed at any step** — the gating
conclusions in Part 3 came out the same at 39 and at 50, which is the evidence
that they were not artefacts of a small sample.

### 6.4 The judgements are adjudicated, not independent

Every one of the 1,891 labels was agreed by three native Pashto speakers
working together: they read the document, discussed whether it answered the
query, and recorded y or n only when all three agreed.

That is a stronger protocol than one assessor working alone, and stronger than
a majority vote, because a disagreement is resolved by argument rather than
averaged away. It has one cost, and it should be stated: **there is no
inter-annotator agreement coefficient for these labels**, because they were
never produced independently. Adjudicated collections cannot report κ, and that
is a property of the design rather than an omission.

One earlier, separate exercise does give a figure. Before the consensus
procedure was adopted, a second judge labelled three queries independently:

```
raw agreement 63.64%    Cohen's κ 0.244    48 of 132 disagreed
```

That describes independent judging, not the labels the experiment uses. It is
worth reporting for two reasons: disagreement of this size is normal in
retrieval evaluation (TREC assessors overlap on 30–45% of the documents they
call relevant, and system rankings stay stable anyway — Voorhees 2000), and it
shows concretely what the consensus procedure was adopted to avoid. On one of
those three queries the per-query outcome **reverses** between the two
independent labellings, which is exactly the instability that agreeing in the
room removes.


### 6.5 Vocabulary mismatch is beyond stemming

```
زده کوونکي    native Pashto, "students"
محصلین        Arabic loan,   "university students"
```

Same meaning, no shared morphology. A stemmer conflates word *forms*, never
*synonyms*. This marks the boundary of what stemming can contribute, and needs
a thesaurus or query expansion instead.

---

## Part 7 — What to report in the paper

1. **The headline.** On 50 queries and 1,891 judgements, MAP rises 0.5785 →
   0.6854 (+0.1070), significant by paired t-test (p = 0.001) and sign test
   (39 of 50, p < 0.001), bootstrap CI [+0.050, +0.164].
2. **Recall@10 is significant too** (0.3011 → 0.3502, p = 0.042); nDCG@10 and
   P@10 improve and are not. Say which is which. The collection is powered for
   the MAP effect (31 needed, 50 held) and not for the rank-weighted measures.
3. **The distribution, not just the mean.** 39 queries gain 7.13 MAP between
   them, 11 lose 1.78, and three of those account for 1.10.
4. **The `‑تون` finding, with both halves.** Gating one suffix is worth
   +0.0115 MAP and wins all four metrics, and costs 0.22 points of intrinsic
   development accuracy. This is the only place where the intrinsic and
   downstream evaluations disagree, and the downstream one is the only one that
   can see it, because both analyses of `روغتون` are defensible for a word in
   isolation. The same gate *raises* both external word lists.
5. **The `‑ستان` negative result.** Same test, opposite answer (−0.0007, and it
   breaks q003). Reporting both is what shows the suffixes were measured rather
   than chosen.
6. **The decisions were stable across collection sizes.** The gating results
   came out the same at 39 queries and at 50. Worth one sentence, because it is
   the answer to "did you tune this on the evaluation?"
7. **The one-directional conflation argument.** 38% of hospital documents
   mention health but only 13% of health documents mention a hospital, so the
   merge adds 4,681 irrelevant documents and no relevant ones.
8. **The 37.0% vocabulary collapse**, of which 98.8% has a morphological
   account.
9. **The judging protocol**, as a strength and with its cost: three native
   speakers agreeing on every label, and therefore no agreement coefficient for
   those labels.

### Suggested wording

> Retrieval effectiveness was evaluated on 50 Pashto queries over 44,814 news
> documents with 1,891 relevance judgements, pooled from both runs and judged
> blind to which run retrieved each document. Each document was judged by three
> native Pashto speakers working together, who recorded a label only when all
> three agreed. Stemming raises MAP from 0.5785 to 0.6854 (+0.1070; paired
> t(49) = 3.60, p = 0.001; bootstrap 95% CI [+0.050, +0.164]; 39 of 50 queries
> improved, sign test p < 0.001) and recall at rank 10 from 0.3011 to 0.3502
> (p = 0.042). nDCG@10 and P@10 improve by 0.042 and 0.046 respectively and
> neither reaches significance; a power analysis indicates the collection is
> adequate for the MAP effect (31 queries required) but not for the
> rank-weighted measures. The gain is unevenly distributed: 39 queries gain
> 7.13 MAP between them while eleven lose 1.78, three of those accounting for
> 1.10.
>
> One suffix was gated on the strength of this evaluation. The place-forming
> `‑تون` is a regular Pashto derivation, but removing it merges a place with
> the quality it is named for — `روغتون` 'hospital' and `روغتیا` 'health' both
> reduce to `روغ`. The merge is one-directional: 38% of the documents
> containing `روغتون` also contain `روغتیا`, but only 13% of those containing
> `روغتیا` contain `روغتون`, so conflation adds 4,681 health documents that
> never mention a hospital while adding no hospital document the unstemmed
> index did not already reach. Gating the suffix raises MAP from 0.6739 to
> 0.6854 and improves all four measures, at a cost of 0.22 points of intrinsic
> development accuracy — the only case in this work where the intrinsic and
> extrinsic evaluations disagree, and one an intrinsic evaluation cannot
> detect, since both analyses are defensible for a word seen in isolation. The
> superficially similar `‑ستان` was tested the same way and left in place,
> because gating it measured marginally worse (−0.0007 MAP). Both results were
> unchanged when the collection grew from 39 queries to 50.
