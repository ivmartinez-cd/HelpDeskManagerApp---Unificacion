# Printer-Logs-Analyzer — caracterización y análisis de migración

Fecha: 2026-08-15. Fuente: lectura completa del código real en
`D:\Dev\Trabajo\Printer-Logs-Analyzer` (backend, frontend, migraciones SQL, docker-compose,
`.env.example`, CLAUDE.md propio). Nada asumido de documentación sin verificar contra código.

> **Actualización del mismo día:** la primera pasada se hizo sobre un snapshot viejo (rama
> `feature/mobile-error-search`, 2026-06-16). Al detectarlo el usuario, se actualizó el repo
> local a `origin/main` (`3d28a96`, 2026-07-17) y se re-verificó todo — los cambios están
> integrados en este documento y resumidos en §12. **Confirmado por el usuario (2026-08-15):
> el 17-jul es lo último que tocó — no hay trabajo sin pushear en la PC laboral. Esta
> caracterización queda congelada sobre `3d28a96`.**

**Alcance decidido por el usuario (2026-08-15):** migrar ahora **solo el análisis de logs**.
El resto (Avisos/mantenimiento preventivo, Monitor de flota, app mobile) queda para una
revisión posterior — al usuario no le gusta cómo está armado y se va a repensar, no portar tal
cual.

**Decisiones del usuario (2026-08-15, segunda ronda):**
- **Entrada principal = scraping SDS por serial; pegar TSV queda como backup** explícito para
  cuando el scraping deje de funcionar (el portal puede cambiar sin aviso). La UI nueva debe
  reflejar esa jerarquía (búsqueda por serial primero, pegar logs como camino secundario
  visible pero no protagonista).
- **El design handoff lo está construyendo el usuario** — no generarlo acá; esperar a que lo
  entregue antes de tocar frontend.
- **Arrancar por los tests de caracterización** (§11 paso 1).

---

## 1. Estado real del legacy

| Aspecto | Realidad verificada |
|---|---|
| Frontend | React 19 + Vite + TS estricto + Zustand. Sin framework de UI (CSS propio, dark glassmorphism). |
| Backend | FastAPI, **sin ORM**: `psycopg2` con pool propio (`infrastructure/database.py`) y migraciones SQL numeradas 001–011 (`scripts/run_migrations.py`, tabla `schema_migrations`). |
| DB | Postgres 17 (`docker-compose.yml`). **Fallback automático a JSON local** (`backend/data/`, `infrastructure/fallback/`) cuando la DB no responde — el catálogo y los análisis guardados siguen funcionando offline. |
| Auth | `x-api-key` simple (`interface/auth.py`), default `"dev"`. La key viaja **horneada en el build del frontend** (`VITE_API_KEY` en docker-compose) — visible client-side. |
| Background jobs | **APScheduler arranca siempre** en el startup de FastAPI (`application/scheduler.py`): `MaintenanceService.sync_and_check_all(discover=True)` cada 30 min. No hay flag de entorno para desactivarlo. Los mails solo salen con `send_mail=True` explícito (el job programado no lo pasa), pero el job sí pega contra la Insight API real y escribe en la DB. |
| Rate limiting | slowapi por endpoint (60/min preview, 30/min upsert, etc.). |
| Tests | 186 pytest backend + 187 vitest frontend (según README/CI badge). |
| Deploy | `INTEGRACION_APPS_PLAN.md` §1: frontend en Vercel, backend en la misma VM que el padre (puerto 8082). El README menciona además Render como backend — **a confirmar cuál es el productivo real antes de migrar datos**. CORS también permite `localhost:8081`. |
| Extra no auditado antes | Hay una **app mobile Expo/React Native** (`mobile/`) en el repo — no estaba en el diagnóstico de las 6 apps. Fuera de alcance; decidir su destino en la revisión posterior. |

> **Precaución operativa para correr el legacy en local** (tests de caracterización): el
> scheduler arranca solo y no hay flag para apagarlo. No manda mails por sí solo, pero pega a
> la Insight API real cada 30 min con `discover=True` (puede dar de alta dispositivos en las
> tablas de mantenimiento de la DB apuntada). Correr con una DB local descartable y sesiones
> cortas, o comentar `start_scheduler()` en `interface/api.py` antes de levantar.

---

## 2. Mapa funcional — qué entra ahora y qué queda para después

### Dentro del alcance «análisis de log»

