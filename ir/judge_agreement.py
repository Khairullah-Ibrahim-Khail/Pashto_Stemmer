# judge_agreement.py
"""How much do two judges agree, on the documents both of them judged?

Run after both have judged the shared queries:

    python judge_agreement.py khairullah classmate

Reports raw agreement and Cohen's kappa. The paper should quote these: a
retrieval result rests on the judgements, and a reader cannot weigh it without
knowing how repeatable they are.
"""
import os
import sys

from config import OUTPUT_DIR


def load(judge):
    path = os.path.join(OUTPUT_DIR, f"qrels_{judge}.tsv")
    if not os.path.exists(path):
        raise SystemExit(f"{path} not found -- has {judge} judged anything yet?")
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                qid, docid, rel = line.rstrip("\n").split("\t")
                out[(qid, docid)] = int(rel)
    return out


def kappa(a, b, shared):
    """Cohen's kappa on the binary relevant/not decision."""
    n = len(shared)
    agree = sum(1 for k in shared if a[k] == b[k]) / n
    pa = sum(1 for k in shared if a[k]) / n          # judge A says relevant
    pb = sum(1 for k in shared if b[k]) / n
    chance = pa * pb + (1 - pa) * (1 - pb)
    return agree, chance, (agree - chance) / (1 - chance) if chance < 1 else 1.0


def band(k):
    for edge, name in ((0.81, "almost perfect"), (0.61, "substantial"),
                       (0.41, "moderate"), (0.21, "fair"), (0.0, "slight")):
        if k >= edge:
            return name
    return "poor"


def main():
    if len(sys.argv) != 3:
        print("usage: python judge_agreement.py <judge-a> <judge-b>")
        return 1
    ja, jb = sys.argv[1], sys.argv[2]
    a, b = load(ja), load(jb)
    shared = sorted(set(a) & set(b))
    if not shared:
        print(f"{ja} judged {len(a)}, {jb} judged {len(b)}, but no document in "
              f"common. Judge the same queries first -- see JUDGING.md step 4.")
        return 1

    agree, chance, k = kappa(a, b, shared)
    queries = len({q for q, _ in shared})
    print(f"\n{ja}: {len(a)} judgements    {jb}: {len(b)} judgements")
    print(f"both judged {len(shared)} documents across {queries} queries\n")
    print(f"  raw agreement   {agree:7.2%}")
    print(f"  expected by chance {chance:7.2%}")
    print(f"  Cohen's kappa   {k:7.3f}   ({band(k)})")
    disagree = [kk for kk in shared if a[kk] != b[kk]]
    if disagree:
        print(f"\n{len(disagree)} disagreements -- settle these together:")
        for q, d in disagree[:20]:
            print(f"   {q}  {d}   {ja}={a[(q, d)]}  {jb}={b[(q, d)]}")
        if len(disagree) > 20:
            print(f"   ... and {len(disagree) - 20} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
