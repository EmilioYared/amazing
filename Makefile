# A-Maze-ing — project automation.
# PYTHON defaults to python3; override with `make PYTHON=python` on
# systems where only `python` exists (e.g. Windows).

PYTHON ?= python3
CONFIG ?= config.txt

MYPY_FLAGS = --warn-return-any --warn-unused-ignores \
	--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

.DEFAULT_GOAL := run
.PHONY: install run debug clean lint lint-strict package help

help:
	@echo "Targets: install run debug clean lint lint-strict package"

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install build wheel flake8 mypy
	$(PYTHON) -m pip install -e .

run:
	$(PYTHON) a_maze_ing.py $(CONFIG)

debug:
	$(PYTHON) -m pdb a_maze_ing.py $(CONFIG)

lint:
	flake8 .
	mypy . $(MYPY_FLAGS)

lint-strict:
	flake8 .
	mypy . --strict

package:
	$(PYTHON) -m build --wheel
	cp dist/mazegen-1.0.0-py3-none-any.whl .

clean:
	rm -rf build dist *.egg-info src/*.egg-info
	rm -rf .mypy_cache .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