| Feature | Endpoints legacy | Código clave |
|---|---|---|
| Parseo + análisis de logs | `POST /parser/preview`, `POST /parser/validate` | `application/parsers/log_parser.py`, `application/services/analysis_service.py`, `interface/utils.py` |
| Catálogo de códigos de error | `POST /error-codes/upsert`, `GET /error-codes/{code}/solution-proxy` | `infrastructure/repositories/error_code_repository.py`, `infrastructure/content_fetcher.py` |
| Extracción automática SDS por serial | `POST /sds/extract-logs`, `GET /sds/resolve-device` | `application/services/sds_web_service.py` (scraping con `requests` + lxml, sin Playwright) |
| Datos Insight en vivo (consumibles, alertas, contadores del equipo analizado) | `GET /insight/devices/{serial}/alerts`, `/meters` | `application/services/insight_service.py` |
| Diagnóstico IA | `POST /analysis/ai-diagnose` | `application/services/ai_diagnosis_service.py` (Claude, prompt de despacho) |
| Resumen IA para PDF + export PDF | `POST /analysis/pdf-summary` | `application/services/ai_pdf_service.py`; frontend `useExportPdf`, `ExecutivePrintReport` |
| Análisis guardados (snapshots) + comparación + salud del equipo | `POST/GET/PUT/DELETE /saved-analyses`, `/{id}/compare`, `/{id}/health` | `interface/routers/saved_analysis.py`, `compare_service.py`, `degradation_service.py`, `telemetry_repository.py` |
| EWS remoto (link temporal al web server del equipo) | `GET /sds/devices/{serial}/remote-ews` | `sds_web_service.fetch_remote_ews_url` |
| Soluciones técnicas CPMD | tabla `error_solutions`, `scripts/ingest_cpmd.py` | `error_solution_repository.py` — ver decisión pendiente §6.4 |

### Fuera del alcance ahora (a repensar después, no portar tal cual)

- **Avisos / mantenimiento preventivo** (`AvisosPage`, router `maintenance` con ~18 endpoints,
  `maintenance_service.py`, `email_service.py`, tablas `maintenance_*`, scheduler APScheduler,
  mails SMTP de alertas por vida útil de componentes).
- **Monitor de flota** (`MonitorDashboard`, router `fleet`: clients/scan/scan-status,
  `fleet_repository`, `fleet.json`).
- **App mobile** (`mobile/`, Expo).
- Tablas `config_versions` / `audit_log` (migración 001): no las usa ningún router del alcance.

Consecuencia importante (corregida tras actualizar a `origin/main`): el alcance necesita
**un solo background job**: los **snapshots SDS automáticos 2×/día** (cron 08:00 y 20:00 UTC,
`sds_snapshot_service.capture_all_devices`) que refrescan la caché HP, extraen y parsean los
logs de cada equipo trackeado en `saved_analyses` y persisten snapshot + telemetría. En el
monolito entra bajo la disciplina de `DISABLE_BACKGROUND_JOBS` como los demás. El resto del
scheduler legacy (sync de mantenimiento c/30 min, mails) sigue fuera de alcance.

---

## 3. El pipeline de análisis de log, en detalle

### 3.1 Entradas (frontend)

Dos caminos que convergen en el mismo `handleAnalyze` (`useAnalysis.ts`):

1. **Pegar/subir logs** (modal `LogPasteModal`): texto TSV copiado del portal HP o archivo.
2. **Por número de serie** (`autoResolveAndAnalyze` en `DashboardPage`): llama
   `POST /sds/extract-logs` → recibe el TSV ya armado + consumibles en vivo → lo pasa por el
   mismo análisis. Es el camino principal de uso (búsqueda rápida con historial en
   `localStorage`, deep-link `/{serial}`).

`handleAnalyze` dispara **en paralelo** `POST /parser/preview` y `POST /parser/validate`;
del validate salen los `codes_new` (códigos sin catalogar) que la UI ofrece dar de alta.

### 3.2 Parser (`log_parser.py`)

- Formato principal: **6 columnas TSV** — tipo, código, fecha, contador, firmware, ayuda
  (la 6ª opcional; con 5 columnas rellena vacío).
- Antes de parsear, `normalize_log_text` reemplaza **2+ espacios por tab** (el portal HP copia
  tabs como espacios).
- Fallback: columnas separadas por espacios con fecha y hora como dos tokens.
- Fecha `DD-MMM-YYYY HH:mm:ss` con **meses en español** mapeados a inglés (`ene→Jan`…
  `dic→Dec`) y hora `H:mm` zero-padded.
- Detección de header: solo en las **primeras 3 líneas no vacías**, por keywords
  (tipo/type/código/fecha/date).
- Tolerante: cada línea inválida se acumula como `ParserError` (línea, texto, motivo) y sigue;
  la UI las muestra en `ParseErrorsBanner`.
- Tipos válidos solo `error|warning|info` (case-insensitive) → `ERROR|WARNING|INFO`.
- Tope de payload: 2.000.000 chars (`MAX_LOGS_LENGTH`).

