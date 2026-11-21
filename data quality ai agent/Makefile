.PHONY: install up down demo test eval

install:
	uv sync --frozen
	npm --prefix frontend ci

up:
	docker compose up --build -d

down:
	docker compose down

demo:
	uv run python scripts/demo.py

test:
	uv run ruff check backend simulator evals
	uv run mypy
	uv run pytest -q
	npm --prefix frontend run lint
	npm --prefix frontend test
	npm --prefix frontend run build

eval:
	uv run python -m evals.run --persist
