# Caracterización del backend de SDS Autoloader (SDSInsumos)

Investigación de solo lectura sobre `C:\Users\imartinez.CDSA\Desktop\proyectos\SDSInsumos\backend`
para preparar la migración de este módulo al monolito `HelpDeskManager-Unificacion`
(Next.js 15 + FastAPI + Postgres), próximo en la cola según `INTEGRACION_APPS_PLAN.md`
("SDSInsumos → VacaSync → STC Cloud"). Sigue el formato de `CONTADORES_CARACTERIZACION.md`.

**Verificación en vivo**: se corrió la suite de tests real del repo legacy —
`cd backend && ../.venv/Scripts/python.exe -m pytest tests/` → **504 passed, 1 warning en
50.92s** (venv preexistente en la raíz de `SDSInsumos/`, Python 3.12.10). No se tocó la DB de
producción (`state.db`) ni se hizo ninguna llamada real a Insight/Canal Directo — toda la
caracterización de abajo es lectura de código + esos 504 tests, no una sesión contra
servicios en vivo (a diferencia de la caracterización de Contadores, que sí corrió contra la
Neon real). El número "330 tests" que menciona `docs/OPTIMIZATION_PLAN.md` está desactualizado;
504 es el conteo real al día de hoy.

---

## 1. Arquitectura general y arranque (`main.py`)

FastAPI `lifespan` instancia en `app.state`: `cfg`, `db` (`StateDb`/SQLite), `client`
(`InsightApiClient`), `sds_portal_client` (`SdsPortalWebClient`, login humano solo para
scripts de migración de contactos y baja de equipos offline), `order_client`
(`SoapOrderClient` — pedidos de insumos vía SOAP wsAyC, **no scraping**), `incident_client`
(`CanalDirectoIncidentClient` — incidentes Pre-Correctivo, sigue scrapeando el portal),
`order_lock` (`KeyedLock` por `(serie, sku)`), `device_cache` (`TTLCache`, TTL =
`poll_interval_minutes`), `poller_alerts`.

Se lanzan **5 tareas de fondo asíncronas** (`asyncio.create_task`), salvo
`DISABLE_BACKGROUND_JOBS=true`:

| Tarea | Intervalo | Qué hace |
|---|---|---|
| `background_poller_task` | `POLL_INTERVAL_MINUTES` (default 120 en código, `.env.example` recomienda 60) | `poller.run_once` (sync de clientes/equipos/scan) + `maybe_auto_load` (autocarga) |
| `background_backup_task` | diaria, ancla de reloj a `BACKUP_HOUR` | backup SQLite + mail opcional |
| `background_offline_check_task` | diaria, ancla a `OFFLINE_CHECK_HOUR` | auditoría equipos offline (secuencial, rate-limited) |
| `background_alert_task` | cada `ALERT_CHECK_MINUTES` (default 15) | sincroniza/escala `request_alerts` |
| `background_pending_alert_task` | cada `ALERT_CHECK_MINUTES` | mail a logística de pedidos Pendientes por vencer |

Todos los handlers de router son **`def` síncronos** (confirmado por grep: cero `async def` en
`routers/`) — corren en el threadpool de FastAPI porque los clientes externos (`requests`,
`zeep`/SOAP, `sqlite3`) son bloqueantes (ADR 002). Paralelismo intra-endpoint vía
`ThreadPoolExecutor`/`parallel_map`, nunca loops secuenciales de I/O. **Al portar a un stack con
cliente HTTP y driver Postgres async, esta restricción desaparece** — pero cualquier código
portado 1:1 que asuma "corro en threadpool, no en el event loop" hay que revisarlo.

Middlewares: `request_id_middleware` (X-Request-ID en logs y respuesta), `cache_control`
(`/assets/*` cache 1 año inmutable, resto `no-cache`), `GZipMiddleware` (min 1024 bytes).

**Sin autenticación en ningún endpoint** — decisión de diseño explícita y documentada
(`SEGURIDAD_PENDIENTE.md`), no un descuido: la app corre en red interna/VPN, nunca expuesta a
internet, y varios endpoints (`/load`) resuelven todo del lado del servidor precisamente
*porque* no hay auth. **Al integrar al monolito unificado, que sí tiene auth de por medio, hay
que decidir esto como cambio de producto explícito**, no asumir que "ya viene protegido".

---

## 2. Endpoints HTTP (45 rutas totales)

43 bajo `/api/*` repartidas en 10 routers + `GET /api/health` + catch-all SPA, todas en
`backend/src/sds_autoloader/routers/`. El router de "requests" (pedidos) **no es un archivo
único** — es el subpaquete `routers/requests/{query,load,actions,models}.py`, ensamblado en
`routers/requests/__init__.py`. Ojo con esto al buscar código: `pending_requests.py` y
`pending_orders.py` (en la raíz del paquete) son **módulos de lógica compartida**, no routers —
los importa el poller de fondo y los routers, pero no definen rutas ellos mismos.

### `GET /api/health` (en `main.py`, no en `routers/`)
Ejecuta en paralelo (`ThreadPoolExecutor`, 2 workers) `client.ping()` (Insight, fuerza
login/refresh de token) y `order_client.ensure_login()` (no-op en `SoapOrderClient`, el SOAP no
tiene sesión). `503 {"ok": false, "errors": [...]}` si alguno falla.

### Router Alertas (`routers/alerts.py`)
- `GET /api/alerts` — escala vencidas en vivo, devuelve `list_active_alerts()` (tabla
  `request_alerts`).
- `POST /api/alerts/ack` — `acknowledge_alerts(ids)`.

### Router Auditoría (`routers/audit.py`)
- `GET /api/audit?limit=1000` (cap 5000) — trae de `order_audit`; para filas viejas sin
  `device_id` (grabadas antes de que existiera esa columna), hace **backfill en el mismo GET**
  consultando Insight en paralelo y persistiendo el resultado — un `GET` con side effect de
  escritura, documentado en el código.

