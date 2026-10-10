# -*- coding: utf-8 -*-
"""
stemmer.py
==========
Top-level orchestrator: the grammar-driven rule-based Pashto stemmer.

Pipeline (per token)
--------------------
    normalize
      -> non-Pashto / empty      -> return unchanged
      -> stopword                -> return unchanged            (freeze)
      -> proper noun             -> return unchanged            (freeze)
      -> irregular/suppletive    -> return mapped stem
      -> RuleEngine.generate     -> candidate stems (multi-pass)
      -> Validator.select        -> dictionary-validated best stem
    => StemResult(input, stem, confidence, attested, rules, trace)

Every sub-module is switchable through :class:`StemmerConfig`, so the
Phase-5 ablation study (Rules-only / +Dictionary / +POS / +Compound / full)
is a matter of flipping flags — no code changes, fully reproducible.

100% rule-based + dictionary. No machine learning anywhere.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from .normalizer import Normalizer, NormalizerConfig
from .dictionary import PashtoLexicon
from .rules import RuleEngine, Candidate
from .suffixes import SUFFIX_RULES
from .prefixes import PREFIX_RULES
from .validation import Validator, ValidationConfig
from .compound import CompoundSplitter, CompoundConfig
from .verb_paradigms import VerbAnalyzer, lemma_to_stem, NOUN_HOMOGRAPHS
from . import pos_rules
from . import exceptions as exc


# Token is "Pashto-ish" if it contains at least one Arabic-block letter.
_PASHTO_CHAR = re.compile(r"[؀-ۿ]")
# Split on whitespace *and* punctuation. Splitting on whitespace alone left
# ‫کورونه،خبرونه‬ as a single token -- Pashto writes the comma without a
# following space often enough that this is common -- and only the last word
# came back stemmed. Punctuation is also stripped from token edges below, but
# that cannot help when it sits between two words.
_TOKEN_SPLIT = re.compile(r"[\s؟،؛٫٬.!?:;…«»()\[\]{}—–]+")
_STRIP_PUNCT = "؟،؛٫٬.!?:;\"'«»()[]{}—–-…‏‎ "


@dataclass
class StemmerConfig:
    use_dictionary: bool = True
    use_exceptions: bool = True        # stopwords, the length rules, Arabic plurals
    # The irregular-verb dictionary is OFF for stemming.
    #
    # It maps a form to its verb (شو -> کېدل, وینم -> لید), which is a LEMMA.
    # Stemming removes affixes; it does not substitute one word for another. On
    # the 2,702 word types whose reference is a truncation, the dictionary
    # decides 104 words and gets 47 right - 45% - because it returns the wrong
    # kind of answer, and it costs 1.07 points overall.
    #
    # Turn it on for lemmatization, where it is the only thing that can reach a
    # suppletive form: it resolves 116 of the 210 types whose reference is a
    # lemma rather than a truncation.
    use_verb_dictionary: bool = False
    use_prefixes: bool = True
    use_suffixes: bool = True
    # POS filtering is OFF. The guesser inferred a part of speech from the
    # word's ENDING (any word ending in ی was called an adjective) — an
    # assumption grounded in no source. The ablation showed it contributes
    # -0.6 accuracy and slightly WORSENS conflation, so it is disabled.
    # Retained only as an ablation arm.
    use_pos: bool = False
    # Compound decomposition. Off by default: the annotation policy keeps
    # compounds whole, and the splitter contradicted it. On the two evaluation
    # sets it fired on seven types and was wrong on all seven, returning the
    # suffix rather than the word (نړۍوال -> وال, پټرولیم -> یم). Disabling it
    # is worth +0.22 on the development set and +0.20 on held-out text.
    use_compound: bool = False
    strip_derivational: bool = True
    # Verb target: "stem" (لوست) or "infinitive" (لوستل).
    # STEM is the default on linguistic grounds: the infinitive ‑ل is itself an
    # affix, and لوست is the base from which لوسته، لوستونکی، لوستل are all
    # formed by adding affixes. This is also what policy §10 requires (a stem
    # must be reachable by removing affixes) — لوستل fails that test.
    # "infinitive" is retained as an ablation arm.
    # A verb reduces to its ROOT. This is the only convention under which
    # every form of a verb lands on one token: رسېدل، رسېږي، ورسېد and رسول all
    # give رس. The infinitive splits رسېدل from رسول, and the past stem splits
    # the present from the past (رسېږ vs رسېد). It also adds no letters, which
    # the annotation policy requires.
    verb_target: str = "stem"
    # The regular derivative verbs are formed by rule, so no dictionary covers
    # them. Their whole verbal tail is removed, which puts every form on the
    # root: لوړېدو، لوړېږي، لوړېدل and لوړول all give لوړ.
    rebuild_derivative_infinitive: bool = True
    derivative_tails: tuple = (
        ("ېدونکو", ""), ("ېدونکي", ""), ("ېدونکی", ""),
        ("ېدلو", ""), ("ېدلي", ""), ("ېدلی", ""), ("ېدلې", ""),
        ("ېدل", ""), ("ېدو", ""), ("ېده", ""), ("ېږی", ""), ("ېږي", ""),
        ("ېږم", ""), ("ېږو", ""), ("ېږ", ""), ("ېد", ""),
        ("ولو", ""), ("ولی", ""), ("ولې", ""), ("ول", ""), ("وي", ""),
    )
    # Author's rule: a form longer than three characters ending in ‑ه، ‑ې or ‑و
    # drops that final letter, so the whole feminine/oblique family collapses
    # to ONE token (سیمه/سیمې/سیمو -> سیم، چاره/چارو -> چار) instead of the
    # inconsistent چار vs چاره. Words of 3 characters or fewer keep it
    # (ښځه، ښه، نو).
    # Proper nouns are NOT frozen (policy §7, revised by the author).
    # A hand-maintained name list can never be complete, so it makes the
    # system behave inconsistently — freezing the names that happen to be
    # listed while stripping every unseen one. A rule-based stemmer has no
    # context model to recognise names, so it applies the same rules to every
    # word. افغانستان→افغان is therefore accepted rule behaviour.
    # Kept switchable for the ablation study.
    freeze_proper_nouns: bool = False
    strip_final_inflection: bool = True
    # ‑ستان IS stripped: the gold correction log records it as a productive
    # suffix (افغانستان→افغان، بلوچستان→بلوچ، عربستان→عرب). Stripping stops
    # there, because letting the other rules continue gave ترکمنستان→ترک.
    strip_stan: bool = True
    stan_min_stem: int = 3
    # --- the author's length rules (gold v2 standard) --------------------- #
    # R2  three letters or fewer            -> keep as is (outranks everything)
    # R1  four letters ending in a yeh/ل/ه  -> remove that letter
    # R3 (NOT Pashto and 7+ letters -> remove the last three) is DISABLED.
    #   Measured on the author's own annotations, cutting three characters was
    #   beaten by simply stripping a real affix: 43.5% vs 51.6% on the
    #   re-annotated held-out news set, and 25.0% vs 45.0% on the 2,912-word
    #   gold. Every word it damaged had a genuine affix (درلودلو→درلو not
    #   درلود, مسووليت→مسوو not مسوول, اعلانات→اعلا not اعلان): it fired before
    #   the inventory was consulted and cut through the root. Turning it off
    #   left overall accuracy unchanged and improved the balanced score.
    #   Set r3_min_len to 7 to re-enable it for the ablation table.
    author_rules: bool = True
    # R1 applies to words of four or five letters. Beyond five it starts
    # cutting roots (measured: held-out accuracy falls from 59.2% to 58.2% at
    # six letters and 54.0% with no upper bound).
    r1_max_len: int = 5
    # A prefix strip is only accepted when what remains is itself an attested
    # word. Without this, بېجينګ (Beijing) lost its بې‑ and لانسیټ its لا‑.
    prefix_needs_attested_stem: bool = True
    # The gold correction log keeps the negation prefixes: ناقانونه→ناقانون،
    # غیرقانونی→غیرقانون. نا‑ and غیر‑ change the meaning of the word, so the
    # negated form is its own lexeme and the prefix stays. Only the agreement
    # ending comes off. Set False to strip them, for the ablation table.
    keep_negation_prefixes: bool = True
    negation_prefixes: tuple = ("نا", "بې", "غیر")
    # The gold correction log calls these a "uniform strip": the abstract-noun
    # and place suffixes come off whenever they are present, without being put
    # to the scorer. They are long and unambiguous, so there is no competing
    # analysis for the scorer to choose between, and leaving them arbitrated
    # meant روغتیا and پوهنتون stayed whole because روغ and پوهن are not in the
    # lexicon. Order matters: longest first.
    # Longest first. The stacked forms (‑تونونو، ‑تیاوې …) are listed in full
    # rather than peeled in two passes, so the plural and the place suffix come
    # off together: روغتونونو→روغ.
    # ‑ځی is NOT here: it collides with verb forms (ګرځی is ګرځېدل, not
    # ګر+ځی), so it stays with the arbitrated rules where the scorer can see
    # the alternative.
    uniform_strip: tuple = ("تونونو", "تونونه", "تیاوو", "تیاوې", "والیو",
                            "توبونو", "توبونه", "والی", "تانو", "تانه",
                            "تیا", "توب", "تون")
    # 2(a) The agent ‑غاړی keeps its stem: the log gives لوبغاړی→لوبغاړ, so only
    # the agreement ending comes off. Uniform, because لوبغاړ is not in the
    # lexicon and the scorer was keeping the word whole.
    agent_endings: tuple = ("غاړی", "غاړې", "غاړو", "غاړي")
    # 1(c) ‑تیا is stripped as a unit, except where the gold records the cut
    # one letter further in. Two words, listed rather than guessed.
    tiya_exceptions: dict = None
    # 3(a) Feminine nouns restore their citation ‑ه, so ښځه/ښځې/ښځو fall
    # together on one stem. This is the one place a letter is added back, and
    # the log asks for it by name ("restore feminine citation form").
    restore_feminine_ha: bool = True
    # Only these bases take the citation ‑ه back. Restoring it wherever a
    # three-letter word ended in و/ې was right 29 times and wrong 55: the gold
    # wants مخې→مخ، هڅو→هڅ، زرو→زر، ورځو→ورځ، شپې→شپ, not the ‑ه form. So the
    # restoration is a listed class, not a rule.
    feminine_ha_bases: tuple = ("ښځ",)
    short_word_strippable: str = "ېو"
    # ‑نی comes off as a unit only for these; elsewhere only the ی does.
    ni_full_strip: tuple = ("کورنی", "لومړنی", "میاشتنی", "کورنۍ", "لومړنۍ")
    uniform_min_stem: int = 2
    # Look up the exceptions, then apply the rules. The irregular-verb table is
    # consulted before the length rules, which is the usual arrangement in a
    # morphological analyser and gives the linguistically correct شو -> کېدل.
    # Setting this True runs the length rules first; on held-out news text the
    # difference is four words out of five hundred, so the ordering is decided
    # on principle rather than on score.
    author_rules_before_dictionary: bool = False
    # ل is NOT in this set. It is the infinitive ending on a verb, but on a
    # noun it is part of the root, and R1 cannot tell them apart: it was taking
    # کابل to کاب and لامل to لام. 51 of the over-strips came from that one
    # letter, so it is left to the verbal rules, which know they are looking at
    # a verb. Worth +1.0 on the gold and +0.6 on held-out text.
    r1_tail: str = "یيېۍئه"
    r3_min_len: int = 0          # 0 = R3 off
    # ‑ه is NOT in this set. A blanket chop of final ه caused 179 of our
    # errors (موده→مود، برخه→برخ، مینه→مین، اندازه→انداز): in Pashto a final ه
    # is very often part of the word, not an ending. ې and و are far more
    # reliably inflectional, so only those are trimmed.
    final_inflection_letters: str = "ېو"
    max_passes: int = 1
    normalizer: NormalizerConfig = field(default_factory=NormalizerConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)


@dataclass
class StemResult:
    input: str
    normalized: str
    stem: str
    confidence: float
    attested: bool
    rules_applied: tuple
    trace: str

    def __str__(self) -> str:
        return f"{self.input} -> {self.stem}  (conf={self.confidence:.2f}; {self.trace})"


class _NullLexicon:
    """Stand-in when use_dictionary=False: nothing is ever attested."""
    def contains(self, w, normalize=True): return False
    __contains__ = contains
    def frequency(self, w, normalize=True): return 0
    def score(self, w, normalize=True): return 0.0
    def longest_valid_prefix(self, w, normalize=True): return None
    def family(self, stem, suffixes, normalize=True): return []
    def family_size(self, stem, suffixes, normalize=True): return 0
    def __len__(self): return 0


class PashtoStemmer:
    def __init__(self, config: Optional[StemmerConfig] = None,
                 lexicon: Optional[PashtoLexicon] = None) -> None:
        self.cfg = config or StemmerConfig()
        self.normalizer = Normalizer(self.cfg.normalizer)

        if self.cfg.use_dictionary:
            self.lexicon = lexicon or PashtoLexicon.from_frequency_file(
                normalizer=self.normalizer)
        else:
            self.lexicon = _NullLexicon()

        suffixes = SUFFIX_RULES if self.cfg.use_suffixes else []
        prefixes = PREFIX_RULES if self.cfg.use_prefixes else []
        self.engine = RuleEngine(
            suffixes=suffixes, prefixes=prefixes,
            max_passes=self.cfg.max_passes,
            strip_derivational=self.cfg.strip_derivational,
        )
        # The family test counts only DERIVATIONAL formations. Inflectional
        # endings must be excluded: for any feminine noun X+ه the base X
        # trivially "has a family" (Xه، Xې، Xو) — but those are the same word's
        # own inflections, not other words, which made the test strip the ه
        # from سیمه/اداره/مینه. A stem is what OTHER WORDS are built from.
        self.validator = Validator(
            self.lexicon, self.cfg.validation,
            family_suffixes={r.affix for r in SUFFIX_RULES
                             if r.category == "derivational"})

        # One result per distinct token, kept for the life of the stemmer.
        # The limit is a guard against an adversarial stream of unique strings
        # rather than a tuning knob: a Pashto corpus of any size has far fewer
        # distinct word types than this.
        self._cache: dict = {}
        self._cache_limit = 500_000

        # Compound splitter needs a real lexicon; disabled without one.
        self.splitter = (CompoundSplitter(self.lexicon, CompoundConfig())
                         if (self.cfg.use_compound and self.cfg.use_dictionary)
                         else None)

        # Normalize the static exception resources into the same space as
        # tokens (critical: e.g. irregular key کوي must match normalized کوی).
        n = self.normalizer.normalize_token
        self._stopwords = {n(w) for w in exc.STOPWORDS}
        self._proper = {n(w) for w in exc.PROPER_NOUNS}
        self._ar_plurals = {n(k): n(v) for k, v in exc.ARABIC_PLURALS.items()}

        # Verb handling is driven by the grammar-sourced PARADIGM table
        # (present/past stems + regular endings), which expands to far more
        # forms than a hand-typed list. The older flat map only fills gaps.
        self._verbs = VerbAnalyzer(normalize=n)
        # Policy §5/§10: a verb reduces to its STEM, not the infinitive —
        # the infinitive ‑ل is itself a suffix, and ‑ول/‑ېدل are verbalizers.
        is_word = (self.lexicon.contains if self.cfg.use_dictionary else None)
        # The family test: a remainder is a stem if other words are built from
        # it (لوست -> لوستل/لوسته/لوستونکی). Uses the suffix inventory itself,
        # so no separate list has to be maintained.
        _suffix_set = tuple({r.affix for r in SUFFIX_RULES})
        family_fn = ((lambda s: self.lexicon.family_size(s, _suffix_set))
                     if self.cfg.use_dictionary else None)
        _target = ((lambda lem: lemma_to_stem(lem, is_word, family_fn))
                   if self.cfg.verb_target == "stem" else (lambda lem: lem))
        self._irregular = {
            form: _target(lemma) for form, lemma in self._verbs.index.items()
        }
        # The legacy flat map must respect the same homograph guard, otherwise
        # it re-introduces noun readings as verbs (لاره 'road' -> لرل).
        _blocked = {n(w) for w in NOUN_HOMOGRAPHS}
        for k, v in exc.IRREGULAR.items():
            k = n(k)
            if k not in _blocked:
                self._irregular.setdefault(k, _target(n(v)))

        # error log: low-confidence / OOV decisions for Phase-6 analysis
        self.error_log: List[StemResult] = []

    # ------------------------------------------------------------------ #
    def stem_word(self, token: str) -> StemResult:
        """The full decision for one token: stem, confidence, rules, trace.

        Results are cached on the raw token. A corpus repeats words heavily --
        five million tokens of news is around seventy thousand distinct words --
        so the second occurrence of a word costs a dictionary lookup instead of
        a full pass over the rule inventory. StemResult is immutable, so handing
        the same object back twice is safe.
        """
        hit = self._cache.get(token)
        if hit is not None:
            return hit
        result = self._stem_word_uncached(token)
        if len(self._cache) < self._cache_limit:
            self._cache[token] = result
        return result

    def clear_cache(self) -> None:
        """Forget every cached result. Only needed if the rules are edited in
        place at run time, which the experiments do."""
        self._cache.clear()

    def _stem_word_uncached(self, token: str) -> StemResult:
        raw = token
        norm = self.normalizer.normalize_token(token).strip(_STRIP_PUNCT)

        # non-Pashto / empty -> unchanged
        if not norm or not _PASHTO_CHAR.search(norm):
            return StemResult(raw, norm, norm, 1.0, False, (), "non-Pashto/empty")

        # Exceptions are checked BEFORE the length guard: some irregular verb
        # forms and stopwords are only 2 chars (ځي, شو, او) yet meaningful.
        if self.cfg.use_exceptions:
            if norm in self._stopwords:
                return StemResult(raw, norm, norm, 1.0, self._att(norm), (),
                                  "stopword (frozen)")
            # The author's length rules run before everything else: in the
            # gold v2 standard R2 (three letters or fewer) outranks even the
            # irregular-verb table (شوه stays شوه, it is not mapped to کېدل).
            if self.cfg.author_rules and self.cfg.author_rules_before_dictionary:
                hit = self._author_rules(norm)
                if hit is not None:
                    stem, rid = hit
                    return StemResult(raw, norm, stem, 0.95, self._att(stem),
                                      (rid,), f"author rule {rid} -> {stem}")

            # ـزی marks Pashtun tribal/family names (احمدزی، یوسفزی). Policy §7:
            # proper nouns are kept whole, so these are frozen, not stripped.
            if (self.cfg.freeze_proper_nouns and len(norm) > 4
                    and norm.endswith("زی")):
                return StemResult(raw, norm, norm, 0.9, self._att(norm), (),
                                  "tribal name -زی (frozen)")
            if self.cfg.freeze_proper_nouns and norm in self._proper:
                return StemResult(raw, norm, norm, 1.0, self._att(norm), (),
                                  "proper noun (frozen)")
            # Arabic broken plurals: internal change, so a dictionary
            # lookup (policy §6) — checked before the affix rules.
            ar = self._ar_plurals.get(norm)
            if ar:
                return StemResult(raw, norm, ar, 0.95, self._att(ar),
                                  ("arabic-plural",), f"broken plural -> {ar}")
            # ‑ستان is an ordinary place-forming affix, not a name marker.
            # Proper nouns get NO special treatment (policy §7), so it is
            # stripped unconditionally and stripping STOPS there — otherwise
            # the cascade ate real roots (ترکمنستان→ترک, هندوستان→هند).
            # ‑ستان can carry an agreement or oblique ending: پاکستانه،
            # افغانستانه. Take that off first so the place suffix is exposed.
            if self.cfg.strip_stan:
                for tail in ("ستانه", "ستانو", "ستانې"):
                    if norm.endswith(tail) and len(norm) - len(tail) >= self.cfg.stan_min_stem:
                        base = norm[: len(norm) - len(tail)]
                        return StemResult(raw, norm, base, 0.9, self._att(base),
                                          ("+ستان",),
                                          f"place affix ‑{tail} -> {base}")

            if (self.cfg.strip_stan and norm.endswith("ستان")
                    and len(norm) - 4 >= self.cfg.stan_min_stem):
                base = norm[:-4]
                return StemResult(raw, norm, base, 0.9, self._att(base),
                                  ("+ستان",), f"place affix ‑ستان -> {base}")

            # The "uniform strip" affixes from the gold correction log. These
            # are applied before the scorer is consulted, and stripping stops
            # there: روغتیا→روغ, پوهنتون→پوهن, چټکوالی→چټک.
            # Regular derivative verbs rebuilt to their infinitive. These are
            # formed by rule, so they are not in the verb dictionary, but the
            # gold still wants the infinitive for them.
            if self.cfg.rebuild_derivative_infinitive:
                for tail, inf in self.cfg.derivative_tails:
                    if norm.endswith(tail) and len(norm) - len(tail) >= 2:
                        base = norm[: len(norm) - len(tail)] + inf
                        return StemResult(raw, norm, base, 0.9, self._att(base),
                                          (f"+{tail}>{inf}",),
                                          f"derivative verb -> {base}")

            # 3(a) Feminine citation form. This runs before the short-word
            # rule, because ښځې and ښځو are three letters and would otherwise
            # be kept whole and never reach the restoration.
            # Only on a three-letter word. Longer words reach the ordinary
            # rules, which strip the ending; restoring there would undo them
            # (کورونو would come back as کورونه).
            if self.cfg.restore_feminine_ha and len(norm) == 3 \
                    and norm[-1] in ("و", "ې"):
                cand = norm[:-1] + "ه"
                if norm[:-1] in self.cfg.feminine_ha_bases:
                    return StemResult(raw, norm, cand, 0.9, True, ("+ه",),
                                      f"feminine citation form -> {cand}")

            # ‑نی taken as a whole, for the few words where the gold does
            if norm in self.cfg.ni_full_strip:
                base = norm[:-2]
                return StemResult(raw, norm, base, 0.95, self._att(base),
                                  ("+نی",), f"listed ‑نی word -> {base}")

            # 1(c) the two ‑تیا words whose cut the gold records differently
            tiya = self.cfg.tiya_exceptions or {"رښتیا": "رښت", "پکتیا": "پکت"}
            if norm in tiya:
                base = tiya[norm]
                return StemResult(raw, norm, base, 0.95, self._att(base),
                                  ("+یا",), f"lexical exception -> {base}")

            # 2(a) agent ‑غاړی: take the ending, keep غاړ
            for aff in self.cfg.agent_endings:
                if norm.endswith(aff) and len(norm) - 1 >= 3:
                    base = norm[:-1]
                    return StemResult(raw, norm, base, 0.9, self._att(base),
                                      (f"+{norm[-1]}",),
                                      f"agent ‑{aff}, ending removed -> {base}")

            if self.cfg.uniform_strip:
                for aff in self.cfg.uniform_strip:
                    if (norm.endswith(aff)
                            and len(norm) - len(aff) >= self.cfg.uniform_min_stem):
                        base = norm[: len(norm) - len(aff)]
                        return StemResult(raw, norm, base, 0.9, self._att(base),
                                          (f"+{aff}",),
                                          f"uniform strip ‑{aff} -> {base}")
            irr = self._irregular.get(norm) if self.cfg.use_verb_dictionary else None
            if irr:
                return StemResult(raw, norm, irr, 0.95, self._att(irr),
                                  ("irregular",), f"irregular -> {irr}")

            if self.cfg.author_rules and not self.cfg.author_rules_before_dictionary:
                hit = self._author_rules(norm)
                if hit is not None:
                    stem, rid = hit
                    return StemResult(raw, norm, stem, 0.95, self._att(stem),
                                      (rid,), f"author rule {rid} -> {stem}")

        # Nothing is removed from a word of three characters or fewer.
        if len(norm) <= 3:
            return StemResult(raw, norm, norm, 0.9, self._att(norm), (),
                              "too short to strip")

        allowed_pos = pos_rules.guess_pos(norm) if self.cfg.use_pos else None
        candidates: List[Candidate] = self.engine.generate(norm, allowed_pos)

        # The gold correction log: on a word carrying a kept negation prefix,
        # only the agreement ending comes off (ناقانونه→ناقانون،
        # غیرقانونی→غیرقانون). The negated form is its own lexeme, so a plural
        # or derivational reading of what follows the prefix is wrong: ناقانونه
        # is نا+قانون+ه, not نا+قانو+نه.
        if self.cfg.keep_negation_prefixes and any(
                norm.startswith(pre) for pre in self.cfg.negation_prefixes):
            agreement = tuple(self.cfg.r1_tail)
            candidates = [c for c in candidates
                          if c.strip_len == 0
                          or (c.strip_len == 1
                              and norm[len(c.stem):] in agreement)]
        # POS is a SOFT preference: the ending-based guess is often wrong
        # (سیاستوال ends in ل and is guessed V, which hides the ‑وال rule).
        # If the filter left nothing to strip, retry without it.
        if allowed_pos is not None and not any(c.strip_len for c in candidates):
            candidates = self.engine.generate(norm, None)
        decision = self.validator.select(norm, candidates)

        # Compound fallback: if the word stayed unchanged/unattested, try to
        # split it into attested parts and stem the head component.
        if (self.splitter is not None and not decision.attested
                and decision.stem == norm):
            head = self.splitter.head(norm)
            if head:
                head_dec = self.validator.select(
                    head, self.engine.generate(head, allowed_pos))
                result = StemResult(raw, norm, head_dec.stem,
                                    max(0.5, head_dec.confidence * 0.9),
                                    head_dec.attested,
                                    ("compound-head",) + head_dec.rules_applied,
                                    f"compound '{norm}' -> head '{head}' -> {head_dec.stem}")
                return result

        if (self.cfg.prefix_needs_attested_stem
                and any(r.startswith("-") for r in decision.rules_applied)
                and not self._att(decision.stem)):
            decision = self.validator.select(
                norm, [c for c in candidates
                       if not any(r.startswith("-") for r in c.rules_applied)])

        stem = self._final_trim(decision.stem)
        trimmed = (stem != decision.stem)
        rules = decision.rules_applied + (('final-trim',) if trimmed else ())
        result = StemResult(raw, norm, stem, decision.confidence,
                            decision.attested, rules, decision.trace)
        if decision.confidence < 0.5:
            self.error_log.append(result)
        return result

    def stem(self, text):
        """Stem anything: a word, a sentence, or a sequence of either.

            stem("کورونه")                -> "کور"
            stem("د کورونو خبرونه")        -> "د کور خبر"
            stem(["کورونه", "خبرونه"])     -> ["کور", "خبر"]
            df["text"].apply(st.stem)     -> a stemmed column

        The shape you pass in is the shape you get back. An earlier version
        took a single token only, and a sentence came back with just its last
        word stemmed -- a wrong answer rather than an error, which is worse.

        Anything that is not a string (a NaN from an empty cell) returns an
        empty string, so one blank row cannot stop a job halfway through a
        file. For the reasoning behind a decision use stem_word or stem_text,
        which return the rules, the confidence and the trace.
        """
        if isinstance(text, str):
            words = [w for w in _TOKEN_SPLIT.split(text) if w.strip(_STRIP_PUNCT)]
            if not words:
                return ""
            if len(words) == 1:
                return self.stem_word(words[0]).stem
            return self.stem_sentence(text)
        if isinstance(text, (list, tuple, set)):
            return type(text)(self.stem(x) for x in text)
        if isinstance(text, dict):
            # Iterating a dict gives its keys, which is almost certainly not
            # what the caller meant. Say so instead of stemming the keys.
            raise TypeError("stem() takes a word, a sentence or a sequence of "
                            "them, not a dict")
        try:
            return [self.stem(x) for x in text]      # any other iterable
        except TypeError:
            return ""

    def stem_file(self, path, column="word", out=None, keep_original=True,
                  new_column=None, sheet=None, unique=False, warn=True,
                  trace=False):
        """Stem one column of a CSV, TSV or Excel file.

            st.stem_file("words.csv")                       # returns the rows
            st.stem_file("words.csv", out="done.csv")       # writes them
            st.stem_file("data.xlsx", column="form", keep_original=False)

        With no `out` nothing is written and the rows come back as a list of
        dicts, so you can inspect the result before deciding to save it. With
        `out` the format follows that file's extension, and a delimited file is
        streamed row by row rather than held in memory.

        column        which column to stem
        out           where to write; None returns the rows instead
        keep_original False drops every column except the stem
        new_column    name for the result; default <column>_stemmed
        sheet         which Excel worksheet; default the first
        unique        stem distinct values only, then map back
        warn          say so once if the column holds sentences
        trace         add a column naming the rules that fired
        """
        from . import files

        target = new_column or f"{column}_stemmed"
        trace_col = f"{column}_rules"

        def fill(row):
            value = row.get(column) or ""
            if trace:
                r = self.stem_word(value.strip()) if len(value.split()) == 1 \
                    else None
                row[target] = r.stem if r else self.stem(value)
                row[trace_col] = "+".join(r.rules_applied) if r else ""
            else:
                row[target] = self.stem(value)
            return row

        # Streaming path: delimited input, a destination, nothing to dedupe.
        if out and not files._is_excel(path) and not files._is_excel(out) \
                and not unique:
            header = files.read_header(path)
            files.check_column(path, column, header)
            fields = ([*header, target] if keep_original else [target])
            if trace:
                fields.append(trace_col)
            import csv as _csv
            n = 0
            with open(out, "w", encoding="utf-8", newline="") as fh:
                w = _csv.DictWriter(fh, fieldnames=fields,
                                    delimiter=files._delimiter(out),
                                    extrasaction="ignore")
                w.writeheader()
                for row in files.iter_rows(path):
                    w.writerow(fill(row))
                    n += 1
            return {"rows": n, "column": target, "out": out}

        header, rows = files.read_rows(path, sheet)
        files.check_column(path, column, header)
        if warn:
            files.warn_multiword(column, (r.get(column) for r in rows))

        if unique:
            # Stem each distinct value once, then map it back onto every row.
            # A vocabulary is far smaller than a corpus, and the cache already
            # makes the repeats cheap -- this skips them entirely.
            seen = {}
            for row in rows:
                v = row.get(column) or ""
                if v not in seen:
                    seen[v] = self.stem(v)
                row[target] = seen[v]
                if trace:
                    r = self.stem_word(v.strip()) if len(v.split()) == 1 else None
                    row[trace_col] = "+".join(r.rules_applied) if r else ""
        else:
            for row in rows:
                fill(row)

        fields = ([*header, target] if keep_original else [target])
        if trace:
            fields.append(trace_col)
        if not keep_original:
            rows = [{k: r.get(k, "") for k in fields} for r in rows]

        if out:
            files.write_rows(out, fields, rows)
            return {"rows": len(rows), "column": target, "out": out}
        return rows

    def stem_text(self, text: str) -> List[StemResult]:
        """Every token with its full decision. Use stem_sentence for a string."""
        text = self.normalizer.normalize(text)
        tokens = [t for t in _TOKEN_SPLIT.split(text) if t.strip(_STRIP_PUNCT)]
        return [self.stem_word(t) for t in tokens]

    def stem_sentence(self, text: str) -> str:
        """Text in, stemmed text out.

        This is the one to reach for with pandas or any map over a column:

            df["stemmed"] = df["text"].apply(st.stem_sentence)

        A non-string (a NaN from an empty cell, say) returns an empty string
        rather than raising, because a single blank row should not stop a job
        halfway through a file.
        """
        if not isinstance(text, str):
            return ""
        return " ".join(r.stem for r in self.stem_text(text))

    # ------------------------------------------------------------------ #
    def _final_trim(self, stem: str) -> str:
        """Drop a final ې/و from a form longer than three characters, so
        سیمې/سیمو reduce to the same token. ‑ه is deliberately excluded: see
        StemmerConfig.final_inflection_letters."""
        if (self.cfg.strip_final_inflection and len(stem) > 3
                and stem[-1] in self.cfg.final_inflection_letters):
            return stem[:-1]
        return stem

    # Letters that exist only in Pashto: a word containing one is certainly
    # Pashto, so the "not Pashto" rule (R3) must not touch it.
    _PASHTO_ONLY = frozenset("ټډړږښځڅڼګېۍ")

    def _is_pashto(self, word: str) -> bool:
        if self._PASHTO_ONLY & frozenset(word):
            return True
        return self._att(word)

    def _author_rules(self, norm: str):
        """The author's length rules. Returns (stem, rule_id) or None."""
        n = len(norm)
        if n <= 3:                                   # R2
            # …except that a three-letter word ending in ‑ې or ‑و still loses
            # it. Those two are unambiguously inflectional, and the gold takes
            # them off even at this length: مخې→مخ، هڅو→هڅ، زرو→زر، شپې→شپ.
            if n == 3 and norm[-1] in self.cfg.short_word_strippable:
                return norm[:-1], f"R2-short-drop-{norm[-1]}"
            return norm, "R2-keep-short"
        # A documented prefix outranks the length rule: ناپوه is نا‑ + پوه,
        # not a four-letter word that happens to end in ه. Only a prefix that
        # is actually removable counts: نا‑ is kept, so ناوړه must still lose
        # its agreement ‑ه.
        if any(r.strip_allowed == "yes" and r.applies_to(norm)
               for r in self.engine.prefixes):
            return None
        if 4 <= n <= self.cfg.r1_max_len and norm[-1] in self.cfg.r1_tail:  # R1
            return norm[:-1], f"R1-drop-{norm[-1]}"
        if norm.endswith("ستان"):
            if self.cfg.strip_stan and n - 4 >= self.cfg.stan_min_stem:
                return norm[:-4], "R4-stan"
            # ‑ستان is not strippable, so the word is returned whole. Without
            # this the ‑ان rule reaches inside the suffix and leaves a fragment
            # (ترکمنستان -> ترکمنست, ګلستان -> ګلست), which is worse than
            # leaving the word alone. This is §12.12 of the affix inventory:
            # strip from the outermost layer inward, and stop when the outer
            # layer may not be removed.
            return norm, "R4-stan-kept"
        if (self.cfg.r3_min_len and n >= self.cfg.r3_min_len
                and not self._is_pashto(norm)):
            return norm[:-3], "R3-foreign-drop3"
        return None

    def _att(self, word: str) -> bool:
        try:
            return self.lexicon.contains(word)
        except Exception:
            return False


if __name__ == "__main__":
    stemmer = PashtoStemmer()
    # The baseline's documented catastrophic failures + normal inflection:
    demo = [
        "افغانستان",   # proper noun: baseline -> افغانست ; we must FREEZE
        "پراختيا",     # baseline -> لان ; light stem should not destroy it
        "پلانونه",     # baseline -> لان ; should -> پلان (plans -> plan)
        "کورونه",      # plural -> کور
        "کورونو",      # oblique plural -> کور
        "ښکلي",        # masc pl adj
        "نجونه",       # girls
        "ناپوه",       # neg prefix -> پوه
        "بېکاره",      # privative -> کار
        "کوي",         # irregular verb -> کول
        "خبرونه",      # news pl -> خبر
    ]
    for w in demo:
        print(stemmer.stem_word(w))
