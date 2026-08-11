# Migración SDSInsumos — estado y próximo paso

Actualizado: 2026-08-11 (Estadísticas, Mail log, Config GET/PUT y Equipos nuevos portados).

## Portado hasta ahora (backend)

Con `a0189fe`, el router de solicitudes del legacy (`routers/requests/` completo:
`query.py`, `load.py`, `actions.py`) quedó **100% portado**, más el Historial:

| Legacy | Unificado | Commit |
|---|---|---|
| Scaffold: 14 tablas + idempotencia (`order_claim`) | modelo de datos + `ClaimedOrderCreation` | `3e36db2` |
| Lógica CD pura / wsAyC SOAP / Insight API | dominio + gateways (`zeep`/`httpx`) | `9367463`, `5bd348f`, `a243527` |
| `POST /requests/{id}/load` (5 bloqueos) | `POST /api/insumos/requests/{id}/load` | `2a0be1f`–`9b68f85` |
| `GET /dashboard` | `GET /api/insumos/dashboard` | `4de5482` |
| `GET /requests` | `GET /api/insumos/requests` | `6c833a3` |
| Ventana de validación 0% (writes + diagnóstico) | `ValidationWindow` (opera desde ListRequests) | `ca7fc0f` |
| `cancel` / `dismiss` / `reconcile` | `POST /api/insumos/requests/{id}/...` | `4ff4cb9` |
| `GET /audit` | `GET /api/insumos/audit` (Page[T]) | `2915d1b` |
| Detalle equipo/consumible (5 reads de `query.py`) | `GET /api/insumos/devices/...` | `e35f454` |
| `GET /orders/pending` (`pending_orders.py`) | `GET /api/insumos/orders/pending` | `a0189fe` |
| Estadísticas (`estadisticas.py` + `business_hours.py`) | `GET /api/insumos/estadisticas` y `/estadisticas/clientes/{id}` | `2412c4a` |
| Mail log lectura (`mail_log.py`) | `GET /api/insumos/mail-log` (Page[T]) | `7f5de6d` |
| Config GET/PUT (`config.py`, sin `maybe_auto_load`) | `GET`/`PUT /api/insumos/config` | `704f7f7` |
| Equipos nuevos (`new_devices.py` + `device_sync.py`) | `/api/insumos/new-devices` (4 endpoints) | `28cbd22` |

`a0189fe` además cerró un gap: el upsert del cache ahora graba `supply_status_history`
(primer avistaje de cada estado), como el legacy.

## Pendiente (backend)

- ~~Scan incremental~~ (`supply_scanner.py` + `routers/scan.py`) — **descartado por ahora**
  (decisión 2026-08-11, ver abajo). No portar hasta que se resuelva la razón de negocio
  que lo motivaba.
- Clientes (`routers/customers.py`, 12 endpoints; incluye scraping del PortalWeb de SDS
  con login humano — el cliente de portal NO está portado)
- Alertas (`routers/alerts.py` + job de escalado)
- Mailer SMTP para insumos (múltiples destinatarios + adjuntos) — el endpoint de
  lectura de `mail_log` ya está portado; falta el envío, que pertenece a los jobs
  de fondo
- Equipos offline (`routers/offline_devices.py` — verify rate-limited, delete
  irreversible gateado por `SDS_DELETE_DRY_RUN`)
- `maybe_auto_load` (vive en `routers/config.py` del legacy pero pertenece al poller,
  ver punto siguiente)
- **5 jobs de fondo** (`main.py`): poller + autocarga (`maybe_auto_load`), backup,
  chequeo offline, alertas, aviso de pedidos por vencer (`find_orders_due_for_alert` y
  el mail a logística quedaron explícitamente diferidos en `a0189fe`)

Después del backend: todo el frontend (preparar handoff de diseño primero — ver skill
`ui-design-handoff`).

## Decisión 2026-08-11: scan incremental descartado por ahora

