# merge_qrels.py
"""Combine the judges' files into the single qrels the experiment scores on.

    python merge_qrels.py khairullah classmate

Where both judged the same document and agree, that is the label. Where they
disagree, the document is written to results/disagreements.tsv and LEFT OUT of
the merged file -- a coin-flip label is worse than no label. Settle those
together, re-judge them, and merge again.
"""
import os
import sys

from config import OUTPUT_DIR, QRELS_FILE
from judge_agreement import load


def main():
    if len(sys.argv) < 2:
        print("usage: python merge_qrels.py <judge> [<judge> ...]")
        return 1
    judges = sys.argv[1:]
    seen = {}
    for j in judges:
        for key, rel in load(j).items():
            seen.setdefault(key, {})[j] = rel

    merged, conflict = {}, []
    for (qid, docid), votes in seen.items():
        vals = set(votes.values())
        if len(vals) == 1:
            merged.setdefault(qid, {})[docid] = vals.pop()
        else:
            conflict.append((qid, docid, votes))

    with open(QRELS_FILE, "w", encoding="utf-8") as fh:
        for qid in sorted(merged):
            for docid, rel in sorted(merged[qid].items()):
                fh.write(f"{qid}\t{docid}\t{rel}\n")

    path = os.path.join(OUTPUT_DIR, "disagreements.tsv")
    with open(path, "w", encoding="utf-8") as fh:
        for qid, docid, votes in sorted(conflict):
            fh.write(f"{qid}\t{docid}\t" +
                     "\t".join(f"{j}={v}" for j, v in sorted(votes.items())) + "\n")

    rel = sum(1 for v in merged.values() for r in v.values() if r)
    total = sum(len(v) for v in merged.values())
    print(f"{total} agreed judgements over {len(merged)} queries "
          f"({rel} relevant) -> {QRELS_FILE}")
    print(f"{len(conflict)} disagreements left out -> {path}")
    if conflict:
        print("Settle those together and re-run, or the queries they belong to "
              "will be scored on an incomplete pool.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
