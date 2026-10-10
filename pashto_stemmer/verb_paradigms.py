# -*- coding: utf-8 -*-
"""
verb_paradigms.py
=================
Pashto verb morphology, stored as **paradigms** rather than as a flat list of
surface forms (see docs/02_annotation_policy.md §5).

Why paradigms
-------------
A Pashto verb is defined by two stems:

    lemma (infinitive)  |  present stem  |  past stem
    تلل                 |  ځ‑            |  لاړ‑ / تل‑
    اخیستل              |  اخل‑          |  اخیست‑
    کول                 |  کو‑           |  کړ‑

The agreement endings (‑م ‑ې ‑ي ‑و ‑ئ), the perfective prefix و‑ and the
infinitive/oblique endings are **regular** and are applied by rule on top.
Storing 2 stems per verb therefore covers far more surface forms than a
hand-typed list, with fewer assumptions.

Two classes of verb
-------------------
1. **Regular** — the stems are predictable from the infinitive, so they are
   derived by rule, not listed:
       X‑ېدل  →  present X‑ېږ ,  past X‑ېد      (رسېدل، پوهېدل، جوړېدل …)
       X‑ول   →  present X‑و  ,  past X‑ول      (جوړول، کارول، زیاتول …)
       X‑ل    →  present X    ,  past X‑        (منل، لېږل، سپارل …)
2. **Suppletive / irregular** — the present stem is not predictable and MUST be
   listed. Suppletion cannot be derived by any rule (ځي vs تلل share no
   material), so a lexicon here is linguistically required, not a shortcut.

Sources (verified against the primary texts, not recall)
--------------------------------------------------------
1. **Tegey & Robson, _A Reference Grammar of Pashto_** (CAL 1996; ERIC
   ED399825), ch. 8 — "Simple irregular verbs", the master list of
   *English | Present stem | Past stem | Infinitive*, plus the four
   "doubly irregular" verbs with idiosyncratic 3rd-person past forms
   (کتل، وتل، ختل، خوړل).
2. **Robson & Tegey, "Pashto"**, in _The Iranian Languages_ (Routledge) —
   Table 13.15 (irregular & suppletive verbs), Table 13.16 (derivative verbs:
   the `‑ېږ`/`‑ېد` intransitive and `‑و`/`‑ول` transitive patterns), and
   Table 13.17 (prefixed را‑/در‑/ور‑ verbs).
3. **Apertium `apertium-pus`** morphological dictionary — confirms the
   agreement endings: shared م (1sg), ې (2sg), و (1pl), ئ (2pl);
   present 3rd ي; past 3sg.m ۀ, 3sg.f ه, 3pl.f ې.
4. **A. B. David, _Descriptive Grammar of Pashto and its Dialects_**
   (De Gruyter 2014) §8.2.6 — confirms the analysis used here:
   **weak verbs = one stem**, **strong verbs = two or more stems**
   (the full strong-verb list, §8.2.6.3.3, is not openly available).

In David's terminology the two classes below are *weak* (predictable, one
stem) and *strong* (two stems, listed).

Orthography: written naturally; everything is passed through the project
Normalizer at build time (ي→ی standardized, ې/ۍ/ئ preserved).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class VerbParadigm:
    lemma: str                      # infinitive (citation form)
    present: Tuple[str, ...]        # present stem(s)
    past: Tuple[str, ...]           # past stem(s)
    note: str = ""


# --------------------------------------------------------------------------- #
# 1. SUPPLETIVE / IRREGULAR VERBS — present stem not predictable
# --------------------------------------------------------------------------- #
IRREGULAR: List[VerbParadigm] = [
    VerbParadigm("کول",      ("کو",),        ("کړ", "کاوه"),   "to do/make [R&T]"),
    VerbParadigm("کېدل",     ("کېږ", "کیږ"), ("شو", "شول"),    "to become/happen [R&T]"),
    VerbParadigm("تلل",      ("ځ",),         ("لاړ", "تل"),    "to go [R&T]"),
    VerbParadigm("راتلل",    ("راځ",),       ("راغل", "راغی"), "to come [R&T]"),
    VerbParadigm("وړل",      ("وړ",),        ("یووړ", "یوړ"),  "to carry/take away [R&T]"),
    VerbParadigm("راوړل",    ("راوړ",),      ("راووړ",),       "to bring [R&T]"),
    VerbParadigm("خوړل",     ("خور",),       ("خوړ",),         "to eat [T&R]"),
    VerbParadigm("لیدل",     ("وین",),       ("لید",),         "to see [T&R]"),
    VerbParadigm("کتل",      ("ګور",),       ("کوت", "کت"),    "to look [T&R]"),
    VerbParadigm("اخیستل",   ("اخل",),       ("اخیست",),       "to take/buy [T&R]"),
    VerbParadigm("نیول",     ("نیس",),       ("نیو",),         "to catch/hold [T&R]"),
    VerbParadigm("ویل",      ("وای",),       ("ویل",),         "to say [T&R]"),
    VerbParadigm("ورکول",    ("ورکو",),      ("ورکړ",),        "to give [R&T]"),
    VerbParadigm("غوښتل",    ("غواړ",),      ("غوښت",),        "to want [T&R]"),
    VerbParadigm("موندل",    ("موم",),       ("موند",),        "to find [T&R]"),
    VerbParadigm("لوستل",    ("لول",),       ("لوست",),        "to read [T&R]"),
    VerbParadigm("لرل",      ("لر",),        ("درلود", "لرل"), "to have"),
    VerbParadigm("وژل",      ("وژن",),       ("وژل", "ووژه"),  "to kill [T&R]"),
    VerbParadigm("اورېدل",   ("اور",),       ("اورېد",),       "to hear"),
    VerbParadigm("پېژندل",   ("پېژن", "پیژن"), ("پېژند", "پیژند"), "to know/recognize [T&R]"),
    VerbParadigm("ښودل",     ("ښی",),        ("ښود",),         "to show [T&R]"),
    VerbParadigm("کېښودل",   ("ږد",),        ("کېښود", "ایښود"), "to put/place"),
    VerbParadigm("پرېښودل",  ("پرېږد",),     ("پرېښود",),      "to leave/abandon"),
    VerbParadigm("الوتل",    ("الوز",),      ("الوت",),        "to fly [T&R]"),
    VerbParadigm("ختل",      ("خېژ",),       ("خوت", "خت"),    "to climb/rise [T&R]"),
    VerbParadigm("پرېوتل",   ("پرېوځ",),     ("پرېوت",),       "to fall"),
    VerbParadigm("کښېنستل",  ("کښېن",),      ("کښېناست", "ناست"), "to sit down"),
    VerbParadigm("ګڼل",      ("ګڼ",),        ("ګاڼه", "ګڼل"),  "to count/consider"),
    VerbParadigm("بلل",      ("بول",),       ("بلل",),         "to call/consider [T&R]"),
    VerbParadigm("ایستل",    ("باس",),       ("ایست", "وېست"), "to pull out/extract [T&R]"),
    VerbParadigm("پرانیستل", ("پرانیز",),    ("پرانیست",),     "to open"),

    # --- added from Tegey & Robson, "Simple irregular verbs" list ---------- #
    VerbParadigm("اغوستل",   ("اغوند",),     ("اغوست",),       "to wear [T&R]"),
    VerbParadigm("اوړل",     ("اوړ",),       ("وښت", "اوښت"),  "to pass/cross [T&R]"),
    VerbParadigm("چاودل",    ("چو",),        ("چاود",),        "to explode [T&R]"),
    VerbParadigm("نغښتل",    ("نغاړ",),      ("نغښت",),        "to wrap/roll up [T&R]"),
    VerbParadigm("ویشتل",    ("ول",),        ("وېشت",),        "to shoot [T&R]"),
    VerbParadigm("وتل",      ("وځ",),        ("وت",),          "to go out [T&R, doubly irr.]"),
    VerbParadigm("رودل",     ("رو",),        ("رود",),         "to suck [T&R]"),

    # --- prefixed verbs, Robson & Tegey Table 13.17 ------------------------ #
    VerbParadigm("ورتلل",    ("ورځ",),       ("ورتل", "ورغل"), "to go there [R&T 13.17]"),
    VerbParadigm("درتلل",    ("درځ",),       ("درتل", "درغل"), "to go to you [R&T 13.17]"),
    VerbParadigm("راکول",    ("راکو",),      ("راکړ",),        "to give here [R&T 13.17]"),
    VerbParadigm("درکول",    ("درکو",),      ("درکړ",),        "to give to you [R&T 13.17]"),
]

# --------------------------------------------------------------------------- #
# 2. REGULAR VERBS — stems derived by rule from the infinitive
# --------------------------------------------------------------------------- #
REGULAR_LEMMAS: List[str] = [
    # ‑ېدل (inchoative/passive): present ‑ېږ, past ‑ېد
    "رسېدل", "پوهېدل", "جوړېدل", "ګرځېدل", "زېږېدل", "پاڅېدل", "غږېدل",
    "اوسېدل", "لوېدل", "بدلېدل", "کښېدل", "زیانمنېدل",
    # ‑ول (causative/denominal): present ‑و, past ‑ول
    "جوړول", "کارول", "زیاتول", "کمول", "پیلول", "بشپړول", "ټاکل_",  # placeholder removed below
    # plain ‑ل
    "منل", "لېږل", "سپارل", "ژغورل", "شړل", "ګالل", "رټل", "څارل",
    "ساتل", "پالل", "ټاکل", "اړول", "وېشل", "لیکل", "خوځول",
]
REGULAR_LEMMAS = [x for x in REGULAR_LEMMAS if not x.endswith("_")]


def derive_regular(lemma: str) -> Optional[VerbParadigm]:
    """Derive (present, past) stems for a regular verb from its infinitive."""
    if lemma.endswith("ېدل"):
        base = lemma[:-3]
        return VerbParadigm(lemma, (base + "ېږ",), (base + "ېد",), "regular -ېدل")
    if lemma.endswith("ول"):
        base = lemma[:-2]
        return VerbParadigm(lemma, (base + "و",), (base + "ول",), "regular -ول")
    if lemma.endswith("ل"):
        base = lemma[:-1]
        return VerbParadigm(lemma, (base,), (base,), "regular -ل")
    return None


def all_paradigms() -> List[VerbParadigm]:
    out = list(IRREGULAR)
    for lem in REGULAR_LEMMAS:
        p = derive_regular(lem)
        if p:
            out.append(p)
    return out


# --------------------------------------------------------------------------- #
# 3. Regular inflectional endings (applied by rule on top of the stems)
# --------------------------------------------------------------------------- #
# NOTE: written in normalized orthography (ي is standardized to ی).
# The bare present stem is NOT included: a Pashto present stem is not a
# free-standing word form (it always carries an agreement ending), and
# indexing it caused false matches on common nouns (ورځ 'day' → ورتلل).
PRESENT_ENDINGS = ("م", "ې", "ي", "و", "ئ")   # 3rd person is ي [AP]
PAST_ENDINGS = ("", "م", "ې", "ه", "و", "ئ", "ل", "ی", "ي", "له", "لو")
INFINITIVE_ENDINGS = ("", "و", "ی", "ې")   # لیدل / لیدلو / لیدلی
PERFECTIVE = "و"                            # و‑ prefix on past forms: ولید، وکړ


# Genuine noun/verb homographs. Each of these IS a possible verb form, but in
# real Pashto text it is overwhelmingly a common noun, so the nominal reading
# wins and the verb analyzer must not claim it.
#   وخت   'time'      vs perfective of ختل (و+خت)
#   ورځ   'day'       vs present stem of ورتلل (ورځ‑)
#   لاره  'road'      vs 3sg.f past of لرل
NOUN_HOMOGRAPHS = {
    "وخت",
    "ورځ", "ورځې", "ورځو", "ورځي",
    "لاره", "لارې", "لارو",
}


def build_form_index(normalize=lambda s: s) -> Dict[str, str]:
    """
    Expand every paradigm into its surface forms and return {form: lemma}.

    Generation is deliberately conservative: the perfective و‑ prefix is applied
    only to PAST forms (where it belongs), and directional prefixes (را/ور/در)
    are not added generically — they are already part of the lemma where they
    occur (راتلل، راوړل، ورکول).
    """
    index: Dict[str, str] = {}

    blocked = {normalize(w) for w in NOUN_HOMOGRAPHS}

    def put(form: str, lemma: str) -> None:
        form = normalize(form)
        if not form or form in blocked:     # noun reading wins for homographs
            return
        if form not in index:               # first paradigm wins (strong first)
            index[form] = normalize(lemma)

    for p in all_paradigms():
        lemma = p.lemma
        # infinitive and its oblique/participial forms
        for e in INFINITIVE_ENDINGS:
            put(lemma + e, lemma)
        # present stem + agreement
        for st in p.present:
            for e in PRESENT_ENDINGS:
                put(st + e, lemma)
        # past stem + agreement, with and without the perfective و‑
        # NOTE: the perfective is applied even when the past stem itself begins
        # with و (وت، وړ، وښت) — ووت / ووړ are the correct perfective forms.
        for st in p.past:
            for e in PAST_ENDINGS:
                put(st + e, lemma)
                put(PERFECTIVE + st + e, lemma)
            # 3sg.m past drops the ل in the come/go suppletive stems only:
            # راغل → راغی، ورغل → ورغی، درغل → درغی.  (Restricted to ‑غل: a
            # general "drop final ل" rule wrongly produced پای from پالل.)
            if st.endswith("غل") and len(st) > 2:
                short = st[:-1]
                for e in ("ی", "ه", ""):
                    put(short + e, lemma)
                    put(PERFECTIVE + short + e, lemma)
    return index


# Basic (non-denominal) verbs in ‑ول: here ول is part of the lexical verb, not
# a verbalizer attached to a noun, so only the infinitive ‑ل is removed.
BASIC_OL_VERBS = {"کول", "ورکول", "راکول", "درکول"}

# How many other words the remainder must form before an affix may be removed.
# This replaces arbitrary character-length thresholds with the operational
# definition of a stem: *a stem is something other words are built from*.
MIN_FAMILY = 2

# No affix is removed from a word of this length or shorter (length rule R2).
MIN_WORD_LEN = 3

# Minimum length of the remainder that may be accepted as a stem.
MIN_STEM_LEN = 3


def lemma_to_stem(lemma: str, is_word=None, family_fn=None) -> str:
    """
    Convert an infinitive (citation form) to its **stem** — policy §5/§10.

    Stemming removes affixes, and the infinitive ‑ل is itself a suffix, so the
    stem is the infinitive minus ‑ل (لوستل → لوست، کېدل → کېد).

    The verbalizers ‑ول (transitive) and ‑ېدل (intransitive) derive verbs from
    nouns/adjectives (Robson & Tegey, Table 13.16), so they are productive
    derivational affixes and are removed as well (§4):
        کارول → کار،  جوړول → جوړ،  جوړېدل → جوړ
    ``is_word`` (the lexicon) confirms the nominal base really exists before
    that deeper strip is taken; otherwise only ‑ل is removed.
    """
    # Nothing is ever removed from a word of three characters or fewer:
    # کول، ویل، وژل، لرل keep their ل. (The same guard the ‑ه rule uses;
    # on short words the affix is part of the lexical item.)
    if len(lemma) <= MIN_WORD_LEN:
        return lemma

    def _supported(base: str) -> bool:
        """Is ``base`` a real stem — i.e. do other words get built from it?"""
        # A one- or two-letter remainder trivially "has a family" (ک matches
        # که، کې، کول …) without being a stem, so it is never accepted.
        if len(base) < MIN_STEM_LEN:
            return False
        if family_fn is not None and family_fn(base) >= MIN_FAMILY:
            return True
        return bool(is_word is not None and is_word(base))

    if lemma.endswith("ېدل"):
        base = lemma[:-3]
        return base if _supported(base) else lemma     # جوړېدل → جوړ
    if lemma.endswith("ول"):
        base = lemma[:-2]
        return base if _supported(base) else lemma     # کارول → کار
    # The verbal ‑ل comes off when what remains is a stem by the family test:
    #   لوست → لوستل، لوستلو، لوستونکی   (family 3) -> strip
    #   کو   → کول، کوو، کوئ، کوونکی      (family 7) -> strip
    # No character-count threshold is used; the same test decides every word,
    # which is what makes it work on unseen vocabulary.
    if lemma.endswith("ل") and len(lemma) > 2:
        base = lemma[:-1]
        return base if _supported(base) else lemma
    return lemma


class VerbAnalyzer:
    """Maps an inflected verb form to its infinitive lemma (O(1) lookup)."""

    def __init__(self, normalize=lambda s: s) -> None:
        self._normalize = normalize
        self.index: Dict[str, str] = build_form_index(normalize)

    def lemma_of(self, token: str) -> Optional[str]:
        return self.index.get(self._normalize(token))

    def __len__(self) -> int:
        return len(self.index)


if __name__ == "__main__":
    idx = build_form_index()
    print(f"paradigms      : {len(all_paradigms())} "
          f"({len(IRREGULAR)} irregular + {len(REGULAR_LEMMAS)} regular)")
    print(f"generated forms: {len(idx)}")
    for f in ["ځي", "ځم", "لاړ", "ولاړل", "وینم", "ولید", "اخلي", "واخیست",
              "غواړي", "وغوښت", "کوي", "وکړل", "رسېږي", "ورسېد", "جوړېږي",
              "منم", "ومنل", "لوستل", "لولي", "ولوست"]:
        print(f"   {f:10} -> {idx.get(f, '—')}")
