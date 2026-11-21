# DEMO — AgentJudge in 90 seconds (offline, $0)

1. (10s) "AgentJudge tests any AI endpoint against 50 frozen questions and
   blocks bad releases. All data is synthetic; runs offline."
   `uv run python scripts/check_balance.py`
2. (25s) "Run the full set against the mock target:"
   `uv run agentjudge run --target stub --set golden_set.jsonl`
   "JSON for machines, Markdown for humans — see reports/."
3. (20s) "Compare and gate — this is the CAB check, automatic:"
   `uv run agentjudge compare reports/run_stub_<date>.json reports/baseline.json`
   `uv run agentjudge gate reports/run_stub_<date>.json --baseline reports/baseline.json`
4. (20s) "We calibrate the judge against 20 human labels:"
   `uv run agentjudge calibrate --human labels/human_20.jsonl --judge reports/run_stub_<date>.json`
   "Kappa tells us agreement beyond luck."
5. (15s) "Trust: `--repeat 3` shows spread; deltas under 0.02 are noise.
   Total cost: $0."
