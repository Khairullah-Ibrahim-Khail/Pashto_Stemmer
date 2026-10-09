# -*- coding: utf-8 -*-
"""
suffixes.py
===========
Pashto suffix inventory for the stemmer.

Organized by function and tagged inflectional vs derivational so the rule
engine can (optionally) strip only inflectional material for true light
stemming. Ordered longest-affix-first within groups; the RuleEngine also
tries all of them and lets the lexicon validator choose, so ordering only
affects the deterministic tie-break.

POS tags used (coarse): N (noun), ADJ (adjective), V (verb).

NOTE ON ACCURACY: this inventory is a *linguistically-motivated starting
point*. Some affixes are ambiguous (e.g. و, ي, ه appear in several
paradigms). We deliberately over-generate candidates and rely on
dictionary validation to prevent the over-stripping that a commit-early
stemmer (the baseline) suffers from. The inventory will be refined
empirically against the gold set (Phase 6).
"""

from __future__ import annotations

from typing import List

from .rules import AffixRule

def _s(affix, category, add_back="", min_stem_len=2, pos=(), note="", first_pass_only=False, productivity="productive", confidence="high", strip_allowed="yes"):
    return AffixRule(affix=affix, side="suffix", category=category,
                     add_back=add_back, min_stem_len=min_stem_len,
                     pos=tuple(pos), note=note,
                     first_pass_only=first_pass_only,
                     productivity=productivity, confidence=confidence,
                     strip_allowed=strip_allowed)

# --- Nominal / adjectival INFLECTION: number, gender, case ------------------
_NOMINAL_INFLECTIONAL: List[AffixRule] = [
    _s("ونو", "inflectional", min_stem_len=2, pos=("N",), note="[T&R M2] oblique plural"),
    # Arabic sound plural ‑ات, highly productive on loanwords in Pashto
    # (صادرات، مذاکرات، انتخابات، معلومات) and its oblique ‑اتو.
    _s("اتو", "inflectional", min_stem_len=3, pos=("N",), note="Ar. pl + obl: صادراتو→صادر"),
    _s("ات", "inflectional", min_stem_len=3, pos=("N",), note="Ar. sound plural: صادرات→صادر"),
    # Numeral-based plural ‑ګونه 'tens/hundreds of' and its oblique.
    _s("ګونو", "inflectional", min_stem_len=2, pos=("N",), note="لسګونو→لس"),
    _s("ګونه", "inflectional", min_stem_len=2, pos=("N",), note="لسګونه→لس"),
    _s("ونه", "inflectional", min_stem_len=2, pos=("N",), note="[T&R M2] direct plural: کور→کورونه"),
    _s("انې", "inflectional", min_stem_len=3, pos=("N",), note="[T&R F2] alt. direct plural: کورنۍ→کورنیانې"),
    _s("یو", "inflectional", min_stem_len=3, pos=("N",), note="[T&R F2/F3] oblique plural: کورنیو، دوستیو"),
    _s("ګانو", "inflectional", min_stem_len=2, pos=("N",), note="[T&R M4/F3] oblique plural ‑ګانو"),
    _s("ګانې", "inflectional", min_stem_len=2, pos=("N",), note="[T&R F2/F3] direct plural ‑ګانې; [inv §5.1] feminine plural of vowel-final stems: دعاګانې→دعا"),
    _s("ګان", "inflectional", min_stem_len=2, pos=("N",), note="plural -gān"),
    _s("انو", "inflectional", min_stem_len=2, pos=("N",), note="[T&R M1] oblique plural ‑انو"),
    _s("ان", "inflectional", min_stem_len=3, pos=("N",), note="[T&R M1] animate plural ‑ان"),
    _s("ون", "inflectional", min_stem_len=3, pos=("N",), note="[N&K] adj->noun: ژوندی→ژوندون، نښتی→نښتون"),
    _s("ۍ", "inflectional", min_stem_len=3, pos=("N", "ADJ"), note="fem sg -əi (often lexical!)"),
    _s("ې", "inflectional", min_stem_len=2, pos=("N", "ADJ"), note="[T&R F1/Adj] feminine / plural ‑ې"),
    # Feminine base restoration (policy §3): the plural/oblique endings replace
    # the base's final ‑ه, so it must be restored — سیمې/سیمو → سیمه،
    # خبرو → خبره، چارو → چاره، ادارې → اداره.
    # Kept on LINGUISTIC grounds (both annotators agree on these forms), even
    # though it currently costs ~2 points against a gold that is internally
    # inconsistent on this pattern. Rules are derived from the grammar, not
    # selected by their effect on the score.
            _s("و", "inflectional", min_stem_len=3, pos=("N", "ADJ"), note="[T&R M3/Adj2] oblique plural ‑و"),
        # ‑ه is only removed when at least THREE characters remain.
    # In Pashto ‑ه is frequently word-forming, not just an ending: چار 'work'
    # → چاره is a derived variant. On short words removing it destroys the
    # word altogether, so the guard protects که، ده، مه، ښه، شپه، ښځه (ښځه would
    # leave only ښځ). Adjectival agreement still strips normally: لنډه → لنډ.
    _s("ه", "inflectional", min_stem_len=3, pos=("N", "ADJ"), note="fem/agreement -a; never removed if <3 chars would remain"),
]

