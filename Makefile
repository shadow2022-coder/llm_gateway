PYTHON ?= .venv/bin/python
HOST ?= 0.0.0.0
PORT ?= 8000
BASE_URL ?= http://127.0.0.1:8000
OWNER ?= local-dev

.PHONY: setup run test lint create-key smoke compose-up

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	cp -n .env.example .env || true

run:
	$(PYTHON) -m uvicorn app.main:app --host $(HOST) --port $(PORT) --reload

test:
	$(PYTHON) -m pytest -q

create-key:
	$(PYTHON) scripts/create_api_key.py --owner $(OWNER)

smoke:
	$(PYTHON) scripts/live_smoke_test.py --base-url $(BASE_URL) --api-key $(API_KEY)

compose-up:
	cp -n .env.example .env || true
	docker compose up --build

lint:
	@echo "lint target placeholder"
