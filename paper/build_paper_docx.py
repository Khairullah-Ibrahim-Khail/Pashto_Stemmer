# -*- coding: utf-8 -*-
"""
build_paper_docx.py
===================
Builds the paper as a Word document and converts it to PDF.

The LaTeX source in paper/main.tex is the reference version; this produces the
same text in .docx for venues that ask for Word, and for editing. Pashto is
rendered through the w:rFonts / w:rtl run properties with a complex-script
font, so it displays correctly without XeLaTeX.

    python3 paper/build_paper_docx.py
"""
from __future__ import annotations

import os
import subprocess

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Inches

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Pashto_Stemmer_Paper.docx")

PASHTO = "Noto Naskh Arabic"
BODY = "Times New Roman"
INK = RGBColor(0x00, 0x00, 0x00)
GREY = RGBColor(0x44, 0x44, 0x44)


# --------------------------------------------------------------------------- #
def style_run(run, size=10, bold=False, italic=False, color=None, pashto=False,
              font=None):
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color or INK
    name = PASHTO if pashto else (font or BODY)
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), name)
    if pashto:
        el = OxmlElement("w:rtl")
        el.set(qn("w:val"), "1")
        rpr.append(el)
    return run


def P(text):
    """A plain Latin-script fragment."""
    return (text, {})


def S(text):
    """A Pashto fragment."""
    return (text, {"pashto": True, "size": 11})


def I(text):
    """An italic fragment."""
    return (text, {"italic": True})


def para(doc, parts, size=10, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=6,
         before=0, indent=0.0, first_line=0.0):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.space_after = Pt(after)
    pf.space_before = Pt(before)
    pf.line_spacing = 1.08
    if indent:
        pf.left_indent = Inches(indent)
    if first_line:
        pf.first_line_indent = Inches(first_line)
    if isinstance(parts, str):
        parts = [P(parts)]
    emit(p, parts, size)
    return p


def emit(p, parts, size):
    """Write the fragments of a paragraph.

    A left-to-right mark is dropped after every Pashto run. Without it the
    neutral characters that follow a right-to-left run -- the arrow in
    "jor-edal -> jor", the comma in a list of examples -- inherit the Pashto
    direction and are laid out backwards.
    """
    for text, kw in parts:
        kw = dict(kw)
        kw.setdefault("size", size)
        style_run(p.add_run(text), **kw)
        if kw.get("pashto"):
            style_run(p.add_run("\u200e"), size=1)


def h1(doc, text, number=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    label = f"{number}. {text}".upper() if number else text.upper()
    style_run(p.add_run(label), size=10, bold=True)
    return p


def h2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    style_run(p.add_run(text), size=10, italic=True, bold=True)
    return p


def bullet(doc, parts):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.05
    if isinstance(parts, str):
        parts = [P(parts)]
    emit(p, parts, 10)
    return p


def shade(cell, fill):
    tcpr = cell._tc.get_or_add_tcPr()
    el = OxmlElement("w:shd")
    el.set(qn("w:val"), "clear")
    el.set(qn("w:fill"), fill)
    tcpr.append(el)


def table(doc, caption, headers, rows, widths=None, pashto_cols=(), note=None,
          pashto_headers=(), body_size=9):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    style_run(p.add_run(caption), size=9, bold=True)
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.autofit = False
    # Word's default cell padding is 0.08 in per side, which on a five-column
    # table adds 0.8 in and pushed the last columns off the page.
    tblpr = t._tbl.tblPr
    # A fixed layout is needed for the column widths below to be honoured;
    # with the default autofit the renderer redistributes them and the last
    # column runs off the page.
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblpr.append(layout)
    mar = OxmlElement("w:tblCellMar")
    for side in ("left", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), "40")       # twentieths of a point ~ 0.028 in
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblpr.append(mar)
    for i, htxt in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        pp = c.paragraphs[0]
        pp.paragraph_format.space_after = Pt(1)
        style_run(pp.add_run(htxt), size=9, bold=True,
                  pashto=(i in pashto_headers))
        shade(c, "E8E8E8")
    # Repeat the header on every page. Without this a table that spans pages
    # shows a headerless grid from the second page on, which is how the
    # appendices looked.
    trpr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trpr.append(th)
    for row in rows:
        tr = t.add_row()
        # keep a row intact rather than splitting it across a page break
        cs = OxmlElement("w:cantSplit")
        tr._tr.get_or_add_trPr().append(cs)
        cells = tr.cells
        # A group-heading row -- a bold label with the rest of the row empty --
        # is merged across the table. Left in the first column it wrapped onto
        # two lines and read like a broken header.
        if str(row[0]).startswith("**") and not any(str(v) for v in row[1:]):
            merged = cells[0].merge(cells[-1])
            merged.text = ""
            pp = merged.paragraphs[0]
            pp.paragraph_format.space_before = Pt(3)
            pp.paragraph_format.space_after = Pt(1)
            style_run(pp.add_run(str(row[0]).replace("**", "")),
                      size=body_size, bold=True, italic=True)
            shade(merged, "F2F2F2")
            continue
        for i, v in enumerate(row):
            cells[i].text = ""
            pp = cells[i].paragraphs[0]
            pp.paragraph_format.space_after = Pt(0)
            pp.paragraph_format.space_before = Pt(0)
            pp.paragraph_format.line_spacing = 1.0
            bold = str(v).startswith("**")
            style_run(pp.add_run(str(v).replace("**", "")), size=body_size, bold=bold,
                      pashto=(i in pashto_cols))
    if widths:
        grid = t._tbl.find(qn("w:tblGrid"))
        for i, w in enumerate(widths):
            if grid is not None and i < len(grid):
                grid[i].set(qn("w:w"), str(int(w * 1440)))
            for row in t.rows:
                row.cells[i].width = Inches(w)
        tw = OxmlElement("w:tblW")
        tw.set(qn("w:w"), str(int(sum(widths) * 1440)))
        tw.set(qn("w:type"), "dxa")
        tblpr.append(tw)
    if note:
        q = doc.add_paragraph()
        q.paragraph_format.space_before = Pt(2)
        q.paragraph_format.space_after = Pt(10)
        style_run(q.add_run(note), size=8.5, italic=True, color=GREY)
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(6)
    return t


def columns(doc, n):
    sec = doc.add_section(WD_SECTION.CONTINUOUS)
    cols = sec._sectPr.xpath("./w:cols")[0]
    cols.set(qn("w:num"), str(n))
    cols.set(qn("w:space"), "360")
    return sec


def two_columns(doc):
    return columns(doc, 2)


