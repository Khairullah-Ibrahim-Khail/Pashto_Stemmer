# archive_judged.py
"""Back-fill the document archive for judgements made before archiving existed.

    python archive_judged.py classmate

Writes results/judged_<judge>.tsv: one row per judgement carrying the query,
the document id, the label, a hash of the document's text and the text itself.
A qrels file alone is keyed by filename, so re-splitting the corpus would make
every judgement unverifiable; this file is what makes them checkable.
"""
import csv
import hashlib
import os
import sys
import time

from config import OUTPUT_DIR
from data_loader import load_corpus, load_queries

ARCHIVE_FIELDS = ["qid", "query", "docid", "relevance", "content_id",
                  "judged_at", "document"]


def main():
    if len(sys.argv) < 2:
        print("usage: python archive_judged.py <judge> [<judge> ...]")
        return 1
    docs = load_corpus()
    queries = load_queries()
    for judge in sys.argv[1:]:
        qrels = os.path.join(OUTPUT_DIR, f"qrels_{judge}.tsv")
        if not os.path.exists(qrels):
            print(f"{qrels} not found -- skipping {judge}")
            continue
        out = os.path.join(OUTPUT_DIR, f"judged_{judge}.tsv")
        rows, missing = [], 0
        stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
        with open(qrels, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                qid, docid, rel = line.rstrip("\n").split("\t")
                text = docs.get(docid)
                if text is None:
                    missing += 1
                    text = ""
                rows.append({
                    "qid": qid, "query": queries.get(qid, ""), "docid": docid,
                    "relevance": rel,
                    "content_id": hashlib.sha1(
                        text.encode("utf-8")).hexdigest()[:16] if text else "",
                    "judged_at": stamp,
                    "document": " ".join(text.split()),
                })
        with open(out, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=ARCHIVE_FIELDS, delimiter="\t")
            w.writeheader()
            w.writerows(rows)
        size = os.path.getsize(out) / 1024
        print(f"{judge}: {len(rows)} judgements archived -> {out} "
              f"({size:.0f} KB)")
        if missing:
            print(f"   {missing} document(s) no longer in the corpus; "
                  f"their text could not be recovered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
