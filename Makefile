.PHONY: setup backend frontend test seed osm

setup:
	cd backend && uv venv --python 3.12 && . .venv/bin/activate && uv pip install -e ".[dev]"
	cd frontend && npm install

backend:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

test:
	cd backend && . .venv/bin/activate && python -m pytest
	cd frontend && npm run build

seed:
	cd backend && . .venv/bin/activate && python -m app.seed

# Download OpenStreetMap data for the pilot city and write docs/data-audit-<city>.md
osm:
	cd backend && . .venv/bin/activate && python -m app.osm_fetch
