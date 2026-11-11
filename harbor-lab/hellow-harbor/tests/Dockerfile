FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv

RUN uv pip install --system \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

RUN mkdir -p /app /logs/verifier

WORKDIR /app

COPY . /tests/

RUN chmod +x /tests/test.sh