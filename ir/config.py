# config.py
import os

# ---- paths -----------------------------------------------------------------
# Anchored to this file's directory, not to the working directory, so that the
# scripts behave the same whether they are run from inside ir/ or from the
# repository root. They used to be plain relative paths, which worked only
# while ir/ was the working directory and failed with a bare "corpus/ not
# found" once ir/ became a subdirectory of the repository.
HERE = os.path.dirname(os.path.abspath(__file__))

# One document per .txt file; the filename without .txt is the docid.
CORPUS_DIR   = os.path.join(HERE, "corpus")
QUERIES_FILE = os.path.join(HERE, "data", "queries.tsv")   # qid <TAB> text
QRELS_FILE   = os.path.join(HERE, "data", "qrels.tsv")     # qid <TAB> docid <TAB> 0|1
OUTPUT_DIR   = os.path.join(HERE, "results")  # runs, judgements and results

# OUTPUT_DIR must not be CORPUS_DIR. It used to be "output", which was also
# where the split documents lived, so run_unstemmed.txt and run_stemmed.txt
# were written into the corpus and would have been read back as two extra
# documents on the next run.

# ---- the stemmer -----------------------------------------------------------
# The package is imported from the surrounding checkout rather than from an
# installed copy, so that the IR numbers describe exactly the code the paper
# reports. ir/ lives inside the repository, so the repository root is this
# file's parent directory; an installed pashto-stemmer of a different version
# cannot be picked up by accident.
STEMMER_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- retrieval -------------------------------------------------------------
TOP_K       = 1000     # depth retrieved
EVAL_K      = 10       # depth scored: P@10, nDCG@10, Recall@10
POOL_PER_RUN = 25      # candidates taken from each run when building qrels

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(QUERIES_FILE) or ".", exist_ok=True)
