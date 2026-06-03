.PHONY: help run setup install format format-check lint test check
.PHONY: pre-commit-install pre-commit-run
.PHONY: docker-build docker-up docker-up-build docker-down docker-restart
.PHONY: docker-logs docker-ps docker-init docker-shell-airflow
.PHONY: docker-volume-init

PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
PRE_COMMIT ?= .venv/bin/pre-commit
PRE_COMMIT_HOME ?= .cache/pre-commit
DOCKER_COMPOSE ?= docker compose
CODE_PATHS := infra/airflow/dags infra/airflow/scripts infra/airflow/tasks apps/api apps/bot tests

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
	@echo "  make api-dev            Run the FastAPI chatbot backend locally"
	@echo "  make bot-dev            Run the Discord bot locally"
	@echo "  make docker-volume-init Create persistent Docker volumes"
	@echo "  make docker-init        Run setup, build, and start services"
	@echo "  make install            Install Python dependencies into .venv"
	@echo "  make format             Format Python code with Ruff"
	@echo "  make format-check       Check Python code formatting with Ruff"
	@echo "  make lint               Lint Python code with Ruff"
	@echo "  make lint-check         Check Python code with Ruff"
	@echo "  make test               Run pytest"
	@echo "  make check              Run format-check, lint, and test"

run: setup docker-up-build
	@set -a; \
	if [ -f .env ]; then . ./.env; fi; \
	set +a; \
	echo ""; \
	echo "JobFlow is starting."; \
	echo "Open these URLs after the containers are healthy:"; \
	echo "  Airflow:       http://localhost:$${AIRFLOW_WEBSERVER_PORT:-8080}"; \
	echo "  Trino:         http://localhost:$${TRINO_HOST_PORT:-8081}"; \
	echo "  MinIO Console: http://localhost:$${MINIO_CONSOLE_PORT:-9001}"; \
	echo "  Chroma:        http://localhost:$${CHROMA_HOST_PORT:-8000}"; \
	echo "  Chatbot API:   http://localhost:$${API_HOST_PORT:-8100}"; \
	echo ""; \
	echo "Useful next commands:"; \
	echo "  make docker-ps"; \
	echo "  make docker-logs"; \
	echo "  make docker-down"

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
	$(PYTHON) -m ruff format $(CODE_PATHS)

format-check:
	$(PYTHON) -m ruff format --check $(CODE_PATHS)

lint:
	$(PYTHON) -m ruff check $(CODE_PATHS) --fix

lint-check:
	$(PYTHON) -m ruff check $(CODE_PATHS)

test:
	$(PYTHON) -m pytest

pre-commit-install:
	PRE_COMMIT_HOME=$(PRE_COMMIT_HOME) $(PRE_COMMIT) install

pre-commit-run:
	PRE_COMMIT_HOME=$(PRE_COMMIT_HOME) $(PRE_COMMIT) run --all-files

check: format-check lint test

docker-build:
	$(DOCKER_COMPOSE) build

docker-volume-init:
	@set -a; \
	if [ -f .env ]; then . ./.env; fi; \
	set +a; \
	for volume in \
		$${POSTGRES_VOLUME_NAME:-jobflow_postgres_data} \
		$${MINIO_VOLUME_NAME:-jobflow_minio_data} \
		$${CHROMA_VOLUME_NAME:-jobflow_chroma_data} \
		$${MONGODB_VOLUME_NAME:-jobflow_mongodb_data}; do \
		docker volume inspect $$volume >/dev/null 2>&1 || docker volume create $$volume >/dev/null; \
	done

docker-up: docker-volume-init
	$(DOCKER_COMPOSE) up -d

docker-up-build: docker-volume-init
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

api-dev:
	PYTHONPATH=apps $(PYTHON) -m uvicorn api.main:app --host 0.0.0.0 --port 8100 --reload

bot-dev:
	PYTHONPATH=apps $(PYTHON) -m bot.main
