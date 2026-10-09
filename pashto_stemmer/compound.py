# -*- coding: utf-8 -*-
"""
compound.py
===========
Rule-based compound decomposition using the lexicon trie.

Pashto forms closed compounds by concatenation, e.g.
    مرګژوبله  = مرګ (death) + ژوبله (injury)   -> "casualties"
    لوبغاړی   = لوب (play) + غاړی               -> "player"
    ولسمشر    = ولس (nation) + مشر (leader)     -> "president"

A single-pass affix stripper cannot handle these; it will hack at the
edges and produce junk. We instead try to split an *unattested* word into
two (or more) attested parts using the trie's longest-valid-prefix query,
then let the stemmer stem the semantic head.

The splitter is deliberately conservative:
  * only fires on reasonably long words (>= min_word_len);
  * every part must itself be an attested lexicon word of >= min_part_len;
  * prefers the segmentation with the fewest parts, then the one whose
    parts are most corpus-frequent (a rule-based MDL-style preference).

This is the "+Compound" ablation arm (Phase 5).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .dictionary import PashtoLexicon


@dataclass
class CompoundConfig:
    min_word_len: int = 6      # don't try to split short words
    min_part_len: int = 2      # each component must be at least this long
    max_parts: int = 3         # cap recursion depth


class CompoundSplitter:
    def __init__(self, lexicon: PashtoLexicon,
                 config: Optional[CompoundConfig] = None) -> None:
        self.lex = lexicon
        self.cfg = config or CompoundConfig()

    def split(self, word: str) -> Optional[List[str]]:
        """
        Return the best list of attested component words, or None if the word
        is not decomposable (or is itself already an attested single word).
        """
        if len(word) < self.cfg.min_word_len:
            return None
        if self.lex.contains(word):
            return None  # a real single word — not a compound to split
        segs = self._segment(word, depth=self.cfg.max_parts)
        if segs and len(segs) >= 2:
            return segs
        return None

    def _segment(self, word: str, depth: int) -> Optional[List[str]]:
        """Greedy-with-backtracking segmentation into attested parts."""
        if not word:
            return []
        if depth <= 0:
            return [word] if self.lex.contains(word) else None

        best: Optional[List[str]] = None
        best_score = -1.0
        # try every prefix that is an attested word (longest first for a
        # natural, frequency-friendly bias)
        for cut in range(len(word), self.cfg.min_part_len - 1, -1):
            head = word[:cut]
            if len(head) < self.cfg.min_part_len:
                continue
            if not self.lex.contains(head):
                continue
            tail = word[cut:]
            if not tail:
                rest: Optional[List[str]] = []
            else:
                rest = self._segment(tail, depth - 1)
            if rest is None:
                continue
            parts = [head] + rest
            if any(len(p) < self.cfg.min_part_len for p in parts):
                continue
            # score: prefer fewer parts, then higher mean frequency
            mean_freq = sum(self.lex.score(p) for p in parts) / len(parts)
            score = (10.0 / len(parts)) + mean_freq
            if score > best_score:
                best_score = score
                best = parts
        return best

    def head(self, word: str) -> Optional[str]:
        """
        Return the semantic head component (Pashto compounds are largely
        head-final), or None if not decomposable.
        """
        segs = self.split(word)
        if not segs:
            return None
        return segs[-1]


if __name__ == "__main__":
    lex = PashtoLexicon.from_frequency_file()
    sp = CompoundSplitter(lex)
    for w in ["مرګژوبله", "ولسمشر", "لوبغاړی", "افغانستان", "کور"]:
        print(f"  {w:12} -> {sp.split(w)}")
