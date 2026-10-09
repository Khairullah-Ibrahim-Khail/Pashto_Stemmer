# -*- coding: utf-8 -*-
"""
pashto_stemmer
==============
A dictionary-enhanced, rule-based stemmer for the Pashto language.

100% rule-based + lexicon — no machine learning. Designed for information
retrieval, indexing, and NLP preprocessing of Pashto text, and as a
reproducible research artifact.

Quick start
-----------
>>> from pashto_stemmer import PashtoStemmer
>>> st = PashtoStemmer()
>>> st.stem("کورونه")
'کور'
>>> st.stem("افغانستان")     # proper nouns are frozen
'افغانستان'
>>> [r.stem for r in st.stem_text("د کورونو خبرونه")]
['د', 'کور', 'خبر']
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
__author__ = "Khairullah"
__license__ = "MIT"
