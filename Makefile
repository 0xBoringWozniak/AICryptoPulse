VENV := venv

ifeq ($(OS),Windows_NT)
   BIN=$(VENV)/Scripts
else
   BIN=$(VENV)/bin
endif

export PATH := $(BIN):$(PATH)

# Change this to actual service name (e.g. bot, service, etc.)
PROJECT := bot
TESTS := tests
REQUIREMENTS := $(PROJECT)/requirements.txt

# Debug
print-paths:
	@echo "Project: $(PROJECT)"
	@echo "Tests directory: $(TESTS)"
	@echo "Requirements file: $(REQUIREMENTS)"

# Clean all artifacts
clean:
	rm -rf $(VENV) || true
	find . -name __pycache__ -exec rm -rf {} \; || true
	find . -name .pytest_cache -exec rm -rf {} \; || true
	find . -name .mypy_cache -exec rm -rf {} \; || true
	find . -name .coverage -exec rm -rf {} \; || true
	find . -name '*runs' -exec rm -rf {} \; || true
	find . -name '*mlruns' -exec rm -rf {} \; || true
	find . -name '*mlartifacts' -exec rm -rf {} \; || true
	find . -name .ipynb_checkpoints -exec rm -rf {} \; || true
	find . -name '*loader' -exec rm -rf {} \; || true
	find . -name '*_cache' -exec rm -rf {} \; || true
	find . -name '*_output' -exec rm -rf {} \; || true
	find . -name '*_logs' -exec rm -rf {} \; || true
	find . -name '*_data' -exec rm -rf {} \; || true
	find . -name '*_results' -exec rm -rf {} \; || true
	find . -name '*build' -exec rm -rf {} \; || true
	find . -name 'dist' -exec rm -rf {} \; || true
	find . -name '*.egg-info' -exec rm -rf {} \; || true


# Setup
.venv:
	cd $(PROJECT) && python3 -m venv $(VENV)
	pip3 install -r $(REQUIREMENTS)
	pip3 install flake8 isort mypy pylint

setup: .venv


# Format
isort_fix: .venv
	isort $(PROJECT) $(TESTS)

format: isort_fix


# Lint
isort: .venv
	isort --check --skip $(VENV) $(PROJECT) $(TESTS)

flake: .venv
	flake8 $(PROJECT) $(TESTS) --exclude=$(VENV)

mypy: .venv
	mypy $(PROJECT) $(TESTS) --exclude $(VENV)

pylint: .venv
	pylint $(PROJECT) $(TESTS) --ignore-paths=$(VENV) --disable=C0116,C0115,C0114,C0301


lint: isort flake pylint


# Test
.pytest:
	pytest -s -v

test: .venv .pytest


# Docker
build:
	docker-compose build

run: build
	docker-compose up -d

# All
dev: setup format lint test
all: setup format lint test run

.DEFAULT_GOAL = run