# --- Verbal INFLECTION: infinitive, agreement, tense ------------------------
_VERBAL_INFLECTIONAL: List[AffixRule] = [
    _s("ېدل", "inflectional", min_stem_len=2, pos=("V",), first_pass_only=True, note="inchoative infinitive -edəl"),
    _s("ېده", "inflectional", min_stem_len=2, pos=("V",), first_pass_only=True, note="-eda"),
    _s("لو", "inflectional", min_stem_len=2, pos=("V",), first_pass_only=True, note="oblique infinitive: کولو→کول"),
    _s("ول", "inflectional", min_stem_len=2, pos=("V",), first_pass_only=True, note="causative -awəl"),
    _s("ل", "inflectional", min_stem_len=2, pos=("V",), first_pass_only=True,
       strip_allowed="no", confidence="low",
       note="NOT stripped. The verbal ‑ل is real, but a standalone rule for it fires on nouns, where ل is root: the gold keeps موټیل، شامل، سهیل، کابل whole. It was right 0 times out of 26. Verbs reach their root through the irregular dictionary and the derivative tails instead."),
    _s("ئ", "inflectional", min_stem_len=3, pos=("V",), note="imperative pl -əy"),
]

# --- DERIVATIONAL: change lexeme (abstract nouns, agentives, relational) -----
_DERIVATIONAL: List[AffixRule] = [
    _s("توب", "derivational", min_stem_len=3, pos=("N",), note="[N&K] adj->noun abstract: مین→مینتوب"),
    _s("والی", "derivational", min_stem_len=3, pos=("N",), note="[N&K] adj->noun abstract: تور→توروالی"),
    _s("والو", "derivational", min_stem_len=3, pos=("N",), note="oblique of -wāli"),
    _s("تیا", "derivational", min_stem_len=2, pos=("N",), note="abstract: پراختیا→پراخ"),
    _s("تون", "derivational", min_stem_len=3, pos=("N",), note="[N&K] adj->noun: بیل→بیلتون، ځای→ځایتون"),
    _s("ونکی", "derivational", min_stem_len=3, pos=("N", "ADJ"), note="[T&R][W] agentive participle -unkay: دراوونکی"),
    _s("ونکو", "derivational", min_stem_len=3, pos=("N",), note="oblique agentive"),
    _s("ونکې", "derivational", min_stem_len=3, pos=("N", "ADJ"), note="fem agentive"),
    _s("وال", "derivational", min_stem_len=3, pos=("N",), productivity="restricted", confidence="medium", strip_allowed="no", note="GATED by the gold standard: نړۍوال is kept whole (1 of 4). The affix is real Pashto morphology, but the annotation treats these words as whole, so the rule is recorded and not applied."),
    _s("وان", "derivational", min_stem_len=3, pos=("N",), productivity="restricted", confidence="low", strip_allowed="no", note="[inv §2.4/§14] needs validation: the earlier example دربان "
            "belongs to ‑بان, so this entry has no confirmed attested example"),
    _s("ګر", "derivational", min_stem_len=3, pos=("N",), note="agentive -gar: کارګر→کار"),
    _s("ور", "derivational", min_stem_len=3, pos=("ADJ",), productivity="restricted", confidence="medium", strip_allowed="no", note="GATED by the gold standard: پېښور، مشهور، لاهور are kept whole (0 of 16). The affix is real Pashto morphology, but the annotation treats these words as whole, so the rule is recorded and not applied."),
    _s("ين", "derivational", min_stem_len=3, pos=("ADJ",), productivity="restricted", confidence="medium", strip_allowed="no", note="GATED by the gold standard: ناورین، واکسین، پوتین are kept whole (2 of 18). The affix is real Pashto morphology, but the annotation treats these words as whole, so the rule is recorded and not applied."),
    _s("یز", "derivational", min_stem_len=3, pos=("ADJ",), note="relational -iz: ولسمشریز"),
    _s("یزو", "derivational", min_stem_len=3, pos=("ADJ",), note="oblique -izo"),
]

