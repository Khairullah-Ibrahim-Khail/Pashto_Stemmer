# Pashto Stemming — Gold-Standard Annotation Policy (v1)

**Purpose.** A single, fixed definition of what a *stem* is, so every annotator
produces the same answer. Written for **standard/academic Pashto**.

On the development set, the two released annotation passes agree on 96.88% of
types (Cohen's κ 0.969) under this policy. Run `python experiments/agreement.py`
to recompute it.

---

## 1. Scope

- **Target language:** standard/academic Pashto (Pashto Academy orthography).
  **Dialectal variants are out of scope** — do not add dialect forms or rules.
- **Task = STEMMING:** remove **Pashto affixes** from a surface form.
  - It is **not** Arabic root extraction.
  - It is **not** general lemmatization (one deliberate exception: verbs, §5).
- A stem **need not be a meaningful standalone word**, but it **must be
  reachable from the surface form by removing/adjusting Pashto affixes**.

## 2. Orthography & normalization

- **Preserve the original form.** The original surface word is always kept; the
  stem is recorded *alongside* it, never overwriting it.
- **Normalization = standardization**, never merging distinct words:
  - `ك` → `ک`; `ة`/`ۀ` → `ه`; Urdu `ٹ ڈ ڑ ے` and Persian `گ` → their Pashto
    counterparts; remove diacritics, tatweel, ZWNJ.
- **No yeh letter is ever rewritten.** `ی ي ې ۍ ئ` all survive normalization
  untouched — verified on every cell of both evaluation sets. They are distinct
  standard Pashto letters carrying gender, number and person.
- Rule *matching* folds the five together so that a rule written with `ی` also
  fires on `ي`, but the letters written out are never altered.

## 3. Nouns and adjectives — remove inflection (always)

| Category | Affixes | Example |
|---|---|---|
| Plural | ‑ونه، ‑ان، ‑ګان | کورونه → کور |
| Oblique / case | ‑ونو، ‑انو، ‑ګانو، ‑و | کورونو → کور |
| Feminine / plural | ‑ې، ‑ۍ (when inflectional) | سیمې → سیم |
| Adjective agreement | ‑ه، ‑ې، ‑و | لنډه → لنډ |

**No letter is added back.** Stemming removes material; it does not restore a
base form. `خبرو → خبر`، `سیمو → سیم`، `چارو → چار` — not `خبره`، `سیمه`،
`چاره`. An earlier draft of this policy called for restoration; the released
reference does not do it, and the stemmer does not either.

## 4. Derivation — remove *productive* Pashto derivational suffixes

`‑توب، ‑تیا، ‑والی/‑والۍ، ‑ونکی، ‑ګر، ‑وال، ‑وان، ‑ي (nisba)، ‑یز`

Examples: `هوښیارۍ → هوښیار`، `ځیرکتیا → ځیرک`، `پوځي → پوځ`،
`سیاستوال → سیاست`.
**Stop at the Pashto stem** — do not continue into an Arabic root.

## 5. Verbs — keep the infinitive; strip what is attached to it

- Perfective prefix and inflection come off, the infinitive stays:
  `ووېشل → وېشل`، `کولو → کول`، `ساتلو → ساتل`
- The infinitive itself is **not** reduced further: `لوستل → لوستل`,
  not `لوست`.
- Verbalizers are a separate matter and do come off (§4), because there the
  whole `‑ېدل`/`‑ول` pattern is the affix on a noun or adjective:
  `کارول → کار`، `جوړېدل → جوړ`، `زیاتوی → زیات`
- Suppletive forms (`ځي`, `لاړ`, `غواړي`, `وینم`, `شول`) map to the
  infinitive — `تلل`، `غوښتل`، `لیدل`، `کېدل` — which is a **lemma**, not a
  stem, and therefore belongs to the lemmatization mode, not to stemming (§1).

**Why.** Across the released reference, no word ending in `‑ل` has that `‑ل`
removed: of 124 such words, 80 are left exactly as they are and the rest lose
only a prefix or an inflectional ending. Stripping the bare `‑ل` was tried and
removed from the system, because it only ever fired on nouns where `ل` belongs
to the root (`کابل → کاب`, `لامل → لام`). The rules `‑لو` and `‑لې` were gated
for the same reason: they take an `ل` the reference keeps.

> Revision note: two earlier drafts of this section said the opposite — one
> targeted the infinitive, a later one the bare stem. Neither matched the data.
> This version was checked against all 124 `‑ل` words in the released
> reference.

**Implementation.** Suppletion cannot be derived by any rule (`ځي` and `تلل`
share no material), so a lexicon is linguistically *required*, not a shortcut.
Irregular verbs are stored as a **paradigm table** —
`lemma | present stem | past stem` (e.g. `تلل | ځ‑ | لاړ/تل‑`,
`اخیستل | اخل‑ | اخیست‑`, `کول | کو‑ | کړ‑`) — with the regular agreement
endings (‑م، ‑ې، ‑ي، ‑و، ‑ئ) applied by rule on top, rather than a flat list of
surface forms. That table produces lemmas, so it is off by default and is
offered as an explicit lemmatization mode.

## 6. Loanwords (Arabic / Persian)

- Strip **only the Pashto affixes** attached to them: `مصنوعي → مصنوع`.
- **No Arabic templatic root extraction:** ✗ `مصنوعي → صنع`، ✗ `جریمه → جریم`.
- **Arabic broken plurals are handled as lexical exceptions**, exactly like
  native Pashto irregular plurals (`کلونو → کال`، `نجونو → نجلۍ`):
  `اثار → اثر`، `مطالب → مطالب` (a broken plural: a lemma, not a stem)، `علوم → علم`.

  They are **listed in an exception lexicon, never guessed by pattern.**
  Rationale: Pashto text is unvowelled, so Arabic templates (فِعال، أفعال،
  فُعُول…) are ambiguous and would misfire on native Pashto words. A bounded,
  curated list gives precision with no false positives.

  This stays consistent with §10: exceptions are **declared lexically**, never
  inferred — which is why `اثار → اثر` is allowed while `مصنوعي → صنع` is not.

## 7. Proper nouns — treated like any other word (revised)

Proper nouns receive **no special treatment**: the ordinary affix rules apply,
so `افغانستان → افغان`, `طالبان → طالب`.

**Rationale (author's ruling).** An earlier draft froze proper nouns against a
hand-written list. That was dropped because such a list can never be complete:
with ~80 names listed and thousands in the language, the system would freeze
the names we happened to include and strip every unseen one — inconsistent
behaviour that is impossible to defend. A rule-based stemmer has no context
model with which to recognise a name, so it applies the same rules to every
word, and a stem that is not a meaningful word is acceptable output for a
stemmer.

**Known cost, accepted:** `پاکستان → پاک` merges the country with the unrelated
word پاک. Measured impact of removing the freeze: −0.8 accuracy, and
conflation slightly *better* (UI 0.240 → 0.237).

## 8. Compounds — keep lexicalized compounds whole

`مرګژوبله`، `سرچینه`، `لوبغاړی` are single lexical items. Strip only the outer
inflection (`لوبغاړي → لوبغاړی`); **do not split** them into components.
✗ `سرچینه → سرچین` (the prefix ‑سر is kept)، ✗ `مرګژوبله → مرګژوبل` (compounds stay whole).

## 9. Function words — unchanged

Postpositions, pronouns, conjunctions, particles: `په، له، چې، دې، کښې، او`.

## 10. Tie-break rule (use when unsure)

> If a proposed stem **cannot be reached** from the surface form by removing or
> adjusting Pashto affixes, it is a **lemma or a root — not a stem**. Reject it.

This single rule resolves most disagreements (e.g. rejects `صنع`, `جرم`, `لدره`,
`کښل`, and `جر`).

---

## Annotation workflow

1. Apply §§2–9 in order; use §10 when unsure.
2. Record: `word` (original), `stem`, `pos`, `is_irregular`, `is_compound`, `notes`.
3. Leave `notes` for anything debatable rather than guessing silently.
4. A portion of the gold is held out and never used for tuning the system.

**Version:** v1.2 — decisions in force:
- **§5 verbs → STEM** (infinitive minus ‑ل), implemented as a paradigm table
  (lemma / present stem / past stem) grounded in descriptive grammars.
  *(Supersedes the v1.0 draft, which wrongly targeted the infinitive.)*
- **§6 Arabic broken plurals** handled as a **lexical exception dictionary**;
  templatic derivation was tested and measured at 40% precision, so rejected.
- **§7 proper nouns are NOT frozen** — rules apply to every word, because a
  hand-written name list can never cover unseen names.
- **§8** lexicalized compounds kept whole.
- Short-word rule: nothing is removed from a word of **3 characters or fewer**.
