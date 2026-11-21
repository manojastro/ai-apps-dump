.PHONY: setup dev test eval seed lint gate compose-up compose-down

setup:
	python -m pip install -e ".[dev]"

dev:
	uvicorn evalharness.api:app --reload --port 8004

test:
	pytest

eval:
	python -m evalharness.cli seed
	python -m evalharness.cli run --mode good --output reports/good.json

seed:
	python -m evalharness.cli seed

lint:
	ruff check apps tests examples

gate:
	python -m evalharness.cli gate --candidate reports/good.json --config config/gates.yml

compose-up:
	docker compose up --build

compose-down:
	docker compose down

