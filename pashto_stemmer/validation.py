# -*- coding: utf-8 -*-
"""
validation.py
=============
Candidate selection — the anti-over-stemming heart of the system.

Given the candidate stems produced by the rule engine, this module scores
each against the frequency-weighted lexicon and picks the best, together
with a confidence value and a human-readable decision trace.

Scoring philosophy (transparent, rule-based — no ML):

    attested candidate   ->  value = 1.0 + freq_score − λ·strip_len
    unattested candidate ->  value = 0.0            − μ·strip_len

Consequences, which are the intended behaviours:
  * An **unattested** strip always scores below keeping the original word
    (0.0 vs negative), so the stemmer never destroys a word into a
    non-word — this is precisely what avoids the baseline's
    پراختيا→لان / پلانونه→لان catastrophe.
  * Among **attested** candidates, the more frequent (usually more basic)
    form wins, with a small penalty against needless over-stripping — so
    کورونه→کور conflates to the corpus-attested base form.
  * A word already at its base (attested, no strip) is happily kept.

For genuinely out-of-vocabulary words (nothing attested, not even the
original) there is an optional fallback to the lightest *inflectional*
strip, so OOV tokens still get some conflation, but with low confidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .dictionary import PashtoLexicon
from .rules import Candidate


@dataclass
class ValidationConfig:
    attested_bonus_a: float = 2.0    # A: an attested stem is strongly preferred
    # The UNSTRIPPED input word is almost always in the corpus, so giving it the
    # full attestation bonus made "do nothing" win by default and hid every
    # single-letter inflection. Its presence in a corpus is no evidence that it
    # is a STEM, so the no-strip candidate gets a much smaller bonus.
    base_attested_bonus: float = 0.5
    # ...and a single sighting is not evidence either. A word the corpus holds
    # once or twice is evidence that it exists, not that it is a base form:
    # انګلیسي occurs once and چینایي twice, and that was enough to outrank a
    # correct strip, so both came back whole. Below this frequency the
    # no-strip candidate is scored as if it were unattested. Measured at 3:
    # +0.48 on the development set and +0.40 on held-out text, the largest
    # single gain of any threshold tried (2, 3, 5, 8 and 15).
    min_base_freq: int = 3
    freq_weight: float = 0.5         # weight on corpus frequency
    strip_reward: float = 0.5        # β: reward for removing affix material
    unattested_strip: float = 0.20   # γ: lets rules still act on UNSEEN words
    family_bonus: float = 2.0        # F: the remainder builds other words
    min_family: int = 2              # how many other words count as a family
    min_stem_len: int = 3            # never accept a shorter remainder as a stem
    # legacy fields kept for the ablation arms
    strip_weight: float = 1.0
    attest_weight: float = 0.5
    # retained for the ablation arms / backwards compatibility
    attested_bonus: float = 1.0
    strip_reward_attested: float = 0.15
    strip_penalty_unattested: float = 0.10
    # OOV handling when nothing (incl. original) is attested:
    #   'original'              -> return the token unchanged
    #   'lightest_inflectional' -> return the smallest inflectional strip
    oov_fallback: str = "lightest_inflectional"
    max_oov_strip: int = 3                    # cap chars removed for OOV fallback


@dataclass
class Decision:
    stem: str
    confidence: float           # 0..1
    attested: bool
    rules_applied: tuple
    trace: str


class Validator:
    def __init__(self, lexicon: PashtoLexicon,
                 config: Optional[ValidationConfig] = None,
                 family_suffixes=None) -> None:
        self.lex = lexicon
        self.cfg = config or ValidationConfig()
        # suffix inventory used for the family test (see _value)
        self._family_suffixes = tuple(family_suffixes or ())

    # ------------------------------------------------------------------ #
    def _value(self, cand: Candidate) -> float:
        """
        Affix evidence is PRIMARY; lexicon attestation is a TIE-BREAKER.

        The lexicon is a list of corpus *surface forms*, not a list of stems,
        so "attested" is weak evidence of stem-hood: ښځو is attested simply
        because it occurs in the corpus. Requiring attestation therefore
        blocked correct strips (ښځو→ښځه) and, worse, made the stemmer useless
        on unseen words — the lexicon must guide, never gate.

        Removing more legitimate affix material wins; among candidates that
        removed the same amount, the attested (and more frequent) one wins —
        which is what picks سیمه over سیم.

        Over-stripping is bounded structurally, not by the lexicon: only
        affixes in the inventory may be removed, and each rule enforces its own
        minimum stem length.
        """
        v = self.cfg.strip_reward * cand.strip_len
        # FAMILY TEST — the general criterion for stem-hood: a remainder is a
        # stem if other words are built from it (څېړ -> څېړل، څېړنه، څېړونکی).
        # The lexicon is a small corpus word-list, so most true stems are NOT
        # directly attested; without this, every derivational strip was
        # rejected (کارکوونکی، کموالی، اړتیا stayed whole).
        if (self._family_suffixes and len(cand.stem) >= self.cfg.min_stem_len
                and self.lex.family_size(cand.stem, self._family_suffixes)
                >= self.cfg.min_family):
            v += self.cfg.family_bonus
        if (cand.strip_len == 0 and self.lex.contains(cand.stem)
                and self.lex.frequency(cand.stem) < self.cfg.min_base_freq):
            return 0.0                # too rare to evidence a base form
        if self.lex.contains(cand.stem):
            bonus = (self.cfg.base_attested_bonus if cand.strip_len == 0
                     else self.cfg.attested_bonus_a)
            return v + bonus + self.cfg.freq_weight * self.lex.score(cand.stem)
        if v > self.cfg.strip_reward * cand.strip_len:
            return v                      # family-supported, though unattested
        # Unattested: a small POSITIVE value proportional to the affix evidence.
        # It loses to any attested candidate, which is what keeps invented
        # stems out, but it still lets the rules act on UNSEEN words, where the
        # lexicon can confirm nothing.
        return self.cfg.unattested_strip * cand.strip_len

    def select(self, original: str, candidates: Sequence[Candidate]) -> Decision:
        """Pick the best candidate and attach confidence + trace."""
        # Ensure the 0-strip original is always in the pool.
        pool: List[Candidate] = list(candidates)
        if not any(c.strip_len == 0 for c in pool):
            pool.append(Candidate(stem=original, rules_applied=(), passes=0, strip_len=0))

        # Highest affix evidence wins; attestation only breaks ties (_value).
        # There is deliberately NO "fall back to the best attested candidate"
        # branch here: that would re-impose the lexicon as a gate and would
        # leave unseen words unstemmed.
        best = max(pool, key=self._value)
        attested = self.lex.contains(best.stem)

        if best.strip_len == 0:
            conf = 0.75 if attested else 0.55
            trace = f"kept base '{best.stem}'" + ("" if attested else " (unattested)")
        else:
            conf = 0.90 if attested else 0.65
            trace = (f"strip {best.rules_applied} -> '{best.stem}'"
                     + (f" (freq={self.lex.frequency(best.stem)})" if attested
                        else " (rule evidence, not in lexicon)"))
        return Decision(best.stem, conf, attested, best.rules_applied, trace)
