# -*- coding: utf-8 -*-
"""
ablation.py
===========
Leave-one-out ablation, over a wider set of switches than the paper uses.

Start from the full system, disable ONE component at a time, and measure the
change. A component that earns its place shows a drop when removed; one that
shows no drop (or an improvement) is not paying for itself.

Metrics: exact-match accuracy and Paice's under-stemming index (UI, lower is
better). UI matters most here — grouping word forms together is the actual
job of a stemmer, and it is less sensitive than exact-match to which label
the annotator happened to choose.
"""
from __future__ import annotations
import csv, os, sys
from collections import defaultdict
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pashto_stemmer.stemmer import PashtoStemmer, StemmerConfig
from pashto_stemmer.validation import ValidationConfig
from pashto_stemmer.dictionary import PashtoLexicon
from pashto_stemmer.normalizer import Normalizer
from pashto_stemmer.metrics import accuracy, paice

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GOLD = os.path.join(ROOT, "dataset", "pashto_gold_corrected_v2.csv")


BANNER = """
NOTE: these figures are NOT the component study in the paper.

This script scores all 2,912 development rows, including the lemma rows whose
reference is a different word rather than a truncation, and it toggles a wider
and partly different set of switches. Its full-system figure is therefore lower
than the paper's by construction.

The paper's tables come from:   python experiments/reproduce_paper.py
"""


def main():
    print(BANNER)
    rows = list(csv.DictReader(open(GOLD, encoding="utf-8-sig")))
    pairs = [(r["word"], r["stem"]) for r in rows
             if r.get("word") and r.get("stem")]
    groups = defaultdict(list)
    for w, s in pairs:
        groups[s].append(w)
    groups = dict(groups)

    nz = Normalizer()
    lex = PashtoLexicon.from_frequency_file(normalizer=nz)

    def run(label, **kw):
        vkw = kw.pop("validation", None)
        cfg = StemmerConfig(validation=ValidationConfig(**vkw) if vkw else ValidationConfig(), **kw)
        st = PashtoStemmer(cfg, lexicon=lex if cfg.use_dictionary else None)
        return label, accuracy(pairs, st.stem), paice(groups, st.stem).ui

    arms = [
        run("FULL SYSTEM"),
        run("− dictionary",            use_dictionary=False),
        run("− exceptions",            use_exceptions=False),
        run("− POS filtering",         use_pos=False),
        run("− compound splitter",     use_compound=False),
        run("− derivational stripping", strip_derivational=False),
        run("− prefix rules",          use_prefixes=False),
        run("− suffix rules",          use_suffixes=False),
        run("− final ه/ې/و rule",      strip_final_inflection=False),
        run("− family test",           validation={"family_bonus": 0.0}),
        run("verb target = infinitive", verb_target="infinitive"),
    ]

    base_acc, base_ui = arms[0][1], arms[0][2]
    print(f"gold words: {len(pairs)}\n")
    print(f"{'configuration':30} {'acc':>7} {'Δacc':>7} {'UI':>7} {'ΔUI':>7}  verdict")
    print("-" * 78)
    for label, acc, ui in arms:
        if label == "FULL SYSTEM":
            print(f"{label:30} {acc:6.1%} {'—':>7} {ui:7.3f} {'—':>7}")
            continue
        dacc, dui = acc - base_acc, ui - base_ui
        # removing it HURTS (acc down or UI up) => the component earns its place
        verdict = "earns its place" if (dacc < -0.002 or dui > 0.005) else \
                  ("no measurable gain" if abs(dacc) < 0.002 and abs(dui) < 0.005
                   else "REMOVING IT HELPS")
        print(f"{label:30} {acc:6.1%} {dacc:+6.1%} {ui:7.3f} {dui:+7.3f}  {verdict}")


if __name__ == "__main__":
    main()
