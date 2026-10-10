# Pashto Irregular Verb Dictionary

> **This document is the survey, not the dictionary.** It records which verbs
> were gathered and which entries were checked against a printed source. The
> dictionary the stemmer actually loads is
> `pashto_stemmer/irregular_verbs.py`, which holds **38 paradigms covering 315
> surface forms**, and it is printed in Appendix B of the paper from
> `paper/verbs_sources.tsv` by `paper/make_verb_appendix.py`.
>
> The two have diverged. Twelve verbs listed here are **not** in the
> dictionary — `اغوستل`، `اوړل`، `چاودل`، `نغښتل`، `ویشتل`، `وتل`، `رودل`،
> `ورتلل`، `درتلل`، `راکول`، `درکول`، `پرانیستل` — and eight that are in the
> dictionary are not described here: `څښل`، `رسېدل`، `پوهېدل`، `اوسېدل`،
> `پاڅېدل`، `سپارل`، `ژغورل`، `کارول`. Where the two disagree, the code is
> what runs.
>
> **Status: partly unverified.** 15 of the 38 implemented entries are
> unverified against a printed source. Do not cite the unverified block until
> it is checked.

## What belongs here — and what does not

Only verbs whose **present stem cannot be derived from the infinitive**
(Pashto *strong* verbs). Everything predictable is handled by **rule**:

| pattern | example | handled by |
|---|---|---|
| `‑ېدل` inchoative | جوړېدل → جوړ | rule |
| `‑ول` causative | جوړول → جوړ | rule |
| plain `‑ل` | لیکل → لیک | rule |
| unpredictable present stem | لیدل → **وین** | this dictionary |

Three entries (`څښل`, `راوستل`, `وروړل`) were **removed** — the plain `‑ل`
rule already derives them, so listing them was redundant.

## A. Verified against a source (34)

| # | Lemma | Present | Past | Meaning | Source |
|--:|---|---|---|---|---|
| 1 | کول | کو | کړ / کاوه | to do/make | Robson & Tegey, *Iranian Languages* |
| 2 | کېدل | کېږ / کیږ | شو / شول | to become/happen | Robson & Tegey, *Iranian Languages* |
| 3 | تلل | ځ | لاړ / تل | to go | Robson & Tegey, *Iranian Languages* |
| 4 | راتلل | راځ | راغل / راغی | to come | Robson & Tegey, *Iranian Languages* |
| 5 | وړل | وړ | یووړ / یوړ | to carry/take away | Robson & Tegey, *Iranian Languages* |
| 6 | راوړل | راوړ | راووړ | to bring | Robson & Tegey, *Iranian Languages* |
| 7 | خوړل | خور | خوړ | to eat | Tegey & Robson (1996) |
| 8 | لیدل | وین | لید | to see | Tegey & Robson (1996) |
| 9 | کتل | ګور | کوت / کت | to look | Tegey & Robson (1996) |
| 10 | اخیستل | اخل | اخیست | to take/buy | Tegey & Robson (1996) |
| 11 | نیول | نیس | نیو | to catch/hold | Tegey & Robson (1996) |
| 12 | ویل | وای | ویل | to say | Tegey & Robson (1996) |
| 13 | ورکول | ورکو | ورکړ | to give | Robson & Tegey, *Iranian Languages* |
| 14 | غوښتل | غواړ | غوښت | to want | Tegey & Robson (1996) |
| 15 | موندل | موم | موند | to find | Tegey & Robson (1996) |
| 16 | لوستل | لول | لوست | to read | Tegey & Robson (1996) |
| 17 | وژل | وژن | وژل / ووژه | to kill | Tegey & Robson (1996) |
| 18 | پېژندل | پېژن / پیژن | پېژند / پیژند | to know/recognize | Tegey & Robson (1996) |
| 19 | ښودل | ښی | ښود | to show | Tegey & Robson (1996) |
| 20 | الوتل | الوز | الوت | to fly | Tegey & Robson (1996) |
| 21 | ختل | خېژ | خوت / خت | to climb/rise | Tegey & Robson (1996) |
| 22 | بلل | بول | بلل | to call/consider | Tegey & Robson (1996) |
| 23 | ایستل | باس | ایست / وېست | to pull out/extract | Tegey & Robson (1996) |
| 24 | اغوستل | اغوند | اغوست | to wear | Tegey & Robson (1996) |
| 25 | اوړل | اوړ | وښت / اوښت | to pass/cross | Tegey & Robson (1996) |
| 26 | چاودل | چو | چاود | to explode | Tegey & Robson (1996) |
| 27 | نغښتل | نغاړ | نغښت | to wrap/roll up | Tegey & Robson (1996) |
| 28 | ویشتل | ول | وېشت | to shoot | Tegey & Robson (1996) |
| 29 | وتل | وځ | وت | to go out | [T&R, doubly irr.] |
| 30 | رودل | رو | رود | to suck | Tegey & Robson (1996) |
| 31 | ورتلل | ورځ | ورتل / ورغل | to go there | Robson & Tegey Table 13.17 |
| 32 | درتلل | درځ | درتل / درغل | to go to you | Robson & Tegey Table 13.17 |
| 33 | راکول | راکو | راکړ | to give here | Robson & Tegey Table 13.17 |
| 34 | درکول | درکو | درکړ | to give to you | Robson & Tegey Table 13.17 |

## B. NOT verified — needs your check (8)

These were added without a citation. They may still be correct, but nobody
has confirmed them against a grammar. Please confirm, correct, or delete.

| # | Lemma | Present | Past | Meaning | Status |
|--:|---|---|---|---|---|
| 1 | لرل | لر | درلود / لرل | to have | ❓ unverified |
| 2 | اورېدل | اور | اورېد | to hear | ❓ unverified |
| 3 | کېښودل | ږد | کېښود / ایښود | to put/place | ❓ unverified |
| 4 | پرېښودل | پرېږد | پرېښود | to leave/abandon | ❓ unverified |
| 5 | پرېوتل | پرېوځ | پرېوت | to fall | ❓ unverified |
| 6 | کښېنستل | کښېن | کښېناست / ناست | to sit down | ❓ unverified |
| 7 | ګڼل | ګڼ | ګاڼه / ګڼل | to count/consider | ❓ unverified |
| 8 | پرانیستل | پرانیز | پرانیست | to open | ❓ unverified |

## Sources actually used

- Tegey, H. & Robson, B. (1996) *A Reference Grammar of Pashto*.
- Robson, B. & Tegey, H. 'Pashto', in *The Iranian Languages* (Routledge), Tables 13.15–13.17.
- David, A. B. (2014) *Descriptive Grammar of Pashto and its Dialects*, §8.2.6 (weak vs strong verbs).
- Apertium `apertium-pus` morphological dictionary (agreement endings).
