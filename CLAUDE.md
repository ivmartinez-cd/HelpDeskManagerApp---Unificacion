# CLAUDE.md

## Jobs de fondo: encendidos, salvo insumos (SDSInsumos sigue productivo)

Regla dura, no opcional, para toda sesión de trabajo en este repo — no solo la actual.

- **Desde el 2026-09-02 (decisión de Iván) los jobs de fondo corren ENCENDIDOS en dev**:
  `DISABLE_BACKGROUND_JOBS=false` en `.env`. Los compañeros usan esta app como entorno de
  pruebas y esperan que SLA, contadores, liquidaciones, WATI y análisis de logs se actualicen
  solos (antes, con el flag en `true`, SLA solo se refrescaba al apretar "Actualizar").
- **Insumos queda apagado SIEMPRE**: `DISABLE_INSUMOS_BACKGROUND_JOBS=true`. SDSInsumos
  (`sdsinsumos.cdsa.com.ar`, el legacy) sigue productivo mientras se migra a este monorepo, y
  su poller acá se pisaría con el de producción. Además la DB de dev (`helpdesk-db`) está
  sembrada con datos reales de producción (ver memoria
  `project_insumos_dev_seeded_from_prod_backup`), incluidos destinatarios de mail reales de
  logística (`app_settings.logistics_mail_to`). **Nada de esto es un mock**: cualquier job o
  llamada que se dispare de verdad tiene efectos reales sobre gente real y sobre Canal Directo
  en producción. No encender insumos (borrar la línea o ponerla en `false`) sin que el usuario
  lo pida explícitamente.
- **Mails en dev van a Mailpit, no a Gmail (desde 2026-08-21).** `.env` apunta
  `SMTP_HOST=mailpit` / `SMTP_PORT=1025` / `SMTP_STARTTLS=false` al servicio `mailpit` del
  compose; todo mail que dispare el backend queda en http://localhost:8025 y nunca sale de la
  máquina. Las credenciales reales de Gmail quedaron comentadas con prefijo `[prod]` en `.env` —
  **no descomentarlas en dev**. Esto es una red de seguridad extra, no reemplaza la regla de
  arriba: SOAP/Insight/wsAyC siguen siendo reales, y un job de fondo que escriba contra ellos
  sigue teniendo efectos reales aunque el mail quede atrapado.
- **Incidente real (2026-08-12)**: editar en vivo código de jobs de fondo
  (`poller_alerts.py`/`background_jobs.py`) con el contenedor `helpdesk-manager-backend`
  corriendo con sus jobs activos disparó un mail real de "poller caído" a destinatarios reales
  de Canal Directo, sin que nadie lo pidiera.
- **Qué implica tener los jobs activos al editar backend**: uvicorn corre sin `--reload`, así
  que editar un archivo no afecta al proceso hasta el próximo `reiniciar.sh backend`. Pero en
  cada reinicio los jobs arrancan y **corren un ciclo inmediato** (SLA, pendientes, contadores,
  liquidaciones-reconciliar, WATI, snapshots HP) con el código que esté en disco en ese
  momento. Antes de reiniciar el backend con código de jobs a medio hacer
  (`backend/src/modules/*/presentation/background_jobs.py`,
  `backend/src/modules/*/application/jobs/`, o cualquier cosa que un job ejecute contra
  SOAP/Insight/wsAyC/Gestión/Mercurio), apagarlos temporalmente y avisarlo:
  ```
  # .env  (temporal, volver a false al terminar)
  DISABLE_BACKGROUND_JOBS=true
  ```
  y recrear el contenedor — `docker restart` NO relee `.env` (reinicia el proceso con el
  entorno viejo):
  ```
  docker compose up -d --force-recreate backend
  docker exec helpdesk-manager-backend printenv DISABLE_BACKGROUND_JOBS DISABLE_INSUMOS_BACKGROUND_JOBS
  ```
  Al terminar, volver a `DISABLE_BACKGROUND_JOBS=false` y recrear de nuevo: dejar los jobs
  apagados "por las dudas" rompe la actualización automática que los compañeros esperan.
- Verificación del arranque sano: en el log, después de `Application startup complete`, tiene
  que aparecer `background_jobs: insumos omitido (DISABLE_INSUMOS_BACKGROUND_JOBS=true)` y
  `background_jobs: 6 job(s) iniciados`. `reiniciar.sh backend` y `make recreate-backend`
  abortan/avisan si `DISABLE_INSUMOS_BACKGROUND_JOBS` no está en `true`.

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
  la verificación completa la corre **GitHub Actions en cada push** (`.github/workflows/ci.yml`:
  `lint-imports`, `ruff`, `mypy`, pytest unit + integración, gates §4/§6/§8/§11, eslint, `tsc`
  y la suite de Playwright). Localmente solo se corre lo barato y acotado al módulo tocado —
  ```
  uv run ruff check <archivos tocados>     # segundos, dentro del contenedor del backend
  make test-module M=<modulo>              # OPCIONAL: pytest unit solo de tests/unit/*/<modulo>
  ```
  — y al pushear se sigue la corrida de CI con `make ci` (`gh run watch`); si queda rojo, se
  arregla y se vuelve a pushear. Si CI falla, no está terminado. **No correr local** `make check`,
  `make check-fast`, `uv run lint-imports`, `uv run mypy src`, `uv run pytest tests/unit`
  completo ni Playwright salvo pedido explícito del usuario: medido el 2026-09-02 con la
  máquina ociosa sobre el HDD USB, lint-imports 42 s, mypy 108 s, pytest unit 101 s,
  sizes+guards 29 s — con 3-4 sesiones de Claude en paralelo cada corrida saturaba el disco y
  freezaba las demás terminales. `lint-imports` sigue siendo la regla más importante y no es
  opinable: la hace cumplir CI, no el ojo. `make test-module` también es caro en este disco
  (contadores, 286 tests: pytest dice 32 s pero la corrida tarda ≈2 min de reloj por el
  arranque de `uv` y los imports desde el HDD): usarlo cuando el cambio lo amerite, no por
  rutina; ruff sí, siempre.
