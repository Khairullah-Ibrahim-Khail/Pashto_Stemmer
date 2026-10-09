# -*- coding: utf-8 -*-
"""
quickstart.py — a 60-second tour of the Pashto stemmer.
Run:  python examples/quickstart.py
"""

from pashto_stemmer import PashtoStemmer, StemmerConfig, AslamzaiBaseline

st = PashtoStemmer()
base = AslamzaiBaseline()

print("1) Single words")
for w in ["کورونه", "خبرونه", "ناپوه", "غواړي", "افغانستان"]:
    print(f"   {w:12} -> {st.stem(w)}")

print("\n2) A sentence (stopwords stay, content words are stemmed)")
sentence = "د افغانستان په کورونو کې خبرونه خپاره شول"
for r in st.stem_text(sentence):
    print(f"   {r.input:12} -> {r.stem}")

print("\n3) Where we beat the Aslamzai (2015) baseline")
for w in ["پراختيا", "پلانونه", "افغانستان"]:
    print(f"   {w:10}  baseline={base.stem(w):8}  ours={st.stem(w)}")

print("\n4) Confidence + decision trace")
for w in ["بېکاره", "لاړ", "پلانونه"]:
    r = st.stem_word(w)
    print(f"   {w:8} -> {r.stem:8} (conf={r.confidence:.2f}; {r.trace})")

print("\n5) Ablation: rules-only (no dictionary) over-stems into non-words")
rules_only = PashtoStemmer(StemmerConfig(use_dictionary=False, use_exceptions=False))
for w in ["پراختيا", "خبرونه"]:
    print(f"   {w:10}  rules-only={rules_only.stem(w):8}  full={st.stem(w)}")
