# per_query.py
"""Per-query scores for both arms, and the paired difference.

The averaged table hides how much queries vary. With few queries the average
is dominated by whichever query happens to behave oddly, and this is what
shows that. It is also the input a significance test needs: once there are
~50 queries, the column of differences below is what a paired test runs on.
"""
import sys

from config import EVAL_K
from data_loader import load_corpus, load_queries, load_qrels
from index import (build_unstemmed_index, build_stemmed_index, stem_query,
                   retrieve)
from metrics import average_precision, ndcg_at_k, precision_at_k, recall_at_k


def main():
    docs, queries, qrels = load_corpus(), load_queries(), load_qrels()
    docids, bu, _ = build_unstemmed_index(docs)
    _, bs, _ = build_stemmed_index(docs)

    print(f"\n{'query':6} {'rel':>4} | {'MAP un':>7} {'MAP st':>7} {'diff':>7}"
          f" | {'P@10 un':>8} {'P@10 st':>8} | {'R@10 un':>8} {'R@10 st':>8}")
    print("-" * 78)
    diffs = []
    for qid, qtext in queries.items():
        if qid not in qrels:
            continue
        rel = {d for d, r in qrels[qid].items() if r > 0}
        ru = retrieve(bu, docids, stem_query(qtext, False))
        rs = retrieve(bs, docids, stem_query(qtext, True))
        mu, ms = average_precision(ru, rel), average_precision(rs, rel)
        diffs.append(ms - mu)
        print(f"{qid:6} {len(rel):>4} | {mu:>7.4f} {ms:>7.4f} {ms - mu:>+7.4f}"
              f" | {precision_at_k(ru, rel, EVAL_K):>8.3f}"
              f" {precision_at_k(rs, rel, EVAL_K):>8.3f}"
              f" | {recall_at_k(ru, rel, EVAL_K):>8.3f}"
              f" {recall_at_k(rs, rel, EVAL_K):>8.3f}")

    n = len(diffs)
    mean = sum(diffs) / n
    print("-" * 78)
    print(f"{'mean':6} {'':>4} | {'':>7} {'':>7} {mean:>+7.4f}")
    if n > 1:
        var = sum((d - mean) ** 2 for d in diffs) / (n - 1)
        sd = var ** 0.5
        print(f"\nMAP difference: mean {mean:+.4f}, sd {sd:.4f} over {n} "
              f"queries ({sum(1 for d in diffs if d > 0)} better, "
              f"{sum(1 for d in diffs if d < 0)} worse, "
              f"{sum(1 for d in diffs if d == 0)} tied)")
        if n < 25:
            print(f"\n{n} queries is too few to test. The spread between "
                  f"queries is larger than\nthe effect, so no significance "
                  f"test on this would mean anything. Judge ~50.")
        else:
            t = mean / (sd / n ** 0.5)
            print(f"paired t = {t:.2f} on {n - 1} df")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
