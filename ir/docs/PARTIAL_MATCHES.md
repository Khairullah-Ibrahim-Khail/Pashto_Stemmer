# Why the search returns documents that match only part of the query

Three questions answered here:

1. Why does a document come back when it only contains *some* of my words?
2. Is that good or bad?
3. A query returns thousands of documents — should I limit it?

---

## 1. Why it happens

### The search engine does not require all your words

BM25 **adds up** a score per word. It does not demand that every word be
present.

Query `د ښځو د حقوقو قانون` — *women's rights law* — has three content words.
A document matching two of them still gets a score:

```
document A    ښځو ✅   حقوقو ✅   قانون ❌    →  high score
document B    ښځو ❌   حقوقو ✅   قانون ✅    →  high score
```

Both appear in the results. They are not equally useful.

### A worked example from this experiment

Query: `د ښځو د حقوقو قانون`

| document | `ښځو` | `حقوقو` | `قانون` | judged |
|---|---|---|---|---|
| UN demanding the Taliban lift restrictions on **women** | ✅ | ✅ | ❌ | **relevant** |
| US law on police use of lethal force | ❌ | ✅ | ✅ | **not relevant** |

**Both matched two of three words. Opposite verdicts.** The difference is
*which* word was missing.

`ښځو` (women) is the **discriminating word** — it makes this query about
women's rights rather than about law in general. `قانون` is not: the subject
can be women's rights without the word *law* appearing anywhere.

### The stemmer widens this

Without the stemmer, a word matches only itself. With it, a word matches its
whole family:

```
query word  کورونه   →  کور    matches کور، کورونه، کورونو، کورې
query word  روغتون   →  روغ    matches روغتون، روغتیا، روغول، روغ، روغېدل
```

The first is what you want. The second is too wide — `روغتیا` (health) is not
`روغتون` (hospital).

---

## 2. Is it good or bad?

### It is good — this is the whole purpose

Pashto changes the ending of a word depending on its role in the sentence. The
same word appears in many shapes:

```
کور        a house
کورونه     houses
کورونو     of/to the houses
کورته      to the house
```

A person searching `کورونه` wants documents about houses. Without stemming,
documents that say only `کور` are invisible to them. **Partial and
family-based matching is not a bug — it is why stemming exists.**

Measured on this collection, stemming raised recall at 10 from **0.3017 to
0.3115** — it found relevant documents the exact-match search missed
entirely. On `q110` the unstemmed search found **nothing** in its top 10
(P@10 = 0.000) and the stemmed search found six.

### It is bad when the family is too big

The danger is **over-stemming** — cutting so deep that unrelated words land on
the same stem.

```
GOOD                              BAD
کورونه  → کور                     روغتون  → روغ
کور     → کور                     روغتیا  → روغ
         same word, two forms              hospital vs health:
                                           two different words
```

Measured across the whole corpus:

```
114,644 word types → 72,173 stems     37.0% collapse
98.8% of merges are legitimate
 1.2% are coincidence
```

So the behaviour is right **98.8%** of the time. The remaining 1.2% is what
causes the occasional bad query.

---

## 3. How to rate it

Do not ask "did it return documents with only some words". Ask the four
measures below. Each answers a different question.

### P@10 — are the top 10 any good?

```
of the top 10 results, how many did a human call relevant?

P@10 = 0.70   →  7 of the top 10 are useful
```

Use this when the user only looks at the first screen. **This is the number to
quote to a non-specialist.**

### Recall@10 — did it find what exists?

```
of ALL relevant documents, how many made the top 10?

Recall@10 = 0.31   →  31% of the relevant documents are in the top 10
```

Low numbers are normal here: a query with 40 relevant documents cannot fit
them into 10 slots. **This is where stemming helps most**, because it finds
documents the exact search cannot see.

### MAP — are the good ones near the top?

```
relevant at positions 1, 2, 3   →  MAP high
relevant at positions 8, 9, 10  →  MAP low
```

Both have the same P@10. MAP separates them. **This is the standard measure
for comparing two systems.**

### nDCG@10 — the same, weighted by position

Position 1 counts more than position 10. Use it alongside MAP; if the two
disagree, say so rather than picking the flattering one.

### How to tell whether a change is real

One number is not evidence. Three checks:

```bash
$PY per_query.py
```

| check | what it tells you |
|---|---|
| **per-query table** | does it help most queries, or just one by a lot? |
| **sign test** | do more queries improve than worsen? |
| **paired t-test** | is the average difference bigger than the noise? |
| **bootstrap CI** | if the range includes 0, you cannot claim a difference |

