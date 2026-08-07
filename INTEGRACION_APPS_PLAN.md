# Plan de unificación: HelpDesk Manager como plataforma definitiva

**Decisión tomada (confirmada por el usuario):** el nombre de la app padre se mantiene —
**HelpDesk Manager**. Esta va a ser la app definitiva. Se reescribe todo a **un solo stack**,
sin límite de tiempo autoimpuesto, siguiendo `ARCHITECTURE_GUIDE.md` (en esta misma carpeta).
No es una integración por gateway/proxy — es una reescritura completa, ejecutada por etapas
(strangler-fig) para no perder producción en el camino.

Esta carpeta (`HelpDeskManager-Unificacion/`) es el espacio de trabajo dedicado a planificar
y ejecutar la unificación — separado del repo de código actual (`HelpDeskManager-Web/`) para
no arrancar cada conversación con todo el ruido de un codebase existente. Una conversación
nueva debería empezar leyendo este archivo y `ARCHITECTURE_GUIDE.md` completos antes de tocar
código en ningún repo.

Este documento es el resultado de auditar el stack real de las 6 apps (se leyeron
`package.json`, `requirements.txt`/`pyproject.toml`, `docker-compose.yml`,
`CLAUDE.md`/`AGENTS.md`/ADRs de cada repo — nada asumido). Se actualiza a medida que se
ejecuta: marcar checkboxes, no reescribir el diagnóstico salvo que cambie la realidad del código.

Estado: **decisiones de arquitectura cerradas, arranque definido (auth-first desde VacaSync),
ejecución no iniciada.**

---

## 1. Diagnóstico por app (hechos, no opiniones)

| App | Frontend actual | Backend actual | DB actual | Background jobs | Deploy actual | Auth propia |
|---|---|---|---|---|---|---|
| **HelpDeskManager-Web** (padre) | Next.js 15 (App Router), React, TS | FastAPI monolítico (`main.py`, 790 líneas, un solo router extraído) | Postgres (Neon, serverless) vía SQLAlchemy | Ninguno propio (subproceso Playwright bajo demanda para token ERS) | Vercel (front) + VM GCP Docker (back, puerto 8010) | **No** (header hardcodeado "Administrador") |
| **SDSInsumos** | Vue 3 + Vite + TS + Tailwind | FastAPI (routers separados) | SQLite WAL | Poller horario (`POLL_INTERVAL_MINUTES`) | Docker/Portainer | No |
| **Calendario-Web (VacaSync)** | React 18 + Vite, react-router, axios | Node/Express + TS + Prisma | Postgres (14 modelos) | No embebido | Docker Compose local | Sí — JWT propio, roles, aislamiento sectorial |
| **Liquidacion-Prestadores** | Next.js 14 (App Router) + TS | FastAPI + SQLAlchemy | SQLite | No embebido | Docker Compose local | No — CORS abierto |
| **Printer-Logs-Analyzer** | React + Vite + Zustand | FastAPI, sin ORM (`psycopg2` + migraciones SQL propias) | Postgres 17 (ya vive en la VM del padre) | **APScheduler** — sync c/30min + 2 cron diarios, en producción hoy | Frontend Vercel, backend en la misma VM que el padre (puerto 8082) | `x-api-key` simple |
| **STC Cloud** | React 19 + Vite + Recharts | Node/Fastify + TS | Postgres 16 + TimescaleDB + Redis/BullMQ | `heartbeatMonitor` (barrido c/5min) + `alertWorker` (BullMQ) + agente Windows nativo (SNMP) | Docker Compose prod, nginx propio | Sí — JWT + refresh, rate limiting, secretos AES |
| ↳ **Contadores** (módulo del padre, no es app aparte) | Next.js 15, dentro de `(modules)/contadores/` del padre | FastAPI del padre — sin separar en router propio, vive en `main.py` (~250 de sus 790 líneas) | Postgres del padre (Neon hoy) vía SQLAlchemy — configs de clientes FTP/SDS/ERS | Ninguno periódico — todo on-demand, salvo el subproceso Playwright bajo demanda que renueva el token de ERS (ya listado en la fila de arriba) | Misma VM/deploy que el padre | Ninguna propia — hereda el auth del padre |

