# CLAUDE.md

## Modo test obligatorio: SDSInsumos sigue productivo, la migración nunca puede tocarlo

Regla dura, no opcional, para toda sesión de trabajo en este repo — no solo la actual.

- SDSInsumos (el legacy) sigue productivo mientras se migra a este monorepo. La DB de dev
  (`helpdesk-db`) está sembrada con datos reales de producción (ver memoria
  `project_insumos_dev_seeded_from_prod_backup`), incluidos destinatarios de mail reales de
  logística (`app_settings.logistics_mail_to`). **Nada de esto es un mock**: cualquier job o
  llamada que se dispare de verdad tiene efectos reales sobre gente real y sobre Canal Directo
  en producción.
- **Mails en dev van a Mailpit, no a Gmail (desde 2026-08-21).** `.env` apunta
  `SMTP_HOST=mailpit` / `SMTP_PORT=1025` / `SMTP_STARTTLS=false` al servicio `mailpit` del
  compose; todo mail que dispare el backend queda en http://localhost:8025 y nunca sale de la
  máquina. Las credenciales reales de Gmail quedaron comentadas con prefijo `[prod]` en `.env` —
  **no descomentarlas en dev**. Esto es una red de seguridad extra, no reemplaza la regla de
  abajo: SOAP/Insight/wsAyC siguen siendo reales, y un job de fondo que escriba contra ellos
  sigue teniendo efectos reales aunque el mail quede atrapado.
- **Incidente real (2026-08-12)**: editar en vivo código de jobs de fondo
  (`poller_alerts.py`/`background_jobs.py`) con el contenedor `helpdesk-manager-backend`
  corriendo con sus jobs activos disparó un mail real de "poller caído" a destinatarios reales
  de Canal Directo, sin que nadie lo pidiera.
- **Antes de tocar o dejar correr cualquier código de jobs de fondo**
  (`backend/src/modules/*/presentation/background_jobs.py`,
  `backend/src/modules/*/application/jobs/`, o cualquier cosa que mande mail o escriba contra
  SOAP/Insight/wsAyC fuera de un `dryRun` explícito), el contenedor del backend tiene que estar
  en modo test:
  ```
  # .env
  DISABLE_BACKGROUND_JOBS=true
  ```
  y hay que confirmar que el contenedor lo tenga **aplicado de verdad** — `docker restart` NO
  relee `.env` (reinicia el proceso con el entorno viejo). Hace falta recrear el contenedor:
  ```
  docker compose up -d --force-recreate backend
  docker exec helpdesk-manager-backend printenv DISABLE_BACKGROUND_JOBS   # tiene que imprimir "true"
  ```
  y verificar en el log de arranque que **no** aparezca `background_jobs: N job(s) iniciados`
  después de `Application startup complete`.
- Esta regla aplica a cualquier módulo con jobs de fondo (insumos, y también
  `sla/presentation/background_jobs.py`), no solo al que se esté tocando en el momento. No
  reactivar los jobs de fondo (borrar la línea de `.env` o ponerla en `false`) sin que el usuario
  lo pida explícitamente — no es una decisión a tomar de forma proactiva.

## Idioma y estilo de comunicación

Regla dura para toda respuesta de texto a el usuario en este repo (no aplica a nombres de
archivo, código, ni a los mensajes de commit, que siguen la convención en inglés ya establecida
en el historial de git).

- **Idioma**: español de Argentina, voseo natural. Sin lunfardo salvo pedido explícito. Otro
  idioma solo si el usuario lo pide expresamente.
- **Tono**: profesional, directo, conciso. Sin relleno.
- **Sin cortesías**: nada de saludos iniciales, frases tipo "¡Con gusto te ayudo!"/"¡Por
  supuesto!", ni cierres tipo "espero que te sea útil". Ir directo al contenido desde la primera
  palabra.
- **Cero alucinaciones**: nunca inventar datos, métricas, fuentes o información factual. Si
  falta información real, buscarla (web, código, comandos) antes de responder; si sigue sin ser
  verificable, decirlo explícitamente en vez de rellenar con una respuesta plausible pero
  infundada.

## Cumplimiento de ARCHITECTURE_GUIDE.md

Este repo tiene `docs/ARCHITECTURE_GUIDE.md` con reglas arquitectónicas obligatorias
(capas, manejo de errores, paginación, tamaños máximos, etc.). No es un documento de referencia
opcional: todo código nuevo tiene que cumplirlo **mientras se escribe**, no corregirse después
en una auditoría aparte. Concretamente:

- **Manejo de errores (§6)**: ningún `except Exception` puede quedar en silencio. Si el error se
  maneja devolviendo un fallback (no se relanza), loguear con `logging.getLogger(__name__)` y
  contexto relevante (`extra={...}`, `exc_info=exc`) en el punto donde se atrapa — no en el
  caller. Si no hay forma útil de manejarlo, dejarlo propagar o envolverlo en un error de dominio
  (`ExternalServiceError` y similares), nunca `except Exception: pass`.
