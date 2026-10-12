# run_experiment.py
import json
from config import OUTPUT_DIR, EVAL_K
from data_loader import load_corpus, load_queries, load_qrels
from index import (build_unstemmed_index, build_stemmed_index, stem_query,
                   retrieve)
from metrics import evaluate_run


def main():
    docs    = load_corpus()
    queries = load_queries()
    qrels   = load_qrels()

    # ---- Build indexes ----
    print("\n=== Building unstemmed index ===")
    docids_u, bm25_u, _ = build_unstemmed_index(docs)

    print("\n=== Building stemmed index ===")
    docids_s, bm25_s, _ = build_stemmed_index(docs)

    # ---- Run queries ----
    run_unstemmed = {}
    run_stemmed   = {}

    print("\n=== Retrieving (unstemmed) ===")
    for qid, qtext in queries.items():
        toks = stem_query(qtext, apply_stemmer=False)
        run_unstemmed[qid] = retrieve(bm25_u, docids_u, toks)

    print("\n=== Retrieving (stemmed) ===")
    for qid, qtext in queries.items():
        toks = stem_query(qtext, apply_stemmer=True)
        run_stemmed[qid] = retrieve(bm25_s, docids_s, toks)

    # ---- Evaluate ----
    print("\n=== Results ===")
    results = {}
    results["Unstemmed"] = evaluate_run(run_unstemmed, qrels, k=EVAL_K)
    results["Stemmed"]   = evaluate_run(run_stemmed,   qrels, k=EVAL_K)

    # ---- Print table ----
    print(f"\n{'Index':<14}{'MAP':>10}{'nDCG@10':>12}{'P@10':>10}{'Recall@10':>12}")
    print("-" * 58)
    for name, m in results.items():
        print(f"{name:<14}{m['MAP']:>10.4f}{m['nDCG@10']:>12.4f}"
              f"{m['P@10']:>10.4f}{m['Recall@10']:>12.4f}")

    # ---- Save ----
    with open(f"{OUTPUT_DIR}/results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    with open(f"{OUTPUT_DIR}/run_unstemmed.txt", "w", encoding="utf-8") as f:
        for qid, ranked in run_unstemmed.items():
            for i, d in enumerate(ranked, 1):
                f.write(f"{qid}\tQ0\t{d}\t{i}\n")

    with open(f"{OUTPUT_DIR}/run_stemmed.txt", "w", encoding="utf-8") as f:
        for qid, ranked in run_stemmed.items():
            for i, d in enumerate(ranked, 1):
                f.write(f"{qid}\tQ0\t{d}\t{i}\n")

    print(f"\nSaved results to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()