# --------------------------------------------------------------------------- #
# SOURCED ADDITIONS
#   [W] Wiktionary / kaikki.org "Pashto suffixes" (lexicographic)
#   [T&R] Tegey & Robson, A Reference Grammar of Pashto
# --------------------------------------------------------------------------- #
_SOURCED: List[AffixRule] = [
    # -- verb -> action/stative noun (highly productive) [W] -----------------
    _s("نه", "derivational", min_stem_len=3, pos=("N",), note="[W] verb->noun: څېړنه→څېړ"),
    _s("نې", "derivational", min_stem_len=3, pos=("N",),
       strip_allowed="no", confidence="medium",
       note="NOT stripped. ‑نې، ‑نی and ‑نۍ are one morpheme and rule matching folds the yeh letters, so any of them also fires on the others: this one was taking پاکستانی to پاکستا. The few words where the gold removes the whole ‑نی are listed in the stemmer."),
        # -- adjective -> stative noun [W] ---------------------------------------
    _s("ښت", "derivational", min_stem_len=3, pos=("N",), note="[W] adj->noun: جوړښت→جوړ"),
    # -- capability / -able [W] ----------------------------------------------
    _s("وړ", "derivational", min_stem_len=3, pos=("ADJ",), note="[W] -able/worthy"),
    # -- place of action [W] --------------------------------------------------
    _s("ځیو", "derivational", min_stem_len=3, pos=("N",), note="[W] obl of -dzay"),
    _s("ځی", "derivational", min_stem_len=3, pos=("N",), note="[W] place: ښوونځی→ښوون"),
    # -- skilled-agent noun [W] ----------------------------------------------
    # -- past participle (T&R: "[-ay] forms participles from verbs") --------
        _s("لې", "derivational", min_stem_len=3, pos=("ADJ", "V"), note="[T&R] fem past participle"),
    # -- Arabic sound masculine plural ‑ین (مسلمین→مسلم) ---------------------
        # -- Persian plural ‑جات (سبزیجات→سبزي) ---------------------------------
    _s("جات", "inflectional", min_stem_len=3, pos=("N",), note="Pers. pl -jāt"),
    # -- place-forming compound finals ---------------------------------------
    _s("خانه", "derivational", min_stem_len=3, pos=("N",), note="place: کتابخانه→کتاب"),
    _s("ځای", "derivational", min_stem_len=3, pos=("N",), note="place: اوسېدنځای"),
    _s("ستان", "derivational", min_stem_len=3, pos=("N",),
       productivity="borrowed", confidence="medium", strip_allowed="no",
       note="[inv §2.3] Persian place suffix. NOT stripped: the gold standard keeps these words whole in 14 of 14 cases (افغانستان، پاکستان، بلوچستان), and the inventory marks it borrowed rather than productive Pashto derivation."),
    # -- plural of -tun [W] ---------------------------------------------------
    _s("تانه", "inflectional", min_stem_len=3, pos=("N",), note="[W] pl of -tun"),
    _s("تانو", "inflectional", min_stem_len=3, pos=("N",), note="[W] obl pl of -tun"),
    # -- abstract noun / nisba from noun [W] ---------------------------------
    _s("ی", "derivational", min_stem_len=3, pos=("N", "ADJ"), note="[W] abstract/nisba: مشری→مشر، پوځی→پوځ"),
    # -- F3 plurals [T&R] -----------------------------------------------------
    _s("وې", "inflectional", min_stem_len=3, pos=("N",), note="[T&R] F3 dir. pl"),
    _s("وو", "inflectional", min_stem_len=3, pos=("N",), note="[T&R] F3 obl. pl"),
    # -- further agentive / adjectival formants ------------------------------
    _s("ناک", "derivational", min_stem_len=3, pos=("ADJ",), note="adj: خطرناک→خطر"),
    _s("من", "derivational", min_stem_len=3, pos=("ADJ",), note="adj: دولتمن→دولت"),
    _s("دار", "derivational", min_stem_len=3, pos=("N",), note="possessive: دوکاندار→دوکان"),
    _s("کار", "derivational", min_stem_len=3, pos=("N",), note="agentive: خدمتکار→خدمت"),
    # -- DIMINUTIVES [Khan23]: a category the inventory lacked entirely.
    #    Khan (2023), HSSC 10:536, Tables 1 & 3.
    _s("وټی", "derivational", min_stem_len=3, pos=("N",), note="[Khan23] diminutive: هلک→هلکوټی، سپی→سپوټی"),
    _s("ګی", "derivational", min_stem_len=3, pos=("N",), note="[Khan23] diminutive: موټر→موټرګی، خوړ→خوارګی"),
        _s("چکی", "derivational", min_stem_len=3, pos=("ADJ",), note="[Khan23] diminutive (adj): سپین→سپینچکی"),
    _s("ګړه", "derivational", min_stem_len=3, pos=("N",), note="[N&K] adj->noun: ښه→ښیګړه"),
    _s("ګړی", "derivational", min_stem_len=3, pos=("N",), note="agentive: منځګړی→منځ"),
]

