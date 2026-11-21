.PHONY: demo up down dev backend frontend test eval seed lint docker-build

PY := .venv/bin/python
PIP := .venv/bin/pip
UVICORN := .venv/bin/uvicorn
PYTEST := .venv/bin/pytest
export PYTHONPATH := $(PWD)/backend
export PATH := $(HOME)/.local/node/bin:$(PATH)

demo: seed
	@echo "Starting DataSentinel AI (backend :8000, frontend :3000)"
	@$(MAKE) -j2 backend frontend

seed:
	@mkdir -p data
	$(PY) scripts/seed_demo.py

backend:
	$(UVICORN) app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

dev: demo

test:
	$(PYTEST) tests -q --tb=short

eval:
	$(PY) evaluation/run_eval.py

up:
	docker compose up --build

down:
	docker compose down

docker-build:
	docker compose build

lint:
	$(PY) -m compileall backend scripts evaluation tests
