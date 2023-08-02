install:
	pip install --upgrade pip-tools pip setuptools
	python3.10 -m piptools compile -o requirements/main.txt pyproject.toml
	python3.10 -m piptools compile --extra dev -o requirements/dev.txt pyproject.toml
	pip install -r requirements/main.txt -r requirements/dev.txt

update-deps:
	pip install --upgrade pip-tools pip setuptools
	python3.10 -m piptools compile --upgrade --resolver backtracking -o requirements/main.txt pyproject.toml
	python3.10 -m piptools compile --extra dev --upgrade --resolver backtracking -o requirements/dev.txt pyproject.toml

init:
	pip install --editable .
	pip install --upgrade -r requirements/main.txt  -r requirements/dev.txt

update: update-deps init

format:
	black --exclude ^/venv .
