# pashto-stemmer

A rule-based stemmer for Pashto (پښتو). No machine learning: 118 affix rules
taken from published grammars, a corpus lexicon used to choose between
candidates, and every decision traceable to a rule.

**81.19%** exact-match accuracy on a 2,717-word development set and **72.75%**
on 499 held-out news types, against 50.68% and 40.48% for the previously
published Pashto stemmer.

```bash
pip install pashto-stemmer
pip install "pashto-stemmer[excel]"   # add .xlsx support
```

## One function

Give it a word, a sentence or a list — you get back the same shape.

```python
from pashto_stemmer import PashtoStemmer
st = PashtoStemmer()

st.stem("کورونه")                      # 'کور'
st.stem("د کورونو خبرونه")              # 'د کور خبر'
st.stem(["کورونه", "خبرونه"])           # ['کور', 'خبر']
st.stem(("کورونه", "خبرونه"))           # ('کور', 'خبر')   tuples and sets too
```

A few words worth seeing, because they show where the line is drawn:

```python
st.stem("افغانستان")   # 'افغان'    ‑ستان is an affix like any other
st.stem("پوهنتون")     # 'پوهن'     a stem need not be a word
st.stem("امریکایی")    # 'امریکا'
st.stem("لوبغاړی")     # 'لوبغاړ'   agent ‑غاړی, stopping before the bare root
st.stem("لاسلیک")      # 'لاسلیک'   a lexicalized compound, kept whole
st.stem("کورس")        # 'کورس'     a loanword, left alone
st.stem("")            # ''         blanks and non-strings never raise
```

**The five yeh letters (`ی ي ې ۍ ئ`) are never rewritten.** They mark gender,
number and case in Pashto, so folding them would destroy the morphology the
stemmer exists to read. Rule *matching* folds them; the output keeps whatever
letter the word had.

## Every entry point

| call | takes | gives back |
|---|---|---|
| `st.stem(x)` | a word, a sentence, a list, a tuple or a set | the same shape, stems only |
| `st.stem_word(w)` | one word | a `StemResult` — the stem plus how it was reached |
| `st.stem_sentence(s)` | a sentence | a sentence of stems |
| `st.stem_text(s)` | a sentence | a `StemResult` per token |
| `st.stem_file(path, …)` | a CSV, TSV or Excel path | rows, or a written file |
| `st.clear_cache()` | — | empties the result cache |

Repeated words are cached (500,000 entries), so a corpus costs about as much
as its vocabulary — roughly 7,000 words/second cold, 3 million cached.

## Why a decision was made

```python
r = st.stem_word("بېکاره")

r.input            # 'بېکاره'   the word as given
r.stem             # 'بېکار'
r.confidence       # 0.65       how sure the selector was, 0.0–1.0
r.attested         # False      whether the stem is in the corpus lexicon
r.rules_applied    # ('+ه',)    which rules took part
r.trace            # "strip ('+ه',) -> 'بېکار' (rule evidence, not in lexicon)"
```

## Stemming a dataset

A stemmer takes a word. The usual input is a column of words — a vocabulary, a
frequency list, the output of a tokeniser.

```python
rows = st.stem_file("words.csv")
rows[0]        # {'word': 'کورونه', 'frequency': '1420', 'word_stemmed': 'کور'}

st.stem_file("words.csv", out="stemmed.csv")
#  -> {'rows': 14, 'column': 'word_stemmed', 'out': 'stemmed.csv'}
```

No `out` and you get the rows back; an `out` and the file is written and you
get a summary. Originals are never touched — the stems go in a new column
beside them.

### `stem_file` parameters

