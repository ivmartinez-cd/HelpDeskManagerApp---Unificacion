# HelpDesk Manager (unificado)

## ¿Qué hace?

Plataforma interna que unifica 6 apps del ecosistema (helpdesk, insumos, liquidaciones,
vacaciones, parque de impresoras, monitoreo STC) en un solo monolito modular.

## Estado

En construcción. Ver `docs/INTEGRACION_APPS_PLAN.md` (plan maestro de la unificación) y
`docs/ARCHITECTURE_GUIDE.md` (norma de arquitectura y código) — léelos completos antes
de tocar código.

## Setup rápido

Todo en Docker (DB + backend + frontend — recomendado para desarrollo local):

```bash
cp .env.example .env
docker compose up -d --build
```

Frontend en `http://localhost:3000`, backend en `http://localhost:8012`.

**Sin hot reload — decisión deliberada** (ver CLAUDE.md): el código está bind-monteado
pero editar un archivo no tiene efecto hasta reiniciar el contenedor
(`docker restart helpdesk-manager-backend` / `helpdesk-manager-frontend`; el del
frontend re-corre el build completo). `docker restart` NO relee `.env` — para cambios
de variables de entorno: `docker compose up -d --force-recreate <servicio>`.

Alternativa sin Docker para backend/frontend (solo la DB containerizada). Atención:
nunca usar `--reload` de uvicorn en este repo — puede relanzar los background jobs en
cada guardado con efectos reales (mails); mantener `DISABLE_BACKGROUND_JOBS=true`:

```bash
cd backend && uv sync --frozen
docker compose up -d db
uv run alembic upgrade head
uv run uvicorn src.shared.presentation.app:app --port 8012
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
