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

    # stem one column of a CSV or Excel file into a new column beside it
    python -m pashto_stemmer.cli --csv words.csv --column word --out stemmed.csv

    # lemmatize instead: the irregular-verb dictionary returns a word
    python -m pashto_stemmer.cli --lemmatize شو

Run with --help for the full list of options.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

from .stemmer import PashtoStemmer, StemmerConfig


def build_parser() -> argparse.ArgumentParser:
    d = StemmerConfig()          # the library's defaults, so the two agree
    p = argparse.ArgumentParser(
        prog="pashto-stem",
        description="A grammar-driven rule-based Pashto stemmer.",
        epilog="With no words and no --file, words are read from stdin.",
    )
    p.add_argument("words", nargs="*", help="words to stem")

    src = p.add_argument_group("input")
    src.add_argument("-f", "--file", help="stem every token in this UTF-8 text file")
    src.add_argument("-c", "--csv", "--excel", "--table", dest="table",
                     metavar="PATH",
                     help="stem one column of this CSV, TSV or .xlsx workbook")
    src.add_argument("--column", default="word", metavar="NAME",
                     help="which column to stem (default: word)")
    src.add_argument("--sheet", metavar="NAME",
                     help="which worksheet of an .xlsx file (default: the first)")

    out = p.add_argument_group("output")
    out.add_argument("--out", metavar="PATH",
                     help="where to write the result (default: stdout)")
    out.add_argument("--new-column", metavar="NAME",
                     help="name for the stem column (default: <column>_stemmed)")
    out.add_argument("--only-stems", action="store_true",
                     help="write just the stem column, not the original columns")
    out.add_argument("--unique", action="store_true",
                     help="stem distinct values only")
    out.add_argument("-t", "--trace", action="store_true",
                     help="also report the confidence and the rules that fired")
    out.add_argument("-q", "--quiet", action="store_true",
                     help="suppress the warning that cells hold sentences")

    beh = p.add_argument_group(
        "behaviour (every default below is the library's default, so the "
        "command line and the API give the same answer for the same word)")
    beh.add_argument("--lemmatize", action="store_true",
                     help="enable the irregular-verb dictionary: شو -> کېدل. "
                          "This substitutes one word for another, which is "
                          "lemmatization, not stemming (default: off)")
    beh.add_argument("--no-dict", action="store_true",
                     help="disable the corpus lexicon used to score candidates")
    beh.add_argument("--no-exceptions", action="store_true",
                     help="disable stopwords, the length rules and the "
                          "Arabic-plural list")
    beh.add_argument("--no-prefixes", action="store_true",
                     help="do not strip prefixes")
    beh.add_argument("--no-suffixes", action="store_true",
                     help="do not strip suffixes")
    beh.add_argument("--no-derivational", action="store_true",
                     help="strip inflection only, leaving derivational "
                          "affixes in place")
    beh.add_argument("--pos", action="store_true",
                     help=f"enable the part-of-speech filter "
                          f"(default: {'on' if d.use_pos else 'off'})")
    beh.add_argument("--compound", action="store_true",
                     help=f"enable compound decomposition "
                          f"(default: {'on' if d.use_compound else 'off'})")
    beh.add_argument("--max-passes", type=int, default=d.max_passes,
                     metavar="N",
                     help=f"how many times to re-run the pipeline on its own "
                          f"output (default: {d.max_passes})")
    # Accepted and ignored: both switches name something that is already off.
    # They are kept so that scripts written against the earlier release, where
    # --no-compound was the only way to get the library's behaviour, keep
    # working unchanged.
    beh.add_argument("--no-pos", action="store_true", help=argparse.SUPPRESS)
    beh.add_argument("--no-compound", action="store_true",
                     help=argparse.SUPPRESS)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    # Every switch below is expressed as a change from StemmerConfig's own
    # default, so the command line and the library cannot drift apart. They
    # did twice: use_pos defaulted to True here and False there, so ښوونځی
    # came out as ښوونځی from the CLI and ښوون from the API, and
    # use_compound was being turned on by the absence of --no-compound.
    cfg = StemmerConfig(
        use_dictionary=not args.no_dict,
        use_exceptions=not args.no_exceptions,
        use_prefixes=not args.no_prefixes,
        use_suffixes=not args.no_suffixes,
        strip_derivational=not args.no_derivational,
        use_verb_dictionary=args.lemmatize,
        use_pos=args.pos,
        use_compound=args.compound,
        max_passes=args.max_passes,
    )
    stemmer = PashtoStemmer(cfg)

    if args.table:
        try:
            info = stemmer.stem_file(
                args.table, column=args.column, out=args.out,
                keep_original=not args.only_stems, new_column=args.new_column,
                sheet=args.sheet, unique=args.unique, trace=args.trace,
                warn=not args.quiet,
            )
        except (KeyError, SystemExit) as exc:
            print(str(exc).strip('"\''), file=sys.stderr)
            return 1
        if args.out:
            print(f"{info['rows']} rows -> {info['out']} "
                  f"(new column: {info['column']})", file=sys.stderr)
        else:
            import csv as _csv
            fields = list(info[0].keys()) if info else []
            w = _csv.DictWriter(sys.stdout, fieldnames=fields)
            w.writeheader(); w.writerows(info)
        return 0

    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            text = fh.read()
        results = stemmer.stem_text(text)
    elif args.words:
        results = [stemmer.stem_word(w) for w in args.words]
    else:
        text = sys.stdin.read()
        results = stemmer.stem_text(text)

    out = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout
    for r in results:
        if args.trace:
            print(f"{r.input}\t{r.stem}\t{r.confidence:.2f}\t{r.trace}", file=out)
        else:
            print(f"{r.input}\t{r.stem}", file=out)
    if args.out:
        out.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
