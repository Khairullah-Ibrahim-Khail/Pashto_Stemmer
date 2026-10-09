<div align="center">

# 🌿 Pashto Stemmer

### Dictionary-Enhanced Rule-Based Stemming for Pashto

*A rule-based stemmer for Pashto — no machine learning anywhere in it. Affix rules
taken from published grammars, a dictionary for the verbs that rules cannot predict,
and a scoring step that chooses between competing analyses.*

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-37%20passing-brightgreen.svg)](tests/)
[![Pashto](https://img.shields.io/badge/language-پښتو-orange.svg)](#)

</div>

---

## Why this exists

Pashto has around forty million speakers and almost no stemming tools. The one
dedicated prior system, Aslamzai & Saad (2015), applies nine fixed affix rules
with no lexicon and no way to choose between analyses. On our test data it leaves
most words untouched and damages many of the ones it does change.

This project takes a different route, and stays entirely rule-based:

- **109 suffix rules and 10 prefix rules**, each carrying the grammar it came from
  (Tegey & Robson, Robson & Tegey, David, Wiktionary, Naeem & Khan, Khan 2023).
- **A dictionary of 42 irregular verbs** — the Pashto strong verbs, whose present
  stem cannot be derived from the infinitive (`لیدل → وین`, `تلل → ځ`). Regular
  verbs are handled by rule, not listed.
- **A scoring step** that picks among the candidate stems the rules generate.
  The lexicon informs that choice; it never blocks a strip, because the output of
  a stemmer does not have to be a dictionary word.

## Results

Two evaluations. The second is the one that matters.

**Held-out news words** — 500 word types drawn from a Pashto news corpus, none of
them in the development set, annotated by a native speaker and never used for
tuning:

| System | Accuracy | On words needing a strip | On words to leave alone | Paice UI ↓ |
|---|:---:|:---:|:---:|:---:|
| Do nothing | 34.60% | 0.0% | 100.0% | 1.000 |
| Aslamzai & Saad (2015) | 37.60% | 15.3% | 79.8% | 0.909 |
| **This stemmer** | **60.40%** | **59.0%** | 63.0% | **0.545** |

**Development set** — 2,912 annotated word types:

| System | Accuracy | Paice UI ↓ | Paice OI ↓ |
|---|:---:|:---:|:---:|
| Do nothing | 36.20% | 1.000 | 0.00000 |
| Aslamzai & Saad (2015) | 42.45% | 0.923 | 0.00001 |
| **This stemmer** | **77.06%** | **0.198** | 0.00022 |

A note on reading these numbers. A stemmer that returns every word unchanged
already scores 34.6% on the held-out set, because a third of Pashto word types
carry no affix. Accuracy alone therefore rewards doing nothing, which is why the
table separates the two halves of the task. Aslamzai & Saad reaches 37.6% overall
but only 15.3% on the words that actually need stripping; this system reaches
59.0% on that half.

The development-set figure is higher than the held-out figure, and the gap is
real. It comes mostly from orthography: the development set is written with `ی`
throughout, while news text uses `ي` for the same suffixes. Rules written in one
convention did not fire on the other until matching was made insensitive to the
choice. Proper nouns and loanwords are the other cost — endings that look like
Pashto affixes but are not.

### What each component contributes

Leave-one-out on the held-out set:

| Configuration | Accuracy | Change |
|---|:---:|:---:|
| Full system | 60.40% | — |
| without suffix rules | 47.60% | −12.80 |
| without the irregular-verb dictionary | 58.80% | −1.60 |
| without the length rules | 59.40% | −1.00 |
| without prefix rules | 60.60% | +0.20 |

The suffix inventory does most of the work. The irregular-verb dictionary is
worth 1.6 points, which is what justifies calling the system dictionary-enhanced.
Prefix stripping costs a fifth of a point; it is kept because `نا‑`, `بې‑`, `هم‑`
and `لا‑` are real Pashto prefixes, and it is guarded so that it only fires when
the remainder is an attested word — without that guard, `بېجينګ` (Beijing) loses
its first two letters.

Reproduce:

```bash
python experiments/compare_stemmers.py
python experiments/run_experiments.py
```

## Install

```bash
git clone https://github.com/khairullah/pashto-stemmer && cd pashto-stemmer
pip install -e .
```

## Usage

```python
from pashto_stemmer import PashtoStemmer

st = PashtoStemmer()

st.stem("کورونه")      # 'کور'    plural ‑ونه removed
st.stem("خبرونه")      # 'خبر'
st.stem("غواړي")       # 'غوښت'   irregular verb, via the dictionary
st.stem("افغانستان")   # 'افغان'  ‑ستان is an affix like any other
st.stem("بېکاره")      # 'کار'    prefix and suffix both removed

# a whole line; stopwords are left alone
[r.stem for r in st.stem_text("د کورونو خبرونه")]   # ['د', 'کور', 'خبر']

# every decision can be inspected
r = st.stem_word("بېکاره")
print(r.stem, r.confidence, r.rules_applied)
# کار 0.90 ('+ه', '-بې')
```

## How it works

```
normalize → stopwords → irregular-verb dictionary → length rules
          → generate every legal candidate → score and select → final trim
```

**Normalization** removes diacritics, tatweel and zero-width joiners, and unifies
the Arabic kaf and the alef-hamza forms. It does **not** merge the five Pashto
yeh letters (ی ي ې ۍ ئ). They mark gender, number and case, and collapsing them
destroys the distinction between `سړی` (man) and `سړي` (men). Rule *matching* is
insensitive to which yeh is written, so a rule spelled with `ی` still fires on a
news word spelled with `ي`, but the letters in the output are never changed.

**Candidate generation** applies every rule that fits, up to three times, and
returns all distinct results. Selection is separate from generation, which is
what allows a competing analysis to win.

**Selection** scores each candidate on how much affix material was removed,
whether other words in the corpus are built on the same stem, and whether the
stem itself is attested. Being attested helps a candidate; it is not required.

## Documentation

| File | Contents |
|---|---|
| [docs/01_affix_inventory.md](docs/01_affix_inventory.md) | the affix inventory: every affix with its productivity, confidence and whether it may be stripped |
| [docs/02_annotation_policy.md](docs/02_annotation_policy.md) | what counts as a stem, and why |
| [docs/03_irregular_verbs.md](docs/03_irregular_verbs.md) | the verb dictionary, marked verified or not |
| [docs/Pashto_Stemmer_Rules.pdf](docs/Pashto_Stemmer_Rules.pdf) | the twelve rules, with explanations and worked examples |
| [docs/Aslamzai_Saad_2015_Rules.pdf](docs/Aslamzai_Saad_2015_Rules.pdf) | the baseline's nine rules, transcribed from the paper |

## Limitations

- Proper nouns and loanwords are the main source of error. `منشي`, `سليمان` and
  `زیارت` end in sequences that look like Pashto affixes.
- Compounds are kept whole. Splitting them reliably needs a lexicon we do not have.
- The evaluation is on word types, not running text, and a single annotator
  produced the gold standard.
- Eight of the 42 irregular verbs have not been checked against a printed grammar.
  They are marked in [docs/05_irregular_verbs.md](docs/05_irregular_verbs.md).

## Citing

```bibtex
@mastersthesis{pashto-stemmer,
  title  = {A Dictionary-Enhanced Rule-Based Stemmer for Pashto},
  author = {Khairullah},
  school = {Institute of Management Sciences, Peshawar},
  year   = {2026}
}
```

## License

MIT. See [LICENSE](LICENSE).
