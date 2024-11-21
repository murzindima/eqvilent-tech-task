FROM python:3.13-alpine

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

COPY . /app/

ENTRYPOINT ["python", "diff_k8s_manifests.py"]
