# metrics.py
import math

def precision_at_k(ranked_docids, relevant, k):
    topk = ranked_docids[:k]
    return sum(1 for d in topk if d in relevant) / k


def recall_at_k(ranked_docids, relevant, k):
    if not relevant:
        return 0.0
    topk = ranked_docids[:k]
    return sum(1 for d in topk if d in relevant) / len(relevant)


def average_precision(ranked_docids, relevant):
    if not relevant:
        return 0.0
    hits = 0
    total_precision = 0.0
    for i, d in enumerate(ranked_docids, start=1):
        if d in relevant:
            hits += 1
            total_precision += hits / i
    return total_precision / len(relevant)


def dcg_at_k(ranked_docids, relevant, k):
    dcg = 0.0
    for i, d in enumerate(ranked_docids[:k], start=1):
        rel = 1 if d in relevant else 0
        dcg += rel / math.log2(i + 1)
    return dcg


def ndcg_at_k(ranked_docids, relevant, k):
    dcg = dcg_at_k(ranked_docids, relevant, k)
    # Ideal DCG: all relevant docs at the top
    ideal = sum(1 / math.log2(i + 1) for i in range(1, min(len(relevant), k) + 1))
    return dcg / ideal if ideal > 0 else 0.0


def evaluate_run(run, qrels, k=10):
    """
    run:   {qid: [docid1, docid2, ...]}  (ranked)
    qrels: {qid: {docid: 1 or 0}}
    Returns averaged metrics.
    """
    map_scores, ndcg_scores, p_scores, r_scores = [], [], [], []
    for qid, ranked in run.items():
        if qid not in qrels:
            continue
        relevant = {d for d, r in qrels[qid].items() if r > 0}
        map_scores.append(average_precision(ranked, relevant))
        ndcg_scores.append(ndcg_at_k(ranked, relevant, k))
        p_scores.append(precision_at_k(ranked, relevant, k))
        r_scores.append(recall_at_k(ranked, relevant, k))
    n = len(map_scores)
    return {
        "MAP":    sum(map_scores) / n if n else 0.0,
        "nDCG@10": sum(ndcg_scores) / n if n else 0.0,
        "P@10":   sum(p_scores) / n if n else 0.0,
        "Recall@10": sum(r_scores) / n if n else 0.0,
        "num_queries": n,
    }