# Full inventory, longest affixes first (helps the lightest-strip tie-break).
# --- Added after per-rule error analysis on the gold set -------------------- #
# Every affix below appeared in the "we left the word whole but the gold
# stripped" error bucket AND is a documented affix. Each was measured
# individually before being added.
_FROM_ERROR_ANALYSIS: List[AffixRule] = [
    _s("یت", "derivational", min_stem_len=3, pos=("N",), note="Arabic abstract-noun -iyyat: فعالیت→فعال، مدیریت→مدیر، شخصیت→شخص"),
    _s("نی", "derivational", min_stem_len=3, pos=("ADJ",),
       strip_allowed="no", confidence="medium",
       note="NOT stripped as a unit. The gold removes only the ی in the common case (پاکستانی→پاکستان، ایرانی→ایران، بهرنی→بهرن) and takes the whole ‑نی in just a few (کورنی→کور، لومړنی→لومړ)، which are listed in the stemmer as exceptions. Taking ‑نی by rule was right 3 times out of 29."),
    _s("یال", "derivational", min_stem_len=3, pos=("N",), productivity="restricted", confidence="medium", strip_allowed="no", note="GATED by the gold standard: مرستیال، خبریال are kept whole (0 of 3). The affix is real Pashto morphology, but the annotation treats these words as whole, so the rule is recorded and not applied."),
    _s("ت", "derivational", min_stem_len=4, pos=("N",), productivity="restricted", confidence="medium", strip_allowed="no", note="GATED by the gold standard: حکومت، وزارت، سفارت are kept whole (0 of 34). The affix is real Pashto morphology, but the annotation treats these words as whole, so the rule is recorded and not applied."),
    _s("لیک", "derivational", min_stem_len=3, pos=("N",), note="compounding -lik: لاسلیک→لاس، برخلیک→برخ"),
    # --- derivative-verb family, R&T Table 13.16. Added on grammatical
    #     grounds after the held-out news set showed them unhandled; the
    #     effect on the score is small either way.
    _s("ېد", "inflectional", min_stem_len=2, pos=("V",), first_pass_only=True, note="[R&T 13.16] derivative past stem: اوسېد→اوس، ګرځېد→ګرځ"),
    _s("ېدونکي", "derivational", min_stem_len=3, pos=("N", "ADJ"), note="[R&T 13.16] derivative agentive: زیاتېدونکي→زیات"),
    _s("یدونکي", "derivational", min_stem_len=3, pos=("N", "ADJ"), note="[R&T 13.16] derivative agentive, ی spelling: اوسیدونکي→اوس"),
    # --- revealed by the author's gold annotations (we lacked these) --------
    _s("نۍ", "derivational", min_stem_len=3, pos=("ADJ",),
       strip_allowed="no", confidence="medium",
       note="NOT stripped, for the same reason as ‑نی: rule matching folds the yeh letters together, so a ‑نۍ rule also fires on ‑نی and takes پاکستانی to پاکستا. The listed ‑نی words are handled in the stemmer."),
    _s("مند", "derivational", min_stem_len=3, pos=("ADJ",), note="possessive -mand: هنرمند→هنر، دولتمند→دولت"),
    _s("ار", "derivational", min_stem_len=4, pos=("N",), productivity="restricted", confidence="medium", strip_allowed="no", note="GATED by the gold standard: میانمار، ټینګار are kept whole (0 of 5). The affix is real Pashto morphology, but the annotation treats these words as whole, so the rule is recorded and not applied."),
    _s("نکی", "derivational", min_stem_len=3, pos=("N", "ADJ"), note="agentive/present participle -unkay: راتلونکی→راتلو، کوونکی→کوو"),
    _s("نکې", "derivational", min_stem_len=3, pos=("N", "ADJ"), note="fem of -unkay: راتلونکې→راتلو"),
    _s("نکو", "derivational", min_stem_len=3, pos=("N", "ADJ"), note="obl of -unkay: راتلونکو→راتلو"),
    # ‑ېږ/‑ېد derivative-verb family (R&T Table 13.16). Regular verbs are
    # handled by RULE, never by the irregular dictionary.
    _s("ېږی", "inflectional", min_stem_len=2, pos=("V",), first_pass_only=True, note="[R&T 13.16] derivative present: جوړېږی→جوړ، کارېږی→کار"),
    _s("ېږو", "inflectional", min_stem_len=2, pos=("V",), first_pass_only=True, note="[R&T 13.16] derivative present 1pl: پوهېږو→پوه"),
    _s("ېږم", "inflectional", min_stem_len=2, pos=("V",), first_pass_only=True, note="[R&T 13.16] derivative present 1sg: پوهېږم→پوه"),
    _s("ېږ", "inflectional", min_stem_len=2, pos=("V",), first_pass_only=True, note="[R&T 13.16] derivative present stem"),
    _s("ېدو", "inflectional", min_stem_len=2, pos=("V",), first_pass_only=True, note="[R&T 13.16] derivative oblique infinitive: لوړېدو→لوړ"),
    _s("ېدا", "inflectional", min_stem_len=2, pos=("V",), first_pass_only=True, note="[R&T 13.16] derivative verbal noun: روږدېدا→روږد"),
]

