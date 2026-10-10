# Pashto Affix Inventory — پښتو تړلي مورفیمونه (Revised)

> **This document is the survey, not the rule list.** It records how the
> affixes of Pashto were gathered and what is known about each one. The rules
> the stemmer actually applies live in `pashto_stemmer/suffixes.py` and
> `prefixes.py`, and are printed in full in Appendix A of the paper and in
> `paper/inventory_rows.tsv`, which is generated from them. The two have
> diverged: 23 of the 118 affixes in the code are not mentioned anywhere in
> the sections below, mostly case and gender variants added during error
> analysis. Some forms discussed here are handled outside the rule table
> altogether (the agent
> ending ‑غاړی through a configuration list, the directional prefixes را‑, در‑,
> ور‑ not at all, having been measured and removed). Where the two disagree,
> the code is what runs.

> **Research note:** This is a structured working inventory for Pashto NLP/morphology. It separates derivational, inflectional, verbal, and stem-internal morphology. Pashto has dialectal variation, allomorphy, irregular verbs, and forms that can function as particles as well as affix-like elements. Therefore, an affix must not be stripped solely because its character sequence appears at the beginning or end of a word.
>
> **Revision note:** This version adds missing productive affixes, corrects directional-prefix meanings and several wrong examples, reclassifies compounds and particles, and adds orthographic normalization and tokenization rules. Entries marked **confidence: low** or **needs validation** must be checked against attested sources before they are used in stemming rules.

**Productivity labels used below:** `productive` · `restricted` · `lexicalized` · `borrowed` (Persian/Arabic/Turkic origin)

---

## 1. Prefixes — پېشواندونه

### 1.1 Derivational prefixes

| Prefix | Main function | Example | Gloss | Productivity | Notes |
|---|---|---|---|---|---|
| نا- | negation/opposition | ناپوه، ناوړه | ignorant, improper | productive | |
| بې- | absence/lack | بې‌کوره، بې‌وسه | homeless, helpless | productive | Adjectives often take **-ه** (see §8.5) |
| بیا- | repetition/again | بیاجوړول | rebuild | productive | Also verbal (§1.2) |
| هم- | co-/same/together | همزولی | same-aged | productive | |
| غیر- | non-/un- | غیررسمي | unofficial | borrowed | Arabic |
| لا- | without/not | لاانتها | endless | borrowed, restricted | Arabic learned formations |
| بلا- | without | بلاشرطه | unconditional | borrowed, restricted | Arabic |
| نیم- | half | نیمګړی | incomplete | restricted | |
| سر- | head/chief | سرمنشي | secretary-general | restricted | |
| ضد- | anti- | ضد انقلاب | counter-revolution | borrowed | Often written separately |

> **Removed from prefix list:** ګڼ- and دوه- (ګڼ اړخیز، دوه اړخیز) are compounds of a quantifier/numeral + stem + **-یز**, not prefixes. Record them as compounds.

### 1.2 Verbal, directional, and aspectual prefixes/particles

| Form | Main function | Example | Note |
|---|---|---|---|
| و- | perfective | وویل، ولیکل | Clitics can intervene: **و یې لیکل** (§11) |
| وا- | perfective (separable) | واخیستل، واورېدل | Verb-specific |
| کې- / کښې- | perfective (separable) | کېښودل، کښېناستل | Verb-specific; spelling varies by dialect |
| پرې- | perfective / "off, down" | پرېښودل، پرېوتل | Construction-dependent |
| را- | toward **1st person** (me/us) | راتلل، راکول | Pronominal-directional |
| در- | toward **2nd person** (you) | درتلل، درکول | Does **not** mean "inward" |
| ور- | toward **3rd person** (him/her/them) | ورتلل، ورکول | Pronominal-directional |
| بیا- | repetition | بیاکول | Can also be lexical/derivational |
| مه | negative imperative | مه کوه | Separate particle, not a prefix |
| نه | verbal negation | نه کوم | Separate particle; can also split و- from stem (و نه لیکل) |

---

## 2. Suffixes — وروستاړي

### 2.1 Abstract/state noun-forming suffixes

