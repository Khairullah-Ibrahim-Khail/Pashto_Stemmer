# tokenizer.py
"""Tokenization for the retrieval experiment.

Normalization is delegated to the project's own Normalizer, not reimplemented
here. An earlier version of this file did its own NFKC, stripped harakat and
tatweel, and deleted the ZWNJ -- which disagreed with the stemmer on the
joiner, so the IR tokens were not the strings the stemmer was measured on.
Both the stemmed and the unstemmed arm now share this one normalization, which
is what makes the comparison a comparison.
"""
import re
import sys

from config import STEMMER_PATH

if STEMMER_PATH not in sys.path:
    sys.path.insert(0, STEMMER_PATH)

from pashto_stemmer.normalizer import Normalizer      # noqa: E402

_NZ = Normalizer()

# A token is a run of Arabic-script LETTERS, digits, or the ZWNJ. Matching
# positively rather than splitting on the complement matters: U+0600-U+06FF
# holds Arabic punctuation as well as letters, so the complement form kept the
# comma and gave "khabaruna," as a token, which no rule and no lexicon matches.
_TOKEN_RE = re.compile(
    "["
    "\u0620-\u063f\u0641-\u064a"            # Arabic letters (U+0640 = tatweel)
    "\u066e-\u066f\u0671-\u06d3\u06d5"       # more letters (U+06D4 = full stop)
    "\u06e5-\u06e6\u06ee-\u06ef\u06fa-\u06ff"
    "\u0660-\u0669\u06f0-\u06f9"            # Arabic-Indic / extended digits
    "\u200c"                                  # ZWNJ: a joined word is one token
    "\u0750-\u077f"                          # Arabic Supplement
    "\ufb50-\ufdff\ufe70-\ufeff"            # presentation forms, if any survive
    "]+")


def normalize(text):
    """The project's normalization: all five yeh letters preserved."""
    return _NZ.normalize(text)


def tokenize(text):
    """Normalized tokens; punctuation and Latin text are dropped."""
    return _TOKEN_RE.findall(normalize(text))