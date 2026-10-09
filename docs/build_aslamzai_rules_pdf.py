# -*- coding: utf-8 -*-
"""
build_aslamzai_rules_pdf.py
===========================
The nine rules of Aslamzai & Saad (2015), transcribed from the published paper,
as a standalone document.

    python3 docs/build_aslamzai_rules_pdf.py  ->  docs/Aslamzai_Saad_2015_Rules.pdf
"""
from __future__ import annotations

import os
import subprocess
import sys

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Inches

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
from pashto_stemmer.baseline import AslamzaiBaseline     # noqa: E402

OUT = os.path.join(HERE, "Aslamzai_Saad_2015_Rules.docx")
PF, BODY = "Noto Naskh Arabic", "Calibri"
NAVY = RGBColor(0x12, 0x3A, 0x5E)
GREY = RGBColor(0x55, 0x55, 0x55)
BASE = AslamzaiBaseline()


def run(p, t, size=10.5, bold=False, pashto=False, color=None, italic=False):
    r = p.add_run(t)
    r.font.size = Pt(size); r.bold = bold; r.italic = italic
    r.font.color.rgb = color or RGBColor(0x1A, 0x1A, 0x1A)
    n = PF if pashto else BODY
    r.font.name = n
    rpr = r._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), n)
    if pashto:
        e = OxmlElement("w:rtl"); e.set(qn("w:val"), "1"); rpr.append(e)
    return r


def head(doc, t, size=13, before=14):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_with_next = True
    run(p, t, size, True, color=NAVY)


def note(doc, t, indent=0.3):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(indent)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.25
    run(p, t, 10, color=RGBColor(0x33, 0x33, 0x33))


def rule(doc, number, condition, action, affixes=(), examples=()):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
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
        run(p, "  ".join(affixes), 12, pashto=True)

    for word, paper_out, gloss in examples:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.space_after = Pt(2)
        run(p, "Their example:  ", 10, color=GREY)
        run(p, word, 12, pashto=True)
        run(p, "  →  ", 10, color=GREY)
        run(p, paper_out, 12, pashto=True, bold=True)
        if gloss:
            run(p, f"    {gloss}", 9.5, italic=True, color=GREY)


def build():
    doc = Document()
    for s in doc.sections:
        s.top_margin = s.bottom_margin = Inches(0.75)
        s.left_margin = s.right_margin = Inches(0.85)
    doc.styles["Normal"].font.name = BODY
    doc.styles["Normal"].font.size = Pt(10.5)

    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(2)
    run(p, "Aslamzai & Saad (2015) — The Nine Rules", 18, True, color=NAVY)
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(10)
    run(p, "S. Aslamzai and S. Saad, \"Pashto Language Stemming Algorithm\", "
           "Asia-Pacific Journal of Information Technology and Multimedia 4(1), 2015, "
           "pp. 25-37. Rules and examples transcribed from pages 28-30.",
        10, italic=True, color=GREY)

    head(doc, "Suffix rules", before=4)

    rule(doc, 1, "5 or more characters, ending in one of these suffixes",
         "remove the suffix",
         affixes=["ستان", "تون", "ونو", "تابه", "ناک", "وان", "وال", "جن", "ان", "ور", "و"],
         examples=[("پوهنتون", "پوهن", "university"),
                   ("موتروان", "موتر", "driver")])

    rule(doc, 2, "4 or more characters, ending in ي",
         "remove ي and add ه",
         affixes=["ي"],
         examples=[("پیغلي", "پیغله", "girls"),
                   ("شایستي", "شایسته", "beautifully")])

    rule(doc, 3, "more than 5 characters, ending in من",
         "remove من",
         affixes=["من"],
         examples=[("دردمن", "درد", "sick, patient"),
                   ("واکمن", "واک", "owner")])

    rule(doc, 4, "5 or more characters, ending in یز",
         "remove یز and add ه",
         affixes=["یز"],
         examples=[("ټولنیز", "ټولنه", "humanity"),
                   ("دودیز", "دود", "traditional")])

    rule(doc, 8, "the same word is repeated",
         "keep one copy as the root",
         examples=[("خوږی خوږی", "خوږی", "sweetly"),
                   ("ترخی ترخی", "ترخی", "smut")])

    head(doc, "Prefix rules")

    rule(doc, 5, "more than 3 characters, starting with one of these prefixes",
         "remove the prefix",
         affixes=["نا", "نه", "م", "بد", "نیک", "تش", "تل", "تور", "تک", "ډیر"],
         examples=[("ناپوه", "پوه", "uneducated"),
                   ("تل پاتی", "پاتی", "permanent")])

    rule(doc, 6, "5 or more characters, starting with ال",
         "remove ال",
         affixes=["ال"],
         examples=[("الزیات", "زیات", "much more"),
                   ("الښه", "ښه", "very good")])

    rule(doc, 7, "5 or more characters, starting with وران",
         "remove وران",
         affixes=["وران"],
         examples=[("وران خولی", "خولی", "joker"),
                   ("وران کاره", "کاره", "bad worker")])

    rule(doc, 9, "more than 3 characters, starting with نا، نه، نیک",
         "remove the prefix",
         affixes=["نا", "نه", "نیک"],
         examples=[("ناپوه", "پوه", "uneducated"),
                   ("نارروغ", "روغ", "sick")])

    head(doc, "Their evaluation")
    note(doc, "Two tests are reported. In the first, the researcher counted correct and "
              "incorrect outputs on two samples of 300 words, giving 88% and 89.33%. In the "
              "second, 600 stemmed words were shown to two native speakers who judged how "
              "many outputs were acceptable, giving 87% and 87.33%. The reported figure of "
              "87.66% is the average.", indent=0)

    head(doc, "Points where the paper is inconsistent")
    note(doc, "Rule 4 says to remove یز and add ه. Its first example does that "
              "(ټولنیز → ټولنه) but its second gives دودیز → دود with no ه.", indent=0)
    note(doc, "Rule 6 requires five or more characters, but its own example الښه has four.",
         indent=0)
    note(doc, "Rule 3 says more than five characters, but its example واکمن has exactly five.",
         indent=0)
    note(doc, "The Rule 5 prefix list contains a bare م, which would turn موتر into وتر and "
              "contradict the Rule 1 example موتروان → موتر.", indent=0)
    note(doc, "The order of prefix and suffix removal is not stated anywhere in the paper.",
         indent=0)
    note(doc, "Rules 5 and 9 overlap: نا، نه، نیک appear in both.", indent=0)

    doc.save(OUT)
    print(f"wrote {OUT}")
    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf",
                    "--outdir", HERE, OUT], check=True, capture_output=True, timeout=180)
    print(f"wrote {OUT.replace('.docx', '.pdf')}")


if __name__ == "__main__":
    build()
