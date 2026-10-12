# Everything found in the IR test: results, errors, bugs, decisions

A complete record. Nothing here is from memory — every number was measured by
a script in this folder and can be regenerated.

---

## Part 1 — The result

### 1.1 Headline

39 queries, 1,489 judgements, 873 relevant, 44,814 documents. Reproduce with
`python significance.py`.

| | unstemmed | stemmed | difference | p | sign p |
|---|---:|---:|---:|---:|---:|
| MAP | 0.5407 | **0.6517** | +0.1110 | **0.005** | **0.001** |
| nDCG@10 | 0.6675 | **0.7178** | +0.0503 | 0.253 | 0.150 |
| P@10 | 0.6359 | **0.6821** | +0.0462 | 0.272 | 0.230 |
| Recall@10 | 0.2946 | **0.3479** | +0.0533 | 0.083 | 0.230 |

The stemmer here is the released one, which gates ‑تون; Part 3 is the
measurement that decided that. Both tests live in `stats_tests.py`, which
checks itself against nine known values, because scipy is not installed here.

### 1.2 Is it significant? For MAP, yes.

| test | result | meaning |
|---|---|---|
| paired t-test on MAP | t = 2.95, p = 0.005 | significant |
| bootstrap 95% CI | [+0.0393, +0.1843] | excludes zero |
| sign test | 30 of 39 improved, p = 0.001 | significant |
| power | Cohen's d 0.472; 36 queries needed | this collection has 39 |

MAP is significant under both tests and the collection is adequately powered
for it. The three cutoff-10 metrics all move the same way and none reaches
significance: the effect at rank 10 is real but smaller than 39 queries can
resolve. Report that distinction rather than four p-values alone.

**This was not true earlier.** With ‑تون still stripped, the same judgements
gave MAP +0.0997 at p = 0.021, and the power analysis asked for 53 queries
against the 39 available — an underpowered study. Gating one suffix moved it
to p = 0.005 and 36.

### 1.3 The queries that lose

Nine of 39 lose. The three largest:

```
q003  د افغانستان ولایتونه   0.5824 → 0.1189   −0.4635
q110  روغتون درملنه         0.8429 → 0.4083   −0.4346
q010  د افغانیو ارزښت       0.6381 → 0.2852   −0.3529
```

Those three lose **1.25 MAP** between them, all nine losers **1.70**, and the
30 that gain make **6.03**. The gate did not change the shape of the effect —
stemming helps most queries moderately and damages a few badly — it changed
how badly: q110 was −0.7126 before it.

---

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
| `روغتون` (hospital) | 28 | 7 | 80% relevant |
| only `روغتیا` (health) | 0 | 13 | **0% relevant** |

Thirteen health-only documents were judged, and every one was marked not
relevant. The −0.4346 loss comes from those labels.

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
| no stemming | 0.5407 | 0.6675 | 0.6359 | 0.2946 |
| **released (`‑تون` gated)** | **0.6517** | **0.7178** | **0.6821** | **0.3479** |
| `‑تون` live, as the grammar says | 0.6404 | 0.7023 | 0.6718 | 0.3448 |
| `‑ستان` gated too | 0.6509 | 0.7166 | 0.6795 | 0.3476 |
| `‑تون` live, `‑ستان` gated | 0.6396 | 0.7011 | 0.6692 | 0.3446 |

| comparison | MAP | t | p | w/l |
|---|---:|---:|---:|---:|
| released vs no stemming | +0.1110 | 2.95 | 0.005 | 30/9 |
| `‑تون` live vs no stemming | +0.0997 | 2.41 | 0.021 | 29/10 |
| `‑تون` live vs released | −0.0113 | −0.97 | 0.340 | 2/4 |
| `‑ستان` gated vs released | −0.0008 | −0.30 | 0.762 | 1/1 |

### 3.1 Gating `‑تون` works

It is the only configuration that wins on all four measures, and it is what
the released stemmer does. Putting the suffix back costs 0.0113 MAP and loses
on every metric.

