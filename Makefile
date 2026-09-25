.PHONY: test demo scenario

PYTHON ?= python3
VENV_PY := .venv/bin/python

test: $(VENV_PY)
	$(VENV_PY) -m pytest

demo: $(VENV_PY)
	$(VENV_PY) -m jobshop.demo

scenario: $(VENV_PY)
	$(VENV_PY) -m jobshop.scenario

$(VENV_PY):
	$(PYTHON) -m venv .venv
	$(VENV_PY) -m pip install --quiet -e ".[dev]"
