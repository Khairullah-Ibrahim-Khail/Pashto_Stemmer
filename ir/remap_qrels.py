# remap_qrels.py
"""Carry judgements onto a re-split corpus, by content instead of filename.

    python remap_qrels.py classmate

Re-splitting the corpus renumbers every document, so a qrels file keyed by
docid becomes wrong rather than merely stale -- q02/doc37203 would name some
other text entirely, and nothing in the scoring would notice. The archive
written by judge_web.py carries a hash of each judged document, so this script
can find where that text now lives and rewrite the ids.

Judgements whose text is no longer in the corpus are reported and left out.
"""
import csv
import hashlib
import os
import sys

from config import OUTPUT_DIR
from data_loader import load_corpus


def main():
    if len(sys.argv) < 2:
        print("usage: python remap_qrels.py <judge> [<judge> ...]")
        return 1
    docs = load_corpus()
    by_hash = {}
    for docid, text in docs.items():
        by_hash[hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]] = docid
    print(f"{len(by_hash):,} distinct document texts in the current corpus\n")

    for judge in sys.argv[1:]:
        arc = os.path.join(OUTPUT_DIR, f"judged_{judge}.tsv")
        if not os.path.exists(arc):
            print(f"{arc} not found. Run: python archive_judged.py {judge}")
            continue
        same = moved = lost = 0
        out_rows = []
        with open(arc, encoding="utf-8") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                cid, old = row["content_id"], row["docid"]
                new = by_hash.get(cid)
                if new is None:
                    lost += 1
                    continue
                if new == old:
                    same += 1
                else:
                    moved += 1
                out_rows.append((row["qid"], new, row["relevance"]))

        qrels = os.path.join(OUTPUT_DIR, f"qrels_{judge}.tsv")
        if moved:
            backup = qrels + ".before-remap"
            if os.path.exists(qrels):
                os.replace(qrels, backup)
                print(f"  previous file kept as {backup}")
            with open(qrels, "w", encoding="utf-8") as fh:
                for qid, docid, rel in sorted(out_rows):
                    fh.write(f"{qid}\t{docid}\t{rel}\n")
        print(f"{judge}: {same} unchanged, {moved} re-mapped to a new id, "
              f"{lost} no longer in the corpus")
        if lost:
            print(f"   those {lost} judgements cannot be used until the "
                  f"documents they describe are back in the corpus")
        if not moved:
            print(f"   nothing to rewrite -- {qrels} is already correct")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
