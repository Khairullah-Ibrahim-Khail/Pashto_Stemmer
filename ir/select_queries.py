# select_queries.py
"""Draw the judged sample from the full query pool, reproducibly and safely.

    python select_queries.py data/queries_all.tsv 50

Random, not hand-picked, with a fixed seed, so the choice can be audited.
Choosing queries after seeing which ones the stemmer handles well is how an
experiment gets fixed without anyone intending it; this removes the chance.

It will not destroy judging already done. A qrels file is keyed by query id,
so if an id were reused for a different query the existing judgements would
silently become wrong answers to a question nobody asked. So this script:

  * keeps every query that already has judgements, with its id and its text,
    and counts it towards the sample;
  * numbers the newly drawn queries so they cannot collide with those ids;
  * backs up queries.tsv and every qrels file before writing;
  * records the id -> text mapping in data/queries.lock.tsv, which
    data_loader checks on every run, so a mismatch is reported rather than
    silently scored.
"""
import glob
import os
import random
import shutil
import sys
import time

from config import QUERIES_FILE, OUTPUT_DIR, STEMMER_PATH
from tokenizer import tokenize

SEED = 20261010
LOCK_FILE = os.path.join(os.path.dirname(QUERIES_FILE) or ".",
                         "queries.lock.tsv")

sys.path.insert(0, STEMMER_PATH)
from pashto_stemmer import PashtoStemmer                   # noqa: E402


def read_tsv_pairs(path, auto_id=False):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8-sig") as fh:
        for n, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) > 1:
                rows.append((parts[0].strip(), parts[1].strip()))
            elif auto_id:
                rows.append((f"q{n:03d}", parts[0].strip()))
    return rows


def judged_qids():
    """Query ids that already carry judgements, from every judge's file."""
    qids = set()
    for path in sorted(glob.glob(os.path.join(OUTPUT_DIR, "qrels_*.tsv"))):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    qids.add(line.split("\t")[0])
    return qids


def back_up():
    stamp = time.strftime("%Y%m%d-%H%M%S")
    folder = os.path.join(OUTPUT_DIR, f"backup-{stamp}")
    made = []
    for path in [QUERIES_FILE, LOCK_FILE] + sorted(
            glob.glob(os.path.join(OUTPUT_DIR, "qrels_*.tsv"))):
        if os.path.exists(path):
            os.makedirs(folder, exist_ok=True)
            shutil.copy2(path, os.path.join(folder, os.path.basename(path)))
            made.append(os.path.basename(path))
    if made:
        print(f"backed up {', '.join(made)} -> {folder}/")
    return folder


def next_free_prefix(used):
    """A numbering block no existing id can fall into."""
    for start in (1, 101, 201, 301, 401, 501):
        block = {f"q{n:03d}" for n in range(start, start + 500)}
        if not (block & used):
            return start
    return 1001


def main():
    if len(sys.argv) < 2:
        print("usage: python select_queries.py <pool.tsv> [how-many]")
        return 1
    pool_path, want = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 50
    pool = read_tsv_pairs(pool_path, auto_id=True)
    if not pool:
        print(f"{pool_path} holds no queries. One per line:\n"
              f"  q01<TAB>د بلوچستان سیاسي وضعیت")
        return 1

    current = dict(read_tsv_pairs(QUERIES_FILE))
    keep_ids = judged_qids() & set(current)
    keep = [(q, current[q]) for q in sorted(keep_ids)]

    if keep:
        print(f"{len(keep)} query(ies) already judged -- keeping id and text, "
              f"and counting them towards the {want}:")
        for q, t in keep:
            print(f"   {q}  {t}")

    orphan = judged_qids() - set(current)
    if orphan:
        print(f"\nWARNING: judgements exist for {sorted(orphan)}, which are "
              f"not in {QUERIES_FILE}.\nTheir text is unknown, so they cannot "
              f"be carried forward and will be ignored.")

    back_up()

    # Draw the remainder, skipping any pool query whose text is already kept.
    kept_text = {t for _, t in keep}
    rng = random.Random(SEED)
    order = [(q, t) for q, t in pool if t not in kept_text]
    rng.shuffle(order)
    need = max(0, want - len(keep))
    drawn, rest = order[:need], order[need:]

    start = next_free_prefix(set(current) | judged_qids())
    chosen = list(keep) + [(f"q{start + i:03d}", t)
                           for i, (_, t) in enumerate(drawn)]

    st = PashtoStemmer()

    def affixed(text):
        toks = tokenize(text)
        return sum(1 for t in toks if st.stem(t) != t), len(toks)

    with open(QUERIES_FILE, "w", encoding="utf-8") as fh:
        for qid, text in chosen:
            fh.write(f"{qid}\t{text}\n")
    with open(LOCK_FILE, "w", encoding="utf-8") as fh:
        fh.write("# id -> text, checked by data_loader. Do not edit by hand:\n"
                 "# if an id here ever names different text, judgements keyed\n"
                 "# to it are answers to a different question.\n")
        for qid, text in chosen:
            fh.write(f"{qid}\t{text}\n")
    held = os.path.splitext(pool_path)[0] + "_heldout.tsv"
    with open(held, "w", encoding="utf-8") as fh:
        for qid, text in rest:
            fh.write(f"{qid}\t{text}\n")

    ch = [affixed(t) for _, t in chosen]
    a, n = sum(x for x, _ in ch), sum(y for _, y in ch)
    none = sum(1 for x, _ in ch if x == 0)
    print(f"\npool {len(pool)}  ->  {len(chosen)} queries "
          f"({len(keep)} kept, {len(drawn)} newly drawn, seed {SEED}), "
          f"{len(rest)} held out")
    print(f"  queries  {QUERIES_FILE}")
    print(f"  lock     {LOCK_FILE}")
    print(f"  held out {held}")
    if drawn:
        print(f"  new ids  q{start:03d} .. q{start + len(drawn) - 1:03d} "
              f"(chosen to avoid {sorted(set(current) | judged_qids())})")
    print(f"\n  {n} query words, {a} ({a / n:.0%}) are changed by the stemmer")
    print(f"  {none} of {len(chosen)} queries contain no word the stemmer "
          f"touches")
    print("\n  If nearly every word is affixed the comparison is easy by "
          "accident.\n  A mix is what makes the result mean something.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
