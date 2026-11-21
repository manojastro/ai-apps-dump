.PHONY: demo evals redteam test install browser-install

install:
	uv sync --group dev
	uv run playwright install chromium

test:
	uv run pytest -q

demo:
	uv run python -m sentinel.demo_planner

evals:
	uv run python evals/run_evals.py

redteam:
	uv run python evals/run_evals.py --redteam-only
