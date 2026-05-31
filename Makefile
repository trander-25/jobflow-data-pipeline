.PHONY: help run setup install format format-check lint test check
.PHONY: pre-commit-install pre-commit-run
.PHONY: docker-build docker-up docker-up-build docker-down docker-restart
.PHONY: docker-logs docker-ps docker-init docker-shell-airflow

PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
PRE_COMMIT ?= .venv/bin/pre-commit
PRE_COMMIT_HOME ?= .cache/pre-commit
DOCKER_COMPOSE ?= docker compose
CODE_PATHS := airflow/dags airflow/scripts airflow/tasks

help:
	@echo "Available commands:"
	@echo "  make run                Run the project from A to Z"
	@echo "  make setup              Create .env from .env.example when missing"
	@echo "  make docker-up-build    Build images and start all services"
	@echo "  make docker-up          Start all services"
	@echo "  make docker-down        Stop all services"
	@echo "  make docker-restart     Restart all services"
	@echo "  make docker-logs        Follow logs from all services"
	@echo "  make docker-ps          Show service status"
	@echo "  make docker-init        Run setup, build, and start services"
	@echo "  make install            Install Python dependencies into .venv"
	@echo "  make format             Format Python code with Black"
	@echo "  make lint               Lint Python code with Flake8"
	@echo "  make test               Run pytest"
	@echo "  make check              Run format-check, lint, and test"

run: setup docker-up-build
	@echo ""
	@echo "JobFlow is starting."
	@echo "Open these URLs after the containers are healthy:"
	@echo "  Airflow:       http://localhost:8080"
	@echo "  Trino:         http://localhost:8081"
	@echo "  MinIO Console: http://localhost:9001"
	@echo ""
	@echo "Useful next commands:"
	@echo "  make docker-ps"
	@echo "  make docker-logs"
	@echo "  make docker-down"

setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env from .env.example"; \
	else \
		echo ".env already exists"; \
	fi

install:
	$(PIP) install -r requirements.txt

format:
	find $(CODE_PATHS) -type f -name '*.py' -print0 | xargs -0 -n 1 $(PYTHON) -m black

format-check:
	find $(CODE_PATHS) -type f -name '*.py' -print0 | xargs -0 -n 1 $(PYTHON) -m black --check

lint:
	$(PYTHON) -m flake8 $(CODE_PATHS)

test:
	$(PYTHON) -m pytest

pre-commit-install:
	PRE_COMMIT_HOME=$(PRE_COMMIT_HOME) $(PRE_COMMIT) install

pre-commit-run:
	PRE_COMMIT_HOME=$(PRE_COMMIT_HOME) $(PRE_COMMIT) run --all-files

check: format-check lint test

docker-build:
	$(DOCKER_COMPOSE) build

docker-up:
	$(DOCKER_COMPOSE) up -d

docker-up-build:
	$(DOCKER_COMPOSE) up -d --build

docker-down:
	$(DOCKER_COMPOSE) down

docker-restart:
	$(DOCKER_COMPOSE) restart

docker-logs:
	$(DOCKER_COMPOSE) logs -f

docker-ps:
	$(DOCKER_COMPOSE) ps

docker-init: setup docker-up-build

docker-shell-airflow:
	$(DOCKER_COMPOSE) exec airflow-webserver bash