| parameter | default | |
|---|---|---|
| `path` | — | `.csv`, `.tsv`, `.txt`, `.xlsx` or `.xlsm` |
| `column` | `"word"` | which column to stem |
| `out` | `None` | where to write; `None` returns the rows |
| `keep_original` | `True` | `False` → only the stem column |
| `new_column` | `None` | default `<column>_stemmed` |
| `sheet` | `None` | which Excel worksheet; `None` → the first |
| `unique` | `False` | stem each distinct value once and map it back; every row is still written |
| `trace` | `False` | add a `<column>_rules` column naming the rules that fired |
| `warn` | `True` | warn once if the cells hold sentences rather than words |

```python
# only the stems, distinct values, with the rules that fired
st.stem_file("words.xlsx", column="لغت", sheet="Sheet2",
             keep_original=False, unique=True, trace=True,
             out="stems.csv")
```

A delimited file with an `out` is streamed, so size is not a limit — 200,000
rows takes under a second. Excel is read into memory.

With pandas, if you would rather hold the file yourself:

```python
df["stem"] = df["word"].apply(st.stem)
```

## Command line

```bash
pashto-stem کورونه خبرونه افغانستان          # کور  خبر  افغان
pashto-stem --file article.txt
pashto-stem کورونه --trace
echo "د کورونو خبرونه" | pashto-stem
pashto-stem --csv words.csv --column word --out stemmed.csv
```

**Input**

| flag | |
|---|---|
| `-f`, `--file PATH` | stem every token in a UTF-8 text file |
| `-c`, `--csv`, `--excel`, `--table PATH` | stem one column of a CSV, TSV or Excel file |
| `--column NAME` | which column to stem (default `word`) |
| `--sheet NAME` | which worksheet of an `.xlsx` file |

**Output**

| flag | |
|---|---|
| `--out PATH` | where to write (default stdout) |
| `--new-column NAME` | name for the stem column |
| `--only-stems` | write just the stem column |
| `--unique` | stem each distinct value once; every row is still written |
| `-t`, `--trace` | also report the confidence and the rules that fired |
| `-q`, `--quiet` | suppress the sentences-in-cells warning |

**Behaviour** — every default is the library's default, so the command line
and the API give the same answer for the same word.

| flag | default | |
|---|---|---|
| `--lemmatize` | off | turn on the irregular-verb dictionary: `شو → کېدل`. This substitutes one word for another, which is lemmatization, not stemming |
| `--no-dict` | lexicon on | stop using the corpus lexicon to score candidates |
| `--no-exceptions` | on | drop stopwords, the length rules and the Arabic-plural list |
| `--no-prefixes` | on | do not strip prefixes |
| `--no-suffixes` | on | do not strip suffixes |
| `--no-derivational` | on | strip inflection only, leaving derivation in place |
| `--pos` | off | enable the part-of-speech filter |
| `--compound` | off | enable compound decomposition |
| `--max-passes N` | `1` | re-run the pipeline on its own output N times |

## Stemming or lemmatization

**Stemming removes characters.** The output is a class label, not a word —
`پوهنتون → پوهن`, as Porter gives *relat* for *relational*. That is correct
behaviour, not a defect.

**Lemmatization substitutes one word for another.** `شو → کېدل` cannot be
reached by removing characters. The irregular-verb dictionary does exactly
this, so it is off by default and offered as an explicit mode:

```python
from pashto_stemmer.stemmer import PashtoStemmer, StemmerConfig

lem = PashtoStemmer(StemmerConfig(use_verb_dictionary=True))
lem.stem("شو")      # 'کېدل'  — a lemma, not a stem
```

## Changing the behaviour

```python
st = PashtoStemmer(StemmerConfig(use_pos=True, max_passes=2))
```