| Suffix | Function | Example | Gloss | Productivity | Notes |
|---|---|---|---|---|---|
| -توب | state/quality | ملګرتوب، سړیتوب | friendship, humanity | productive | |
| -تیا | state/quality | وړتیا، روغتیا | ability, health | productive | |
| -والی | state/quality | ښه‌والی، لوړوالی | goodness, height | productive | Spacing/ZWNJ varies |
| -ا | abstract from adjective | ښکلا | beauty | restricted | ښکلی → ښکلا |
| -ي | abstract noun | ازادي، بېکاري، ډاکټري | freedom, unemployment | productive | Homograph with adjectival/plural -ي |
| -ګلوي | relationship/state | ورورګلوي | brotherhood | restricted | |
| -یت | abstract | امنیت، انسانیت | security, humanity | borrowed | Arabic |
| -ولي | relationship/state | — | — | **needs validation** | Earlier example خپلولي not standard; standard word is خپلوي |

> **Removed:** -واکي. خپلواکي = خپل + واک + **-ي** (compound + abstract -ي), not a separate suffix.

### 2.2 Action/result noun-forming suffixes

| Suffix | Function | Example | Gloss | Productivity |
|---|---|---|---|---|
| -نه | action/result | ښوونه، پالنه | teaching, care | productive |
| -ون | action/result | بدلون، ژوندون | change, life | productive |
| -ګ | action (from verbs) | تګ، راتګ، پرمختګ | going, coming, progress | productive |
| -ښت | action/state | خوځښت، کمښت | movement, shortage | productive |
| -ښنه | action | بخښنه | forgiveness | restricted |
| -اک | action/product | خوراک، څښاک، پوښاک | food, drink, clothing | restricted |
| -اوی | action/abstract | پوهاوی، سپکاوی | awareness, insult | restricted |

> **Note:** Infinitive **-ل** (کول) is also used as a verbal noun. It is listed once, in §6.4, with `subtype: infinitive/verbal noun`, to avoid double rule firing.

### 2.3 Place/institution/container suffixes

| Suffix | Function | Example | Gloss | Productivity | Notes |
|---|---|---|---|---|---|
| -تون | place/institution | روغتون، پوهنتون | hospital, university | productive | |
| -ځی | place | ښوونځی | school | restricted | |
| -ځای | place | عبادتځای | place of worship | productive | Also a free noun (ځای) |
| -ستان | land/place | افغانستان، ګلستان | Afghanistan, flower garden | borrowed | Persian |
| -خانه | house/place | کتابخانه، چایخانه | library, teahouse | borrowed | Persian |
| -زار | place of abundance | ګلزار، سبزه‌زار | flower garden, meadow | borrowed, restricted | Persian |
| -دان / -داني | container | ګلدان، قلمداني، شمعداني | vase, pen-case, candlestick | borrowed, restricted | Persian |
| -غالی | place | لوبغالی | stadium, playground | lexicalized | **Confidence: low.** Only one attested example. Do not strip. Contrast with -غاړی (لوبغاړی). Do not confuse with the noun غالۍ (carpet). |

### 2.4 Agent/occupation/person-forming suffixes

| Suffix | Function | Example | Gloss | Productivity | Notes |
|---|---|---|---|---|---|
| -ونکی / -ونکې / -ونکي | agent / active participle | ښوونکی، لیکوونکی، زده کوونکی | teacher, writer, student | productive | Inflects for gender/number |
| -ګر | agent/occupation | کارګر، سوداګر | worker, trader | productive | |
| -وال | person associated with | کلیوال، لیکوال | villager, writer | productive | |
| -غاړی / -غاړې / -غاړي | agent/performer | سندرغاړی، لوبغاړی | singer, player | productive | |
| -پال | keeper/supporter | وطنپال | patriot | productive | **Dual function:** noun (§2.4) and adjective (§3). One lexicon entry with two output categories. |
| -کار | agent/doer | ګناهکار | sinner | borrowed | Earlier example سوداګر was wrong (that is -ګر) |
| -ګار | agent/doer | خدمتګار | servant | borrowed | Distinct from -کار |
| -بان | keeper/guard | دربان، باغبان | gatekeeper, gardener | borrowed | Persian. Split from -وان. |
| -وان | person/agent | — | — | **needs validation** | Earlier example دربان belonged to -بان |
| -خور | consumer/taker | رشوتخور، غوښه‌خور | bribe-taker, carnivore | borrowed | Semi-compound; not "-خوره" |
| -پوه | expert in | ژبپوه، تاریخپوه | linguist, historian | productive | Compound-like; پوه is also a free adjective |
| -چي | occupation | موچي | shoemaker | borrowed (Turkic), lexicalized | Do not strip |

