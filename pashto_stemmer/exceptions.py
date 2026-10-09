# -*- coding: utf-8 -*-
"""
exceptions.py
=============
Static lexical resources that override the rule engine:

    STOPWORDS      - function words returned unchanged (no useful stem)
    IRREGULAR      - suppletive / irregular surface -> stem map
    PROPER_NOUNS   - high-frequency names that must never be stripped
                     (the baseline mangled افغانستان -> افغانست)

These are intentionally small, high-confidence starting sets. They will be
extended during gold-set annotation (Phase 4). Because the stemmer also
validates against the lexicon, an *incomplete* list here degrades
gracefully (a miss, not a wrong strip).

All entries are stored already-normalized-compatible (plain surface forms);
the caller normalizes the query before lookup.
"""

from __future__ import annotations

from typing import Dict, Set

# --------------------------------------------------------------------------- #
# Stopwords: pronouns, prepositions, conjunctions, copulas, particles.
# --------------------------------------------------------------------------- #
STOPWORDS: Set[str] = {
    # conjunctions / particles
    "او", "یا", "خو", "هم", "چې", "که", "نو", "بیا", "ان", "لا",
    # negation / modality particles
    "نه", "مه", "به", "دې", "دی", "ده", "دا", "دغه", "هغه", "هغې", "هغو",
    # prepositions / postpositions
    "د", "په", "له", "تر", "پر", "کې", "کښې", "ته", "سره", "څخه", "باندې",
    "لپاره", "وروسته", "مخکې", "لاندې", "پورته", "پسې", "غوندې", "بې", "پرته",
    # pronouns
    "زه", "ته", "دی", "دا", "موږ", "مونږ", "تاسو", "تاسي", "دوی", "دوئ",
    "ما", "تا", "مو", "یې", "مې", "دې", "هغوی", "خپل", "خپله", "ځان",
    # wh-words
    "څه", "څوک", "ولې", "څنګه", "کله", "چیرته", "چېرته", "کوم", "څومره", "څو",
    # frequent quantifiers / adverbs (function-like)
    "ټول", "ډېر", "ډیر", "یو", "یوه", "هر", "هیڅ", "هېڅ", "بل", "بله",
    "اوس", "نور", "ورته", "همدا", "همدغه",
    # copula / existential "to be" — genuine function words
    "وو", "و", "دئ",
    # NOTE: شو، شوه، شول، شوی، شوې are NOT listed here. They are past forms of
    # the full verb کېدل 'to become', so they are handled by the verb paradigm
    # table (policy §5: verbs → infinitive), not frozen as stopwords.
}

# --------------------------------------------------------------------------- #
# Irregular / suppletive verbs: surface form -> light stem (infinitive lemma).
# The strong, audited paradigm-organized lexicon lives in irregular_verbs.py
# (~40 verbs, ~300 forms). We import and use it directly.
# --------------------------------------------------------------------------- #
from .irregular_verbs import IRREGULAR_VERBS as IRREGULAR  # noqa: E402

# --------------------------------------------------------------------------- #
# Proper nouns: place/country/personal names common in the corpus that
# must be frozen (returned unchanged) even though they superficially end in
# strippable material (e.g. افغانستان ends in ان).
# --------------------------------------------------------------------------- #
PROPER_NOUNS: Set[str] = {
    "افغانستان", "پاکستان", "ایران", "امریکا", "امریکه", "انګلستان",
    "هندوستان", "چین", "روسیه", "ترکیه", "عربستان", "ازبکستان",
    "تاجکستان", "ترکمنستان", "قزاقستان", "کابل", "کندهار", "هرات",
    "بلخ", "ننګرهار", "خوست", "پکتیا", "پکتیکا", "کونړ", "نورستان",
    "بدخشان", "بغلان", "کندز", "کوندوز", "غزني", "لوګر", "میدان",
    "پروان", "کاپیسا", "لغمان", "نیمروز", "هلمند", "زابل", "ارزګان",
    "دایکندی", "بامیان", "سمنگان", "سرپل", "جوزجان", "فاریاب", "بادغیس",
    "غور", "فراه", "تخار", "پنجشیر", "وردګ", "پېښور", "کوټه", "اسلام‌اباد",
    "کراچۍ", "لاهور", "بلوچستان", "تهران", "واشنګټن", "لندن", "مسکو",
    "بیجینګ", "دهلي", "ماسکو", "اروپا", "اسیا", "افریقا", "امارات",
    "ترمپ", "بایډن", "پوتین", "اوباما", "محمد", "احمد", "عمر", "علی",
    "طالبان", "داعش", "القاعده", "ناتو", "اقوام", "یونیسف",
}


def is_stopword(word: str) -> bool:
    return word in STOPWORDS


def irregular_stem(word: str):
    """Return the irregular stem for ``word`` or None."""
    return IRREGULAR.get(word)


def is_proper_noun(word: str) -> bool:
    return word in PROPER_NOUNS


if __name__ == "__main__":
    print(f"stopwords    : {len(STOPWORDS)}")
    print(f"irregular    : {len(IRREGULAR)}")
    print(f"proper nouns : {len(PROPER_NOUNS)}")


# --------------------------------------------------------------------------- #
# Arabic BROKEN PLURALS — dictionary, not rules (policy §6).
# The change is internal (اثار / اثر), so it is outside affix stripping.
# Pattern-based derivation was tried and measured at only 40% precision on
# unvowelled Pashto text, which is why this is a curated list.
# --------------------------------------------------------------------------- #
import os as _os

_AR_PLURALS_FILE = _os.path.join(_os.path.dirname(__file__), "data",
                                 "arabic_plurals.tsv")


def load_arabic_plurals(path: str = _AR_PLURALS_FILE) -> Dict[str, str]:
    """{plural: singular} loaded from the curated TSV (empty if missing)."""
    out: Dict[str, str] = {}
    if not _os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0] and parts[1]:
                out[parts[0]] = parts[1]
    return out


ARABIC_PLURALS: Dict[str, str] = load_arabic_plurals()
