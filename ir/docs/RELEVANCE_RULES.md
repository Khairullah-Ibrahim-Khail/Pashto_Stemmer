# How to decide: relevant or not relevant

Read this before judging. Everyone judging must use the same rule, or the
numbers at the end mean nothing.

---

## The one question

> **A Pashto speaker types this query into a search box.
> Does this document give them what they were looking for?**

`y` if yes. `n` if no. `s` only if you truly cannot tell.

Nothing else. Not how the computer found it. Not which words it shares.

---

## The rule you must NOT use

Someone suggested: *mark it relevant if the document contains the query word,
or a word with the same stem.*

**Do not do this. It would make the whole experiment worthless.**

Here is why, in plain terms.

We are testing whether the stemmer helps search. The way we test it is:

1. the stemmer decides which documents to return
2. **a human decides whether those documents are any good**

Step 2 is the only independent measurement in the experiment. If the human
decides "good" by asking *does it share a stem*, then step 2 is just step 1
asked again. The stemmer would be marking its own homework.

What would actually happen:

- Every document the stemmed search returns shares a stem **by definition** —
  that is how it was found. So all of them become relevant, and the stemmed
  run scores near 100%.
- The unstemmed run returns documents matching the exact word, so some of its
  results would be marked *not* relevant for failing a test it never took.
- The result would be "stemming is almost perfect", and it would be a
  measurement of nothing at all. Any examiner who reads the method will see
  this immediately.

**Judge as if the stemmer did not exist.** You are judging the document
against the question, not against the software.

---

## How to decide, in three steps

### Step 1 — find the word that carries the question

Every query has one word that makes it *that* question rather than a general
one:

| query | the word that matters |
|---|---|
| `د ښځو د حقوقو قانون` | **ښځو** (women) — not حقوق, not قانون |
| `روغتون درملنه` | **روغتون** (hospital) — not درمل |
| `د افغانیو ارزښت` | **افغانیو** (the currency) — not ارزښت |
| `د پوهنتون زده کوونکي` | **پوهنتون** (university) — not زده کوونکي |

### Step 2 — is the **meaning** of that word in the document?

Not the letters. The meaning.

- `روغتیا` means *health*. `روغتون` means *hospital*. **Different meanings.**
  A document about health services does not answer a question about hospital
  treatment, even though the stemmer merges them.
- `پوهنه` means *education*. `پوهنتون` means *university*. **Different.**
  The Ministry of Education is not a university.
- `افغانۍ` is *money*. `افغانستان` is *the country*. `افغانان` are *people*.
  **Three different things**, all stemmed to `افغان`.

**If the meaning is absent → `n`. Stop there. Do not read further.**

This is also the fast path: most `n` decisions take five seconds.

### Step 3 — is the document *about* it, or does it just mention it?

If the meaning is present, one more check.

- ✅ **About it** → `y`. A report on a student protest at a university
  answers `د پوهنتون زده کوونکي`.
- ❌ **Mentions it in passing** → `n`. A cricket report that happens to name a
  province does not answer `د افغانستان ولایتونه`.

---

## Worked examples from your own data

**Query `روغتون درملنه`** (hospital treatment)

| document | decision | why |
|---|---|---|
| treatment at Al-Wafa **hospital** in Gaza | `y` | a hospital, and treatment in it |
| Ministry of Health buying **medicine** for **health centres** | `n` | `روغتیا` is health, not a hospital; it is about procurement |

**Query `د ښځو د حقوقو قانون`** (women's rights law)

| document | decision | why |
|---|---|---|
| UN demanding the Taliban lift restrictions on **women**, their rights to work and study | `y` | about women's rights, even though the word `قانون` never appears |
| US law on police use of lethal force | `n` | plenty of `حقوق` and `قانون`, **no women** |

**Query `د افغانستان ولایتونه`** (the provinces of Afghanistan)

| document | decision | why |
|---|---|---|
| floods across seven **provinces of China** | `n` | wrong country |
| an arrest in **Takhar** province | `n` | the province is where it happened, not the subject |

---

## Four situations that will come up

**1. The document holds several unrelated stories.**
Your documents were made by grouping consecutive sentences, so one document
often contains two or three separate news items. **If any story in it answers
the query, press `y`.** Read the whole document — it is all on screen now.

**2. The document uses a different word for the same thing.**
`محصلین` and `زده کوونکي` both mean students. If the document is about
university students, it is relevant **whatever word it uses**. Judge meaning,
never spelling.

**3. The query word is there but means something else.**
`ارزګان` (Uruzgan, a province) is not `ارزښت` (value). `اوسکار` (Oscar) is not
`اوس` (now). Same letters at the start, different word → `n`.

**4. The query itself is vague.**
Some queries are too general — `د افغانستان ولایتونه` is nearly every Afghan
news story. For these, apply step 3 strictly: relevant only if provinces are
the **subject** (their administration, boundaries, a list, a comparison), not
if one is merely the location. Write down the rule you choose and apply it to
every document in that query.

---

## Consistency beats correctness

There is no perfectly right answer for every document. What matters is that
**you decide the same way every time**, and that everyone judging decides the
same way as each other.

- Before you start a query, read it and decide what would satisfy it.
- Do not change your standard halfway through a query.
- If you change your mind about a rule, go back and redo the documents you
  already judged under the old one — `/review` makes this quick.

## If you are unsure

Press `s`. It is recorded as unjudged and costs nothing. A guess becomes a
number in the final table; a skip does not.
