#!/bin/bash
# Sincroniza el código de la carpeta de Windows a la copia de Linux que montan los
# contenedores (docker corre en WSL) y reinicia el servicio pedido.
#
# Uso (se corre DENTRO de WSL; desde Windows ver CLAUDE.md "Sin hot reload"):
#   bash scripts/wsl/sincronizar-y-reiniciar.sh frontend      # sync + restart frontend (build completo)
#   bash scripts/wsl/sincronizar-y-reiniciar.sh backend       # sync + restart backend (exige DISABLE_BACKGROUND_JOBS=true)
#   bash scripts/wsl/sincronizar-y-reiniciar.sh solo-sync     # sync sin reiniciar nada
#
# Por qué existe: los contenedores NO montan la carpeta de Windows (leer /mnt/c desde WSL
# es lento) sino /home/ivan/proyectos/helpdesk-manager. Este script es el único paso que hay
# que recordar: reemplaza al "docker restart" a secas.
set -euo pipefail

WIN="${HDM_WIN:-/mnt/c/Users/imartinez.CDSA/Desktop/Proyectos/HelpDeskManager-Unificacion}"
LIN="${HDM_LINUX:-/home/ivan/proyectos/helpdesk-manager}"
SVC="${1:-}"
ESPERA_MAX="${HDM_ESPERA_MAX:-600}"

[ -d "$WIN/frontend" ] || { echo "No encuentro la carpeta de Windows: $WIN" >&2; exit 1; }
[ -d "$LIN/frontend" ] || { echo "No encuentro la copia de Linux: $LIN" >&2; exit 1; }
case "$SVC" in frontend|backend|solo-sync) ;; *) echo "Uso: $0 frontend|backend|solo-sync" >&2; exit 1;; esac

# Excluidos: dependencias/builds (son volúmenes nombrados dentro de los contenedores),
# .git (la copia de Linux es un espejo, no se versiona ahí), estado en runtime (backend/var).
EXCL=(--exclude node_modules --exclude .next --exclude .venv --exclude .git --exclude __pycache__
      --exclude '*.pyc' --exclude test-results --exclude playwright-report --exclude .pytest_cache
      --exclude .ruff_cache --exclude .mypy_cache --exclude var/
      --exclude next-env.d.ts --exclude tsconfig.tsbuildinfo)

echo "== Sincronizando $WIN → $LIN"
rsync -rlt --delete --itemize-changes "${EXCL[@]}" "$WIN/frontend/" "$LIN/frontend/" | grep -E '^[<>ch*]' | sed 's/^/  frontend: /' || true
rsync -rlt --delete --itemize-changes "${EXCL[@]}" "$WIN/backend/" "$LIN/backend/" | grep -E '^[<>ch*]' | sed 's/^/  backend:  /' || true

# .env: se copia tal cual si cambió. Un cambio de variables NO se aplica con restart:
# hace falta `docker compose up -d --force-recreate <svc>` (CLAUDE.md).
if ! cmp -s "$WIN/.env" "$LIN/.env"; then
  cp "$WIN/.env" "$LIN/.env"
  echo "  .env: cambió — recordá que docker restart NO lo relee (docker compose up -d --force-recreate <svc> en $LIN)"
fi
echo "== Sincronización lista"

[ "$SVC" = "solo-sync" ] && exit 0

esperar_200() {  # $1 = url ; espera hasta ESPERA_MAX segundos
  local url="$1" t=0
  while [ "$t" -lt "$ESPERA_MAX" ]; do
    if [ "$(curl --noproxy '*' -s -o /dev/null -m 5 -w '%{http_code}' "$url")" = "200" ]; then
      echo "== $url responde 200 (${t}s)"; return 0
    fi
    sleep 5; t=$((t + 5))
  done
  echo "== TIMEOUT esperando $url" >&2; return 1
}

if [ "$SVC" = "backend" ]; then
  flag="$(grep -E '^DISABLE_BACKGROUND_JOBS=' "$LIN/.env" | tail -1 | cut -d= -f2 | tr -d '\r[:space:]')"
  if [ "$flag" != "true" ]; then
    echo "ABORTADO: DISABLE_BACKGROUND_JOBS no está en true en $LIN/.env (regla dura de CLAUDE.md)." >&2
    exit 2
  fi
  echo "== docker restart helpdesk-manager-backend (alembic upgrade head + uvicorn)"
  docker restart helpdesk-manager-backend >/dev/null
  esperar_200 "http://127.0.0.1:8012/docs"
  echo "== DISABLE_BACKGROUND_JOBS en el contenedor: $(docker exec helpdesk-manager-backend printenv DISABLE_BACKGROUND_JOBS || echo '(no definida)')"
  if docker logs --since 10m helpdesk-manager-backend 2>&1 | grep -q 'background_jobs: .* iniciados'; then
    echo "ATENCIÓN: el log muestra background jobs iniciados — revisar .env y recrear el contenedor." >&2
  fi
else
  echo "== docker restart helpdesk-manager-frontend (next build && next start, ~2-4 min)"
  docker restart helpdesk-manager-frontend >/dev/null
  esperar_200 "http://127.0.0.1:3000/login"
fi
