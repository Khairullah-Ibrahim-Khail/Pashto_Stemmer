# conflation_report.py
"""Regenerates every number in CONFLATION_ANALYSIS.md.

    python conflation_report.py

Splits what the stemmer merges into four kinds, so the question "is this an
error or is it Pashto" is answered by measurement rather than by argument:

  A  the same word spelled differently      -- a normalization gain
  B  one documented affix removed           -- normal stemming
  C  a stack of documented affixes          -- normal morphology, deeper
  D  no affix decomposition exists          -- the only genuine errors
"""
import collections
import functools
import sys

sys.path.insert(0, ".")
from config import STEMMER_PATH
from data_loader import load_corpus
from index import stem_word
from tokenizer import tokenize

sys.path.insert(0, STEMMER_PATH)
from pashto_stemmer.prefixes import PREFIX_RULES          # noqa: E402
from pashto_stemmer.suffixes import SUFFIX_RULES          # noqa: E402

FOLD = str.maketrans({"ي": "ی", "ې": "ی", "ۍ": "ی", "ئ": "ی", "ے": "ی"})
fold = lambda s: s.translate(FOLD)                        # noqa: E731
SUF = {fold(r.affix) for r in SUFFIX_RULES}
PRE = {fold(r.affix) for r in PREFIX_RULES}


@functools.lru_cache(maxsize=None)
def decomposes(piece):
    """Is this removed material a stack of documented suffixes?"""
    if piece == "":
        return True
    return any(piece.endswith(a) and decomposes(piece[:len(piece) - len(a)])
               for a in SUF)


def classify(word, stem):
    fw, fs = fold(word), fold(stem)
    if fw == fs:
        return "A"
    if fw.startswith(fs):
        piece = fw[len(fs):]
        return "B" if piece in SUF else "C" if decomposes(piece) else "D"
    if fw.endswith(fs) and fw[:len(fw) - len(fs)] in PRE:
        return "B"
    if fs in fw:
        i = fw.index(fs)
        a, b = fw[:i], fw[i + len(fs):]
        if a in PRE and (b in SUF or decomposes(b)):
            return "C"
    return "D"


def main():
    docs = load_corpus()
    vocab = collections.Counter()
    for text in docs.values():
        vocab.update(tokenize(text))
    groups = collections.defaultdict(set)
    for w in vocab:
        groups[stem_word(w)].add(w)
    multi = {s: ws for s, ws in groups.items() if len(ws) > 1}

    print(f"\n{len(docs):,} documents, {sum(vocab.values()):,} tokens")
    print(f"{len(vocab):,} word types -> {len(groups):,} stems"
          f"   ({1 - len(groups) / len(vocab):.1%} collapse)")
    print(f"{len(multi):,} stems ({len(multi) / len(groups):.1%}) merge two or "
          f"more types\n")

    kinds = collections.Counter()
    examples = collections.defaultdict(list)
    for s, ws in multi.items():
        for w in ws:
            k = classify(w, s)
            kinds[k] += 1
            if k == "D":
                examples[s].append(w)
    tot = sum(kinds.values())
    names = {"A": "the same word spelled differently (a gain)",
             "B": "one documented affix removed (normal stemming)",
             "C": "a stack of documented affixes (normal morphology)",
             "D": "no affix decomposition exists (genuine error)"}
    print(f"{tot:,} (word, stem) pairs inside merged classes\n")
    for k in "ABCD":
        print(f"  {k}  {kinds[k]:>7,}  {kinds[k] / tot:>6.1%}   {names[k]}")
    ok = kinds["A"] + kinds["B"] + kinds["C"]
    print(f"\n  legitimate: {ok:,} ({ok / tot:.1%})"
          f"      coincidental: {kinds['D']:,} ({kinds['D'] / tot:.1%})")

    print(f"\nlargest classes:")
    for s, ws in sorted(multi.items(), key=lambda kv: -len(kv[1]))[:8]:
        print(f"  {s:10} {len(ws):>3} types, "
              f"{sum(vocab[w] for w in ws):>7,} tokens")
    print(f"\nstems holding a coincidental member: {len(examples):,}")
    for s, ws in sorted(examples.items(), key=lambda kv: -len(kv[1]))[:12]:
        print(f"  {s:12} {' '.join(sorted(ws, key=lambda w: -vocab[w])[:5])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