El módulo "STC" que ya existe en el sidebar del padre **no es STC Cloud** — es una utilidad
desechable de parseo de IPs, sin relación de código con el Fastify de STC Cloud. Se elimina/
reemplaza cuando entra el STC Cloud real (Fase por-app, más abajo).

**Nota (2026-08-07):** el diagnóstico original no incluía los módulos de negocio que ya viven
*dentro* del padre HelpDeskManager-Web (se lo trató solo como shell/auth). "Contadores" es uno
real y no trivial (~2200 líneas entre `proyeccion_contadores.py`, `sds_api.py`, `ers_api.py` y
los endpoints de `main.py`): 8 herramientas (descarga SDS/ERS/FTP, procesar DB3, estimación en
0, suma fija, proyección con algoritmo propio, calculadora manual). Se agrega al diagnóstico y
al orden de migración de Fase 0 (ver checklist). Puede haber otros módulos del padre en la
misma situación (ej. `recursos/`, mencionado en `UI_UX_ROADMAP.md`) — no auditados todavía, no
asumir que están cubiertos.

### Riesgos de negocio que hay que portar fiel, no reinventar
- **SDSInsumos:** idempotencia de pedidos SOAP (`persistNewSupply` + verificación posterior
  con `getSupplyById`), poller alineado a SDS, ventana de validación configurable.
- **VacaSync:** saldo de vacaciones **cronológico progresivo** (no estático), aislamiento
  sectorial de managers validado en servidor, recursión de carry-over ya marcada como frágil.
- **Liquidacion-Prestadores:** motor de reglas data-driven (ALT001–ALT009), numeración con
  dígito verificador módulo-10 para dedup contra WS de AyC, sync que hoy pisa el estado local
  de revisión (riesgo conocido, documentado en su propio ADR-001).
- **Printer-Logs-Analyzer:** scheduler compartiendo DB con contenedores ya en producción.
- **STC Cloud:** agente Windows con URL de backend fija — el contrato de API no puede romperse
  sin coordinar el rollout de agentes ya instalados en campo.
- **Contadores:** el algoritmo de proyección (`proyeccion_contadores.py`, detección de reset de
  contador, ventana de tendencia reciente, umbral mínimo de consumo) genera el CSV que alimenta
  **SiGes** (sistema de facturación) — un error de proyección impacta directo en lo que se
  factura a un cliente, mismo nivel de riesgo que el motor de reglas de
  Liquidacion-Prestadores. La integración con ERS (Epson) no tiene API oficial: autentica
  scrapeando el portal vía un subproceso Playwright que persiste token + cookies de Incapsula a
  un archivo (`ers_token.json`) — punto frágil a preservar o mejorar, no a romper. Las
  credenciales de HP SDS están **hardcodeadas en texto plano** en `sds_api.py` (API key y
  secret) — al migrar hay que moverlas a variables de entorno, no portarlas tal cual.

Estos 6 puntos son la razón por la que la reescritura se hace con **tests de caracterización**
antes de tocar cada módulo (ver Fase 3).

---

## 2. Arquitectura objetivo

### Stack único
- **Frontend:** Next.js 15 + React + TS + Tailwind (ya es el del padre y el de
  Liquidacion-Prestadores).
- **Backend:** FastAPI + Python, como **monolito modular** — un solo servicio desplegable,
  con límites de dominio claros por módulo (`domain/insumos/`, `domain/liquidaciones/`,
  `domain/vacaciones/`, `domain/parque-impresoras/`, `domain/stc/`), siguiendo la estructura
  de capas de `ARCHITECTURE_GUIDE.md` §2–3 (`domain → application → infrastructure ←
  presentation`). **No microservicios** — con este tamaño de equipo y uso, separar en
  servicios independientes desde el día uno viola YAGNI (§1 de la guía); se reconsidera solo
  si un módulo concreto demuestra necesitar escalar o desplegarse por separado.
- **Base de datos:** un solo Postgres, **autoalojado en contenedor** (no Neon/serverless
  externo). Migran a él: las 2 SQLite (SDSInsumos, Liquidacion-Prestadores), el Prisma de
  VacaSync, el Postgres de HelpDeskManager-Web (hoy en Neon), y el Postgres+TimescaleDB de
  STC Cloud (Timescale es una **extensión** de Postgres, no un motor aparte — se activa sobre
  la misma instancia sin perder la funcionalidad de series temporales).
