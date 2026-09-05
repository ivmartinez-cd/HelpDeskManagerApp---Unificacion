#!/bin/sh
set -e

uv run alembic upgrade head
# --no-server-header: no anunciar "server: uvicorn". La IP real detrás del proxy
# inverso la resuelve uvicorn con X-Forwarded-For, pero solo desde las IPs de
# FORWARDED_ALLOW_IPS (variable de entorno que uvicorn lee solo; ver .env.example).
exec uv run uvicorn src.shared.presentation.app:app --host 0.0.0.0 --port 8012 \
    --proxy-headers --no-server-header
