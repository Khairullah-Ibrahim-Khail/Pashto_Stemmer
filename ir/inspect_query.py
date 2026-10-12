# inspect_query.py
"""Why one query behaved as it did: the top of each run, with the judgement.

    python inspect_query.py q02

A query where stemming loses is either a real weakness or a judging mistake,
and this is how to tell which. Documents marked NOT RELEVANT that the stemmed
run ranked highly are the ones to re-read: if they are in fact relevant, the
loss is a judging error, not a retrieval one.
"""
import sys

from config import EVAL_K
from data_loader import load_corpus, load_queries, load_qrels
from index import (build_unstemmed_index, build_stemmed_index, stem_query,
                   retrieve)
from metrics import average_precision

SNIP = 150


def main():
    if len(sys.argv) != 2:
        print("usage: python inspect_query.py <qid>")
        return 1
    qid = sys.argv[1]
    docs, queries, qrels = load_corpus(), load_queries(), load_qrels()
    if qid not in queries:
        print(f"{qid} not in {list(queries)}")
        return 1
    qtext = queries[qid]
    judged = qrels.get(qid, {})
    rel = {d for d, r in judged.items() if r > 0}

    docids, bu, _ = build_unstemmed_index(docs)
    _, bs, _ = build_stemmed_index(docs)
    ru = retrieve(bu, docids, stem_query(qtext, False))
    rs = retrieve(bs, docids, stem_query(qtext, True))

    print(f"\n{qid}: {qtext}")
    print(f"query tokens  unstemmed {stem_query(qtext, False)}")
    print(f"              stemmed   {stem_query(qtext, True)}")
    print(f"{len(judged)} judged, {len(rel)} relevant")
    print(f"MAP unstemmed {average_precision(ru, rel):.4f}   "
          f"stemmed {average_precision(rs, rel):.4f}")

    def table(name, ranked):
        print(f"\n  top {EVAL_K}, {name}")
        print(f"  {'#':>2} {'docid':11} {'judged':12}")
        for i, d in enumerate(ranked[:EVAL_K], 1):
            mark = ("RELEVANT" if d in rel
                    else "not relevant" if d in judged else "UNJUDGED")
            print(f"  {i:>2} {d:11} {mark:12} "
                  f"{' '.join(docs[d][:SNIP].split())}...")
    table("unstemmed", ru)
    table("stemmed", rs)

    only_s = [d for d in rs[:EVAL_K] if d not in ru[:EVAL_K]]
    print(f"\n  {len(only_s)} documents only the STEMMED run put in the top "
          f"{EVAL_K}:")
    for d in only_s:
        mark = ("RELEVANT" if d in rel
                else "not relevant" if d in judged else "UNJUDGED")
        print(f"     {d}  {mark}")
    bad = [d for d in only_s if d in judged and d not in rel]
    if bad:
        print(f"\n  RE-READ THESE {len(bad)} -- marked not relevant, and they "
              f"are what cost this query:")
        for d in bad:
            print(f"\n     {d}\n     {' '.join(docs[d][:420].split())}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
