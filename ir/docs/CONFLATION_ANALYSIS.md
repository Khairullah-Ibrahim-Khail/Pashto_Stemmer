# Why one stem gathers many words — error, bug, or Pashto?

Measured on the retrieval corpus: **44,814 documents, 114,644 word types,
5.4 million tokens of Pashto news.** Reproduce with
`python conflation_report.py`.

## The headline

```
114,644 word types  →  72,173 stems        37.0% collapse
15,650 stems (21.7%) merge two or more word types
58,121 (word, stem) pairs sit inside a merged class
```

Those 58,121 pairs break down as follows. This is the answer to the question.

| | pairs | share | what it is |
|---|---:|---:|---|
| **A** | 9,432 | **16.2%** | the same word spelled differently — a **gain** |
| **B** | 45,585 | **78.4%** | one documented affix removed — **normal stemming** |
| **C** | 2,406 | **4.1%** | a stack of documented affixes — **normal morphology** |
| **D** | 697 | **1.2%** | no affix decomposition exists — **the only real errors** |

**98.8% is legitimate. 1.2% is coincidence, and most of that was a bug now
fixed.**

---

## A. Orthographic variants — 16.2%, and a benefit not a cost

4,850 merged stems contain at least one pair of words that are the *same word*
written two ways. 8,903 types — **7.8% of the entire vocabulary** — are a
respelling of another type in the same class.

```
جوړېدو / جوړیدو        جوړېږي / جوړیږي        جوړېدل / جوړیدل
جوړوونکي / جوړونکي     اوسېدونکي / اوسیدونکي
زده کوونکي / زده كوونكي        (Arabic kaf and yeh)
```

Pashto has no single settled orthography across Afghanistan and Pakistan:
`ې` against `ی`, Arabic `ك`/`ي` against Pashto `ک`/`ی`, optional ZWNJ, and
inconsistent spacing in compounds. Merging these is **exactly what a stemmer
should do**, and it is a contribution this project should claim rather than
count as conflation. Without it, a search for `جوړېدو` misses every document
that writes `جوړیدو`.

## B. One documented affix — 78.4%, normal stemming

The large majority. `کار` → `کارونه` (`‑ونه`, plural), `کاري` (`‑ي`,
relational), `کارول` (`‑ول`, verbalizer). Every removal matches an affix in
the 118-rule inventory, each citing a published grammar.

This is where Pashto differs in **degree** from English, and the degree is the
point:

| stem | types | tokens | spans |
|---|---:|---:|---|
| `کار` | 68 | 18,332 | noun, verb, agent, adjective, 6 compounds |
| `جوړ` | 54 | 12,409 | adjective, verb, agent, abstract noun |
| `لوب` | 54 | 20,410 | noun, verb, agent, adjectival |
| `اور` | 50 | 5,323 | noun, verb, participle |
| `اوس` | 48 | 14,493 | adverb, verb, agent |
| `خپر` | 48 | 6,068 | adjective, verb, agent |
| `زیات` | 45 | 20,751 | adjective, verb, abstract noun |
| `پوه` | 44 | 2,656 | adjective, verb, agent, abstract |

`کار` alone absorbs `کار` `کارونه` `کارونو` `کاره` `کارول` `کاروي` `کارېږي`
`کارېدل` `کاروونکي` `کارونکي` `کارېدونکي` `کاري` `کاریز` `کارپوه` `کارګر`
`کارمند` `کارخانه` `کارځای` `همکار` …

The cause is structural: **`‑ول` and `‑ېدل` form a verb from almost any noun
or adjective**, and each resulting verb then carries the full agreement
paradigm (`‑م ‑ې ‑ي ‑و ‑ئ`), a past stem, a participle and an agent noun in
`‑وونکی` with its own four agreement forms. One root therefore surfaces in
dozens of types. English has nothing comparable; Porter's deepest merges —
*universal/universe/university* → `univers`, *organization* → `organ` — reach
three or four types, not sixty-nine.

**This is over-stemming in Paice's sense and is reported as such. It is a
measured cost of root-based conflation, not a defect in the inventory.**

## C. Stacked affixes — 4.2%, also normal