- Las desviaciones conscientes del texto literal de la guía se documentan como ADR en
  `backend/docs/adr/` (ver `007-vocabulario-de-permisos-en-shared-excepcion-de-presentation.md`
  como ejemplo) — una excepción sin ADR es una violación, no una decisión.

## Frontend recarga solo; el backend requiere restart explícito

**Frontend: NO reiniciar.** Desde el 2026-09-02 el contenedor corre `next dev` (Fast Refresh),
así que editar un archivo de `frontend/` se refleja solo en ~2 s. La app es un entorno de
pruebas que los compañeros del usuario usan mientras él corrige cosas en vivo: modo dev es el
estado correcto, no un parche. Antes corría `next build && next start` en cada arranque, y
`reiniciar.sh frontend` re-corría ese build completo tras cada edición: medido el 2026-09-02,
~3 min por vuelta con la presión de I/O del WSL en `full avg10=89%` (el 89% del tiempo TODAS las
tareas del sistema bloqueadas esperando el HDD USB, con CPU y RAM casi libres). Eso era lo que
freezaba las demás terminales en cada implementación.

**Backend: sí reiniciar.** Uvicorn corre sin `--reload` — decisión deliberada, no una
limitación: el `--reload` relanzaba los background jobs con cada guardado y así se disparó el
mail real del incidente 2026-08-12. El código sigue bind-monteado (`./backend:/app`), pero
editar un archivo de `backend/` **no tiene ningún efecto** hasta reiniciar el contenedor.

**Docker corre en WSL (Ubuntu-24.04), no en Windows.** Desde 2026-08-21 el repo se edita
**directo en la copia de Linux** (`/home/ivan/proyectos/helpdesk-manager`, la misma que montan
los contenedores) — ya no hay una copia paralela en Windows ni un paso de rsync entre medio
(leer `/mnt/c` desde WSL es lento, por eso el bind mount siempre apuntó a Linux). El único paso
a recordar tras editar es `scripts/wsl/reiniciar.sh`, corrido desde una terminal WSL parada en
el repo:

```
bash scripts/wsl/reiniciar.sh backend          # tras editar backend/
# tras editar frontend/: NADA, Fast Refresh lo recompila solo
```

- **Backend** (`helpdesk-manager-backend`): uvicorn corre sin `--reload`. Tras editar
  `backend/`, `reiniciar.sh backend` hace `docker restart`, que re-corre el entrypoint:
  `alembic upgrade head` + uvicorn; el script aborta si `DISABLE_INSUMOS_BACKGROUND_JOBS` no
  está en `true` y avisa si el log muestra jobs iniciados sin la línea `insumos omitido`.
  Recordar que `docker restart` NO relee `.env` — para cambios de variables de entorno hace
  falta, parado en `/home/ivan/proyectos/helpdesk-manager`,
  `docker compose up -d --force-recreate backend`.
- **Frontend** (`helpdesk-manager-frontend`): corre `next dev` (Fast Refresh). Tras editar
  `frontend/` **no hay que hacer nada**: la ruta se recompila sola en ~2 s (medido con el disco
  ocioso) y el navegador la toma al recargar. `reiniciar.sh frontend` detecta el modo dev, avisa
  y no reinicia; `reiniciar.sh frontend --force` fuerza el restart para los casos que sí lo
  piden (cambió una variable de entorno, se rompió el dev server). Reiniciarlo cuesta un
  arranque en frío de varios minutos en este disco, así que no hacerlo por costumbre.
  El comando lo fija `command:` en `docker-compose.yml`; para servir un build de producción,
  `FRONTEND_CMD=npm run build && npm run start` en `.env` + `docker compose up -d
  --force-recreate frontend`.
- Cualquier comando `docker …` / `docker compose …` se corre directo en la terminal WSL, parado
  en el repo — ya no hace falta pasar por `wsl.exe` desde Windows.
