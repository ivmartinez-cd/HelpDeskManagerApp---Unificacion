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
  SOAP/Insight/wsAyC/Gestión/Orion), apagarlos temporalmente y avisarlo:
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
- **Insumos > Despachados tiene su propio flag**: `DISABLE_DESPACHADOS_BACKGROUND_JOBS`
  (default `true`, independiente del de insumos). Su job consulta Siges/ORION y OCA reales,
  solo lectura, y escribe únicamente en las tablas `insumos_despacho_*` de HDM: no manda mails
  ni escribe afuera. **Encendido desde el 2026-09-25 (decisión de Iván)**:
  `DISABLE_DESPACHADOS_BACKGROUND_JOBS=false` en `.env`, cada 2 h, lun-sáb de 8 a 20.
  "Actualizar ahora" en la pantalla corre la misma sincronización aunque el flag esté en `true`. Detalle en `docs/insumos/DESPACHADOS.md`.
- Verificación del arranque sano: en el log, después de `Application startup complete`, tiene
  que aparecer `background_jobs: insumos omitido (DISABLE_INSUMOS_BACKGROUND_JOBS=true)`,
  `despachados: iniciando (intervalo 120 min)` y `background_jobs: 9 job(s) iniciados`.
  `reiniciar.sh backend` y `make recreate-backend` abortan/avisan si `DISABLE_INSUMOS_BACKGROUND_JOBS` no está en `true`.

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
- **Menos técnico, más claro** (2026-09-11): al explicar qué hace una feature/reporte, responder
  en términos de negocio (qué trae, qué filtra, de dónde sale el dato) — no como changelog de
  código. Nada de nombres de archivo/clase/función, fragmentos de SQL, ni citas `file:line` salvo
  que el usuario pida el detalle técnico o esté depurando código con él.

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
  Para funciones, desde ADR-042 (2026-10-01) el gate mide **solo el cuerpo** (sin firma, decoradores
  ni docstring) y falla recién **por encima de 25 líneas**: 20 sigue siendo la referencia al
  escribir, 21-25 es margen aceptado. No partir una función por 2-3 líneas solo para pasar el
  conteo; sí dividirla si mezcla responsabilidades, mida lo que mida.
