# -*- coding: utf-8 -*-
"""
make_inventory_tables.py
========================
Writes the inventory tables for the paper straight out of the rule objects, so
the paper cannot drift from the code.

    python3 paper/make_inventory_tables.py

Outputs, all in paper/:
    inventory_rows.tsv        one line per rule, read by build_paper_docx.py
    inventory_summary.tsv     the per-group counts, read by the same
    appendix_inventory.tex    the appendix longtable body for main.tex
    inventory_summary.tex     the summary table body for main.tex
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from pashto_stemmer.prefixes import PREFIX_RULES          # noqa: E402
from pashto_stemmer.suffixes import SUFFIX_RULES          # noqa: E402

# Tags that point at a published grammar or lexical resource, as against
# "[inv §x]", which points at this project's own inventory document.
PUBLISHED = re.compile(r"\[(T&R|R&T|N&K|Khan23|W|AP|Penzl)\b")
TAG = re.compile(r"\[([^\]]+)\]")

PROD_SHORT = {"productive": "prod.", "restricted": "restr.",
              "lexicalized": "lex.", "borrowed": "borr."}
CONF_SHORT = {"high": "high", "medium": "med.", "low": "low"}

GROUPS = [
    ("Nominal inflection",      "number and case on nouns and adjectives"),
    ("Verbal inflection",       "infinitive, agreement and tense"),
    ("Derivation: nouns",       "abstract, agentive, place and diminutive"),
    ("Derivation: adjectives",  "relational, possessive and privative"),
    ("Derivation: verbs",       "denominal verb formation"),
    ("Prefixes",                "negation, repetition and degree"),
]


def group_of(rule) -> str:
    pos = set(rule.pos)
    if rule.side == "prefix":
        return "Prefixes"
    if rule.category == "inflectional":
        return "Verbal inflection" if "V" in pos else "Nominal inflection"
    if "V" in pos:
        return "Derivation: verbs"
    if "ADJ" in pos and "N" not in pos:
        return "Derivation: adjectives"
    return "Derivation: nouns"


def short_type(rule) -> str:
    side = "pre" if rule.side == "prefix" else "suf"
    cat = "infl" if rule.category == "inflectional" else "der"
    return f"{side}, {cat}"


# Rules the author proposed, mostly oblique and feminine variants of forms that
# are themselves cited. Labelled rather than left looking merely uncited.
AUTHOR_PROPOSED = {
    "\u0647\u0645", "\u0648\u0627\u0644\u0648", "\u0648\u0646\u06a9\u0648",
    "\u0648\u0646\u06a9\u06d0", "\u0646\u06a9\u06cc", "\u0646\u06a9\u06d0",
    "\u0646\u06a9\u0648", "\u0644\u06cc\u06a9", "\u06cc\u0632\u0648",
}


def source_of(rule) -> str:
    """What backs this rule: a publication, our inventory, or nothing yet."""
    m = TAG.search(rule.note)
    if m:
        return m.group(1)
    if rule.strip_allowed != "yes":
        return "gated"           # never applied; no grammar is being appealed to
    if rule.affix in AUTHOR_PROPOSED:
        return "author"
    return "untraced"            # no published source recorded yet


def rows():
    out = []
    for r in list(SUFFIX_RULES) + list(PREFIX_RULES):
        out.append({
            "affix": r.affix,
            "group": group_of(r),
            "type": short_type(r),
            "min": str(r.min_stem_len),
            "pos": "/".join(r.pos) or "\u2014",
            "productivity": r.productivity,
            "confidence": r.confidence,
            "strip": r.strip_allowed,
            "source": source_of(r),
            "published": "yes" if PUBLISHED.search(r.note) else "no",
        })
    order = {g: i for i, (g, _) in enumerate(GROUPS)}
    out.sort(key=lambda d: (order[d["group"]], -len(d["affix"]), d["affix"]))
    return out


def summary(rs):
    table = []
    for name, gloss in GROUPS:
        g = [d for d in rs if d["group"] == name]
        if not g:
            continue
        table.append({
            "group": name,
            "gloss": gloss,
            "rules": len(g),
            "published": sum(1 for d in g if d["published"] == "yes"),
            "gated": sum(1 for d in g if d["strip"] == "no"),
            "examples": " ".join(d["affix"] for d in g if d["strip"] == "yes")
        })
    return table


# -- example affixes are chosen by hand: the frequent, recognisable member of
#    each group, not whichever one happens to sort first.
EXAMPLES = {
    "Nominal inflection":     ("\u0648\u0646\u0647", "\u0627\u0646\u0648", "\u06d0"),
    "Verbal inflection":      ("\u06d0\u062f\u0644", "\u0648\u0644"),
    "Derivation: nouns":      ("\u062a\u0648\u0628", "\u062a\u06cc\u0627",
                               "\u062a\u0648\u0646"),
    "Derivation: adjectives": ("\u06cc\u0632", "\u0645\u0646\u062f",
                               "\u0646\u0627\u06a9"),
    # the single rule in this group is gated, so there is no example to show
    "Derivation: verbs":      (),
    "Prefixes":               ("\u0647\u0645", "\u0628\u06cc\u0627",
                               "\u0646\u06cc\u0645"),
}


def main() -> int:
    rs = rows()
    with open(os.path.join(HERE, "inventory_rows.tsv"), "w", encoding="utf-8") as fh:
        cols = ["affix", "group", "type", "min", "pos", "productivity",
                "confidence", "strip", "source"]
        fh.write("\t".join(cols) + "\n")
        for d in rs:
            fh.write("\t".join(d[c] for c in cols) + "\n")

    sm = summary(rs)
    with open(os.path.join(HERE, "inventory_summary.tsv"), "w", encoding="utf-8") as fh:
        fh.write("group\tgloss\trules\tpublished\tgated\texamples\n")
        for d in sm:
            ex = " ".join(EXAMPLES[d["group"]]) or "\u2014"
            fh.write(f"{d['group']}\t{d['gloss']}\t{d['rules']}\t{d['published']}"
                     f"\t{d['gated']}\t{ex}\n")

    # Both .tex files carry their own tabular environment. An \\input placed
    # *inside* a tabular is not reliable -- the file's final newline reaches
    # the stream as a space, which opens a row and makes the \\bottomrule that
    # follows it a misplaced \\noalign -- so main.tex inputs these at float
    # level instead.
    with open(os.path.join(HERE, "inventory_summary.tex"), "w", encoding="utf-8") as fh:
        fh.write("% generated by paper/make_inventory_tables.py -- do not edit\n")
        fh.write("\\begin{tabular}{lcccl}\n\\toprule\n")
        fh.write("Group & Rules & Published & Kept & Examples\\\\\n\\midrule\n")
        for d in sm:
            ex = " ".join(EXAMPLES[d["group"]]) or "---"
            cell = "---" if ex == "---" else f"\\ps{{{ex}}}"
            fh.write(f"{d['group']} & {d['rules']} & {d['published']} & "
                     f"{d['gated']} & {cell}\\\\\n")
        fh.write("\\midrule\n")
        fh.write(f"Total & {sum(d['rules'] for d in sm)} & "
                 f"{sum(d['published'] for d in sm)} & "
                 f"{sum(d['gated'] for d in sm)} & \\\\\n")
        fh.write("\\bottomrule\n\\end{tabular}\n")

    with open(os.path.join(HERE, "appendix_inventory.tex"), "w", encoding="utf-8") as fh:
        fh.write("% generated by paper/make_inventory_tables.py -- do not edit\n")
        fh.write("\\begin{longtable}{llclllcl}\n\\toprule\n")
        head = ("Affix & Type & min & POS & Productivity & Confidence & "
                "Strip & Source\\\\\n")
        fh.write(head + "\\endfirsthead\n\\toprule\n" + head + "\\endhead\n")
        current = None
        for d in rs:
            if d["group"] != current:
                current = d["group"]
                fh.write("\\midrule\n\\multicolumn{8}{l}{\\emph{%s}}\\\\\n"
                         "\\midrule\n" % current)
            fh.write(" & ".join([
                f"\\ps{{{d['affix']}}}", d["type"], d["min"], d["pos"],
                PROD_SHORT[d["productivity"]], CONF_SHORT[d["confidence"]],
                d["strip"], d["source"].replace("&", "\\&"),
            ]) + "\\\\\n")
        fh.write("\\bottomrule\n\\end{longtable}\n")

    print(f"{len(rs)} rules, {sum(1 for d in rs if d['published']=='yes')} with a "
          f"published source, {sum(1 for d in rs if d['strip']!='yes')} never stripped")
    for d in sm:
        print(f"  {d['group']:24s} {d['rules']:3d} rules  "
              f"{d['published']:3d} published  {d['gated']:3d} gated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
