# -*- coding: utf-8 -*-
"""
files.py
========
Reading and writing the tabular formats people actually have: CSV, TSV and
Excel. The stemmer itself knows nothing about files; this module is the only
place that opens one.

Two rules shape the design.

The caller decides when something is written. `stem_file` with no `out=`
returns the rows and touches nothing on disk, so you can look at the result
before committing to it.

Nothing is overwritten. The stems go in a new column beside the original, and
every other column is carried through untouched.
"""
from __future__ import annotations

import csv
import os
import sys
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

EXCEL_EXT = (".xlsx", ".xlsm")
TAB_EXT = (".tsv", ".tab")


def _delimiter(path: str) -> str:
    return "\t" if os.path.splitext(path)[1].lower() in TAB_EXT else ","


def _is_excel(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in EXCEL_EXT


def _open_workbook(path, load_workbook):
    """Open an .xlsx, or say plainly that the file is not one.

    A CSV renamed to .xlsx is a common mistake, and openpyxl reports it as
    "BadZipFile: File is not a zip file" -- an .xlsx *is* a zip archive, but
    that message tells the user nothing about what to do.
    """
    try:
        return load_workbook(path, data_only=True, read_only=True)
    except Exception as exc:
        kind = type(exc).__name__
        if kind not in ("BadZipFile", "InvalidFileException", "KeyError"):
            raise
        looks_like_text = False
        try:
            with open(path, "rb") as fh:
                head = fh.read(4)
            looks_like_text = not head.startswith(b"PK")
        except OSError:
            pass
        hint = ("It looks like plain text, not a workbook -- if it is really a "
                "CSV or TSV, give it that extension and it will be read."
                if looks_like_text else
                "The file is corrupt or is an old .xls, which openpyxl cannot "
                "read; re-save it as .xlsx.")
        raise SystemExit(f"{path}: not a readable Excel workbook. {hint}")


def read_rows(path: str, sheet: Optional[str] = None
              ) -> Tuple[List[str], List[Dict[str, str]]]:
    """Read a whole table into memory. Returns (column names, rows)."""
    if _is_excel(path):
        try:
            from openpyxl import load_workbook
        except ImportError:                                   # pragma: no cover
            raise SystemExit("reading .xlsx needs openpyxl: pip install openpyxl")
        wb = _open_workbook(path, load_workbook)
        if sheet is not None and sheet not in wb.sheetnames:
            wb.close()
            raise SystemExit(
                f"{path}: no worksheet named {sheet!r}. "
                f"This file has: {', '.join(wb.sheetnames)}")
        ws = wb[sheet] if sheet else wb[wb.sheetnames[0]]
        it = ws.iter_rows(values_only=True)
        header = ["" if c is None else str(c) for c in next(it, ())]
        rows = [dict(zip(header, ["" if c is None else str(c) for c in r]))
                for r in it]
        wb.close()
        return header, rows

    # utf-8-sig, not utf-8: a CSV saved from Excel begins with a byte-order
    # mark, and without this the first column comes back named "﻿word".
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=_delimiter(path))
        return list(reader.fieldnames or []), list(reader)


def iter_rows(path: str) -> Iterator[Dict[str, str]]:
    """Stream a delimited file one row at a time, for files too large to hold."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh, delimiter=_delimiter(path)):
            yield row


def read_header(path: str) -> List[str]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return next(csv.reader(fh, delimiter=_delimiter(path)), [])


def write_rows(path: str, fieldnames: Sequence[str],
               rows: Sequence[Dict[str, str]]) -> None:
    """Write a table, choosing the format from the extension."""
    if _is_excel(path):
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.append(list(fieldnames))
        for r in rows:
            ws.append([r.get(k, "") for k in fieldnames])
        wb.save(path)
        return
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fieldnames),
                           delimiter=_delimiter(path), extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def check_column(path: str, column: str, fieldnames: Sequence[str]) -> None:
    """Fail loudly and usefully rather than writing a file full of blanks."""
    if column not in fieldnames:
        raise KeyError(
            f"{os.path.basename(path)}: no column {column!r}. "
            f"Columns are: {', '.join(fieldnames) or '(none)'}"
        )


def warn_multiword(column: str, values, limit: int = 200) -> None:
    """Say something once if the column holds sentences rather than words.

    A stemmer takes a word. Pointing it at a sentence column still works --
    every token is stemmed separately -- but it is usually a sign the wrong
    column was named, and silence there costs the user a whole run.
    """
    for n, v in enumerate(values):
        if n >= limit:
            break
        if isinstance(v, str) and len(v.split()) > 1:
            print(f"note: column {column!r} holds cells with more than one word, "
                  f"such as {v!r}. Each word in them is stemmed separately, "
                  f"which is right for a text column and wrong if the cell was "
                  f"meant to be a single word.", file=sys.stderr)
            return
