# make_qrels.py
"""Interactive relevance judging, pooled over both runs.

Why pooling matters. The first version of this script drew its candidates from
the UNSTEMMED index alone and asked you to judge those. A document that only
the stemmed index retrieves would then never have been shown, never judged,
and counted as irrelevant -- so the experiment would have been scored on a
pool built to favour the system being compared against. The standard remedy is
to pool: take the top POOL_PER_RUN from each run, judge the union, and shuffle
it so that you cannot tell which run produced a document.

Judgements are saved after every answer, so stopping with 'q' loses nothing.
"""
import os
import random
import sys

from config import QRELS_FILE, POOL_PER_RUN, OUTPUT_DIR
from data_loader import load_corpus, load_queries
from index import (build_unstemmed_index, build_stemmed_index, stem_query,
                   retrieve)

SNIPPET_LEN = 240
SEED = 20261010          # fixed, so the presentation order is reproducible

# Most Linux terminals do no bidirectional reordering and no Arabic shaping, so
# Pashto comes out unjoined and in the wrong direction. Reshaping converts the
# text to visual order with the right contextual forms, which such a terminal
# then displays correctly. Set PASHTO_RESHAPE=1 to turn it on; leave it off in
# anything that already handles BiDi, or the text is reversed twice.
RESHAPE = os.environ.get("PASHTO_RESHAPE") == "1"
if RESHAPE:
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
    except ImportError:
        raise SystemExit("PASHTO_RESHAPE=1 needs: pip install arabic-reshaper "
                         "python-bidi")


def show(text):
    """Pashto as the terminal can actually render it."""
    if not RESHAPE:
        return text
    return get_display(arabic_reshaper.reshape(text))


def judge_file(judge):
    """Each judge writes their own file; merge_qrels.py combines them.

    Two people judging into one file would overwrite each other, and the
    agreement between them -- which the paper should report -- would be
    impossible to compute after the fact.
    """
    if not judge:
        return QRELS_FILE
    return os.path.join(OUTPUT_DIR, f"qrels_{judge}.tsv")


def load_existing(path):
    """Judgements already made, so a second session continues where it left."""
    qrels = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                qid, docid, rel = line.rstrip("\n").split("\t")
                qrels.setdefault(qid, {})[docid] = int(rel)
    return qrels


def save(qrels, path):
    with open(path, "w", encoding="utf-8") as fh:
        for qid in sorted(qrels):
            for docid, rel in sorted(qrels[qid].items()):
                fh.write(f"{qid}\t{docid}\t{rel}\n")


def main():
    judge = sys.argv[1] if len(sys.argv) > 1 else ""
    if not judge:
        print("usage: python make_qrels.py <your-name>\n"
              "       e.g. python make_qrels.py khairullah")
        return 1
    out = judge_file(judge)
    print(f"Judging as {judge!r}; answers go to {out}")

    docs = load_corpus()
    queries = load_queries()
    qrels = load_existing(out)
    judged = sum(len(v) for v in qrels.values())
    if judged:
        print(f"{judged} judgements already on file; continuing.")

    print("\nBuilding both indexes, so the pool is drawn from both runs...")
    docids, bm25_u, _ = build_unstemmed_index(docs)
    _, bm25_s, _ = build_stemmed_index(docs)

    rng = random.Random(SEED)
    for qid, qtext in queries.items():
        pool_u = retrieve(bm25_u, docids, stem_query(qtext, False), POOL_PER_RUN)
        pool_s = retrieve(bm25_s, docids, stem_query(qtext, True), POOL_PER_RUN)
        pool = list(dict.fromkeys(pool_u + pool_s))
        rng.shuffle(pool)                      # judge blind to the source run

        todo = [d for d in pool if d not in qrels.get(qid, {})]
        print("\n" + "=" * 72)
        print(f"Query {qid}: {show(qtext)}")
        print(f"{len(pool)} pooled ({len(pool_u)} unstemmed + {len(pool_s)} "
              f"stemmed, {len(pool_u) + len(pool_s) - len(pool)} shared), "
              f"{len(todo)} left to judge")
        print("=" * 72)

        for n, docid in enumerate(todo, 1):
            snippet = " ".join(docs[docid][:SNIPPET_LEN].split())
            print(f"\n[{n}/{len(todo)}] {docid}\n    {show(snippet)}...")
            while True:
                ans = input("    Relevant? [y/n/s=skip/q=quit] ").strip().lower()
                if ans in ("y", "yes"):
                    qrels.setdefault(qid, {})[docid] = 1
                elif ans in ("n", "no"):
                    qrels.setdefault(qid, {})[docid] = 0
                elif ans in ("s", "skip"):
                    pass
                elif ans in ("q", "quit"):
                    save(qrels, out)
                    print(f"\nStopped. {sum(len(v) for v in qrels.values())} "
                          f"judgements in {out}")
                    return 0
                else:
                    continue
                break
            save(qrels, out)

    save(qrels, out)
    rel = sum(1 for v in qrels.values() for r in v.values() if r)
    print(f"\nAll queries judged: {sum(len(v) for v in qrels.values())} "
          f"judgements, {rel} relevant.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
