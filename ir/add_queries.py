# coding: utf-8
"""Add a batch of new queries to the collection, safely.

    python add_queries.py data/queries_new11.tsv

Appends the queries in the given file to data/queries.tsv and records them in
data/queries.lock.tsv. Existing queries and every judgement already made are
left exactly as they are: a judgement is keyed by query id and document id, so
adding new ids cannot disturb them.

It refuses to run if a query id in the batch is already in use, or if the same
query text is already present under another id, because either would make the
collection score a question twice. Everything is backed up first.

After this, start the judging tool as usual; the new queries appear with no
judgements and the browser pools them from both runs in the normal way.
"""
import os
import shutil
import sys
import time

from config import QUERIES_FILE

LOCK_FILE = os.path.join(os.path.dirname(QUERIES_FILE) or ".",
                         "queries.lock.tsv")


def read_pairs(path):
    """(id, text) for every non-comment, non-blank line of a TSV."""
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            out.append((parts[0].strip(), parts[1].strip()))
    return out


def main(batch_path):
    if not os.path.exists(batch_path):
        raise SystemExit(f"{batch_path} not found")

    existing = read_pairs(QUERIES_FILE)
    batch = read_pairs(batch_path)
    if not batch:
        raise SystemExit(f"{batch_path} holds no queries")

    by_id = dict(existing)
    by_text = {t: i for i, t in existing}

    clashes = [i for i, _ in batch if i in by_id]
    if clashes:
        raise SystemExit("these ids are already in use, refusing to run: "
                         + ", ".join(clashes))
    repeats = [(i, t) for i, t in batch if t in by_text]
    if repeats:
        raise SystemExit("this text is already a query under another id: "
                         + "; ".join(f"{i} == {by_text[t]}" for i, t in repeats))

    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(os.path.dirname(QUERIES_FILE) or ".",
                          f"backup-{stamp}")
    os.makedirs(backup, exist_ok=True)
    for f in (QUERIES_FILE, LOCK_FILE):
        if os.path.exists(f):
            shutil.copy2(f, os.path.join(backup, os.path.basename(f)))

    with open(QUERIES_FILE, "a", encoding="utf-8") as fh:
        for i, t in batch:
            fh.write(f"{i}\t{t}\n")

    locked = dict(read_pairs(LOCK_FILE)) if os.path.exists(LOCK_FILE) else {}
    with open(LOCK_FILE, "a", encoding="utf-8") as fh:
        for i, t in batch:
            if i not in locked:
                fh.write(f"{i}\t{t}\n")

    print(f"added {len(batch)} queries; the collection now has "
          f"{len(existing) + len(batch)}")
    print(f"backup of the previous files: {backup}/")
    for i, t in batch:
        print(f"   {i}  {t}")
    print("\nnow judge them:")
    print("   python judge_web.py <your-name>")
    print("   open http://127.0.0.1:8000/queries and work through the new ids")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1
                          else "data/queries_new11.tsv"))