> **Removed:** -پالنه. It is **-پال + -نه** (two layers), e.g., وطنپالنه = وطن + پال + نه. Model it with `derivation_order` (§10).

---

## 3. Adjective-forming suffixes — صفت جوړوونکي وروستاړي

| Suffix | Function | Example | Gloss | Productivity | Notes |
|---|---|---|---|---|---|
| -ي | relational/nisba | افغاني، کابلي، کلیوالي | Afghan, Kabuli, rural | productive | Homograph with plural and abstract -ي |
| -نی / -نۍ / -ني | relational | کورنی، ورځنی، لومړنی | domestic, daily, primary | productive | Inflects for gender/number |
| -یز / -یزه | characterized by/related to | هېوادیز، ټولنیز، ټولنیزه | national, social | productive | -یزه is the feminine form |
| -انه | manner, "-like/-ly" | ماشومانه، زړورانه، دوستانه | childish, bravely, friendly | productive | Also adverbial |
| -من | possessing | عقلمن، ارزښتمن | intelligent, valuable | productive | |
| -جن | characterized by | زهرجن | poisonous | restricted | |
| -ور | possessing/endowed with | زړور، هنرور | brave, skilled | restricted | |
| -ناک | full of/inducing | خطرناک، دردناک | dangerous, painful | borrowed | Persian |
| -ین | made of | زرین | golden | borrowed, restricted | Persian |
| -لی / -لې / -لي | past participle as adjective | لیکلی، پوخ شوی | written, cooked | productive | See §6.3 |
| -پال | supporting/cherishing | وطنپال | patriotic | productive | Same entry as §2.4 |

> **Comparison:** Native Pashto comparison is analytic (تر ... ښه، تر ټولو ښه). There is no native comparative suffix. Persian **-تر / -ترین** appear only in loans (بهتر) and should be handled lexically.

---

## 4. Diminutive/evaluative morphology — کوچني/عاطفي جوړښتونه

| Form | Function | Example | Productivity | Notes |
|---|---|---|---|---|
| -ګی / -ګۍ | diminutive | کتابګی | restricted | **Confidence: medium.** Validate with attested examples. |
| -ګوټی / -کوټی | diminutive | — | restricted | **Needs validation.** Not an adjective-forming suffix. |
| -وکی | diminutive | وړوکی | lexicalized | Do not strip |

> **Removed examples:** هلکوکی and کوچکی (doubtful; کوچکی is closer to Persian, Pashto uses کوچنی).
>
> Diminutive formation is highly sensitive to noun class, gender, phonology, and dialect. Do not implement these as unrestricted suffix-stripping rules.

---

## 5. Nominal inflection — نومیز صرفي پایونه

### 5.1 Plural markers

| Ending | Function | Example | Notes |
|---|---|---|---|
| -ونه | masculine plural (inanimate) | کتاب → کتابونه | |
| -ان | masculine plural (mostly animate) | استاد → استادان | |
| -ګان | masculine plural (vowel-final stems) | ماما → ماماګان | |
| -ي | plural of masculine -ی nouns | سړی → سړي | |
| -ې | feminine plural | ښځه → ښځې | |
| -ګانې | feminine plural (vowel-final stems) | دعا → دعاګانې | |
| -ۍ → -ۍ / -نې | feminine -ۍ class | نجلۍ → نجونې | Irregular; use lexicon |
| -ات | Arabic sound plural | معلومات، احساسات | borrowed |
| -ین | Arabic sound plural | معلمین | borrowed |
| broken plurals | Arabic internal plural | علما، اخبار | **Lexicon only**; cannot be stripped |

### 5.2 Oblique/case-related endings

| Ending | Typical function | Example | Notes |
|---|---|---|---|
| -و | oblique plural | هلکو | Homograph with vocative plural |
| -انو | oblique plural | هلکانو | |
| -ونو | oblique plural | کتابونو | |
| -ي | oblique singular of masculine -ی nouns | سړي | Homograph with plural |
| -ې | feminine singular oblique | ښځې | Homograph with plural and verb endings |

### 5.3 Vocative

| Ending | Function | Example | Notes |
|---|---|---|---|
| -ه | masculine singular vocative | هلکه! | |
| -و | plural vocative | هلکو! | Homograph with oblique -و |

### 5.4 Gender alternation (adjectives and some nouns)

