.PHONY: test lint format

TEST ?= tests
PYTHON ?= python3
PYTHONPATH ?= .:../../libs/audit-common:../audit-agents
PYTHON_FILES = audit_api tests

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest discover tests -v

lint:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m compileall -q audit_api tests

format:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m compileall -q audit_api tests