- **Paginación (§11)**: todo endpoint que devuelva una colección (`list[...]`) va paginado, con
  el envelope genérico `Page[T]` de `src/shared/presentation/schemas/pagination.py` — no
  duplicar ese shape por módulo. Para catálogos chicos que alimentan un combobox con búsqueda en
  vivo (no una tabla paginada en la UI), un `size` default generoso es válido siempre que el
  contrato siga siendo paginado.
- **Tamaños máximos (§4)**: archivo ≤300 líneas, clase ≤200, función ≤20. Si un archivo se pasa,
  separar en módulos por responsabilidad en el momento, no siguiendo agregando al mismo archivo.
- **Verificación antes de dar por terminado un módulo** (no solo al final de todo el proyecto):
  correr, dentro del contenedor del backend —
  ```
  uv run lint-imports   # contratos de capas/módulos — la regla más importante, no es opinable
  uv run ruff check src tests
  uv run mypy src
  uv run pytest tests/unit -q
  ```
  Si algo de esto falla, no está terminado. `lint-imports` en particular es la única forma
  confiable de verificar la dirección de dependencias entre capas — no alcanza con revisar a
  ojo. Atajo equivalente desde la raíz del repo (WSL): `make check` (corre los cuatro dentro
  del contenedor); el `pre-push` de git lo corre solo antes de cada push.
- Las desviaciones conscientes del texto literal de la guía se documentan como ADR en
  `backend/docs/adr/` (ver `007-vocabulario-de-permisos-en-shared-excepcion-de-presentation.md`
  como ejemplo) — una excepción sin ADR es una violación, no una decisión.

## Sin hot reload en los contenedores: los cambios de código requieren restart explícito

Desde 2026-08-13 (commit `e0576cd`) ni el backend ni el frontend recargan código solos —
decisión deliberada, no una limitación: el `--reload` de uvicorn podía relanzar los background
jobs con cada guardado (así se disparó el mail real del incidente 2026-08-12). El código sigue
bind-monteado (`./backend:/app`, `./frontend:/app`), pero editar un archivo **no tiene ningún
efecto** hasta reiniciar el contenedor.

**Docker corre en WSL (Ubuntu-24.04), no en Windows.** Desde 2026-08-21 el repo se edita
**directo en la copia de Linux** (`/home/ivan/proyectos/helpdesk-manager`, la misma que montan
los contenedores) — ya no hay una copia paralela en Windows ni un paso de rsync entre medio
(leer `/mnt/c` desde WSL es lento, por eso el bind mount siempre apuntó a Linux). El único paso
a recordar tras editar es `scripts/wsl/reiniciar.sh`, corrido desde una terminal WSL parada en
el repo:

```
bash scripts/wsl/reiniciar.sh frontend
bash scripts/wsl/reiniciar.sh backend
```

- **Backend** (`helpdesk-manager-backend`): uvicorn corre sin `--reload`. Tras editar
  `backend/`, `reiniciar.sh backend` hace `docker restart`, que re-corre el entrypoint:
  `alembic upgrade head` + uvicorn; el script aborta si `DISABLE_BACKGROUND_JOBS` no está en
  `true` y avisa si el log muestra jobs iniciados. Recordar que `docker restart` NO relee
  `.env` — para cambios de variables de entorno hace falta, parado en
  `/home/ivan/proyectos/helpdesk-manager`, `docker compose up -d --force-recreate backend`.
- **Frontend** (`helpdesk-manager-frontend`): el contenedor corre `next build && next start`
  (build de producción al arrancar). Tras editar `frontend/`, `reiniciar.sh frontend` re-corre
  el build completo — tarda bastante más que un dev server; el script espera a que `/login`
  vuelva a responder 200 antes de devolver.
- Cualquier comando `docker …` / `docker compose …` se corre directo en la terminal WSL, parado
  en el repo — ya no hace falta pasar por `wsl.exe` desde Windows.
- Playwright local (`frontend/`): el puerto 3001 lo ocupa otro contenedor del usuario
  (`stc_api`); usar `PW_PORT=3011 npx playwright test …`.

**Cómo verificar**: no asumir que un cambio está servido solo porque el navegador lo muestra
(el navegador tiene su propia caché). Antes de dar por buena una captura o un test visual:

```
curl -s http://localhost:3000/<ruta> | grep <algo del cambio nuevo>
```

No dejar los contenedores apagados al terminar — son los servidores que quedan corriendo entre
sesiones para poder probar en el navegador.

## Varias sesiones de Claude en paralelo sobre el mismo checkout

El usuario trabaja habitualmente con **varias sesiones de Claude Code abiertas a la vez** (3 o
4, cada una en su ventana, lanzadas con `~/.local/bin/dev` / `hdm`), todas sobre **este mismo
checkout** — no hay worktrees ni ramas por sesión. Consecuencia: `git status` mezcla el trabajo
en curso de todas, y un archivo puede estar siendo editado por otra sesión en este momento.

Existen dos mecanismos de coordinación; usarlos, no asumir que se está solo:

1. **Registro de ediciones entre sesiones (automático, por hooks).** Hooks en
   `.claude/settings.local.json` corren `~/.local/bin/claude-session-registry`: cada
   `Edit`/`Write` de cualquier sesión queda anotado en `.claude/sessions/edits.tsv` (hora,
   sesión, módulo, archivo), y antes de editar un archivo que **otra** sesión tocó hace poco
   llega un aviso por `additionalContext` (mismo archivo = aviso fuerte; mismo módulo = aviso
   suave). Al arrancar una sesión también llega el resumen de las demás. Qué hacer cuando
   aparece el aviso: releer el archivo (pudo cambiar), no pisar ni revertir ni reformatear lo
   ajeno, y **no commitear archivos que no sean de la propia tarea** — al commitear, agregar
   explícitamente los archivos propios (`git add <archivos>`), nunca `git add -A`/`git add .`.
   Para ver el registro a mano: `hd-status` o `claude-session-registry status`.
2. **Comunicación directa entre sesiones.** `ListAgents` lista las otras sesiones de Claude
   abiertas en esta máquina; `SendMessage` les manda un mensaje y pueden responder. Usarlo
   cuando el registro muestra que otra sesión está en el mismo módulo/archivo y hace falta
   coordinar (quién toca qué, si algo está a medio hacer, si se puede reiniciar un contenedor
   que la otra está usando), o cuando un `reiniciar.sh`/`compose up` va a cortar el stack que
   las demás están probando.

Si un aviso del registro se refiere a un archivo que hay que modificar sí o sí y la otra sesión
sigue activa, decírselo al usuario antes de seguir, no resolverlo pisando.

## Guardas automáticas de git (se cumplen solas, no son opcionales)

Además de las reglas de arriba hay tres guardas mecánicas. No intentar rodearlas; si una
bloquea algo que de verdad hace falta, explicárselo al usuario y que decida él.

- **`claude-git-guard`** (hook PreToolUse de Claude sobre `Bash`, en
  `.claude/settings.local.json`): **deniega** `git add -A` / `--all` / `.`, `git commit -a` /
  `-am` y `git push --force`. Motivo: con varias sesiones sobre el mismo checkout, esos
  comandos suben trabajo ajeno o reescriben historia compartida. Siempre `git add <archivos
  propios>` explícito y `git commit` sin `-a`.
- **`.githooks/pre-commit`** (≈2 s): rechaza el commit si algún archivo staged fue editado más
  recientemente por **otra** sesión de Claude (según el registro de sesiones); override
  consciente y coordinado: `ALLOW_FOREIGN=1 git commit …`. Si hay cambios en `backend/`, corre
  `lint-imports` + `ruff` (archivos staged) + `mypy` dentro del contenedor.
- **`.githooks/pre-push`** (≈45 s): lista los commits que se van a subir (leerlos, no pushear a
  ciegas), corre `make check` completo (lint-imports + ruff + mypy + pytest) y, si hay cambios
  en `frontend/`, eslint + `tsc --noEmit` del frontend. Si algo falla, no se pushea. Si un paso
  del frontend falla con salida vacía, otra sesión estaba reiniciando el contenedor — reintentar.
- Los hooks de git se activan por clon con `make hooks` (`git config core.hooksPath
  .githooks`). `--no-verify` existe, pero usarlo es una decisión del usuario, no de Claude.

`make check` es la forma canónica de correr la verificación del módulo que exige
`ARCHITECTURE_GUIDE.md`.

### Cuándo pushear (decisión del usuario, 2026-08-21)

`main` es la rama de trabajo y el remoto (`origin` en GitHub; a futuro el Gitea de Canal
Directo) es el **respaldo**: lo que no está pusheado existe solo en el disco de esta PC. Regla:

- **Pushear al cerrar cada bloque de trabajo** (feature terminada y probada, fin de una
  migración) **y siempre al final del día de trabajo**, antes del `wsl --shutdown`.
- **Hacerlo proactivamente cuando se detecte la condición**, sin esperar a que el usuario lo
  pida de nuevo: el hook de arranque avisa si hay **≥5 commits sin pushear o el más viejo
  tiene más de 24 h**; `hd-status` muestra lo mismo. En ese caso, al terminar la tarea en
  curso (no en el medio), correr `git push origin main` y decirlo en el resumen final — el
  `pre-push` garantiza que no suba nada que rompa `make check`. Si el push falla por el hook,
  reportarlo y no usar `--no-verify`.
- **Una sola sesión pushea.** Si `git status`/el registro de sesiones muestran que otra
  sesión está commiteando en ese momento, esperar a que termine o coordinar por
  `SendMessage`; pushear en paralelo desde varias sesiones solo duplica el `pre-push`.
- No pushear después de cada commit chico (el `pre-push` tarda ~45 s; el ruido no aporta), ni
  hacer `force push` jamás (bloqueado por `claude-git-guard`).

`make help` lista el resto de atajos (`status`, `restart-*`,
`recreate-backend`, `logs-*`, `mailpit`, `typecheck-frontend`). Antes de una migración o un
script que toque datos: `make db-backup TAG=<motivo>` (pg_dump a `backups/`, ignorado por git);
para volver atrás, `make db-restore FILE=backups/<archivo>.dump` (pide confirmación, detiene el
backend mientras restaura).
