# -*- coding: utf-8 -*-
"""Tests for PashtoLexicon. Run: python pashto_stemmer/tests/test_dictionary.py"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pashto_stemmer.dictionary import PashtoLexicon  # noqa: E402
from pashto_stemmer.normalizer import Normalizer      # noqa: E402


def _small_lex():
    lex = PashtoLexicon(normalizer=Normalizer())
    lex.update([("افغانستان", 100), ("افغان", 40), ("افغانانو", 8),
                ("کور", 30), ("کورونه", 5), ("مرګ", 12), ("ژوبله", 7),
                ("دی؟", 130)])  # punctuation must be cleaned on load
    return lex


def test_membership_and_freq():
    lex = _small_lex()
    assert lex.contains("افغان")
    assert lex.frequency("افغانستان") == 100
    assert not lex.contains("قققققق")


def test_punctuation_cleaned_on_add():
    lex = _small_lex()
    assert lex.contains("دی")          # ؟ stripped
    assert not lex.contains("دی؟")


def test_kaf_variant_conflates():
    lex = _small_lex()
    # query with Arabic kaf ك must hit the keheh-normalized entry کور
    assert lex.contains("كور")


def test_score_monotonic_and_bounded():
    lex = _small_lex()
    # دی؟ -> دی at freq 130 is the most frequent entry, so it scores 1.0
    assert lex.score("دی") == 1.0
    assert 0.0 < lex.score("افغانستان") < 1.0    # 100 < 130
    assert lex.score("افغان") < lex.score("افغانستان")   # 40 < 100
    assert lex.score("unknownword") == 0.0


def test_longest_valid_prefix_for_compound():
    lex = _small_lex()
    # مرګ + ژوبله ; مرګ is a word and a prefix of the compound
    assert lex.longest_valid_prefix("مرګژوبله") == "مرګ"


def test_prefix_walk_sorted_by_freq():
    lex = _small_lex()
    res = lex.words_with_prefix("افغان", limit=10)
    words = [w for w, _ in res]
    assert words[0] == "افغانستان"                # highest freq first
    assert "افغان" in words


def test_real_file_loads():
    lex = PashtoLexicon.from_frequency_file()
    assert len(lex) > 4000
    assert lex.contains("افغانستان")


def _run_all():
    fns = [g for n, g in globals().items() if n.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn(); print(f"  PASS  {fn.__name__}"); passed += 1
        except AssertionError as e:
            print(f"  FAIL  {fn.__name__}: {e}")
        except Exception as e:  # e.g. missing file
            print(f"  ERROR {fn.__name__}: {e}")
    print(f"\n{passed}/{len(fns)} passed")
    return passed == len(fns)


if __name__ == "__main__":
    sys.exit(0 if _run_all() else 1)
