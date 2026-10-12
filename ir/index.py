# index.py
"""Builds the two BM25 indexes and retrieves against them.

The only difference between the two arms is the stemmer. Both share the same
tokenizer and the same normalization, so a difference in the measured scores
can only come from stemming.
"""
import sys

from rank_bm25 import BM25Okapi
from tqdm import tqdm

from config import STEMMER_PATH, TOP_K
from tokenizer import tokenize

if STEMMER_PATH not in sys.path:
    sys.path.insert(0, STEMMER_PATH)

from pashto_stemmer import PashtoStemmer                 # noqa: E402

# One instance, created once: it carries a 500,000-entry result cache, so a
# corpus costs about as much as its vocabulary.
_stemmer = PashtoStemmer()
stem_word = _stemmer.stem


def build_unstemmed_index(docs):
    docids = list(docs.keys())
    tokenized = [tokenize(docs[d])
                 for d in tqdm(docids, desc="tokenizing (unstemmed)")]
    return docids, BM25Okapi(tokenized), tokenized


def build_stemmed_index(docs):
    docids = list(docs.keys())
    tokenized = []
    for d in tqdm(docids, desc="tokenizing + stemming"):
        tokenized.append([stem_word(t) for t in tokenize(docs[d])])
    return docids, BM25Okapi(tokenized), tokenized


def stem_query(query, apply_stemmer):
    tokens = tokenize(query)
    return [stem_word(t) for t in tokens] if apply_stemmer else tokens


def retrieve(bm25, docids, query_tokens, top_k=TOP_K):
    """Ranked docids, best first.

    Defined here rather than in run_experiment, so that make_qrels can import
    the same function the experiment uses -- it used to import it from index
    where it did not exist, and crashed.
    """
    if not query_tokens:
        return []
    scores = bm25.get_scores(query_tokens)
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return [docids[i] for i in order[:top_k]]
