# -*- coding: utf-8 -*-
"""
End-to-end stemmer regression tests, anchored on the Aslamzai baseline's
documented failures. Run: python tests/test_stemmer.py
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pashto_stemmer.stemmer import PashtoStemmer, StemmerConfig  # noqa: E402

_stemmer = PashtoStemmer()


def S(w):
    return _stemmer.stem(w)


# --- baseline CATASTROPHIC failures that we must fix ----------------------
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
    """Author's rule: no affix comes off a word of 3 characters or fewer."""
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
    # known gap that the author's final ه/ې/و rule is what fixes.
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
    # a sentence: every token, not just the last one. An earlier version
    # treated the whole string as one token and returned "د کورونو خبر".
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
