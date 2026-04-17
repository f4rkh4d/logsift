.PHONY: install test lint

install:
	python -m pip install -e ".[dev]"

test:
	pytest -q

lint:
	python -m compileall -q src tests
