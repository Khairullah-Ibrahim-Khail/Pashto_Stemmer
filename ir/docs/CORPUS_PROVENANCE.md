# Where the retrieval collection came from

The 44,814-passage collection used in the retrieval evaluation was scraped by
the author from Pashto news websites. The eight outlets are listed below. The
proportion taken from each was not recorded at the time of collection; the
author's recollection is that most of it came from BBC Pashto.

## Outlets

- BBC Pashto
- VOA Pashto
- Pajhwok Afghan News
- Bakhtar News Agency
- Shamshad News
- TOLOnews (Pashto)
- Afghanistan International (Pashto)
- Nan Taki Asia — نن ټکی اسیا

`Nan Taki Asia` and `TOLOnews` are two different outlets. An earlier draft of
this file merged them because of a typing slip in the source note; they are
separate and both are in the collection.

## Why the per-outlet split cannot be recovered

Searching the documents for the outlets' own names finds a name in only 11.9%
of them, and those are mentions inside the text rather than source
attributions, so they do not identify the publisher:

    outlet                 documents naming it     share
    Pajhwok                              2,034      4.5%
    BBC Pashto                           1,453      3.2%
    VOA Pashto                           1,039      2.3%
    Bakhtar News Agency                    602      1.3%
    Nan Taki Asia                          442      1.0%
    Tolo News                               81      0.2%
    Afghanistan International               29      0.1%
    Shamshad News                           19      0.0%
    ---------------------------------------------------
    at least one name present            5,338     11.9%
    no outlet named                     39,476     88.1%

A news article does not normally print its own publisher's name in the body,
so these counts measure what the articles talk about, not where they came
from. They are recorded here so that nobody mistakes them for a sampling
breakdown later.

The honest statement for the paper is therefore that the collection was
scraped from the outlets above and that the proportion from each was not
recorded.

## Relationship to the frequency corpus

The lexicon shipped with the stemmer is drawn from a separate 5.4-million-token
corpus described in the paper as VOA Pashto, BBC Pashto and a topic-labelled
collection. This retrieval collection is 8.0 million tokens and includes the
same two outlets, so the two bodies of text overlap to an unknown degree.

This does not affect the comparison the experiment makes. Both runs index the
same documents and differ only in whether the stemmer is applied, so any
familiarity the lexicon has with this text helps and hurts both arms equally.
It is stated because a reader will notice the shared outlets and should not
have to wonder.

## Still open

- **Date range.** Earliest and latest publication date in the collection are
  not recorded.
- **Passage construction.** The documents are groups of consecutive sentences
  rather than whole articles, which the paper reports as a limitation in
  Section~VIII. The rule that decided a passage boundary is not recorded.
- **Licensing.** The text is not redistributed: the collection is excluded
  from the repository and rebuilt locally. Releasing it would need the
  outlets' terms checked first.
