# coding: utf-8
"""Every check the evaluation has to pass before a number is reported.

    python verify_integrity.py

The checks exist because each one corresponds to a mistake that was actually
made during this evaluation and would have produced a publishable-looking but
wrong result. The worst was check 10: `from pashto_stemmer import stem` raised
ImportError, the code fell back to an identity function, and both arms of the
experiment became the same system while still printing a difference.

Exit status is 0 only if every check passes.
"""
import hashlib
import os
import sys

sys.path.insert(0, ".")
from config import (CORPUS_DIR, EVAL_K, HERE, OUTPUT_DIR, POOL_PER_RUN,
                    QRELS_FILE, STEMMER_PATH, TOP_K)
from data_loader import load_corpus, load_qrels, load_queries
from tokenizer import tokenize

sys.path.insert(0, STEMMER_PATH)

PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(f"  {'pass' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))


def main():
    docs = load_corpus()
    queries = load_queries()
    qrels = load_qrels()
    print()

    # 1 -- every judged query is a query we actually have text for
    missing = sorted(set(qrels) - set(queries))
    check("1  every judged query has query text", not missing, f"missing {missing}")

    # 2 -- the query lock: a qid must never have been reused for other text
    lock = os.path.join(HERE, "data", "queries.lock.tsv")
    drift = []
    if os.path.exists(lock):
        with open(lock, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip() or line.startswith("#"):
                    continue
                qid, text = line.rstrip("\n").split("\t")[:2]
                if qid in queries and queries[qid] != text:
                    drift.append(qid)
    check("2  no query id was reused for different text", not drift, f"drifted {drift}")

    # 3 -- every judged document is a document in the corpus
    ghosts = sorted({d for v in qrels.values() for d in v} - set(docs))
    check("3  every judged docid exists in the corpus", not ghosts,
          f"{len(ghosts)} unknown, e.g. {ghosts[:3]}")

    # 4 -- grades are binary; nothing half-judged slipped in
    bad = sorted({r for v in qrels.values() for r in v.values()} - {0, 1})
    check("4  every grade is 0 or 1", not bad, f"saw {bad}")

    # 5 -- no query is all-zero: a query with no relevant document
    #      contributes an undefined average precision
    empty = sorted(q for q, v in qrels.items() if not any(v.values()))
    check("5  every query has at least one relevant document", not empty, f"empty {empty}")

    # 6 -- no duplicate (query, document) rows, which would double-weight a doc
    dupes = []
    with open(QRELS_FILE, encoding="utf-8") as fh:
        seen = set()
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 3:
                continue
            if (p[0], p[1]) in seen:
                dupes.append((p[0], p[1]))
            seen.add((p[0], p[1]))
    check("6  no duplicate query-document rows", not dupes, f"{len(dupes)} duplicates")

    # 7 -- the judgement archive still describes these documents. The archive
    #      stores a hash of the text shown to the judge, so a corpus edit after
    #      judging cannot silently invalidate a label.
    # The archive stores content_id = sha1(document text)[:16], written at the
    # moment the judge saw the text, so this compares the label against the
    # document it was actually made on.
    frozen = os.path.join(OUTPUT_DIR, "frozen")
    arch = [os.path.join(OUTPUT_DIR, f) for f in os.listdir(OUTPUT_DIR)
            if f.startswith("judged_") and f.endswith(".tsv")]
    arch += [os.path.join(frozen, f) for f in os.listdir(frozen)
             if ".judged." in f and f.endswith(".tsv")]
    stale, checked, nohash = [], 0, []
    for a in arch:
        with open(a, encoding="utf-8") as fh:
            head = fh.readline().rstrip("\n").split("\t")
            if "content_id" not in head or "docid" not in head:
                nohash.append(a)
                continue
            hi, di = head.index("content_id"), head.index("docid")
            for line in fh:
                row = line.rstrip("\n").split("\t")
                if len(row) <= max(hi, di) or not row[hi] or row[di] not in docs:
                    continue
                checked += 1
                if hashlib.sha1(docs[row[di]].encode("utf-8")).hexdigest()[:16] != row[hi]:
                    stale.append((os.path.basename(a), row[di]))
    check("7  archived judgements match current document text",
          not stale and checked > 0 and not nohash,
          f"{len(stale)} of {checked:,} rows drifted across {len(arch)} archives"
          + (f"; no content_id in {nohash}" if nohash else ""))

    # 8 -- the pool is deep enough that EVAL_K is fully judged for both runs
    check("8  pool depth covers the evaluation depth", POOL_PER_RUN >= EVAL_K,
          f"pool {POOL_PER_RUN} per run vs eval depth {EVAL_K}")
    check("9  retrieval depth exceeds the pool", TOP_K > POOL_PER_RUN,
          f"top-k {TOP_K} vs pool {POOL_PER_RUN}")

    # 10 -- THE IMPORTANT ONE. The stemmer must import and must not be identity.
    try:
        from pashto_stemmer.stemmer import PashtoStemmer
        st = PashtoStemmer()
        probe = ["کورونه", "خبرونه", "ښوونځیو", "لیکوال", "پوهنتونه"]
        moved = [w for w in probe if st.stem(w) != w]
        check("10 the stemmer imports and actually changes words", len(moved) >= 3,
              f"{len(moved)}/{len(probe)} probe words changed")
    except Exception as exc:
        check("10 the stemmer imports and actually changes words", False, repr(exc))
        st = None

    # 11 -- the two index vocabularies must genuinely differ
    if st is not None:
        sample = list(docs)[:2000]
        plain, stemmed = set(), set()
        for d in sample:
            t = tokenize(docs[d])
            plain.update(t)
            stemmed.update(st.stem(x) for x in t)
        shrink = 1 - len(stemmed) / max(1, len(plain))
        check("11 stemming conflates the vocabulary", 0.05 < shrink < 0.95,
              f"{len(plain):,} -> {len(stemmed):,} types ({shrink:.1%} fewer)")

    # 12 -- the tokenizer is the project normalizer, not an ad-hoc split
    src = open(os.path.join(HERE, "tokenizer.py"), encoding="utf-8").read()
    check("12 the tokenizer uses the project Normalizer",
          "Normalizer" in src and "import" in src)

    print(f"\n{len(PASS)}/{len(PASS) + len(FAIL)} checks pass")
    if FAIL:
        print("failed: " + ", ".join(FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
