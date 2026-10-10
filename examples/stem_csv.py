# -*- coding: utf-8 -*-
"""
stem_csv.py — stemming a word list.

    python examples/stem_csv.py

A stemmer takes a word and returns its stem. Tokenisation belongs upstream, so
the normal input is a column of words: a vocabulary, a frequency list, the
output of a tokeniser. This runs on sample_words.csv beside it.

The same job without writing any code:

    pashto-stem --csv examples/sample_words.csv --column word --out stemmed.csv
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pashto_stemmer import PashtoStemmer                       # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
st = PashtoStemmer()

# No `out=`, so nothing is written: the rows come back and you decide.
rows = st.stem_file(os.path.join(HERE, "sample_words.csv"), column="word")

print(f"{'word':14}{'stem':14}{'frequency':>10}")
print("-" * 38)
for r in rows:
    print(f"{r['word']:14}{r['word_stemmed']:14}{r['frequency']:>10}")

# Words the stemmer deliberately leaves alone are as much the point as the
# ones it cuts: کورس is a loanword, not کور + س.
unchanged = [r["word"] for r in rows if r["word"] == r["word_stemmed"]]
print(f"\nleft unchanged: {', '.join(unchanged)}")

# Why a particular word came out the way it did.
r = st.stem_word("ښوونځیو")
print(f"\nښوونځیو -> {r.stem}   rules {r.rules_applied}   "
      f"confidence {r.confidence:.2f}")

# Writing it out is one more call, and only happens because you asked.
out = os.path.join(HERE, "sample_words_stemmed.csv")
info = st.stem_file(os.path.join(HERE, "sample_words.csv"),
                    column="word", out=out)
print(f"\nwrote {info['rows']} rows to {os.path.basename(info['out'])}")