### Router Configuración (`routers/config.py`)
- `GET /api/config` — settings con defaults aplicados.
- `PUT /api/config` — **status 200 siempre**, `{"ok": false, "error": ...}` en validaciones de
  negocio encadenadas: umbrales críticos ordenados, `autoloadMaxDays` [1,30],
  `autoloadMinPercent` [1,100] (topes duros server-side, mitigación de seguridad explícita —
  ver `SEGURIDAD_PENDIENTE.md`), `validationWindowHours` [1,48], `staleDeviceDays` [1,60],
  ventanas de offline [24,720]/[2,100]/[1,100], `alertEscalationMinutes` [5,1440], horario
  laboral [0,23)/[1,24) con `start<end`, emails de logística validados por regex.
- `maybe_auto_load(...)` **vive en este archivo pero no es un endpoint** — la invoca solo el
  poller de fondo (`main.py`). Ver sección 4.

### Router Clientes (`routers/customers.py`)
12 endpoints: listado/toggle de clientes (incluido `bulk-toggle`, afecta a TODOS), CRUD de
`customer_zone_contacts` (incluido `seed-default` masivo, requiere `customer_ids` explícito a
propósito — nunca pisa toda la cartera sin querer), `import-from-supply` (rellena contactos
desde un supply real vía SOAP `getSupplyById`), `sds-contacts` (parsea comentarios libres de
Insight con regex), `zones` (zonas activas de un cliente vía solicitudes OUTSTANDING),
`zone-contacts-import/{preview,apply}` (scraping del PortalWeb de SDS con login humano —
requiere `SDS_PORTAL_USERNAME/PASSWORD`, si faltan devuelve error de negocio en vez de crashear),
`sync-customers` (upsert de `customers_config` desde Insight).

### Router Estadísticas (`routers/estadisticas.py`)
`GET /api/estadisticas` y `GET /api/estadisticas/clientes/{customer_id}` — agregación **en
vivo por SQL** sobre `order_audit` (sin precálculo, volumen chico), con comparativa contra
período previo equivalente. Incluye `fulfillment` (horas hábiles de gestión propia, ver
`business_hours.py`) y `pendingToDispatch` (días corridos Pendiente→Despachado en CD).

### Router Mails (`routers/mail_log.py`)
`GET /api/mail-log?limit=500` (cap 2000) — tabla `mail_log`, registra backup diario, alertas de
poller caído/recuperado, aviso de pedidos por vencer.

### Router Equipos nuevos (`routers/new_devices.py`)
Equipos descubiertos en Insight sin registrar en `known_devices`. `POST /api/sync-new-devices`
dispara `device_sync.sync_devices`.

### Router Equipos offline (`routers/offline_devices.py`)
Detección + baja de equipos dados de baja físicamente. `_DELETABLE_STATUSES = {"BODEGA"}` —
único veredicto que habilita baja masiva. `POST /api/offline-devices/verify` consulta Canal
Directo **secuencial y pausada** (rate-limit real, no solo paralelismo limitado) — `409` si ya
hay una verificación en curso. `POST /api/offline-devices/delete` es **irreversible**, gateado
por `SDS_DELETE_DRY_RUN=true` (default), secuencial sin paralelismo ni reintento, cada ítem con
su propio resultado (`ok=False` individual no aborta el batch), auditado siempre.

### Router Supply Scan (`routers/scan.py`)
- `GET /api/supply-scan/status`.
- `POST /api/supply-scan/run` — `409` si ya hay un scan corriendo, `429` con
  `retry_after_seconds` si no pasó el cooldown de 120s. Ver sección 3.

### Router Solicitudes (`routers/requests/`) — el núcleo de negocio

**`query.py`** (lectura): `GET /api/dashboard` (delega a `pending_requests.compute_dashboard_state`,
ver sección 4), `GET /api/requests` (el endpoint más complejo — resuelve validaciones
pendientes, trae OUTSTANDING de Insight, cruza contra `processed_requests` +
`supply_serial_cache` + SOAP en vivo, libera solicitudes cuyo pedido quedó Anulado/Cancelado,
pagina), `GET /api/orders/pending` (wrapper de `pending_orders.compute_pending_orders`),
`GET /api/devices/{serial}/supplies`, `.../consumables/{index}/history`,
`.../consumables/{index}/requests`, `.../availability-windows`, `.../consumables/{index}/detail`.

**`load.py`** — **el contrato central pedido por el CLAUDE.md**:

```
POST /api/requests/{request_id}/load
body: LoadRequestBody { customerId, customerName, dryRun, forceOverride, overrideInsumoId, revision }
→ status 200 SIEMPRE
→ { ok: true, orderId, supplyUrl, warn } | { ok: false, error, conflictType?, conflictData?, options? }
```

`LoadRequestBody` **deliberadamente no acepta** `deviceId`/`serial`/`sku` del cliente —
todo se deriva del lado del servidor releyendo Insight, por diseño de seguridad (sin esto, la
API sin auth permitiría cosechar series/SKU reales y crear pedidos sin alerta genuina detrás).
Ver sección 4 para el flujo completo paso a paso (es el corazón de la idempotencia).

**`actions.py`**: `POST /.../cancel` (anula vía SOAP `void_supply`/`void_incident` + reconfirma
+ libera local), `POST /.../dismiss` (da de baja en HP SDS mismo, `status_update="DELETE"` —
única ruta del router que usa un 5xx real, no `{ok:false}`), `POST /.../reconcile` (vincula
un pedido que YA existe en CD pero que la app no registró — **nunca crea uno nuevo**, solo
busca vía `order_client.find_order_by_reference`).

---

## 3. El mecanismo de idempotencia SOAP — paso a paso

Esto es lo que `INTEGRACION_APPS_PLAN.md` marca como riesgo conocido. Es el bloque de lógica
más delicado de todo el módulo — se rompe fácil al reescribir porque combina tres capas
distintas (clave de idempotencia local, verificación post-creación contra la API externa, y
detección de pedidos invisibles) que solo funcionan juntas.

### 3.1. Clave de idempotencia: `reference = f"SDS-{hp_request_id}"`

