PYTHON=python3.10

install:
	pip install --upgrade pip-tools pip setuptools
	$(PYTHON) -m piptools compile -o requirements/main.txt pyproject.toml
	$(PYTHON) -m piptools compile --extra dev -o requirements/dev.txt pyproject.toml
	pip install -r requirements/main.txt -r requirements/dev.txt

update-deps:
	pip install --upgrade pip-tools pip setuptools
	$(PYTHON) -m piptools compile --upgrade --resolver backtracking -o requirements/main.txt pyproject.toml
	$(PYTHON) -m piptools compile --extra dev --upgrade --resolver backtracking -o requirements/dev.txt pyproject.toml

init:
	pip install --editable .
	pip install --upgrade -r requirements/main.txt  -r requirements/dev.txt

update: update-deps init

format:
	black --exclude ^/venv .

start-docker-colima:
	colima start

stop-docker-colima:
	colima stop

build-image:
	docker build -f Dockerfile -t innholdsmengde .

build-local-image:
	docker build -f Dockerfile.local -t innholdsmengde_local .