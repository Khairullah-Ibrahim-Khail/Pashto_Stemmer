# -*- coding: utf-8 -*-
"""
make_verb_appendix.py
=====================
Generates Appendix B from the irregular-verb dictionary itself, so that the
appendix cannot claim a verb the software does not hold.

    python paper/make_verb_appendix.py

The dictionary is pashto_stemmer/irregular_verbs.py. Each paradigm's gloss,
present stem, past stem and source live in paper/verbs_sources.tsv, which is
keyed by infinitive; the generator refuses to emit a verb that has no row
there, and reports any row whose verb has left the dictionary.

Generating it is the point: a hand-maintained appendix drifts. The one this
replaced listed 42 verbs against a dictionary of 38, twelve of them not
implemented and eight implemented ones missing, with five source cells
truncated to "[T&R" or "Robson & Tegey Table". A truncated locus is not a
citation, so those five are carried as unverified rather than completed with
a number nobody recorded.
"""
from __future__ import annotations

import csv
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from pashto_stemmer.irregular_verbs import _VERB_PARADIGMS   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.join(HERE, "verbs_sources.tsv")
OUT = os.path.join(HERE, "appendix_verbs.tex")


def ps(s: str) -> str:
    """Wrap Pashto in the paper's \\ps macro; an em dash stays plain."""
    return s if s in ("—", "") else "\\ps{%s}" % s


def tex(s: str) -> str:
    return s.replace("&", "\\&")


def load():
    with open(SOURCES, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def main() -> int:
    rows = load()
    by_inf = {r["infinitive"]: r for r in rows}
    held = list(_VERB_PARADIGMS)

    missing = [v for v in held if v not in by_inf]
    if missing:
        print("ERROR: in the dictionary but not in verbs_sources.tsv: "
              + " ".join(missing))
        return 1
    stale = [r["infinitive"] for r in rows
             if r["in_dictionary"] == "yes" and r["infinitive"] not in _VERB_PARADIGMS]
    if stale:
        print("ERROR: marked in_dictionary but absent from it: " + " ".join(stale))
        return 1

    implemented = [by_inf[v] for v in held]
    identified = [r for r in rows if r["in_dictionary"] == "no"]
    unverified = sum(1 for r in implemented if r["source"] == "unverified")
    forms = sum(len(p) for p in _VERB_PARADIGMS.values())

    L = []
    L.append("\\section{The irregular-verb dictionary}")
    L.append("")
    L.append(f"The {len(implemented)} strong verbs the dictionary holds, with the "
             f"{forms} surface forms they map. These are the verbs whose present "
             "stem cannot be derived from the infinitive. The last column names "
             f"the source; {unverified} entries are marked unverified and are "
             "labelled as such here rather than presented as settled. The "
             "dictionary returns a lemma, so it is off by default and belongs to "
             "the lemmatization mode described in Section~\\ref{sec:scope}. This "
             "table is generated from the dictionary by "
             "\\texttt{paper/make\\_verb\\_appendix.py}, so it cannot claim a verb "
             "the software does not hold.")
    L.append("")
    L.append("\\footnotesize")
    L.append("\\begin{longtable}{lllrl}")
    head = "Infinitive & Present stem & Past & Forms & Gloss, source\\\\"
    L.append("\\toprule")
    L.append(head)
    L.append("\\endfirsthead")
    L.append("\\toprule")
    L.append(head)
    L.append("\\endhead")
    L.append("\\midrule")
    for r in implemented:
        L.append(" & ".join([ps(r["infinitive"]), ps(r["present"]), ps(r["past"]),
                             r["forms"],
                             tex(r["gloss"]) + " --- " + tex(r["source"])]) + "\\\\")
    L.append("\\bottomrule")
    L.append("\\end{longtable}")
    L.append("\\normalsize")
    L.append("")
    L.append(f"A further {len(identified)} strong verbs were identified during the "
             "work and are \\emph{not} in the dictionary. They are listed because "
             "a reader extending the dictionary should start here, and so that "
             "the main table is not read as covering them.")
    L.append("")
    L.append("\\footnotesize")
    L.append("\\begin{longtable}{lllll}")
    L.append("\\toprule")
    L.append("Infinitive & Present stem & Past & Gloss & Source\\\\")
    L.append("\\midrule")
    for r in identified:
        L.append(" & ".join([ps(r["infinitive"]), ps(r["present"]), ps(r["past"]),
                             tex(r["gloss"]), tex(r["source"])]) + "\\\\")
    L.append("\\bottomrule")
    L.append("\\end{longtable}")
    L.append("\\normalsize")
    L.append("")

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"{len(implemented)} verbs in the dictionary ({forms} forms), "
          f"{unverified} unverified; {len(identified)} identified but not "
          f"implemented  -> paper/appendix_verbs.tex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
