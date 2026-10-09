<div align="center">

# 🌿 Pashto Stemmer

### A Grammar-Driven Rule-Based Stemmer for Pashto

*No machine learning anywhere in it. 117 affix rules taken from published
grammars, each carrying its source, its productivity, and an explicit decision
about whether it may be applied at all — and a scoring step that chooses
between competing analyses.*

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-48%20passing-brightgreen.svg)](tests/)
[![Pashto](https://img.shields.io/badge/language-پښتو-orange.svg)](#)

</div>

---

## Contents

[Why this exists](#why-this-exists) ·
[Quick start](#quick-start) ·
[Stemming a file](#stemming-a-file) ·
[Results](#results) ·
[Reproducing the paper](#reproducing-the-paper) ·
[Stemming or lemmatization](#stemming-or-lemmatization) ·
[How it works](#how-it-works) ·
[The five yeh letters](#the-five-yeh-letters) ·
[Repository layout](#repository-layout) ·
[Data](#data) ·
[Limitations](#limitations)

## Why this exists

Pashto has around forty million speakers and almost no stemming tools. The one
dedicated prior system, Aslamzai & Saad (2015), applies nine fixed affix rules
with no lexicon and no way to choose between analyses. On our test data it
leaves most words untouched and damages many of the ones it does change.

This project takes a different route and stays entirely rule-based:

- **107 suffix rules and 10 prefix rules**, 111 of them located in Tegey &
  Robson or Penzl by chapter or section. Each records the grammar it came
  from, whether it is inflectional or derivational, a minimum surviving stem
  length, the part of speech it signals, its productivity, a confidence level,
  and whether it may be stripped at all. **27 of the 117 are documented and
  deliberately never applied** — recording an affix and refusing to strip it is
  not the same as omitting it, because the inventory is also a description of
  the language.
- **Generation separated from selection.** Every rule that fits is applied and
  all the results compete, so a shallower analysis can displace a deeper one.
  The lexicon informs that choice; it never blocks a strip, because the output
  of a stemmer does not have to be a dictionary word.
- **A dictionary of 42 irregular verbs** — the strong verbs, whose present stem
  cannot be derived from the infinitive (`لیدل → وین`, `تلل → ځ`). It returns a
  **lemma**, which is lemmatization rather than stemming, so it is **off by
  default**. See [Stemming or lemmatization](#stemming-or-lemmatization).

## Quick start

```bash
git clone https://github.com/Khairullah-Ibrahim-Khail/Pashto_Stemmer
cd Pashto_Stemmer
pip install -e .
python examples/quickstart.py
```

```python
from pashto_stemmer import PashtoStemmer

st = PashtoStemmer()

st.stem("کورونه")      # 'کور'      plural ‑ونه removed
st.stem("خبرونه")      # 'خبر'
st.stem("افغانستان")   # 'افغان'    ‑ستان is an affix like any other
st.stem("پوهنتون")     # 'پوهن'     the stem need not be a word
st.stem("روغتیا")      # 'روغ'
st.stem("ښوونځی")      # 'ښوون'
st.stem("لوبغاړی")     # 'لوبغاړ'   agent ‑غاړی, stopping before the bare root
st.stem("کورس")        # 'کورس'     a loanword, left alone

# a whole line; stopwords are left alone
[r.stem for r in st.stem_text("د کورونو خبرونه")]   # ['د', 'کور', 'خبر']

# every decision can be inspected
r = st.stem_word("بېکاره")
print(r.stem, r.confidence, r.rules_applied)
# بېکار 0.65 ('+ه',)
```

From the shell:

```bash
python -m pashto_stemmer.cli کورونه خبرونه افغانستان
python -m pashto_stemmer.cli --file article.txt
echo "د کورونو خبرونه" | python -m pashto_stemmer.cli --trace
```

## Stemming a file

**A plain text file.** The CLI reads UTF-8 and writes one `word<TAB>stem` pair
per line, so the output pipes straight into `cut`, `sort` or `uniq`:

```bash
python -m pashto_stemmer.cli --file article.txt
```

```
د	د
افغانستان	افغان
په	په
کورونو	کور
خبرونه	خبر
```

Stopwords come back unchanged, which is what you want for an index. Add
`--trace` to see the confidence and the rules that fired on each word.

**A dataset — CSV, TSV or Excel.** Point the CLI at the file and name the
column. Every original column is written back with the stemmed text in a new
one beside it:

```bash
python -m pashto_stemmer.cli --csv   articles.csv  --column text --out stemmed.csv
python -m pashto_stemmer.cli --excel articles.xlsx --column text --out stemmed.xlsx
```

```
id,text,note,text_stemmed
1,د کورونو خبرونه,a,د کور خبر
2,پوهنتون ته ولاړ,b,پوهن ته ولاړ
3,افغانستان او پاکستان,c,افغان او پاک
```

`--csv`, `--excel` and `--table` are the same option under three names; what
matters is the file extension. `.csv` and `.tsv` are read as text, `.xlsx` and
`.xlsm` through openpyxl, and the output format follows the extension you give
`--out` — so `--out stemmed.xlsx` writes a workbook, and leaving `--out` off
prints CSV to stdout so it pipes. Use `--sheet` to pick a worksheet other than
the first.

Two details that matter in practice. CSV files are read as `utf-8-sig`, so a
file exported from Excel works without stripping its byte-order mark. And if
the named column is not there, the CLI lists the column names it did find and
exits non-zero rather than writing a file with an empty column in it.

Reading `.xlsx` needs openpyxl:

```bash
pip install openpyxl
```

From Python, if you want the result in memory rather than on disk:

```python
from pashto_stemmer import PashtoStemmer

st = PashtoStemmer()
" ".join(r.stem for r in st.stem_text("د کورونو خبرونه"))   # 'د کور خبر'
```

Build the `PashtoStemmer()` once and reuse it — it loads the rule inventory and
the lexicon on construction, after which it stems about 7,000 word types per
second.

## Results

Two evaluations. The first is the one that matters.

**Held-out news words** — 499 word types drawn from a Pashto news corpus, none
of them in the development set, annotated by the same three native speakers with
the reference field initially empty, all three agreeing on the result, and never
consulted during development:

| System | Accuracy | On words needing a strip | On words to leave alone | Paice UI ↓ |
|---|:---:|:---:|:---:|:---:|
| Do nothing | 37.27% | 0.0% | 100.0% | 1.000 |
| Aslamzai & Saad (2015) | 40.48% | 16.9% | 80.1% | 0.889 |
| **This stemmer** | **71.34%** | **70.6%** | 72.6% | **0.500** |

**Development set** — 2,717 annotated word types:

| System | Accuracy | On words needing a strip | On words to leave alone | Paice UI ↓ |
|---|:---:|:---:|:---:|:---:|
| Do nothing | 47.77% | 0.0% | 100.0% | 1.000 |
| Aslamzai & Saad (2015) | 50.68% | 12.2% | 92.8% | 0.919 |
| **This stemmer** | **80.27%** | **78.6%** | 82.0% | **0.304** |

**Two external word lists** — 5,000 and 10,000 types, independently annotated,
neither produced by this project, 96% of them unseen:

| Dataset | Types | Exact | ye-folded |
|---|---:|:---:|:---:|
| External 5k | 5,000 | **71.96%** | **80.14%** |
| — Aslamzai & Saad (2015) | | 51.24% | 57.36% |
| External 10k | 10,000 | **70.39%** | **77.69%** |
| — Aslamzai & Saad (2015) | | 47.95% | 53.68% |

Three sets at 70–72% exact is the generalisation evidence. Both lists
ye-normalise their reference column while leaving `ي` in the word column, so a
stem is scored wrong for keeping the letter the word actually has; folding the
five ye letters for the comparison alone — the output is never rewritten —
gives the second column. The same folding is worth 1.51 points on our
development set and 0.80 on our held-out set, which are internally consistent.
They also follow a different annotation policy, agreeing with our reference on
70.8% and 64.1% of shared words. Those disagreements sort cleanly: about a
quarter are places where our reference gives a lemma no truncation reaches,
roughly half cut deeper than we do, a quarter cut less, and only two in 154 are
about the spelling of a ye. They test generalisation, not correctness under our
policy. See
[dataset/external/README.md](dataset/external/README.md).

### How to read these numbers

**Accuracy alone rewards doing nothing.** A stemmer that returns every word
unchanged already scores 37.3% on the held-out set, because a large share of
Pashto word types carry no affix. That is why both tables split the task in
two. Aslamzai & Saad reaches 40.5% overall but only **16.9%** on the words that
actually need stripping; this system reaches **70.6%** on that half, a factor
of four.

**The development set was annotated independently by three native speakers** —
the author, a Pashto-medium school principal and a university teacher of Pashto —
and adjudicated by the author. Two of the three passes are released, so the
agreement between them is recomputable, not asserted: they chose the same stem
on **96.88%** of the 2,725 types both annotated (Cohen's κ **0.969**), and
agreed on **98.24%** of the binary judgement of whether a word carries an affix
at all (κ **0.965**). Run `python experiments/agreement.py` to reproduce it.

**Both sets exclude the rows a truncating stemmer cannot reach.** Where the
reference is an Arabic broken plural or a suppletive form — `اثارو → اثر`,
`نجونو → نجلۍ` — the answer is a lemma that no affix rule can produce, and
marking a stemmer wrong there penalises it for not being a lemmatizer. That is
195 of 2,912 development types and 1 of 500 held-out types, reported
separately rather than hidden.

**87% in the prior work is not comparable with 71% here.** The difference is
the protocol, not the algorithm. Aslamzai & Saad show system output to native
speakers and ask whether it is acceptable; we fix the reference before seeing
any output and require an exact match. Scored their way, a stemmer that
modifies **no word at all scores 100%**, because every unchanged word is
acceptable to a judge and it produces nothing else:

| System | A: exact match | B: judged acceptable | Words modified |
|---|:---:|:---:|:---:|
| Do nothing | 37.27% | **100.00%** | 0.0% |
| Aslamzai & Saad (2015) | 40.48% | 80.76% | 37.5% |
| **This stemmer** | **71.34%** | **98.60%** | 68.3% |

This does not show the published 87% to be wrong. It shows the measurement
answers a different question.

Per-rule precision is published too, in the paper's Table XI — how often each
rule fires in a selected analysis and how often that analysis is right. Building
it retired two rules (`لو`, `لې`) that fired 26 times between them and were
never correct, worth +0.85 on the development set.

### What each component contributes

Leave-one-out, in percentage points:

| Configuration | Development | Held-out |
|---|:---:|:---:|
| **Full system** | **80.27%** | **71.34%** |
| without suffix rules | 71.99% (−8.28) | 58.92% (−12.42) |
| without the length rules | 77.62% (−2.65) | 69.34% (−2.00) |
| without the corpus lexicon | 80.09% (−0.18) | 71.74% (+0.40) |
| without the uniform-strip group | 80.05% (−0.22) | 71.14% (−0.20) |
| without prefix rules | 80.24% (−0.04) | 71.54% (+0.20) |
| *with* the verb dictionary | 78.91% (−1.36) | 70.54% (−0.80) |

The suffix inventory does most of the work. Three of these rows record
decisions taken **against** the measured score, stated rather than quietly
resolved in favour of whatever scored best:

- **Prefix rules** cost four hundredths of a point and are kept, because
  `هم‑`, `بیا‑`, `نیم‑` and `لا‑` are real Pashto prefixes and deleting the
  rules would amount to claiming the language has none. The effect is small
  partly because four of the ten prefix rules are gated off: `نا‑`, `بې‑` and
  `غیر‑` are negation prefixes the annotation policy keeps, since `ناقانونه`
  is not an instance of `قانون` but its opposite, and `سر‑` is a free noun as
  often as it is a prefix.
- **The corpus lexicon** is worth 0.18 points on development data and −0.40 on
  held-out. Its contribution is marginal now that the uniform-strip and length
  rules decide most cases before the scorer is consulted, so this system should
  **not** be described as lexicon-driven.
- **The verb dictionary** costs about a point on both sets, for the reason in
  the next section.

A fourth result is negative and reported anyway. A 257-entry list of
development-set words that should be left unchanged raises development accuracy
by 8.5 points and held-out accuracy by **zero**: of the 51 held-out types
needing the same treatment, none appear in the list. It is pure memorisation of
one sample.

### Where the errors are

| What the reference removes | Types | Accuracy |
|---|---:|---:|
| Nominal inflection | 624 | 80.1% |
| Verbal inflection | 41 | 95.1% |
| Derivation: nouns | 582 | 90.9% |
| Derivation: adjectives | 18 | 88.9% |
| **No affix, word left whole** | **1,347** | **79.1%** |
| **Nothing in the inventory** | **105** | **30.5%** |

Accuracy is high wherever the reference removes an affix the inventory holds.
The damage is in the last two rows: 282 words stripped that should have been
left alone, and 105 types the inventory cannot explain at all.

The selection score is published in full — the formula and all six weights are
in the paper's Table V, and in `pashto_stemmer/validation.py`. They were set by
hand and adjusted on the development set; none were fitted automatically and
the held-out set was never used to choose them.

## Reproducing the paper

```bash
python experiments/reproduce_paper.py     # every results table in the paper
python experiments/evaluate_external.py   # the two external word lists
python experiments/agreement.py           # inter-annotator agreement and kappa
python experiments/audit_annotation.py    # removals matching no documented affix
python experiments/compare_stemmers.py    # the development-set comparison
python experiments/ablation.py            # a broader component sweep
```

`reproduce_paper.py` regenerates the four result tables exactly as printed, and
prints its own warning if any figure drifts. `audit_annotation.py` checks every
removal in an annotated set against the affix inventory and writes the
unresolved rows to `dataset/unsupported_removals_*.csv`; 33 of 287 removals in
the held-out reference and 105 of 1,355 in the development reference match no
documented affix, and each is either an annotation error or a gap in the
inventory.
Note that `ablation.py` scores **all 2,912 development rows**, including the
lemma rows a truncating stemmer cannot reach, and toggles a different set of
switches — so its figures are deliberately not the paper's, and it is kept as a
wider exploration rather than as the paper's evidence.

Run the tests with:

```bash
for f in tests/test_*.py; do python "$f"; done
```

48 tests across five files: the stemmer end to end, the normalizer's treatment
of the yeh letters, the irregular-verb dictionary, Paice's metrics, and the
command line including both file modes.

## Stemming or lemmatization

These are different tasks, and the distinction decides how the system is
configured.

**Stemming removes characters.** The output is a class label, not a word.
Porter maps both *relational* and *relate* to *relat*, which is not an English
word; this system likewise produces `ښوون`, `لوبغاړ` and `پوهن`. That is
correct behaviour, not a defect.

**Lemmatization substitutes one word for another.** `شو → کېدل` and
`نجونو → نجلۍ` cannot be reached by removing characters. The irregular-verb
dictionary does exactly this, so it belongs to lemmatization: on the 2,717
stemming types it changes the output for 69 words and is right on 11 of them,
because it supplies the wrong *kind* of answer. On the 195 lemma types it
answers 51, against 8 without it. It is therefore off by default and offered
as an explicit mode:

```python
from pashto_stemmer.stemmer import PashtoStemmer, StemmerConfig

lem = PashtoStemmer(StemmerConfig(use_verb_dictionary=True))
lem.stem("شو")      # 'کېدل'  — a lemma, not a stem
```

## How it works

```
normalize → stopwords → deterministic affix groups → length rules
          → generate every legal candidate → score and select → final trim
```

**Normalization** removes diacritics, tatweel and zero-width joiners, and
unifies the Arabic kaf, the alef-hamza forms, and the Urdu letters common in
Pashto written in Pakistan (`ٹ ڈ ڑ ے`, Persian `گ`). These are encoding
corrections, not changes of spelling.

**Deterministic affix groups** bypass the scorer. The abstract-noun and place
suffixes `تیا`, `توب`, `والی` and `تون` are long and unambiguous, so no
competing analysis exists to weigh. Leaving them arbitrated meant `روغتیا` and
`پوهنتون` came back unchanged, because `روغ` and `پوهن` are not in the lexicon.

**Candidate generation** applies every rule that fits and returns all distinct
results, including the original word with nothing removed. Selection is a
separate stage, which is what allows a shallower analysis to win.

**Selection** scores each candidate on how much affix material was removed,
whether other words in the corpus are built on the same stem, and whether the
stem itself is attested. Being attested raises a candidate's score; it is never
required. The unstripped word gets only a small bonus — it is almost always in
the corpus, and giving it the full one made inaction the default winner and
concealed every single-letter inflection.

**Guards.** A prefix is removed only when the remainder is an attested word;
without this, `لانسیټ` loses its first two letters. And a four- or five-letter
word beginning with a *removable* prefix goes to the full inventory instead of
simply losing its last letter.

## The five yeh letters

Pashto writes five distinct characters called *yeh*. They are not
interchangeable — they carry gender, number and case:

| Letter | Example | Function |
|---|---|---|
| ی | سړی | masculine singular direct |
| ي | سړي | masculine plural/oblique; 3rd person present |
| ې | ښکلې | feminine; plural |
| ۍ | نجلۍ | feminine singular, one noun class |
| ئ | ووایئ | 2nd person plural imperative |

Normalization pipelines written for Persian or Urdu routinely merge these into
one character. **This one does not**, and that is verified: no yeh character is
altered in any cell of either evaluation set. Merging them would make `سړی`
(man) and `سړي` (men) indistinguishable.

Rule *matching* is a separate question. The same suffix is written `ی` in
dictionary orthography and `ي` in news orthography, so a rule spelled one way
never fired on the other: of the 500 held-out news types 118 contain `ي`, and
of the 2,912 development types **none** do. Matching now compares a folded key
while the letters written out are never changed. On news text that is worth
1.20 points — the clearest case in the project of a defect a single-source
evaluation set could not have revealed.

## Repository layout

```
pashto_stemmer/     the library
  stemmer.py          the pipeline and its configuration
  rules.py            the AffixRule type and candidate generation
  suffixes.py         107 suffix rules
  prefixes.py          10 prefix rules
  normalizer.py       encoding repair; never merges the yeh letters
  validation.py       candidate scoring and selection
  baseline.py         Aslamzai & Saad (2015), reimplemented from the paper
  metrics.py          accuracy and Paice's under/over-stemming indices
  cli.py              command line interface
dataset/            both annotated sets and the correction log
docs/               the affix inventory, annotation policy, verb dictionary
experiments/
  reproduce_paper.py  regenerates every results table in the paper
  evaluate_external.py  the two independently annotated word lists
  agreement.py        inter-annotator agreement and Cohen's kappa
  audit_annotation.py checks annotations against the affix inventory
  compare_stemmers.py the development-set comparison
  ablation.py         a wider component sweep (not the paper's table)
paper/              the paper: LaTeX source, Word, PDF, and its generators
tests/              48 tests
```

## Data

| File | Contents |
|---|---|
| `dataset/pashto_gold_corrected_v2.csv` | development set, 2,912 word types (`word,stem`) |
| `dataset/test_500_news_corrected.csv` | held-out set, 500 news word types (`no,word,frequency,stem,note`) |
| `dataset/annotations/` | two of the three independent annotation passes |
| `dataset/external/` | two independently annotated word lists, 5k and 10k, not ours |
| `dataset/pashto_gold_changes(1).md` | every hand correction and the reason for it |
| `dataset/ANNOTATION_GUIDELINES.md` | what counts as a stem |

Both sets were annotated independently by three native speakers — the author, a
Pashto-medium school principal and a university teacher of Pashto — and
adjudicated by the author. The two released development-set passes agree at
96.88% on the exact stem (κ 0.969). The held-out set was annotated with the
reference field initially empty, so that nothing anchored them to any system's
output.

Both sets were audited by comparing every removal against the affix inventory.
A removal matching no documented affix is either an annotation error or
evidence that the inventory is incomplete, and inspection separates the two.
That audit caught a bad first pass of the held-out set, in which 47% of
removals corresponded to no affix at all, and it found six affixes the
inventory was missing. The procedure is cheap and we recommend it.

## Limitations

- **Native words, not loanwords, are the harder half.** We assumed borrowings
  dominated the error and measured otherwise: on the types the reference leaves
  whole we are wrong on 28.3% of certainly-native words against 17.8% of the
  rest. `خواړه`, `وړاندې`, `داسې`, `پاتې` and `یوازې` are ordinary Pashto words
  the length rules cut.
- **The final `ه` is genuinely ambiguous.** `لنډه → لنډ` is right and
  `خواړه → خواړ` is wrong, and nothing in the surface form separates them. The
  rule fires 131 times on the development set and is right 86 times; removing
  it costs 1.62 points. No reformulation conditioned on the surface form can
  help — only a lexical resource can.
- **Three rules sit below 60% precision and are kept**: `ان` (46.4%) and the
  two three-letter length rules (53.8%, 56.2%). Gating `ان` costs 0.40 points on
  held-out text, so the low precision reflects competition with longer analyses
  rather than a broken rule.
- **Compounds are kept whole.** That is a policy, not a solution. A splitter
  was implemented, measured and removed: across both sets it fired on seven
  types and was wrong on all seven, returning a suffix instead of a word
  (`نړۍوال → وال`, `پټرولیم → یم`).
- **The evaluation is on word types, not running text**, so there is no
  measurement of retrieval effectiveness and no evidence yet about downstream
  gains.
- **Agreement is measured on the development set.** Two of its three
  independent passes are released (κ 0.969 on the exact stem, 0.965 on the
  binary decision). The held-out set carries a single agreed reference, so no
  coefficient is computed for it.
- **Citations are located but not page-verified.** 111 of 117 rules cite
  Tegey & Robson by chapter or Penzl by section; the remaining six are oblique
  and feminine variants of cited suffixes and are marked author-proposed. The
  chapter attributions were assembled by the author and have not been checked
  page by page, so treat each locus as a pointer. Every rule carries its source
  in the `source` column of `paper/inventory_rows.tsv` and in Appendix A. Of the 42 irregular verbs, 8 are unverified
  against a printed grammar and are marked as such in
  [docs/03_irregular_verbs.md](docs/03_irregular_verbs.md).

## Documentation

| File | Contents |
|---|---|
| [paper/main.tex](paper/main.tex) | the paper, LaTeX source — build with XeLaTeX or LuaLaTeX |
| [paper/Pashto_Stemmer_Paper.pdf](paper/Pashto_Stemmer_Paper.pdf) | the paper, built |
| [docs/01_affix_inventory.md](docs/01_affix_inventory.md) | every affix with its productivity, confidence and whether it may be stripped |
| [docs/02_annotation_policy.md](docs/02_annotation_policy.md) | what counts as a stem, and why |
| [docs/03_irregular_verbs.md](docs/03_irregular_verbs.md) | the verb dictionary, marked verified or not |
| [docs/Aslamzai_Saad_2015_Rules.pdf](docs/Aslamzai_Saad_2015_Rules.pdf) | the baseline's nine rules, transcribed from the paper |

The paper's inventory tables are generated straight from the rule objects by
`paper/make_inventory_tables.py`, so the documentation cannot drift from the
implementation.

## Citing

```bibtex
@mastersthesis{pashto-stemmer,
  title  = {A Grammar-Driven Rule-Based Stemmer for Pashto},
  author = {Khairullah Ibrahim Khail},
  school = {Institute of Management Sciences, Peshawar},
  year   = {2026}
}
```

## License

MIT. See [LICENSE](LICENSE).
