.PHONY: test lint format

TEST ?= tests
PYTHON ?= python3
PYTHONPATH ?= .:../../libs/audit-common
PYTHON_FILES = audit_agents tests

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest discover tests -v

lint:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m compileall -q audit_agents tests

format:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m compileall -q audit_agents tests
