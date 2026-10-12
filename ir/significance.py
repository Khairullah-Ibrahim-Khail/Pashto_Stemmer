# coding: utf-8
"""The headline table: stemmed against unstemmed, with significance.

    python significance.py

Reports, for each of the four metrics, both arms' means, the paired difference,
a paired t-test, the win/loss count and an exact sign test. The sign test is
reported beside the t-test because per-query average precision is bounded and
skewed, so the t-test's normality assumption is not safe on 39 queries; where
the two tests disagree, the sign test is the one to believe.

For MAP it also reports a bootstrap confidence interval and the number of
queries this effect size would need for 80% power.
"""
import math
import random
import statistics
import sys

sys.path.insert(0, ".")
from config import EVAL_K, STEMMER_PATH, TOP_K
from data_loader import load_corpus, load_qrels, load_queries
from metrics import average_precision, ndcg_at_k, precision_at_k, recall_at_k
from stats_tests import n_for_power, sign_test, t_sf2
from tokenizer import tokenize

sys.path.insert(0, STEMMER_PATH)
from rank_bm25 import BM25Okapi                               # noqa: E402
from pashto_stemmer.stemmer import PashtoStemmer              # noqa: E402

SEED = 20261010
RESAMPLES = 10000
LABEL = {"MAP": "MAP", "nDCG": f"nDCG@{EVAL_K}",
         "P": f"P@{EVAL_K}", "R": f"Recall@{EVAL_K}"}


def main():
    docs, queries, qrels = load_corpus(), load_queries(), load_qrels()
    docids = list(docs)
    st = PashtoStemmer()

    print(f"building two indexes over {len(docids):,} documents...")
    bm_u = BM25Okapi([tokenize(docs[d]) for d in docids])
    bm_s = BM25Okapi([[st.stem(t) for t in tokenize(docs[d])] for d in docids])

    def ranked(bm, tokens):
        sc = bm.get_scores(tokens)
        order = sorted(range(len(sc)), key=lambda i: sc[i], reverse=True)
        return [docids[i] for i in order[:TOP_K]]

    def score(run, rel):
        return dict(MAP=average_precision(run, rel),
                    nDCG=ndcg_at_k(run, rel, EVAL_K),
                    P=precision_at_k(run, rel, EVAL_K),
                    R=recall_at_k(run, rel, EVAL_K))

    per = {}
    for q in sorted(qrels):
        rel = {d for d, g in qrels[q].items() if g > 0}
        tok = tokenize(queries[q])
        per[q] = {"u": score(ranked(bm_u, tok), rel),
                  "s": score(ranked(bm_s, [st.stem(t) for t in tok]), rel)}

    n = len(per)
    judged = sum(len(v) for v in qrels.values())
    relevant = sum(1 for v in qrels.values() for g in v.values() if g > 0)
    print(f"\n{n} queries, {judged:,} judgements, {relevant:,} relevant\n")
    print(f"{'metric':12}{'unstemmed':>11}{'stemmed':>10}{'diff':>10}"
          f"{'t':>7}{'p':>8}{'w/l':>8}{'sign p':>9}")
    print("-" * 75)

    random.seed(SEED)
    notes = []
    for m in ("MAP", "nDCG", "P", "R"):
        d = [per[q]["s"][m] - per[q]["u"][m] for q in per]
        mu = statistics.mean(per[q]["u"][m] for q in per)
        ms = statistics.mean(per[q]["s"][m] for q in per)
        mean, sd = statistics.mean(d), statistics.stdev(d)
        t = mean / (sd / math.sqrt(n))
        w = sum(1 for x in d if x > 0)
        l = sum(1 for x in d if x < 0)
        print(f"{LABEL[m]:12}{mu:>11.4f}{ms:>10.4f}{mean:>+10.4f}"
              f"{t:>7.2f}{t_sf2(t, n - 1):>8.3f}{f'{w}/{l}':>8}"
              f"{sign_test(w, l):>9.3f}")
        if m == "MAP":
            boot = sorted(statistics.mean(random.choices(d, k=n))
                          for _ in range(RESAMPLES))
            notes.append(f"MAP bootstrap 95% CI  [{boot[RESAMPLES // 40]:+.4f}, "
                         f"{boot[RESAMPLES - RESAMPLES // 40]:+.4f}]  "
                         f"({RESAMPLES:,} resamples, seed {SEED})")
            dz = mean / sd
            need = n_for_power(dz)
            notes.append(f"Cohen's d {dz:.3f}; {need} queries needed for 80% "
                         f"power at alpha .05, and this collection has {n}")

    print()
    for note in notes:
        print("  " + note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
