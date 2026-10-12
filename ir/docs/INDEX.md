# Documentation

Read in this order.

| file | read it when |
|---|---|
| **[README.md](README.md)** | you want to know how the retrieval test works — the pipeline, the flowchart, how to run it |
| **[JUDGING.md](JUDGING.md)** | you are about to judge documents. Send this to anyone helping |
| **[RELEVANCE_RULES.md](RELEVANCE_RULES.md)** | you are deciding `y` or `n` and want the rule. **Read before judging** |
| **[PARTIAL_MATCHES.md](PARTIAL_MATCHES.md)** | a document came back matching only some query words, and you want to know if that is good, how to rate it, and how to fix it |
| **[IR_FINDINGS.md](IR_FINDINGS.md)** | you want the complete record: results, statistics, every bug found and fixed, every limitation |
| **[CONFLATION_ANALYSIS.md](CONFLATION_ANALYSIS.md)** | you want to know whether the stemmer merging many words into one stem is an error or Pashto morphology |

## In one paragraph

44,814 Pashto news documents, 39 queries, 1,489 human relevance judgements.
The same search engine is run twice — once on plain text, once on stemmed text
— and the two rankings are scored against the same judgements. Stemming raises
MAP from 0.5407 to 0.6517, which is significant by both a paired t-test
(p = 0.005) and a sign test (30 of 39 improved, p = 0.001). The three
cutoff-10 measures improve too, none of them significantly. The gain is uneven:
30 queries gain 6.03 MAP between them while nine lose 1.70. One suffix,
`‑تون`, caused the worst of those losses by merging *hospital* with *health*
and *university* with *education*; it is now gated, which improves all four
measures and costs 0.22 points of intrinsic accuracy — the one case where the
word-level and the retrieval evaluations disagree.
