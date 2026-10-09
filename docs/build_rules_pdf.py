# -*- coding: utf-8 -*-
"""
build_rules_pdf.py
==================
States the stemmer as a numbered rule set, in the same form Aslamzai & Saad
(2015) use: each rule is a condition and an action, with the affixes it covers
listed inside the rule rather than in a separate inventory.

The affix lists are read from the live code, so the document cannot drift from
the implementation.

    python3 docs/build_rules_pdf.py   ->  docs/Pashto_Stemmer_Rules.pdf
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from collections import defaultdict

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Inches

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

from pashto_stemmer.stemmer import PashtoStemmer        # noqa: E402
from pashto_stemmer.suffixes import SUFFIX_RULES        # noqa: E402
from pashto_stemmer.prefixes import PREFIX_RULES        # noqa: E402
from pashto_stemmer.verb_paradigms import IRREGULAR     # noqa: E402
from pashto_stemmer.baseline import AslamzaiBaseline    # noqa: E402

OUT = os.path.join(HERE, "Pashto_Stemmer_Rules.docx")
PF, BODY = "Noto Naskh Arabic", "Calibri"
NAVY = RGBColor(0x12, 0x3A, 0x5E)
GREY = RGBColor(0x55, 0x55, 0x55)
ST = PashtoStemmer()
BASE = AslamzaiBaseline()

# A pool of real words from the project's own annotated data, used to give each
# affix a worked example that comes from Pashto text rather than from invention.
def _word_pool():
    import csv
    from pashto_stemmer.normalizer import Normalizer
    nz = Normalizer()
    pool = set()
    for name in ("pashto_gold_corrected_v2.csv", "test_500_news.csv"):
        path = os.path.join(HERE, "..", "dataset", name)
        if not os.path.exists(path):
            continue
        for row in csv.DictReader(open(path, encoding="utf-8-sig")):
            w = nz.normalize_token((row.get("word") or "").strip())
            if len(w) >= 3:
                pool.add(w)
    return sorted(pool, key=len)

POOL = _word_pool()


def example_for_affix(affix, side, min_stem):
    """Find a real word the affix applies to, and stem it live."""
    for w in POOL:
        if len(w) - len(affix) < min_stem:
            continue
        if side == "suffix" and w.endswith(affix) and w != affix:
            out = ST.stem(w)
            if out != w:
                return w, out
        if side == "prefix" and w.startswith(affix) and w != affix:
            out = ST.stem(w)
            if out != w:
                return w, out
    return None, None


def run(p, t, size=10.5, bold=False, pashto=False, color=None, italic=False):
    r = p.add_run(t)
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    r.font.color.rgb = color or RGBColor(0x1A, 0x1A, 0x1A)
    n = PF if pashto else BODY
    r.font.name = n
    rpr = r._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), n)
    if pashto:
        e = OxmlElement("w:rtl")
        e.set(qn("w:val"), "1")
        rpr.append(e)
    return r


def head(doc, t, size=13, before=14):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_with_next = True
    run(p, t, size, True, color=NAVY)


def shade(c, f):
    tp = c._tc.get_or_add_tcPr()
    e = OxmlElement("w:shd")
    e.set(qn("w:val"), "clear")
    e.set(qn("w:fill"), f)
    tp.append(e)


def affix_table(doc, rules, side):
    """One row per affix: the affix, its minimum stem, a real word, and the
    stem the running code produces for it."""
    rows = []
    for r in sorted(rules, key=lambda x: (-len(x.affix), x.affix)):
        w, out = example_for_affix(r.affix, side, r.min_stem_len)
        rows.append([r.affix, r.min_stem_len,
                     w or "—", out or "—", gloss_note(r.note)])
    tbl(doc, ["Affix", "Min stem", "Example word", "Stem produced", "What it marks"],
        rows, [0.7, 0.62, 1.15, 1.15, 3.0], pcols=(0, 2, 3), size=9)


def gloss_note(note, k=46):
    t = re.sub(r"\[[^\]]+\]", "", note or "").strip(" :;-")
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[\u0620-\u06D5]+\s*→\s*[\u0620-\u06D5]+", "", t).strip(" :;-,")
    return t[:k] + ("…" if len(t) > k else "")


def explain(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.25
    run(p, text, 10, color=RGBColor(0x33, 0x33, 0x33))


def rule(doc, number, condition, action, affixes=None, examples=(), note=""):
    """One numbered rule: condition, action, the affixes it covers, examples."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(11)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run(p, f"Rule {number}:  ", 11, True, color=NAVY)
    run(p, condition, 11, True)

    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.space_after = Pt(3)
    run(p, "→  " + action, 10.5)

    if affixes:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.space_after = Pt(3)
        run(p, f"Affixes ({len(affixes)}):  ", 10, bold=True, color=GREY)
        run(p, "  ".join(affixes), 11.5, pashto=True)

    for src, want in examples:
        got = ST.stem(src)
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.space_after = Pt(2)
        run(p, "Example:  ", 10, color=GREY)
        run(p, src, 11.5, pashto=True)
        run(p, "  →  ", 10, color=GREY)
        run(p, got, 11.5, pashto=True, bold=True)
        if want and got != want:
            run(p, f"   (expected {want})", 9, italic=True, color=GREY)

    if note:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.space_after = Pt(4)
        run(p, note, 9.5, italic=True, color=GREY)


