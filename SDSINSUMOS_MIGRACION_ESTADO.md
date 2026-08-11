# Migración SDSInsumos — estado y próximo paso

Actualizado: 2026-08-10 (commits `e35f454` y `a0189fe`).

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

`a0189fe` además cerró un gap: el upsert del cache ahora graba `supply_status_history`
(primer avistaje de cada estado), como el legacy.

## Pendiente (backend)

- **Scan incremental** (`supply_scanner.py` + `routers/scan.py`) ← **próximo sugerido**
- Clientes (`routers/customers.py`, 12 endpoints; incluye scraping del PortalWeb de SDS
  con login humano — el cliente de portal NO está portado)
- Configuración (`routers/config.py`, GET/PUT con validaciones encadenadas)
- Alertas (`routers/alerts.py` + job de escalado)
- Estadísticas (`routers/estadisticas.py`)
- Mail log (`routers/mail_log.py`) + mailer
- Equipos nuevos (`routers/new_devices.py` + `device_sync.py`)
- Equipos offline (`routers/offline_devices.py` — verify rate-limited, delete
  irreversible gateado por `SDS_DELETE_DRY_RUN`)
- **5 jobs de fondo** (`main.py`): poller + autocarga (`maybe_auto_load`), backup,
  chequeo offline, alertas, aviso de pedidos por vencer (`find_orders_due_for_alert` y
  el mail a logística quedaron explícitamente diferidos en `a0189fe`)

Después del backend: todo el frontend (preparar handoff de diseño primero — ver skill
`ui-design-handoff`).

## Próximo paso sugerido: el scan incremental

**Por qué primero**: sin el scan, `supply_serial_cache` se siembra solo al crear cada
pedido. Los pedidos de origen Interno son invisibles para `getTopSupplies`/portal
(ADR 003 del legacy: el PHP filtra `ID_Origen <> 3`), así que el cache es la única
fuente que los ve para el chequeo anti-duplicados — y se degrada con el tiempo si nadie
lo refresca. También es prerequisito real del poller.

**Qué portar** (caracterización §3.3): checkpoint (`scan_checkpoint`) con bootstrap
automático, barrido de `SCAN_BATCH_SIZE=300` IDs vía `getSupplyById` en paralelo,
persistencia en cache, y la regla dura de **avanzar el checkpoint solo hasta el último
ID que existió de verdad** (bug real documentado: checkpoint en 444401 con máximo real
~441500 dejó el cache vacío). Endpoints: `GET /api/supply-scan/status` y
`POST /api/supply-scan/run` (409 si ya corre, 429 + `retry_after_seconds` con cooldown
de 120s).

**Decisión de diseño a tomar antes de escribir código** (quedó abierta el 2026-08-10):

1. **Serialización del scan**: el legacy usa `threading.Lock` global + cooldown — no
   sobrevive multi-proceso/replica. Opciones en Postgres:
   - `pg_advisory_xact_lock` (simple, se libera solo, pero no deja estado consultable
     para `GET /status` ni para el 429 con `retry_after_seconds`), o
   - tabla de estado del scan (fila única con `running_since` / `last_finished_at`),
     mismo espíritu que `order_claim` — deja el status y el cooldown consultables.
   La segunda parece encajar mejor con el contrato del endpoint, pero decidirlo
   explícitamente (y documentar ADR si se desvía de la guía).
2. **Modelo de ejecución**: ¿el `POST /run` ejecuta el barrido inline en el request
   (~300 llamadas SOAP; simple, pero el request queda colgado ~decenas de segundos) o
   se sienta acá el primer precedente de background jobs del proyecto (que el poller,
   backup y alertas van a necesitar igual)? El proyecto hoy tiene **cero** precedente
   de background jobs — lo que se elija acá va a ser el molde para los 5 jobs del
   legacy.