- **Deploy:** todo (frontend + backend + DB) corre como stack(s) de **Portainer** en la VM de
  GCP / red corporativa, detrás de un **proxy inverso con dominio local** (patrón ya en
  producción con SDSInsumos, ej. `sdsinsumos.cdsa.com.ar` — la app unificada seguiría el mismo
  esquema, ej. `helpdesk.cdsa.com.ar`), **accesible solo desde la red corporativa**. Decisión
  del usuario (2026-08-06): se abandona Vercel como hosting del frontend — al ser una
  herramienta interna, no necesita exposición pública. Esto reemplaza el esquema actual de
  HelpDeskManager-Web (Vercel + VM GCP con Neon externo).
- **Auth:** uno solo, y es la **primera pieza que se construye**, no la última. Decisión del
  usuario: la UI de login/auth se porta a partir de la de **VacaSync** (Calendario-Web) —
  reutilizar su pantalla y flujo como base visual/UX del auth unificado, no reinventarla desde
  cero. El modelo de permisos **no es de roles fijos** (ADMIN/MANAGER/usuario) — tiene que ser
  una matriz usuario × módulo (y potencialmente usuario × acción dentro de un módulo) **100%
  editable por el usuario admin** desde una pantalla propia, sin tocar código para dar/quitar
  acceso a un módulo. El aislamiento sectorial de VacaSync (managers solo ven su departamento)
  es la referencia conceptual más cercana, pero acá se generaliza a "qué módulos y qué acciones
  ve cada usuario", no solo sectores de un módulo de vacaciones.
- **Agente Windows de STC Cloud:** sigue siendo un cliente nativo aparte (SNMP + `.exe`). Solo
  se reescribe su contraparte de servidor (ingesta, alertas); el contrato de API se versiona
  y se mantiene compatible para no romper agentes ya instalados en campo.

### Background jobs: **APScheduler + Postgres, sin Redis/Celery**

Decisión cerrada. Motivo (detalle completo en el historial de este documento / conversación):
de los 4 jobs reales en todo el ecosistema, 3 son cron periódico puro (poller de SDSInsumos,
sync de Printer-Logs-Analyzer —ya en producción con APScheduler—, heartbeat monitor de STC
Cloud) y el único que tiene forma de cola (`alertWorker` de STC Cloud) se resuelve con un
**patrón outbox sobre Postgres**: la ingesta de eventos SNMP escribe filas con
`status=pending`, un job de APScheduler las levanta cada pocos segundos, procesa y marca
`done`/`failed` con reintentos por columna. No se suma Redis como pieza operativa nueva.
Es una decisión reversible: si el volumen de alertas lo justifica en el futuro, la migración
a Celery/Redis queda aislada a ese único módulo (medir antes de optimizar, §11 de la guía).

---

## 3. Herramientas, skills y servidores MCP

Estado verificado: **no hay servidores MCP configurados** en ningún repo (`mcpServers: {}`
en `.claude.json` global y de proyecto; sin `.mcp.json` en ninguno de los 6 repos).

### Ya disponibles (sin instalar nada)
- **`Bash`/`PowerShell`** + `gh` CLI — git multi-repo, Docker local, `gcloud` (verificar
  instalación en Fase 1).
- **Skill `example-skills:webapp-testing`** (Playwright) — para las pruebas end-to-end de
  cada módulo migrado y, sobre todo, para correr los **tests de caracterización de UI**
  (grabar comportamiento de la app vieja, comparar contra la nueva).
- **Skill `run`** — para levantar cada app vieja localmente mientras se le extraen los tests
  de caracterización.
- **Agente `Explore`** — para releer un repo hijo antes de portar su módulo.

### Recomendado sumar
- **MCP server de Postgres genérico** — conexión directa (VPN/red corporativa) por connection
  string al Postgres consolidado autoalojado en Portainer, y mientras tanto a los Postgres
  viejos de cada app (VacaSync, Printer-Logs-Analyzer, STC Cloud) para comparar datos durante
  la migración. **Pendiente elegir paquete concreto** (ver nota de seguridad abajo) — prioridad
  alta desde la Fase 2 (consolidación de schema).
- **MCP de GitHub** (opcional, `gh` CLI ya cubre la mayoría) — solo si el volumen de PRs
  cruzados lo justifica.

