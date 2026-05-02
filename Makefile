PYTHON = python3
CONFIG = config.txt

install:
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
	$(PYTHON) -m pip install flake8 mypy build
	$(PYTHON) -m pip install -e .

run:
	$(PYTHON) a_maze_ing.py $(CONFIG)

debug:
	$(PYTHON) -m pdb a_maze_ing.py $(CONFIG)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf dist/ build/ *.egg-info/ 2>/dev/null || true

lint:
	flake8 . --max-line-length=99 --exclude=dist,build,.venv
	$(PYTHON) -m mypy . --warn-return-any --warn-unused-ignores \
	        --ignore-missing-imports --disallow-untyped-defs \
	        --check-untyped-defs

lint-strict:
	flake8 . --max-line-length=99 --exclude=dist,build,.venv
	$(PYTHON) -m mypy . --strict --ignore-missing-imports
build-package:
	$(PYTHON) -m build

.PHONY: install run debug clean lint lint-strict build-package