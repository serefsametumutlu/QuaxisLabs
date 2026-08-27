.PHONY: test lint typecheck repaint-all

test:
	pytest -q

lint:
	ruff check .
	python -m tlab.cli lint

typecheck:
	mypy tlab

repaint-all:
	python -m tlab.cli lint
	pytest -q -k repaint
