PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
ARGS ?=

.DEFAULT_GOAL := help

.PHONY: help install run test coverage lint format format-check check

help:
	@echo "make install       — создать окружение и установить инструменты"
	@echo "make run           — запустить программу с интерактивным вводом"
	@echo "make run ARGS='--text мама' — передать аргументы программе"
	@echo "make test          — запустить unit-тесты"
	@echo "make coverage      — проверить покрытие без сохранения артефактов"
	@echo "make lint          — проверить стиль кода"
	@echo "make format        — отформатировать Python-код"
	@echo "make format-check  — проверить форматирование без изменений"
	@echo "make check         — проверить стиль, форматирование и покрытие"

$(VENV_PYTHON):
	$(PYTHON) -m venv $(VENV)

install: $(VENV_PYTHON)
	$(VENV_PYTHON) -m pip install -r requirements.txt

run: $(VENV_PYTHON)
	$(VENV_PYTHON) -m tandem_repeat $(ARGS)

test: $(VENV_PYTHON)
	$(VENV_PYTHON) -m pytest -q

# Для coverage и ruff сначала выполните make install.
# Данные покрытия хранятся во временном файле до завершения команды.
coverage: $(VENV_PYTHON)
	@COVERAGE_FILE=$$(mktemp); export COVERAGE_FILE; \
	trap 'rm -f "$$COVERAGE_FILE"' EXIT; \
	export COVERAGE_RCFILE=/dev/null; \
	$(VENV_PYTHON) -m coverage run --branch --source=tandem_repeat \
		-m pytest -q && \
	$(VENV_PYTHON) -m coverage report --show-missing --fail-under=95

lint: $(VENV_PYTHON)
	$(VENV_PYTHON) -m ruff check --isolated --line-length 79 \
		--target-version py310 --select E,F,I,W .

format: $(VENV_PYTHON)
	$(VENV_PYTHON) -m ruff format --isolated --line-length 79 \
		--target-version py310 .

format-check: $(VENV_PYTHON)
	$(VENV_PYTHON) -m ruff format --isolated --check --line-length 79 \
		--target-version py310 .

check: lint format-check coverage
