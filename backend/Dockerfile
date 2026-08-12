FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Driver ODBC de Microsoft para SQL Server — lo necesita pyodbc (módulo sla,
# consulta en vivo a Siges/MERCURIO). La clave es la de 2025: el repo de
# Debian 13 ya no está firmado con la microsoft.asc clásica.
RUN apt-get update && apt-get install -y --no-install-recommends curl gnupg2 \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft-2025.asc \
        | gpg --batch --yes --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/13/prod trixie main" \
        > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 unixodbc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
RUN uv run playwright install --with-deps chromium

COPY . .
RUN chmod +x docker-entrypoint.sh

EXPOSE 8012

# Corre las migraciones pendientes antes de levantar uvicorn — evita el
# desincronismo entre el código (git pull) y el schema/datos de cada máquina
# de dev (cada una tiene su propio Postgres local, no sincronizado).
ENTRYPOINT ["./docker-entrypoint.sh"]