- Playwright local (`frontend/`): corre en el **host WSL**, no en el contenedor (la imagen es
  Alpine y no soporta los navegadores). Setup hecho el 2026-08-21: node por nvm
  (`export PATH=$HOME/.nvm/versions/node/v24.19.0/bin:$PATH`, en shells no interactivos no está
  en el PATH), `npm ci` en `frontend/`, Chromium en `~/.cache/ms-playwright/` y las libs de
  sistema por `apt`. El puerto 3001 lo ocupa otro contenedor del usuario (`stc_api`); usar
  `PW_PORT=3011 ./node_modules/.bin/playwright test …` parado en `frontend/`. Gotchas:
  `frontend/node_modules` y `frontend/.next` son puntos de montaje de volúmenes de Docker
  (los crea como directorios vacíos de root; si vuelven a quedar así tras un `compose up`,
  `rmdir` + `mkdir` como usuario propio — el contenedor usa sus volúmenes y no se entera); y
  `playwright.config.ts` borra `http_proxy`/`https_proxy` del entorno porque el proxy
  corporativo rechaza `localhost` y todas las navegaciones terminan en `net::ERR_ABORTED`.

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
- **`.githooks/pre-commit`** (≈5 s): rechaza el commit si algún archivo staged fue editado más
  recientemente por **otra** sesión de Claude (según el registro de sesiones); override
  consciente y coordinado: `ALLOW_FOREIGN=1 git commit …`. Si hay `.py` staged en `backend/`,
  corre `ruff` sobre esos archivos dentro del contenedor. Nada más.
- **`.githooks/pre-push`** (instantáneo): lista los commits que se van a subir (leerlos, no
  pushear a ciegas). **No corre ninguna verificación local** desde el 2026-09-02.
- **CI en GitHub Actions** (`.github/workflows/ci.yml`): corre en cada push a `main` y en cada
  PR, sin tocar esta máquina, **toda** la verificación: backend `lint-imports` + `ruff` + `mypy`
  + pytest unit + `test-integration` (service container de Postgres propio del runner; el schema
  sale de `Base.metadata.create_all`, no de Alembic) + gates §4/§6/§8/§11
  (`scripts/check_sizes.py` y `check_guards.py --committed`); frontend eslint + `tsc --noEmit`;
  y la **suite completa de Playwright** (job `e2e`). La suite es hermética — `tests/global-setup.ts`
  levanta un backend mock en 18099 y cada spec mockea sus datos con `page.route()`; no toca el
  backend real ni datos reales — así que CI la reemplaza por completo; localmente solo se corre a
  pedido del usuario (`PW_PORT=3011 npx playwright test` en `frontend/`). Historia: hasta el
  2026-09-01 el pre-push corría todo esto local y un push dejó el HDD saturado ~40 min; el
  2026-09-02 se midió que incluso `check-fast` tardaba ≈5 min con la máquina ociosa y se sacó
  todo de los hooks. Contrapartida aceptada: `main` en GitHub puede quedar rojo unos minutos;
  quien pushea sigue la corrida con `make ci` y arregla.
- Los hooks de git se activan por clon con `make hooks` (`git config core.hooksPath
  .githooks`). `--no-verify` existe, pero usarlo es una decisión del usuario, no de Claude.

`make check` sigue siendo la verificación canónica que exige `ARCHITECTURE_GUIDE.md`; la corre
CI en cada push. Localmente, solo si el usuario lo pide explícitamente.

### Cuándo pushear (decisión del usuario, 2026-08-21)

`main` es la rama de trabajo y el remoto (`origin` en GitHub; a futuro el Gitea de Canal
Directo) es el **respaldo**: lo que no está pusheado existe solo en el disco de esta PC. Regla:

- **Pushear al cerrar cada bloque de trabajo** (feature terminada y probada, fin de una
  migración) **y siempre al final del día de trabajo**, antes del `wsl --shutdown`.
- **Hacerlo proactivamente cuando se detecte la condición**, sin esperar a que el usuario lo
  pida de nuevo: el hook de arranque avisa si hay **≥5 commits sin pushear o el más viejo
  tiene más de 24 h**; `hd-status` muestra lo mismo. En ese caso, al terminar la tarea en
  curso (no en el medio), correr `git push origin main` y decirlo en el resumen final — y
  después seguir la corrida de CI con `make ci`; si falla, arreglarlo antes de cerrar la tarea.
  Nunca `--no-verify`.
- **Una sola sesión pushea.** Si `git status`/el registro de sesiones muestran que otra
  sesión está commiteando en ese momento, esperar a que termine o coordinar por
  `SendMessage`; pushear en paralelo desde varias sesiones solo duplica el `pre-push`.
- El `pre-push` ya no cuesta nada, pero igual pushear por bloque de trabajo y no por cada
  commit chico: cada push dispara una corrida de CI y cancela la anterior en curso. Nunca
  `force push` (bloqueado por `claude-git-guard`).

`make help` lista el resto de atajos (`status`, `restart-*`,
`recreate-backend`, `logs-*`, `mailpit`, `typecheck-frontend`). Antes de una migración o un
script que toque datos: `make db-backup TAG=<motivo>` (pg_dump a `backups/`, ignorado por git);
para volver atrás, `make db-restore FILE=backups/<archivo>.dump` (pide confirmación, detiene el
backend mientras restaura).
