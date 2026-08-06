# HelpDesk Manager (unificado)

## ¿Qué hace?

Plataforma interna que unifica 6 apps del ecosistema (helpdesk, insumos, liquidaciones,
vacaciones, parque de impresoras, monitoreo STC) en un solo monolito modular.

## Estado

En construcción. Ver `INTEGRACION_APPS_PLAN.md` (plan maestro de la unificación) y
`ARCHITECTURE_GUIDE.md` (norma de arquitectura y código) en esta misma carpeta — léelos
completos antes de tocar código. El plan de implementación del módulo `auth` (fundaciones)
vive en `C:\Users\imartinez.CDSA\.claude\plans\idempotent-pondering-graham.md`.

## Setup rápido

```bash
cp .env.example .env
cd backend && uv sync --frozen
docker compose up -d db
uv run alembic upgrade head
uv run uvicorn src.shared.presentation.app:app --reload
```

```bash
cd frontend && npm install
npm run dev
```

## Arquitectura

Backend FastAPI (Python 3.12) como monolito modular: `src/modules/<módulo>/{domain,
application,infrastructure,presentation}/`, más `src/shared/` para lo transversal
(config, errores, DB, middlewares). Frontend Next.js (App Router) + Tailwind. Un solo
Postgres autoalojado en contenedor (Portainer / red corporativa, sin exposición pública).
Ver ADRs en `docs/adr/` para las decisiones de arquitectura y por qué.

## Tests

```bash
cd backend && uv run pytest
```

## Variables de entorno

Ver `.env.example` — agrupado por módulo de dominio. Ninguna variable tiene un valor
secreto real en ese archivo (ver `ARCHITECTURE_GUIDE.md` §8).