El scan existía para completar números de incidente al generar un pedido y para ver
pedidos anteriores ya en la DB de producción — necesario porque los pedidos de origen
Interno no son visibles para el WS (`ID_Origen <> 3` en el PHP legacy, ADR 003).
Posiblemente esa particularidad cambie pronto (decisión de negocio en danza), lo que
volvería innecesario portar el scan tal cual. Se decidió NO migrarlo hasta que esa
regla se resuelva, para no invertir en algo que se va a descartar.

## Análisis comparativo de los módulos pendientes (2026-08-11)

Hecho para decidir el orden de migración de los 8 puntos de la lista de arriba. Legacy
revisado: `SDSInsumos/backend/src/sds_autoloader/`. Dato importante: **el schema
Postgres ya tiene las 14 tablas del legacy creadas** (migración `ebe03bf01e96`),
incluidas `mail_log`, `request_alerts`, `pending_order_notifications`, `dca_monitors`,
`known_devices`, `app_settings`, `customer_zone_contacts`, con sus `Model` de
SQLAlchemy ya escritos — para varios de estos módulos falta solo domain/application/
presentation, no el schema.

| # | Módulo | Tamaño | Deps. externas | Depende de pendiente | Riesgo | Reuso de infra portada |
|---|---|---|---|---|---|---|
| 1 | `customers.py` | 400 líneas / 13 endpoints | Insight, SOAP, **scraping portal (nuevo)** | comparte cliente portal con #7 | **Alto** | Parcial (`ZoneContacts`, modelo) |
| 2 | `config.py` (GET/PUT) | ~240 líneas / 2 endpoints | ninguna | — (separar de `maybe_auto_load`) | **Bajo** | Alto (`AppSettingModel`, criterios ya portados) |
| 3 | `alerts.py` + escalado | 87+84 líneas / 2 endpoints | ninguna (job sí usa Insight) | usa `get_dashboard` ya portado | **Medio** | Alto (`RequestAlertModel`, `get_dashboard`) |
| 4 | `estadisticas.py` | 414 líneas / 2 endpoints | ninguna | — | **Bajo** | Muy alto (`order_audit` ya portado) |
| 5 | `mail_log.py` + mailer | 40+50 líneas / 1 endpoint | SMTP | se llena solo con jobs (#8) | **Bajo** | Alto (`MailLogModel`, mailer SMTP ya existe en `auth`) |
| 6 | `new_devices.py` + `device_sync.py` | 141+86 líneas / 4 endpoints | Insight | prerequisito de #7 | **Medio** | Alto (`KnownDeviceModel`, gateway Insight) |
| 7 | `offline_devices.py` | 268+399 líneas / 5 endpoints | SOAP rate-limited, Insight, **scraping portal (nuevo)** | necesita #6, comparte cliente portal con #1 | **Alto** | Parcial (`DcaMonitorModel`, `KnownDeviceModel`) |
| 8 | 5 jobs de fondo | ~200 líneas | Insight, SOAP, SMTP, filesystem | **de todos los anteriores** (#1-#7) | **Alto** | Bajo (sin precedente de scheduler; backup SQLite no aplica a Postgres) |

Notas por módulo:

1. **Clientes**: 13 endpoints (list/patch/bulk-toggle, CRUD de contactos por zona,
   seed-default, import-from-supply, sds-contacts, zones, preview/apply de
   zone-contacts-import, sync-customers). El scraping del PortalWeb (`SdsPortalWebClient`,
   cookie `JSESSIONID`, HTML por regex) es frágil por diseño y compartido con #7 —
   conviene decidir el cliente de portal una sola vez para ambos.
2. **Config**: el archivo legacy mezcla GET/PUT (240 líneas, sin I/O externo, bajo
   riesgo) con `maybe_auto_load` (que en realidad pertenece al punto 8) — separarlos al
   portar. Los criterios de negocio (`is_autoload_eligible`, `needs_validation`) ya están
   portados como domain services.
3. **Alertas**: `alerts.py` (router, 87 líneas) y `PollerAlerts` (job de escalado, 84
   líneas) son dos cosas distintas pese al nombre compartido. El job de escalado necesita
   la lógica de "pending list" que ya expone `get_dashboard`, y es el primer precedente
   real de background job del proyecto.
4. **Estadísticas**: agregación SQL en vivo sobre `order_audit` (ya portado, con
   repositorio propio), comparativa contra período previo y horas hábiles
   (`business_hours.py`, lógica pura). Sin cliente externo ni scraping — el candidato más
   autocontenido para practicar el patrón.
5. **Mail log**: el endpoint solo lee la tabla `mail_log` (queda vacía sin los jobs del
   punto 8). Ya hay un mailer SMTP async en el monorepo
   (`modules/auth/infrastructure/smtp_mailer.py` + `mailer_factory.py`, con fallback a
   `ConsoleMailer` si `SMTP_HOST` vacío) — falta extenderlo para múltiples destinatarios
   y adjuntos (zip del backup).
6. **Equipos nuevos**: diff simple (nuevo vs. conocido) vía Insight, pero con una regla
   delicada agregada en producción: podar equipos que Insight ya no devuelve (huérfanos;
   bug real medido el 2026-07-31). Es prerequisito de facto de #7 y paso 3 del poller.
7. **Equipos offline**: el módulo más grande junto con Clientes. Combina heurística no
   trivial (normalización de razón social + alias hardcodeados, detección de caída de
   colector real vs. heurística de respaldo), rate-limiting real contra SOAP
   (`VERIFY_DELAY_SECONDS=2s`), scraping de portal para el delete, y una operación
   **irreversible** (gateada por `SDS_DELETE_DRY_RUN`) con lock global que en
   Postgres/multi-proceso necesita el mismo rediseño ya identificado para el scan
   incremental.
8. **5 jobs de fondo**: `background_poller_task` (→ device_sync + `maybe_auto_load`, y
   llamaba al scan incremental de forma non-fatal — se puede saltar ese paso sin romper
   el job, a costa de que el cache se degrade), `background_backup_task` (específico de
   SQLite, **no aplica tal cual a Postgres** — necesita redefinición de alcance, no port
   1:1), `background_offline_check_task` (→ punto 7 completo), `background_alert_task`
   (→ punto 3), `background_pending_alert_task` (→ mail_log + mailer + `pending_orders`,
   ya portado). Es el primer precedente de scheduler de todo el monorepo — sin
   `apscheduler`, `asyncio.create_task` en `lifespan`, ni ADR sobre el tema hoy.

### Recomendación de orden

**Estadísticas (4) → Mail log (5) → Config GET/PUT separado de autocarga (2) → Equipos
nuevos + device_sync (6) → Alertas (3) → Equipos offline (7) → Clientes/scraping portal
(1) → Jobs de fondo (8)**, dejando el scraping del PortalWeb (compartido por #1 y #7)
como una decisión de infraestructura única a tomar antes de encarar cualquiera de los
dos.

Justificación: primero los módulos autocontenidos de bajo riesgo que no requieren
infraestructura nueva (4, 5, 2-parcial) para consolidar el patrón sobre tablas que ya
existen en el schema; luego los que arrastran dependencias reales entre sí en orden
causal (6 antes que 7, y ambos antes que los jobs); el scraping de portal (1 y 7) se
deja para el final porque es la única infraestructura genuinamente nueva y frágil
(además de compartida entre ambos); y los 5 jobs de fondo (8) van al final porque
dependen de *todo* lo anterior y, al ser el primer precedente de scheduler del
monorepo, es la misma decisión de diseño que quedó explícitamente abierta para el scan
incremental — mejor decidirla una sola vez cuando ya estén portados los módulos que ese
scheduler va a orquestar.