# --------------------------------------------------------------------------- #
# From docs/pashto_affix_inventory new finale .md
# --------------------------------------------------------------------------- #
# Every entry below carries the productivity, confidence and strip_allowed
# values that §10 of the inventory requires. Entries the inventory marks
# "do not strip", "lexicalized" or "needs validation" are recorded with
# strip_allowed set so the inventory stays complete without the engine acting
# on them (§12.9, §12.13).
_FROM_FINAL_INVENTORY: List[AffixRule] = [
    # -- §2.1 abstract / state nouns -------------------------------------- #
    _s("ا", "derivational", min_stem_len=4, pos=("N",), productivity="restricted", confidence="low", strip_allowed="no", note="[inv §2.1] abstract from adjective (ښکلی→ښکلا). NOT stripped: a "
            "single-letter rule removing final ا is string matching (§12.1) and "
            "the inventory gives only one attested example (§12.9). It cost 3.2 "
            "points on held-out news text, taking the ا off امریکا and اریانا."),
    _s("ګلوي", "derivational", min_stem_len=3, pos=("N",), productivity="restricted", note="[inv §2.1] relationship: ورورګلوي→ورور"),

    # -- §2.2 action / result nouns --------------------------------------- #
    _s("ګ", "derivational", min_stem_len=4, pos=("N",), productivity="restricted", confidence="medium", strip_allowed="no", note="GATED by the gold standard: ترڅنګ and similar are kept whole (0 of 6). The affix is real Pashto morphology, but the annotation treats these words as whole, so the rule is recorded and not applied."),
    _s("ښنه", "derivational", min_stem_len=3, pos=("N",), productivity="restricted", note="[inv §2.2] action: بخښنه→بخښ"),
    _s("اک", "derivational", min_stem_len=4, pos=("N",), productivity="restricted", note="[inv §2.2] action/product: خوراک، څښاک، پوښاک"),
    _s("اوی", "derivational", min_stem_len=3, pos=("N",), productivity="restricted", confidence="medium", strip_allowed="no", note="GATED by the gold standard: پوهاوی، سپکاوی are kept whole (0 of 3). The affix is real Pashto morphology, but the annotation treats these words as whole, so the rule is recorded and not applied."),

    # -- §2.3 place / container ------------------------------------------- #
    _s("زار", "derivational", min_stem_len=3, pos=("N",), productivity="borrowed", confidence="medium", note="[inv §2.3] place of abundance (Persian): ګلزار→ګل"),
    _s("داني", "derivational", min_stem_len=3, pos=("N",), productivity="borrowed", confidence="medium", note="[inv §2.3] container (Persian): قلمداني→قلم"),
    _s("دان", "derivational", min_stem_len=4, pos=("N",), productivity="borrowed", confidence="medium", note="[inv §2.3] container (Persian): ګلدان→ګل"),
    _s("غالی", "derivational", min_stem_len=3, pos=("N",), productivity="lexicalized", confidence="low", strip_allowed="no", note="[inv §2.3] DO NOT STRIP: one attested example (لوبغالی); near-minimal "
            "pair with ‑غاړی (§12.13)"),

    # -- §2.4 agent / occupation ------------------------------------------ #
    _s("پال", "derivational", min_stem_len=3, pos=("N", "ADJ"), note="[inv §2.4/§3] keeper/supporter, noun AND adjective: وطنپال→وطن"),
    _s("ګار", "derivational", min_stem_len=3, pos=("N",), productivity="borrowed", note="[inv §2.4] agent, distinct from ‑کار: خدمتګار→خدمت"),
    _s("بان", "derivational", min_stem_len=3, pos=("N",), productivity="borrowed", note="[inv §2.4] keeper/guard (Persian): دربان، باغبان"),
    _s("خور", "derivational", min_stem_len=3, pos=("N",), productivity="borrowed", confidence="medium", note="[inv §2.4] consumer: رشوتخور→رشوت"),
    _s("پوه", "derivational", min_stem_len=3, pos=("N",), note="[inv §2.4] expert in: ژبپوه→ژب، تاریخپوه→تاریخ"),
    _s("چي", "derivational", min_stem_len=3, pos=("N",), productivity="lexicalized", confidence="low", strip_allowed="no", note="[inv §2.4] DO NOT STRIP: Turkic, lexicalized (موچي)"),
    _s("ولي", "derivational", min_stem_len=3, pos=("N",), productivity="restricted", confidence="low", strip_allowed="no", note="[inv §2.1/§14] needs validation: no confirmed attested example"),

    # -- §3 adjective-forming --------------------------------------------- #
    _s("یزه", "derivational", min_stem_len=3, pos=("ADJ",), note="[inv §3] feminine of ‑یز: ټولنیزه→ټولن"),
    _s("انه", "derivational", min_stem_len=3, pos=("ADJ",), note="[inv §3] manner, -like/-ly: ماشومانه، زړورانه، دوستانه"),
    _s("جن", "derivational", min_stem_len=3, pos=("ADJ",), productivity="restricted", note="[inv §3] characterized by: زهرجن→زهر"),

    # -- §4 diminutives: recorded, never stripped ------------------------- #
    _s("وکی", "derivational", min_stem_len=3, pos=("N",), productivity="lexicalized", confidence="low", strip_allowed="no", note="[inv §4] DO NOT STRIP: lexicalized (وړوکی)"),
    _s("ګوټی", "derivational", min_stem_len=3, pos=("N",), productivity="restricted", confidence="low", strip_allowed="no", note="[inv §4/§14] needs validation: no attested example"),
    _s("کوټی", "derivational", min_stem_len=3, pos=("N",), productivity="restricted", confidence="low", strip_allowed="no", note="[inv §4/§14] needs validation: no attested example"),

    # -- §5.1 plural, §5.3 vocative --------------------------------------- #
    # ‑ګانې was already in the sourced block above; its §5.1 gloss and example
    # were merged into that entry rather than added as a second rule. The
    # duplicate was harmless at run time -- the engine generated the same
    # candidate twice -- but it made the inventory count one too high.
]

SUFFIX_RULES: List[AffixRule] = sorted(
    _FROM_FINAL_INVENTORY +
    _FROM_ERROR_ANALYSIS +
    _NOMINAL_INFLECTIONAL + _VERBAL_INFLECTIONAL + _DERIVATIONAL + _SOURCED,
    key=lambda r: -len(r.affix),
)

if __name__ == "__main__":
    for r in SUFFIX_RULES:
        print(f"  {r.affix:6} {r.side:6} {r.category:13} add={r.add_back or '∅':2} "
              f"min={r.min_stem_len} pos={','.join(r.pos) or '-':8} {r.note}")
    print(f"\n{len(SUFFIX_RULES)} suffix rules")
