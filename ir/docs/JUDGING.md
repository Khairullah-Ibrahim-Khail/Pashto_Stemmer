# Relevance judging — what to do

Thank you for helping. This experiment measures whether a Pashto stemmer makes
search better. The software is finished; what it needs is human judgement,
because only a Pashto speaker can say whether a document actually answers a
question.

You will read short news passages and press **one key** for each: `y` if it
answers the question, `n` if it does not. Nothing you do can break anything,
and your answers are saved after every single key press.

---

## 1. Start

```bash
cd "/home/khairullah/Documents/testing Folder/stemmer/IR"
PY="/home/khairullah/Documents/Pashto Faker/.venv/bin/python"

$PY judge_web.py YOUR-NAME
```

Use your own first name, lowercase, no spaces — `ahmad`, `sana`, `bilal`. It
keeps your answers in your own file, separate from everyone else's.

It takes about **90 seconds** to start: it reads 44,814 documents and builds
two search indexes. When it is ready it prints:

```
  ==> open  http://127.0.0.1:8000  in your browser
```

Open that address. **Do the judging in the browser, not the terminal** — a
terminal cannot display Pashto correctly, it shows the letters unjoined and
backwards.

> **If two of you are judging on the same computer at the same time**, the
> second person adds a different port number:
> ```bash
> $PY judge_web.py sana 8001      # then open http://127.0.0.1:8001
> ```

## 2. What you will see

A question at the top, one document below it, three buttons at the bottom.

| key | button | meaning |
|---|---|---|
| `y` | اړوند | this document **answers** the question |
| `n` | اړوند نه دی | it does not |
| `s` | skip | you genuinely cannot decide |

The bar across the top shows how far along you are. Close the tab whenever you
like and run the same command again later — it carries on from where you
stopped and never asks you the same document twice.

## 3. What counts as "relevant"

**Ask yourself: would somebody searching for this be glad to find this
document?**

✅ **Yes** — it is *about* the subject, even if only partly.
For `د بلوچستان سیاسي وضعیت` (the political situation in Balochistan), a
report on political protest in Quetta is relevant.

❌ **No** — it merely *contains a word* from the question.
A sports report that happens to mention Balochistan is **not** about
Balochistan's political situation.

❌ **No** — it is about a different country, a different time, or a different
subject, however similar the words look.

Three rules that matter:

1. **Judge the subject, not the writing.** A badly written document on the
   right subject is relevant. A beautiful one on the wrong subject is not.
2. **Judge each document on its own.** Do not count how many you have already
   marked relevant. Some questions have twenty good documents, some have one,
   some have none — all three are normal and all three are useful.
3. **If you cannot tell from the passage shown, press `s`.** A guess is worse
   than a skip.

## 4. Fixing a mistake

Click **review & fix** at the top, or go to `http://127.0.0.1:8000/review`.

Every judgement you have made is listed under its question, with the passage
and your answer. A **green** edge means you marked it relevant, **red** means
not. Click a different button to change it — the page updates in place and
does not jump.

## 5. Judge independently — this part matters

**Do not look at anybody else's answers, and do not discuss documents while
judging.** Two people judging the same documents separately is the only way to
show that "relevant" means something consistent rather than one person's
opinion. If we compare notes first, that evidence is gone.

When two of you have finished the same questions:

```bash
$PY judge_agreement.py ahmad sana
```

It prints how often you agreed and a score called Cohen's kappa. **Report the
kappa; do not treat any particular value as a pass mark.** Relevance is a
judgement, not a fact with one right answer: in TREC, trained assessors
overlap on only 30-45% of the documents they call relevant, and the ranking of
systems stays the same anyway (Voorhees 2000). A low kappa is a reason to go
and read the disagreements, not a reason to throw the work away.

So when the number is low, we sit together, work through the list of
disagreements it prints, agree a rule, write it into
[RELEVANCE_RULES.md](RELEVANCE_RULES.md), and judge those again. What matters
is that the rule we end up applying is the same one, and that both arms of the
experiment are judged by that same rule. That conversation is worth having
early — which is why the first ten questions are judged by everybody.

## 6. How long it takes

About **10 seconds per document**. The current set is 132 documents, so
roughly 25 minutes. The full experiment will be around 1,800 documents across
50 questions, which is why we are splitting it between us.

---

## Questions people ask

**Can I break the experiment?** No. You only ever write to
`results/qrels_YOUR-NAME.tsv`. Nobody else's file, and no original data, can
be touched by anything you do.

**What if I close the browser by accident?** Nothing is lost. Every key press
is already written to disk. Start the command again and continue.

**Why do some documents come up under more than one question?** Because the
same document can be relevant to several. Judge it against the question shown
on screen, not against what you remember deciding before.

**The order looks random.** It is, deliberately. The documents come from two
different search methods and the order is shuffled so you cannot tell which
method found which document. That is what keeps the comparison honest.

**I don't understand what a question is asking.** Ask Khairullah rather than
guessing. One misread question wastes 36 judgements.
