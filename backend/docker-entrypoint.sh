#!/bin/sh
set -e

uv run alembic upgrade head
exec uv run uvicorn src.shared.presentation.app:app --host 0.0.0.0 --port 8012
