.PHONY: run-frontend run-backend add-backend-deps add-backend-dev-deps clean-backend lint-backend format-backend

NPM ?= npm
UV ?= uv
DEPS ?=

run-frontend:
	cd frontend && $(NPM) run web

run-backend:
	cd backend && $(UV) run fastapi dev app/main.py

add-backend-deps:
	@if [ -z "$(DEPS)" ]; then \
		echo 'Usage: make add-backend-deps DEPS="pkg1 pkg2" [UV=uv]'; \
		exit 1; \
	fi
	cd backend && $(UV) add $(DEPS)

add-backend-dev-deps:
	@if [ -z "$(DEPS)" ]; then \
		echo 'Usage: make add-backend-dev-deps DEPS="pkg1 pkg2" [UV=uv]'; \
		exit 1; \
	fi
	cd backend && $(UV) add $(DEPS) --dev

lint-backend:
	cd backend && $(UV) run zuban check && $(UV) run ruff check

format-backend:
	cd backend && $(UV) run ruff format

clean-backend:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