> **Nota de seguridad (2026-08-06):** al buscar candidatos de MCP de Postgres se encontraron
> trampas — evitar instalar sin verificar mantenedor real:
> - `@neondatabase/mcp-server-neon` (npm) — deprecado por el propio mantenedor, y de todos
>   modos irrelevante ahora que la DB consolidada no vive en Neon.
> - `@modelcontextprotocol/server-postgres` (npm) — deprecado/sin soporte oficial.
> - `mcp-server-postgres` (npm) — **no es un servidor real**, es un paquete-canario de un
>   proyecto de bug-bounty de "npx-confusion" (nombre elegido para que agentes de IA lo
>   instalen por error al buscar "postgres mcp"). No instalar bajo ningún concepto.
> Antes de instalar cualquier MCP de Postgres, verificar mantenedor activo y adopción real,
> no tomar el primer resultado de `npm search`/`npm view`.

### Fuera de alcance
- `ANTIGRAVITY_SKILLS.md` del repo padre documenta un framework de skills de **otro agente**
  (Antigravity/Windsurf) — no es compatible con Claude Code, no se usa.
- No se necesita MCP de Docker/GCP dedicado: `gcloud`/`docker` por Bash alcanzan.
- No se suma Redis/Celery (ver §2, decisión de background jobs).
- `claude-mem` (plugin npm de terceros, sistema de memoria/compresión) — evaluado y
  descartado (2026-08-06): se superpone con la memoria nativa de Claude Code ya activa en
  este proyecto (`.claude/.../memory/`), no suma valor adicional que justifique un plugin de
  terceros con hooks en cada sesión.

---

## 4. Checklist de ejecución

### Fase 0 — Cerrado
- [x] Estrategia: reescritura completa a un solo stack (Next.js + FastAPI + Postgres).
- [x] Arquitectura de backend: monolito modular, no microservicios.
- [x] Background jobs: APScheduler + Postgres (outbox), sin Redis/Celery.
- [x] Nombre de la app padre: se mantiene **HelpDesk Manager**.
- [x] **Arranque:** lo primero que se construye es auth, no un módulo de negocio. UI portada
      desde la pantalla de login de VacaSync. Permisos = matriz usuario × módulo (× acción),
      100% administrable desde la UI por el usuario admin — no roles fijos hardcodeados.
- [x] **Deploy objetivo:** todo (frontend + backend + DB) en Portainer / red corporativa,
      proxy inverso con dominio local, sin exposición pública — se abandona Vercel/Neon (ver
      §2 "Deploy" y "Base de datos").
- [x] **Orden de migración de los módulos de negocio** (confirmado 2026-08-07, una vez el auth
      esté en pie): **Contadores → Liquidacion-Prestadores → Printer-Logs-Analyzer →
      SDSInsumos → VacaSync → STC Cloud.** Contadores va primero pese a alimentar facturación
      (mismo riesgo que Liquidacion-Prestadores) porque es el de menor esfuerzo de migración:
      no tiene DB externa que consolidar ni deploy propio que apagar — ya vive en el FastAPI
      del padre, solo hay que reubicarlo a la nueva estructura de capas. Sirve como piloto de
      bajo riesgo *operativo* del patrón de migración, aunque su lógica de negocio (algoritmo
      de proyección) sí requiere tests de caracterización serios antes de tocarla (ver §1,
      riesgos de negocio).
- [ ] Qué hacer con el módulo "STC" dummy actual del padre (eliminar antes de traer STC
      Cloud real).

### Fase 1 — Preparar herramientas
- [x] Verificar `gcloud` CLI instalado y autenticado — confirmado (2026-08-06): cuenta activa
      `argivan92@gmail.com`, proyecto `clean-circuit-405918` correcto.
- [x] Entorno base verificado (2026-08-06): Node 24, Python 3.12/3.14, git, `gh`, Docker, todo
      ya instalado, nada faltante.
- [x] Instalado, registrado y validado `postgres-mcp` (crystaldba, PyPI, mantenido
      activamente — ver nota de seguridad en §3) vía `uv tool install postgres-mcp --python
      3.12` (aislado, sin tocar site-packages compartidos). Nota: la versión publicada 0.3.0
      requiere fijar `mcp<2.0.0` (`uv pip install "mcp<2.0.0" --python <venv del tool>`) — la
      última release de mcp (2.0.0) reestructuró `mcp.server.fastmcp` y rompe postgres-mcp
      0.3.0. Registrado como `postgres-vacasync` con `claude mcp add ... --access-mode
      restricted` (solo lectura) contra la DB de VacaSync (`localhost:5432`, scope local de
      este proyecto). Se conecta cuando el stack de VacaSync está levantado (Docker Desktop).