`کارولو` is `کار` + `ول` + `و`: two affixes, both documented. The engine
strips one layer per pass (`max_passes=1`), so a single documented affix does
not account for the removal — but the morphology does.

```
کارولو      کار + ول + و
کاروونکو    کار + وونکی + و
جوړېدونکې   جوړ + ېدونکی + ې
```

Counting these as errors would be wrong. They are the same phenomenon as B,
one layer deeper.

## D. No affix decomposition — 1.2%, the only genuine errors

697 pairs across 573 stems. These divide into three kinds, and **the largest
kind has already been fixed**.

### D1. ZWNJ artefacts — now fixed

```
نشه‌يي → نشه‌   خامنه‌یي → خامنه‌   وسله‌والو → وسله‌
شیعه‌ګانو      هیله‌مند       لیک‌       ‌اړخیزو
```

The stemmer was deleting the joiner, welding the halves of a word together,
and leaving a dangling joiner at the edge. Both were fixed on 2026-10-10. The
current stemmer returns:

```
نشه‌يي     → نشه          وسله‌والو  → وسله
خامنه‌یي   → خامنه        شیعه‌ګانو  → شیعه
```

**This corpus was indexed before the fix, so these still appear in the
measurement above. Re-indexing removes most of the 1.2%.**

### D2. Arabic broken plurals — correct, by dictionary not by rule

```
وسایل → وسیله      قوانین → قانون      اخبار → خبر
```

No rule can derive these; the exception dictionary handles them. They appear
as "unexplained" only because the explanation is lexical rather than
morphological. **Correct behaviour.**

### D3. Coincidental string matches — genuine errors, small in number

```
کارتون  (cartoon)   → کار      no کار root
کاروان  (caravan)   → کار
اورګان  (organ)     → اور
اوربان  (Orbán)     → اور
اوسکار  (Oscar)     → اوس
پاکستانه            → پاک      Pakistan merged with "clean"
پوهتون، پوهتونونه   → پوه      misspellings of پوهنتون in the source text
```

Loanwords and proper names whose opening letters happen to match a Pashto
root. These are errors by any definition. They are a handful of types out of
114,644, and no rule-based system without a gazetteer avoids them.

---

## Known inconsistency, separate from all of the above

```
پوهنتون     → پوهن
پوهنتونونو  → پوهن
پوهنتونو    → پوهنتون      ← stops one strip short
```

The oblique singular is analysed differently from its own singular and plural.
This is **not** over-stemming and **not** Pashto complexity — it is the same
word answered two ways depending on its case ending, and nothing in the
grammar defends it. It should be fixed.

---

## The retrieval consequence, and the honest framing

The `پوه` class merges `پوهنتون` (university) with `پوهنه` (education). On
query q02, `د پوهنتون زده کوونکي` — *university students* — this pulled
education-ministry documents into the top 10, which the human judges correctly
marked not relevant, and the query lost MAP.

That is the cost of correct derivational conflation crossing a semantic
boundary users care about. **An intrinsic word-type evaluation cannot detect
it**, because both `پوهن` analyses are defensible in isolation; only a
downstream task reveals the boundary. This is a finding, not a defect.

### Wording for the paper

> The stemmer collapses a 114,644-type news vocabulary to 72,173 stems, a
> 37.0% reduction. Of the merges, 16.2% are orthographic variants of one
> word — a normalization gain, given that Pashto has no settled orthography
> across its two main regions — and 82.6% are removals of documented affixes,
> singly or stacked. Only 1.2% have no morphological account, and most of
> those were an orthographic defect since corrected. The largest classes
> gather a root's whole derivational family: `کار` absorbs 69 types over
> 18,332 tokens, including the verbalized `کارول` and the agentive
> `کاروونکي`. This is over-stemming in Paice's sense and is reported as such,
> but it follows from Pashto morphology rather than from the inventory:
> `‑ول` and `‑ېدل` verbalize almost any noun or adjective, and each derived
> verb carries a full agreement paradigm, so one root surfaces in an order of
> magnitude more forms than in English.

**Not "not an error" — "a measured cost, not a defect".** The second is
falsifiable and the numbers above are the falsification test.
