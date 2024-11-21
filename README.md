
# Kubernetes Manifests Diff Tool

This is a simple tool to compare Kubernetes YAML manifests and identify differences in the resources.

## Disclaimer

I have chosen to keep everything in a single file for simplicity's sake. Given the relatively small scope of the project, this approach helps maintain readability and keeps things easy to follow. Splitting the code into multiple files would add unnecessary complexity without a significant benefit at this stage. The main focus is clarity and ease of understanding rather than over-engineering the structure.

## Features

- Compares Kubernetes manifests in YAML format.
- Outputs differences in `added`, `removed`, and `changed` sections.
- Supports running tests using `pytest`.
- Includes linting, formatting, and code organization with `black`, `ruff`, and `isort`.
- Docker support for running the tool inside a container.

## Installation

You can install the necessary dependencies using [Poetry](https://python-poetry.org/):

```shell
poetry install
```

To activate the Poetry shell (virtual environment):

```shell
poetry shell
# or
make shell
# or
make venv
```

## Configuration

| Variable    | Description                                | Default Value | Possible Values                    | Type   |
|-------------|--------------------------------------------|---------------|------------------------------------|--------|
| `LOG_FORMAT`| Specifies the format of log output         | `text`        | `text`, `json`                     | String |
| `LOG_LEVEL` | Sets the logging level for the application | `INFO`        | `DEBUG`, `INFO`, `WARNING`, `ERROR`| String |

## Usage

To run the tool and compare two YAML files:

```shell
poetry run python diff_k8s_manifests.py <file_current.yaml> <file_desired.yaml>
```

### Docker Usage

You can also run the tool using Docker.

1. **Build the Docker image:**

    ```shell
    make docker_build
    # or
    docker build -t diff_k8s_manifests .
    ```

2. **Run the Docker container:**

    ```shell
    make docker_run
    # or
    docker run --rm diff_k8s_manifests
    ```

3. **Clean up the Docker image:**

    ```shell
    make docker_clean
    # or
    docker rmi diff_k8s_manifests
    ```

## Testing

You can run tests using `pytest`:

```shell
make test
# or
poetry run pytest -vvvs
# or
poetry run pytest -vvvs tests/
```

## Linting, Formatting, and Organizing

We use `black`, `ruff`, and `isort` to ensure code quality.

- To format the code with `black`:

    ```shell
    make format
    # or
    poetry run black .
    ```

- To organize imports with `isort`:

    ```shell
    make organize
    # or
    poetry run isort .
    ```

- To lint the code with `ruff`:

    ```shell
    make lint
    # or
    poetry run ruff check .
    ```

- To run all checks (formatting, organizing, and linting):

    ```shell
    make all_checks
    ```

## Cleaning

To clean up compiled Python files and other temporary files:

```shell
make clean
# or
find . -name '*.pyc' -delete
find . -name '__pycache__' -delete
rm -rf .pytest_cache
rm -rf .ruff_cache
```

## Roadmap

- **Add CI/CD**: Implement a continuous integration and continuous delivery pipeline to automatically test and deploy the project.
  
- **Add Kubernetes Object Validation**: Introduce validation to ensure that the `kind` and `apiVersion` fields are handled correctly and that the system can recognize and validate Kubernetes objects based on their type.
  
- **Enhance Test Coverage**: Improve the test suite by adding more scenarios to ensure all possible edge cases are covered.
  
- **Improve Logging and Error Handling**: Refine the logging system and add more granular error handling to better trace issues during execution.

- **Documentation Expansion**: Provide more detailed documentation around the usage, edge cases, and common pitfalls of the project.
