# -*- coding: utf-8 -*-
"""
error_analysis.py
=================
Regenerates the paper's error analysis -- the two tables and the counts in
Section V.D and V.E -- from the released data and the live rule objects.

    python experiments/error_analysis.py

It prints, in order:

    Table XI   precision of the most frequently firing rules (development set)
    Table XII  accuracy by the affix the reference removes (development set)
    the three-way split of the errors into over-strips, under-strips and
    same-length disagreements, for both sets
    accuracy on the types the reference leaves whole, split by whether the
    word carries a letter that only native Pashto vocabulary has
    the cost of gating the two rules the paper discusses

Rule attribution comes from StemResult.rules_applied, so a rule is credited
only when it took part in the analysis that was finally selected. A rule that
proposed a candidate the scorer rejected is not counted.
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 "..", "paper")))

from reproduce_paper import DEV, HELD, load                      # noqa: E402
from make_inventory_tables import group_of as group_of_rule      # noqa: E402
from pashto_stemmer.prefixes import PREFIX_RULES                 # noqa: E402
from pashto_stemmer.stemmer import PashtoStemmer, StemmerConfig  # noqa: E402
from pashto_stemmer.suffixes import SUFFIX_RULES                 # noqa: E402

# Letters that occur only in native Pashto vocabulary. A word containing one is
# certainly not a borrowing; a word without one may be either, so the test is
# one-sided and is reported as such.
NATIVE_ONLY = set("ټډړږښځڅڼګېۍ")

FOLD = str.maketrans({"ي": "ی", "ې": "ی", "ۍ": "ی", "ئ": "ی", "ے": "ی"})


def fold(s: str) -> str:
    return s.translate(FOLD)


# The same index the annotation audit uses: folded, so that a rule written with
# one yeh letter still matches a removal written with another, and side-aware,
# so that a suffix rule cannot explain a removal from the front of the word.
AFFIX = {}
for _r in list(SUFFIX_RULES) + list(PREFIX_RULES):
    AFFIX.setdefault((fold(_r.affix), _r.side), _r)


def group_of(word: str, stem: str) -> str:
    """Which part of the inventory the reference's removal belongs to.

    The grouping follows the rule the removal matches, not a guess about the
    word: a removal is nominal or verbal inflection, noun- or
    adjective-forming derivation, according to the category and part of speech
    the matched rule declares. A removal no rule explains is its own group,
    and those rows are the ones the annotation audit writes out.
    """
    w, s = fold(word), fold(stem)
    if not s or w == s:
        return "No affix, word left whole"
    if w.startswith(s):
        rule = AFFIX.get((w[len(s):], "suffix"))
    elif w.endswith(s):
        rule = AFFIX.get((w[:len(w) - len(s)], "prefix"))
    else:
        # Stripped at both ends: a perfective prefix and a verbal ending come
        # off the same word (وښيي -> ښي). The removal is explained when each
        # end matches a rule of its own side, and is grouped by the suffix,
        # which is the end that carries the inflection.
        front, back = w[:w.index(s)], w[w.index(s) + len(s):]
        rule = AFFIX.get((back, "suffix"))
        if rule is None or AFFIX.get((front, "prefix")) is None:
            return "Nothing in the inventory"
    if rule is None:
        return "Nothing in the inventory"
    return group_of_rule(rule)


# The same order and the same labels as the inventory summary (Table II), so
# that the two tables can be read against each other.
GROUP_ORDER = ["Nominal inflection", "Verbal inflection", "Derivation: nouns",
               "Derivation: adjectives", "Derivation: verbs", "Prefixes",
               "No affix, word left whole", "Nothing in the inventory"]


def rule_precision(st, pairs, top=14):
    fires = defaultdict(int)
    correct = defaultdict(int)
    for w, s in pairs:
        res = st.stem_word(w)
        hit = res.stem == s
        for name in dict.fromkeys(res.rules_applied):
            fires[name] += 1
            correct[name] += hit
    ranked = sorted(fires.items(), key=lambda kv: -kv[1])[:top]
    print(f"\nTABLE XI  precision of the {top} most frequently firing rules "
          "(development set)")
    print(f" {'rule':28} {'fires':>6} {'correct':>8} {'precision':>10}")
    print(" " + "-" * 56)
    for name, n in ranked:
        print(f" {name:28} {n:6} {correct[name]:8} "
              f"{correct[name] / n:9.1%}")


def by_group(st, pairs):
    buckets = defaultdict(list)
    for w, s in pairs:
        buckets[group_of(w, s)].append((w, s))
    print("\nTABLE XII  accuracy by the affix the reference removes "
          "(development set)")
    print(f" {'what the reference removes':28} {'types':>6} {'accuracy':>9}")
    print(" " + "-" * 46)
    for g in GROUP_ORDER:
        rows = buckets.get(g, [])
        if not rows:
            continue
        ok = sum(1 for w, s in rows if st.stem(w) == s)
        print(f" {g:28} {len(rows):6} {ok / len(rows):8.1%}")
    whole = buckets["No affix, word left whole"]
    wrong = sum(1 for w, s in whole if st.stem(w) != s)
    print(f"\n {wrong} of the {len(whole)} types the reference leaves whole "
          f"are stripped that should not have been.")
    return buckets


def error_kinds(st, pairs, label):
    over = under = other = untouched = 0
    for w, s in pairs:
        o = st.stem(w)
        if o == s:
            continue
        if len(o) < len(s):
            over += 1
        elif len(o) > len(s):
            under += 1
            untouched += (o == w)
        else:
            other += 1
    total = over + under + other
    print(f"\n{label}: {total} errors -- {over} over-strips ({over/total:.0%}), "
          f"{under} under-strips ({under/total:.0%}, {untouched} of them words "
          f"left untouched), {other} the same length but different letters")


def native_split(st, buckets):
    whole = buckets["No affix, word left whole"]
    native = [(w, s) for w, s in whole if set(w) & NATIVE_ONLY]
    rest = [(w, s) for w, s in whole if not set(w) & NATIVE_ONLY]
    for name, rows in (("certainly native", native), ("the rest", rest)):
        bad = sum(1 for w, s in rows if st.stem(w) != s)
        print(f" among the types left whole, {name:17} {len(rows):5} types, "
              f"wrong on {bad / len(rows):5.1%}")


def gating_cost(dev, held):
    """What the two gated verbal rules are worth, measured rather than quoted."""
    print()
    for affix in ("لو", "لې"):
        rule = next((r for r in SUFFIX_RULES if r.affix == affix), None)
        if rule is None:
            print(f" {affix}: not in the inventory")
            continue
        was = rule.strip_allowed
        object.__setattr__(rule, "strip_allowed", "yes")
        st = PashtoStemmer()
        ungated = [sum(1 for w, s in p if st.stem(w) == s) / len(p)
                   for p in (dev, held)]
        object.__setattr__(rule, "strip_allowed", was)
        st = PashtoStemmer()
        gated = [sum(1 for w, s in p if st.stem(w) == s) / len(p)
                 for p in (dev, held)]
        print(f" gating {affix} is worth "
              f"{(gated[0] - ungated[0]) * 100:+.2f} points on the development "
              f"set and {(gated[1] - ungated[1]) * 100:+.2f} on held-out text")


def r1_costs(dev, held):
    """What each letter in the R1 length rule is worth."""
    base = PashtoStemmer()
    full = [_acc(base, p) for p in (dev, held)]
    tail = StemmerConfig().r1_tail
    print("\n cost of dropping each letter from the R1 length rule:")
    for letter in tail:
        cfg = StemmerConfig()
        cfg.r1_tail = tail.replace(letter, "")
        st = PashtoStemmer(cfg)
        d, h = _acc(st, dev), _acc(st, held)
        print(f"   R1 without {letter}   development {d:6.2f}% "
              f"({d - full[0]:+.2f})   held-out {h:6.2f}% ({h - full[1]:+.2f})")


def _acc(st, pairs):
    return sum(1 for w, s in pairs if st.stem(w) == s) / len(pairs) * 100


def main() -> int:
    _, dev = load(DEV, "word", "stem")
    _, held = load(HELD, "word", "stem")
    st = PashtoStemmer()
    rule_precision(st, dev, top=14)
    buckets = by_group(st, dev)
    error_kinds(st, dev, "development set")
    error_kinds(st, held, "held-out set")
    print()
    native_split(st, buckets)
    gating_cost(dev, held)
    r1_costs(dev, held)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
