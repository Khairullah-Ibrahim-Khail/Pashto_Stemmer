# -*- coding: utf-8 -*-
"""
rules.py
========
Typed representation of a morphological affix rule + the pure
candidate-generation logic that applies rules to a token.

This replaces the baseline's flat "9 hard-coded rules" with a data-driven
inventory where every affix carries linguistic metadata:

    - side        : 'suffix' | 'prefix'
    - category    : 'inflectional' | 'derivational'
    - add_back    : letters re-attached to the stem after stripping
                    (e.g. ښکلي -> strip ي, add ه  ->  ښکله)
    - min_stem_len: minimum length (in code points) of the surviving stem,
                    a guard against over-stripping short words
    - pos         : POS tag(s) the affix signals (used by pos_rules.py)
    - note        : linguistic note / example (documentation only)

The engine here does NOT decide which candidate is correct — it only
*generates* candidates. Selection is the job of validation.py, which
consults the lexicon. Separating generation from validation is the core
idea we borrow from the Persian/Urdu hybrid stemmers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Yeh folding — for MATCHING ONLY, never for output.
#
# Pashto has five yeh letters and they are morphologically contrastive, so the
# normalizer preserves every one of them. But the SAME suffix is written ي in
# news orthography (لومړي، تاریخي، حکومتي) and ی in the dictionary orthography
# our rule inventory is written in. A rule spelled with ی therefore never fired
# on news text: 118 of 499 held-out news words contain ي, while 0 of the 2912
# gold words do, so the gap was invisible until the news set was annotated.
#
# We therefore compare a folded KEY when deciding whether a rule applies, and
# always slice the ORIGINAL token for the result. No letter is ever rewritten.
_YEH_FOLD = str.maketrans({"ي": "ی", "ې": "ی", "ۍ": "ی", "ئ": "ی"})


def _key(s: str) -> str:
    """Match key: all yeh letters compare equal. Output is never folded."""
    return s.translate(_YEH_FOLD)


@dataclass(frozen=True)
class AffixRule:
    affix: str
    side: str                       # 'suffix' | 'prefix'
    category: str                   # 'inflectional' | 'derivational'
    add_back: str = ""
    min_stem_len: int = 2
    pos: Tuple[str, ...] = ()
    note: str = ""
    # Some affixes are only valid on the ORIGINAL word, never on a stem that
    # has already lost material. The verbal ‑ل is the case: لوستل→لوست is
    # right, but ښکلې→ښکل→ښک strips a ل that is part of the adjective root.
    first_pass_only: bool = False

    # --- fields required by §10 of docs/pashto_affix_inventory new finale .md #
    # productivity: how freely the affix forms new words.
    #   'productive'  - forms new words freely
    #   'restricted'  - forms a limited set
    #   'lexicalized' - survives only in fixed words; must not be stripped
    #   'borrowed'    - Persian, Arabic or Turkic origin
    productivity: str = "productive"
    # confidence in the entry itself. §12.9: an affix with no attested example
    # stays at 'low'.
    confidence: str = "high"
    # §12: whether the rule engine may remove this affix at all.
    #   'yes'          - normal rule
    #   'no'           - documented but never stripped (lexicalized, or unattested)
    #   'lexicon-only' - handled by a dictionary, not by rule
    strip_allowed: str = "yes"

    def __post_init__(self) -> None:
        if self.side not in ("suffix", "prefix"):
            raise ValueError(f"side must be suffix/prefix, got {self.side!r}")
        if self.category not in ("inflectional", "derivational"):
            raise ValueError(f"bad category {self.category!r}")
        if self.productivity not in ("productive", "restricted", "lexicalized",
                                     "borrowed"):
            raise ValueError(f"bad productivity {self.productivity!r}")
        if self.confidence not in ("high", "medium", "low"):
            raise ValueError(f"bad confidence {self.confidence!r}")
        if self.strip_allowed not in ("yes", "no", "lexicon-only"):
            raise ValueError(f"bad strip_allowed {self.strip_allowed!r}")

    # ------------------------------------------------------------------ #
    def applies_to(self, token: str) -> bool:
        """Can this rule fire on ``token`` without violating min_stem_len?

        Matching is done on the yeh-folded key so that a rule written with ی
        also fires on the same suffix written ي/ې/ۍ/ئ. The token itself is
        never modified.
        """
        tk, ak = _key(token), _key(self.affix)
        if self.side == "suffix":
            if not tk.endswith(ak):
                return False
        else:  # prefix
            if not tk.startswith(ak):
                return False
        stem_len = len(token) - len(self.affix) + len(self.add_back)
        return stem_len >= self.min_stem_len

    def apply(self, token: str) -> Optional[str]:
        """Return the stripped form, or None if the rule does not apply."""
        if not self.applies_to(token):
            return None
        if self.side == "suffix":
            base = token[: len(token) - len(self.affix)]
            return base + self.add_back
        else:
            base = token[len(self.affix):]
            return self.add_back + base


@dataclass
class Candidate:
    """One generated stem hypothesis plus its derivation trace."""
    stem: str
    rules_applied: Tuple[str, ...] = ()      # human-readable rule ids
    passes: int = 0
    strip_len: int = 0                        # total chars removed (proxy for aggressiveness)

    def __hash__(self) -> int:
        return hash(self.stem)


class RuleEngine:
    """
    Applies an affix inventory to a token to produce candidate stems.

    Parameters
    ----------
    suffixes, prefixes:
        Ordered sequences of AffixRule. Order matters only for the
        deterministic "lightest strip" tie-break; validation.py does the
        real selection.
    max_passes:
        How many times to iteratively peel affixes (nested morphology).
    strip_derivational:
        If False, derivational affixes are skipped (pure light/inflectional
        stemming). Exposed as an ablation switch.
    """

    def __init__(
        self,
        suffixes: Sequence[AffixRule],
        prefixes: Sequence[AffixRule],
        max_passes: int = 3,
        strip_derivational: bool = True,
    ) -> None:
        self.suffixes = list(suffixes)
        self.prefixes = list(prefixes)
        self.max_passes = max_passes
        self.strip_derivational = strip_derivational

    def _active(self, rules: Sequence[AffixRule]) -> List[AffixRule]:
        # §12 of the affix inventory: an affix whose strip_allowed is not 'yes'
        # is documented but never removed by rule. Lexicalized forms (وړوکی,
        # موچي) and unattested entries are recorded so the inventory is
        # complete, not so the engine can act on them.
        rules = [r for r in rules if r.strip_allowed == "yes"]
        if self.strip_derivational:
            return list(rules)
        return [r for r in rules if r.category == "inflectional"]

    def _rule_id(self, r: AffixRule) -> str:
        mark = "-" if r.side == "prefix" else "+"
        return f"{mark}{r.affix}" + (f">{r.add_back}" if r.add_back else "")

    def generate(self, token: str, allowed_pos=None) -> List[Candidate]:
        """
        Breadth-first multi-pass generation.

        Returns every distinct stem reachable by peeling 0..max_passes
        affixes, including the original token (0 strips). De-duplicated by
        surface form, keeping the derivation with the fewest removed chars.

        If ``allowed_pos`` is given (a set of coarse POS tags), only affixes
        that are POS-agnostic or compatible with it are applied — the
        POS-aware ablation arm.
        """
        original = token

        def _pos_ok(rule: AffixRule) -> bool:
            if allowed_pos is None or not rule.pos:
                return True
            return bool(set(rule.pos) & set(allowed_pos))

        active_rules = [r for r in self._active(self.suffixes) if _pos_ok(r)] + \
                       [r for r in self._active(self.prefixes) if _pos_ok(r)]

        best: dict[str, Candidate] = {
            token: Candidate(stem=token, rules_applied=(), passes=0, strip_len=0)
        }
        frontier: List[Candidate] = [best[token]]

        for depth in range(1, self.max_passes + 1):
            new_frontier: List[Candidate] = []
            for cand in frontier:
                for r in active_rules:
                    if r.first_pass_only and cand.strip_len > 0:
                        continue
                    stripped = r.apply(cand.stem)
                    if stripped is None or stripped == cand.stem:
                        continue
                    # Aggressiveness = total affix material removed so far.
                    # NOTE: this must count the AFFIX, not the net length
                    # change — a rule with add_back (سیمې→سیمه: strip ې, add ه)
                    # leaves the length unchanged, and measuring net length
                    # would score it as "no work done" and deny it the
                    # conflation reward in validation.
                    strip_len = cand.strip_len + len(r.affix)
                    new_cand = Candidate(
                        stem=stripped,
                        rules_applied=cand.rules_applied + (self._rule_id(r),),
                        passes=depth,
                        strip_len=strip_len,
                    )
                    prev = best.get(stripped)
                    if prev is None or new_cand.strip_len < prev.strip_len:
                        best[stripped] = new_cand
                        new_frontier.append(new_cand)
            if not new_frontier:
                break
            frontier = new_frontier

        return list(best.values())
