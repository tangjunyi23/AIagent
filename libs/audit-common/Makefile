.PHONY: test lint format

TEST ?= tests
PYTHON ?= python3
PYTHON_FILES = audit_common tests

test:
	$(PYTHON) -m unittest discover tests -v

lint:
	$(PYTHON) -m compileall -q audit_common tests

format:
	$(PYTHON) -m compileall -q audit_common tests