### 3.3 Enriquecimiento con catálogo (`error_code_repository.py` + `interface/utils.py`)

Cada evento se cruza contra `error_codes` por código exacto y se anota con
`code_severity/code_description/code_solution_url/code_solution_content`. El repositorio cae
transparentemente a JSON local si la DB no está (seed empaquetado
`fallback/error_codes_seed.json`, copia escribible `data/error_codes_local.json` con lock de
threads y cache en memoria invalidada por upsert).

### 3.4 Incidentes (`analysis_service.py`)

Sin reglas: **un incidente por código**. Eventos ordenados por timestamp, agrupados por código;
severidad del incidente = máxima del grupo; `counter_range = (primer, último contador)`;
clasificación = primera descripción de catálogo no vacía (sino el código); `sds_link` +
contenido = primera URL de solución del grupo. `global_severity` = máxima de todos los eventos.
`id = "{code}-{start_time.isoformat()}"`.

### 3.5 Códigos nuevos → catálogo (`error_codes` router)

`POST /error-codes/upsert`: da de alta/edita un código; si trae `solution_url`, valida SSRF
(`content_fetcher.validate_ssrf_url`) y **fetchea el contenido de la página de solución** para
cachearlo (usando la sesión SDS si es URL de `kaas.hpcloud.hp.com`). El UPDATE usa
`COALESCE(NULLIF(...))`: **un campo vacío nunca pisa un valor existente**.
`GET /{code}/solution-proxy`: trae el contenido en vivo con credenciales SDS, con fallback al
cache guardado.

Además, cada extracción SDS (`extract_help_urls`) actualiza el catálogo con las URLs frescas de
ayuda (JWT del Content Bootstrapper de HP que expiran) y su descripción — el catálogo se
mantiene solo con el uso.

### 3.6 Diagnóstico IA (`ai_diagnosis_service.py`)

- Modelo hardcodeado `claude-sonnet-4-6` (la constante de precios dice "Opus" — inconsistencia
  del legacy), prompt caching, `max_tokens=2048`.
- El backend enriquece cada incidente con la solución técnica (cache o fetch en vivo, cap 3000
  chars) antes de mandar a la IA.
- **El system prompt es lógica de negocio real**: calcula "delta" (páginas impresas después del
  último evento de cada error), clasifica ACTIVO-CRÍTICO (<100) / ACTIVO-MODERADO (100–400) /
  RESUELTO (>400), y de ahí decide `urgencia` (urgente/programar/monitorear) y **`despacho`
  (si/no/remoto) — la decisión de mandar o no un técnico a sitio**, distinguiendo familias de
  error de hardware físico (13/50/51/52/54/57/59/55.xx) de las resolubles remotamente
  (41/10/98/99/33.xx). Respuesta JSON estricta con campos internos `_hw_deltas` y
  `_despacho_logica`. Portar el prompt **textual**, no reescribirlo.
- El diagnóstico **no se auto-persiste** (decisión explícita comentada en el código: guardar es
  acción del usuario).
- `POST /analysis/pdf-summary` (`ai_pdf_service.py`): resumen ejecutivo aparte para el PDF.
- Devuelve tokens + costo estimado USD.

### 3.7 Export PDF

Frontend: `ExecutivePrintReport` (componente A4 oculto en el DOM) + `useExportPdf`
(html2canvas/jspdf o print CSS — hay `print.css`/`print-overrides.css`). Si la IA falla, cae a
reporte estándar sin resumen IA.

### 3.8 Análisis guardados, comparación y salud

- `saved_analyses`: snapshot con `incidents` como **JSONB resumido** (`incident_to_summary`:
  código, clasificación, severidad, ocurrencias, rango de fechas/contadores, sds_link) —
  no guarda los eventos crudos.
- Al guardar/actualizar con `equipment_identifier`, hace **fan-out a
  `device_telemetry_events`** (una fila por incidente, serial limpio) — el historial que
  alimenta el motor de salud. El update borra la telemetría del snapshot antes de re-insertar
  (evita duplicación).
- `POST /{id}/compare`: re-parsea un log nuevo y devuelve diff (códigos nuevos/desaparecidos,
  cambios de ocurrencias, días de diferencia) + **tendencia** (`compare_service.calculate_trend`):
  - *empeoró* si: código ERROR nuevo, o un ERROR existente sube ≥3 ocurrencias, o pasa de 0
    errores a ≥1, o el total de ocurrencias ERROR sube ≥20%.
  - *mejoró* solo si: desapareció al menos un ERROR **y** bajó el total **y** no hay ERRORes
    nuevos. Sino *estable*.