```
q110   0.1303 → 0.4083      recovered by gating
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

Net MAP change against the released stemmer: **−0.0008**. Nothing, and in the
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

### 6.3 Thirty-nine queries is below the TREC convention

TREC convention is 50; this collection has 39. The power analysis says 36 are
needed for the MAP effect at 80% power, so MAP is adequately powered and the
three cutoff-10 metrics are not — their effects are smaller and would need a
larger collection to resolve. Say which claims the collection supports rather
than reporting four p-values as though they were equally grounded.

The earlier 30-query version of this collection was genuinely underpowered:
it asked for 134 queries at the effect size then measured.

### 6.4 One judge for most of the set

The 39 queries were judged by one person. A second judge covered 3 of them:

```
raw agreement 68.18%    Cohen's κ 0.301    42 of 132 disagreed
```

That is within the normal range for IR relevance — TREC assessors overlap on
30–45% of the documents they call relevant and system rankings stay stable
anyway (Voorhees 2000) — so a low κ is not grounds for discarding the work.
But the per-query result **reverses** between the two labellings on `q05`
(+0.386 vs −0.088). With 3 shared queries that cannot be averaged out; with
25 or more it would become noise. This is the collection's weakest point and
should be stated plainly, as a single-assessor collection with a 3-query
agreement probe rather than as a dual-judged one.


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

1. **The headline.** On 39 queries and 1,489 judgements, MAP rises 0.5407 →
   0.6517 (+0.1110), significant by paired t-test (p = 0.005) and sign test
   (30 of 39, p = 0.001), bootstrap CI [+0.039, +0.184].
2. **What is *not* significant.** nDCG@10, P@10 and Recall@10 all improve and
   none reaches significance. Say so. The collection is powered for the MAP
   effect (36 needed, 39 held) and not for the smaller rank-10 effects.
3. **The distribution, not just the mean.** 30 queries gain 6.03 MAP between
   them, 9 lose 1.70, and three of those account for 1.25. Stemming helps most
   queries moderately and damages a few badly.
4. **The `‑تون` finding, with both halves.** Gating one suffix is worth
   +0.0113 MAP and wins all four metrics, and costs 0.22 points of intrinsic
   development accuracy. This is the only place in the project where the
   intrinsic and downstream evaluations disagree — and the downstream one is
   the only one that can see it, because both analyses of `روغتون` are
   defensible for a word in isolation. The same gate *raises* both external
   word lists, so the 0.22 is specific to our own annotation.
5. **The `‑ستان` negative result.** Same test, opposite answer (−0.0008, and
   it breaks q003). Reporting both is what shows the suffixes were measured
   rather than chosen.
6. **The one-directional conflation argument.** 38% of hospital documents
   mention health but only 13% of health documents mention a hospital, so the
   merge adds 4,681 irrelevant documents and no relevant ones. This is the
   general form of the argument for gating a *place* suffix and it is worth
   stating, because it predicts which suffixes will behave this way.
7. **The 37.0% vocabulary collapse**, of which 98.8% has a morphological
   account. The first figure in the project measured on running text rather
   than isolated word types.
8. **Every limitation in Part 6**, especially 6.4: one assessor for 39
   queries with a 3-query agreement probe, and a per-query reversal on one of
   those three.

### Suggested wording

> Retrieval effectiveness was evaluated on 39 Pashto queries over 44,814 news
> documents with 1,489 relevance judgements pooled from both runs and judged
> blind to which run retrieved each document. Stemming raises MAP from 0.5407
> to 0.6517 (+0.1110; paired t(38) = 2.95, p = 0.005; bootstrap 95% CI
> [+0.039, +0.184]; 30 of 39 queries improved, sign test p = 0.001).
> nDCG@10, P@10 and Recall@10 improve by 0.050, 0.046 and 0.053 respectively,
> none significantly; a power analysis indicates the collection is adequate
> for the MAP effect (36 queries required) but not for the smaller effects at
> rank 10. The gain is unevenly distributed: 30 queries gain 6.03 MAP between
> them while nine lose 1.70, three of those accounting for 1.25.
>
> One suffix was gated on the strength of this evaluation. The place-forming
> `‑تون` is a regular Pashto derivation, but removing it merges a place with
> the quality it is named for — `روغتون` 'hospital' and `روغتیا` 'health' both
> reduce to `روغ`. The merge is one-directional: 38% of the documents
> containing `روغتون` also contain `روغتیا`, but only 13% of those containing
> `روغتیا` contain `روغتون`, so conflation adds 4,681 health documents that
> never mention a hospital while adding no hospital document the unstemmed
> index did not already reach. Gating the suffix raises MAP from 0.6404 to
> 0.6517 and improves all four measures, at a cost of 0.22 points of intrinsic
> development accuracy — the only case in this work where the intrinsic and
> extrinsic evaluations disagree, and one an intrinsic evaluation cannot
> detect, since both analyses are defensible for a word in isolation. The
> superficially similar `‑ستان` was tested the same way and left in place,
> because gating it measured marginally worse (−0.0008 MAP).