Se construye **al vuelo** en `poller.create_order_and_record`/`create_incident_and_record`
(`poller.py:236,358`) y en `routers/requests/actions.py` (reconcile). **No se persiste como
columna propia en SQLite** — lo que persiste es `hp_request_id` (INTEGER, PK natural de
`processed_requests`). El prefijo viejo `HP-` (pedidos previos a jul-2026, ver `CHANGELOG.md`
`[1.1.0]`) es un detalle de formato del lado de Canal Directo, no del modelo de datos local: no
hay de dónde derivarlo retroactivamente si se pierde. `NroIncidenteCliente` en el payload SOAP
es donde viaja esta referencia — es el campo que Canal Directo devuelve intacto y que la
verificación posterior compara.

### 3.2. Creación: `SoapOrderClient.create_order` (`canal_directo_soap_client.py:82-223`)

1. Resuelve `familia_id`/`empresa_id`/`sucursal_id` de la serie vía SOAP `getMachineBySerial`
   — si no resuelve familia, `SerieNoActivaEnCanalDirecto` (serie no activa/reasignada a
   bodega).
2. Resuelve el insumo dentro de la familia con `insumo_matching.select_insumo_id` (heurística
   SKU exacto → tipo+color → única opción → error interactivo `InsumoAmbiguoError` con
   opciones para que el operador desambigüe a mano, ver `override_insumo_id`).
3. Resuelve contactos (zona → último pedido de la sucursal vía SOAP → config global) —
   valida que estén completos (nombre/apellido, teléfono, email de ambos) o lanza `RuntimeError`
   explícito.
4. Arma el payload `persistNewSupply` con `NroIncidenteCliente=order.reference` y
   **`origen_id` en la RAÍZ del payload, no anidado en `Supply`** — bug real corregido: antes
   quedaba anidado y todo pedido terminaba con origen Web en vez de Interno. Checklist del
   CLAUDE.md lo marca como regla dura a no romper de nuevo.
5. Llama `soap_query.persist_new_supply(payload)` — **sin reintento automático, nunca**: es la
   operación que crea el pedido real, reintentarla arriesga duplicar.
6. **`persistNewSupply` no valida que la serie exista**: si no la encuentra, el
   `INSERT...SELECT FROM Maquina` del lado del servidor no inserta filas, pero el ID "exitoso"
   (`MAX+1`) se devuelve igual. Por eso el paso 7 es obligatorio, no defensivo.
