.PHONY: test lint api-test web-test dev up bootstrap

bootstrap:
	./scripts/bootstrap.sh

dev:
	docker compose -f docker-compose.dev.yml up --build

up:
	docker compose up --build -d

api-test:
	cd apps/api && MR9_SECRET_KEY=$${MR9_SECRET_KEY:-unit-test-secret-key-please-change} MR9_DATABASE_URL=$${MR9_DATABASE_URL:-sqlite+pysqlite:///:memory:} PYTHONPATH=. python3 -m pytest -q --tb=short

web-test:
	cd apps/web && npm test --if-present && npx tsc --noEmit

lint:
	cd apps/api && python3 -m ruff check app tests || true
	cd apps/web && npm run lint --if-present

test: api-test web-test
