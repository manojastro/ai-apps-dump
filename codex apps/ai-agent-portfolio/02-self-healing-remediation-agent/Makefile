PYTHON ?= python

.PHONY: setup dev test eval seed smoke lint web-build compose-check sandbox sandbox-destroy
setup:
	$(PYTHON) -m venv .venv
	.venv/Scripts/python -m pip install -e ".[test]"
	cd apps/web && npm install
dev:
	$(PYTHON) -m uvicorn app.main:app --reload --port 8002
test:
	$(PYTHON) -m pytest -q
eval:
	$(PYTHON) -m app.evaluation --output reports/evaluation.json --markdown reports/evaluation.md
seed:
	curl -X POST http://localhost:8002/api/admin/seed -H "Authorization: Bearer demo-operator-token" -H "X-CSRF-Token: demo-csrf-token"
smoke:
	$(PYTHON) scripts/smoke.py
lint:
	$(PYTHON) -m compileall -q apps/api services
web-build:
	cd apps/web && npm run build
compose-check:
	docker compose config -q
sandbox:
	powershell -ExecutionPolicy Bypass -File scripts/create-sandbox.ps1
sandbox-destroy:
	powershell -ExecutionPolicy Bypass -File scripts/destroy-sandbox.ps1