- `GET /{id}/health` (`degradation_service.py`, motor puro y testeado): reglas en orden de
  prioridad — R2 falla post-reparación (ERROR crítico después del último mantenimiento
  registrado → RED), R1 recurrencia (>3 veces en 5.000 páginas o 7 días → RED), R3
  estabilización (10.000 páginas o 15 días limpio → GREEN), default YELLOW. Dos sutilezas
  ganadas a fuerza de bugs, documentadas en docstrings:
  - `_dedup_events`: los logs SDS son **acumulativos** (cada extracción re-lista el histórico);
    sin dedup por `(code, event_time)` cada snapshot re-contaría los mismos eventos.
  - la ventana de páginas solo aplica con `counter > 0` (con counter 0, `latest - 0 ≤ 5000` era
    siempre true y marcaba errores antiquísimos como recurrentes).

### 3.9 Integraciones SDS / Insight

- **Insight API** (`insight_service.py`): JWT vía `POST /PortalAPI/login`, endpoints
  `GET /PortalAPI/api/devices/search?q=serial:{serial}` (resolución de equipo),
  `/devices/{id}/consumables`, `/devices/{id}/alerts/current` + `/history`,
  `/devices/{id}/meters/history`, `/customers/search`, `/devices?customerId=`.
  Mismo host y credenciales (`INSIGHT_API_KEY/SECRET`) que insumos — **queda confirmada la
  duda de Fase 1 del plan: es la misma integración HP Insight**.
- **SDS Web Portal** (`sds_web_service.py`): login por form POST a
  `https://hp-sds-latam.insightportal.net/PortalWeb/login` con `requests.Session` singleton,
  TTL 20 min, doble-check con lock. Eventlogs por AJAX
  (`/devices/{id}/hpsmart/eventlogs?from=...&eventLevel=info|warning|error`, headers
  `x-ekm-usage: dialog` + `x-requested-with`), respuesta XML con CDATA → `html_to_tsv` arma el
  TSV con el header canónico de 6 columnas. Sin Playwright, sin token persistido a disco (a
  diferencia de ERS en Contadores).
- **EWS remoto**: `/devices/{id}/hpsmart/ews` → link JWT one-time a `ews.hpjamservices.com`.

---

## 4. Modelo de datos del alcance

| Tabla | Migración | Contenido | ¿Migrar datos? |
|---|---|---|---|
| `error_codes` | 003 | Catálogo: code (unique), severity, description, solution_url, solution_content | **Sí** — es el activo de conocimiento del módulo (seed local: ~21 KB / decenas de códigos; el productivo puede tener más). |
| `error_solutions` | 004 | Soluciones CPMD por (model_family, code): causa, pasos técnico, FRUs (JSONB), fuente | Según decisión §6.4. |
| `saved_analyses` | 005 + 006 | Snapshots JSONB + `ai_diagnosis` | **Sí** — historial operativo real. |
| `device_telemetry_events` | 011 | Telemetría por serial (FK a saved_analyses, ON DELETE SET NULL) | **Sí** si se porta salud/telemetría (§6.3). |
| `config_versions`, `audit_log` | 001 | Sin uso en el alcance | No. |
| `maintenance_*` | 007–010 | Mantenimiento preventivo | No (fuera de alcance). |

Nota: `saved_analyses.id` ya es UUID y `device_telemetry_events.id` también — la migración de
datos es más directa que la de liquidaciones (no hay remapeo INTEGER→UUID salvo
`error_codes.id`/`error_solutions.id`, que son SERIAL pero nadie los referencia por FK).

---

## 5. Comportamientos no obvios / frágiles a portar fiel

1. `normalize_log_text` (2+ espacios → tab) — sin esto, los logs pegados del portal no parsean.
2. Meses en español en timestamps y hora sin zero-pad.
3. Header detection solo en primeras 3 líneas no vacías.
4. Upsert de catálogo con semántica COALESCE/NULLIF (vacío no pisa).
5. `extract_serial_number`: acepta `"Modelo (SERIAL)"` y extrae lo del paréntesis, uppercase.
6. Dedup de telemetría acumulativa y guarda de counter=0 en el motor de salud (§3.8).
7. Umbrales exactos de tendencia (≥3 ocurrencias, ≥20%) y de salud (3/5.000/7, 10.000/15).
8. Prompt de IA con la regla de despacho (deltas 100/400, familias de hardware) — negocio real
   que decide visitas técnicas; portar textual.
9. Catálogo auto-actualizado en cada extracción SDS (URLs de ayuda con JWT fresco).
10. El update de un análisis guardado crea el reemplazo de telemetría completo (delete+insert).
11. Sesión SDS con TTL 20 min y login con lock (varios requests concurrentes no deben
    disparar logins paralelos).
12. Timeouts explícitos de la extracción: 25 s el extract completo, 20 s el EWS remoto, con
    504 al frontend.

---

