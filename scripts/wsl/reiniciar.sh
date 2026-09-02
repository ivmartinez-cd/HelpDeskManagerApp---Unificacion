#!/bin/bash
# Reinicia el servicio pedido tras editar código en la copia de Linux que montan los
# contenedores (docker corre en WSL, ya no hay copia paralela en Windows).
#
# Uso (se corre DENTRO de WSL, parado en el repo):
#   bash scripts/wsl/reiniciar.sh backend       # restart backend (exige DISABLE_BACKGROUND_JOBS=true)
#   bash scripts/wsl/reiniciar.sh frontend      # normalmente NO hace falta (ver abajo)
#
# Por qué existe: el BACKEND no recarga solo (uvicorn sin --reload, decisión deliberada: el
# --reload relanzaba los background jobs con cada guardado y así se mandó un mail real,
# incidente 2026-08-12).
#
# El FRONTEND sí recarga solo desde el 2026-09-02: el contenedor corre `next dev` (Fast
# Refresh), así que editar un archivo de frontend/ se refleja en ~2 s sin reiniciar nada.
# `reiniciar.sh frontend` avisa y no hace nada; para forzar el restart igual (p. ej. tras
# cambiar variables de entorno) usar: reiniciar.sh frontend --force
# Reemplaza a scripts/wsl/sincronizar-y-reiniciar.sh, que hacía rsync desde Windows: ese paso
# ya no hace falta porque el repo se edita directo acá.
set -euo pipefail

LIN="${HDM_LINUX:-/home/ivan/proyectos/helpdesk-manager}"
SVC="${1:-}"
FORCE="${2:-}"
ESPERA_MAX="${HDM_ESPERA_MAX:-600}"

[ -d "$LIN/frontend" ] || { echo "No encuentro el repo: $LIN" >&2; exit 1; }
case "$SVC" in frontend|backend) ;; *) echo "Uso: $0 frontend|backend" >&2; exit 1;; esac
cd "$LIN"

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
  # ¿El contenedor está en modo dev (next dev)? Entonces Fast Refresh ya recompila solo y
  # reiniciar solo cuesta un arranque en frío caro (medido 2026-09-02: ~4 min contra ~2 s
  # que tarda una edición con el dev server ya levantado).
  cmd_actual="$(docker inspect helpdesk-manager-frontend --format '{{join .Config.Cmd " "}}' 2>/dev/null || true)"
  if printf '%s' "$cmd_actual" | grep -q 'run dev' && [ "$FORCE" != "--force" ]; then
    echo "== el frontend corre en modo dev (next dev): NO hace falta reiniciar."
    echo "   Editá el archivo y recargá el navegador; Fast Refresh lo recompila en ~2 s."
    echo "   Si de verdad necesitás recrear el contenedor (p. ej. cambió una variable de"
    echo "   entorno): bash scripts/wsl/reiniciar.sh frontend --force"
    curl --noproxy '*' -s -o /dev/null -m 10 -w '   estado actual de /login: %{http_code}\n' http://127.0.0.1:3000/login || true
    exit 0
  fi
  echo "== docker restart helpdesk-manager-frontend (arranque en frío del dev server, varios minutos en este disco)"
  docker restart helpdesk-manager-frontend >/dev/null
  esperar_200 "http://127.0.0.1:3000/login"
fi
