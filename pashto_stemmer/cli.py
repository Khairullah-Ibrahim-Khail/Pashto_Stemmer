# -*- coding: utf-8 -*-
"""
cli.py
======
Command-line interface for the Pashto stemmer.

Examples
--------
    # stem words given as arguments
    python -m pashto_stemmer.cli کورونه خبرونه افغانستان

    # stem a whole file (one token per output line, tab-separated)
    python -m pashto_stemmer.cli --file article.txt

    # read stdin, show the decision trace
    echo "د کورونو خبرونه" | python -m pashto_stemmer.cli --trace
"""

from __future__ import annotations

import argparse
import sys

from .stemmer import PashtoStemmer, StemmerConfig


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pashto-stem",
        description="Dictionary-enhanced rule-based Pashto stemmer.",
    )
    p.add_argument("words", nargs="*", help="words to stem")
    p.add_argument("-f", "--file", help="stem all tokens in this UTF-8 text file")
    p.add_argument("-t", "--trace", action="store_true",
                   help="print confidence and decision trace")
    p.add_argument("--no-dict", action="store_true", help="disable the lexicon")
    p.add_argument("--no-exceptions", action="store_true",
                   help="disable stopword/irregular/proper-noun handling")
    p.add_argument("--no-pos", action="store_true", help="disable POS filtering")
    p.add_argument("--no-compound", action="store_true",
                   help="disable compound decomposition")
    p.add_argument("--pos", action="store_true",
                   help="enable the POS filter (off by default, as in the library)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    # The defaults here must match StemmerConfig, or the command line and the
    # library give different answers for the same word. use_pos was defaulting
    # to True here and False there, so ښوونځی came out as ښوونځی from the CLI
    # and ښوون from the API.
    cfg = StemmerConfig(
        use_dictionary=not args.no_dict,
        use_exceptions=not args.no_exceptions,
        use_pos=args.pos,
        use_compound=not args.no_compound,
    )
    stemmer = PashtoStemmer(cfg)

    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            text = fh.read()
        results = stemmer.stem_text(text)
    elif args.words:
        results = [stemmer.stem_word(w) for w in args.words]
    else:
        text = sys.stdin.read()
        results = stemmer.stem_text(text)

    for r in results:
        if args.trace:
            print(f"{r.input}\t{r.stem}\t{r.confidence:.2f}\t{r.trace}")
        else:
            print(f"{r.input}\t{r.stem}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
