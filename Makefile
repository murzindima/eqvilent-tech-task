.PHONY: install test clean shell venv format lint organize all_checks docker_build docker_run docker_clean

install:
	poetry install

test:
	poetry run pytest -vvvs

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache

shell:
	poetry shell

venv: shell

format:
	poetry run black .

organize:
	poetry run isort .

lint:
	poetry run ruff check .

all_checks: format organize lint
	@echo "All formatting, organizing, and linting checks completed."

docker_build:
	docker build -t diff_k8s_manifests .

docker_run:
	docker run --rm diff_k8s_manifests

docker_clean:
	docker rmi diff_k8s_manifests