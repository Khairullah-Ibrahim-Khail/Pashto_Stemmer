# -*- coding: utf-8 -*-
"""
normalizer.py
=============
Unicode + Pashto orthographic normalization for the grammar-driven
rule-based Pashto stemmer.

Design principle: **conservative, Pashto-aware normalization.**
------------------------------------------------------------------
Most Persian/Urdu normalizers unify *all* "yeh" letters
(ي / ی / ې / ۍ / ئ) into a single character. For Pashto this is WRONG:
those yeh forms are morphologically contrastive — they mark gender,
number, and case (e.g. masculine ي vs. feminine ۍ vs. Pashto ې). The
whole point of a stemmer is to reason about that morphology, so normalization
must NOT destroy it.

Only *true encoding noise* is removed by default:
    - Arabic tashkeel / harakat (diacritics)
    - tatweel / kashida (ـ) elongation
    - zero-width non-joiner inside a token
    - collapse of Arabic vs. Persian digit families
    - Arabic kaf  ك (U+0643)  -> keheh ک (U+06A9)
    - alef-hamza  أ إ (U+0623/5) -> bare alef ا (keeps madda آ)
    - alef maksura ى (U+0649) -> Farsi yeh ی (U+06CC)
    - heh variants ة ہ -> ه (U+0647)

Every transformation is an independent flag on `NormalizerConfig`, so a
given normalization *aggressiveness* is a reproducible experimental
variable for the ablation study (Phase 5). In particular `unify_yeh`
and `unify_gaf` default to False and exist only to *measure* the damage
aggressive normalization does to Pashto stemming.

References:
    - Larkey et al. (Light stemming philosophy: normalize conservatively)
    - Aslamzai & Saad (2015) normalization stage (baseline)
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict


# ---------------------------------------------------------------------------
# Unicode code-point groups (named for readability / documentation)
# ---------------------------------------------------------------------------

# Arabic tashkeel / harakat and Quranic annotation marks. These are combining
# marks that never change the identity of a stem, only its vocalization.
_DIACRITICS = (
    "ؘؙؚؐؑؒؓؔؕؖؗ"  # honorifics / small high marks
    "ًٌٍَُِّْٕٓٔ"  # fathatan..hamza marks
    "ٖٜٟٗ٘ٙٚٛٝٞ"        # extended vowel marks
    "ٰ"                                                              # superscript alef
    "ۖۗۘۙۚۛۜ۟۠ۡۢ"   # Quranic marks
    "ۣ۪ۭۤۧۨ۫۬"
)

_TATWEEL = "ـ"          # ـ  kashida / elongation
_ZWNJ = "‌"             # zero-width non-joiner
_ZWJ = "‍"              # zero-width joiner

# Persian / Extended Arabic-Indic digits (U+06F0..U+06F9)
_PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
# Arabic-Indic digits (U+0660..U+0669)
_ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_ASCII_DIGITS = "0123456789"


def _build_map(pairs: Dict[str, str]) -> Dict[int, str]:
    """Turn a {src_char: dst_str} dict into a str.translate() table."""
    return {ord(src): dst for src, dst in pairs.items()}


@dataclass
class NormalizerConfig:
    """
    Flags controlling normalization aggressiveness.

    Defaults are the *linguistically safe* Pashto profile. The two
    intentionally-dangerous flags (`unify_yeh`, `unify_gaf`) default off
    and exist only for the ablation experiment that quantifies how much
    over-normalization hurts Pashto stemming.
    """

    remove_diacritics: bool = True
    remove_tatweel: bool = True
    remove_zwnj: bool = True          # strip ZWNJ *inside* a token
    strip_zwj: bool = True

    unify_arabic_kaf: bool = True     # ك -> ک
    unify_alef_hamza: bool = True     # أ إ -> ا   (madda آ preserved)
    unify_alef_maksura: bool = True   # ى -> ی
    unify_heh_variants: bool = True   # ة ہ ھ -> ه
    # Urdu letters that appear in Pashto written in Pakistan. They are the same
    # letters, encoded differently, so folding them is an encoding fix and not a
    # change of spelling. Taken from the companion Pashto_Normalizer project:
    #   https://github.com/Khairullah-Ibrahim-Khail/Pashto_Normalizer
    # ے (Urdu yeh barree) is NOT one of the five Pashto yeh; it stands for ې.
    unify_urdu_letters: bool = True    # ٹ ڈ ڑ ے -> ټ ډ ړ ې
    unify_pashto_gaf: bool = True      # گ (Persian) -> ګ (Pashto)
    unify_urdu_stop: bool = True       # ۔ -> .
    # Pashto has FIVE yeh letters and ي (U+064A, سخته یې) is one of them:
    # it marks masculine plural/oblique (سړي) and the 3rd-person present
    # (کوي), while ی (U+06CC) marks the masculine singular direct (سړی).
    # Merging them destroys a real grammatical distinction (سړی/سړي), so it
    # is OFF. Kept switchable only to quantify the damage in the ablation.
    normalize_arabic_yeh: bool = False  # ي -> ی  (DO NOT enable)

    # 'none' keeps digits verbatim; 'arabic' folds Persian->Arabic-Indic;
    # 'ascii' folds everything to 0-9.
    digits: str = "none"

    collapse_whitespace: bool = True
    apply_nfc: bool = True            # canonical Unicode composition first
    # NFKC additionally folds the Arabic presentation forms onto the ordinary
    # letters, which is what text copied from a PDF is made of. It leaves every
    # Pashto letter alone, including all five yeh, so it is on by default.
    apply_nfkc: bool = True

    # --- Deliberately aggressive / for ablation only ---------------------
    unify_yeh: bool = False           # DANGEROUS for Pashto: ي ی ې ۍ ئ ->ی
    unify_gaf: bool = False           # گ <-> ګ

    def __post_init__(self) -> None:
        if self.digits not in ("none", "arabic", "ascii"):
            raise ValueError(
                f"digits must be 'none', 'arabic', or 'ascii', got {self.digits!r}"
            )


class Normalizer:
    """
    Stateless normalizer built once from a :class:`NormalizerConfig`.

    Usage
    -----
    >>> nz = Normalizer()
    >>> nz.normalize("افغانســـتان")   # tatweel removed
    'افغانستان'
    """

    def __init__(self, config: NormalizerConfig | None = None) -> None:
        self.config = config or NormalizerConfig()
        self._char_map = self._compile_char_map()
        self._delete_chars = self._compile_delete_set()

    # ------------------------------------------------------------------ #
    # Compilation
    # ------------------------------------------------------------------ #
    def _compile_char_map(self) -> Dict[int, str]:
        pairs: Dict[str, str] = {}
        c = self.config

        if c.unify_arabic_kaf:
            pairs["ك"] = "ک"          # ك -> ک

        if c.unify_alef_hamza:
            pairs["أ"] = "ا"          # أ -> ا
            pairs["إ"] = "ا"          # إ -> ا

        if c.unify_alef_maksura:
            pairs["ى"] = "ی"          # ى -> ی

        if c.normalize_arabic_yeh:
            pairs["ي"] = "ی"          # ي (U+064A) -> ی (U+06CC)

        if c.unify_urdu_letters:
            pairs["ٹ"] = "ټ"          # Urdu tteh   -> Pashto tteh
            pairs["ڈ"] = "ډ"          # Urdu ddal   -> Pashto ddal
            pairs["ڑ"] = "ړ"          # Urdu rreh   -> Pashto rreh
            pairs["ے"] = "ې"          # Urdu yeh barree -> Pashto ye; it is not
                                      # one of the five Pashto yeh letters
        if c.unify_pashto_gaf:
            pairs["گ"] = "ګ"          # Persian gaf -> Pashto gaf

        if c.unify_urdu_stop:
            pairs["۔"] = "."

        if c.unify_heh_variants:
            pairs["ة"] = "ه"          # ة -> ه
            pairs["ہ"] = "ه"          # ہ -> ه (heh goal)
            pairs["ھ"] = "ه"          # ھ -> ه (doachashmee)

        if c.digits == "arabic":
            for p, a in zip(_PERSIAN_DIGITS, _ARABIC_DIGITS):
                pairs[p] = a
        elif c.digits == "ascii":
            for p, a in zip(_PERSIAN_DIGITS, _ASCII_DIGITS):
                pairs[p] = a
            for ar, a in zip(_ARABIC_DIGITS, _ASCII_DIGITS):
                pairs[ar] = a

        # --- ablation-only aggressive folds ---
        if c.unify_yeh:
            # aggressive: also collapse the DISTINCT Pashto yeh letters
            # (ې ۍ ئ) into ی — destroys gender/number info; measured in the
            # ablation study only.
            for y in "يېۍئ":
                pairs[y] = "ی"
        if c.unify_gaf:
            pairs["گ"] = "ګ"          # گ -> ګ

        return _build_map(pairs)

    def _compile_delete_set(self) -> str:
        """Characters removed outright (translated to None)."""
        remove = ""
        if self.config.remove_diacritics:
            remove += _DIACRITICS
        if self.config.remove_tatweel:
            remove += _TATWEEL
        if self.config.remove_zwnj:
            remove += _ZWNJ
        if self.config.strip_zwj:
            remove += _ZWJ
        return remove

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def normalize(self, text: str) -> str:
        """Normalize an arbitrary text span (may contain many tokens)."""
        if not text:
            return text

        if self.config.apply_nfkc:
            # NFKC folds the Arabic presentation forms (U+FB50-U+FEFF) onto the
            # ordinary letters. Text copied out of a PDF or an older website is
            # full of them -- ﮐﻮﺭﻭﻧﻪ is U+FB90 U+FEEE ... not ک و ر و ن ه -- and
            # without this it reaches the rules as characters no affix matches,
            # so the word is returned unstemmed and nothing says why.
            # Verified safe for Pashto: NFKC leaves all five yeh letters and all
            # nine Pashto-only consonants (ټ ډ ړ ږ ښ ځ څ ڼ ګ) unchanged.
            text = unicodedata.normalize("NFKC", text)
        elif self.config.apply_nfc:
            text = unicodedata.normalize("NFC", text)

        # 1) delete noise characters
        if self._delete_chars:
            text = text.translate({ord(ch): None for ch in self._delete_chars})

        # 2) character-for-character substitutions
        if self._char_map:
            text = text.translate(self._char_map)

        # 3) whitespace
        if self.config.collapse_whitespace:
            text = re.sub(r"\s+", " ", text).strip()

        return text

    def normalize_token(self, token: str) -> str:
        """
        Normalize a single already-tokenized word. Same transforms as
        :meth:`normalize` but without whitespace collapsing (there is no
        internal whitespace in a token) — kept separate so the stemmer can
        call it cheaply per token.
        """
        if not token:
            return token
        if self.config.apply_nfkc:
            token = unicodedata.normalize("NFKC", token)
        elif self.config.apply_nfc:
            token = unicodedata.normalize("NFC", token)
        if self._delete_chars:
            token = token.translate({ord(ch): None for ch in self._delete_chars})
        if self._char_map:
            token = token.translate(self._char_map)
        return token.strip()


# Convenience singleton with the safe default profile.
default_normalizer = Normalizer()


if __name__ == "__main__":
    demo = [
        "افغانســـتان",              # tatweel
        "پاكستان",                   # Arabic kaf ك
        "مُدَّت",                      # diacritics
        "کا‌بل",                # ZWNJ inside token
        "۱۴۰۵ کال",                  # persian digits
        "نجلۍ ښکلې ښکلي",            # 3 distinct yeh forms — must survive
    ]
    nz = Normalizer()
    for d in demo:
        print(f"{d!r:30}  ->  {nz.normalize(d)!r}")
