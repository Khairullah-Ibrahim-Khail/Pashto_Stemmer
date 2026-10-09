# -*- coding: utf-8 -*-
"""
prefixes.py
===========
Pashto prefix inventory.

Pashto has far fewer productive derivational prefixes than suffixes. We keep
this list deliberately conservative — spurious prefix stripping is a common
source of over-stemming (the baseline's Rule 6 blindly strips a leading ز!).
The lexicon validator gates every strip, but a tight inventory reduces the
candidate explosion.

Verbal deictic/directional prefixes (را/ور/در) and the perfective و are
included but marked with a high min_stem_len because they are single/short
and easy to over-apply; validation must confirm the result is a real word.
"""

from __future__ import annotations

from typing import List

from .rules import AffixRule


def _p(affix, category, add_back="", min_stem_len=3, pos=(), note="",
       productivity="productive", confidence="high", strip_allowed="yes"):
    return AffixRule(affix=affix, side="prefix", category=category,
                     add_back=add_back, min_stem_len=min_stem_len,
                     pos=tuple(pos), note=note, productivity=productivity,
                     confidence=confidence, strip_allowed=strip_allowed)


_DERIVATIONAL: List[AffixRule] = [
    _p("نا", "derivational", min_stem_len=3, pos=("ADJ", "N"), strip_allowed="no",
       note="[T&R ch.5 prefixed adjectives] KEPT, not stripped: the gold "
            "correction log records the negated form as its own lexeme "
            "(ناقانونه→ناقانون، ناوړه→ناوړ). Only the agreement ending is removed."),
    _p("بې", "derivational", min_stem_len=3, pos=("ADJ", "N"), strip_allowed="no",
       note="[T&R ch.5 prefixed adjectives] KEPT, not stripped: the negated form "
            "is its own lexeme. Only the agreement ending is removed."),
    _p("لا", "derivational", min_stem_len=3, productivity="borrowed",
       confidence="medium",
       note="[T&R ch.2 Arabic/Persian bound morphemes] [inv §1.1] privative in "
            "Arabic learned formations: لاانتها"),
    # --- added from docs/pashto_affix_inventory new finale .md §1.1 -------- #
    _p("بیا", "derivational", min_stem_len=3, pos=("V", "N"),
       note="[T&R ch.7 adverbs] [inv §1.1] repetition: بیاجوړول→جوړول"),
    _p("غیر", "derivational", min_stem_len=3, pos=("ADJ",), productivity="borrowed",
       strip_allowed="no",
       note="[T&R ch.2 morphological borrowings] KEPT, not stripped: the gold "
            "correction log records the negated form as its own lexeme "
            "(غیرقانونی→غیرقانون). Only the agreement ending is removed."),
    _p("بلا", "derivational", min_stem_len=3, pos=("ADJ",), productivity="borrowed",
       confidence="medium",
       note="[T&R ch.5 intensive modifiers] [inv §1.1] without (Arabic, "
            "restricted): بلاشرطه→شرطه"),
    _p("نیم", "derivational", min_stem_len=3, pos=("ADJ", "N"),
       productivity="restricted",
       note="[T&R ch.5 numbers and modifiers] [inv §1.1] half: نیمګړی→ګړی"),
    _p("سر", "derivational", min_stem_len=4, pos=("N",), productivity="restricted",
       confidence="medium", strip_allowed="no",
       note="[T&R ch.4 nominal compounding] [inv §1.1] head/chief (سرمنشي→منشي). "
            "NOT stripped: سر is a free noun and the prefix reading cannot be told "
            "from a compound, so it removed سر from ordinary words."),
    _p("ضد", "derivational", min_stem_len=3, pos=("N",), productivity="borrowed",
       confidence="medium",
       note="[T&R ch.2 modern loan vocabulary] [inv §1.1] anti- (Arabic); often "
            "written separately: ضد انقلاب"),
]

_LOAN_DERIVATIONAL: List[AffixRule] = [
    # ‑پر REMOVED: it false-strips ordinary words (پراختیا→اختیا،
    # پروګرام، پرېکړه). A prefix this short needs lexical support we
    # do not have, so it is not a safe rule.

    _p("هم",  "derivational", min_stem_len=3, note="[T&R ch.2 Persian compounds] co-/fellow: همکار→کار"),
]

_VERBAL_INFLECTIONAL: List[AffixRule] = [
]

# Only the genuine DERIVATIONAL prefixes are kept. The verbal particles and
# single-letter prefixes (و‑، را‑، ور‑، در‑، پرې‑، وا‑، کم‑ …) were measured
# against the author's gold and against held-out news text and came out right
# between 13% and 50% of the time. They cannot be told apart from a
# word-initial letter of the root (بېجينګ, لانسیټ, رارسېدو), so they cost more
# than they returned and were dropped.
PREFIX_RULES: List[AffixRule] = sorted(
    _DERIVATIONAL + _LOAN_DERIVATIONAL + _VERBAL_INFLECTIONAL,
    key=lambda r: -len(r.affix),
)


if __name__ == "__main__":
    for r in PREFIX_RULES:
        print(f"  {r.affix:5} {r.category:13} min={r.min_stem_len} "
              f"pos={','.join(r.pos) or '-':6} {r.note}")
    print(f"\n{len(PREFIX_RULES)} prefix rules")
