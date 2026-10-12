# data_loader.py
import os
import csv
from config import CORPUS_DIR, QUERIES_FILE, QRELS_FILE, OUTPUT_DIR

def load_corpus(limit=None):
    """Read every .txt in CORPUS_DIR. Filename without .txt is the docid.

    limit reads only the first N documents, which is how to try the pipeline
    end to end before committing to all 40,091.
    """
    if not os.path.isdir(CORPUS_DIR):
        raise SystemExit(
            f"{CORPUS_DIR}/ not found. It must hold one .txt per document, "
            f"the filename without .txt being the docid.")
    docs = {}
    for fname in sorted(os.listdir(CORPUS_DIR)):
        if not fname.endswith(".txt"):
            continue
        with open(os.path.join(CORPUS_DIR, fname), encoding="utf-8") as f:
            docs[fname[:-4]] = f.read().strip()
        if limit and len(docs) >= limit:
            break
    print(f"Loaded {len(docs)} documents.")
    return docs


def load_queries():
    """Read queries.tsv: qid <TAB> query text"""
    if not os.path.exists(QUERIES_FILE):
        raise SystemExit(
            f"{QUERIES_FILE} not found. One query per line:\n"
            f"  q01<TAB>د بلوچستان امنیتي وضعیت\n"
            f"  q02<TAB>د پوهنتون زده کوونکي")
    queries = {}
    with open(QUERIES_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            qid, text = line.split("\t", 1)
            queries[qid] = text.strip()
    _check_lock(queries)
    print(f"Loaded {len(queries)} queries.")
    return queries


def _check_lock(queries):
    """Refuse to run if a query id now names different text.

    A qrels file is keyed by id alone. If an id is reused for another query,
    every judgement under it becomes an answer to a question nobody asked --
    and nothing in the scoring would notice. select_queries.py writes the lock;
    this is what makes it worth writing.
    """
    lock = os.path.join(os.path.dirname(QUERIES_FILE) or ".",
                        "queries.lock.tsv")
    if not os.path.exists(lock):
        return
    changed = []
    with open(lock, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            qid, text = line.rstrip("\n").split("\t", 1)
            if qid in queries and queries[qid] != text.strip():
                changed.append((qid, text.strip(), queries[qid]))
    if changed:
        lines = "\n".join(f"  {q}\n     locked as: {was}\n     now reads:  {now}"
                           for q, was, now in changed)
        raise SystemExit(
            f"{len(changed)} query id(s) now name different text than when "
            f"they were judged:\n{lines}\n\n"
            f"Judgements keyed to those ids would be scored against the wrong "
            f"query.\nEither restore the text, or give the new queries fresh "
            f"ids and delete\nthe stale rows from {OUTPUT_DIR}/qrels_*.tsv.")


def load_qrels():
    """Read qrels.tsv: qid <TAB> docid <TAB> 0|1 -- written by make_qrels.py"""
    if not os.path.exists(QRELS_FILE):
        raise SystemExit(
            f"{QRELS_FILE} not found. Build it first: python make_qrels.py")
    qrels = {}
    with open(QRELS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            qid, docid, rel = line.split("\t")
            qrels.setdefault(qid, {})[docid] = int(rel)
    print(f"Loaded qrels for {len(qrels)} queries.")
    return qrels