- **Verificación antes de dar por terminado un módulo** (no solo al final de todo el proyecto):
  **hoy no hay CI**. GitHub quedó abandonado (2026-09-24) y el Gitea de Canal Directo, que es
  el único remoto vivo, no tiene runner registrado — `.gitea/workflows/ci.yml` es un no-op a
  propósito, para que no encole corridas que nadie va a tomar. O sea: **lo que no se corre en
  esta máquina, no se corre en ningún lado**.
  ```
  uv run ruff check <archivos tocados>     # segundos, dentro del contenedor del backend
  make test-module M=<modulo>              # pytest unit solo de tests/unit/*/<modulo>
  make check                               # verificación completa que exige ARCHITECTURE_GUIDE.md
  ```
  Mientras no haya runner, `make check` (o al menos `make check-fast`) hay que correrlo antes
  de dar por terminado un módulo: es la única red que queda. `lint-imports` sigue siendo la
  regla más importante y no es opinable — antes la hacía cumplir CI; ahora, nadie salvo esta
  corrida. `ruff`, siempre.

  Historia, para que no confunda: hasta el 2026-09-02 regía lo contrario ("no correr `make
  check` local"), porque en la máquina anterior — WSL sobre un HDD USB — lint-imports tardaba
  42 s, mypy 108 s, pytest unit 101 s y sizes+guards 29 s, y con 3-4 sesiones en paralelo cada
  corrida saturaba el disco y freezaba las demás terminales. Esta máquina es Ubuntu nativo
  sobre NVMe y esos números **no** están re-medidos; la razón de fondo de aquella regla (que
  CI lo corría igual) ya no existe.
- Las desviaciones conscientes del texto literal de la guía se documentan como ADR en
  `docs/adr/` (ver `007-vocabulario-de-permisos-en-shared-excepcion-de-presentation.md`
  como ejemplo) — una excepción sin ADR es una violación, no una decisión.

## Frontend recarga solo; el backend requiere restart explícito

**Frontend: NO reiniciar.** Desde el 2026-09-02 el contenedor corre `next dev` (Fast Refresh),
así que editar un archivo de `frontend/` se refleja solo en ~2 s. La app es un entorno de
pruebas que los compañeros del usuario usan mientras él corrige cosas en vivo: modo dev es el
estado correcto, no un parche. Antes corría `next build && next start` en cada arranque, y
`reiniciar.sh frontend` re-corría ese build completo tras cada edición: ~3 min por vuelta en la
máquina anterior (WSL sobre HDD USB), que era lo que freezaba las demás terminales en cada
implementación. En esta máquina el build sería más rápido, pero el modo dev se queda igual: el
punto es que los compañeros ven el cambio al recargar, sin esperar ningún build.

**Backend: sí reiniciar.** Uvicorn corre sin `--reload` — decisión deliberada, no una
limitación: el `--reload` relanzaba los background jobs con cada guardado y así se disparó el
mail real del incidente 2026-08-12. El código sigue bind-monteado (`./backend:/app`), pero
editar un archivo de `backend/` **no tiene ningún efecto** hasta reiniciar el contenedor.

**Docker corre en Ubuntu nativo — ya no hay WSL ni Windows de por medio** (migración
2026-09-24; antes el stack vivía en WSL sobre un HDD USB, y de ahí salen varias de las
mediciones históricas de este archivo). El repo se edita directo en el checkout que montan los
contenedores: `/home/ivan-martinez/proyectos/canal/helpdesk-manager`, sobre el NVMe de la
máquina. Los scripts ya no dependen de esa ruta (`scripts/wsl/reiniciar.sh` deduce la raíz del
repo de su propia ubicación); el directorio conserva el nombre `wsl/` solo por historia. El
único paso a recordar tras editar es:

```
bash scripts/wsl/reiniciar.sh backend          # tras editar backend/
# tras editar frontend/: NADA, Fast Refresh lo recompila solo
```

- **Backend** (`helpdesk-manager-backend`): uvicorn corre sin `--reload`. Tras editar
  `backend/`, `reiniciar.sh backend` hace `docker restart`, que re-corre el entrypoint:
  `alembic upgrade head` + uvicorn; el script aborta si `DISABLE_INSUMOS_BACKGROUND_JOBS` no
  está en `true` y avisa si el log muestra jobs iniciados sin la línea `insumos omitido`.
  Recordar que `docker restart` NO relee `.env` — para cambios de variables de entorno hace
  falta, parado en la raíz del repo, `docker compose up -d --force-recreate backend`
  (o `make recreate-backend`).
- **Frontend** (`helpdesk-manager-frontend`): corre `next dev` (Fast Refresh). Tras editar
  `frontend/` **no hay que hacer nada**: la ruta se recompila sola en ~2 s (medido con el disco
  ocioso) y el navegador la toma al recargar. `reiniciar.sh frontend` detecta el modo dev, avisa
  y no reinicia; `reiniciar.sh frontend --force` fuerza el restart para los casos que sí lo
  piden (cambió una variable de entorno, se rompió el dev server). Reiniciarlo cuesta un
  arranque en frío de varios minutos en este disco, así que no hacerlo por costumbre.
  El comando lo fija `command:` en `docker-compose.yml`; para servir un build de producción,
  `FRONTEND_CMD=npm run build && npm run start` en `.env` + `docker compose up -d
  --force-recreate frontend`.
- Cualquier comando `docker …` / `docker compose …` se corre directo en la terminal, parado en
  el repo.
- **Acceso desde otras máquinas de la LAN** (para que un compañero pruebe la app): esta PC es
  `192.168.178.39`, así que la URL es `http://192.168.178.39:3000`. Cada IP nueva desde la que
  se entre hay que agregarla en **dos** lugares, o la app falla de formas confusas:
  `allowedDevOrigins` en `frontend/next.config.ts` (si falta, la página carga pero React nunca
  hidrata: el login no responde y no hay error visible) y `_ORIGENES_DEV` en
  `backend/src/shared/presentation/app.py` (CORS; solo hace falta si algo llama al backend
  fuera del rewrite `/api/*` de Next, que es same-origin).
- **Playwright no está instalado en este host** (no hay node/nvm ni `~/.cache/ms-playwright`);
  la suite la corre CI. Si hace falta correrla local, se instala primero (node + `npm ci` en
  `frontend/` + `npx playwright install --with-deps chromium`). Gotchas que siguen valiendo:
  `frontend/node_modules` y `frontend/.next` son puntos de montaje de volúmenes de Docker (los
  crea como directorios vacíos de root; si vuelven a quedar así tras un `compose up`, `rmdir` +
  `mkdir` como usuario propio — el contenedor usa sus volúmenes y no se entera); y
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
4, en la app de escritorio), todas sobre **este mismo checkout** — no hay worktrees ni ramas por
sesión. Consecuencia: `git status` mezcla el trabajo en curso de todas, y un archivo puede estar
siendo editado por otra sesión en este momento.

**No hay ningún mecanismo automático que avise de eso** (hubo uno, por hooks, que no sobrevivió
a la migración de máquina del 2026-09-24). O sea: nada va a advertir que otra sesión tocó el
archivo que estás por editar. Las reglas se cumplen a ojo:

- **Releer el archivo antes de editarlo** si pasó un rato desde la última lectura: pudo cambiar
  abajo tuyo.
- **No pisar, revertir ni reformatear trabajo ajeno**, aunque parezca a medio hacer.
- **No commitear lo que no es de la propia tarea**: `git add <archivos propios>` explícito,
  nunca `git add -A` / `git add .`. Ante la duda, `git diff` del archivo antes de stagearlo.
