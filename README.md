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

Frontend en `http://localhost:3000`, backend en `http://localhost:8012`. DB, backend y
Mailpit escuchan solo en `127.0.0.1`; desde otras PCs de la LAN se entra únicamente al
frontend (ver CLAUDE.md, "Acceso desde otras máquinas").

**Recarga** (ver CLAUDE.md): el frontend corre `next dev` y se recompila solo al guardar.
El backend corre **sin** `--reload` a propósito (los jobs de fondo tienen efectos reales):
tras editar `backend/`, `bash scripts/wsl/reiniciar.sh backend`. `docker restart` NO relee
`.env` — para cambios de variables de entorno: `docker compose up -d --force-recreate <servicio>`.

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

## Tests y verificación

No hay CI: la verificación corre en esta máquina, con los contenedores levantados
(`make help` lista todos los atajos).

```bash
make check-fast          # lint-imports + ruff + mypy + pytest unit + tamaños + guards + audit
make check               # lo anterior con cobertura por capa (domain ≥90%, application ≥85%) + integración
make test-module M=vacaciones   # pytest unit de un solo módulo
make lint-frontend && make typecheck-frontend
```

`make audit` (incluido en los dos `check`) corre `pip-audit` sobre `uv.lock` y `npm audit`;
necesita red. La suite E2E de Playwright es hermética (mockea el backend); Node no está
instalado en el host, así que se corre con la imagen oficial de Playwright montando
`frontend/`.

## Variables de entorno

La lista completa, comentada y agrupada por módulo, está en `.env.example` (ningún valor
real ahí, ver `ARCHITECTURE_GUIDE.md` §8). Las que hay que mirar sí o sí:

| Variable | Para qué | Obligatoria |
|---|---|---|
| `ENVIRONMENT` | `development` habilita orígenes LAN en CORS y `/docs` | Sí |
| `POSTGRES_PASSWORD`, `DATABASE_URL` | Base de datos | Sí |
| `SESSION_COOKIE_SECURE` | Cookie de sesión solo por HTTPS (`false` solo en dev) | Sí |
| `DISABLE_BACKGROUND_JOBS` | Jobs de fondo (SLA, contadores, WATI…); en dev `false` | Sí |
| `DISABLE_INSUMOS_BACKGROUND_JOBS` | **Siempre `true` en dev**: el legacy de insumos sigue productivo | Sí |
| `DISABLE_DESPACHADOS_BACKGROUND_JOBS` | Sincronización de envíos OCA (solo lectura) | No (default `true`) |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_STARTTLS` | Mails; en dev, Mailpit (`mailpit`, `1025`, `false`) | Sí |
| `ORION_HOST`, `ORION_USER`, `ORION_PASSWORD` | Siges/ORION de solo lectura (SLA, contadores, liquidaciones…) | Sí, para esos módulos |
| `WSAYC_USERNAME`, `WSAYC_PASSWORD` | SOAP de Canal Directo (pedidos, liquidaciones) | Sí, para esos módulos |
| `SDS_API_KEY` (+ secret), `WATI_API_TOKEN` | Integraciones de contadores e insumos / WhatsApp | Por módulo |
| `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` | Diagnóstico de logs HP / clasificación de incidentes | Por módulo |

El resto tiene valores por defecto en el código; están al final de `.env.example`.
