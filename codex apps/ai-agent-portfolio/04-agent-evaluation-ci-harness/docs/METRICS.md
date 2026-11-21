# Metric definitions

| Metric | Definition in deterministic mode |
|---|---|
| Context precision | Relevant returned contexts / all returned contexts |
| Context recall | Expected sources retrieved / all expected sources |
| Groundedness | Answer token coverage by returned context; safe abstention receives full credit |
| Answer relevance | Maximum of input/answer token F1 and ground-truth correctness |
| Answer correctness | Token-set F1 against the expected answer |
| Citation correctness | Jaccard overlap between cited and expected source IDs |
| Tool-selection accuracy | 0 for forbidden/disallowed tools, otherwise 1 |
| Task success | Target’s structured success result, or a conservative metric-derived fallback |
| Unanswerable handling | Safe abstention/escalation for cases labeled unanswerable |
| Cost and latency | Target-reported usage/cost and p50/p95 sample latency |

Aggregate values are macro means. Reports also split by category and provide fixed-seed bootstrap intervals. These lexical defaults are transparent CI proxies, not claims of semantic equivalence. A semantic judge/Ragas integration should be calibrated against human labels before use.

