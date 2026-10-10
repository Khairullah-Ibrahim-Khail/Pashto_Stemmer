# -*- coding: utf-8 -*-
"""
pos_rules.py
============
Lightweight, rule-based part-of-speech guessing to *constrain* affix
stripping. There is no statistical tagger here (the project is 100%
rule-based) — instead the coarse POS a word's ending signals is read off the
surface, and the rule engine may apply only affixes compatible with it.

Why this helps
--------------
Over-generation is the enemy of a candidate-based stemmer. A verbal
infinitive suffix (ل) should not be tried on an obvious noun plural
(کورونه). By tagging a likely POS from surface cues and filtering the
affix inventory to matching POS (plus POS-agnostic affixes), the candidate
set shrinks, runtime falls, and spurious strips become less likely.

The guesser returns a *set* of plausible POS (coarse: N, ADJ, V) because
Pashto endings are ambiguous; the lexicon validator still makes the final
call. This module is switchable (the "+POS" ablation arm in Phase 5).
"""

from __future__ import annotations

from typing import FrozenSet, Set

N, ADJ, V = "N", "ADJ", "V"
_ALL: FrozenSet[str] = frozenset({N, ADJ, V})

# Surface-ending cues -> plausible POS. Longest cues first at match time.
_VERB_ENDINGS = ("ېدل", "ېده", "ول", "لو", "ل", "ئ")
_NOUN_ENDINGS = ("ونه", "ونو", "ګانو", "ګانې", "ګان", "انو", "تون", "توب",
                 "تیا", "والی", "ان", "ون")
_ADJ_ENDINGS = ("ونکی", "والو", "یز", "یزو", "ین", "ور", "ي", "ی")
_FEM_ENDINGS = ("ه", "ې", "ۍ")   # feminine noun/adj markers


def guess_pos(token: str) -> FrozenSet[str]:
    """
    Return the set of plausible coarse POS tags for ``token`` based on its
    ending. Falls back to all POS when nothing matches (so no rule is
    wrongly excluded).
    """
    pos: Set[str] = set()

    for suf in _VERB_ENDINGS:
        if token.endswith(suf):
            pos.add(V)
            break
    for suf in _NOUN_ENDINGS:
        if token.endswith(suf):
            pos.add(N)
            break
    for suf in _ADJ_ENDINGS:
        if token.endswith(suf):
            pos.add(ADJ)
            break
    for suf in _FEM_ENDINGS:
        if token.endswith(suf):
            pos.update({N, ADJ})
            break

    return frozenset(pos) if pos else _ALL


def compatible(rule_pos, allowed_pos) -> bool:
    """
    A rule is compatible if it is POS-agnostic (empty rule_pos) or shares at
    least one POS with the allowed set.
    """
    if not rule_pos:
        return True
    return bool(set(rule_pos) & set(allowed_pos))


if __name__ == "__main__":
    for w in ["کورونه", "کول", "ښکلی", "ناروغۍ", "خبرونه", "پراختیا"]:
        print(f"  {w:10} -> {sorted(guess_pos(w))}")
