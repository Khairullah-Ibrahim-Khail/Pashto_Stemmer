# -*- coding: utf-8 -*-
"""
make_figures.py
===============
Renders the figures in paper/figures/ into the formats the two versions of the
paper need: PDF for the LaTeX build and PNG for the Word build.

    python3 paper/make_figures.py

Requires graphviz (the `dot` binary).
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")


def main() -> int:
    sources = sorted(glob.glob(os.path.join(HERE, "*.dot")))
    if not sources:
        print("no .dot sources in", HERE)
        return 1
    for src in sources:
        stem = src[:-4]
        for fmt, extra in (("pdf", []), ("png", ["-Gdpi=300"])):
            subprocess.run(["dot", f"-T{fmt}", *extra, src, "-o", f"{stem}.{fmt}"],
                           check=True)
            print(f"wrote {stem}.{fmt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