| Masculine | Feminine | Plural | Example |
|---|---|---|---|
| ∅ | -ه | -ې / ∅ | غټ / غټه |
| -ی | -ې | -ي | ملګری / ملګرې / ملګري |
| -ونکی | -ونکې | -ونکي | ښوونکی / ښوونکې / ښوونکي |

> Pashto nominal inflection is not a simple suffix-substitution system. Gender, number, noun class, and final stem shape can trigger stem alternation.

---

## 6. Verbal morphology — فعلي صرف

### 6.1 Verb-forming (denominal/deadjectival) suffixes

| Suffix | Function | Example | Present stem | Notes |
|---|---|---|---|---|
| -ول | transitive/causative | ګرمول | ګرموي | Pairs with -ېدل |
| -ېدل | intransitive/inchoative | ګرمېدل، ښکارېدل | ګرمېږي، ښکارېږي | Present stem **-ېږ-** |
| + کول | compound transitive | کار کول، ښکاره کول | کوي | Light verb, written separately |
| + کېدل | compound intransitive/passive | ښکاره کېدل | کېږي | Light verb |

### 6.2 Personal endings

**Present (e.g., ګرځېدل → ګرځ-):**

| Person | Ending | Example |
|---|---|---|
| 1sg | -م | ګرځم |
| 2sg | -ې | ګرځې |
| 3sg/pl | -ي | ګرځي |
| 1pl | -و | ګرځو |
| 2pl | -ئ | ګرځئ |

**Past (intransitive, e.g., وګرځېدل):**

| Person | Ending | Example |
|---|---|---|
| 1sg | -م | وګرځېدم |
| 2sg | -ې | وګرځېدې |
| 3sg masc | -ه / ∅ | وګرځېده / وګرځېد |
| 3sg fem | -ه | وګرځېده |
| 1pl | -و | وګرځېدو |
| 2pl | -ئ | وګرځېدئ |
| 3pl masc | -ل | وګرځېدل |
| 3pl fem | -ې | وګرځېدې |

> **Ergativity:** In the past tense, transitive verbs agree with the **object**, not the subject. Feature assignment must take this into account.
>
> **Homograph:** 3pl masculine past **-ل** (تلل "they went") is identical to the infinitive **-ل**. Flag as ambiguous.
>
> Exact endings vary by tense/aspect, verb class, and dialect. Irregular verbs (کول، تلل، راتلل، کېدل) must come from the verb lexicon.

### 6.3 Participles

| Ending | Function | Example | Notes |
|---|---|---|---|
| -لی | past participle, masc sg | لیکلی، تللی | Regular form |
| -لې | past participle, fem / pl | لیکلې | |
| -لي | past participle, masc pl | لیکلي | |
| -ونکی | active participle | لیکوونکی | Also agent noun (§2.4) |
| کړی / کړې / کړي | irregular participle of کول | کړی | Lexicon, not -ی rule |

### 6.4 Infinitive

| Ending | Function | Example | Notes |
|---|---|---|---|
| -ل | infinitive / verbal noun | کول، تلل، لیکل | Removing -ل gives the **past stem** only |

### 6.5 Imperative and potential

| Form | Function | Example |
|---|---|---|
| -ه | imperative singular | کوه، ولیکه |
| -ئ | imperative plural | کوئ، ولیکئ |
| -ای / -لای + شول | potential/optative | کولای شم، لیکلای شي |
| مه + imperfective | negative imperative | مه کوه |

### 6.6 Present vs past stems

Present stems frequently differ from the infinitive/past stem. These must be stored in the verb lexicon:

| Infinitive | Past stem | Present stem |
|---|---|---|
| لیکل | لیکل- | لیک- |
| تلل | تل- / لاړ- | ځ- |
| کتل | کتل- | ګور- |
| اخیستل | اخیستل- | اخل- |
| کول | کړ- / کاو- | کو- |

---

## 7. Stem-internal morphology — د ریښې دننه بدلون

Not every Pashto morphological operation is a detachable prefix or suffix.

Important phenomena include:

- stem vowel alternation
- consonant alternation
- irregular past stems
- suppletion
- internal past/perfective morphology
- participial stem changes
- person/number-conditioned stem changes
- present/past stem differences (§6.6)

### Examples of the principle

