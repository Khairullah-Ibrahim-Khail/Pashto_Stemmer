# -*- coding: utf-8 -*-
"""
dictionary.py
=============
The lexical backbone of the stemmer: the frequency list the selection
stage consults.

`PashtoLexicon` loads a word-frequency list (default:
``stemming/pashto_dictionary.txt`` — one ``word<TAB>count`` per line) and
exposes the queries the rule engine needs:

    - membership          :  is this string an attested Pashto word?
    - frequency / score   :  corpus frequency (used to rank stem candidates)
    - longest valid prefix:  for compound decomposition
    - prefix walk (trie)  :  all attested words starting with a prefix

Why a frequency-weighted lexicon (and not a plain word set)?
------------------------------------------------------------
The hybrid stemmers of Persian (Rahimi 2015) and
Urdu (Khan 2018) resolve the over-stemming problem by *validating* each
rule-generated candidate against a lexicon and preferring the candidate
the corpus actually attests. Frequency lets us break ties between two
"real word" candidates by corpus evidence — a purely rule-based signal
(it is a corpus statistic, not a learned model), which keeps the system
100% rule-based / ML-free.

Every entry is passed through the project Normalizer on load and stripped
of trailing/leading Perso-Arabic punctuation, so the lexicon is in the
exact same normalized space the stemmer operates in.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from .normalizer import Normalizer


# Perso-Arabic + ASCII punctuation that sometimes clings to corpus tokens.
_STRIP_PUNCT = "؟،؛٫٬.!?:;\"'«»()[]{}—–-…\u200F\u200E"

# Default resource — packaged data (works after `pip install`), with a
# fallback to the repo's resources/ for source checkouts.
_PKG_DICT = os.path.join(os.path.dirname(__file__), "data", "pashto_dictionary.txt")
_REPO_DICT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "resources", "pashto_dictionary.txt")
)
_DEFAULT_DICT = _PKG_DICT if os.path.exists(_PKG_DICT) else _REPO_DICT


def _clean_surface(word: str) -> str:
    return word.strip().strip(_STRIP_PUNCT).strip()


class _TrieNode:
    __slots__ = ("children", "is_word", "freq")

    def __init__(self) -> None:
        self.children: Dict[str, "_TrieNode"] = {}
        self.is_word: bool = False
        self.freq: int = 0


@dataclass
class LexiconStats:
    entries: int
    total_frequency: int
    max_frequency: int
    source: str


class PashtoLexicon:
    """
    Frequency-weighted Pashto lexicon backed by a character trie.

    Parameters
    ----------
    normalizer:
        Normalizer used to canonicalize every entry (and every query).
        Pass the *same* instance the stemmer uses so the spaces match.
    """

    def __init__(self, normalizer: Optional[Normalizer] = None) -> None:
        self.normalizer = normalizer or Normalizer()
        self._root = _TrieNode()
        self._freq: Dict[str, int] = {}
        self._max_freq: int = 0
        self._total_freq: int = 0
        self._source: str = "(empty)"

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #
    @classmethod
    def from_frequency_file(
        cls,
        path: str = _DEFAULT_DICT,
        normalizer: Optional[Normalizer] = None,
        encoding: str = "utf-8",
    ) -> "PashtoLexicon":
        """Load a ``word<TAB>count`` (or plain ``word``) per-line file."""
        lex = cls(normalizer=normalizer)
        with open(path, "r", encoding=encoding) as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                parts = line.split("\t")
                surface = parts[0]
                try:
                    freq = int(parts[1]) if len(parts) > 1 else 1
                except ValueError:
                    freq = 1
                lex.add(surface, freq)
        lex._source = path
        return lex

    def add(self, surface: str, freq: int = 1) -> None:
        """Add/accumulate a single surface form (normalized on the way in)."""
        word = self.normalizer.normalize_token(_clean_surface(surface))
        if not word:
            return
        # accumulate frequency across duplicate/normalized collisions
        new_freq = self._freq.get(word, 0) + freq
        self._freq[word] = new_freq
        self._total_freq += freq
        if new_freq > self._max_freq:
            self._max_freq = new_freq

        node = self._root
        for ch in word:
            node = node.children.setdefault(ch, _TrieNode())
        node.is_word = True
        node.freq = new_freq

    def update(self, words: Iterable[Tuple[str, int]]) -> None:
        for w, f in words:
            self.add(w, f)

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #
    def contains(self, word: str, normalize: bool = True) -> bool:
        """True if ``word`` is an attested lexicon entry."""
        if normalize:
            word = self.normalizer.normalize_token(word)
        return word in self._freq

    __contains__ = contains

    def frequency(self, word: str, normalize: bool = True) -> int:
        """Corpus frequency of ``word`` (0 if unknown)."""
        if normalize:
            word = self.normalizer.normalize_token(word)
        return self._freq.get(word, 0)

    def score(self, word: str, normalize: bool = True) -> float:
        """
        Normalized attestation score in [0, 1]:
            0.0            -> not in lexicon
            (0, 1]         -> log-scaled frequency, 1.0 == most frequent word
        Log scaling keeps a few ultra-frequent words (افغانستان, وخت) from
        dominating candidate ranking.
        """
        if normalize:
            word = self.normalizer.normalize_token(word)
        f = self._freq.get(word, 0)
        if f <= 0:
            return 0.0
        import math
        return math.log1p(f) / math.log1p(self._max_freq)

    def longest_valid_prefix(self, word: str, normalize: bool = True) -> Optional[str]:
        """
        Longest prefix of ``word`` that is itself an attested word.
        Used by compound decomposition to split e.g. ``مرګژوبله``.
        Returns None if no prefix (of length >= 1) is a word.
        """
        if normalize:
            word = self.normalizer.normalize_token(word)
        node = self._root
        best: Optional[str] = None
        acc: List[str] = []
        for ch in word:
            nxt = node.children.get(ch)
            if nxt is None:
                break
            acc.append(ch)
            node = nxt
            if node.is_word:
                best = "".join(acc)
        return best

    def has_prefix(self, prefix: str, normalize: bool = True) -> bool:
        """True if any lexicon word starts with ``prefix``."""
        if normalize:
            prefix = self.normalizer.normalize_token(prefix)
        node = self._root
        for ch in prefix:
            node = node.children.get(ch)
            if node is None:
                return False
        return True

    def words_with_prefix(self, prefix: str, limit: int = 50,
                          normalize: bool = True) -> List[Tuple[str, int]]:
        """Return up to ``limit`` (word, freq) pairs starting with ``prefix``."""
        if normalize:
            prefix = self.normalizer.normalize_token(prefix)
        node = self._root
        for ch in prefix:
            node = node.children.get(ch)
            if node is None:
                return []
        out: List[Tuple[str, int]] = []

        def walk(n: _TrieNode, acc: str) -> None:
            if len(out) >= limit:
                return
            if n.is_word:
                out.append((acc, n.freq))
            for c, child in n.children.items():
                if len(out) >= limit:
                    return
                walk(child, acc + c)

        walk(node, prefix)
        out.sort(key=lambda t: -t[1])
        return out[:limit]

    # ------------------------------------------------------------------ #
    # Introspection
    # ------------------------------------------------------------------ #
    def family(self, stem: str, suffixes: Iterable[str],
               normalize: bool = True) -> List[str]:
        """
        The stem's **word family**: attested words formed from ``stem`` by
        adding one of ``suffixes``.

        This is the operational test of stem-hood: a real stem is one from
        which other words are built — لوست gives لوسته، لوستونکی، لوستل. It
        replaces arbitrary character-length thresholds with actual corpus
        evidence, and applies uniformly to every word.
        """
        if normalize and self.normalizer is not None:
            stem = self.normalizer.normalize_token(stem)
        if not stem:
            return []
        out = []
        for suf in suffixes:
            w = stem + suf
            if w != stem and self.contains(w, normalize=False):
                out.append(w)
        return out

    def family_size(self, stem: str, suffixes: Iterable[str],
                    normalize: bool = True) -> int:
        return len(self.family(stem, suffixes, normalize=normalize))

    def stats(self) -> LexiconStats:
        return LexiconStats(
            entries=len(self._freq),
            total_frequency=self._total_freq,
            max_frequency=self._max_freq,
            source=self._source,
        )

    def __len__(self) -> int:
        return len(self._freq)

    def __iter__(self) -> Iterator[str]:
        return iter(self._freq)


if __name__ == "__main__":
    lex = PashtoLexicon.from_frequency_file()
    s = lex.stats()
    print(f"source     : {s.source}")
    print(f"entries    : {s.entries}")
    print(f"max freq   : {s.max_frequency}")
    print(f"total freq : {s.total_frequency}")
    for w in ["افغانستان", "پاكستان", "وخت", "نجلۍ", "دی؟", "زهکاذبنشته"]:
        print(f"  {w!r:14} in={lex.contains(w)!s:5} "
              f"freq={lex.frequency(w):4d} score={lex.score(w):.3f}")
    print("longest_valid_prefix('مرګژوبله') =", lex.longest_valid_prefix("مرګژوبله"))
    print("words_with_prefix('افغان', 5)    =", lex.words_with_prefix("افغان", 5))