## 6. Decisiones a tomar antes/durante la migración (no las tomo yo)

> **Resueltas por el usuario (2026-08-15, tercera ronda):**
> - **§6.2 EWS remoto: SÍ entra en esta entrega.**
> - **§6.5 Modelo de IA: se construye un selector de modelos** que lista los disponibles
>   vía la Models API de Anthropic (`GET /v1/models` / `client.models.list()` — devuelve
>   id, display_name, context window y capabilities por modelo) para elegir desde la UI.
>   **Hoy no hay créditos en la cuenta de Anthropic** — la parte de IA se implementa pero
>   no se puede probar en vivo hasta que haya créditos; los tests van con mocks (como los
>   del legacy).
> - **Centro de notificaciones (§12.5): evaluar qué hacer al portar.** Contexto del
>   usuario: existe para avisar cuando termina el refresh de caché HP (que no avisa solo),
>   pero **no estaba funcionando bien** en el legacy. No portar tal cual: rediseñar el
>   mecanismo de aviso del refresh (puede ser algo más simple que watchers en threads +
>   tabla de notificaciones) al llegar a esa parte.

1. **Mock fallbacks en `/sds/extract-logs` — recomiendo NO portar.** El legacy, si Insight
   falla, inventa un device mock (`device_id` = suma de ords del serial, modelo "HP LaserJet
   Managed MFP", zona "Desconocido (Fallo de Conexión)"); y si el scraping SDS falla, devuelve
   **dos eventos de log hardcodeados falsos** que el usuario ve como si fueran reales. En el
   monolito esto violaría además §6 de la guía (fallback silencioso). Propuesta: error claro
   502/504 + opción de pegar el log a mano.
2. **EWS remoto**: ¿entra en esta primera migración? Es chico (1 endpoint + 1 botón) y útil,
   pero es scraping extra.
3. **Telemetría + salud del equipo (`/health`, degradation engine)**: está acoplado a los
   análisis guardados (fan-out al guardar). Propongo portarlo junto (es motor puro, barato de
   testear), pero es recortable si se quiere una primera entrega mínima.
4. **`error_solutions` / CPMD**: la tabla y `scripts/ingest_cpmd.py` (ingesta de manuales de
   servicio PDF) existen, pero en el flujo de análisis el router los inyecta como dependencia
   sin uso visible en los endpoints del alcance (se usan más en fleet/mantenimiento). Decidir:
   ¿portar tabla+datos ahora, o dejarlo para la segunda pasada?
5. **Modelo de IA**: el legacy fija `claude-sonnet-4-6` con precios desactualizados e
   inconsistentes (comenta "Opus"). Al portar, elegir modelo y centralizar precios (o dropear
   el cálculo de costo).
6. **Rate limiting**: slowapi por endpoint desaparece; el monolito autentica por sesión. ¿Se
   necesita algún límite específico para `ai-diagnose` (costo por llamada)?
7. **Dónde vive la DB productiva real** (VM puerto 8082 vs Render): confirmar antes de armar el
   script de migración de datos.
8. **App mobile**: destino a decidir en la revisión de "lo demás".

---

## 7. Reuso en el monorepo (ya construido)

- **Insight**: `modules/insumos` ya tiene puerto + gateway httpx
  (`insumos/domain/repositories/insight_gateway.py`,
  `infrastructure/insight/httpx_insight_gateway.py`) contra el mismo host con las mismas
  credenciales (`settings.py` ya las tiene). Faltarían métodos que insumos no usa:
  `search por serial` (`q=serial:`), `alerts/current`, `meters/history`. Aplicar el patrón
  **ADR-018**: la plomería compartida en `shared/infrastructure/`, el puerto y el vocabulario
  de negocio por módulo. No importar desde `modules/insumos` (violaría
  `modules-are-independent`).
- **SDS PortalWeb**: `insumos` ya scrapea el mismo portal (login form + sesión) en
  `httpx_sds_portal_gateway.py` — misma consideración ADR-018 para compartir el login/sesión.
- **Slot del módulo**: `backend/src/modules/parque_impresoras/` ya existe (placeholder) y el
  catálogo de permisos ya tiene la entrada `parque-impresoras` (`is_enabled=false`) — activar
  recién al final, como liquidaciones.
- **Mailer**: no se necesita para este alcance (los mails son del módulo de mantenimiento).
- **Anthropic**: no hay integración IA en el monolito todavía — `ANTHROPIC_API_KEY` es una
  env var nueva a agregar a settings (hoy existe solo en el legacy).
- **Frontend**: primitivas de `frontend/src/shared/components/ui/` + patrón de features
  (`frontend/src/features/<modulo>/`).

---

## 8. Divergencias del legacy con `ARCHITECTURE_GUIDE.md` (corregir al portar, no copiar)

- **Auth**: `x-api-key` (y encima horneada en el bundle del frontend) → permisos
  usuario × módulo del padre (`require_permission`).
- **§11**: `GET /saved-analyses` y varios GET de maintenance devuelven `list` cruda → `Page[T]`.
- **§6**: hay `except Exception` que degradan en silencio (mock fallbacks de §6.1, catálogos,
  consumibles → lista vacía sin log de contexto en algunos casos).
- **§4**: el frontend legacy tiene archivos enormes (`SavedAnalysisDetail.tsx` ~51 KB,
  `MonitorDashboard.tsx` ~38 KB, `ExecutivePrintReport.tsx` ~31 KB, `DashboardPage.tsx` ~30 KB)
  — separar por responsabilidad al portar.
- **Acceso a datos**: psycopg2 crudo + SQL manual → SQLAlchemy + Alembic como el resto del
  monolito. El fallback a JSON local **no se porta**: en el monolito la DB es local al stack
  (la razón de ser del fallback era Neon/corporate firewall).
- **IA en router**: `ai.py` instancia repos y llama servicios directo en el endpoint con
  imports inline → reestructurar en use case + puertos.

---

## 9. UI: no hay design handoff — prerequisito antes de tocar frontend

En `Handsoff Mockups/` hay handoffs de inicio, reasignación temporal y SDS Insumos — **ninguno
de Printer-Logs-Analyzer**. La UI legacy (dark glassmorphism propio, charts Recharts, heatmap,
timeline) no responde a la marca Canal Directo (Institucional: naranja `#F7941D` / gris
`#58595B`).

Según el flujo establecido (skill `ui-design-handoff`): **antes de escribir un componente hay
que tener el handoff** con las pantallas del alcance:

1. Vista de bienvenida / búsqueda por serial (+ historial de búsquedas).
2. Panel de análisis: KPIs, top errores, gráfico de incidentes en el tiempo, heatmap, tablas de
   incidentes y eventos con filtros de severidad y rango de fechas, panel de consumibles y
   alertas Insight.
3. Panel de diagnóstico IA.
4. Modales: pegar logs, alta/edición de código en catálogo, contenido de solución, guardar
   análisis, comparar.
5. Listado y detalle de análisis guardados (+ badge de salud del equipo, resultado de compare).
6. Reporte PDF A4 (tiene diseño print propio).

---

## 10. Datos a migrar (cuando llegue el momento)

Desde la DB productiva (ubicación a confirmar, §6.7): `error_codes` completo,
`saved_analyses` + `device_telemetry_events` (respetando FKs), y `error_solutions` si se decide
§6.4. Patrón ya probado: script one-off contra snapshot read-only, conteos y sumas de control,
como `migrate_liquidaciones_data_from_sqlite.py`. Los JSON de fallback locales
(`data/error_codes_local.json`, `saved_analyses_local.json`) pueden contener deltas no
sincronizados a la DB — revisarlos antes de descartar.

---

## 11. Plan propuesto (orden de ejecución dentro de Fase 3)

1. **Caracterización ejecutable — HECHA (2026-08-15).** Tests nuevos en el repo legacy:
   `backend/tests/test_caracterizacion_analisis_logs.py` (18 tests, sobre las muestras
   reales de `samples/`: hp_log.txt con 54 eventos y la respuesta AJAX real del portal con
   293 filas y 8 links de ayuda). Fijan: conteos exactos por código/tipo, meses en español,
   hora sin zero-pad, counter=0 válido, quirk de columna corrida con campo intermedio vacío
   (§5.13), detección de header solo en las 3 primeras líneas, incidentes de la muestra
   (rangos de contador, ids, severidades), catálogo que enriquece clasificación/link pero
   NO severidad, `html_to_tsv` + round-trip completo (portal→TSV→parser, 293/293),
   `extract_help_urls` con dedup por código, diff+tendencia (estable/empeoró/mejoró) con
   la muestra real, shape exacto del JSONB `incident_to_summary`, y `extract_serial_number`.
   **Suite legacy completa: 236 passed** (218 preexistentes + 18 nuevos; los motores de
   salud y tendencia ya estaban bien cubiertos por `test_degradation_service.py` — incluidos
   dedup de re-imports y guarda de counter=0 — y `test_compare_service.py`; no se
   duplicaron). Corridos sin levantar el server (pytest puro, sin scheduler).
2. **Design handoff** del alcance (§9) — bloquea el frontend, no el backend.
3. **Backend**: `modules/parque_impresoras/` con capas de la guía —
   - domain: entidades Event/EnrichedEvent/Incident/AnalysisResult/ErrorCode, parser y
     analysis como servicios de dominio puros, motores compare/degradation puros.
   - application: use cases (analizar, validar, upsert catálogo, extraer SDS, diagnosticar IA,
     CRUD snapshots, comparar, salud).
   - infrastructure: repos SQLAlchemy (error_codes, saved_analyses, telemetry), gateways
     Insight/SDS (patrón ADR-018), cliente Anthropic.
   - presentation: routers con `require_permission`, `Page[T]` en listados.
   - Migración Alembic del schema (4 tablas del alcance).
4. **Frontend**: `features/parque-impresoras/` + `(app)/parque-impresoras/` según handoff.
5. **Datos reales + activación** del módulo (`is_enabled=true` al final).
6. **Paralelo con el legacy** — este módulo NO tiene el riesgo de jobs de fondo del alcance,
   pero sí usuarios activos; observación antes de apagar la parte de análisis. Ojo: el legacy
   no se puede apagar entero hasta que se resuelva "lo demás" (avisos/monitor siguen vivos).

---

## 12. Actualización a `origin/main` (3d28a96, 2026-07-17) — qué cambió vs. la primera pasada

El repo local estaba en un snapshot del 2026-06-16. Se actualizó por fast-forward (la rama
local era ancestro directo de main, nada se perdió) y se re-corrió toda la suite: **255
passed**, incluidos los 18 tests de caracterización — **el pipeline central (parser,
incidentes, compare, html_to_tsv, extract_help_urls, motor de salud) no cambió de
comportamiento**. Lo nuevo que SÍ afecta el alcance:

1. **Snapshots SDS automáticos 2×/día** (`sds_snapshot_service.py` + 2 jobs cron en
   `scheduler.py`): para cada serial único en `saved_analyses`, refresca la caché de datos HP
   (`refresh_hp_data_cache`, método nuevo del portal), extrae, parsea y guarda snapshot con
   nombre `Auto - {serial} - {fecha} (mañana|tarde)` + telemetría. Es el único background job
   del alcance (ver §2). Precaución local reforzada: correr el legacy levantado ahora SÍ
   escribe snapshots contra SDS/Insight reales dos veces al día.
2. **Incidentes CDS vía wsAyC** (`cds_service.py`, `GET .../cds-incidents`): pega al SOAP
   `wsg.cdsisa.com.ar/wsAyC_server.php` (getCounters / incidentes con repuestos y tareas del
   técnico, últimos 12 meses), con cache 10 min y circuit breaker (3 fallos → 5 min). Se
   muestran en panel propio y alimentan a la IA como `metadata.cds_incidents`. **Tercer
   consumidor de wsAyC en el monolito** → reusar `shared/infrastructure/wsayc/client_provider.py`
   (ADR-018), NO portar el cliente `requests` crudo del legacy (usa `verify=False` — no
   replicar eso). También muestra el **dígito verificador EAN** en los números de incidente
   (port del algoritmo módulo-10 ya conocido de liquidaciones).
3. **Prompt de IA v2** (§3.6 sigue válido en estructura, pero las reglas cambiaron): umbral
   dinámico `max(vol_diario × 7, 400)` en lugar del 400 fijo, doble criterio de actividad
   (delta de páginas O recencia temporal ≤7 días), gate de **reincidencia** (hardware activo
   con `occurrences == 1` sin ráfaga → nunca despacho "si", como mucho "remoto"), y
   `metadata.cds_incidents` como contexto. Campo interno nuevo `_volumen`. Nota del código:
   el script standalone `scripts/ai_diagnose.py` quedó con el prompt viejo a propósito — el
   productivo es el del servicio.
4. **CPMD resuelto por el propio legacy** (cierra la decisión §6.4): se eliminó el pipeline
   parseado (`error_solutions` dropeada en migración 013, repo y `ingest_cpmd.py` borrados) y
   se reemplazó por **servido directo de PDF** (`routers/cpmd.py`: `GET /cpmd/pdf-url` +
   `POST /cpmd/upload`, manifest en `data/cpmd/`, estáticos en `/static/cpmd`, visor y upload
   desde la UI). Esto es lo que se porta.
5. **Centro de notificaciones in-app** (`notifications` tabla + router + `NotificationsBell`)
   con `hp_cache_notifier.py`: threads watcher que siguen el refresh de caché HP hasta
   completarse y actualizan la notificación; se reanudan al arrancar la app
   (`resume_pending_watches`). Decisión nueva para la migración: ¿portar tal cual o mapearlo
   a un mecanismo más simple del monolito? (los watchers en threads + JSON fallback no
   encajan directo en la arquitectura objetivo).
6. **Comparar dos snapshots entre sí** (`GET /saved-analyses/{id}/compare-with/{target_id}`,
   `_diff_two_snapshots`: ordena cronológicamente, diff + tendencia sin re-parsear logs) y
   panel de historial de snapshots con gráfico (`SnapshotHistoryPanel`) — extiende §3.8.
7. **Tabla de operaciones HP Smart** (`GET .../hp-operations`, con fix de unwrap del CDATA
   AJAX) — estado de operaciones del dispositivo en el portal.
8. **Catálogo de modelos de impresora** (`printer_model_repository.py`, entidades
   `PrinterModel`/`PrinterConsumable`/`ConsumableWarning`): partes/consumibles por modelo con
   vida útil y códigos relacionados, para advertencias por contador. **Drift de schema
   detectado**: consulta `printer_models`/`printer_consumables`/`consumable_related_codes`
   pero **ninguna migración las crea** (fallback local `migrations/printer_models.json`,
   seed en `scripts/seed_json_to_db.py`) — verificar cómo existen en la DB productiva antes
   de la migración de datos.
9. **UI ya rebrandeada a Canal Directo** (naranja corporativo, logos/isotipos SVG, tipografía
   **RNS Sanz** — la misma que Calendario web): §9 queda matizado — el legacy nuevo ya no es
   el glassmorphism genérico; es insumo directo para el handoff que está armando el usuario.
10. **Mobile creció** (scanner de código de barras, búsqueda de errores, pantalla Analyzer
    rediseñada) — sigue fuera de alcance.
11. Deploy: frontend dockerizado pasó a build de producción con Nginx y `API_BASE` dinámico
    (commit `cc05903`) — revisar `docs/deploy.md` actualizado del legacy al confirmar dónde
    vive la DB productiva (§6.7).

### §12.bis — Caracterización relanzada sobre la app actualizada (2026-08-15)

Segunda pasada de tests de caracterización, ahora sobre `3d28a96` (pedida por el usuario).
El archivo `backend/tests/test_caracterizacion_analisis_logs.py` quedó en **21 tests**;
suite completa del legacy: **258 passed**. Cobertura de lo nuevo:

- Lo que julio ya traía testeado y NO se duplicó: `cds_service` completo (15 tests:
  parse SOAP, filtro de templates, `find_counter_for_incident`, circuit breaker, cache),
  endpoints nuevos de `sds.py` (refresh-cache, hp-operations, cds-incidents con mocks),
  `_parse_hp_operations` (strip del link "Ver datos en bruto").
- Agregado: `_diff_two_snapshots` (compare-with) con datos de la muestra real, y el
  **servicio de snapshots automáticos** ejercitado con el HTML real del portal (fakes de
  repos/SDS, Insight mockeado): refresh de caché antes de extraer, upsert de los 3 códigos
  de ayuda de la muestra, snapshot `Auto - {serial} - {fecha} (mañana|tarde)`, y skip
  cuando no hay incidentes.
- **BUG REAL encontrado y pineado** (`test_snapshot_automatico_con_portal_real`): tras
  crear el snapshot, el fan-out a telemetría de `sds_snapshot_service._capture_device`
  accede a `inc.last_event_time` sobre la entidad de dominio `Incident`, **que no tiene
  ese campo** (solo existe en el schema `SavedAnalysisIncidentItem` del endpoint manual).
  En producción: cada captura automática guarda el snapshot, **nunca escribe telemetría**
  (el motor de salud no recibe datos de las capturas automáticas) y `capture_all_devices`
  loguea "Snapshot capture failed" por dispositivo. La migración debe **corregirlo usando
  `end_time`**, no replicarlo — mismo criterio que los bugs del importador de liquidaciones.
- Fallback hash confirmado en vivo: con Insight caído, `device_id` = suma de ords del
  serial (`MXTEST01` → 582) — refuerza §6.1 (no portar mocks silenciosos).

## 13. Referencias de código legacy (para la reescritura)

- Parser y análisis: `backend/application/parsers/log_parser.py`,
  `backend/application/services/analysis_service.py`, `backend/interface/utils.py`
- Routers del alcance: `backend/interface/routers/{analysis,error_codes,sds,ai,saved_analysis}.py`
- Servicios: `backend/application/services/{sds_web_service,insight_service,ai_diagnosis_service,ai_pdf_service,compare_service,degradation_service}.py`
- Repos: `backend/infrastructure/repositories/{error_code,saved_analysis,telemetry,error_solution}_repository.py`
- Schema: `backend/migrations/003,004,005,006,011`
- Frontend del alcance: `frontend/src/pages/DashboardPage.tsx`,
  `frontend/src/components/{Dashboard,Analysis,Parser}/`, `frontend/src/hooks/useAnalysis.ts`,
  `frontend/src/store/useAnalysisStore.ts`, `frontend/src/services/api.ts`
- Muestras reales para tests: `samples/` (TSV, HTML del portal, CSV de eventos)