| Surface form | Morphological issue |
|---|---|
| کول → وکړ | irregular/perfective stem relation |
| تلل → لاړ | suppletive/irregular relationship |
| راتلل → راغلل | directional + irregular verbal morphology |
| ورکول → ورکړ | verbal stem alternation |
| نجلۍ → نجونې | irregular nominal plural |
| کوره (in بې‌کوره) ← کور | stem alternation under derivation |

These must be handled by **verb/noun dictionaries and paradigm tables**, not only by suffix/prefix rules.

---

## 8. Multi-affix structures

### 8.1 Prefix + stem

```text
نا + پوه
بې + کور + ه
```

### 8.2 Stem + suffix

```text
ملګري + توب
ښه + والی
وطن + پال
```

### 8.3 Prefix + stem + suffix (layered, not circumfix)

```text
نا + پوه + ي
بې + کار + ي        (بېکار → بېکاري)
بې + غږ + ي         (بې‌غږ → بې‌غږي)
```

### 8.4 Stacked suffixes

```text
وطن + پال + نه      (وطنپالنه)
لیک + ونکی          (لیکوونکی)
```

### 8.5 Co-occurrence patterns (not circumfixes)

بې- adjectives regularly take **-ه**: بې‌کوره، بې‌وسه، بې‌غمه. Record this with a `co_occurs_with` field rather than treating بې- ... -ه as a single circumfix.

### 8.6 Verbal prefix + stem + verbal ending

```text
و + لیک + ل
را + تل + ل
کو + ي
و + ګرځېد + م
```

### 8.7 Compound-initial elements (not prefixes)

Some free words form families of compounds. They must **not** be stripped as prefixes, because many of the resulting words are lexicalized.

| Element | Examples | Notes |
|---|---|---|
| ځان (self) | ځانګړی، ځانمرګی، ځان‌غوښتنه | ځانګړی ("special") is lexicalized |
| مخ (face/front) | مخکښ، پرمختګ | پرمختګ = پر + مخ + تګ |

> **Rejected as prefixes:** پرله- (پرله‌پسې is one lexicalized word), تېر- (تېر شوی is a compound verb form), ناوړه- (an independent adjective, itself نا- + وړه).

---

## 9. Important distinction for NLP

Do **not** put all of the following into one undifferentiated "affix" list:

1. Derivational affixes
2. Inflectional affixes
3. Verb-forming suffixes (-ول / -ېدل)
4. Verbal aspectual elements
5. Directional (pronominal) verbal elements
6. Negative particles
7. Independent grammatical particles and enclitics
8. Compound-initial elements
9. Stem alternations
10. Irregular/suppletive forms

For a Pashto stemmer/lemmatizer, the recommended representation is:

```text
WORD
 ├── CLITICS (removed at tokenization)
 ├── PREFIX / PREFIX-LIKE ELEMENT
 ├── STEM / ROOT
 ├── DERIVATIONAL SUFFIX(ES) — ordered layers
 ├── INFLECTIONAL SUFFIX
 └── INFLECTIONAL FEATURES
      ├── person
      ├── number
      ├── gender
      ├── case (direct / oblique / vocative)
      ├── tense
      ├── aspect
      ├── mood
      └── agreement target (subject / object — ergative past)
```

---

## 10. Recommended database schema for an affix lexicon

| Field | Example |
|---|---|
| affix | نا- |
| normalized_affix | نا |
| type | prefix |
| subtype | derivational |
| function | negation/opposition |
| example | ناپوه |
| stem_or_base | پوه |
| derived_form | ناپوه |
| output_category | adjective |
| derivation_order | 1 (1 = innermost layer) |
| co_occurs_with | — (e.g., بې- → -ه) |
| allomorphs | — (e.g., -ونکی / -ونکې / -ونکي) |
| homograph_of | — (e.g., -و oblique ↔ -و vocative) |
| origin | native / Persian / Arabic / Turkic |
| language | Pashto |
| dialect | Common/unspecified |
| productivity | productive / restricted / lexicalized / borrowed |
| confidence | high / medium / low |
| strip_allowed | yes / no / lexicon-only |
| notes | Do not strip blindly |

---

## 11. Orthographic normalization and tokenization

### 11.1 The five ی letters — keep separate, never merge

| Letter | Name | Typical role | Example |
|---|---|---|---|
| ی | nārīna yē | masculine singular ending | سړی |
| ي | ma'rūfa yē | plural, oblique, 3rd-person verb | سړي، کوي |
| ې | majhūla yē | feminine, plural, 2sg verb | ښځې، کوې |
| ۍ | ṡəźīna yē | feminine singular ending | نجلۍ |
| ئ | fāiliya yē | 2nd plural verb, imperative | کوئ |