- **Hablar con las otras sesiones.** `ListAgents` lista las que están abiertas; `SendMessage` les
  manda un mensaje y pueden responder. Usarlo cuando hay que tocar un módulo/archivo que otra
  sesión está trabajando (quién toca qué, si algo está a medio hacer), y **siempre** antes de un
  `reiniciar.sh`/`compose up` que va a cortar el stack que las demás están probando.

Si hace falta sí o sí modificar algo que otra sesión está tocando, decírselo al usuario antes de
seguir, no resolverlo pisando.

## Reglas de git

Nada las hace cumplir automáticamente: son reglas, no guardas. No intentar rodearlas; si una
estorba algo que de verdad hace falta, explicárselo al usuario y que decida él.

- **Nunca** `git add -A` / `--all` / `.`, `git commit -a` / `-am`, ni `git push --force`.
  Motivo: con varias sesiones sobre el mismo checkout, esos comandos suben trabajo ajeno o
  reescriben historia compartida. Siempre `git add <archivos propios>` explícito y `git commit`
  sin `-a`.
- **`.githooks/pre-commit`** (≈5 s): si hay `.py` staged en `backend/`, corre `ruff` sobre esos
  archivos dentro del contenedor. Nada más.
- **`.githooks/pre-push`** (instantáneo): lista los commits que se van a subir (leerlos, no
  pushear a ciegas). **No corre ninguna verificación local** desde el 2026-09-02.
- **No hay CI** (ver la sección de arriba): ningún push dispara verificación en ningún lado.
  El workflow de GitHub Actions (`.github/workflows/ci.yml`) quedó en el repo como referencia
  de qué tiene que correr — backend `lint-imports` + `ruff` + `mypy` + pytest unit +
  integración + gates §4/§6/§8/§11, frontend eslint + `tsc --noEmit`, y la suite de Playwright
  — pero nadie lo ejecuta, y el usuario decidió el 2026-09-24 dejarlo así por ahora. Antes de
  volver a proponer un runner, saber que hay dos obstáculos reales (ver el comentario de
  `.gitea/workflows/ci.yml`): el certificado de `gitea.cdsa.com.ar` está vencido desde el
  2025-10-13 y es autofirmado, y el runner necesitaría el socket de Docker de esta máquina.
  La suite de Playwright es hermética (`tests/global-setup.ts` levanta un backend mock en 18099
  y cada spec mockea sus datos con `page.route()`: no toca el backend real ni datos reales),
  así que correrla local es seguro — pero hoy Playwright no está instalado en este host.
- Los hooks de git se activan por clon con `make hooks` (`git config core.hooksPath
  .githooks`). `--no-verify` existe, pero usarlo es una decisión del usuario, no de Claude.

`make check` es la verificación canónica que exige `ARCHITECTURE_GUIDE.md` y, sin CI, el único
lugar donde corre es acá.

### Cuándo pushear (decisión del usuario, 2026-08-21)

`develop` es la rama de trabajo y `origin` — el Gitea de Canal Directo
(`git@gitea.cdsa.com.ar:imartinez/Helpdesk-manager.git`, por SSH) — es el **respaldo**: lo que
no está pusheado existe solo en el disco de esta PC. El remoto `github` quedó abandonado el
2026-09-24; no pushear ahí. Regla:

- **Pushear al cerrar cada bloque de trabajo** (feature terminada y probada, fin de una
  migración) **y siempre al final del día de trabajo**, antes de apagar la máquina.
- **Hacerlo proactivamente cuando se detecte la condición**, sin esperar a que el usuario lo
  pida de nuevo: **≥5 commits sin pushear o el más viejo con más de 24 h** (lo avisaba el hook
  de arranque, hoy ausente: revisarlo a mano con `git log origin/develop..`). En ese caso, al
  terminar la tarea en curso (no en el medio), correr `git push` y decirlo en el resumen final.
  Nunca `--no-verify`.
- **Una sola sesión pushea.** Si `git status`/el registro de sesiones muestran que otra
  sesión está commiteando en ese momento, esperar a que termine o coordinar por
  `SendMessage`; pushear en paralelo desde varias sesiones solo duplica el `pre-push`.
- El `pre-push` casi no cuesta (lista los commits y corre `ruff` sobre los `.py` de backend del
  rango), pero igual pushear por bloque de trabajo y no por cada commit chico. Nunca
  `force push`.

`make help` lista el resto de atajos (`status`, `restart-*`,
`recreate-backend`, `logs-*`, `mailpit`, `typecheck-frontend`). Antes de una migración o un
script que toque datos: `make db-backup TAG=<motivo>` (pg_dump a `backups/`, ignorado por git);
para volver atrás, `make db-restore FILE=backups/<archivo>.dump` (pide confirmación, detiene el
backend mientras restaura).
