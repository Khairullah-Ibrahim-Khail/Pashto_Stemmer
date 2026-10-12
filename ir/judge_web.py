# judge_web.py
"""Relevance judging in the browser, because a terminal cannot render Pashto.

    python judge_web.py <your-name>      then open http://127.0.0.1:8000

Most Linux terminals do no bidirectional reordering and no Arabic shaping, so
Pashto appears unjoined and backwards. A browser does both correctly, gives
readable type, and makes the five hours bearable.

Same pooling, same seed, same output file as make_qrels.py -- the two are
interchangeable, and you can switch between them mid-way.
"""
import csv
import hashlib
import html
import json
import os
import random
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from config import OUTPUT_DIR, POOL_PER_RUN
from data_loader import load_corpus, load_queries
from index import (build_unstemmed_index, build_stemmed_index, stem_query,
                   retrieve)

SEED = 20261010          # the same order make_qrels.py uses
# The whole document, not a snippet. Every document in this corpus is longer
# than 700 characters (median 1,507), and they were formed by grouping
# consecutive sentences, so the part that answers a query is often in the
# second half. A cut snippet therefore hid the evidence the judge needed.
# A very long outlier is capped only so the page stays usable; the cap is
# reported on screen when it bites.
SNIPPET = 20000
PORT = 8000

STATE = {}


def qrels_path(judge):
    return os.path.join(OUTPUT_DIR, f"qrels_{judge}.tsv")


def archive_path(judge):
    return os.path.join(OUTPUT_DIR, f"judged_{judge}.tsv")


def content_id(text):
    """A short hash of the document's own text.

    The qrels file is keyed by docid, and a docid is only a filename. Re-split
    the corpus and every id changes, which silently turns a judgement into an
    answer about some other document. This hash travels with the text, so a
    judgement can be verified later, and remap_qrels.py can carry judgements
    onto a new corpus by matching content rather than filename.
    """
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


ARCHIVE_FIELDS = ["qid", "query", "docid", "relevance", "content_id",
                  "judged_at", "document"]