Merging them destroys grammatical information: سړی / سړي (man / men), کوې / کوي (you do / he does), ملګری / ملګرې / ملګري (friend: masc / fem / plural).

### 11.2 What to normalize (encoding variants only)

1. Arabic ي (U+064A) in word-medial position → ی (U+06CC). Handle word-final ي by context, since it is also the Pashto ma'rūfa yē. **Test on real text.**
2. Arabic ى (alef maksura, U+0649) → ی.
3. Arabic ك (U+0643) → ک (U+06A9).
4. ۀ vs ه → choose one convention and record the original.
5. Spacing and ZWNJ around suffixes (ښه والی / ښه‌والی) → standardize, and match all variants.
6. Diacritics (zabar, zer, pesh) → strip for matching only.

Always keep the original surface form in a separate field.

### 11.3 Tokenization before stemming

1. **Enclitic pronouns:** مې، دې، یې، مو — sometimes attached in informal text. Separate them first.
2. **Postpositions:** کې، ته، سره، نه — sometimes attached. Separate them first.
3. **Split verbal complexes:** clitics and negation can come between a perfective prefix and its stem (و یې لیکل، و نه لیکل). Reattach for lemmatization.
4. **Light verbs:** کول / کېدل compounds are written as two words; link them as one lexical unit.

---

## 12. Quality-control rules

1. Never remove an apparent affix solely by string matching.
2. Keep the original word unchanged in the corpus.
3. Store normalized and surface forms separately.
4. Mark ambiguous affixes and homographs.
5. Keep irregular verbs and present/past stems in a separate lexicon.
6. Record dialectal variants separately.
7. Distinguish derivation from inflection.
8. Distinguish particles, enclitics, and compound elements from true affixes.
9. Validate every proposed affix with attested examples. Entries without attested examples stay at **confidence: low**.
10. Use a human-validated affix list for the final stemming rules.
11. Never merge the five ی letters.
12. Strip suffixes from the outermost layer inward, and check each intermediate form against the lexicon.
13. Never use fuzzy matching on near-minimal pairs (e.g., لوبغاړی / لوبغالی).

---

## 13. High-level inventory

```text
PREFIXES
├── Derivational (نا، بې، هم، بیا، غیر، لا، بلا، نیم، سر، ضد)
├── Aspectual/perfective (و، وا، کې/کښې، پرې)
├── Directional-pronominal (را، در، ور)
└── Negative particles (نه، مه) — separate words

SUFFIXES
├── Abstract/state nouns
├── Action/result nouns
├── Place/institution/container nouns
├── Agent/occupation nouns
├── Adjectives
├── Verb-forming (-ول، -ېدل)
└── Diminutive/evaluative

INFLECTION
├── Plural
├── Case (direct / oblique / vocative)
├── Gender
├── Person
├── Number
├── Tense
├── Aspect
├── Mood (imperative, potential)
└── Participles

COMPOUND-INITIAL ELEMENTS
└── ځان، مخ

STEM-INTERNAL MORPHOLOGY
├── Stem alternation
├── Vowel alternation
├── Consonant alternation
├── Irregular stems
├── Present/past stem pairs
└── Suppletion

PRE-PROCESSING
├── Orthographic normalization
└── Clitic and postposition tokenization
```

---

## 14. Open items needing validation

| Item | Issue |
|---|---|
| -ولي | No confirmed attested example |
| -وان | Needs an attested native example |
| -ګی / -ګۍ، -ګوټی / -کوټی | Confirm diminutive examples and class restrictions |
| -غالی | Only one attested example (لوبغالی) |
| کښتۍبان | Unconfirmed |
| Word-final Arabic ي normalization | Needs testing on real corpus text |

### Sources for validation

- Anne David, *Descriptive Grammar of Pashto and its Dialects* — comprehensive grammatical treatment.
- *Pashto Affixes from the Viewpoint of Lexical Morphology* — reports a substantially larger affix inventory and distinguishes derivational and inflectional affixes.
- Pashto computational morphology literature — useful for machine-readable treatment of verbal prefixes, suffixes, and inflection.
- Pashto Academy dictionary and Raverty's dictionary — for checking attested examples.