def tbl(doc, hdr, rows, widths, pcols=(), size=9.5):
    t = doc.add_table(rows=1, cols=len(hdr))
    t.style = "Table Grid"
    for i, h in enumerate(hdr):
        c = t.rows[0].cells[i]
        c.text = ""
        pp = c.paragraphs[0]
        pp.paragraph_format.space_after = Pt(1)
        run(pp, h, size, True, color=RGBColor(0xFF, 0xFF, 0xFF))
        shade(c, "123A5E")
    for ri, rw in enumerate(rows):
        cs = t.add_row().cells
        for i, v in enumerate(rw):
            cs[i].text = ""
            pp = cs[i].paragraphs[0]
            pp.paragraph_format.space_after = Pt(1)
            run(pp, str(v), size, pashto=(i in pcols))
        if ri % 2:
            for c in cs:
                shade(c, "F2F5F9")
    for r_ in t.rows:
        for i, w in enumerate(widths):
            r_.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def by_class():
    g = defaultdict(list)
    for r in SUFFIX_RULES:
        g[(r.category, r.min_stem_len)].append(r.affix)
    for k in g:
        g[k].sort(key=lambda a: (-len(a), a))
    return g


def build():
    doc = Document()
    for s in doc.sections:
        s.top_margin = s.bottom_margin = Inches(0.75)
        s.left_margin = s.right_margin = Inches(0.8)
    doc.styles["Normal"].font.name = BODY
    doc.styles["Normal"].font.size = Pt(10.5)

    g = by_class()
    infl2, infl3 = g[("inflectional", 2)], g[("inflectional", 3)]
    der3, der4 = g[("derivational", 3)], g[("derivational", 4)]
    pre = [r.affix for r in sorted(PREFIX_RULES, key=lambda x: (-len(x.affix), x.affix))]

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    run(p, "Pashto Stemmer — The Rule Set", 18, True, color=NAVY)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    run(p, "Twelve rules, applied in this order. A word leaves the process at the first "
            "rule that matches it, except for Rules 6 to 9, which generate competing "
            "analyses that Rule 10 then chooses between.", 10.5, italic=True, color=GREY)

    head(doc, "Part 1 — Rules that decide on their own", before=4)
    explain(doc, "If one of these matches, the word is finished. Nothing further is tried.")

    rule(doc, 1, "The word is in the stopword list",
         "return it unchanged")
    explain(doc, "Pashto function words such as د، په، او، چې carry no affix. They are also "
                 "very short, so an affix rule would otherwise destroy them. Every stemmer "
                 "for every language does this.")

    rule(doc, 2, "The word is a form of an irregular verb",
         "return that verb's lemma from the dictionary",
         examples=[("شو", "کېدل"), ("کوي", "کول"), ("ځي", "تلل"), ("وینم", "لید"),
                   ("غواړي", "غوښتل")])
    explain(doc, "Pashto verbs divide into weak verbs, whose stems follow from the "
                 "infinitive, and strong verbs, whose present stem must simply be known. "
                 "No rule derives وین from لیدل or ځ from تلل. These are listed; everything "
                 "predictable is left to Rules 6 to 8. The list holds "
                 f"{len(IRREGULAR)} verbs and is printed in full at the end.")
    explain(doc, "This runs before the length rules on purpose. If the length rules ran "
                 "first, شو would be caught by Rule 3 as a short word and never reach the "
                 "dictionary.")

    rule(doc, 3, "The word is three letters or fewer",
         "return it unchanged",
         examples=[("وخت", "وخت"), ("کور", "کور"), ("لاس", "لاس")])
    explain(doc, "A Pashto root is rarely shorter than three letters. Removing anything from "
                 "a word this short leaves a fragment, not a stem. This also protects the "
                 "many three-letter content words: کور house, لاس hand, وخت time.")

    rule(doc, 4, "The word is four or five letters and ends in ی ي ې ۍ ئ ل or ه",
         "remove that final letter",
         affixes=["ی", "ي", "ې", "ۍ", "ئ", "ل", "ه"],
         examples=[("موده", "مود"), ("اداره", "ادار"), ("ګوښه", "ګوښ"),
                   ("لومړي", "لومړ"), ("رسېدل", "رس")])
    explain(doc, "These seven letters are the commonest single-letter endings in Pashto: the "
                 "five ye letters mark gender, number and person, ه marks the feminine and "
                 "adjectival agreement, and ل is the infinitive ending. On a short word a "
                 "final letter from this set is nearly always an ending rather than part of "
                 "the root.")
    explain(doc, "The upper bound of five letters is the part to question. Beyond it the rule "
                 "starts cutting roots: held-out accuracy falls from 59.2% at five letters to "
                 "58.2% at six and 54.0% with no bound. Longer words are left to Rules 6 to 8, "
                 "which know which particular suffix they are removing.")

    rule(doc, 5, "The word ends in ‑ستان and at least three letters remain",
         "remove ‑ستان and stop; no further rule is applied",
         affixes=["ستان"],
         examples=[("افغانستان", "افغان"), ("بلوچستان", "بلوچ"), ("ترکمنستان", "ترکمن"),
                   ("هندوستان", "هندو")])
    explain(doc, "‑ستان forms place names from a noun: افغان + ستان, بلوچ + ستان. It is an "
                 "ordinary derivational suffix and is treated as one; a place name gets no "
                 "special protection.")
    explain(doc, "The rule stops rather than continuing because the general rules would keep "
                 "going: ترکمنستان first loses ستان to give ترکمن, and then Rule 7 would take "
                 "the ‑من and leave ترک. Stopping is the whole point of stating it separately.")

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    head(doc, "Part 2 — Rules that propose an analysis", before=0)
    explain(doc, "These do not decide anything on their own. Each proposes a candidate stem; "
                 "they may apply on top of one another up to three times; and Rule 10 chooses "
                 "between the results. A single-pass stemmer must commit to its first guess, "
                 "which is the main structural difference from the baseline.")
    explain(doc, "In the tables below, 'example word' is a real word from the project's "
                 "annotated data and 'stem produced' is what the running code returns for it. "
                 "Nothing in these columns was typed by hand.")

    infl2_rules = [r for r in SUFFIX_RULES
                   if r.category == "inflectional" and r.min_stem_len == 2]
    infl3_rules = [r for r in SUFFIX_RULES
                   if r.category == "inflectional" and r.min_stem_len == 3]
    der_rules = [r for r in SUFFIX_RULES if r.category == "derivational"]

    rule(doc, 6, "The word ends in an inflectional suffix and at least two letters remain",
         "propose the word without that suffix")
    explain(doc, "Inflection changes the form of a word without changing the word itself: "
                 "کور and کورونه are the same noun, singular and plural. These are the longer "
                 "inflectional endings, so two remaining letters is enough — there is little "
                 "chance of confusing ‑ونو with root material.")
    explain(doc, "The ‑ېږ and ‑ېد group belongs here too. These form verbs from nouns and "
                 "adjectives by a regular pattern (جوړ → جوړېدل, جوړېږي), which is why those "
                 "verbs are not in the dictionary.")
    affix_table(doc, infl2_rules, "suffix")

    rule(doc, 7, "The word ends in a short inflectional suffix and at least three letters "
                 "remain",
         "propose the word without that suffix")
    explain(doc, "The same kind of ending, but only one or two letters long. A longer minimum "
                 "stem is required because a short ending is much harder to tell from the end "
                 "of a root: the ه of لنډه is a suffix, the ه of سیمه is part of the word.")
    affix_table(doc, infl3_rules, "suffix")

    rule(doc, 8, "The word ends in a derivational suffix and at least three letters remain",
         "propose the word without that suffix")
    explain(doc, "Derivation makes a new word rather than a new form: کار work gives کارګر "
                 "worker, چټک fast gives چټکوالی speed. Strictly these are different lexemes, "
                 "so removing them is a decision rather than a fact, and it is taken here "
                 "because the purpose is to group related words together.")
    affix_table(doc, der_rules, "suffix")

    rule(doc, 9, "The word begins with a prefix, at least three letters remain, and what "
                 "remains is an attested word",
         "propose the word without that prefix")
    explain(doc, "Pashto has few productive prefixes. نا‑ and بې‑ negate, هم‑ means 'co-', "
                 "لا‑ intensifies. The attestation condition is what makes the rule safe: "
                 "بېجينګ (Beijing) begins with بې but جينګ is not a Pashto word, so nothing "
                 "is removed.")
    explain(doc, "The verbal particles و‑، را‑، ور‑، در‑، پرې‑، وا‑ were implemented and then "
                 "removed. Measured on the annotated data they stripped correctly between 13% "
                 "and 50% of the time, because a word-initial و or را cannot be told apart "
                 "from the first letter of a root.")
    affix_table(doc, list(PREFIX_RULES), "prefix")

    head(doc, "Part 3 — Choosing between the proposals")
    rule(doc, 10, "Several rules proposed different stems",
         "score each proposal and return the highest",
         note="The score adds: how much affix material was removed; a bonus if other words "
              "in the corpus are built on the same stem; a bonus if the stem itself occurs. "
              "Being attested raises a proposal's score but never blocks one, because a "
              "stem does not have to be a dictionary word. The unstripped word receives only "
              "a small attestation bonus, since the input is almost always in the corpus and "
              "that says nothing about whether it is a stem.")

    explain(doc, "This is where the system differs most from a single-pass stemmer. For "
                 "کورونو the proposals are کورونو unchanged, کور by Rule 6, and کورون by "
                 "Rule 7. All three are legal; the score decides. A first-match stemmer has "
                 "to take whichever rule it happens to try first.")

    rule(doc, 11, "A proposal would leave fewer letters than the rule's minimum",
         "discard that proposal",
         note="Without this کېدل reduces to ک.")

    explain(doc, "Each rule carries its own minimum rather than one global threshold, "
                 "because a three-letter suffix can safely leave less behind than a "
                 "one-letter suffix can.")

    rule(doc, 12, "A rule marked first-pass-only would apply to a word that has already lost "
                  "material",
         "do not apply it",
         note="The verbal ‑ل must not come off an adjective root that happens to end in ل: "
              "ښکلې → ښکل is right, ښکلې → ښکل → ښک is not.")

    explain(doc, "Some endings are only endings on an intact word. Once material has "
                 "already come off, what now sits at the end of the word may be root.")

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    head(doc, "A rule that was tested and removed", before=0)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    run(p, "One further rule was proposed, implemented and then deleted: remove the last "
            "three letters of any non-Pashto word of seven letters or more. It is recorded "
            "here because a rule that was tested and rejected is part of the method.",
        10.5)
    tbl(doc, ["Judged against", "Cut three letters", "Remove a documented affix"],
        [["Development set, 2,912 words", "25.0%", "45.0%"],
         ["Held-out set, first annotation", "59.7%", "35.5%"],
         ["Held-out set, re-annotated", "43.5%", "51.6%"]],
        [2.6, 1.5, 1.9])
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    run(p, "Removing a real affix wins on both careful annotations. Every word the rule "
            "damaged carried a genuine affix: درلودلو → درلو where the affix is ‑لو, "
            "مسووليت → مسوو where it is ‑یت, اعلانات → اعلا where it is ‑ات. The rule fired "
            "before the affix list was consulted and cut through the root.", 10.5)

    head(doc, "The irregular-verb dictionary used by Rule 2")
    ver = [p for p in IRREGULAR if "[" in p.note]
    unv = [p for p in IRREGULAR if "[" not in p.note]

    def gl(n, k=28):
        t = re.sub(r"\[[^\]]+\]", "", n or "").strip(" :;-")
        t = re.sub(r"\s+", " ", t)
        return t[:k] + ("…" if len(t) > k else "")

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    run(p, f"{len(ver)} verbs checked against a printed grammar:", 10.5, bold=True)
    tbl(doc, ["Infinitive", "Present stem", "Past stem", "Meaning"],
        [[v.lemma, " / ".join(v.present), " / ".join(v.past), gl(v.note)] for v in ver],
        [1.3, 1.3, 1.5, 2.6], pcols=(0, 1, 2))
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    run(p, f"{len(unv)} verbs not yet checked against a printed grammar:", 10.5, bold=True)
    tbl(doc, ["Infinitive", "Present stem", "Past stem", "Meaning"],
        [[v.lemma, " / ".join(v.present), " / ".join(v.past), gl(v.note)] for v in unv],
        [1.3, 1.3, 1.5, 2.6], pcols=(0, 1, 2))

    doc.save(OUT)
    print(f"wrote {OUT}")
    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf",
                    "--outdir", HERE, OUT],
                   check=True, capture_output=True, timeout=180)
    print(f"wrote {OUT.replace('.docx', '.pdf')}")


if __name__ == "__main__":
    build()
