---
description: Run a failure experiment — predict, break, observe, fix
---
Design a failure experiment for the current milestone. $ARGUMENTS

1. Describe the failure in one line (e.g. "LLM returns invalid JSON", "tool times out", "vector index missing").
2. Ask me to PREDICT what will happen. Wait for my answer.
3. Run the experiment (safely — never touch real systems, never delete data without asking).
4. Show what really happened: logs, error, trace.
5. Compare my prediction to reality.
6. If the system didn't handle it well, help me add the fix (I write the core fix as a LEARNER TASK).
7. Add it to the README "Failure demos" section with the command to reproduce it.
