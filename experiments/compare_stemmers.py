# -*- coding: utf-8 -*-
"""
compare_stemmers.py
===================
Head-to-head on the gold set:

  1. A stemmer that does nothing      - the floor, since many word types
                                        carry no affix at all
  2. Aslamzai & Saad (2015)           - the published nine-rule baseline
  3. Ours without the dictionary      - what the rules alone achieve
  4. Ours, inflection only            - no derivational stripping
  5. Ours, full system

Metrics: exact-match accuracy and Paice's under/over-stemming indices.
"""
from __future__ import annotations
import csv, os, sys
from collections import defaultdict
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pashto_stemmer.stemmer import PashtoStemmer, StemmerConfig
from pashto_stemmer.baseline import AslamzaiBaseline
from pashto_stemmer.metrics import accuracy, paice
from pashto_stemmer.normalizer import Normalizer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GOLD = os.path.join(ROOT, "dataset", "pashto_gold_corrected_v2.csv")



def is_stemming_row(word, stem):
    """Is this row within the stemming task at all?

    Stemming removes characters; it cannot insert them. Where the reference is
    an Arabic broken plural or a suppletive form (اثارو→اثر، نجونو→نجلۍ), the
    answer is a lemma, which no affix rule can produce. Those rows belong to
    lemmatization and are reported separately rather than counted as stemming
    failures. Comparison ignores which of the five yeh letters is written,
    since that is a spelling difference and not an affix.
    """
    fold = str.maketrans({"ي": "ی", "ې": "ی", "ۍ": "ی", "ئ": "ی", "ے": "ی"})
    w, s = word.translate(fold), stem.translate(fold)
    return w.startswith(s) or w.endswith(s)


def main():
    rows = list(csv.DictReader(open(GOLD, encoding="utf-8-sig")))
    # Both sides go through the same normalization the stemmer uses, so a
    # comparison never fails on an encoding variant.
    nz = Normalizer()
    all_pairs = [(nz.normalize_token(r["word"].strip()),
                  nz.normalize_token(r["stem"].strip()))
                 for r in rows if r.get("word") and r.get("stem")]
    pairs = [(w, s) for w, s in all_pairs if is_stemming_row(w, s)]
    lemma = len(all_pairs) - len(pairs)
    groups = defaultdict(list)
    for w, s in pairs:
        groups[s].append(w)
    groups = dict(groups)

    systems = [
        ("Do nothing", lambda w: w),
        ("Aslamzai & Saad (2015)", AslamzaiBaseline().stem),
        ("Ours, no dictionary", PashtoStemmer(
            StemmerConfig(use_dictionary=False)).stem),
        ("Ours, inflection only", PashtoStemmer(
            StemmerConfig(strip_derivational=False)).stem),
        ("Ours, full system", PashtoStemmer().stem),
    ]
    print(f"gold words: {len(all_pairs)}")
    print(f"  stemming rows scored : {len(pairs)}")
    print(f"  lemma rows excluded  : {lemma} "
          f"({lemma / len(all_pairs):.1%}) - the reference is a different word, "
          f"not a truncation\n")
    print(f"{'system':34} {'acc':>7} {'UI':>7} {'OI':>9}")
    print("-" * 60)
    for name, fn in systems:
        pr = paice(groups, fn)
        print(f"{name:34} {accuracy(pairs, fn):6.1%} {pr.ui:7.3f} {pr.oi:9.5f}")


if __name__ == "__main__":
    main()