| field | default | |
|---|---|---|
| `use_dictionary` | `True` | score candidates against the corpus lexicon |
| `use_exceptions` | `True` | stopwords, the length rules, Arabic plurals |
| `use_verb_dictionary` | `False` | the lemmatization mode |
| `use_prefixes` | `True` | strip prefixes |
| `use_suffixes` | `True` | strip suffixes |
| `strip_derivational` | `True` | `False` → inflection only |
| `use_pos` | `False` | part-of-speech filtering |
| `use_compound` | `False` | compound decomposition |
| `max_passes` | `1` | passes over the pipeline |
| `min_base_freq` | `3` | sightings needed before an unstripped word counts as a base |
| `uniform_min_stem` | `3` | shortest stem the `‑توب` group may leave |
| `freeze_proper_nouns` | `False` | `True` keeps `افغانستان` whole |
| `strip_stan` | `True` | strip `‑ستان` |
| `author_rules` | `True` | the length rules R1 and R2 |
| `r1_max_len` | `5` | longest word R1 takes a final letter off |
| `keep_negation_prefixes` | `True` | `ناقانونه → ناقانون`, not `قانون` |

The defaults are the configuration every published figure was measured with.
Two switches look like free accuracy on the development set and are not:
`use_pos=True` gains 0.30 points there and loses 0.41 on held-out text;
`r1_max_len=6` gains 0.78 and loses 0.61.

Normalization has its own config, and the setting worth knowing is that no yeh
letter is ever rewritten:

```python
from pashto_stemmer.normalizer import Normalizer, NormalizerConfig
nz = Normalizer(NormalizerConfig(apply_nfkc=True))   # the default
```

`apply_nfkc=True` folds Arabic presentation forms (`ﻛ` → `ک`) and is verified
safe for all five yeh letters and the nine Pashto-only consonants.

## Results

Exact-match accuracy, with Paice's under-stemming index. The *affixed* column
is the half of the data that actually needs a strip — the honest test, since a
stemmer that modifies nothing already scores 47.77% on Pashto word types.

| system | development | affixed | held-out | UI |
|---|---:|---:|---:|---:|
| modifies nothing | 47.77% | 0.0% | 37.27% | 1.000 |
| Aslamzai & Saad (2015) | 50.68% | 12.2% | 40.48% | 0.919 |
| **this stemmer** | **81.19%** | **81.0%** | **72.75%** | **0.291** |

On two independently annotated external word lists, 5,000 and 10,000 types
neither produced by this project: **72.30%** and **70.18%**.

Every figure is reproducible from the repository —
`python experiments/reproduce_paper.py`.

## Limitations

- **Word types, not running text.** No retrieval evaluation is reported, so
  the relationship between these gains and downstream performance is untested.
- **The corpus lexicon is the limiting factor.** Where the right stem is not
  in the word list, the system keeps the word whole or over-strips:
  `چینایي → چینایي`, `الماني → الم`.
- **Citations are located, not page-verified.** 112 of 118 rules cite Tegey &
  Robson by chapter or Penzl by section; the remaining six are entries the
  engine never applies. Of the 38 irregular verbs, 15 are unverified against a
  printed grammar and are marked as such.
- **28 of the 118 rules are documented and deliberately never applied**,
  each with the measurement that overruled the grammar.

## Links

- [Repository, data and the paper](https://github.com/Khairullah-Ibrahim-Khail/Pashto_Stemmer)
- [How the affixes were surveyed](https://github.com/Khairullah-Ibrahim-Khail/Pashto_Stemmer/blob/main/docs/01_affix_inventory.md)
- [What counts as a stem, and why](https://github.com/Khairullah-Ibrahim-Khail/Pashto_Stemmer/blob/main/docs/02_annotation_policy.md)
- [Contributing](https://github.com/Khairullah-Ibrahim-Khail/Pashto_Stemmer/blob/main/CONTRIBUTING.md)
- [Issues](https://github.com/Khairullah-Ibrahim-Khail/Pashto_Stemmer/issues)

## Citing

```bibtex
@mastersthesis{pashto-stemmer,
  title  = {A Grammar-Driven Rule-Based Stemmer for Pashto},
  author = {Khairullah Ibrahim Khail},
  school = {Institute of Management Sciences, Peshawar},
  year   = {2026}
}
```

MIT licensed.
