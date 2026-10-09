# -*- coding: utf-8 -*-
"""
agreement.py
============
Inter-annotator agreement on the development set.

Three native speakers annotated the 2,912 word types independently: the author,
the principal of a Pashto-medium school, and a university teacher of Pashto.
Their individual passes are in dataset/annotations/ and dataset/, and this
script compares them.

    python experiments/agreement.py

Two views are reported. The first treats the whole stem string as the label,
which is the strict reading: two annotators agree only if they produce exactly
the same characters. The second collapses the judgement to the decision that
matters most -- did this word carry an affix at all -- and is the figure
comparable with binary annotation tasks elsewhere.

Chance agreement on the stem string is near zero, because the label space is
every substring of the word, so Cohen's kappa and raw agreement almost
coincide there. On the binary decision chance agreement is about 0.5, and the
kappa is the meaningful number.
"""
from __future__ import annotations

import csv
import itertools
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pashto_stemmer.normalizer import Normalizer                 # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NZ = Normalizer()

# The author's own pass is not included. An early file exists but was produced
# quickly and was superseded; treating it as an independent annotation would
# overstate what can be evidenced. The two passes below are the ones that were
# annotated carefully and retained, and the released reference is the author's
# adjudication of them.
PASSES = {
    "school principal": os.path.join(ROOT, "dataset", "annotations",
                                     "annotator_school_principal.csv"),
    "university tutor": os.path.join(ROOT, "dataset", "annotations",
                                     "annotator_university_teacher.csv"),
}
REFERENCE = os.path.join(ROOT, "dataset", "pashto_gold_corrected_v2.csv")


def load(path):
    out = {}
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            w = (r.get("word") or "").strip()
            s = (r.get("stem") or "").strip()
            if w and s:
                out[NZ.normalize_token(w)] = NZ.normalize_token(s)
    return out


def kappa(a_lab, b_lab):
    """Cohen's kappa for two aligned label sequences."""
    n = len(a_lab)
    po = sum(1 for x, y in zip(a_lab, b_lab) if x == y) / n
    ca, cb = Counter(a_lab), Counter(b_lab)
    pe = sum(ca[c] / n * cb[c] / n for c in set(ca) | set(cb))
    k = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    return n, po, pe, k


def report(passes, label_fn, title):
    print(f"\n{title}")
    print(f"  {'pair':38} {'n':>5} {'agreement':>10} {'chance':>8} {'kappa':>7}")
    print("  " + "-" * 72)
    for a, b in itertools.combinations(passes, 2):
        A, B = passes[a], passes[b]
        shared = sorted(set(A) & set(B))
        n, po, pe, k = kappa([label_fn(w, A[w]) for w in shared],
                             [label_fn(w, B[w]) for w in shared])
        print(f"  {a + ' vs ' + b:38} {n:5} {po:10.2%} {pe:8.4f} {k:7.4f}")


def main() -> int:
    missing = [n for n, p in PASSES.items() if not os.path.exists(p)]
    if missing:
        print("missing annotation passes:", ", ".join(missing))
        return 1
    passes = {n: load(p) for n, p in PASSES.items()}
    for n, d in passes.items():
        print(f"{n:20} {len(d)} types")

    report(passes, lambda w, s: s, "EXACT STEM STRING")
    report(passes, lambda w, s: "keep" if w == s else "strip",
           "BINARY DECISION: does this word carry an affix at all")

    # How close the adjudicated reference stays to each annotator.
    ref = load(REFERENCE)
    print("\nTHE RELEASED REFERENCE AGAINST EACH PASS")
    for n, d in passes.items():
        shared = sorted(set(d) & set(ref))
        same = sum(1 for w in shared if d[w] == ref[w])
        print(f"  {n:20} {same:5} of {len(shared):5} identical ({same/len(shared):.2%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
