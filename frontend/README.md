# HelpDesk Manager — Frontend

## ¿Qué hace?

UI Next.js (App Router) + Tailwind del monolito unificado: un feature slice por
módulo de negocio bajo `src/features/`, servido detrás del login unificado.

## Setup rápido

Desde la raíz del repo:

```bash
docker compose up -d --build frontend
```

El contenedor corre `next build && next start` (build de producción al arrancar).
Sin hot reload: tras editar código, `docker restart helpdesk-manager-frontend` y
esperar a que `http://localhost:3000/` vuelva a responder antes de probar — el
build completo tarda varios minutos. El navegador cachea: verificar cambios con
`curl` antes de dar por buena una captura.

Alternativa dev server sin Docker: `npm install && npm run dev`.

## Arquitectura

`src/features/<módulo>/{components,hooks,api,types}/` por feature +
`src/shared/` (componentes y utilidades comunes) + `src/services/` (http client,
sesión). Cada módulo portado sigue un design handoff de fidelidad visual (ver
skill `ui-design-handoff`); no inventar diseño nuevo. Norma general en
`docs/ARCHITECTURE_GUIDE.md`.

## Verificación

```bash
docker exec helpdesk-manager-frontend npx tsc --noEmit
docker exec helpdesk-manager-frontend npx eslint src --quiet
```

## Variables de entorno

| Variable | Descripción | Obligatoria |
|---|---|---|
| `BACKEND_URL` | Destino del proxy de `next.config` hacia la API. En Docker la fija `docker-compose.yml` (`http://backend:8012`); sin Docker cae al default `http://127.0.0.1:8012`. | No (tiene default) |

El resto de la configuración vive en el `.env` de la raíz y es del backend.
