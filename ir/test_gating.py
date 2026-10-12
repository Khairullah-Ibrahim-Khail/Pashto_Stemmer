# coding: utf-8
"""What each gating decision is worth in retrieval.

    python test_gating.py

Two suffixes were tested the same way and got opposite answers, so both arms
are kept here rather than only the one that justified a change:

    released      the shipped stemmer: ‑تون gated, ‑ستان stripped
    ‑تون live     ungate the place suffix, i.e. strip it as the grammar says
    ‑ستان gated   also refuse the ‑ستان strip
    both changed  ‑تون live and ‑ستان gated

The same judgements score every arm. A relevance judgement says whether a
document answers a query, which does not depend on which stemmer retrieved it,
so nothing has to be re-judged when the stemmer changes.
"""
import math
import statistics
import sys

sys.path.insert(0, ".")
from config import EVAL_K, STEMMER_PATH, TOP_K
from data_loader import load_corpus, load_qrels, load_queries
from metrics import average_precision, ndcg_at_k, precision_at_k, recall_at_k
from stats_tests import sign_test, t_sf2
from tokenizer import tokenize

sys.path.insert(0, STEMMER_PATH)
from rank_bm25 import BM25Okapi                                # noqa: E402
from pashto_stemmer.stemmer import PashtoStemmer, StemmerConfig  # noqa: E402
from pashto_stemmer.suffixes import SUFFIX_RULES                # noqa: E402

# The stacked forms the released config no longer lists, restored when the
# place suffix is put back so that روغتونونو comes apart the way it used to.
TUN_STACKED = ("تونونو", "تونونه")


def build(stemmer, docs, docids):
    if stemmer is None:
        toks = [tokenize(docs[d]) for d in docids]
    else:
        toks = [[stemmer.stem(t) for t in tokenize(docs[d])] for d in docids]
    return BM25Okapi(toks)


def tun_live(**extra):
    """A stemmer with the place suffix stripped again, as the grammar says."""
    rule = next(r for r in SUFFIX_RULES if r.affix == "تون")
    object.__setattr__(rule, "strip_allowed", "yes")
    base = StemmerConfig()
    uni = TUN_STACKED + tuple(base.uniform_strip) + ("تون",)
    st = PashtoStemmer(StemmerConfig(uniform_strip=uni, **extra))
    object.__setattr__(rule, "strip_allowed", "no")   # leave the module as found
    return st


def main():
    docs, queries, qrels = load_corpus(), load_queries(), load_qrels()
    docids = list(docs)

    print(f"building five indexes over {len(docids):,} documents...")
    released = PashtoStemmer()
    arms = [
        ("unstemmed", "no stemming", None),
        ("released", "released (‑تون gated)", released),
        ("tun", "‑تون live (grammar)", tun_live()),
        ("stan", "‑ستان gated too", PashtoStemmer(StemmerConfig(strip_stan=False))),
        ("both", "‑تون live, ‑ستان gated", tun_live(strip_stan=False)),
    ]
    index = {k: build(st, docs, docids) for k, _, st in arms}
    stem = {k: st for k, _, st in arms}

    def ranked(k, q):
        tok = tokenize(queries[q])
        if stem[k] is not None:
            tok = [stem[k].stem(t) for t in tok]
        sc = index[k].get_scores(tok)
        order = sorted(range(len(sc)), key=lambda i: sc[i], reverse=True)
        return [docids[i] for i in order[:TOP_K]]

    per = {}
    for q in sorted(qrels):
        rel = {d for d, g in qrels[q].items() if g > 0}
        per[q] = {k: dict(MAP=average_precision(r, rel),
                          nDCG=ndcg_at_k(r, rel, EVAL_K),
                          P=precision_at_k(r, rel, EVAL_K),
                          R=recall_at_k(r, rel, EVAL_K))
                  for k, r in ((k, ranked(k, q)) for k, _, _ in arms)}

    n = len(per)
    print(f"\n{n} queries, {sum(len(v) for v in qrels.values()):,} judgements\n")
    print(f"{'system':26}{'MAP':>9}{'nDCG@10':>10}{'P@10':>9}{'Recall@10':>11}")
    print("-" * 65)
    for k, label, _ in arms:
        print(f"{label:26}" + "".join(
            f"{statistics.mean(per[q][k][m] for q in per):>{w}.4f}"
            for m, w in (("MAP", 9), ("nDCG", 10), ("P", 9), ("R", 11))))

    print(f"\n{'comparison':34}{'MAP':>9}{'t':>7}{'p':>8}{'w/l':>8}{'sign p':>9}")
    print("-" * 75)
    for a, b, label in (("unstemmed", "released", "released vs no stemming"),
                        ("unstemmed", "tun", "‑تون live vs no stemming"),
                        ("released", "tun", "‑تون live vs released"),
                        ("released", "stan", "‑ستان gated vs released"),
                        ("released", "both", "both changed vs released")):
        d = [per[q][b]["MAP"] - per[q][a]["MAP"] for q in per]
        mean, sd = statistics.mean(d), statistics.stdev(d)
        t = mean / (sd / math.sqrt(n)) if sd else 0.0
        w = sum(1 for x in d if x > 0)
        l = sum(1 for x in d if x < 0)
        print(f"{label:34}{mean:>+9.4f}{t:>7.2f}{t_sf2(t, n - 1):>8.3f}"
              f"{f'{w}/{l}':>8}{sign_test(w, l):>9.3f}")

    print("\n  the queries the released stemmer loses most against no stemming:")
    order = sorted(per, key=lambda q: per[q]["released"]["MAP"]
                   - per[q]["unstemmed"]["MAP"])[:5]
    print(f"    {'query':7}{'unstem':>9}{'released':>10}{'‑تون live':>11}"
          f"{'‑ستان gated':>13}   text")
    for q in order:
        p_ = per[q]
        print(f"    {q:7}{p_['unstemmed']['MAP']:>9.4f}{p_['released']['MAP']:>10.4f}"
              f"{p_['tun']['MAP']:>11.4f}{p_['stan']['MAP']:>13.4f}   {queries[q]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
