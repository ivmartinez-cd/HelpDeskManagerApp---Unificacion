# Atajos de desarrollo (se corren en WSL, parado en la raíz del repo).
# Los contenedores no recargan código solos — ver CLAUDE.md "Sin hot reload".

BACKEND  := helpdesk-manager-backend
FRONTEND := helpdesk-manager-frontend
DB       := helpdesk-db
EXEC     := docker exec $(BACKEND)
PGUSER   ?= helpdesk
PGDB     ?= helpdesk

TEST_DB  := helpdesk-db-test
NET      := helpdesk-manager_default

.PHONY: help status check check-fast lint-imports ruff mypy test test-integration sizes sizes-wip guards guards-wip lint-frontend typecheck-frontend hooks \
        db-backup db-restore restart-backend restart-frontend recreate-backend \
        logs-backend logs-frontend mailpit up ps

help:  ## Lista los targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[1m%-18s\033[0m %s\n", $$1, $$2}'

status:  ## Estado del entorno (contenedores, modo test, jobs, git)
	@hd-status

# --- Verificación obligatoria antes de dar por terminado un módulo (CLAUDE.md) ---
check: lint-imports ruff mypy test test-integration sizes guards  ## lint-imports + ruff + mypy + pytest unit + integración + gates §4 y §6/§8/§11
	@echo "✔ check completo"

# Mismo check, sin test-integration: esa parte pega contra Postgres real (vía
# Docker) y en esta máquina compartida (WSL sobre HDD externo) su I/O sostenido
# frena las demás terminales. La corre GitHub Actions en cada push (con un
# service container propio, no toca este disco) — este target es lo que usa
# el pre-push local para no bloquear la máquina (ver CLAUDE.md, incidente
# 2026-09-01).
check-fast: lint-imports ruff mypy test sizes guards  ## check sin test-integration (usado por pre-push)
	@echo "✔ check-fast completo (test-integration corre en CI, no acá)"

lint-imports:  ## Contratos de capas/módulos (la regla más importante)
	$(EXEC) uv run lint-imports

ruff:  ## ruff check src tests
	$(EXEC) uv run ruff check src tests

mypy:  ## mypy src
	$(EXEC) uv run mypy src

test:  ## pytest tests/unit -q
	$(EXEC) uv run pytest tests/unit -q

test-integration:  ## pytest tests/integration (levanta helpdesk-db-test y lo conecta a la red del backend)
	docker compose -f docker-compose.test.yml up -d --wait db-test
	@docker network connect $(NET) $(TEST_DB) 2>/dev/null || true
	$(EXEC) env DB_TEST_HOST=$(TEST_DB) DB_TEST_PORT=5432 uv run pytest tests/integration -q

sizes:  ## Gate §4 sobre HEAD (lo que se pushea): función/clase/archivo fuera del inventario congelado (scripts/sizes-baseline.json)
	python3 scripts/check_sizes.py --committed

sizes-wip:  ## Gate §4 sobre el árbol de trabajo (lo que tenés editado, incluido WIP ajeno)
	python3 scripts/check_sizes.py

guards:  ## Gate §6/§8/§11 sobre HEAD: excepts silenciosos, SQL por f-string, secretos, print/console.log, XSS, list sin Page, endpoint sin authz (scripts/guards-baseline.json)
	python3 scripts/check_guards.py --committed

guards-wip:  ## Gate §6/§8/§11 sobre el árbol de trabajo
	python3 scripts/check_guards.py

lint-frontend:  ## eslint del frontend (dentro del contenedor)
	docker exec $(FRONTEND) npm run -s lint

typecheck-frontend:  ## tsc --noEmit del frontend (≈15 s; next build lo hace recién al reiniciar)
	docker exec $(FRONTEND) npx tsc --noEmit

# --- Base de datos de dev (datos reales sembrados: respaldar antes de migraciones riesgosas) ---
db-backup:  ## pg_dump formato custom a backups/helpdesk-db_<fecha>[_TAG].dump  (make db-backup TAG=pre-migracion-x)
	@mkdir -p backups
	@f=backups/helpdesk-db_$$(date +%Y-%m-%d_%H%M)$(if $(TAG),_$(TAG),).dump; \
	docker exec $(DB) pg_dump -U $(PGUSER) -d $(PGDB) -Fc >"$$f" && echo "✔ $$f ($$(du -h "$$f" | cut -f1))"

db-restore:  ## Restaura FILE=backups/<x>.dump|.sql sobre la DB de dev — DESTRUCTIVO, pide confirmación
	@test -n "$(FILE)" || { echo "Uso: make db-restore FILE=backups/<archivo>.dump  (o .sql plano)"; exit 2; }
	@test -f "$(FILE)" || { echo "✘ no existe $(FILE)"; exit 2; }
	@printf 'Esto PISA la base "%s" con %s (el backend se detiene mientras tanto). ¿Seguir? [s/N] ' "$(PGDB)" "$(FILE)"; \
	read -r r; [ "$$r" = s ] || [ "$$r" = S ] || { echo "abortado"; exit 1; }
	docker stop $(BACKEND) >/dev/null
	docker cp "$(FILE)" $(DB):/tmp/restore.in
	@case "$(FILE)" in \
	  *.sql) docker exec $(DB) psql -U $(PGUSER) -d $(PGDB) -q -v ON_ERROR_STOP=0 -f /tmp/restore.in 2>&1 | tail -5 ;; \
	  *)     docker exec $(DB) pg_restore -U $(PGUSER) -d $(PGDB) --clean --if-exists --no-owner --no-privileges /tmp/restore.in 2>&1 | tail -5 ;; \
	esac
	docker exec $(DB) rm -f /tmp/restore.in
	docker start $(BACKEND) >/dev/null && echo "✔ restaurado desde $(FILE); backend arrancando (corre alembic upgrade head)"

hooks:  ## Activa los hooks de git del repo (.githooks: pre-commit y pre-push) en este clon
	git config core.hooksPath .githooks
	@echo "✔ core.hooksPath=.githooks (pre-commit: archivos ajenos + lint/ruff/mypy; pre-push: make check + lint frontend)"

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
