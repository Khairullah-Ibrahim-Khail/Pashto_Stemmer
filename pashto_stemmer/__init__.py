# -*- coding: utf-8 -*-
"""
pashto_stemmer
==============
A grammar-driven, rule-based stemmer for the Pashto language.

100% rule-based + lexicon — no machine learning. Designed for information
retrieval, indexing, and NLP preprocessing of Pashto text, and as a
reproducible research artifact.

Quick start
-----------
>>> from pashto_stemmer import PashtoStemmer
>>> st = PashtoStemmer()
>>> st.stem("کورونه")
'کور'
>>> st.stem("افغانستان")     # ‑ستان is an affix like any other
'افغان'
>>> st.stem("پوهنتون")       # the stem need not be a word
'پوهن'
>>> [r.stem for r in st.stem_text("د کورونو خبرونه")]
['د', 'کور', 'خبر']

Proper nouns get no special treatment: the annotation policy strips a
documented affix wherever it appears, so ‑ستان comes off افغانستان. Loanwords
whose ending only resembles an affix are left alone, کورس stays کورس.
"""

from .stemmer import PashtoStemmer, StemmerConfig, StemResult
from .normalizer import Normalizer, NormalizerConfig
from .dictionary import PashtoLexicon
from .validation import ValidationConfig
from .baseline import AslamzaiBaseline

__all__ = [
    "PashtoStemmer",
    "StemmerConfig",
    "StemResult",
    "Normalizer",
    "NormalizerConfig",
    "PashtoLexicon",
    "ValidationConfig",
    "AslamzaiBaseline",
]

__version__ = "0.1.0"
__author__ = "Khairullah Ibrahim Khail"
__license__ = "MIT"
