FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
RUN uv run playwright install --with-deps chromium

COPY . .

EXPOSE 8012

CMD ["uv", "run", "uvicorn", "src.shared.presentation.app:app", "--host", "0.0.0.0", "--reload", "--port", "8012"]
