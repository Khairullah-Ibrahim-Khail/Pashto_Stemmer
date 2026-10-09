# -*- coding: utf-8 -*-
"""
evaluate_external.py
====================
Runs the stemmer against the two independently annotated word lists in
dataset/external/, and reproduces Table IX of the paper.

    python experiments/evaluate_external.py

Neither list was produced by this project. They are reported as a test of
whether the system generalises beyond the data it was built against, not as a
measure of correctness under this project's annotation policy -- they follow a
different one, which the script also quantifies.

Two comparisons are printed. Exact match requires the stem to agree character
for character. The folded comparison treats the five yeh letters as equal
*when comparing only*; the stemmer's output is never rewritten. Both lists
normalise their reference column to ی while leaving ي in the word column, so
without the folded figure a correct stem is scored wrong for keeping the letter
the word actually has.
"""
from __future__ import annotations

import csv
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pashto_stemmer.baseline import AslamzaiBaseline                 # noqa: E402
from pashto_stemmer.normalizer import Normalizer                     # noqa: E402
from pashto_stemmer.stemmer import PashtoStemmer                     # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXT = os.path.join(ROOT, "dataset", "external")
GOLD = os.path.join(ROOT, "dataset", "pashto_gold_corrected_v2.csv")
HELD = os.path.join(ROOT, "dataset", "test_500_news_corrected.csv")

FOLD = str.maketrans({"ي": "ی", "ې": "ی", "ۍ": "ی", "ئ": "ی", "ے": "ی"})
NZ = Normalizer()


def fold(s: str) -> str:
    return s.translate(FOLD)


def load(path, word_col, stem_col):
    out = []
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            w, s = (r.get(word_col) or "").strip(), (r.get(stem_col) or "").strip()
            if w and s:
                out.append((NZ.normalize_token(w), NZ.normalize_token(s)))
    return out


def exact(pairs, fn):
    return sum(1 for w, s in pairs if fn(w) == s) / len(pairs)


def folded(pairs, fn):
    return sum(1 for w, s in pairs if fold(fn(w)) == fold(s)) / len(pairs)


def main() -> int:
    files = [("External, 5,000 types", "pashto_5k_stemmed.csv", "original", "stem"),
             ("External, 10,000 types", "pashto_10k_stemmed.csv", "original", "stem")]
    missing = [f for _, f, _, _ in files if not os.path.exists(os.path.join(EXT, f))]
    if missing:
        print("missing from dataset/external/:", ", ".join(missing))
        return 1

    ours = PashtoStemmer().stem
    base = AslamzaiBaseline().stem
    gold = {w: s for w, s in load(GOLD, "word", "stem")}
    held = {w for w, _ in load(HELD, "word", "stem")}

    print(f"{'dataset':26} {'types':>7} {'exact':>8} {'folded':>8} {'gain':>6}")
    print("-" * 60)
    for label, fname, wcol, scol in files:
        pairs = load(os.path.join(EXT, fname), wcol, scol)
        e, f_ = exact(pairs, ours), folded(pairs, ours)
        print(f"{label:26} {len(pairs):7} {e:8.2%} {f_:8.2%} {(f_ - e) * 100:+6.2f}")
        print(f"{'    Aslamzai & Saad':26} {'':7} {exact(pairs, base):8.2%} "
              f"{folded(pairs, base):8.2%}")
        words = {w for w, _ in pairs}
        overlap = len(words & set(gold)) + len(words & held)
        m = dict(pairs)
        shared = sorted(set(m) & set(gold))
        same = sum(1 for w in shared if m[w] == gold[w])
        print(f"{'':26} {'':7} overlap with our sets {overlap} "
              f"({overlap / len(pairs):.1%}); of the {len(shared)} words shared with "
              f"our development reference, {same} agree ({same / len(shared):.1%})")

    print()
    for label, path, wcol, scol in (("Our held-out set", HELD, "word", "stem"),
                                    ("Our development set", GOLD, "word", "stem")):
        from reproduce_paper import is_stemming_row          # noqa: E402
        pairs = [p for p in load(path, wcol, scol) if is_stemming_row(*p)]
        e, f_ = exact(pairs, ours), folded(pairs, ours)
        print(f"{label:26} {len(pairs):7} {e:8.2%} {f_:8.2%} {(f_ - e) * 100:+6.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