In the earlier 30-query version of this experiment the two tests disagreed:
the mean was +0.0574 MAP with **p = 0.196 — not significant** — while the sign
test was significant (21 of 30 improved, p = 0.043). **Report both**, because
the disagreement is itself informative: stemming helps many queries a little
and hurts a few a lot, which is exactly the shape a t-test handles badly.

On the final 50 queries both tests agree for MAP (+0.1070, t-test p = 0.001,
sign test p < 0.001); recall@10 is significant under the t-test (p = 0.042) and
nDCG@10 and P@10 are not. So the rule still holds — report both, and say which claims the
collection can actually support.

---

## 4. How to fix it when it is bad

In order of cost. Try them in this order.

### Fix 1 — gate the one suffix causing the damage

Find the query that lost:

```bash
$PY inspect_query.py q110
```

Look at the query words before and after stemming. If one got much shorter,
that is your cause:

```
روغتون · درملنه   →   روغ · درمل
      ↑ hospital became "healthy"
```

Then switch that suffix off and re-measure:

```bash
$PY test_gating.py
```

**Result here:** gating `‑تون` raised MAP from 0.6739 to **0.6854** and
improved all four measures, costing 0.22 points of intrinsic word-type
accuracy.

**Always measure before and after.** Gating `‑ستان` looked like the same kind
of fix and produced **−0.0010** — it recovered one query and broke another.

### Fix 2 — accept it and document it

Some cases cannot be fixed by rule:

```
افغانستان  (the country)  →  افغان
افغانۍ     (the money)    →  افغان
افغانان    (the people)   →  افغان
```

Telling these apart needs a list of names, which a rule-based system does not
have. Write it down as a limitation rather than inventing a rule that breaks
other queries.

### Fix 3 — fix the query, not the stemmer

Some queries are too general for the corpus:

```
تازه خبرونه        "latest news"      — matches the whole corpus
د افغانستان ولایتونه                   — both words are in most documents
```

No stemmer setting helps. Either drop the query or make it specific.

### Fix 4 — require the discriminating word

Not implemented here, but the standard remedy: weight the rare query word
higher, or require it to be present. BM25 already favours rare words through
`idf`, but it will not *insist* on one.

---

## 5. "My query returns thousands of documents — should I limit it?"

**No. Returning many documents is not a problem. The order is what matters.**

### Why limiting is the wrong instinct

```
44,814 documents in the corpus
 1,000 retrieved per query          ← the engine's cut-off
    10 scored                       ← what the measures look at
    25 per index put in the pool    ← what a human judges
```

A search engine is a **ranking** machine, not a filter. Google returns
millions of results; nobody minds, because the first page is good. Your
measures only look at the top 10 for exactly this reason.

So the question is never "how many came back". It is **"are the top 10
right"** — and that is `P@10`.

### What the settings actually mean

In `config.py`:

```python
TOP_K        = 1000   # how deep the engine retrieves
EVAL_K       = 10     # how deep the measures look
POOL_PER_RUN = 25     # how many each index contributes for judging
```

**Do not lower `TOP_K` to "reduce results".** It would only hide documents
from `MAP`, which reads the full ranking, and make your numbers look better
without the search improving at all.

### When a large result set *is* telling you something

If a query returns thousands of documents **and the top 10 are bad**, the
problem is the query, not the count:

```
تازه خبرونه   "latest news"   →  every news document matches
```

There is no information need there — nothing to rank *against*. Fix the query.

### What to do instead of limiting

| situation | what to do |
|---|---|
| thousands returned, top 10 good | **nothing**. Working as intended. |
| thousands returned, top 10 bad | the query is too generic — rewrite or drop it |
| few returned, all good | fine, but check `Recall@10` — are you missing some? |
| few returned, all bad | the discriminating word is being over-stemmed. Fix 1. |

### One real adjustment you could make

Raise the judging depth, not the retrieval depth:

```python
POOL_PER_RUN = 50     # was 25
```

This judges more documents per query, which makes `Recall@10` more accurate —
because its denominator ("all relevant documents") is only ever as complete as
the pool you judged. It costs more of your reading time and nothing else.

---

## 6. Summary

| question | answer |
|---|---|
| Why do partial matches come back? | BM25 adds up per-word scores; it never requires all words |
| Is that good? | **Yes** — it is the purpose of stemming, and 98.8% of merges are legitimate |
| When is it bad? | when two different words share a stem: `روغتون` / `روغتیا` |
| How do I rate it? | P@10, Recall@10, MAP, nDCG@10 — plus the per-query table, sign test and bootstrap |
| How do I fix it? | diagnose with `inspect_query.py`, gate the suffix, re-measure with `test_gating.py` |
| Too many results? | not a problem. Only the top 10 are scored. Never lower `TOP_K` to flatter the numbers |
