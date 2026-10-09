# -*- coding: utf-8 -*-
"""
Tests for the Pashto normalizer.

Run:  python -m pytest pashto_stemmer/tests/test_normalizer.py -v
  or: python pashto_stemmer/tests/test_normalizer.py   (plain assert runner)
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pashto_stemmer.normalizer import Normalizer, NormalizerConfig  # noqa: E402


nz = Normalizer()


def test_removes_tatweel():
    assert nz.normalize("افغانســـتان") == "افغانستان"


def test_unifies_arabic_kaf():
    # ك U+0643 -> ک U+06A9
    assert "ك" not in nz.normalize("پاكستان")
    assert nz.normalize("پاكستان") == "پاکستان"


def test_removes_diacritics():
    assert nz.normalize("مُدَّت") == "مدت"


def test_removes_internal_zwnj():
    assert "‌" not in nz.normalize("کا‌بل")


def test_alef_hamza_folds_but_madda_preserved():
    assert nz.normalize("أحمد") == "احمد"
    assert nz.normalize("آسیا") == "آسیا"   # madda must survive


def test_heh_variants_fold():
    assert nz.normalize("مکتبة") == "مکتبه"


def test_all_five_yeh_are_preserved():
    """Pashto has FIVE yeh and ي (سخته یې) is one of them: it marks masculine
    plural/oblique and the 3rd-person present, while ی marks masculine
    singular direct. Merging them destroys سړی vs سړي, so none are merged."""
    for ch in "يیېۍئ":
        assert nz.normalize(ch) == ch, f"{ch} was altered"
    assert nz.normalize("سړی") != nz.normalize("سړي")   # man vs men
    assert nz.normalize("کوي") == "کوي"                  # 3rd person present


def test_distinct_pashto_yeh_letters_PRESERVED():
    """
    THE critical Pashto invariant: the DISTINCT feminine yeh letters ې and ۍ
    carry gender/number and must NOT be collapsed into ی. Conflating ي→ی does
    not touch them, so masc vs fem stays contrastive.
    """
    assert nz.normalize("ې") == "ې"
    assert nz.normalize("ۍ") == "ۍ"
    # masc (ښکلي→ښکلی), fem (ښکلې), fem2 (ښکلۍ) stay three distinct forms
    forms = {nz.normalize("ښکلي"), nz.normalize("ښکلې"), nz.normalize("ښکلۍ")}
    assert len(forms) == 3, f"yeh forms collapsed: {forms}"


def test_digits_none_default_keeps_persian_digits():
    assert nz.normalize("۱۴۰۵") == "۱۴۰۵"


def test_digits_ascii_option():
    nz2 = Normalizer(NormalizerConfig(digits="ascii"))
    assert nz2.normalize("۱۴۰۵") == "1405"


def test_ablation_unify_yeh_collapses_forms():
    # ablation arm only — measures the damage aggressive folding does
    """The dangerous flag, when explicitly enabled, must collapse — this is
    what we measure the cost of in the ablation study."""
    aggressive = Normalizer(NormalizerConfig(unify_yeh=True))
    forms = {aggressive.normalize("ښکلي"), aggressive.normalize("ښکلې")}
    assert len(forms) == 1


def test_idempotent():
    s = "افغانســـتان پاكستان مُدَّت"
    once = nz.normalize(s)
    assert nz.normalize(once) == once


def test_whitespace_collapse():
    assert nz.normalize("د   افغانستان\n\tخبرونه") == "د افغانستان خبرونه"


def _run_all():
    fns = [g for name, g in globals().items() if name.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {fn.__name__}: {e}")
    print(f"\n{passed}/{len(fns)} passed")
    return passed == len(fns)


if __name__ == "__main__":
    ok = _run_all()
    sys.exit(0 if ok else 1)
