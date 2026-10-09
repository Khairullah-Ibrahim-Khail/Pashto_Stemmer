# -*- coding: utf-8 -*-
"""
reproduce_paper.py
==================
Regenerates every number in the paper's result tables from the released data,
so that each one can be checked rather than taken on trust.

    python experiments/reproduce_paper.py

It prints, in order:

    Table V    the two evaluation protocols on the held-out set
    Table VI   the held-out evaluation
    Table VII  the development set
    Table VIII the component study

All four score only the *stemming* rows. A row whose reference is a different
word rather than a truncation -- an Arabic broken plural, a suppletive verb
form -- is outside what a truncating stemmer can do, and is counted separately.
"""
from __future__ import annotations

import csv
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pashto_stemmer.baseline import AslamzaiBaseline            # noqa: E402
from pashto_stemmer.metrics import paice                        # noqa: E402
from pashto_stemmer.normalizer import Normalizer                # noqa: E402
from pashto_stemmer.prefixes import PREFIX_RULES                # noqa: E402
from pashto_stemmer.stemmer import PashtoStemmer, StemmerConfig  # noqa: E402
from pashto_stemmer.suffixes import SUFFIX_RULES                # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEV = os.path.join(ROOT, "dataset", "pashto_gold_corrected_v2.csv")
HELD = os.path.join(ROOT, "dataset", "test_500_news_corrected.csv")

FOLD = str.maketrans({"ي": "ی", "ې": "ی", "ۍ": "ی", "ئ": "ی", "ے": "ی"})


def fold(s: str) -> str:
    return s.translate(FOLD)


def is_stemming_row(word: str, stem: str) -> bool:
    """Can the reference be reached by removing characters from the word?

    Stemming removes material from the edges of a word; it cannot insert.
    Where the reference is an Arabic broken plural or a suppletive form
    (اثارو→اثر، نجونو→نجلۍ), the answer is a lemma that no affix rule can
    produce, and those rows belong to lemmatization.

    The test is substring containment, not a prefix or suffix test. An earlier
    version asked only whether the reference was at one end, which excluded
    forms stripped at both ends -- وښيي→ښي, رارسېدو→رسېد, where a perfective
    prefix and a verbal ending both come off. Those are removals like any
    other, and excluding them dropped 26 held-out rows that this system gets
    wrong, which flattered the result by 3.9 points. Comparison ignores which
    of the five yeh letters is written, since that is a spelling difference
    between registers and not an affix.
    """
    w, s = fold(word), fold(stem)
    return bool(s) and s in w



# --------------------------------------------------------------------------- #
def load(path, word_col, stem_col):
    nz = Normalizer()
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    pairs = []
    for r in rows:
        w, s = (r.get(word_col) or "").strip(), (r.get(stem_col) or "").strip()
        if w and s:
            pairs.append((nz.normalize_token(w), nz.normalize_token(s)))
    stemming = [p for p in pairs if is_stemming_row(*p)]
    return pairs, stemming


def split(pairs):
    """(types the reference strips, types it leaves alone)."""
    affixed = [(w, s) for w, s in pairs if w != s]
    bare = [(w, s) for w, s in pairs if w == s]
    return affixed, bare


def acc(pairs, fn):
    """Protocol A: the reference is fixed in advance and the match is exact.

    Folding is used to decide whether a row belongs to the stemming task at
    all, because that is a question about the register the word is written in.
    It is not used here: a stemmer that returns the right letters in the wrong
    yeh has not returned the reference.
    """
    if not pairs:
        return float("nan")
    return sum(1 for w, s in pairs if fn(w) == s) / len(pairs)


def groups_of(pairs):
    g = defaultdict(list)
    for w, s in pairs:
        g[s].append(w)
    return dict(g)


# --------------------------------------------------------------------------- #
# Protocol B: a judge is shown the output and asked whether it is an acceptable
# analysis. We make that reproducible by counting an output as acceptable when
# nothing was removed that is not a documented affix, and by treating an
# unchanged word as acceptable, which is how a judge shown one would score it.
AFFIXES = {fold(r.affix): r.side for r in list(SUFFIX_RULES) + list(PREFIX_RULES)}