7. **Verificación post-creación obligatoria** (`_verify_created`): relee por
   `getSupplyById(new_id)` y confirma que `NroIncidenteCliente` coincide exactamente con
   `order.reference`. Con **reintentos cortos ante lag de lectura**: `(1, 2, 4)` segundos —
   caso real documentado en el código (pedido `443017`/`SDS-974325`, 2026-08-03: se creó bien
   pero la primera verificación no lo vio, recién ~4 min después el scan periódico lo detectó).
   Si tras los 3 reintentos la referencia no coincide → `RuntimeError` ("revisar manualmente
   antes de reintentar") — **no se marca procesado**, el próximo ciclo puede reintentar sin
   riesgo porque la verificación habría fallado igual si el pedido real sí existiera con esa
   referencia (ver `reconcile` para el caso "en realidad sí se creó").
8. Siembra `supply_serial_cache` inmediatamente (no espera al próximo ciclo del scan) — crítico
   porque los pedidos de origen Interno son invisibles para `getTopSupplies`/portal (ver 3.3),
   así que esta tabla es la **única** fuente que ve este pedido para el chequeo anti-duplicados
   hasta que el scan lo confirme.

### 3.3. Por qué el scan incremental sigue siendo imprescindible (`supply_scanner.py`)

Confirmado contra el código fuente PHP del servicio (ADR 003, jul-2026): `getTopSupplies`
filtra explícitamente `WHERE ... AND i.ID_Origen <> 3` (3 = Interno). **Los pedidos que esta
app crea (origen Interno) nunca aparecen en `getTopSupplies` ni en el listado del portal** —
la única forma de verlos es `getSupplyById` con el ID numérico exacto. De ahí el scan:

1. Lee checkpoint (`scan_checkpoint`); si es 0, bootstrap automático (estima rango de IDs desde
   los propios `processed_requests`, refina con `getTopSupplies` si hay `empresa_ids`
   configurados).
2. Escanea `SCAN_BATCH_SIZE=300` IDs en paralelo (`ThreadPoolExecutor`, 20 workers) vía
   `getSupplyById`.
3. Persiste hallazgos en `supply_serial_cache`.
4. **Avanza el checkpoint solo hasta el último ID que existió de verdad**, nunca hasta
   `to_id` a ciegas — bug real documentado: adelantar el checkpoint más allá de la frontera de
   IDs reales dejó el cache vacío una vez (checkpoint en 444401 cuando el máximo real era
   ~441500), porque los supplies creados después quedaban *detrás* del checkpoint y ya no se
   escaneaban nunca más.

Protegido por `_scan_lock` (global, `threading.Lock`) + `ScanCooldownError` (120s) —
dos corridas simultáneas (poller + botón manual, o el botón spameado) duplicarían ~300 llamadas
SOAP y se pisarían el checkpoint entre sí.

### 3.4. Serialización check-then-act: `KeyedLock` por `(serie, sku)`

`concurrency.py::KeyedLock` — lock por clave con refcount, instanciado una vez como
`app.state.order_lock`. Todo el flujo "¿ya hay un pedido activo/de hoy para esta serie+sku?" →
crear → `mark_processed` corre **dentro** de `order_lock.acquire((serial, sku))`, tanto en
`/load` (manual) como en `maybe_auto_load` (automático) — así dos requests concurrentes (o el
poller corriendo a la vez que un click manual) no pueden pasar ambos el chequeo
anti-duplicados antes de que el primero registre el pedido. **Al migrar a Postgres, este lock
en memoria de un solo proceso deja de alcanzar** si el nuevo despliegue corre más de una
instancia — hay que resolverlo con un constraint único real o un advisory lock de Postgres, no
asumir que el equivalente Python de `KeyedLock` es suficiente en un entorno multi-proceso.

### 3.5. Bloqueos del flujo `/load`, en orden, y cuáles son saltables

Dentro del `order_lock`, en este orden exacto (`routers/requests/load.py`):

1. **Ventana de validación pendiente** (0% sospechoso, ver sección 5) — bloquea salvo
   `forceOverride`.
2. Pedido ya `processed` y no `CANCELLED` → reverifica que no esté Anulado/Cancelado en CD; si
   sigue válido, responde **idempotente** `{ok: true, orderId, supplyUrl}` sin crear nada nuevo.
3. **Pedido ya cargado HOY para esta serie+sku** (`db.get_today_order_for`) — saltable con
   `forceOverride`.
4. **Pedido activo en CD para la serie** (cache + `resolve_supply_match`) — saltable con
   `forceOverride`, y no aplica en `dryRun`.
5. **`CANCEL_RELOAD_DAILY_LIMIT = 3`** (`db.count_created_today(request_id)`) — **NUNCA
   saltable, ni con `forceOverride`**: es el techo anti-abuso real (anti "cancelar+recargar"
   por script). Es el único de los cinco que no tiene bypass.

`resolve_supply_match` (`poller.py:13-74`) es un detalle sutil: el SOAP no trae
`NroArticulo`/`Descripcion` en `getSupplyById`/`getTopSupplies`, así que sin completar esos
campos primero (vía `fetch_supply_article_description`, solo si faltan), **cualquier supply de
origen externo caería en el fallback "sin datos → asumir match"** — exactamente el bug real
documentado que causó una asociación incorrecta (pedido `441448`, bug `971496`): un pedido de
*otro* consumible de la misma serie bloqueaba la carga del correcto. Solo se llama en paths de
bloqueo/creación (poller, `/load`), no en vistas de solo lectura.

### 3.6. Reconciliación manual (`POST /.../reconcile`)

Cubre el caso "`/load` reportó error pero en realidad el pedido sí se creó" (típico: falló la
verificación por lag de lectura). Busca entre `supply_serial_cache` local (única vía que ve
pedidos de origen Interno) uno cuyo `NroIncidenteCliente` coincida exactamente con la
referencia — nunca crea un pedido nuevo, solo vincula.

---

## 4. El poller / autoloader

`POLL_INTERVAL_MINUTES` vive en `config.py` (`Config.poll_interval_minutes`, leído de la env
var homónima) — **default en código es `120`**, pero `.env.example` recomienda `60` porque
"SDS lee niveles de consumibles cada 1 hora" (KB HP 30000040938). El `TTLCache` de equipos
(`device_cache`) usa el mismo valor como TTL (`ttl_seconds=cfg.poll_interval_minutes * 60`).

### 4.1. `poller.run_once` (sync de datos, NUNCA crea pedidos)

Ejecutado dentro de `background_poller_task` vía `asyncio.to_thread`. Pasos:
1. `client.get_customers()` + `db.sync_customers(...)`.
2. Por cada cliente habilitado: cuenta OUTSTANDING sin registrar (solo log, no acción).
3. `device_sync.sync_devices(...)` — detecta equipos nuevos en SDS (non-fatal si falla).
4. `supply_scanner.run_incremental_scan(...)` — non-fatal (`ScanInProgressError`/
   `ScanCooldownError` se loguean y se saltea el ciclo, no rompe el poller).
5. `db.prune_supply_cache(older_than_days=365)` — limpieza periódica, non-fatal.

**Si falla a mitad de camino**: cada paso está en su propio `try/except` con log
(`logger.exception`, non-fatal) — un fallo en `device_sync` no aborta el scan ni la limpieza.
Solo una excepción en `client.get_customers()` (paso 1, sin try propio) tumbaría el ciclo
completo, que `background_poller_task` captura en su propio `try/except` exterior y registra
como fallo consecutivo vía `poller_alerts.record_failure` (dispara mail tras
`ALERT_AFTER_FAILURES=3` ciclos seguidos fallidos, si hay SMTP configurado). El próximo ciclo
arranca igual `POLL_INTERVAL_MINUTES` después, sin backoff ni reintento inmediato.

### 4.2. `maybe_auto_load` (creación automática, `routers/config.py:297-...`)

Separado de `run_once` a propósito (docstring: "la creación de pedidos es exclusivamente
manual salvo esta función explícita"). Flujo:
1. Si `settings["autoload_enabled"]` es falso, no hace nada.
2. `resolve_pending_validations(...)` primero — una solicitud confirmada en este mismo ciclo ya
   puede autocargarse sin esperar al próximo.
3. Por cliente habilitado, trae OUTSTANDING, filtra `is_stale_replaced` y ya procesadas,
   filtra por `is_autoload_eligible(days_left, percent_left, max_days, min_pct)` — criterio
   único: `days_left <= max_days OR percent_left <= min_pct`.
4. De las elegibles, las que llegan en **0% exacto** (`needs_validation`) arrancan la ventana
   de validación (sección 5) y **no se autocargan en el mismo ciclo en que se las ve por
   primera vez** — solo pasan si ya están `CONFIRMED`.
5. Para cada elegible restante, dentro de `order_lock.acquire((serial, sku))`: repite
   básicamente los mismos 5 bloqueos de `/load` (sin `forceOverride`, todos aplican siempre) más
   una verificación adicional contra el portal en vivo (`order_client.lookup_supplies_by_serial`,
   **fail-closed**: si no responde, se pospone al próximo ciclo en vez de arriesgar duplicar).
6. `AUTOLOAD_MAX_ORDERS_PER_CYCLE=10` — válvula de seguridad económica: si SDS devuelve datos
   anómalos (ej. todos los contadores en 1%), la app no crea pedidos reales sin límite; el
   excedente queda para el próximo ciclo.
7. Detecta kit de mantenimiento (`is_maintenance_kit`) y crea vía `create_incident_and_record`
   o `create_order_and_record` según corresponda — mismo mecanismo de idempotencia de la
   sección 3.

---

## 5. Ventana de validación (`request_validation.py`) — no es idempotencia pero es adyacente

Solicitudes elegibles que llegan en **0% exacto** (no simplemente "bajo") pasan por una ventana
de espera (`validation_window_hours`, default 6h) antes de habilitar la carga (manual o
automática) — motivado por un caso real documentado: un glitch de sensor reportó 0% cuando en
realidad seguía en ~87%, se autocargó un pedido innecesario 23 minutos después. Mientras está
`PENDING`, **ni la autocarga ni el botón manual actúan, sin excepción**; el diagnóstico
automático (`validation_diagnosis.py`) es puramente informativo, nunca decide. Se resuelve
re-consultando el nivel EN VIVO (no la foto de la solicitud) en cada ciclo del poller y en cada
carga del dashboard — si se recupera, `DISMISSED` inmediato (no espera el techo); si sigue bajo
y venció el techo, `CONFIRMED`. Relevante para la migración porque toca la misma tabla/lock que
la creación de pedidos y puede introducirse un bug de carrera si se separa mal.

---

## 6. Modelo de datos (SQLite → Postgres)

**Sin ORM**, SQL directo. Único punto de acceso: `StateDb` (`state_db.py`), compuesta por
herencia múltiple de 7 mixins en `db/`: `CustomersMixin`, `OrdersMixin`, `SuppliesMixin`,
`DevicesMixin`, `SettingsMixin`, `AlertsMixin`, `MailLogMixin`, `ValidationsMixin`, todos sobre
`db/base.py::BaseDb`. DDL centralizado en `db/schema.py` (`SCHEMA`, un solo `executescript`),
14 `CREATE TABLE IF NOT EXISTS` + 10 índices; altas incrementales de columnas vía
`run_migrations()` (patrón `PRAGMA table_info` + `ALTER TABLE ADD COLUMN`, idempotente).

**Conexión** (`BaseDb._connect`): `sqlite3.connect(path, timeout=10)`,
`row_factory=sqlite3.Row`; en cada apertura: `busy_timeout=10000`, `synchronous=NORMAL`,
`cache_size=-65536` (64MB), `temp_store=MEMORY`. WAL se activa **una sola vez** en
`__init__` (`journal_mode=WAL`), no en cada conexión. **Sin `foreign_keys=ON` en ningún lado, y
sin una sola cláusula `FOREIGN KEY` en las 14 tablas** — las relaciones (`customer_id`,
`device_id`, `hp_request_id`) son de convención, no de integridad referencial. Decisión a
tomar explícitamente en Postgres.

### 6.1. Las 14 tablas

| Tabla | PK | Notas de migración |
|---|---|---|
| `customers_config` | `customer_id` (externo, no autoincrement) | `enabled` INTEGER→BOOLEAN |
| `processed_requests` | `hp_request_id` (externo) | idempotencia central; `status` CREATED/CANCELLED (nunca DELETE real); índice `(device_serial, sku, created_at)` |
| `supply_serial_cache` | `supply_id` (externo, de CD) | `fecha` en `DD/MM/YYYY` (formato CD, no ISO) — parsear explícito al migrar; doble índice `serial`/`serial COLLATE NOCASE` → colapsa a uno funcional o `citext` en PG |
| `supply_status_history` | `id` AUTOINCREMENT | `UNIQUE(supply_id, estado)` es la dedup; único punto de escritura de estado de toda la app; **ojo con la semántica de desempate por `id` bajo `INSERT OR IGNORE`** — en PG un `SERIAL` con `ON CONFLICT DO NOTHING` sí avanza el `nextval`, comportamiento distinto |
| `pending_order_notifications` | `hp_request_id` | crecimiento indefinido, sin `prune` en el código leído |
| `scan_checkpoint` | `key` (key-value) | en la práctica 1 fila |
| `customer_zone_contacts` | `(customer_id, zone)` compuesta | `zone=''` es "zona default" real, NUNCA usar NULL con `NULLS NOT DISTINCT` en el equivalente PG |
| `app_settings` | `key` (key-value) | — |
| `order_audit` | `id` AUTOINCREMENT | historial permanente, nunca se borra; fuente de TODAS las estadísticas; `dry_run` INTEGER→BOOLEAN; `hp_request_time` es el único campo ISO-Z crudo de Insight en esta tabla |
| `known_devices` | `device_id` (externo) | únicas 2 tablas con `DELETE` real (`prune_missing_devices`, `delete_known_device`) — sin FK, sin cascada a limpiar |
| `dca_monitors` | `(customer_id, monitor_name)` compuesta | `online` no confiable solo — exige también `status='ACTIVE'` + `last_contact` vencido |
| `request_alerts` | `hp_request_id` | máquina de estados `TRIGGERED→ESCALATED→ACKNOWLEDGED\|RESOLVED`, con reapertura `RESOLVED→TRIGGERED` |
| `mail_log` | `id` AUTOINCREMENT | `kind`: backup / poller_alert / poller_recovery / pending_order_alert |
| `request_validations` | `hp_request_id` | única columna `REAL` de todo el schema (`initial_percent_left`); `deadline_at` armado con f-string + `int()` explícito (no bind param, pero sin riesgo de inyección por el cast) |

### 6.2. Tres formatos de fecha en columnas TEXT (el punto más delicado de la migración)

1. **`datetime('now')` de SQLite** — `"YYYY-MM-DD HH:MM:SS"`, siempre UTC. La mayoría de
   `created_at`/`updated_at`/`cached_at`/etc. → mapea directo a `TIMESTAMPTZ`.
2. **ISO-8601 crudo de Insight** — `"YYYY-MM-DDTHH:MM:SS.mmmZ"`, copiado tal cual en columnas
   que **no genera la app**: `request_alerts.requested_at`, `known_devices.last_contact`/
   `discovery_date`, `dca_monitors.last_contact`, `order_audit.hp_request_time`. El código
   compara estas columnas como TEXT (nunca con funciones de fecha SQLite) precisamente porque
   mezclar este formato con el de SQLite rompe el orden léxico — comentarios explícitos en
   `alerts.py`/`devices.py`. En Postgres se simplifica mucho convirtiendo a `TIMESTAMPTZ` real.
3. **`DD/MM/YYYY[ HH:MM:SS]` de Canal Directo** — solo en `supply_serial_cache.fecha`,
   convertido a `YYYYMMDD` para orden lexicográfico vía función Python o `substr()` SQL inline.
   Parsear explícito, no asumir `CAST` directo.

**"Hoy" en localtime Argentina**: todas las comparaciones de "pedidos de hoy"/estadísticas
diarias usan `date(created_at, 'localtime')` — SQLite convierte usando la **zona del sistema
operativo del proceso**, no una constante de negocio. En Postgres, el equivalente correcto es
`(created_at AT TIME ZONE 'America/Argentina/Buenos_Aires')::date` — explícito, no depender de
la TZ del servidor donde corre el contenedor.

**No hay JSON en ninguna columna** de las 14 tablas (revisado completo) — todo `TEXT` es texto
libre o IDs/nombres externos, o un entero serializado como string (`scan_checkpoint.value`).

**Booleanos**: siempre `INTEGER NOT NULL DEFAULT 0` escrito como `1 if x else 0` — mapean
directo a `BOOLEAN`.

---

## 7. Formato de fecha/hora — trampas específicas de la API de Insight

Esta es exactamente la clase de bug que el usuario ya sufrió al migrar Contadores (formato de
fecha exacto exigido por HP, OAuth distinto al asumido) — acá el equivalente documentado:

- **`timeutil.today_range_utc`**: calcula el rango "hoy" en `America/Argentina/Buenos_Aires` y
  lo devuelve **convertido a UTC** en formato `"%Y-%m-%dT%H:%M:%SZ"` (con `Z` literal, no
  offset `+00:00`) — es lo que se manda como `fromDate`/`toDate` a la API de Insight. Replicar
  ese string exacto, no asumir que cualquier ISO 8601 sirve.
- **`timeutil.format_arg_datetime`** — advertencia textual literal en el docstring:
  > "Usar SOLO con campos de Insight verificados como UTC real (`requested`/`statusDate`/
  > `replacedDate` en consumable-requests, `recordDate` en consumables/history). **NUNCA con
  > `readDateLocal` del historial de consumibles: su convención horaria no está confirmada y ya
  > causó dos conclusiones erróneas retractadas (ago-2026)**" — ver `validation_diagnosis.py`.
  **No todos los campos de fecha de la misma API son UTC** — cualquier campo de fecha nuevo que
  se use al portar el cliente de Insight hay que clasificarlo explícitamente como "UTC
  verificado" o "dudoso", nunca asumir por el nombre del campo.
- **Fechas de Canal Directo (incidentes SOAP)**: formato propio `'DD/MM/YYYY HH:MM:SS'`, **ya
  en hora Argentina** — a diferencia de Insight, acá NO hay `Z` ni conversión de huso que
  hacer (`validation_diagnosis.py::_format_cd_local`/`_cd_local_to_utc`).
- `get_consumable_history` sin `start_date` trae solo los **últimos 90 días** (default del
  propio endpoint de Insight); `start_date` acepta como máximo 12 meses atrás — más viejo da
  `400 Bad Request`. El código usa 364 días (no 365) al pedir el máximo rango.
- Conversión de TZ vía `zoneinfo.ZoneInfo`, no `pytz` — si el nuevo stack es Node/TS, verificar
  equivalencia de DST con `Intl`/`Buenos_Aires` (hoy sin DST, pero lo tuvo históricamente).
- **Auth de Insight**: no es API key simple — `POST /login` con `Authorization: Basic
  base64(key:secret)` devuelve `access_token` + `expires_in`; se cachea con margen de refresco
  de **300 segundos** (`_TOKEN_REFRESH_MARGIN_SECONDS`) antes de que expire, protegido por
  `threading.Lock` porque el poller y los endpoints del threadpool comparten el mismo cliente.
  Confirmar si esto coincide con lo que se asumía al planificar la migración — es el mismo tipo
  de sorpresa ("OAuth distinto al asumido") que ya pasó con Contadores.

---

## 8. Otras trampas concretas a las que prestar atención al reescribir

- **Timeouts explícitos obligatorios en toda llamada HTTP**: `DEFAULT_TIMEOUT = (5, 30)`
  (connect, read) en `http_util.py`, aplicado vía `Session` compartida — nunca una llamada
  `requests` suelta sin timeout (colgaría un thread del pool para siempre).
- **Reintentos SOLO en GET/HEAD/OPTIONS** (`urllib3.Retry`, `backoff_factor=0.5`,
  `status_forcelist=(429,500,502,503,504)`), **POST explícitamente excluido** —
  `allowed_methods` no incluye POST a propósito, porque reintentar la creación de un pedido lo
  duplicaría. Regla de negocio dura, no un detalle de configuración accidental.
- **`pool_maxsize=20`** en el adapter HTTP — el poller, el health check y los requests de UI
  corren en paralelo; el default de 10 generaba warnings de conexiones descartadas.
- **`read_capped_text`** (`http_util.py`) — lee streaming con `iter_content`, corta a
  `MAX_PORTAL_HTML_BYTES=5MB` antes de terminar de bajar la respuesta completa a memoria (un
  simple `len(resp.content) > max_bytes` no protege nada porque `requests` ya bajó todo para
  dar ese `.content`). Usado al parsear HTML del portal (incidentes Pre-Correctivo, PortalWeb).
- **Serial "sucio"**: `clean_serial()` saca espacios/puntos/tabs/saltos de línea — caso real
  documentado: Insight guarda `"Z83DBJEJ90000GT."` (con punto final) mientras CD tiene
  `"Z83DBJEJ90000GT"` sin punto, y `getMachineBySerial` hace match **exacto** — el punto de más
  daba un falso "equipo sin asignar" (bodega) para un equipo que en realidad seguía en cliente.
- **Extracción de serial de pedidos "origen interno"** (`_INTERNAL_SERIAL_RE` en
  `soap_query.py`): regex que busca el primer token ≥5 chars de `[A-Z0-9]` que contenga
  al menos una letra, **sin exigir que arranque con letra** — bug real corregido (supply
  `441396`): algunos seriales (impresoras Samsung) arrancan con dígito, y la versión anterior
  del regex (documentada, ahora obsoleta, en `docs/scan_supplies_matching.md` —
  **ese doc quedó desactualizado, no confiar en él para este detalle, usar el código real**)
  exigía letra inicial y los perdía.
- **`ean_check_digit`**: modulo-10 propio de Canal Directo, pesos `3,1,3,1,...` aplicados
  **de izquierda a derecha** (no desde el dígito más a la derecha como el EAN/GTIN estándar) —
  fácil de implementar mal si se asume el algoritmo estándar por el nombre.
- **`persistNewSupply`/`voidSupply`/`voidIncident` no son fiables por su respuesta**:
  `voidSupply`/`voidIncident` devuelven `"true"` **siempre**, sin importar si el ID existía o
  no — el caller siempre debe reconsultar (`fetch_supply_by_id`) para confirmar el estado real.
  Mismo patrón que `persistNewSupply` (ID "exitoso" sin insertar fila real).
- **Estados de Canal Directo por lista negra, no whitelist** (`cd_states.py`): el filtro de
  "¿sigue en tránsito?" es `estado NOT IN (terminales)`, nunca una whitelist de estados
  conocidos — bug original documentado: agregar un estado intermedio nuevo sin anticiparlo
  hacía desaparecer el pedido en silencio de cualquier vista de seguimiento.
  `RELEASE_STATES = {Anulado, Cancelado}` — **Entregado NO libera la solicitud** (es cierre
  exitoso, no anulación); confundir estos dos conjuntos es un bug fácil.
- **`getArticleParts` nunca trae `sku`** en producción, en ninguna de las dos vías (SOAP o
  portal) — el paso 1 de `insumo_matching.select_insumo_id` (match exacto por SKU) está en el
  código pero hoy nunca dispara; no eliminarlo pensando que es dead code, es forward-compatible.
- **`_verify_serial`/incidentes**: reintento de sesión (`re-login`) SOLO ante señal real de
  sesión vencida (`"/users/login" in html` o `"Debe iniciar"`) — bug corregido documentado en
  `CHANGELOG.md`: forzar re-login sin esa señal generaba loops innecesarios.
- **`DEVICE_DELETED`/baja de equipos offline**: acción **irreversible**, siempre secuencial
  (nunca paralela) con pausa entre serie y serial (rate-limit deliberado, no solo cortesía),
  gateada por `SDS_DELETE_DRY_RUN=true` por default — cambiar a `false` es una decisión
  operativa explícita, no algo que deba quedar en `false` "por si acaso" en un ambiente nuevo
  sin que alguien lo decida a propósito.
- **`CANCEL_RELOAD_DAILY_LIMIT = 3`**: constante hardcodeada en `load.py`, no configurable
  desde `/api/config` — a diferencia de los demás umbrales, este es el único bloqueo del flujo
  `/load` que no acepta `forceOverride`. Si se migra a configuración editable, evaluar si eso
  sigue siendo deseable (hoy es intencional: "techo anti-abuso real").
- **`AUTOLOAD_MAX_ORDERS_PER_CYCLE=10`**: válvula económica, hardcoded como env var pero sin
  bypass — igual de importante preservar como techo duro, no solo "límite sugerido".

---

## 9. Variables de entorno / credenciales (solo nombres, ver `config.py` y `.env.example`)

**Insight API (HP SDS Manager LATAM)**: `INSIGHT_BASE_URL`, `INSIGHT_API_KEY` (requerida),
`INSIGHT_API_SECRET` (requerida).

**SDS PortalWeb (login humano, distinto de la API key/secret)**: `SDS_PORTAL_BASE_URL`,
`SDS_PORTAL_USERNAME`, `SDS_PORTAL_PASSWORD` (opcionales, solo scripts de migración de
contactos y baja de equipos offline), `SDS_DELETE_DRY_RUN`.

**Canal Directo / WebAgentes**: `CD_BASE_URL`, `CD_USERNAME`/`CD_PASSWORD` (requeridas, hoy
solo usadas por el cliente de incidentes — los pedidos de insumos van por SOAP sin login),
`CD_ORIGEN_ID` (default `3`=Interno), `CD_MOTIVO_ID`, `CD_SOLICITANTE_*` (5 campos),
`CD_DESTINATARIO_*` (5 campos).

**Scan de supplies**: `CD_EMPRESA_IDS` (CSV; vacío = scan deshabilitado).

**Autocarga**: `AUTOLOAD_MAX_ORDERS_PER_CYCLE`.

**Integración post-pedido con Insight**: `INSIGHT_MARK_ACTIONED`, `INSIGHT_STATUS_ON_ORDER`
(valores válidos: ACTION, DELAYED, DELIVERED, DISPATCHED, DELETE, REJECTED, QUERY, IGNORE,
UNIGNORE — nótese `ACTION`, no `ACTIONED`: bug corregido documentado en `CHANGELOG.md
[1.0.0]`).

**App/infraestructura**: `APP_TIMEZONE`, `POLL_INTERVAL_MINUTES`, `DB_PATH`, `APP_HOST`,
`APP_PORT`, `SSL_CERTFILE`/`SSL_KEYFILE`, `LOG_PATH`, `FRONTEND_PATH`,
`BACKUP_RETENTION_DAYS`, `BACKUP_HOUR`, `OFFLINE_CHECK_HOUR`, `ALERT_CHECK_MINUTES`.

**SMTP/mail**: `SMTP_HOST` (vacío = todo el mail deshabilitado), `SMTP_PORT`,
`SMTP_USERNAME`/`SMTP_PASSWORD` (Gmail requiere "contraseña de aplicación"),
`BACKUP_MAIL_TO`/`BACKUP_MAIL_FROM`, `ALERT_MAIL_TO`, `ALERT_AFTER_FAILURES`.

**Pruebas manuales**: `DISABLE_BACKGROUND_JOBS` (para levantar una segunda instancia contra la
misma DB sin correr un segundo poller en paralelo — riesgo de carrera check-then-act entre dos
procesos con SQLite/`KeyedLock` en memoria).

Fallback legado a `config.json` en la raíz si no hay `INSIGHT_API_KEY` en el entorno —
probablemente irrelevante para la migración, documentado por si aparece en algún host viejo.

---

## 10. Deuda técnica conocida relevante para la migración

### `SEGURIDAD_PENDIENTE.md` — auditoría 2026-07-15, **8/8 hallazgos cerrados en código**
Sin pendientes de código. Único pendiente operativo (fuera de alcance del código): rotar la
contraseña de Canal Directo (era débil, 6 dígitos) y el key/secret de Insight de un
`config.json` legacy ya borrado del disco (nunca estuvo en git) — buen momento para pedir
credenciales rotadas al armar el nuevo entorno en vez de reusar las viejas.

Decisiones de seguridad explícitas a **preservar**, no bugs: sin auth en ningún endpoint (red
interna/VPN); bounds server-side en `/api/config`; `/load` resuelve todo del lado servidor;
`CANCEL_RELOAD_DAILY_LIMIT=3` no bypasseable; `SCAN_COOLDOWN_SECONDS=120`; mensajes de error
sanitizados hacia frontend/audit (nunca `str(exc)` crudo, el detalle completo solo va a
`logger.exception`); `MAX_PORTAL_HTML_BYTES=5MB` con streaming capado.

### `OPTIMIZATION_PLAN.md` — Fases 1-5 completas, sin ítems abiertos
Nada pendiente en "próximos pasos" (paginación server-side, estadísticas históricas, request
ID tracing — entregados). Relevante para portar: timeouts explícitos como estándar obligatorio
(sección 8), reintentos solo en GET, anti-duplicados con lock por `(serie,sku)` (sección 3.4),
idempotencia `SDS-{hp_request_id}` (sección 3.1), queries batch (`get_processed_ids`,
`find_active_supplies_by_serials`) en vez de N+1 — patrón a preservar en el nuevo query layer.

### Documentación desactualizada detectada durante esta caracterización
`docs/scan_supplies_matching.md` transcribe `_INTERNAL_SERIAL_RE` con la versión **vieja** del
regex (exige letra inicial) — el código real ya no la tiene (fix del serial que empieza con
dígito, ver sección 8). El propio doc tiene una nota "usar como orientación, no como cita
exacta" sobre números de línea, pero no sobre este regex específico — verificado contra el
código real de `soap_query.py`, que es la fuente de verdad. Al preparar la migración, **no
copiar fragmentos de código de esta doc sin verificar contra `soap_query.py` directamente**.

### `MIGRACION.md` — runbook del host definitivo, contenido relevante para el monolito unificado
Cita literal sobre qué NO usar como plataforma: "ECS / Fargate / Lambda / App Runner / Elastic
Beanstalk. La app usa SQLite en modo WAL sobre disco local y un poller siempre encendido; en
plataformas gestionadas eso obliga a EFS/NFS (locking de SQLite roto) o a migrar a Postgres,
que es una decisión de producto aparte" — decisión que la migración actual ya está tomando.
Salidas HTTPS necesarias a preservar en el hosting nuevo: `hp-sds-latam.insightportal.net`
(Insight + PortalWeb), `webagentes.canaldirecto.com.ar` (scraping incidentes/PortalWeb),
`wsg.cdsisa.com.ar` (SOAP wsAyC), SMTP (backups/alertas). Poller siempre encendido — no
compatible con serverless; decidir cómo convive con los pollers de los demás módulos ya
migrados (¿uno por módulo vs. un scheduler central del monolito?). Regla de negocio a preservar
en cualquier topología nueva: **nunca dos instancias activas a la vez contra Canal Directo**
(riesgo de pedidos reales duplicados) — hoy se resuelve apagando la vieja antes de encender la
nueva; en Postgres con múltiples réplicas hay que resolverlo con locks reales, no solo
disciplina operativa.

---

## 11. Resumen ejecutivo de riesgos al portar (orden de prioridad)

1. **El mecanismo de idempotencia SOAP (sección 3) es la pieza más frágil** — combina clave de
   idempotencia no persistida, verificación post-creación con reintentos por lag real medido en
   producción, un scan incremental que es la única forma de ver los propios pedidos, y un lock
   en memoria de proceso único. Reescribir cualquiera de las cuatro piezas de forma aislada, sin
   entender que dependen entre sí, es el escenario más probable de introducir duplicados reales
   de pedidos (dinero real, según el propio código).
2. **`KeyedLock` en memoria no sobrevive a múltiples instancias/procesos** — si el monolito
   unificado corre más de un worker o réplica, hay que reemplazarlo por un mecanismo real de
   Postgres (constraint único + `ON CONFLICT`, o advisory lock), no portar la clase tal cual.
3. **Tres formatos de fecha distintos conviviendo en columnas TEXT**, con reglas de comparación
   ad-hoc (orden léxico ISO-Z vs. `datetime('now')` vs. `DD/MM/YYYY`) — la conversión de tipos
   al migrar a `TIMESTAMPTZ` de Postgres es más trabajo real que el DDL en sí, que ya está
   centralizado y es simple.
4. **No todos los campos de fecha de la API de Insight son UTC** — `readDateLocal` tiene
   semántica horaria no confirmada y ya generó bugs reales retractados; clasificar cada campo
   nuevo explícitamente, no asumir por el nombre.
5. **Sin autenticación por diseño** — decisión consciente a revisar como cambio de producto
   explícito al integrar al monolito (que sí tiene auth), no heredar el supuesto "red interna"
   sin decidirlo.

---

## Archivos leídos (rutas absolutas, referencia)

`backend/src/sds_autoloader/{main,config,poller,soap_query,canal_directo_client,
canal_directo_soap_client,canal_directo_incident_client,insight_client,insumo_matching,
request_validation,validation_diagnosis,pending_requests,pending_orders,concurrency,
http_util,cd_states,state_db}.py`, `backend/src/sds_autoloader/db/{__init__,base,schema,
alerts,customers,devices,mail_log,orders,settings,supplies,validations}.py`,
`backend/src/sds_autoloader/routers/{alerts,audit,config,customers,estadisticas,mail_log,
new_devices,offline_devices,scan}.py`, `backend/src/sds_autoloader/routers/requests/
{__init__,query,load,actions,models}.py`, `SDSInsumos/CLAUDE.md`, `SDSInsumos/CHANGELOG.md`,
`SDSInsumos/docs/{SEGURIDAD_PENDIENTE,OPTIMIZATION_PLAN,scan_supplies_matching,
web_scraping_reference}.md`, `SDSInsumos/docs/adr/{001..004}-*.md`, `SDSInsumos/MIGRACION.md`,
`SDSInsumos/.env.example`. Tests corridos en vivo: `backend/tests/` completo (504 passed).
