FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /usr/app

COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt
