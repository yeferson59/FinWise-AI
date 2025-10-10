.PHONY: run-frontend run-backend add-backend-deps add-backend-dev-deps

NPM ?= npm
UV ?= uv
DEPS ?=

run-frontend:
	cd frontend && $(NPM) run web

run-backend:
	cd backend && $(UV) run fastapi dev main.py

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
