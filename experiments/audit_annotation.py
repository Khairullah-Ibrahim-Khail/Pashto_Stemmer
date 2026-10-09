# -*- coding: utf-8 -*-
"""
audit_annotation.py
===================
Compares every removal in an annotated set against the affix inventory.

A removal that matches no documented affix is either an annotation error or
evidence that the inventory is incomplete; only inspection separates the two.
The script reports the counts and writes the unresolved rows to a CSV so they
can be ruled on one by one.

    python experiments/audit_annotation.py

Outputs dataset/unsupported_removals_heldout.csv and
dataset/unsupported_removals_dev.csv.
"""
from __future__ import annotations

import csv
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pashto_stemmer.prefixes import PREFIX_RULES          # noqa: E402
from pashto_stemmer.suffixes import SUFFIX_RULES          # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FOLD = str.maketrans({"ي": "ی", "ې": "ی", "ۍ": "ی", "ئ": "ی", "ے": "ی"})
RULES = list(SUFFIX_RULES) + list(PREFIX_RULES)
AFFIX = {r.affix.translate(FOLD): r for r in RULES}


def fold(s: str) -> str:
    return s.translate(FOLD)


def removal(word: str, stem: str):
    """What was taken off, and from which end. None if the stem is not a cut."""
    w, s = fold(word), fold(stem)
    if not s or w == s:
        return None
    if w.startswith(s):
        return w[len(s):], "suffix"
    if w.endswith(s):
        return w[:len(w) - len(s)], "prefix"
    return None


def audit(path, word_col, stem_col, out_name):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    removals, unsupported = 0, []
    for r in rows:
        w = (r.get(word_col) or "").strip()
        s = (r.get(stem_col) or "").strip()
        cut = removal(w, s)
        if cut is None:
            continue
        removals += 1
        piece, side = cut
        rule = AFFIX.get(piece)
        if rule is not None and rule.side == side:
            continue
        unsupported.append({
            "word": w,
            "annotated_stem": s,
            "removed": piece,
            "side": side,
            "in_inventory": "yes, wrong side" if rule is not None else "no",
            "verdict": "",          # fill in: annotation error | missing affix
        })
    out = os.path.join(ROOT, "dataset", out_name)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(unsupported[0].keys()))
        wr.writeheader()
        wr.writerows(unsupported)
    pct = len(unsupported) / removals if removals else 0
    print(f"{os.path.basename(path):34} {removals:5} removals, "
          f"{len(unsupported):4} unsupported ({pct:.1%})  -> dataset/{out_name}")
    return unsupported


def main() -> int:
    ds = os.path.join(ROOT, "dataset")
    audit(os.path.join(ds, "test_500_news.csv"), "word", "expert_stem",
          "unsupported_removals_heldout_firstpass.csv")
    audit(os.path.join(ds, "test_500_news_corrected.csv"), "word", "expert_stem",
          "unsupported_removals_heldout.csv")
    audit(os.path.join(ds, "pashto_gold_corrected_v2.csv"), "word", "stem",
          "unsupported_removals_dev.csv")
    print("\nThe verdict column is empty on purpose: each row is either an "
          "annotation error\nor an affix the inventory is missing, and only "
          "inspection decides which.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
