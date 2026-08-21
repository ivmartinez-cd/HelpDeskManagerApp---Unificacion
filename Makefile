# Atajos de desarrollo (se corren en WSL, parado en la raíz del repo).
# Los contenedores no recargan código solos — ver CLAUDE.md "Sin hot reload".

BACKEND  := helpdesk-manager-backend
FRONTEND := helpdesk-manager-frontend
EXEC     := docker exec $(BACKEND)

.PHONY: help status check lint-imports ruff mypy test restart-backend restart-frontend \
        recreate-backend logs-backend logs-frontend mailpit up ps

help:  ## Lista los targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[1m%-18s\033[0m %s\n", $$1, $$2}'

status:  ## Estado del entorno (contenedores, modo test, jobs, git)
	@hd-status

# --- Verificación obligatoria antes de dar por terminado un módulo (CLAUDE.md) ---
check: lint-imports ruff mypy test  ## lint-imports + ruff + mypy + pytest (dentro del backend)
	@echo "✔ check completo"

lint-imports:  ## Contratos de capas/módulos (la regla más importante)
	$(EXEC) uv run lint-imports

ruff:  ## ruff check src tests
	$(EXEC) uv run ruff check src tests

mypy:  ## mypy src
	$(EXEC) uv run mypy src

test:  ## pytest tests/unit -q
	$(EXEC) uv run pytest tests/unit -q

# --- Contenedores ---
restart-backend:  ## docker restart del backend (exige DISABLE_BACKGROUND_JOBS=true)
	bash scripts/wsl/reiniciar.sh backend

restart-frontend:  ## docker restart del frontend (next build && start, varios minutos)
	bash scripts/wsl/reiniciar.sh frontend

recreate-backend:  ## Recrear backend releyendo .env (docker restart NO relee .env)
	docker compose up -d --force-recreate backend
	@$(EXEC) printenv DISABLE_BACKGROUND_JOBS | grep -qx true \
	  || { echo "✘ DISABLE_BACKGROUND_JOBS no es 'true' en el contenedor — ver CLAUDE.md"; exit 1; }
	@echo "✔ backend recreado en modo test"

up:  ## Levantar todo el stack (db, backend, mailpit, frontend)
	docker compose up -d

ps:  ## docker compose ps
	docker compose ps

logs-backend:  ## Últimas 100 líneas del backend, siguiendo
	docker logs -n 100 -f $(BACKEND)

logs-frontend:  ## Últimas 100 líneas del frontend, siguiendo
	docker logs -n 100 -f $(FRONTEND)

mailpit:  ## Abre la bandeja de Mailpit (mails de dev)
	@echo "Mailpit: http://localhost:8025"
	@command -v wslview >/dev/null && wslview http://localhost:8025 || true