- [x] Skill `example-skills:webapp-testing` operativo (2026-08-06): Playwright 1.60
      (Python)/1.62 (Node) instalados, Chromium ya descargado en
      `%LOCALAPPDATA%\ms-playwright`.
- [x] Relevadas env vars de las 5 apps hijas + padre → `.env.example` nuevo en
      `HelpDeskManager-Unificacion/`, agrupado por módulo de dominio. Encontrado a resolver en
      Fase 2: `INSIGHT_API_KEY`/`INSIGHT_API_SECRET` aparecen tanto en insumos como en
      parque-impresoras — confirmar si es la misma integración HP Insight.

### Fase 2 — Fundaciones del monolito (arranca por auth, no por un módulo de negocio)
- [x] Esqueleto de capas (`domain/application/infrastructure/presentation`) del nuevo backend
      FastAPI, con módulo real `auth` (completo: entidades, value objects, repositorios,
      casos de uso, routers) y módulos vacíos por dominio (`insumos`, `liquidaciones`,
      `vacaciones`, `parque_impresoras`, `stc`) — confirmado leyendo
      `backend/src/modules/*` (2026-08-07). **Falta** módulo `contadores` (se crea al arrancar
      Fase 3 de este módulo).
- [x] Login portado a Next.js (`login-form.tsx`, `auth-split-layout.tsx`) + flujo de
      forgot/reset password (`(auth)/forgot-password/`, `(auth)/reset-password/`,
      `use-password-reset.ts`) + change-password modal — más completo que el alcance
      original (que solo pedía portar el login).
- [x] Schema de permisos usuario × módulo (× acción) editable: `permission_repository`,
      `module_catalog_repository`, `well_known_permissions.py`, `admin_permissions_router.py`
      + pantalla de administración (commit `20b634b`).
- [x] Backend de auth completo: JWT/sesión (`session_token_generator`, `sqlalchemy_session_repository`),
      hash con Argon2 (no bcrypt como VacaSync — mejora, no regresión), reset de password con
      token + mailer (SMTP real), `admin_users_router.py` para gestión de usuarios.
- [ ] Diseñar y migrar el schema de Postgres consolidado con datos reales de VacaSync/
      Printer-Logs-Analyzer — confirmado (2026-08-07, revisando `alembic/versions/`): las
      migraciones existentes son solo del schema de auth (`baseline`, `auth_schema`,
      `seed_catalog`, `rename_admin_module_label`). Todavía no hay migración de datos de
      VacaSync/Printer-Logs-Analyzer. Sigue abierto, sin corregir.
- [x] Sidebar rediseñado (`shared/components/sidebar.tsx`): renderiza `modules` desde
      `useSession()` — ya es permission-driven, no lista plana hardcodeada (commit `19bff67`).
- [x] **Corrección (2026-08-07): sí hay suite de tests de auth, y pasa al 100%.** Dije antes
      que no había tests — fue un error mío, un `find` con `maxdepth 3` no llegó a
      `tests/integration/infrastructure/auth/` ni a `tests/unit/domain/auth/`. Corrida real:
      `pytest tests/` → **61 passed** (tests de dominio: value objects/entities de auth —
      `email`, `raw_password`, `permission_set`, `session`, `user`, etc. — más tests de
      infraestructura: Argon2, generador de tokens, repositorios SQLAlchemy de
      user/session/login_attempt). Los 10 tests de integración fallaban en el primer intento
      por `ConnectionRefusedError` — no es un test roto, es que requieren el Postgres de test
      dedicado (`docker-compose.test.yml`, contenedor `helpdesk-db-test`, puerto 5440) y no
      estaba levantado; al levantarlo (`docker compose -f docker-compose.test.yml up -d`)
      pasaron los 61/61. Lo que sigue sin existir es un test de **punta a punta** de la UI
      (login real por navegador → admin edita permisos de otro usuario → ese usuario no ve el
      módulo en el sidebar) — los 61 tests son unitarios/de integración de infraestructura, no
      e2e. Eso no bloquea arrancar Fase 3 de Contadores.