def append_archive(judge, qid, qtext, docid, rel, text):
    """Record what was judged, in full, alongside the judgement itself."""
    import time
    path = archive_path(judge)
    new = not os.path.exists(path)
    with open(path, "a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=ARCHIVE_FIELDS, delimiter="\t",
                           quoting=csv.QUOTE_MINIMAL,
                           extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow({
            "qid": qid, "query": qtext, "docid": docid, "relevance": rel,
            "content_id": content_id(text),
            "judged_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "document": " ".join(text.split()),
        })


def load_judged(path):
    out = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    qid, docid, rel = line.rstrip("\n").split("\t")
                    out[(qid, docid)] = int(rel)
    return out


def save_judged(path, judged):
    with open(path, "w", encoding="utf-8") as fh:
        for (qid, docid), rel in sorted(judged.items()):
            fh.write(f"{qid}\t{docid}\t{rel}\n")


def build():
    judge = STATE["judge"]
    docs = load_corpus()
    queries = load_queries()
    print("\nBuilding both indexes so the pool is drawn from both runs...")
    docids, bm25_u, _ = build_unstemmed_index(docs)
    _, bm25_s, _ = build_stemmed_index(docs)

    rng = random.Random(SEED)
    tasks = []
    for qid, qtext in queries.items():
        pu = retrieve(bm25_u, docids, stem_query(qtext, False), POOL_PER_RUN)
        ps = retrieve(bm25_s, docids, stem_query(qtext, True), POOL_PER_RUN)
        pool = list(dict.fromkeys(pu + ps))
        rng.shuffle(pool)
        for docid in pool:
            tasks.append((qid, qtext, docid))

    STATE.update(docs=docs, queries=queries, tasks=tasks,
                 docids=docids, bm25_u=bm25_u, bm25_s=bm25_s,
                 path=qrels_path(judge), judged=load_judged(qrels_path(judge)))
    print(f"\n{len(tasks)} (query, document) pairs pooled over "
          f"{len(queries)} queries")
    print(f"{len(STATE['judged'])} already judged\n")
    print(f"  ==> open  http://127.0.0.1:{PORT}  in your browser\n")


def next_task(only=None):
    """The next unjudged pair, optionally restricted to one query."""
    for qid, qtext, docid in STATE["tasks"]:
        if only and qid != only:
            continue
        if (qid, docid) not in STATE["judged"]:
            return qid, qtext, docid
    return None


PAGE = """<!doctype html>
<html lang="ps" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Relevance judging</title>
<style>
:root{--bg:#fbfaf8;--fg:#1a1a1a;--mut:#6b6b6b;--line:#e2ded8;--card:#fff;
      --yes:#1f7a3f;--no:#9b2226;--accent:#2b4f81}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){
  --bg:#15171a;--fg:#e9e6e1;--mut:#9aa0a6;--line:#2c3036;--card:#1c1f23;
  --yes:#4caf6d;--no:#e06c75;--accent:#7aa2d2}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
     font-family:"Noto Naskh Arabic","Scheherazade New",serif;
     display:flex;flex-direction:column;min-height:100vh}
header{padding:14px 16px;border-bottom:1px solid var(--line);
       display:flex;gap:14px;align-items:baseline;flex-wrap:wrap}
.q{font-size:1.45rem;font-weight:700}
.meta{font-family:ui-sans-serif,system-ui,sans-serif;font-size:.8rem;
      color:var(--mut);direction:ltr}
.bar{height:4px;background:var(--line)}
.bar>div{height:100%;background:var(--accent);transition:width .2s}
main{flex:1;display:flex;justify-content:center;padding:18px 16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;
      padding:22px 24px;max-width:860px;width:100%;
      box-shadow:0 1px 3px rgba(0,0,0,.05)}
.snip{font-size:1.3rem;line-height:2.1}
.docid{font-family:ui-monospace,monospace;font-size:.75rem;color:var(--mut);
       direction:ltr;margin-bottom:14px}
footer{padding:14px 16px 26px;display:flex;gap:12px;justify-content:center;
       flex-wrap:wrap;border-top:1px solid var(--line)}
button{font:inherit;font-size:1.05rem;padding:13px 30px;border-radius:9px;
       border:1px solid var(--line);background:var(--card);color:var(--fg);
       cursor:pointer;min-width:120px}
button:hover{border-color:var(--accent)}
.y{background:var(--yes);border-color:var(--yes);color:#fff}
.n{background:var(--no);border-color:var(--no);color:#fff}
kbd{font-family:ui-monospace,monospace;font-size:.72rem;opacity:.85}
.done{text-align:center;padding:60px 20px;font-size:1.2rem}
.hint{font-family:ui-sans-serif,system-ui,sans-serif;font-size:.78rem;
      color:var(--mut);text-align:center;padding:0 16px 20px;direction:ltr}
a{color:var(--accent)}
.rv{max-width:1000px;width:100%;margin:0 auto}
.row{background:var(--card);border:1px solid var(--line);border-radius:10px;
     padding:12px 16px;margin-bottom:10px;display:grid;
     grid-template-columns:1fr auto;gap:12px;align-items:center}
.row.rel{border-inline-start:4px solid var(--yes)}
.row.not{border-inline-start:4px solid var(--no)}
.row.skip{border-inline-start:4px solid var(--mut)}
.row.none{border-inline-start:4px solid var(--accent);background:var(--bg)}
.rtxt{font-size:1.12rem;line-height:1.9;max-height:16em;overflow-y:auto}
.rid{font-family:ui-monospace,monospace;font-size:.7rem;color:var(--mut);
     direction:ltr}
.tag{font-family:ui-sans-serif,system-ui,sans-serif;font-size:.72rem;
     direction:ltr;white-space:nowrap}
.acts{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}
.acts button{min-width:0;padding:7px 13px;font-size:.9rem;opacity:.55}
.acts button.now{opacity:1;font-weight:700;outline:2px solid currentColor;
                 outline-offset:1px}
.acts button:hover{opacity:1}
.row{transition:opacity .12s}
h2{font-size:1.15rem;margin:22px 0 10px;padding-inline-start:4px}
.jump{font-family:ui-sans-serif,system-ui,sans-serif;font-size:.78rem;
      direction:ltr;display:flex;gap:6px;flex-wrap:wrap;width:100%;
      margin-top:8px}
.jump a{padding:3px 9px;border:1px solid var(--line);border-radius:6px;
        text-decoration:none}
.jump a.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.qrow{display:grid;grid-template-columns:62px 1fr 110px 190px;gap:14px;
      align-items:center;background:var(--card);border:1px solid var(--line);
      border-radius:10px;padding:11px 16px;margin-bottom:8px;
      text-decoration:none;color:inherit}
.qrow:hover{border-color:var(--accent)}
.qrow.done{opacity:.6}
.qrow.part{border-inline-start:4px solid var(--accent)}
.qrow.todo{border-inline-start:4px solid var(--yes)}
.qid{font-family:ui-monospace,monospace;font-size:.78rem;color:var(--mut);
     direction:ltr}
.qtext{font-size:1.15rem}
.qbar{height:6px;background:var(--line);border-radius:3px;overflow:hidden}
.qbar>div{height:100%;background:var(--accent)}
.qnum{font-family:ui-sans-serif,system-ui,sans-serif;font-size:.74rem;
      color:var(--mut);direction:ltr;text-align:end}
@media(max-width:700px){.qrow{grid-template-columns:1fr}
  .qnum{text-align:start}}
.tokens{background:var(--card);border:1px solid var(--line);border-radius:10px;
        padding:14px 18px;margin-bottom:18px;font-size:1.1rem;line-height:1.9}
.tokens b{font-family:ui-sans-serif,system-ui,sans-serif;font-size:.8rem}
.tokens .note{font-family:ui-sans-serif,system-ui,sans-serif;font-size:.78rem;
              color:var(--mut);direction:ltr;margin-top:8px;line-height:1.5}
.b-rel{color:var(--yes);font-weight:700}
.b-not{color:var(--no);font-weight:700}
.b-un{color:var(--mut)}
.b-new{background:var(--accent);color:#fff;padding:1px 6px;border-radius:4px}
.row[data-only="1"]{box-shadow:inset 4px 0 0 var(--accent)}
@media(max-width:640px){.row{grid-template-columns:1fr}
  .acts{justify-content:flex-start}}
</style></head><body>
__BODY__
<script>
// Only the judging page has a current document, and only there does a reload
// make sense -- it advances to the next one. The review page leaves these
// unbound: a keypress there used to fire a POST with an empty id and reload,
// which is what threw the scroll back to the top.
const QID = "__QID__", DOCID = "__DOCID__";
if (QID && DOCID) {
  function send(rel){
    fetch("/judge",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({qid:QID,docid:DOCID,rel:rel})})
     .then(r=>{ if(!r.ok) throw new Error(r.status); location.reload(); })
     .catch(e=>alert("Not saved: "+e+
        "\\nYour earlier answers are safe in the file."));
  }
  window.send = send;
  document.addEventListener("keydown",e=>{
    if(e.target.tagName==="INPUT"||e.target.tagName==="TEXTAREA") return;
    if(e.key==="y"||e.key==="Y"||e.key==="ArrowRight") send(1);
    if(e.key==="n"||e.key==="N"||e.key==="ArrowLeft")  send(0);
    if(e.key==="s"||e.key==="S")                       send(-1);
  });
}
</script></body></html>"""


def render(only=None):
    task = next_task(only)
    pool = [t for t in STATE["tasks"] if not only or t[0] == only]
    total = len(pool)
    done = sum(1 for q, _, d in pool if (q, d) in STATE["judged"])
    if task is None:
        rel = sum(1 for v in STATE["judged"].values() if v == 1)
        body = (f'<div class="done">All {done} judged — {rel} relevant.<br>'
                f'<span class="meta">Saved to {html.escape(STATE["path"])}. '
                f'<a href="/review">review &amp; fix</a> · '
                f'you can close this tab.</span></div>')
        return PAGE.replace("__BODY__", body).replace("__QID__", "") \
                   .replace("__DOCID__", "")

    qid, qtext, docid = task
    full = STATE["docs"][docid]
    snippet = " ".join(full[:SNIPPET].split())
    cut = len(full) > SNIPPET
    pct = 100.0 * done / total if total else 0
    body = f"""
<header>
  <div class="q">{html.escape(qtext)}</div>
  <div class="meta">{html.escape(qid)} &nbsp;·&nbsp; {done} of {total} judged
     &nbsp;·&nbsp; {total - done} left
     &nbsp;·&nbsp; <a href="/review">review &amp; fix</a>
     &nbsp;·&nbsp; <a href="/queries">all queries</a>
     &nbsp;·&nbsp; <a href="/inspect?q={qid}">diagnose</a></div>
</header>
<div class="bar"><div style="width:{pct:.1f}%"></div></div>
<main><div class="card">
  <div class="docid">{html.escape(docid)}</div>
  <div class="snip">{html.escape(snippet)}{"… [truncated, document is "
       + format(len(full), ",") + " characters]" if cut else ""}</div>
</div></main>
<footer>
  <button class="y" onclick="send(1)">اړوند &nbsp;<kbd>y</kbd></button>
  <button class="n" onclick="send(0)">اړوند نه دی &nbsp;<kbd>n</kbd></button>
  <button onclick="send(-1)">skip &nbsp;<kbd>s</kbd></button>
</footer>
<div class="hint">Does this document answer the query above? Mentioning a word
  from the query is not enough — it has to be about the topic.
  Keys: <kbd>y</kbd> relevant · <kbd>n</kbd> not · <kbd>s</kbd> skip</div>"""
    return PAGE.replace("__BODY__", body).replace("__QID__", qid) \
               .replace("__DOCID__", docid)


REVIEW_JS = """<script>
// Update the row where it sits. Reloading the page threw the scroll position
// back to the top, which makes correcting anything past the first screen a
// hunt -- and after fifty judgements that is most of them.
const LABEL = {1:"relevant", 0:"not relevant", "-1":"skipped"};
const CLS   = {1:"rel", 0:"not", "-1":"skip"};
function set(qid,docid,rel){
  const row = document.getElementById("row-"+qid+"-"+docid);
  if(row) row.style.opacity = .45;
  fetch("/judge",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({qid:qid,docid:docid,rel:rel})})
   .then(r=>{
     if(!r.ok) throw new Error(r.status);
     if(!row) return;
     row.style.opacity = 1;
     row.className = "row " + CLS[rel];
     const tag = row.querySelector(".tag");
     if(tag) tag.textContent = LABEL[rel];
     row.querySelectorAll(".acts button").forEach(b=>
        b.classList.toggle("now", b.dataset.rel == String(rel)));
     return fetch("/counts").then(r=>r.json()).then(c=>{
        const el = document.getElementById("counts");
        if(el) el.innerHTML = c.total + " judged &nbsp;\u00b7&nbsp; " +
           c.rel + " relevant &nbsp;\u00b7&nbsp; " + c.not + " not " +
           "&nbsp;\u00b7&nbsp; " + c.skip + " skipped";
     });
   })
   .catch(e=>{ if(row){ row.style.opacity=1;
      row.style.outline="2px solid var(--no)"; }
      alert("Not saved: "+e+"\\nYour earlier answers are safe in the file."); });
}
</script>"""


def render_review(only=None):
    """Everything judged so far, with a button to change any of it.

    The file is the record, so a correction here rewrites it immediately --
    there is nothing to re-run and no progress to lose.
    """
    judged = STATE["judged"]
    if not judged:
        body = ('<div class="done">Nothing judged yet. '
                '<a href="/">start judging</a></div>')
        return PAGE.replace("__BODY__", body) \
                   .replace("__QID__", "").replace("__DOCID__", "")

    qtext = {q: t for q, t, _ in STATE["tasks"]}
    by_query = {}
    if only:
        # One query: list EVERY document in its pool, in the order they are
        # offered, with the unjudged ones included. That makes this page a
        # list you can work straight down, rather than a record of what is
        # already done.
        for qid, _, docid in STATE["tasks"]:
            if qid != only:
                continue
            by_query.setdefault(qid, []).append(
                (docid, judged.get((qid, docid), None)))
    else:
        for (qid, docid), rel in judged.items():
            by_query.setdefault(qid, []).append((docid, rel))
    if only and not by_query:
        body = (f'<div class="done">No documents pooled for '
                f'{html.escape(only)}. <a href="/review">show all</a></div>')
        return PAGE.replace("__BODY__", body) \
                   .replace("__QID__", "").replace("__DOCID__", "")

    if only:
        vals = [r for _, r in by_query.get(only, [])]
        rel_n = sum(1 for v in vals if v == 1)
        not_n = sum(1 for v in vals if v == 0)
        skip_n = sum(1 for v in vals if v is None)
    else:
        rel_n = sum(1 for v in judged.values() if v == 1)
        not_n = sum(1 for v in judged.values() if v == 0)
        skip_n = sum(1 for v in judged.values() if v < 0)
    parts = [f'''<header>
  <div class="q">Review</div>
  <div class="meta"><span id="counts">{sum(len(v) for v in by_query.values()) if only else len(judged)} {"in this query" if only else "judged"} &nbsp;·&nbsp;
     {rel_n} relevant &nbsp;·&nbsp; {not_n} not &nbsp;·&nbsp;
     {skip_n} {"not judged" if only else "skipped"}</span>
     &nbsp;·&nbsp; <a href="/">back to judging</a></div>
  <div class="jump">''' + " ".join(
       [f'<a href="/review">all</a>'] +
       [f'<a href="/review?q={q}" class="{"on" if q == only else ""}">{q}</a>'
        for q in sorted({qq for qq, _ in judged})]) + '''</div>
</header>
<main><div class="rv">''']
    for qid in sorted(by_query):
        parts.append(f'<h2>{html.escape(qid)} &nbsp; '
                     f'{html.escape(qtext.get(qid, ""))}</h2>')
        rows_here = by_query[qid] if only else sorted(by_query[qid])
        for docid, rel in rows_here:
            cls = {1: "rel", 0: "not", None: "none"}.get(rel, "skip")
            tag = {1: "relevant", 0: "not relevant",
                   None: "not judged yet"}.get(rel, "skipped")
            snip = " ".join(STATE["docs"].get(docid, "")[:SNIPPET].split())
            parts.append(f'''<div class="row {cls}" id="row-{qid}-{docid}">
  <div>
    <div class="rid">{html.escape(docid)} &nbsp;<span class="tag">{tag}</span></div>
    <div class="rtxt">{html.escape(snip)}</div>
  </div>
  <div class="acts">
    <button class="y{" now" if rel == 1 else ""}" data-rel="1"
            onclick="set(\'{qid}\',\'{docid}\',1)">اړوند</button>
    <button class="n{" now" if rel == 0 else ""}" data-rel="0"
            onclick="set(\'{qid}\',\'{docid}\',0)">نه</button>
    <button class="{"now" if rel is not None and rel < 0 else ""}" data-rel="-1"
            onclick="set(\'{qid}\',\'{docid}\',-1)">skip</button>
  </div>
</div>''')
    parts.append("</div></main>" + REVIEW_JS)
    return PAGE.replace("__BODY__", "".join(parts)) \
               .replace("__QID__", "").replace("__DOCID__", "")


def render_inspect(qid):
    """Why one query behaved as it did: both rankings, with your labels.

    A query where stemming loses is either a weakness in the stemmer or a
    judging mistake. The two rankings side by side, each document carrying the
    label you gave it, is what separates them -- and the stemmed query tokens
    at the top usually name the cause outright.
    """
    queries = STATE["queries"]
    if qid not in queries:
        opts = " ".join(f'<a href="/inspect?q={q}">{q}</a>'
                        for q in sorted(queries))
        body = (f'<header><div class="q">Diagnose a query</div>'
                f'<div class="meta"><a href="/">back to judging</a></div>'
                f'<div class="jump">{opts}</div></header>')
        return PAGE.replace("__BODY__", body) \
                   .replace("__QID__", "").replace("__DOCID__", "")

    qtext = queries[qid]
    tok_u = stem_query(qtext, False)
    tok_s = stem_query(qtext, True)
    judged = {d: r for (q, d), r in STATE["judged"].items() if q == qid}
    rel = {d for d, r in judged.items() if r == 1}
    ru = retrieve(STATE["bm25_u"], STATE["docids"], tok_u, 10)
    rs = retrieve(STATE["bm25_s"], STATE["docids"], tok_s, 10)
    only_s = [d for d in rs if d not in ru]

    def ap(ranked):
        hits = 0.0
        tot = 0.0
        for i, d in enumerate(retrieve(
                STATE["bm25_u"] if ranked is ru else STATE["bm25_s"],
                STATE["docids"], tok_u if ranked is ru else tok_s), 1):
            if d in rel:
                hits += 1
                tot += hits / i
        return tot / len(rel) if rel else 0.0

    def badge(d):
        if d in rel:
            return '<span class="tag b-rel">relevant</span>'
        if d in judged:
            return '<span class="tag b-not">not relevant</span>'
        return '<span class="tag b-un">unjudged</span>'

    def column(title, ranked):
        out = [f'<h2>{title}</h2>']
        for i, d in enumerate(ranked, 1):
            cls = ("rel" if d in rel else "not" if d in judged else "skip")
            mark = ' data-only="1"' if d in only_s else ""
            snip = " ".join(STATE["docs"][d][:SNIPPET].split())
            out.append(f'''<div class="row {cls}"{mark}>
  <div>
    <div class="rid">{i}. {html.escape(d)} &nbsp;{badge(d)}
       {'&nbsp;<span class="tag b-new">stemmed only</span>' if d in only_s else ''}</div>
    <div class="rtxt">{html.escape(snip)}</div>
  </div>
</div>''')
        return "".join(out)

    opts = " ".join(
        f'<a href="/inspect?q={q}" class="{"on" if q == qid else ""}">{q}</a>'
        for q in sorted(queries))
    body = f'''<header>
  <div class="q">{html.escape(qtext)}</div>
  <div class="meta">{html.escape(qid)} &nbsp;·&nbsp; {len(judged)} judged,
     {len(rel)} relevant &nbsp;·&nbsp; MAP unstemmed {ap(ru):.4f},
     stemmed {ap(rs):.4f} &nbsp;·&nbsp;
     <a href="/">back to judging</a> &nbsp;·&nbsp;
     <a href="/review?q={qid}">review this query</a></div>
  <div class="jump">{opts}</div>
</header>
<main><div class="rv">
  <div class="tokens">
     <div><b>query words</b></div>
     <div>unstemmed &nbsp; {" · ".join(html.escape(t) for t in tok_u)}</div>
     <div>stemmed &nbsp;&nbsp;&nbsp; {" · ".join(html.escape(t) for t in tok_s)}</div>
     <div class="note">If a stemmed word is much shorter than the original,
        it is probably matching other words too — that is the usual cause.</div>
  </div>
  {column("top 10 — unstemmed", ru)}
  {column("top 10 — stemmed", rs)}
</div></main>'''
    return PAGE.replace("__BODY__", body) \
               .replace("__QID__", "").replace("__DOCID__", "")


def render_queries():
    """Every query, with progress, so you can pick what to work on."""
    counts = {}
    for qid, _, docid in STATE["tasks"]:
        n, d = counts.get(qid, (0, 0))
        counts[qid] = (n + 1, d + (1 if (qid, docid) in STATE["judged"] else 0))
    rows = []
    for qid, qtext in STATE["queries"].items():
        n, d = counts.get(qid, (0, 0))
        rel = sum(1 for (q, dd), v in STATE["judged"].items()
                  if q == qid and v == 1)
        pct = 100.0 * d / n if n else 0
        state = ("done" if n and d >= n else "part" if d else "todo")
        label = ("finished" if state == "done"
                 else f"{n - d} left" if d else f"{n} to judge")
        rows.append(f'''<a class="qrow {state}" href="/review?q={qid}">
  <div class="qid">{html.escape(qid)}</div>
  <div class="qtext">{html.escape(qtext)}</div>
  <div class="qbar"><div style="width:{pct:.0f}%"></div></div>
  <div class="qnum">{d}/{n} &nbsp;·&nbsp; {rel} rel &nbsp;·&nbsp; {label}</div>
</a>''')
    tot = len(STATE["tasks"])
    dn = len(STATE["judged"])
    body = f'''<header>
  <div class="q">Queries</div>
  <div class="meta">{len(STATE["queries"])} queries &nbsp;·&nbsp; {dn} of {tot}
     judged &nbsp;·&nbsp; <a href="/">next unjudged</a>
     &nbsp;·&nbsp; <a href="/review">review &amp; fix</a></div>
</header>
<main><div class="rv">{"".join(rows)}</div></main>'''
    return PAGE.replace("__BODY__", body) \
               .replace("__QID__", "").replace("__DOCID__", "")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass                              # keep the console readable

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/counts":
            j = STATE["judged"]
            payload = json.dumps({
                "total": len(j),
                "rel": sum(1 for v in j.values() if v == 1),
                "not": sum(1 for v in j.values() if v == 0),
                "skip": sum(1 for v in j.values() if v < 0),
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if path == "/inspect":
            q = parse_qs(urlparse(self.path).query).get("q", [None])[0]
            page = render_inspect(q).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)
            return
        if path == "/review":
            q = parse_qs(urlparse(self.path).query).get("q", [None])[0]
            page = render_review(q).encode("utf-8")
        elif path == "/queries":
            page = render_queries().encode("utf-8")
        elif path == "/":
            q = parse_qs(urlparse(self.path).query).get("q", [None])[0]
            page = render(q).encode("utf-8")
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(n) or b"{}")
        qid, docid, rel = data.get("qid"), data.get("docid"), data.get("rel")
        if qid and docid:
            STATE["judged"][(qid, docid)] = rel if rel in (0, 1) else -1
            save_judged(STATE["path"],
                        {k: v for k, v in STATE["judged"].items() if v >= 0})
            # Archive the document text with every judgement, not just its id.
            qtext = next((t for q, t, _ in STATE["tasks"] if q == qid), "")
            append_archive(STATE["judge"], qid, qtext, docid,
                           STATE["judged"][(qid, docid)],
                           STATE["docs"].get(docid, ""))
            done = sum(1 for v in STATE["judged"].values() if v >= 0)
            print(f"\r{done} judged", end="", flush=True)
        self.send_response(204)
        self.end_headers()


def main():
    global PORT
    if not 2 <= len(sys.argv) <= 3:
        print("usage: python judge_web.py <your-name> [port]\n"
              "       python judge_web.py ahmad          -> port 8000\n"
              "       python judge_web.py sana 8001      -> port 8001\n\n"
              "Two people on the same machine need different ports; each\n"
              "writes to their own file either way.")
        return 1
    STATE["judge"] = sys.argv[1]
    if len(sys.argv) == 3:
        PORT = int(sys.argv[2])
    build()
    try:
        ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
    except OSError as exc:
        print(f"\nCannot use port {PORT}: {exc}\n"
              f"Someone else is judging on it. Try: "
              f"python judge_web.py {STATE['judge']} {PORT + 1}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
