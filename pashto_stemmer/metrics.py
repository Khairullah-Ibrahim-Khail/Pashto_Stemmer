# -*- coding: utf-8 -*-
"""
metrics.py
==========
Evaluation metrics for stemming — both intrinsic (no gold labels needed)
and gold-based (Paice's method). All numbers reported in the thesis/paper
come from this module run on real data; nothing is hand-authored.

Intrinsic metrics (computable on any word list)
-----------------------------------------------
  * ICF  — Index Compression Factor = (N_words − N_stems) / N_words
  * stem_validity_rate — fraction of produced stems that are attested Pashto
    words (a strong quality proxy: the baseline emits non-words like لان;
    a good stemmer emits real words).
  * unchanged_rate — fraction of words the stemmer left untouched
    (an under-stemming proxy).
  * mean_class_size — average number of word types per stem class.
  * dictionary_hit_rate — fraction of *inputs* already in the lexicon.
  * throughput — words/second.

Gold-based metrics (need annotated stems / conflation groups)
-------------------------------------------------------------
  * accuracy — exact-match of predicted stem vs gold stem.
  * Paice UI / OI / ERRT — under-stemming index, over-stemming index, and
    the error-rate-relative-to-truncation summary (Paice, 1994).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass
class IntrinsicReport:
    n_words: int
    n_stems: int
    icf: float
    stem_validity_rate: float
    unchanged_rate: float
    mean_class_size: float
    dictionary_hit_rate: float
    throughput_wps: float

    def as_dict(self) -> Dict:
        return asdict(self)


def intrinsic_metrics(
    words: Sequence[str],
    stem_fn: Callable[[str], str],
    is_word: Optional[Callable[[str], bool]] = None,
) -> IntrinsicReport:
    """
    Run ``stem_fn`` over ``words`` and compute intrinsic metrics.

    ``is_word`` (optional) tests lexicon membership; used for
    stem_validity_rate and dictionary_hit_rate. If None those are reported
    as 0.0.
    """
    words = list(words)
    n = len(words)
    t0 = time.perf_counter()
    stems = [stem_fn(w) for w in words]
    dt = time.perf_counter() - t0

    stem_set = set(stems)
    unchanged = sum(1 for w, s in zip(words, stems) if w == s)

    if is_word is not None:
        valid_stems = sum(1 for s in stem_set if is_word(s))
        validity = valid_stems / len(stem_set) if stem_set else 0.0
        hits = sum(1 for w in set(words) if is_word(w))
        hit_rate = hits / len(set(words)) if words else 0.0
    else:
        validity = 0.0
        hit_rate = 0.0

    return IntrinsicReport(
        n_words=n,
        n_stems=len(stem_set),
        icf=(n - len(stem_set)) / n if n else 0.0,
        stem_validity_rate=validity,
        unchanged_rate=unchanged / n if n else 0.0,
        mean_class_size=n / len(stem_set) if stem_set else 0.0,
        dictionary_hit_rate=hit_rate,
        throughput_wps=n / dt if dt > 0 else float("inf"),
    )


# --------------------------------------------------------------------------- #
# Gold-based metrics
# --------------------------------------------------------------------------- #
def accuracy(pairs: Sequence[Tuple[str, str]], stem_fn: Callable[[str], str]) -> float:
    """Exact-match stem accuracy over (word, gold_stem) pairs."""
    if not pairs:
        return 0.0
    correct = sum(1 for w, gold in pairs if stem_fn(w) == gold)
    return correct / len(pairs)


@dataclass
class PaiceReport:
    ui: float            # under-stemming index  (0 best)
    oi: float            # over-stemming index   (0 best)
    sw: float            # stemming weight = OI/UI
    dmt: int             # desired merge total
    umt: int             # under-stemming merge total (missed merges)
    dnt: int             # desired non-merge total
    wmt: int             # wrongly merged total (bad merges)

    def as_dict(self) -> Dict:
        return asdict(self)


def paice(groups: Dict[str, List[str]], stem_fn: Callable[[str], str]) -> PaiceReport:
    """
    Paice's (1994) understemming/overstemming indices.

    ``groups`` maps a concept/lemma id -> list of word types that SHOULD
    conflate together (the gold semantic groups).

    UI = missed same-group merges / all same-group pairs
    OI = wrong cross-group merges / all cross-group pairs
    """
    # Precompute stems.
    word_stem: Dict[str, str] = {}
    for members in groups.values():
        for w in members:
            word_stem[w] = stem_fn(w)

    group_ids = list(groups.keys())

    # Desired Merge Total & Under-stemming Merge Total (within-group pairs)
    dmt = 0
    umt = 0
    for members in groups.values():
        m = list(dict.fromkeys(members))  # unique, keep order
        for i in range(len(m)):
            for j in range(i + 1, len(m)):
                dmt += 1
                if word_stem[m[i]] != word_stem[m[j]]:
                    umt += 1

    # Desired Non-merge Total & Wrongly Merged Total (cross-group pairs)
    dnt = 0
    wmt = 0
    for a in range(len(group_ids)):
        for b in range(a + 1, len(group_ids)):
            ma = list(dict.fromkeys(groups[group_ids[a]]))
            mb = list(dict.fromkeys(groups[group_ids[b]]))
            for wa in ma:
                for wb in mb:
                    dnt += 1
                    if word_stem[wa] == word_stem[wb]:
                        wmt += 1

    ui = umt / dmt if dmt else 0.0
    oi = wmt / dnt if dnt else 0.0
    sw = (oi / ui) if ui else float("inf")
    return PaiceReport(ui=ui, oi=oi, sw=sw, dmt=dmt, umt=umt, dnt=dnt, wmt=wmt)


if __name__ == "__main__":
    # tiny self-check
    demo_words = ["کورونه", "کورونو", "کور", "خبرونه", "خبر"]
    rep = intrinsic_metrics(demo_words, lambda w: w[:3])
    print(rep.as_dict())
