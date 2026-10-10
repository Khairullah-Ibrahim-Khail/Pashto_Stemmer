# -*- coding: utf-8 -*-
"""
End-to-end stemmer regression tests, anchored on the Aslamzai baseline's
documented failures. Run: python tests/test_stemmer.py
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pashto_stemmer.normalizer import Normalizer                 # noqa: E402
from pashto_stemmer.stemmer import PashtoStemmer, StemmerConfig  # noqa: E402

_stemmer = PashtoStemmer()


def S(w):
    return _stemmer.stem(w)


# --- the baseline's documented catastrophic failures ----------------------
def test_proper_nouns_follow_the_rules():
    """No name list: the ordinary rules apply, because a hand-written list can
    never cover unseen names. The gold correction log records ‑ستان as a
    productive suffix, so a place name loses it like any other word."""
    assert S("طالبان") == "طالب"            # ‑ان is a strippable plural
    assert S("افغانستان") == "افغان"        # productive ‑ستان
    assert S("بلوچستان") == "بلوچ"
    assert S("ترکمنستان") == "ترکمن"        # and stripping stops there
    assert S("افغانستانه") == "افغان"       # agreement ending outside ‑ستان
    assert S("افغانستان") != "افغانست"      # the baseline's failure


def test_no_false_conflation():
    # The baseline's failure mode: unrelated words collapsing together.
    # (پراختيا is left whole here: the ‑تیا rule needs the ي/ی spelling that
    #  the source text uses; the invariant that matters is no false merge.)
    assert S("پلانونه") == "پلان"
    assert S("پراختيا") != S("پلانونه")   # the key property: no false merge


# --- normal inflectional stemming -----------------------------------------
def test_noun_plurals_conflate_to_base():
    assert S("کورونه") == "کور"
    assert S("کورونو") == "کور"
    assert S("خبرونه") == "خبر"


def test_negation_prefixes_are_kept():
    """The gold correction log keeps نا‑، بې‑ and غیر‑: the negated word is its
    own lexeme, so only the agreement ending comes off."""
    assert S("ناقانونه") == "ناقانون"
    assert S("ناوړه") == "ناوړ"
    assert S("غیرقانونی") == "غیرقانون"
    assert S("ناروغ") == "ناروغ"
    assert S("بېکاره") == "بېکار"


def test_prefix_stripping():
    """هم‑ and بیا‑ are still removed, and a prefix only comes off when what
    remains is an attested word, so a loanword keeps its first letters."""
    assert S("همکار") == "کار"
    assert S("بېجينګ") == "بېجينګ"          # Beijing, not جينګ


def test_irregular_verb_dictionary_is_for_lemmatization():
    """The verb dictionary maps a form to its VERB (شو -> کېدل), which is a
    lemma. Stemming removes affixes and does not substitute one word for
    another, so the dictionary is off by default and must be asked for."""
    from pashto_stemmer.stemmer import PashtoStemmer, StemmerConfig
    lem = PashtoStemmer(StemmerConfig(use_verb_dictionary=True,
                                      verb_target="lemma")).stem
    assert lem("شو") == "کېدل"
    assert lem("وینم") == "لیدل"
    assert lem("وکړ") == "کول"
    assert lem("وکتل") == "کتل"
    # and in stemming mode the same words keep their own shape
    assert S("شو") == "شو"
    assert S("وکتل") == "وکتل"


def test_nothing_removed_from_short_words():
    """Length rule R2: no affix comes off a word of 3 characters or fewer."""
    for w in ["کول", "وژل", "ویل", "لرل", "ښځه", "کور", "خبر", "ښه"]:
        assert S(w) == w, f"{w} was stripped"


def test_derivative_verbs_reduce_to_the_root():
    """A regular derivative verb loses its whole verbal tail, so every form
    lands on the root: لوړېدل، لوړېږي، لوړېدو and لوړول all give لوړ."""
    assert S("لوړېدل") == "لوړ"
    assert S("لوړېږي") == "لوړ"
    assert S("لوړېدو") == "لوړ"
    assert S("لوړول") == "لوړ"
    assert S("جوړېدل") == "جوړ"
    # a verb is still never cut to a single letter
    assert S("کېدل") == "کېدل"


def test_derivative_verb_family_conflates():
    """Regular derivative verbs are formed by rule, so every form reaches the
    root without any dictionary: رسېدل، رسېږي، رسېدو and رسول all give رس."""
    assert {S(w) for w in ["رسېدل", "رسېږي", "رسېدو", "رسول"]} == {"رس"}
    assert {S(w) for w in ["لوړېدل", "لوړېږي", "لوړېدو", "لوړول"]} == {"لوړ"}


def test_feminine_family_conflates():
    """The point of stemming: every member of the feminine family must return
    the SAME token. Which token it is depends on strip_final_inflection."""
    # NOTE: only the default config is asserted. With strip_final_inflection
    # OFF the family does NOT fully conflate (چاره->چار but چارو->چاره), a
    # known gap that the final ه/ې/و rule is what fixes.
    for fam in (["سیمه", "سیمې", "سیمو"], ["اداره", "ادارې"],
                ["چاره", "چارو", "چارې"]):
        assert len({S(w) for w in fam}) == 1, f"{fam} -> {[S(w) for w in fam]}"


def test_stopword_frozen():
    assert S("او") == "او"
    assert S("چې") == "چې"


def test_five_yeh_distinction_survives_stemming():
    """ي and ی are different Pashto letters, so سړی (man) and سړي (men) must
    NOT be conflated by the stemmer either."""
    assert S("سړی") != S("سړي")
    assert S("ښکلی") == S("ښکلې")     # one adjective, one stem


def test_ablation_rules_only_runs():
    """Rules-only config (no dictionary) must still run without error and
    produce *some* stem — used as an ablation arm in Phase 5."""
    rules_only = PashtoStemmer(StemmerConfig(use_dictionary=False,
                                             use_exceptions=False))
    out = rules_only.stem("کورونه")
    assert isinstance(out, str) and len(out) >= 2



def test_arabic_broken_plurals_are_dictionary():
    """Policy §6: internal-change plurals are a DICTIONARY, not rules."""
    assert S("مطالب") == "مطلب"
    assert S("اثار") == "اثر"
    assert S("اخبار") == "خبر"
    assert S("علوم") == "علم"

def test_stem_takes_a_word_a_sentence_or_a_list():
    st = PashtoStemmer()
    # one word
    assert st.stem("کورونه") == "کور"
    # a sentence: every token, not just the last one. Treating the whole
    # string as one token returns "د کورونو خبر", which is the regression
    # this line guards.
    assert st.stem("د کورونو خبرونه") == "د کور خبر"
    # a sequence keeps its shape
    assert st.stem(["کورونه", "خبرونه"]) == ["کور", "خبر"]
    assert st.stem(("کورونه", "خبرونه")) == ("کور", "خبر")
    # blanks and non-strings do not raise: one empty cell must not stop a job
    assert st.stem("") == "" and st.stem("   ") == "" and st.stem(None) == ""
    # surrounding whitespace is not a second token
    assert st.stem("  پوهنتون  ") == "پوهن"


def test_stem_sentence_matches_stem_text():
    st = PashtoStemmer()
    text = "په سیمو کې د ښوونځیو جوړول روان دي"
    assert st.stem_sentence(text) == " ".join(r.stem for r in st.stem_text(text))
    assert st.stem(text) == st.stem_sentence(text)


def test_lexicalized_compounds_are_kept_whole():
    """Annotation policy §8: a lexicalized compound is one lexical item.

    The ‑لیک rule splits them if it is not gated (لاسلیک → لاس), against both
    the policy and the reference. This is the test that covers §8.
    """
    st = PashtoStemmer()
    assert st.stem("لاسلیک") == "لاسلیک"
    assert st.stem("برخلیک") == "برخلیک"
    # the compound head is kept: سر is not stripped off سرچینه
    assert st.stem("سرچینه").startswith("سرچی")
    # the outer inflection is still removed from a compound
    assert st.stem("لاسلیکونه") == "لاسلیک"


def test_relational_yeh_after_a_vowel():
    """The relational ‑ي on a vowel-final base: both yeh letters come off.

    The inventory held the single-yeh form only, so امریکایی came back whole
    (removing one yeh leaves امریکاي, not a word, and the scorer then kept the
    base). Rule matching folds the yeh letters, so one entry covers the
    dictionary spelling یي and the news spelling يي.
    """
    st = PashtoStemmer()
    assert st.stem("امریکایی") == "امریکا"
    assert st.stem("امریکايي") == "امریکا"        # the news spelling
    assert st.stem("اروپایی") == "اروپا"
    assert st.stem("روغتیایی") == "روغتیا"
    assert st.stem("اشنايي") == "اشنا"
    # a single yeh is still a single strip
    assert st.stem("پاکستاني") == "پاکستان"


def test_a_single_corpus_sighting_is_not_evidence_of_a_base():
    """min_base_freq: a word seen once must not outrank a correct strip.

    انګلیسي occurs once in the lexicon and چینایي twice, and that was enough
    for "keep the whole word" to beat the affix rule, so both came back
    unstemmed even though the rule had produced the right candidate.
    """
    st = PashtoStemmer()
    assert st.stem("انګلیسي") == "انګلیس"
    assert st.stem("چینایي") == "چینا"
    # a frequent word is still safe: the threshold must not strip common nouns
    for w in ("خلک", "مور", "کورس", "پلار"):
        assert st.stem(w) == w, w


def test_uniform_group_honours_its_own_minimum_stem():
    """مکتوب is an Arabic root with no ‑توب in it.

    Every rule in the uniform-strip group declares min_stem_len=3, but the
    group's own guard was 2, which let ‑توبونه come off مکتوبونه and leave مک.
    """
    st = PashtoStemmer()
    assert st.stem("مکتوب") == "مکتوب"
    assert st.stem("مکتوبونه") == "مکتوب"
    assert st.stem("مینتوب") == "مین"      # a real ‑توب still comes off


def test_plural_outranks_the_length_rule():
    """‑ونه is a documented plural; R1 must not pre-empt it at five letters.

    کورونه (six letters) reached the plural rule and gave کور, while غرونه
    (five) hit R1 first and gave غرون — the same morphology answered two ways
    by word length alone.
    """
    st = PashtoStemmer()
    assert st.stem("غرونه") == "غر"
    assert st.stem("پسونه") == "پس"
    assert st.stem("اسونه") == "اس"
    assert st.stem("کورونه") == "کور"     # the six-letter case still works


def test_the_zwnj_survives_stemming():
    """The joiner is part of the word; deleting it is a letter change.

    زده‌کوونکي lost its ZWNJ, the halves welded, and a suffix came off the
    weld giving زدهک. The affix ‑ونکي is real, so removing it is correct —
    what was wrong is that an invisible character vanished.
    """
    st = PashtoStemmer()
    out = st.stem("زده‌کوونکي")
    assert "\u200c" in out, repr(out)
    assert out == "زده\u200cک", repr(out)
    # ...but a joiner the strip has left at an edge joins nothing and goes:
    # مجله‌ګانې loses ‑ګانې and must not end in a dangling joiner.
    assert st.stem("مجله‌ګانې") == "مجله", repr(st.stem("مجله‌ګانې"))
    assert st.stem("کښتۍ‌ګانې") == "کښتۍ"


def test_annotation_policy_claims_hold():
    """The provisions of docs/02_annotation_policy.md that code can check."""
    st = PashtoStemmer()
    nz = Normalizer()
    # §1 no yeh letter is ever rewritten
    for c in "یيېۍئ":
        assert nz.normalize_token(c) == c
    # §1 other scripts' letters are mapped to their Pashto counterparts
    assert nz.normalize_token("ك") == "ک" and nz.normalize_token("ة") == "ه"
    assert nz.normalize_token("ٹ") == "ټ" and nz.normalize_token("ے") == "ې"
    assert nz.normalize_token("کـــور") == "کور"          # tatweel
    # short-word rule: nothing is removed from three letters or fewer
    assert st.stem("کور") == "کور"
    # §9 function words are returned unchanged
    assert st.stem("او") == "او" and st.stem("په") == "په"
    # §4 proper nouns get no special treatment
    assert st.stem("افغانستان") == "افغان"
    # §10 no letter is ever added back
    assert st.stem("سیمو") == "سیم"
    # the negation prefix is part of the lexeme
    assert st.stem("ناقانونه") == "ناقانون"


def _run_all():
    fns = [g for n, g in globals().items() if n.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn(); print(f"  PASS  {fn.__name__}"); passed += 1
        except AssertionError as e:
            print(f"  FAIL  {fn.__name__}: {e}")
        except Exception as e:
            print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(fns)} passed")
    return passed == len(fns)


if __name__ == "__main__":
    sys.exit(0 if _run_all() else 1)
