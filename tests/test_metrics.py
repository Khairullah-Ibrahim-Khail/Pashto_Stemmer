# -*- coding: utf-8 -*-
"""Tests for metrics. Run: python tests/test_metrics.py"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pashto_stemmer.metrics import intrinsic_metrics, accuracy, paice


def test_accuracy():
    pairs = [("کورونه", "کور"), ("خبرونه", "خبر")]
    assert accuracy(pairs, lambda w: "کور" if w == "کورونه" else "خبر") == 1.0
    assert accuracy(pairs, lambda w: w) == 0.0


def test_intrinsic_icf_and_unchanged():
    words = ["کورونه", "کورونو", "کور"]
    rep = intrinsic_metrics(words, lambda w: "کور")  # collapse all to one
    assert rep.n_stems == 1
    assert abs(rep.icf - (3 - 1) / 3) < 1e-9
    assert rep.unchanged_rate == 1 / 3   # only "کور" unchanged


def test_paice_perfect_stemmer():
    # gold: two concepts; a perfect stemmer merges within, not across.
    groups = {"کور": ["کورونه", "کورونو", "کور"], "خبر": ["خبرونه", "خبر"]}
    def perfect(w):
        return "کور" if "کور" in w else "خبر"
    pr = paice(groups, perfect)
    assert pr.ui == 0.0   # no missed merges
    assert pr.oi == 0.0   # no wrong merges


def test_paice_understemmer():
    groups = {"کور": ["کورونه", "کور"]}
    pr = paice(groups, lambda w: w)   # never conflates
    assert pr.ui == 1.0               # all desired merges missed


def _run():
    fns = [g for n, g in globals().items() if n.startswith("test_")]
    ok = 0
    for fn in fns:
        try:
            fn(); print(f"  PASS  {fn.__name__}"); ok += 1
        except AssertionError as e:
            print(f"  FAIL  {fn.__name__}: {e}")
    print(f"\n{ok}/{len(fns)} passed")
    return ok == len(fns)


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
