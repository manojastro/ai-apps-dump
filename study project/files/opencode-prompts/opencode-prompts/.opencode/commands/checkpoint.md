---
description: Close the current milestone — test, explain, quiz, log, commit
---
Close the current milestone using the learning loop in AGENTS.md:

1. Run lint (`uv run ruff check .`), types (`uv run mypy src`), and tests (`uv run pytest -q`). Show the real output.
2. If anything fails, stop and help me fix it. Do not continue.
3. Check every LEARNER TASK in this milestone is done by me (not by you).
4. Give me the "How this works" section: plain English, a small diagram, one IT-ops analogy.
5. Ask me 3 quiz questions (concept, debugging, interview). Wait for my answers, then grade them.
6. Append the milestone entry to LEARNING_LOG.md using the template in AGENTS.md.
7. Suggest a Conventional Commit message and commit after I say ok.
8. Show the milestone status table. Then stop.