### Fase 3 — Por módulo (repetir en el orden de Fase 0, uno a la vez)
- [ ] **Tests de caracterización primero:** correr la app vieja (skill `run`), capturar
      comportamiento real (inputs → outputs) de los flujos críticos y de la lógica frágil
      listada en §1, antes de escribir una sola línea del módulo nuevo.
- [ ] Portar el modelo de datos del módulo al Postgres consolidado (migración con datos
      reales, no solo schema).
- [ ] Reescribir domain/application/infrastructure siguiendo `ARCHITECTURE_GUIDE.md`,
      validando contra los tests de caracterización — deben pasar antes de tocar la UI.
- [ ] Portar la UI a Next.js dentro de `(modules)/<módulo>/`.
- [ ] Prueba end-to-end con Playwright: flujo completo desde el sidebar del padre.
- [ ] Correr en paralelo (app vieja + módulo nuevo) con tráfico real por un período de
      observación antes de apagar la app vieja — **no hay cutover en frío** en los módulos
      con lógica frágil (SDSInsumos, VacaSync, Liquidacion-Prestadores).
- [ ] Apagar la app vieja de este módulo (repo/deploy) solo después del período de
      observación sin discrepancias.
- [ ] Actualizar `PROJECT_CONTEXT.md` del padre.

#### Fase 3 — Contadores (primer módulo, en curso — 2026-08-07)
- [x] **Tests de caracterización:** corrida la app vieja en vivo (backend local puerto 8011,
      contra la Neon real de producción, confirmada por `docker inspect` en la VM — solo
      lectura, sin tocar endpoints que escriben en la DB; FTP no probado en vivo, requiere
      autorización aparte por los 231 clientes reales). Cubiertas las 8 herramientas: SDS, ERS
      (incluida la renovación forzada de token vía Playwright, ~7.5s), DB3, en0, suma fija,
      calculadora, y el algoritmo de proyección (8 tests nuevos en
      `HelpDeskManager-Web/backend/tests/test_proyeccion_caracterizacion.py`, más el existente
      `test_proyeccion.py` — 9/9 pasan). Hallazgos y comportamientos no obvios (incluidos
      posibles bugs a decidir si se preservan) documentados en
      `CONTADORES_CARACTERIZACION.md` (esta carpeta) — leer antes de reescribir el módulo.
- [x] **Modelo de datos portado (2026-08-07), con datos reales.** Creado
      `backend/src/modules/contadores/` (domain: entities `FtpClient`/`MeterClientConfig`,
      value object `MeterSource`, repos `Protocol`; infrastructure: modelos SQLAlchemy con PK
      UUID + repos concretos). Migración Alembic `fc502aa52749` (reversible, verificado
      downgrade+upgrade) aplicada al Postgres consolidado (`helpdesk-db`, puerto 5439). 18 tests
      nuevos (unit + integración), 79/79 pasan en total. `ruff`/`mypy`/`import-linter` limpios —
      se agregaron contratos `contadores-domain-no-frameworks` y `modules-are-independent` a
      `.importlinter` (antes solo existía el de auth). Datos reales copiados desde Neon con
      `scripts/migrate_contadores_data_from_neon.py`: **231 filas de `ftp_clients` + 5 de
      `meter_client_configs`** verificadas en la DB nueva. `resource_links` NO se portó — es
      del módulo `recursos/`, no de Contadores (ver nota de §1 sobre gap no auditado).
- [~] Reescribir domain/application/infrastructure — **5 de 8 herramientas completas
      (2026-08-07): Proyección, Calculadora manual, DB3→CSV, Estimación en 0, Suma Fija.**
      Todas de punta a punta (domain → application → infrastructure → presentation), cada una
      gateada con `require_permission(EXPORT)`, endpoints:
      `POST /api/contadores/{proyeccion,calc,db3,en0,suma-fija}`. Validadas contra tests de
      caracterización (mismos números que la app vieja) + tests end-to-end con archivos reales
      (Excel/CSV/SQLite). **116/116 tests, `ruff`/`mypy`/`import-linter` limpios.**
      Faltan 3: SDS, ERS (integraciones externas HP/Epson), gestión de clientes FTP — quedan
      para después por requerir manejo de credenciales/red externa, más deliberación.
      **Corrección (2026-08-07):** los dos "bugs" documentados antes (shift de en0, `dias_est`
      negativo de la calculadora) resultaron ser falsos positivos — comparé contra código
      muerto (`csv_en0.py`, `estimador_manual.py`) que `main.py` ni siquiera importa; la
      implementación real (`counters_tools.py`) es más simple y su comportamiento es correcto.
      También confirmado código muerto: `ejecutar_autoestimacion` (importada, nunca llamada).
      Detalle en `CONTADORES_CARACTERIZACION.md`.
      **Simplificado a propósito (YAGNI):** el dashboard de KPIs con celdas coloreadas y la hoja
      "Leyenda"/"Validación" de la app vieja no se portaron — son polish visual, no reglas de
      negocio; el Excel nuevo tiene hojas Proyección/Auditoría/Resumen con datos correctos.
