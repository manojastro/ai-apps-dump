.PHONY: setup dev up down seed incident eval test test-e2e lint

setup:
	cd backend && uv sync --extra dev
	cd frontend && npm install

dev:
	cd backend && uv run uvicorn app.main:app --reload --port 8003

up:
	docker compose up --build

down:
	docker compose down

seed:
	cd backend && uv run python -m app.seed

incident:
	cd backend && uv run python -m app.incident_generator --scenario misleading-signal --investigate

eval:
	cd backend && uv run python -m app.evaluation --output ../evaluation/reports

test:
	cd backend && uv run pytest

test-e2e:
	cd frontend && npm run test:e2e

lint:
	cd backend && uv run ruff check app tests
	cd frontend && npm run typecheck