def judged_acceptable(word: str, out: str) -> bool:
    w, o = fold(word), fold(out)
    if w == o:
        return True
    if not o or len(o) >= len(w):
        return o in AFFIXES
    if w.startswith(o):
        return w[len(o):] in AFFIXES
    if w.endswith(o):
        return w[:len(w) - len(o)] in AFFIXES
    return False


def protocol_b(pairs, fn):
    return sum(1 for w, _ in pairs if judged_acceptable(w, fn(w))) / len(pairs)


def modified(pairs, fn):
    return sum(1 for w, _ in pairs if fn(w) != w) / len(pairs)


# --------------------------------------------------------------------------- #
def row(name, pairs, fn, bold=False):
    affixed, bare = split(pairs)
    g = groups_of(pairs)
    pr = paice(g, fn)
    mark = "*" if bold else " "
    return (f"{mark}{name:24} {acc(pairs, fn):7.2%} {acc(affixed, fn):8.1%} "
            f"{acc(bare, fn):7.1%} {pr.ui:7.3f} {pr.oi:9.5f}")


def header(title):
    print(f"\n{title}")
    print(f" {'system':24} {'accuracy':>7} {'affixed':>8} {'bare':>7} "
          f"{'UI':>7} {'OI':>9}")
    print(" " + "-" * 66)


def main() -> int:
    dev_all, dev = load(DEV, "word", "stem")
    held_all, held = load(HELD, "word", "expert_stem")

    ours = PashtoStemmer().stem
    base = AslamzaiBaseline().stem
    nothing = lambda w: w                                        # noqa: E731

    print(f"development set : {len(dev_all)} types, {len(dev)} stemming, "
          f"{len(dev_all) - len(dev)} lemma")
    print(f"held-out set    : {len(held_all)} types, {len(held)} stemming, "
          f"{len(held_all) - len(held)} lemma")

    # ---- Table V: the two protocols on the held-out set --------------------
    print("\nTABLE V  the same held-out types under both protocols")
    print(f" {'system':24} {'A: exact':>9} {'B: judged':>10} {'modified':>9}")
    print(" " + "-" * 56)
    for name, fn in (("Modifies nothing", nothing),
                     ("Aslamzai & Saad", base),
                     ("Proposed", ours)):
        print(f" {name:24} {acc(held, fn):8.2%} {protocol_b(held, fn):10.2%} "
              f"{modified(held, fn):9.1%}")

    # ---- Tables VI and VII -------------------------------------------------
    header("TABLE VI  held-out evaluation")
    for name, fn in (("Modifies nothing", nothing),
                     ("Aslamzai & Saad", base),
                     ("Proposed", ours)):
        print(row(name, held, fn, bold=(name == "Proposed")))

    header("TABLE VII  development set")
    for name, fn in (("Modifies nothing", nothing),
                     ("Aslamzai & Saad", base),
                     ("Proposed", ours)):
        print(row(name, dev, fn, bold=(name == "Proposed")))

    # ---- Table VIII: the component study -----------------------------------
    configs = [
        ("Full system",             StemmerConfig()),
        ("- suffix rules",          StemmerConfig(use_suffixes=False)),
        ("- length rules",          StemmerConfig(author_rules=False)),
        ("- corpus lexicon",        StemmerConfig(use_dictionary=False)),
        ("- uniform-strip group",   StemmerConfig(uniform_strip=())),
        ("- prefix rules",          StemmerConfig(use_prefixes=False)),
        ("+ verb dictionary",       StemmerConfig(use_verb_dictionary=True)),
    ]
    print("\nTABLE VIII  each component removed in turn")
    print(f" {'configuration':24} {'development':>20} {'held-out':>20}")
    print(" " + "-" * 66)
    full_d = full_h = None
    for name, cfg in configs:
        fn = PashtoStemmer(cfg).stem
        d, h = acc(dev, fn), acc(held, fn)
        if full_d is None:
            full_d, full_h = d, h
            print(f" {name:24} {d:19.2%} {h:19.2%}")
        else:
            print(f" {name:24} {d:12.2%} ({(d - full_d) * 100:+5.2f}) "
                  f"{h:12.2%} ({(h - full_h) * 100:+5.2f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