def figure(doc, path, caption, width=3.15):
    """A figure with its caption, inside the current column."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    p.add_run().add_picture(path, width=Inches(width))
    q = doc.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.LEFT
    q.paragraph_format.space_after = Pt(10)
    q.paragraph_format.line_spacing = 1.0
    style_run(q.add_run(caption), size=8.5)
    return p


def wide_table(doc, *args, **kw):
    """A table spanning the full page width, as IEEE's table* does.

    The five-column result tables do not fit in a single text column, so they
    break out of the two-column layout and the text resumes after them.
    """
    columns(doc, 1)
    t = table(doc, *args, **kw)
    two_columns(doc)
    return t


def read_tsv(name):
    """Read one of the files make_inventory_tables.py generates."""
    path = os.path.join(HERE, name)
    if not os.path.exists(path):
        raise SystemExit(f"{name} is missing; run paper/make_inventory_tables.py first")
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n").split("\t") for l in fh if l.strip()]
    head, body = lines[0], lines[1:]
    return [dict(zip(head, row)) for row in body]


def inventory_summary_rows():
    rows_out = []
    totals = [0, 0, 0]
    for d in read_tsv("inventory_summary.tsv"):
        rows_out.append([d["group"], d["rules"], d["published"], d["gated"],
                         d["examples"]])
        for i, k in enumerate(("rules", "published", "gated")):
            totals[i] += int(d[k])
    rows_out.append(["**Total", f"**{totals[0]}", f"**{totals[1]}",
                     f"**{totals[2]}", ""])
    return rows_out


def verb_rows():
    """The 42 strong verbs, parsed from docs/03_irregular_verbs.md."""
    import re
    path = os.path.join(os.path.dirname(HERE), "docs", "03_irregular_verbs.md")
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line.startswith("|") or line.count("|") < 5:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 5 and cells[0].isdigit():
            src = re.sub(r"\*([^*]*)\*", r"\1", cells[5] if len(cells) > 5 else "")
            src = "unverified" if "unverified" in src.lower() else src.split(",")[0][:24]
            out.append([cells[1], cells[2], cells[3], cells[4], src])
    return out


def appendix_rows():
    out, current = [], None
    for d in read_tsv("inventory_rows.tsv"):
        if d["group"] != current:
            current = d["group"]
            out.append(["**" + current, "", "", "", "", "", "", ""])
        out.append([d["affix"], d["type"], d["min"], d["pos"],
                    d["productivity"], d["confidence"], d["strip"], d["source"]])
    return out


# --------------------------------------------------------------------------- #
def build():
    doc = Document()
    for s in doc.sections:
        s.top_margin = s.bottom_margin = Inches(0.9)
        s.left_margin = s.right_margin = Inches(0.85)
    doc.styles["Normal"].font.name = BODY
    doc.styles["Normal"].font.size = Pt(10)

    # ---------------- title block ----------------
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)
    style_run(p.add_run("A Grammar-Driven Rule-Based Stemmer for Pashto"),
              size=18, bold=True)
    for line, sz, it in [("Khairullah Ibrahim Khail", 11, False),
                         ("Institute of Management Sciences, Peshawar, Pakistan", 10, True),
                         ("ibrahimkhil976@gmail.com", 10, False)]:
        q = doc.add_paragraph()
        q.alignment = WD_ALIGN_PARAGRAPH.CENTER
        q.paragraph_format.space_after = Pt(2)
        style_run(q.add_run(line), size=sz, italic=it)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ---------------- abstract ----------------
    h1(doc, "Abstract")
    para(doc,
         "Pashto has roughly forty million speakers and very few text-processing "
         "tools. The only stemmer published for the language applies nine affix "
         "rules without a lexicon and without any means of choosing between "
         "competing analyses. We present a rule-based Pashto stemmer built from "
         "an affix inventory of 117 rules drawn from published grammars, in which "
         "every rule records its source, its productivity, and whether it may be "
         "applied at all. Candidate stems are generated separately from the "
         "decision of which candidate to keep, so a shallower analysis can "
         "displace a deeper one. No machine learning is used.")
    para(doc,
         "Since no annotated set for Pashto stemming existed, we built two. A "
         "development set of 2,912 word types and a held-out set of 500 types "
         "sampled from news text were each annotated independently by three "
         "native-speaker Pashto educators, who agreed on 96.88% of stems "
         "(\u03ba = 0.969). The held-out set was annotated with its reference "
         "column empty and was not consulted while the system was being developed. "
         "499 of its 500 types fall within the stemming task and are the denominator "
         "below; the remaining one needs a different word and is reported apart.")
    para(doc,
         "On that set the proposed system reaches 71.34% exact-match accuracy "
         "against 40.48% for a faithful reimplementation of the prior system, and "
         "70.6% against 16.9% on the types that carry an affix. Paice's "
         "under-stemming index falls from 0.889 to 0.500.")
    para(doc,
         "A secondary finding concerns evaluation itself. The protocol used in "
         "the prior work — presenting system output to native speakers and asking "
         "whether it is acceptable — assigns a score of 100% to a system that "
         "modifies no word at all. We report results under both that protocol and "
         "exact match against a reference fixed in advance, and recommend the "
         "latter for Pashto stemming.")
    para(doc, [I("Keywords: "), P("Pashto, stemming, morphological analysis, "
                                  "rule-based methods, low-resource languages, "
                                  "evaluation methodology, information retrieval")],
         after=10)

    two_columns(doc)

    # ---------------- 1 introduction ----------------
    h1(doc, "Introduction", 1)
    para(doc, "A reader searching for documents about houses does not distinguish "
              "between house, houses and of the houses. A retrieval system does, "
              "because to the system these are three unrelated strings. Stemming "
              "removes that difference by stripping the endings a word carries, so "
              "that related forms collapse onto a single index term. For English the "
              "problem has been settled since Porter's algorithm [2], which remains "
              "in production use after four decades.")
    para(doc, "For Pashto almost nothing exists. The language is spoken by "
              "approximately forty million people across Afghanistan and Pakistan, "
              "is one of the two official languages of Afghanistan, and has a growing "
              "volume of digital text in news and social media. It also has a rich "
              "inflectional system, which is precisely the condition under which "
              "stemming matters. A Pashto retrieval system without stemming will miss "
              "most relevant documents; a classifier will treat the singular and "
              "plural of a key term as unrelated features and learn each from less "
              "data than it has.", first_line=0.18)
    para(doc, "The single published Pashto stemmer, by Aslamzai and Saad [1], applies "
              "nine affix rules in a fixed order with no lexicon and no selection "
              "stage. Our reimplementation of those rules leaves most words untouched, "
              "and damages a substantial fraction of the words it does modify.",
         first_line=0.18)
    para(doc, "Three properties of Pashto make a naive approach fail.", first_line=0.18)

    h2(doc, "A. Five letters for one sound")
    para(doc, "Pashto writes five distinct characters conventionally called ye. They "
              "are not interchangeable; they carry gender, number and case:")
    wide_table(doc, "TABLE I.  THE FIVE PASHTO YE LETTERS",
          ["Letter", "Example", "Function"],
          [["ی", "سړی", "masculine singular direct"],
           ["ي", "سړي", "masculine plural/oblique; 3rd person present"],
           ["ې", "ښکلې", "feminine; plural"],
           ["ۍ", "نجلۍ", "feminine singular, one noun class"],
           ["ئ", "ووایئ", "2nd person plural imperative"]],
          widths=[1.0, 1.4, 4.2], pashto_cols=(0, 1))
    para(doc, [P("Normalization pipelines written for Persian or Urdu routinely merge "
                 "these into a single character. For Pashto that destroys the "
                 "information a stemmer needs: "), S("سړی"), P(" (man) and "),
                S("سړي"), P(" (men) become indistinguishable. Our system preserves "
                            "all five.")])

    h2(doc, "B. Endings that are not endings")
    para(doc, [P("The same final letter may be an affix in one word and part of the "
                 "root in another, with nothing in the surface form to separate the "
                 "two cases: "), S("لنډه"), P(" reduces to "), S("لنډ"),
                P(", where "), S("ه"), P(" marks agreement, while "), S("سیمه"),
                P(" must remain "), S("سیمه"), P(", because there the "), S("ه"),
                P(" belongs to the word. A native speaker resolves this by knowing "
                  "the word; a rule conditioned on the surface form cannot.")])

    h2(doc, "C. Verbs whose stems cannot be derived")
    para(doc, [P("Pashto distinguishes weak verbs, whose stems follow from the "
                 "infinitive, from strong verbs, whose present stem must be known: "),
                S("لیدل"), P(" has the present stem "), S("وین"), P(", and "),
                S("تلل"), P(" has "), S("ځ"), P(". No affix rule derives "), S("وین"),
                P(" from "), S("لیدل"), P(". These verbs are frequent and must be "
                                           "listed.")])

    h2(doc, "D. Contributions")
    bullet(doc, "An affix inventory of 117 rules in which each entry records its "
                "grammatical source, its productivity, a confidence level, and an "
                "explicit decision about whether it may be stripped. Twenty-seven "
                "entries are documented but never applied.")
    bullet(doc, "Two annotated evaluation sets for Pashto stemming, one of which was "
                "annotated blind and never used during development.")
    bullet(doc, "An evaluation protocol that separates performance on word types "
                "carrying an affix from performance on types that do not, because "
                "overall accuracy alone rewards inactivity in a language where nearly "
                "half of word types are uninflected.")
    bullet(doc, "A quantitative account of what each component contributes, including "
                "two components that we retain despite a measured cost and one rule "
                "that we implemented, measured and removed.")
    bullet(doc, "The observation that the evaluation protocol used in prior Pashto "
                "stemming work cannot distinguish a working stemmer from an inert one.")

    # ---------------- 2 related work ----------------
    h1(doc, "Related Work", 2)

    h2(doc, "A. Rule-based stemming")
    para(doc, "Lovins [3] published the first English stemmer, a single-pass "
              "longest-match algorithm over 294 endings. Porter [2] replaced it with "
              "a five-step procedure whose conditions depend on a measure of syllable "
              "count. Its durability is instructive: the algorithm is small, fast, "
              "entirely inspectable, and makes no claim to produce real words. Porter "
              "maps both relational and relate to relat, which is not an English word. "
              "The output of a stemmer is a class label rather than a lemma, and "
              "confusing the two is a recurring error in work on morphologically rich "
              "languages.")
    para(doc, "Paice [4] contributed both an algorithm and, more consequentially for "
              "the present work, an evaluation method [5]. His under-stemming index "
              "counts related word pairs a system fails to conflate, and his "
              "over-stemming index counts unrelated pairs it wrongly merges. Because "
              "the two move in opposite directions, reporting both is more informative "
              "than accuracy alone.", first_line=0.18)

    h2(doc, "B. Arabic-script languages")
    para(doc, "Khoja and Garside [6] built an Arabic root extractor that strips affixes "
              "and matches the remainder against triliteral patterns. Larkey, "
              "Ballesteros and Connell [7] showed that light stemming, removing only a "
              "short list of prefixes and suffixes, outperforms aggressive root "
              "extraction for retrieval. Their conclusion shaped the design adopted "
              "here: removing less, but removing it reliably, is preferable to removing "
              "more. For Persian, Sharifloo and Shamsfard [8] used a bottom-up parser "
              "over a morpheme lexicon. The pattern common to these systems is that a "
              "lexicon resolves ambiguity that rules alone cannot.")

    h2(doc, "C. Pashto")
    para(doc, "Work on Pashto stemming is confined, to our knowledge, to Aslamzai and "
              "Saad [1]. Because that system is the baseline for everything reported "
              "here, we describe it in full.")
    para(doc, [P("Their algorithm applies nine rules, four removing suffixes and five "
                 "removing prefixes, each with a length condition. Rule 1 removes one "
                 "of eleven suffixes from words of five or more characters; Rule 2 "
                 "replaces a final "), S("ي"), P(" with "), S("ه"),
                P(" in words of four or more; Rule 3 removes "), S("من"),
                P("; Rule 4 removes "), S("یز"), P(" and appends "), S("ه"),
                P("; Rules 5, 6, 7 and 9 remove prefixes; and Rule 8 reduces a "
                  "reduplicated word to one copy.")], first_line=0.18)
    para(doc, "Reproducing the baseline exactly mattered, since a comparison against a "
              "misimplementation would be worthless. Our implementation reproduces all "
              "eight worked examples given in the paper. Four points in the publication "
              "required a decision, and we record them so that they can be checked:",
         first_line=0.18)
    bullet(doc, [P("The order of prefix and suffix removal is not stated. We remove "
                   "suffixes first, because the paper's own example "), S("موتروان"),
                  P(" → "), S("موتر"), P(" only succeeds in that order; with "
                    "prefixes first, the Rule 5 prefix "), S("م"),
                  P(" removes the first letter of "), S("موتر"), P(".")])
    bullet(doc, [P("Rule 3 is stated for words of “more than 5 characters” but "
                   "its example "), S("واکمن"), P(" has exactly five, so we implement "
                   "the condition as five or more.")])
    bullet(doc, [P("The Rule 5 prefix list contains a bare "), S("م"),
                  P(", which contradicts the "), S("موتروان"), P(" example above. We "
                    "exclude it, giving the baseline the reading its own example implies "
                    "rather than the one that would lower its score.")])
    bullet(doc, [P("Rule 4 instructs the reader to remove "), S("یز"),
                  P(" and append "), S("ه"), P(". Its first example follows this, but "
                    "its second gives "), S("دودیز"), P(" → "), S("دود"),
                  P(" with no "), S("ه"), P(".")])
    para(doc, [P("Rule 2 is also linguistically incorrect as published. It maps the "
                 "masculine plural adjective "), S("ښکلي"), P(" to "), S("ښکله"),
                P(", which is the feminine singular; Tegey and Robson [9] give the "
                  "masculine singular "), S("ښکلی"), P(" as the base form of this "
                  "class. The rule is corrected in our inventory.")])
    para(doc, "Finally, the reported accuracy of 87% is not comparable with the figures "
              "in this paper, and the difference lies in the protocol rather than in the "
              "algorithm. We return to this in Section VI.", first_line=0.18)

    h2(doc, "D. Grammatical sources")
    para(doc, "The affix inventory was assembled from published descriptions rather "
              "than by inspecting a corpus. Table II lists the sources used and the tag "
              "each carries in the released inventory file.")
    para(doc, [P("Of the 117 rules, 111 cite a published source, located by "
                 "chapter in Tegey and Robson [9] or by section in Penzl [12]. The "
                 "remaining six are oblique and feminine variants of suffixes that "
                 "are themselves cited \u2014 "), S("ونکو"), P(" and "), S("ونکې"),
                P(" beside "), S("ونکی"), P(", "), S("یزو"), P(" beside "), S("یز"),
                P(", "), S("والو"), P(" beside "), S("والی"), P(" \u2014 and a "
                  "grammar that gives the base form does not always list every case "
                  "variant. They are marked author-proposed rather than left to look "
                  "unsourced.")], first_line=0.18)
    para(doc, "The provenance of each rule is recorded in Appendix A rather than "
              "summarised, so a reader can check any individual entry. One "
              "distinction a single citation count would hide is worth drawing: "
              "sixteen of the cited rules are documented and never applied. For "
              "those the citation establishes that the affix exists, not that "
              "removing it is safe, and the decision not to strip rests on measured "
              "behaviour rather than on the grammar.", first_line=0.18)
    wide_table(doc, "TABLE II.  SOURCES FOR THE AFFIX INVENTORY",
          ["Source", "Tag"],
          [["Tegey & Robson, A Reference Grammar of Pashto [9]", "[T&R]"],
           ["Robson & Tegey, “Pashto” [10]", "[R&T]"],
           ["David, Descriptive Grammar of Pashto [11]", "—"],
           ["Naeem & Khan, derivational morphology [13]", "[N&K]"],
           ["Khan, Pashto diminutives [16]", "[Khan23]"],
           ["Penzl, A Grammar of Pashto [12]", "[Penzl]"],
           ["Wiktionary / kaikki.org Pashto suffixes", "[W]"],
           ["Apertium apertium-pus", "[AP]"]],
          widths=[4.6, 2.0])

    # ---------------- 3 morphology ----------------
    h1(doc, "Pashto Morphology", 3)
    para(doc, "This section covers the parts of the morphology that bear on the design. "
              "It is not a complete grammatical description.")

    h2(doc, "A. Orthography")
    para(doc, [P("Beyond the Arabic inventory, Pashto adds retroflex and other "
                 "consonants that occur in neither Arabic nor Persian: "),
                S("ټ ډ ړ ږ ښ ځ څ ڼ ګ"), P(". A word containing any of these is "
                  "certainly Pashto rather than a loan, and the system uses that fact.")])
    para(doc, [P("A complication became apparent only late in this work. The same suffix "
                 "is written with different ye letters in different registers: "
                 "dictionary orthography prefers "), S("لومړی"),
                P(" where news orthography writes "), S("لومړي"), P(". A rule spelled "
                  "in one convention does not fire on the other. The system therefore "
                  "compares a folded key when deciding whether a rule applies, while "
                  "the letters it writes out are never altered. Section VII quantifies "
                  "the effect.")], first_line=0.18)

    h2(doc, "B. Nominal inflection")
    para(doc, [P("Tegey and Robson divide Pashto nouns into masculine classes M1–M4 "
                 "and feminine classes F1–F3, each with its own plural and oblique "
                 "endings. The endings the system removes most often are "), S("ونه"),
                P(" and "), S("ونو"), P(" (masculine plural and its oblique), "),
                S("ان"), P(" and "), S("انو"), P(" (animate plural and oblique), "),
                S("ې"), P(" (feminine plural) and "), S("و"),
                P(" (oblique plural). Nominal inflection is not a simple "
                  "suffix-substitution system: gender, number, noun class and the final "
                  "shape of the stem can all trigger stem alternation.")])

    h2(doc, "C. Verbal morphology")
    para(doc, [P("Two productive patterns form verbs from nouns and adjectives. The "),
                S("ېدل"), P(" intransitive and "), S("ول"), P(" transitive patterns "
                  "are regular, so both are handled by rule and neither appears in the "
                  "dictionary: "), S("جوړېدل"), P(" → "), S("جوړ"), P(" and "),
                S("جوړول"), P(" → "), S("جوړ"), P(". For strong verbs the present "
                  "stem cannot be predicted, and these are listed: "), S("لیدل"),
                P(" / "), S("وین"), P(", "), S("تلل"), P(" / "), S("ځ"), P(", "),
                S("کول"), P(" / "), S("کو"), P(", "), S("غوښتل"), P(" / "),
                S("غواړ"), P(".")])

    h2(doc, "D. Loanwords")
    para(doc, [P("Pashto has borrowed heavily from Arabic, Persian and English, and "
                 "loanwords are the principal remaining source of error, because their "
                 "endings frequently resemble Pashto affixes. The correct stem of "),
                S("منشي"), P(" is "), S("منشي"), P(", not "), S("منش"), P("; of "),
                S("کورس"), P(" is "), S("کورس"), P(", not "), S("کور"),
                P(", which is a different word meaning "), I("house"), P("; and of "),
                S("بېجينګ"), P(" (Beijing) is the word itself, not "), S("جينګ"),
                P(". Arabic broken plurals are a related problem, formed by changing the "
                  "internal vowel pattern rather than by adding material, so that no "
                  "suffix rule can reach them.")])

    # ---------------- 4 method ----------------
    h1(doc, "Method", 4)
    para(doc, "Fig. 1 shows the order in which a word passes through the system. Three "
              "of the stages can return a stem on their own, and the remaining word "
              "goes to the generate-and-select stages that do the general work. Every "
              "stage can be disabled independently, which is what makes the component "
              "study in Section VII possible.")
    figure(doc, os.path.join(HERE, "figures", "pipeline.png"),
           "Fig. 1.  The pipeline. Stages 2\u20134 can each return a stem and stop; "
           "everything else reaches stage 5, where all applicable rules are applied and "
           "the results are then scored against one another. The two dashed boxes are "
           "not stages: the guards constrain which strips the earlier stages may make, "
           "and the irregular-verb dictionary is an optional lemmatization mode that is "
           "off by default. Affixes are transliterated in the figure for legibility and "
           "given in Pashto script in the text.")

    h2(doc, "A. Normalization")
    para(doc, [P("Normalization removes differences that carry no information: Arabic "
                 "diacritics, the tatweel elongation character, zero-width joiners, and "
                 "the several Unicode encodings of the same letter. The Arabic kaf is "
                 "mapped to the Pashto keheh, the alef-hamza forms to bare alef, and the "
                 "Urdu letters common in Pashto written in Pakistan ("), S("ٹ ڈ ڑ ے"),
                P(" and the Persian "), S("گ"), P(") to their Pashto counterparts. These "
                  "are encoding corrections rather than changes of spelling.")])
    para(doc, "What normalization does not do is merge the ye letters. We verified that "
              "no ye character is altered in any cell of either evaluation set. The "
              "This holds through the whole pipeline, not only at the normalization "
              "step: the output is always a slice of the input token, so whichever ye "
              "the word was written with is the one the stem carries. A rule spelled "
              "with \u06cc that fires on a word spelled with \u064a returns \u064a. The "
              "aggressive fold remains available behind a configuration flag so that the "
              "cost of the error reported in the literature can be measured rather than "
              "asserted.", first_line=0.18)

    h2(doc, "B. The affix inventory")
    para(doc, "The inventory holds 107 suffix rules and 10 prefix rules. Each rule "
              "records the affix and the side it attaches to; whether it is inflectional "
              "or derivational; a minimum surviving stem length; the part of speech the "
              "affix signals, where known; its productivity (productive, restricted, "
              "lexicalized or borrowed); a confidence level; and whether it may be "
              "stripped at all.")
    para(doc, [P("Table III gives the schema in full, with three entries written out. "
                 "The last field does real work. Twenty-seven entries are documented but "
                 "never applied, because applying them was measured to be harmful or "
                 "because the grammatical source provides no attested example. The "
                 "lexicalized diminutive "), S("وکی"), P(", the last column of "
                  "Table III, is one: it survives only in fixed words such as "),
                S("وړوکی"), P(", so removing it by rule damages them. Recording the "
                  "affix and refusing to strip it is not the same as omitting it, "
                  "because the inventory is also a description of the language. The "
                  "minimum stem length does equally real work: without it the verb "),
                S("کېدل"), P(" reduces to the single letter "), S("ک"), P(".")],
         first_line=0.18)
    wide_table(doc, "TABLE III.  THE RULE SCHEMA, WITH THREE ENTRIES WRITTEN OUT",
               ["Field", "ونه", "توب", "وکی"],
               [["side", "suffix", "suffix", "suffix"],
                ["category", "inflectional", "derivational", "derivational"],
                ["min. stem", "2", "3", "3"],
                ["POS signalled", "N", "N", "N"],
                ["productivity", "productive", "productive", "lexicalized"],
                ["confidence", "high", "high", "low"],
                ["strip allowed", "yes", "yes", "**no"],
                ["source", "[T&R] M2", "[N&K]", "inventory \u00a74"],
                ["example", "کورونه \u2192 کور", "مینتوب \u2192 مین",
                 "وړوکی unchanged"]],
               widths=[1.3, 1.9, 1.9, 1.7], pashto_cols=(1, 2, 3),
               pashto_headers=(1, 2, 3),
               note="The third entry is documented and never applied. The header row "
                    "and the last two rows are in Pashto script.")
    para(doc, "Table IV groups the 117 rules by what they do. Derivation accounts for "
              "71 of them against 37 inflectional rules, which is the opposite of what "
              "a stemmer for English would need and follows from where Pashto puts its "
              "productive morphology. The grouping also shows where the gated entries "
              "are concentrated: 16 of the 27 are noun-forming derivational suffixes, "
              "which is the area where lexicalization is commonest and where a rule is "
              "most likely to be documented in a grammar and still be unsafe to apply.")
    wide_table(doc, "TABLE IV.  THE 117 RULES BY FUNCTION",
               ["Group", "Rules", "Published", "Kept", "Examples"],
               inventory_summary_rows(),
               widths=[2.0, 0.7, 0.95, 0.65, 2.3], pashto_cols=(4,),
               note="\u201cPublished\u201d counts the rules citing a published grammar "
                    "or lexical resource; \u201ckept\u201d counts those documented and "
                    "never stripped. The full inventory is Appendix A.")

    h2(doc, "C. Length rules")
    para(doc, [P("Three rules were contributed by the author, a native speaker of "
                 "Pashto, from his own judgement, and then tested against the "
                 "annotated data. A word of three "
                 "letters or fewer is returned unchanged. A word of four or five letters "
                 "ending in one of the five ye letters or in "), S("ه"),
                P(" loses that letter. A word ending in "), S("ستان"),
                P(" loses that suffix, and stripping stops there.")])
    para(doc, [P("The last condition is necessary: allowing the general rules to "
                 "continue produced "), S("ترکمنستان"), P(" → "), S("ترک"),
                P(" rather than "), S("ترکمن"), P(". The second rule originally "
                  "included "), S("ل"), P(", which we removed after measuring it. On a "
                  "verb "), S("ل"), P(" is the infinitive ending, but on a noun it is "
                  "part of the root, and the rule could not distinguish the two: it "
                  "reduced "), S("کابل"), P(" to "), S("کاب"), P(" and "), S("لامل"),
                P(" to "), S("لام"), P(", accounting for 51 over-strips on its own.")],
         first_line=0.18)
    para(doc, [P("A fourth rule was proposed and rejected. It would have removed the "
                 "last three characters of any non-Pashto word of seven characters or "
                 "more. Measured against three independent references, removing a "
                 "documented affix instead was more accurate in both careful "
                 "annotations (45.0% against 25.0% on the development set, 51.6% "
                 "against 43.5% on the held-out set). Every word the rule damaged "
                 "carried a genuine affix: "), S("مسووليت"), P(" became "), S("مسوو"),
                P(" where the affix is "), S("یت"), P(", and "), S("اعلانات"),
                P(" became "), S("اعلا"), P(" where the affix is "), S("ات"),
                P(". The rule fired before the inventory was consulted and cut through "
                  "the root.")], first_line=0.18)

    h2(doc, "D. Candidate generation and selection")
    para(doc, [P("Generation and selection are separate, which is the central design "
                 "decision borrowed from the Persian and Urdu hybrid systems. The "
                 "generator applies every rule that fits and returns all distinct forms "
                 "reached, including the original word with nothing removed. For "),
                S("کورونو"), P(" the pool contains the untouched form, the result of "
                  "removing "), S("ونو"), P(", and the result of removing "), S("و"),
                P(" alone. Nothing is decided at this stage, which is what allows a "
                  "shallower analysis to displace a deeper one.")])
    para(doc, "A word that is already a stem is not passed through untouched by "
              "default. Below the length rules it enters the same competition as any "
              "other word, as the no-strip candidate, and it can lose: that is why the "
              "system modifies 68.3% of held-out types while the reference modifies "
              "62.7%, and why the do-nothing floor is not a floor the system inherits.",
         first_line=0.18)
    para(doc, "Selection scores each candidate on how much affix material was "
              "removed, whether other words in the corpus are built on the same stem, "
              "and whether the stem itself is attested. For a candidate reached by "
              "removing k characters the score is \u03b2k, plus a bonus F when the "
              "remainder has a word family of at least two members, plus either the "
              "attestation bonus A and w times the candidate's normalised corpus "
              "frequency if the stem is attested, or \u03b3k if it is not. The family "
              "term fires only when the remainder is at least three characters long.",
         first_line=0.18)
    wide_table(doc, "TABLE V.  WEIGHTS IN THE SELECTION SCORE",
               ["Symbol", "Meaning", "Value"],
               [["\u03b2", "reward per character removed", "0.50"],
                ["F", "bonus when the remainder has a word family", "2.00"],
                ["A (k>0)", "attestation bonus for a stripped candidate", "2.00"],
                ["A (k=0)", "attestation bonus for the unstripped word", "0.50"],
                ["w", "weight on corpus frequency", "0.50"],
                ["\u03b3", "reward per character for an unattested strip", "0.20"]],
               widths=[1.0, 4.1, 0.9],
               note="Set by hand and adjusted on the development set; none were fitted "
                    "automatically, and the held-out set was not used to choose any of "
                    "them.")
    para(doc, "Two of these carry the design decisions. The attestation bonus for the "
              "unstripped word is a quarter of the one a stripped candidate gets, "
              "because the unstripped word is nearly always in the corpus and giving "
              "it the full bonus made inaction the default winner. And \u03b3 is above "
              "zero so the rules can act on a word the lexicon has never seen: an "
              "unattested strip still scores above nothing, so out-of-vocabulary input "
              "is stemmed rather than returned whole, though it loses to any attested "
              "candidate.")
    para(doc, "Two corrections to this stage were necessary during development and are "
              "worth recording, since both are easy to get wrong.", first_line=0.18)
    para(doc, [P("First, an early version required the stem to be an attested Pashto "
                 "word before accepting a strip. That is incorrect: the output of a "
                 "stemmer is a class label, and Porter's "), I("relat"),
                P(" is not an English word either. Attestation now raises a candidate's "
                  "score without gating it, and the system freely produces stems that "
                  "are not words, including "), S("ښوون"), P(", "), S("لوبغاړ"),
                P(" and "), S("پوهن"), P(".")], first_line=0.18)
    para(doc, "Second, the unstripped input word is almost always present in the corpus, "
              "so awarding it the full attestation bonus made inaction the default winner "
              "and concealed every single-letter inflection. Presence in a corpus is "
              "evidence that a string is a word, not that it is a stem, and the no-strip "
              "candidate now receives a much smaller bonus.", first_line=0.18)
    para(doc, [P("A small number of affix groups bypass the scorer entirely; we "
                 "call these the uniform-strip group, and it is the component measured "
                 "under that name in Table X. The abstract-noun and place suffixes "),
                S("تیا"), P(", "), S("توب"),
                P(", "), S("والی"), P(" and "), S("تون"), P(" are long and unambiguous, "
                  "so no competing analysis exists for the scorer to weigh; leaving them "
                  "arbitrated meant that "), S("روغتیا"), P(" and "), S("پوهنتون"),
                P(" remained unchanged because "), S("روغ"), P(" and "), S("پوهن"),
                P(" are absent from the lexicon.")], first_line=0.18)

    h2(doc, "E. Throughput")
    para(doc, "The system is a single pass of string operations over a 117-rule table, "
              "with no model to load. On one core of a commodity laptop it stems "
              "roughly 6,800 word types per second cold and 7,100 warm, measured over "
              "the development set. For an indexing pipeline the stemmer is not the "
              "bottleneck.")

    h2(doc, "F. Guards")
    para(doc, [P("Two guards were added after error analysis. A prefix is removed only "
                 "when what remains is itself an attested word. Without it the system "
                 "strips "), S("لا"), P(" from "), S("لانسیټ"), P(", leaving "),
                S("نسیټ"), P(", and from "), S("لاانتها"), P(", leaving "), S("انتها"),
                P("; with it, both words are returned whole. The guard is conservative "
                  "in both directions, since "), S("لاانتها"), P(" genuinely is "),
                S("لا"), P(" + "), S("انتها"), P(", and we accept the missed strip in "
                  "exchange for not cutting into loanwords.")])
    para(doc, [P("The second guard concerns the interaction between the prefix rules "
                 "and the length rules. A word of four or five letters that begins with "
                 "a removable prefix is passed to the full inventory instead of simply "
                 "losing its last letter. Only a prefix that may actually be removed "
                 "counts: "), S("نا"), P(" is kept rather than stripped, so "),
                S("ناوړه"), P(" is still handled by the length rule and becomes "),
                S("ناوړ"), P(", which is what the annotation gives.")], first_line=0.18)
    para(doc, [P("A third component was implemented and then removed. A compound "
                 "splitter returned the head of a word it judged to be a compound, "
                 "which conflicted with the annotation policy's decision to keep "
                 "compounds whole. Measured, it fired on seven types across the two "
                 "evaluation sets and was wrong on all seven, usually because the "
                 "\u201chead\u201d it returned was itself a suffix: "), S("نړۍوال"),
                P(" \u2192 "), S("وال"), P(" and "), S("پټرولیم"), P(" \u2192 "),
                S("یم"), P(". Disabling it is worth 0.22 points on the development set "
                  "and 0.20 on held-out text. Splitting Pashto compounds reliably needs "
                  "a lexicon of free forms that we do not have, and guessing at the "
                  "boundary was worse than leaving it alone.")], first_line=0.18)

    h2(doc, "G. The verb dictionary and the scope of the task")
    para(doc, [P("The system includes a dictionary of 42 strong verbs, of which 34 are "
                 "checked against a printed grammar and 8 are marked unverified. The "
                 "dictionary maps an inflected form to its verb: "), S("شو"),
                P(" → "), S("کېدل"), P(". That output is a lemma, and substituting "
                  "one word for another is lemmatization rather than stemming. On the "
                  "word types whose reference is a truncation, the dictionary decides "
                  "the output on 69 of them and is right on 11, because it supplies "
                  "the wrong kind of answer; it costs 1.36 points on the development "
                  "set and 0.80 on held-out text.")])
    para(doc, "The dictionary is therefore disabled by default and provided as an "
              "explicit lemmatization mode. We report its contribution separately in "
              "Section VII rather than folding it into the stemming result.",
         first_line=0.18)

    # ---------------- 5 data ----------------
    h1(doc, "Data and Annotation", 5)
    para(doc, "No annotated set for Pashto stemming was available, so two were "
              "constructed. The distinction between them determines how the results "
              "should be read.")

    h2(doc, "A. Corpus")
    para(doc, "Word frequencies were taken from a corpus of Pashto news and general "
              "text assembled from VOA Pashto, BBC Pashto and a topic-labelled "
              "collection, totalling approximately 5.4 million tokens and 68,850 "
              "distinct word types. The lexicon shipped with the system is a "
              "5,443-type frequency list drawn from this material.")
    para(doc, "Building a larger lexicon from the full corpus was attempted and made "
              "results worse. The reason is instructive: a raw corpus contains inflected "
              "forms as well as base forms, so with 48,000 types the attestation signal "
              "ceased to mean “this is a stem” and began rewarding "
              "over-stripped forms that happened to occur. The smaller list was better "
              "by being sparser.", first_line=0.18)

    h2(doc, "B. Development set")
    para(doc, "2,912 word types were annotated independently by three native "
              "speakers of Pashto before the rule inventory was settled: the author, "
              "the principal of a Pashto-medium school, and a university teacher of the "
              "language. None of the three saw another's work, and none saw any system "
              "output. The author then adjudicated the disagreements and produced the "
              "released reference.")
    para(doc, "Two of the three passes are released as separate files, and the "
              "agreement between them can therefore be recomputed rather than asserted. "
              "On the 2,725 types both annotated, they chose the same stem for 96.88%, "
              "which is a Cohen's \u03ba [14] of 0.969. Reduced to the decision that matters "
              "most \u2014 whether the word carries an affix at all \u2014 they agree "
              "on 98.24%, \u03ba = 0.965. The two coefficients answer different "
              "questions. Chance agreement on the full stem string is 0.001, because the "
              "label space is every substring of the word, so there \u03ba adds little "
              "to the raw figure; on the binary decision chance agreement is 0.503, and "
              "the \u03ba is doing real work. Both fall in the band Landis and Koch [15] "
              "describe as almost perfect agreement.", first_line=0.18)
    para(doc, [P("The disagreements are small in substance as well as in number. Of "
                 "the 86 types the two annotators stem differently, 84% differ by one "
                 "or two characters: "), S("مرست"), P(" against "), S("مرس"), P(", "),
                S("خون"), P(" against "), S("خو"), P(". They are disagreements about "
                  "how deep to cut, not about which analysis applies.")],
         first_line=0.18)
    para(doc, "The adjudicated reference stays close to both passes: 93.64% identical "
              "to the school principal's and 94.98% to the university teacher's. Where it "
              "departs from both, it follows the written annotation policy, and the 42 "
              "policy decisions taken during the project are logged individually with "
              "their reasons.", first_line=0.18)
    para(doc, "One part of the construction is circular and we state it rather than "
              "leave it to be found. 116 verb forms were revised for consistency with "
              "the verb analysis, and 81 of those were changed to the reading the system "
              "itself produces, which is 3.0% of the stemming types. That is a real "
              "dependency between the reference and the system, it is confined to verbs, "
              "and it is why the held-out set rather than this one is treated as the "
              "result.", first_line=0.18)

    h2(doc, "C. Held-out set")
    para(doc, "500 word types were sampled at random from the news corpus under three "
              "constraints: a frequency of at least five, to exclude typographical "
              "noise; a length of at least three characters; and no overlap with the "
              "development set. The sample was annotated by the same three native "
              "speakers, with the reference field initially empty so that nothing "
              "anchored them to any system's output. All three agreed on the result, "
              "and it is released as a single reference column. The set was not "
              "consulted during development, and every figure reported for it comes "
              "from a single run of the finished system.")
    para(doc, [P("The first pass was audited by comparing every removal against the "
                 "affix inventory. On the released first-pass file, 50 of 299 removals, "
                 "16.7%, match no documented affix: words such as "), S("مزاج"),
                P(" and "), S("حارث"), P(", which carry no affix at all, had been "
                  "shortened. Thirty rows were revised in response, and the figure "
                  "falls to 33 of 287, or 11.5%. The same audit on the development set "
                  "leaves 105 of 1,355 removals, or 7.7%, unaccounted for.")],
         first_line=0.18)
    para(doc, "That audit procedure is reusable and we recommend it. For each annotated "
              "pair, the material removed is compared against the affix inventory; a "
              "removal matching no affix is either an annotation error or evidence that "
              "the inventory is incomplete, and inspection separates the two. Applied to "
              "the development set, the same procedure identified six affixes the "
              "inventory lacked.", first_line=0.18)
    para(doc, "The 33 removals that remain unaccounted for in the final held-out set "
              "are a live defect, not a resolved one. Each is either an annotation "
              "error, in which case the reported accuracy is measured against a "
              "reference that is wrong on that row, or a gap in the inventory, in which "
              "case the inventory is incomplete. They are released as a list so that "
              "the question is open to inspection rather than settled by assertion.",
         first_line=0.18)

    h2(doc, "D. Annotation policy")
    para(doc, [P("The policy the annotations follow is released with the data. Its main "
                 "provisions are that the output is a stem and need not be a word; that "
                 "Arabic broken plurals are handled by dictionary lookup rather than by "
                 "rule; that proper nouns receive no special treatment, so "),
                S("افغانستان"), P(" loses its "), S("ستان"), P(" like any other word; "
                  "that compounds are kept whole; and that where two analyses are both "
                  "defensible, the shallower is preferred.")])

    # ---------------- 6 protocol ----------------
    h1(doc, "Evaluation Protocol", 6)

    h2(doc, "A. Why exact-match accuracy alone is insufficient")
    para(doc, "The natural measure is the proportion of word types for which the system "
              "produces the annotated stem. On its own it is misleading. Nearly half of "
              "Pashto word types carry no affix and should be returned unchanged, so a "
              "system that modifies nothing scores 47.77% on the development set and "
              "37.27% on the held-out set. Every letter a system declines to remove "
              "earns it credit.")
    para(doc, "Tuning against overall accuracy therefore drives a stemmer towards "
              "inactivity. During this work an apparent improvement of nearly three "
              "points proved, on inspection, to be exactly that: the system had become "
              "more conservative, losing seven points on the word types requiring a "
              "strip while gaining twelve on those requiring none.", first_line=0.18)
    para(doc, "All results below report three figures: accuracy on the types the "
              "annotation strips, accuracy on the types it leaves unchanged, and overall "
              "accuracy. The first cannot be obtained by inaction.", first_line=0.18)

    h2(doc, "B. The scope of the stemming task")
    para(doc, [P("Stemming removes characters; it cannot insert them. Where the "
                 "reference is an Arabic broken plural or a suppletive form — "),
                S("اثارو"), P(" → "), S("اثر"), P(", "), S("نجونو"),
                P(" → "), S("نجلۍ"), P(" — the answer is a lemma that no "
                  "affix rule can produce. Marking a truncating stemmer wrong on those "
                  "types penalises it for not being a lemmatizer.")])
    para(doc, "We therefore score the two tasks separately. A type belongs to the "
              "stemming task when the reference can be obtained by removing characters "
              "from the word, comparison being insensitive to which ye letter is "
              "written. By this criterion the development set contributes 2,717 stemming "
              "types and 195 lemma types, and the held-out set 499 and 1. Of the 195, "
              "155 are verb forms whose reference is an infinitive that no truncation "
              "reaches; the remaining 40 are suppletive or irregular nominals and "
              "Arabic broken plurals, so the boundary between the two tasks is almost "
              "entirely the strong verb. Results for "
              "the lemma types are reported separately in Section VII.",
         first_line=0.18)

    h2(doc, "C. Two protocols compared")
    para(doc, "Aslamzai and Saad report 87% accuracy; our reimplementation of the same "
              "nine rules reaches 40.48% on held-out data. The difference is entirely "
              "methodological, and the point is important enough to measure rather than "
              "assert.")
    para(doc, "Protocol A, used throughout this paper, fixes the reference before any "
              "system output is seen and counts a result only if it matches exactly. "
              "Protocol B reproduces theirs: a judge is shown the output and decides "
              "whether it is an acceptable analysis. We implement Protocol B "
              "reproducibly by counting an output as acceptable when nothing was removed "
              "that is not a documented affix, and by treating an unchanged word as "
              "always acceptable, which is how a judge shown an unchanged word would "
              "score it.", first_line=0.18)
    wide_table(doc, "TABLE VI.  THE SAME 499 HELD-OUT WORD TYPES UNDER BOTH PROTOCOLS",
          ["System", "A: exact", "B: judged", "Modified"],
          [["Modifies nothing", "37.27%", "**100.00%", "0.0%"],
           ["Aslamzai & Saad [1]", "40.48%", "80.76%", "37.5%"],
           ["**Proposed", "**71.34%", "**98.60%", "68.3%"]],
          widths=[2.6, 1.3, 1.3, 1.3],
          note="The final column gives the proportion of types the system modifies at "
               "all.")
    para(doc, "The first row of Table VI is the finding. Under Protocol B a system that "
              "modifies no word scores 100%, because every unchanged word is acceptable "
              "to a judge and it produces nothing else. The protocol cannot separate a "
              "working stemmer from an inert one, and a figure obtained under it cannot "
              "be compared with an exact-match figure.")
    para(doc, "Nothing here shows the published 87% to be incorrect. It shows that the "
              "measurement answers a different question. We note that the proposed "
              "system also outperforms the baseline under Protocol B, by 98.60% to "
              "80.76%, so the conclusion does not depend on the choice.",
         first_line=0.18)

    # ---------------- 7 results ----------------
    h1(doc, "Results", 7)

    h2(doc, "A. Held-out evaluation")
    para(doc, "Table VII reports the held-out set, which is the primary result: 499 word "
              "types from news text, annotated with the reference field initially empty "
              "and never used during development.")
    wide_table(doc, "TABLE VII.  HELD-OUT EVALUATION, 499 WORD TYPES",
          ["System", "Accuracy", "Affixed", "Bare", "UI"],
          [["Modifies nothing", "37.27%", "0.0%", "100.0%", "1.000"],
           ["Aslamzai & Saad", "40.48%", "16.9%", "80.1%", "0.889"],
           ["**Proposed", "**71.34%", "**70.6%", "72.6%", "**0.500"]],
          widths=[2.2, 1.2, 1.1, 1.1, 0.9],
          note="“Affixed” and “Bare” are accuracy on the types the "
               "annotation changes and leaves unchanged.")
    para(doc, "The two systems fail in opposite directions, and that is more "
              "informative than the gap between them. Of the baseline's 297 held-out "
              "errors, 254 \u2014 86% \u2014 are under-strips, and 163 are words it "
              "left untouched altogether; only 9% are over-strips. Of our 143, 51% are "
              "over-strips and 44% under-strips. The baseline's problem is inaction, "
              "ours is excess, which is the trade a stemmer has to make and the reason "
              "the two halves of the task are reported separately.")
    para(doc, "The proposed system improves on the baseline by 30.9 points overall. The "
              "separation of the two halves is more informative than the overall figure: "
              "on the types that require a strip the baseline reaches 16.9% and the "
              "proposed system 70.6%, a factor of four. Paice's under-stemming index "
              "falls from 0.889 to 0.500, and over-stemming remains below 4×10⁻⁵.")

    h2(doc, "B. Development set")
    wide_table(doc, "TABLE VIII.  DEVELOPMENT SET, 2,717 STEMMING TYPES",
          ["System", "Accuracy", "Affixed", "Bare", "UI"],
          [["Modifies nothing", "47.77%", "0.0%", "100.0%", "1.000"],
           ["Aslamzai & Saad", "50.68%", "12.2%", "92.8%", "0.919"],
           ["**Proposed", "**80.27%", "**78.6%", "82.0%", "**0.304"]],
          widths=[2.2, 1.2, 1.1, 1.1, 0.9])
    para(doc, "Table VIII reports the development set. The figure is higher than the "
              "held-out result. The revisions described in Section V.B account for 0.07 "
              "points of that gap, so the explanation lies elsewhere: it is "
              "orthographic, and Section VII.E gives it. The development set is "
              "reported for comparability with the baseline, which is scored "
              "identically, and because Paice's indices are more stable on the larger "
              "set. On the types requiring a strip the margin is wider still: 78.6% "
              "against 12.2%, a factor of six.")

    h2(doc, "C. Two external datasets")
    para(doc, "After the system was finalised, it was run against two independently "
              "annotated Pashto word lists of 5,000 and 10,000 types. Neither was "
              "produced by this project, and 96% of their entries appear in neither of "
              "our evaluation sets. Exact-match accuracy is 71.96% and 70.39%, against "
              "51.24% and 47.95% for the baseline. Those figures sit beside the 71.34% "
              "measured on held-out news text, which is the point: the system does not "
              "depend on the data it was built against.")
    wide_table(doc, "TABLE IX.  TWO INDEPENDENTLY ANNOTATED WORD LISTS",
               ["Dataset", "Types", "Exact", "Folded"],
               [["External, 5,000 types", "5,000", "**71.96%", "**80.14%"],
                ["    Aslamzai & Saad", "", "51.24%", "57.36%"],
                ["External, 10,000 types", "10,000", "**70.39%", "**77.69%"],
                ["    Aslamzai & Saad", "", "47.95%", "53.68%"],
                ["Our held-out set", "499", "71.34%", "72.14%"],
                ["Our development set", "2,717", "80.27%", "81.78%"]],
               widths=[2.6, 1.1, 1.3, 1.3],
               note="The folded column compares with the five ye letters treated as "
                    "equal; the stemmer's output is never rewritten.")
    para(doc, [P("Both lists carry a reference column normalised to "), S("ی"),
                P(" while their word column retains "), S("ي"), P(", so a stem is "
                  "scored wrong whenever it preserves the letter the word actually "
                  "has. Folding the five ye letters together for the comparison alone "
                  "raises the two figures to 80.14% and 77.69%. The same folded "
                  "comparison is worth 1.51 points on our development set and 0.80 on "
                  "our held-out set, both of which are internally consistent in their "
                  "orthography. The size of that difference is what the measurement "
                  "shows: seven to eight points on the external lists against one on "
                  "ours places the disagreement in how they spell the reference rather "
                  "than in the stemming.")])
    para(doc, [P("One caveat limits what these lists establish. On the words "
                 "they share with our development set the two references agree 70.8% "
                 "and 64.1% of the time. Sorting the disagreements shows they are a "
                 "difference of policy rather than noise. About a quarter \u2014 19.1% "
                 "on the 5,000-type list and 24.3% on the larger one \u2014 are cases "
                 "where our reference gives a lemma that no truncation reaches, "),
                S("اخلی"), P(" \u2192 "), S("اخیستل"), P(" against their "), S("اخ"),
                P("; those are not disagreements about stemming at all but about where "
                  "stemming stops. Of the rest, roughly half cut deeper than we do ("),
                S("تنګی"), P(" \u2192 "), S("تن"), P(" against our "), S("تنګ"),
                P(") and about a quarter cut less ("), S("استازیتوب"), P(" \u2192 "),
                S("استازی"), P(" against our "), S("استاز"), P("). Only two "
                  "disagreements in 154 come down to the spelling of a ye. The two "
                  "annotations differ consistently in how deep a stem should go and in "
                  "whether verbs are reduced to a stem or to an infinitive, which is "
                  "why these lists test generalisation rather than correctness under "
                  "our policy.")], first_line=0.18)

    h2(doc, "D. Component study")
    wide_table(doc, "TABLE X.  EACH COMPONENT REMOVED IN TURN",
          ["Configuration", "Development", "Held-out"],
          [["**Full system", "**80.27%", "**71.34%"],
           ["− suffix rules", "71.99% (−8.28)", "58.92% (−12.42)"],
           ["− length rules", "77.62% (−2.65)", "69.34% (−2.00)"],
           ["− corpus lexicon", "80.09% (−0.18)", "71.74% (+0.40)"],
           ["− uniform-strip group", "80.05% (−0.22)", "71.14% (−0.20)"],
           ["− prefix rules", "80.24% (−0.04)", "71.54% (+0.20)"],
           ["+ verb dictionary", "78.91% (−1.36)", "70.54% (−0.80)"]],
          widths=[2.6, 1.95, 1.95],
          note="Changes in percentage points.")
    para(doc, "The suffix inventory does most of the work, and removing it costs 12.4 "
              "points on held-out text. The author's length rules contribute between two "
              "and three points on both sets.")
    para(doc, "Three rows record decisions taken against the measured score, and we "
              "state them explicitly rather than quietly adopting whichever setting "
              "scored best.", first_line=0.18)
    para(doc, [P("Prefix stripping costs a few hundredths of a point on the "
                 "development set. We retain it because "), S("هم"), P(", "), S("بیا"),
                P(", "), S("نیم"), P(" and "), S("لا"), P(" are genuine Pashto "
                  "prefixes, and removing the rules would amount to claiming the "
                  "language has none; the attestation guard described in Section IV.E "
                  "is what makes them safe. The small effect is itself explained by the "
                  "inventory: of the ten prefix rules, four are documented and never "
                  "stripped. "), S("نا"), P(", "), S("بې"), P(" and "), S("غیر"),
                P(" are negation prefixes that the annotation policy keeps, because "),
                S("ناقانونه"), P(" is not an instance of "), S("قانون"),
                P(" but its opposite, and "), S("سر"), P(" is a free noun as often as "
                  "it is a prefix.")], first_line=0.18)
    para(doc, "The corpus lexicon is worth 0.18 points on the development set and "
              "−0.40 on held-out text. Its contribution is now marginal, because "
              "the uniform-strip and length rules decide most cases before the scorer is "
              "consulted. We report this plainly: the system should not be described as "
              "lexicon-driven.", first_line=0.18)
    para(doc, "Enabling the verb dictionary costs 1.36 points on the development set and "
              "0.80 on held-out text, for the "
              "reason given in Section IV.F. Its proper contribution is to the lemma "
              "types, where it answers 51 of the 195 in the development set against "
              "8 without it.",
         first_line=0.18)

    h2(doc, "E. Orthography")
    para(doc, [P("The gap between the two evaluation sets has one dominant cause. Of the "
                 "500 held-out news types, 118 contain the hard ye "), S("ي"),
                P("; of the 2,912 development types, none do. The inventory contained "
                  "thirteen rules ending in the narrow ye "), S("ی"),
                P(" and none ending in "), S("ي"), P(", so a large class of news words "
                  "passed through untouched: "), S("لومړي"), P(" and "), S("تاریخي"),
                P(" were returned unchanged.")])
    para(doc, "Making rule matching insensitive to which ye is written, while leaving the "
              "output letters untouched, corrected this. On the development set, which is "
              "written entirely in one convention, exact matching scores 0.15 points "
              "higher; on held-out news text the folded comparison is worth 1.20 points, "
              "so it earns its place on the set that reflects real text. This is the "
              "clearest instance in the project of a defect that a single-source "
              "evaluation set could not have revealed.", first_line=0.18)

    # ---------------- 8 discussion ----------------
    h1(doc, "Discussion", 8)

    h2(doc, "A. Correct rules and under-determined rules")
    para(doc, [P("A per-rule analysis separates two kinds of failure, and the "
                 "distinction matters for how the remaining error should be addressed.")])
    para(doc, "Table XI gives the precision of the rules that fire most often on "
              "the development set: how many times each contributed to the analysis "
              "finally selected, and how often that analysis matched the reference. "
              "Publishing it is uncomfortable and necessary. A rule can contribute "
              "positive points overall and still be wrong half the time it fires, and a "
              "reader cannot tell the two apart from an ablation table.")
    wide_table(doc, "TABLE XI.  PRECISION OF THE MOST FREQUENTLY FIRING RULES",
               ["Rule", "Fires", "Correct", "Precision"],
               [["R2 keep short word", "398", "357", "89.7%"],
                ["R1 drop ه", "228", "161", "70.6%"],
                ["R1 drop ی", "190", "149", "78.4%"],
                ["R1 drop ې", "160", "133", "83.1%"],
                ["final trim", "131", "81", "61.8%"],
                ["\u2212 ۍ", "126", "106", "84.1%"],
                ["\u2212 و", "108", "88", "81.5%"],
                ["\u2212 ونو", "58", "54", "93.1%"],
                ["R2 drop ې at 3 letters", "39", "21", "**53.8%"],
                ["\u2212 ونه", "39", "35", "89.7%"],
                ["R2 drop و at 3 letters", "32", "18", "**56.2%"],
                ["\u2212 ان", "28", "13", "**46.4%"]],
               widths=[2.6, 1.0, 1.1, 1.3],
               note="\u201cFires\u201d counts the analyses finally selected in which "
                    "the rule took part. Development set.")
    para(doc, [P("Building that table changed the system. Two rules turned out to fire "
                 "26 times between them and be right on none of those occasions: "),
                S("لو"), P(", the oblique infinitive, and "), S("لې"), P(", the "
                  "feminine past participle. Both bundle an "), S("ل"), P(" into the "
                  "affix that the reference keeps, either as the infinitive marker ("),
                S("ساتلو"), P(" \u2192 "), S("ساتل"), P(", not "), S("سات"),
                P(") or as part of the root ("), S("بریالی"), P(" \u2192 "),
                S("بریال"), P("). The rules that remove the final vowel alone already "
                  "produce the right answer, so these two could only ever take one "
                  "letter too many. They are now documented and never applied, which is "
                  "worth 0.85 points on the development set and nothing either way on "
                  "held-out text. This is the same defect as the standalone verbal "),
                S("ل"), P(", removed earlier for the same reason: it applied only to "
                  "nouns where "), S("ل"), P(" belongs to the root and turned "),
                S("کابل"), P(" into "), S("کاب"), P(". Two further rules were removed "
                  "during the work, one taking "), S("نی"), P(" as a unit where the "
                  "affix is usually the "), S("ی"), P(" alone, and one restoring a "
                  "feminine "), S("ه"), P(" to any stem that had lost one, which "
                  "produced "), S("کورونو"), P(" \u2192 "), S("کورونه"), P(".")])
    para(doc, [P("Three rules remain below 60% precision and are kept. "), S("ان"),
                P(" is right 13 times in 28, but it is the ordinary animate plural of "
                  "Pashto and gating it costs 0.40 points on held-out text; its low "
                  "precision reflects competition with longer analyses rather than a "
                  "defect in the rule. The two three-letter length rules sit at 53.8% "
                  "and 56.2% for the reason the next paragraph describes, and the "
                  "alternative to a coin-flip there is to leave every short inflected "
                  "word unstemmed.")], first_line=0.18)
    para(doc, [P("Other rules are correct but under-determined. The rule removing a "
                 "final "), S("ه"), P(" from a short word fires 131 times on the "
                  "development set and is correct 86 times. "), S("لنډه"),
                P(" → "), S("لنډ"), P(" is right and "), S("خواړه"), P(" → "),
                S("خواړ"), P(" is wrong, and the two words are indistinguishable in "
                  "shape. Removing the rule loses more than it saves: overall accuracy "
                  "falls by 1.62 points. No reformulation conditioned on the surface "
                  "form can help; only a lexical resource can.")], first_line=0.18)

    h2(doc, "B. What limits the current accuracy")
    para(doc, [P("The 536 development-set errors divide into three kinds. 293 of "
                 "them, 55%, are over-strips, where the system removed more than the "
                 "reference does; 202, 38%, are under-strips, and 134 of those are "
                 "words the system left untouched altogether; the remaining 41 are the "
                 "same length as the reference but differ in which letters survive. The "
                 "held-out set behaves the same way, 51% and 44%. Over-stripping is "
                 "therefore the larger problem on both sets, which is what one would "
                 "expect of a system whose scorer rewards removing affix material.")],
         first_line=0.18)
    para(doc, "Table XII locates the errors. Accuracy is high wherever the reference "
              "removes an affix the inventory holds \u2014 90.9% on noun-forming "
              "derivation, 95.1% on verbal inflection \u2014 and the two weak rows are "
              "the ones that do not depend on the inventory being right. 105 types have "
              "a reference the inventory cannot explain at all, and we reach 30.5% on "
              "those. The larger group is the 1,347 types the reference leaves whole, "
              "where we are right 79.1% of the time: 282 words stripped that should not "
              "have been, the biggest single source of error in the system.",
         first_line=0.18)
    wide_table(doc, "TABLE XII.  ACCURACY BY THE AFFIX THE REFERENCE REMOVES",
               ["What the reference removes", "Types", "Accuracy"],
               [["Nominal inflection", "624", "80.1%"],
                ["Verbal inflection", "41", "95.1%"],
                ["Derivation: nouns", "582", "90.9%"],
                ["Derivation: adjectives", "18", "88.9%"],
                ["No affix, word left whole", "1,347", "**79.1%"],
                ["Nothing in the inventory", "105", "**30.5%"]],
               widths=[3.2, 1.2, 1.4], note="Development set.")
    para(doc, [P("We had attributed that bucket to loanwords, and the data does not "
                 "support it. Pashto marks native vocabulary orthographically: a word "
                 "containing one of "), S("ټ ډ ړ ږ ښ ځ څ ڼ ګ ې ۍ"), P(" is certainly "
                  "not a borrowing, though a word without one may be either, so the "
                  "test is one-sided. Among the types the reference leaves whole we are "
                  "wrong on 28.3% of the certainly-native ones and 17.8% of the rest. "
                  "Native words are the harder half, not the easier one, and the errors "
                  "bear it out: "), S("خواړه"), P(", "), S("وړاندې"), P(", "),
                S("داسې"), P(", "), S("پاتې"), P(", "), S("یوازې"), P(" and "),
                S("پورې"), P(" are ordinary Pashto words ending in "), S("ه"),
                P(" or "), S("ې"), P(" that the length rules cut. The shortfall is the "),
                S("ه"), P("/"), S("ی"), P("/"), S("ې"), P(" ambiguity, and it falls on "
                  "native vocabulary rather than on borrowings.")], first_line=0.18)
    para(doc, "We tested the obvious remedy and report the result because it is "
              "negative. A 257-entry list of development-set words that should be left "
              "unchanged raises development accuracy by 8.5 points and held-out accuracy "
              "by zero: of the 51 held-out types needing the same treatment, none appear "
              "in the list. The list is pure memorisation of one sample. The "
              "generalizing form of the same idea is a lexicon of words that must not "
              "be stripped. On the evidence above it would need to cover ordinary "
              "native vocabulary rather than borrowings alone, which makes it a larger "
              "undertaking than we first assumed, and we leave it to future work.", first_line=0.18)

    # ---------------- 9 limitations ----------------
    h1(doc, "Limitations", 9)
    para(doc, "The evaluation is on word types rather than running text, so no "
              "measurement of retrieval effectiveness is reported, and the relationship "
              "between the intrinsic gains shown here and downstream performance remains "
              "untested.")
    para(doc, "Of 117 affix rules, 111 cite a published grammar by chapter or "
              "section and six are marked author-proposed. The chapter attributions "
              "were assembled by the author and have not been independently checked "
              "page by page, so a reader verifying the inventory should treat each "
              "locus as a pointer rather than as a quotation. "
              "than summarised. Of 42 verbs in the dictionary, 34 are checked "
              "against a printed grammar and 8 are marked unverified in the released "
              "documentation. We prefer to label these rather than to present them as "
              "settled.", first_line=0.18)
    para(doc, [P("Compounds are kept whole, which is a policy choice rather than a "
                 "solution: it avoids a class of error at the cost of never conflating "),
                S("لاسلیک"), P(" with "), S("لاس"), P(". The annotation does not follow "
                  "the policy perfectly either, and an audit during development found "
                  "types where the reference itself splits a compound. The released "
                  "audit script reports every removal that matches no documented affix, "
                  "which is where such cases surface.")], first_line=0.18)
    para(doc, "The corpus is drawn from news and general text, so the vocabulary of "
              "specialised domains is under-represented.", first_line=0.18)

    # ---------------- 10 conclusion ----------------
    h1(doc, "Conclusion", 10)
    para(doc, "We presented a rule-based stemmer for Pashto built from an affix "
              "inventory of 117 rules taken from published grammars, each recording its "
              "source, its productivity and an explicit decision about whether it may be "
              "applied. No machine learning is used, and every decision the system makes "
              "can be traced to a rule or a dictionary entry.")
    para(doc, "On 499 held-out word types from news text, annotated blind and never used "
              "during development, the system reaches 71.34% exact-match accuracy "
              "against 40.48% for the published baseline, and 70.6% against 16.9% on the "
              "types that require a strip. On a 2,717-type development set it reaches "
              "80.27% against 50.68%, with Paice's under-stemming index falling from "
              "0.919 to 0.304.", first_line=0.18)
    para(doc, "Three observations generalise beyond this particular system. Exact-match "
              "accuracy is not a sufficient measure for stemming in a language where a "
              "large share of word types carry no affix, because it rewards inactivity; "
              "reporting the two halves of the task separately costs nothing and prevents "
              "the error. An evaluation set drawn from a single orthographic convention "
              "will conceal defects that a second source exposes immediately, as the ye "
              "variants did here. And when a rule-based system finds no affix, the useful "
              "response is to ask what the inventory is missing rather than to remove "
              "characters regardless: the one rule in this work that guessed a boundary "
              "instead of finding one was measured against three references, lost on both "
              "careful annotations, and was removed.", first_line=0.18)
    para(doc, "The stemmer, the affix inventory with its sources, the verb dictionary, "
              "both annotated sets and the scripts that reproduce every figure in this "
              "paper are released under an MIT licence at "
              "https://github.com/Khairullah-Ibrahim-Khail/Pashto_Stemmer. Every "
              "table in this paper is regenerated by "
              "experiments/reproduce_paper.py, and the inter-annotator figures by "
              "experiments/agreement.py.", first_line=0.18)

    # ---------------- acknowledgment ----------------
    h1(doc, "Acknowledgment")
    para(doc, "The author thanks the two native speakers who annotated the data "
              "alongside him: the principal of a Pashto-medium school and a university "
              "teacher of Pashto.")

    # ---------------- references ----------------
    h1(doc, "References")
    refs = [
        "S. Aslamzai and S. Saad, “Pashto language stemming algorithm,” "
        "Asia-Pacific Journal of Information Technology and Multimedia, vol. 4, no. 1, "
        "pp. 25–37, 2015.",
        "M. F. Porter, “An algorithm for suffix stripping,” Program, vol. 14, "
        "no. 3, pp. 130–137, 1980.",
        "J. B. Lovins, “Development of a stemming algorithm,” Mechanical "
        "Translation and Computational Linguistics, vol. 11, pp. 22–31, 1968.",
        "C. D. Paice, “Another stemmer,” ACM SIGIR Forum, vol. 24, no. 3, "
        "pp. 56–61, 1990.",
        "C. D. Paice, “An evaluation method for stemming algorithms,” in Proc. "
        "17th Annual International ACM SIGIR Conference, 1994, pp. 42–50.",
        "S. Khoja and R. Garside, “Stemming Arabic text,” Computing "
        "Department, Lancaster University, Tech. Rep., 1999.",
        "L. S. Larkey, L. Ballesteros, and M. E. Connell, “Improving stemming for "
        "Arabic information retrieval: light stemming and co-occurrence analysis,” "
        "in Proc. 25th Annual International ACM SIGIR Conference, 2002, "
        "pp. 275–282.",
        "A. A. Sharifloo and M. Shamsfard, “A bottom up approach to Persian "
        "stemming,” in Proc. 3rd International Joint Conference on Natural Language "
        "Processing, 2008.",
        "H. Tegey and B. Robson, A Reference Grammar of Pashto. Washington, DC: Center "
        "for Applied Linguistics, 1996.",
        "B. Robson and H. Tegey, “Pashto,” in The Iranian Languages, "
        "G. Windfuhr, Ed. London: Routledge, 2009.",
        "A. B. David, Descriptive Grammar of Pashto and its Dialects. Berlin: "
        "De Gruyter Mouton, 2014.",
        "H. Penzl, A Grammar of Pashto: A Descriptive Study of the Dialect of "
        "Kandahar, Afghanistan. Washington, DC: American Council of Learned "
        "Societies, 1955.",
        "T. Naeem and M. A. Khan, “Automatic derivation of nouns from adjectives in "
        "Pashto,” Center for Language Engineering, Pakistan.",
        "J. Cohen, “A coefficient of agreement for nominal scales,” "
        "Educational and Psychological Measurement, vol. 20, no. 1, "
        "pp. 37–46, 1960.",
        "J. R. Landis and G. G. Koch, “The measurement of observer agreement "
        "for categorical data,” Biometrics, vol. 33, no. 1, "
        "pp. 159–174, 1977.",
        "A. Khan, “The diminutive morphological function between English and "
        "Pashto,” Humanities and Social Sciences Communications, vol. 10, art. 536, "
        "2023.",
    ]
    for i, r in enumerate(refs, 1):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.space_after = Pt(3)
        pf.left_indent = Inches(0.22)
        pf.first_line_indent = Inches(-0.22)
        pf.line_spacing = 1.0
        style_run(p.add_run(f"[{i}] "), size=8.5)
        style_run(p.add_run(r), size=8.5)

    # ---------------- appendix ----------------
    columns(doc, 1)
    h1(doc, "Appendix A:  The Complete Affix Inventory")
    para(doc, "The 117 rules in full, in the order the engine holds them. "
              "\u201cType\u201d gives the side and whether the rule is inflectional or "
              "derivational; \u201cmin\u201d is the shortest stem the rule is allowed "
              "to leave; \u201cstrip\u201d is whether the engine may remove the affix "
              "at all; \u201csource\u201d is what backs the rule \u2014 a published "
              "grammar, this project's inventory document, gated for an entry that is "
              "never applied, and author for one the author proposes. The entries marked no "
              "under "
              "\u201cstrip\u201d are documented and never applied, for the "
              "reasons given in Section IV.B. This table is generated directly from the "
              "rule objects by paper/make_inventory_tables.py, so it cannot drift from "
              "the implementation.")
    table(doc, "TABLE A.I.  THE COMPLETE AFFIX INVENTORY",
          ["Affix", "Type", "min", "POS", "Productivity", "Confidence", "Strip",
           "Source"],
          appendix_rows(),
          widths=[0.8, 0.85, 0.4, 0.8, 0.95, 0.9, 0.6, 0.95], pashto_cols=(0,),
          body_size=8)

    h1(doc, "Appendix B:  The Irregular-Verb Dictionary")
    para(doc, "The 42 strong verbs whose present stem cannot be derived from the "
              "infinitive. The last column names the source; eight entries are marked "
              "unverified and are labelled as such in the released documentation "
              "rather than presented as settled. The dictionary returns a lemma, so it "
              "is off by default and belongs to the lemmatization mode described in "
              "Section IV.G.")
    table(doc, "TABLE B.I.  THE IRREGULAR-VERB DICTIONARY",
          ["Infinitive", "Present stem", "Past", "Gloss", "Source"],
          verb_rows(),
          widths=[1.0, 1.0, 1.1, 1.6, 1.4], pashto_cols=(0, 1, 2), body_size=8)

    doc.save(OUT)
    return OUT


def to_pdf(path):
    for binary in ("libreoffice", "soffice"):
        try:
            subprocess.run(
                [binary, "--headless", "--convert-to", "pdf", "--outdir",
                 os.path.dirname(path), path],
                check=True, capture_output=True, timeout=300,
            )
            return path[:-5] + ".pdf"
        except (FileNotFoundError, subprocess.CalledProcessError,
                subprocess.TimeoutExpired):
            continue
    return None


if __name__ == "__main__":
    docx = build()
    print(f"wrote {docx}")
    pdf = to_pdf(docx)
    print(f"wrote {pdf}" if pdf else "no LibreOffice found; .docx only")
