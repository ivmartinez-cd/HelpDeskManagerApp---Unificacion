# HelpDesk Manager — Backend

## ¿Qué hace?

API FastAPI (Python 3.12) del monolito modular que unifica las apps del ecosistema:
auth, insumos, contadores, liquidaciones, vacaciones, sla, prestadores, turnos,
preventivos y analisis-log-hp.

## Setup rápido

Desde la raíz del repo (todo containerizado; las migraciones Alembic corren en el
entrypoint):

```bash
cp .env.example .env
docker compose up -d --build backend
```

Sin hot reload: tras editar código, `docker restart helpdesk-manager-backend`.
Para cambios de `.env`: `docker compose up -d --force-recreate backend` (un
`restart` no relee el entorno). En dev, `DISABLE_BACKGROUND_JOBS=true` siempre —
los jobs de fondo mandan mails reales (ver CLAUDE.md).

## Arquitectura

Monolito modular módulo→capa (`src/modules/<módulo>/{domain,application,
infrastructure,presentation}/` + `src/shared/` transversal), con dependencias
Presentation → Application → Domain ← Infrastructure verificadas por
`import-linter`. Norma completa en `docs/ARCHITECTURE_GUIDE.md`; decisiones y
excepciones en `docs/adr/` (la 003 justifica esta estructura).

## Tests y gates

Dentro del contenedor — los cuatro tienen que pasar antes de dar algo por
terminado:

```bash
docker exec helpdesk-manager-backend uv run lint-imports
docker exec helpdesk-manager-backend uv run ruff check src tests
docker exec helpdesk-manager-backend uv run mypy src
docker exec helpdesk-manager-backend uv run pytest tests/unit -q
```

`tests/integration` requiere la DB de test (puerto `DB_TEST_PORT`).

## Variables de entorno

Ver `.env.example` en la raíz (cubre todos los campos de
`src/shared/infrastructure/config/settings.py`, agrupado por módulo; sin valores
secretos reales). Las credenciales van solo por `.env` — nunca como defaults en
`settings.py` (§8 de la guía).
