# -*- coding: utf-8 -*-
"""
baseline.py
===========
Reimplementation of the **Aslamzai & Saad (2015)** Pashto stemming algorithm,
used as the comparison baseline in all experiments.

Reference:
    S. Aslamzai and S. Saad, "Pashto Language Stemming Algorithm,"
    Asia-Pacific Journal of Information Technology and Multimedia, 4(1),
    pp. 25-37, 2015. DOI 10.17576/apjitm-2015-0401-03

The nine rules below are transcribed from pages 28-30 of that paper. An
earlier version of this file did not match the publication: it used suffix
lists and prefixes that do not appear in the paper (for example it treated
'ۍ' as Rule 3 and 'توب' as Rule 4, where the paper gives 'من' and 'یز'), which
made the comparison unfair to the baseline. Every rule here is quoted in the
docstring of the method that implements it so the correspondence can be
checked against the PDF in resources/.

Two things in the paper are ambiguous and the choices made here are recorded:

1.  The paper does not state whether prefixes or suffixes are removed first.
    Figure 2 shows a single "remove all the suffixes & prefixes" box. Prefixes
    are applied first here, which matches the worked examples (ناپوه -> پوه).

2.  Figures 3 and 4 give pseudocode covering a subset of the rules, with
    different length conditions from the numbered rules (Figure 4 requires
    five characters for نا- where Rule 5 requires more than three). The
    numbered rules are taken as authoritative since they are the fuller
    statement; `strict_figures=True` switches to the figure variant.

For a fair head-to-head the experiment harness feeds this class and the
proposed system the same normalized tokens, so no normalization happens here.
"""

from __future__ import annotations


class AslamzaiBaseline:
    """The published nine-rule Pashto stemmer: no lexicon, no validation."""

    #: Rule 1 suffixes, in the order printed in the paper.
    RULE1_SUFFIXES = ("ستان", "تون", "ونو", "تابه", "ناک", "وان", "وال",
                      "جن", "ان", "ور", "و")
    #: Rule 5 prefixes.
    #  The printed list also contains a bare "م". It is excluded by default
    #  because the paper's own worked example contradicts it: موتروان is given
    #  as موتر, but a م- prefix rule turns that into وتر. Whether the character
    #  is a typesetting artefact of the right-to-left list cannot be settled
    #  from the PDF, so the baseline is given the reading its example implies.
    #  Pass include_m_prefix=True for the literal list.
    RULE5_PREFIXES = ("نا", "نه", "بد", "نیک", "تش", "تل", "تور", "تک", "ډیر")
    #: Rule 9 prefixes (a subset of Rule 5, repeated in the paper).
    RULE9_PREFIXES = ("نا", "نه", "نیک")

    def __init__(self, strict_figures: bool = False,
                 include_m_prefix: bool = False) -> None:
        self.strict_figures = strict_figures
        self.rule5_prefixes = (self.RULE5_PREFIXES + ("م",)
                               if include_m_prefix else self.RULE5_PREFIXES)

    # ------------------------------------------------------------------ #
    # Suffix rules
    # ------------------------------------------------------------------ #
    def remove_suffixes(self, word: str) -> str:
        """Rules 1-4 and 8, applied in the order given in the paper.

        Rule 1: "words which are composed of five or more characters and end
                 with suffixes ستان، تون، ونو، ان، و، ور، ناک، جن، وان، وال،
                 تابه: just remove the suffixes"        (پوهنتون -> پوهن)
        Rule 2: "words which are comprised of 4 or more characters and end
                 with ي: remove the suffix and add ه"   (پیغلي -> پیغله)
        Rule 3: "if the word has more than 5 characters and ends with من just
                 remove the suffix من"                  (واکمن -> واک)
        Rule 4: "if the word is composed of 5 or more characters and ends with
                 یز remove the suffix یز and add ه"     (ټولنیز -> ټولنه)
        Rule 8: "when the same word is repeated as suffixes, it is removed as
                 a root word"                           (خوږی خوږی -> خوږی)
        """
        if self.strict_figures:
            # Figure 3: یز | نیز first, then ي -> ه, both at five characters.
            if len(word) >= 5:
                for suf in ("نیز", "یز"):
                    if word.endswith(suf):
                        return word[: -len(suf)]
            if len(word) >= 5 and word.endswith("ي"):
                return word[:-1] + "ه"
            return word

        if len(word) >= 5:
            for suf in self.RULE1_SUFFIXES:
                if word.endswith(suf):
                    return word[: -len(suf)]
        if len(word) >= 4 and word.endswith("ي"):
            return word[:-1] + "ه"
        # The paper says "more than 5 characters", but its own example واکمن
        # has exactly five, so >= is used.
        if len(word) >= 5 and word.endswith("من"):
            return word[:-2]
        if len(word) >= 5 and word.endswith("یز"):
            return word[:-2] + "ه"
        half = len(word) // 2
        if half and word[:half] == word[half:]:
            return word[:half]
        return word

    # ------------------------------------------------------------------ #
    # Prefix rules
    # ------------------------------------------------------------------ #
    def remove_prefixes(self, word: str) -> str:
        """Rules 5-7 and 9.

        Rule 5: "words that have more than 3 characters and start with the
                 prefixes نا، نه، م، بد، نیک، تش، تل، تور، تک، ډیر: just
                 remove the prefixes"                   (ناپوه -> پوه)
        Rule 6: "words which have 5 or more characters and start with ال just
                 remove the ال"                         (الزیات -> زیات)
        Rule 7: "words which have 5 or more than five characters and start
                 with وران: just remove وران"           (وران خولی -> خولی)
        Rule 9: "words that have more than 3 characters and start with نا، نه،
                 نیک: just remove the prefixes"         (ناروغ -> روغ)
        """
        if self.strict_figures:
            # Figure 4: نا | نیک first, then بد | ال, both at five characters.
            if len(word) >= 5:
                for pre in ("نیک", "نا"):
                    if word.startswith(pre):
                        return word[len(pre):]
                for pre in ("بد", "ال"):
                    if word.startswith(pre):
                        return word[len(pre):]
            return word

        if len(word) >= 5 and word.startswith("وران"):
            return word[4:]
        if len(word) >= 5 and word.startswith("ال"):
            return word[2:]
        if len(word) > 3:
            for pre in self.rule5_prefixes:
                if word.startswith(pre):
                    return word[len(pre):]
            for pre in self.RULE9_PREFIXES:
                if word.startswith(pre):
                    return word[len(pre):]
        return word

    # ------------------------------------------------------------------ #
    def stem(self, word: str) -> str:
        """Suffixes are removed before prefixes.

        The paper does not state the order, but its own example fixes it:
        موتروان -> موتر requires the suffix وان to go first, because the Rule 5
        prefix م would otherwise take the first letter of موتر and leave وتر.
        """
        word = self.remove_suffixes(word)
        word = self.remove_prefixes(word)
        return word


if __name__ == "__main__":
    b = AslamzaiBaseline()
    # the paper's own worked examples
    for w, want in [("پوهنتون", "پوهن"), ("موتروان", "موتر"), ("پیغلي", "پیغله"),
                    ("واکمن", "واک"), ("ټولنیز", "ټولنه"), ("ناپوه", "پوه"),
                    ("الزیات", "زیات"), ("ناروغ", "روغ")]:
        got = b.stem(w)
        print(f"  {w:10} -> {got:10} (paper: {want}) {'ok' if got == want else 'DIFFERS'}")