- [x] Portar la UI a Next.js dentro de `(modules)/contadores/` (`frontend/src/features/contadores/`, `frontend/src/app/(app)/contadores/page.tsx`).
- [x] Prueba end-to-end con Playwright (`frontend/tests/contadores.spec.ts`).
- [x] Activación en catálogo de permisos (`is_enabled=True` en migración `6d910a2b8e39`).
- [ ] Correr en paralelo con la app vieja antes de apagarla.
- [ ] Apagar el módulo Contadores de la app vieja.
- [ ] Actualizar `PROJECT_CONTEXT.md` del padre.

### Fase 4 — STC Cloud (caso especial, va último)
- [ ] Migrar `heartbeatMonitor` y `alertWorker` (BullMQ → outbox Postgres + APScheduler,
      según decisión de §2) manteniendo el contrato de API que consume el agente Windows.
- [ ] Versionar el endpoint de ingesta del agente para poder desplegar el backend nuevo sin
      romper agentes ya instalados en campo (rollout coordinado, no big-bang).
- [ ] Migrar Timescale como extensión del Postgres consolidado; validar performance de
      queries de series temporales contra el volumen real de datos históricos.
- [ ] El resto del checklist de Fase 3 aplica igual (caracterización, paralelo, cutover).

### Fase 5 — QA final y despliegue
- [ ] Suite Playwright completa sobre los 6 módulos ya migrados, en claro/oscuro,
      desktop/mobile.
- [ ] Confirmar que no queda ningún contenedor/DB de las apps viejas corriendo en la VM.
- [ ] Auditoría de que el auth unificado cubre todos los endpoints (nada quedó con CORS
      abierto ni con el `x-api-key` viejo de Printer-Logs-Analyzer).
- [ ] Documentar en `PROJECT_CONTEXT.md` la arquitectura final consolidada.

---

## 5. Referencias

- `ARCHITECTURE_GUIDE.md` (esta misma carpeta) — principios, capas, testing, seguridad;
  norma de todo el rewrite. Antes vivía en la raíz de `Proyectos/`; se movió acá porque
  ningún otro repo lo referenciaba por path (verificado con grep antes de mover).
- `HelpDeskManager-Web/PROJECT_CONTEXT.md` — infraestructura real de la VM y Neon.
- `SDSInsumos/CLAUDE.md` — reglas de idempotencia SOAP y checklist de calidad propio.
- `Liquidacion-Prestadores/ADR_001_integracion_ws_ayc.md` — riesgos del sync con AyC.
- `Calendario web/.agents/AGENTS.md` — reglas de aislamiento sectorial y cálculo de saldos.
- `Printer-Logs-Analyzer/CLAUDE.md` y `docs/deploy.md` — patrón APScheduler ya en producción.
- `STC cloud/SECURITY_AUDIT.md` — manejo de secretos y JWT del portal/agente.
- `HelpDeskManager-Web/backend/services/proyeccion_contadores.py` (algoritmo de proyección),
  `sds_api.py`/`ers_api.py` (integraciones HP SDS / Epson ERS), `backend/main.py` (endpoints
  `/api/contadores`, `/api/sds`, `/api/ers`, `/api/ftp`, `/api/tools`) — módulo Contadores.
- `docs/adr/007-vocabulario-de-permisos-en-shared-excepcion-de-presentation.md` — por qué
  `ModuleKey`/`ActionKey`/`Permission` viven en `shared/` pero `require_permission` sigue en
  `auth`, con la excepción de import-linter acotada a la capa `presentation`.
