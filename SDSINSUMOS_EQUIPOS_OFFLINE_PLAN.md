# Port de Equipos Offline (SDSInsumos) al backend unificado

## Contexto

`SDSINSUMOS_MIGRACION_ESTADO.md` deja como próximo paso el punto 7, **Equipos Offline**: el
módulo más grande que queda junto con Clientes. Es la pantalla que detecta equipos que dejaron de
reportar a SDS, los clasifica contra Canal Directo para distinguir un retiro físico real de una
caída de colector, y permite darlos de baja en el PortalWeb de HP — una operación **irreversible**.

Sin esto, el inventario de SDS acumula equipos fantasma indefinidamente (medido en producción:
861 equipos ocultos de un solo cliente). El backend nuevo ya tiene todo el andamiaje: las tablas
`known_devices` y `dca_monitors` existen con todos los campos necesarios, el gateway SOAP wsAyC y
la Insight API están portados, y los 4 settings dinámicos de offline ya se editan desde
`/api/insumos/config`. **No hace falta ninguna migración de schema.**

Lo genuinamente nuevo es: el cliente de scraping del PortalWeb (compartido a futuro con Clientes) y
un mecanismo de exclusión mutua entre workers, que no tiene precedente en el monorepo.

**Alcance de esta ronda**: backend completo, incluida la baja. Fuera de alcance: el job nocturno
`background_offline_check_task` (pertenece al punto 8, diferido) y la pantalla de frontend.

### Decisiones ya tomadas

| Tema | Decisión |
|---|---|
| Verify largo (210 equipos × 2s ≈ 7 min) | `limit` **obligatorio**, tope 50, UI usa 25. La respuesta informa `remaining` para iterar |
| Lock entre workers | Advisory lock de Postgres, aplicado **también** a la baja (el legacy no la protege) |
| 3 bugs del legacy | Se corrigen los 3, documentados en el código |
| Permiso de la baja | `insumos.delete` (ya sembrado en el catálogo, sin usar) |
| Límite transaccional | Se mantiene en `get_db`, sin commits explícitos — misma exposición que `load_order` |

---

## Trampas descubiertas en el relevamiento (no obvias, alto costo si se pasan por alto)

1. **`httpx` no sigue redirects; `requests` sí.** Toda la detección de sesión vencida del portal se
   basa en `"/PortalWeb/login" in resp.url`. Sin `follow_redirects=True` explícito, `resp.url` nunca
   es `/login`, el re-login nunca ocurre y la baja falla con un error engañoso. Es el bug #1 más
   probable de este port.
2. **Nunca re-loguear especulativamente** contra el portal. Solo ante la señal confirmada de redirect
   a `/login`. Un re-login de más dispara el throttle de re-autenticación y bloquea el lote entero
   (incidente real de producción, 2026-07-30). Va documentado en el código.
3. **`CdMachine` no tiene los campos que la clasificación necesita.** Hoy expone `familia_id`,
   `empresa_id`, `sucursal_id`, `machine_id` — pero `classify_machine` necesita `Empresa` (razón
   social), `Estado` y `Sucursal` como texto. Hay que extenderlo y mapearlo en `parse_machine`.
4. **Los ADR viven en `docs/adr/` en la raíz**, no en `backend/docs/adr/` (ese directorio no existe).
5. **`insumos.delete` ya está sembrado** en `4c741806341e_seed_catalog.py` pero no declarado en
   `domain/well_known_permissions.py`.
6. Los advisory locks son **session-scoped**: acquire y release tienen que correr en la misma conexión
   física. Ver §3.

---

## 1. Lógica pura de dominio (el 70% del riesgo, testeable sin DB)

Port verbatim del legacy `SDSInsumos/backend/src/sds_autoloader/offline_devices.py`. Archivos nuevos
en `backend/src/modules/insumos/domain/`:

| Archivo | Responsabilidad |
|---|---|
| `value_objects/dca_monitor.py` | `MonitorKey` (frozen, hashable: `customer_id` + `monitor_name`) y `DcaMonitorStatus`. **La corrección del bug 3 vive en el tipo**, no en un comentario |
| `value_objects/offline_device.py` | `OfflineDevice`, `CdVerdict`, `DeviceLocationUpdate`, `MassOutage` — todos frozen |
| `value_objects/offline_clock.py` | `calendar_days_offline()` (días **calendario** en tz local) y `outage_day()` (día **UTC**, `last_contact[:10]`). Husos distintos **a propósito**: cambiar el segundo a tz local reagrupa todos los outages |
| `services/company_matching.py` | Las 3 regex + los 8 alias hardcodeados con sus comentarios de producción + `normalize_company_name`, `expand_alias`, `same_company` |
| `services/machine_classification.py` | `classify_machine()` → BODEGA / OTRO_CLIENTE / EN_CLIENTE. Separador de detalle `" · "` (U+00B7) |
| `services/outage_detection.py` | `detect_monitor_outages` (señal real, sin umbral de cantidad), `detect_mass_outages` (heurística con doble umbral), `detect_outages` (compone: excluye los del monitor y concatena sin re-sort) |
| `services/recheck_schedule.py` | `RECHECK_INTERVAL_DAYS = 7`, `select_due()` — AND de 3 condiciones, orden `last_contact ASC`, **no** filtra `offline_dismissed` |
| `services/offline_candidates.py` | `deletable = not in_outage and cd_status == "BODEGA"`. `dismissed` **no** afecta `deletable`, solo el contador |

Detalles que el port debe respetar al pie de la letra (están en el informe de relevamiento y en el
código legacy): división **float** en el umbral de porcentaje, `fleet == 0` saltea el chequeo de %,
alias de una palabra matchean por token exacto y los multipalabra por substring, `day` del outage
confirmado es el **mínimo** de los `last_contact` del grupo.

**Modificaciones**: `value_objects/cd_supply.py` (`CdMachine` += `empresa_name`, `estado`,
`sucursal_name`, aditivo con defaults), `entities/audit_record.py` (+`EVENT_DEVICE_DELETED`),
`well_known_permissions.py` (+`DELETE`), `domain/errors.py` (+`OfflineCheckInProgressError` y
`DeleteInProgressError`, ambos `BusinessRuleViolationError` → 409).

---

## 2. Puertos y repositorios

`KnownDeviceRepository` (`domain/repositories/known_device_repository.py`) suma 4 métodos:

```python
async def list_offline(self, older_than_hours: int) -> list[OfflineDevice]
async def set_device_locations(self, entries: Sequence[DeviceLocationUpdate]) -> None
async def set_offline_dismissed(self, device_id: int, dismissed: bool) -> bool
async def delete_device(self, device_id: int) -> bool
```

`list_offline` **no filtra por `customers_config.enabled`** y usa LEFT JOIN — deliberado, no es un
descuido: ese flag gobierna la auto-carga de pedidos, no si el inventario tiene equipos obsoletos
(caso Santander). `set_device_locations` pisa `cd_checked_at` **siempre**, incluso con `cd_status`
en ERROR, para que el equipo espere el intervalo de re-chequeo en vez de quemar el presupuesto del
wsAyC en el lote siguiente.

Puertos nuevos: `dca_monitor_repository.py` (`upsert`, `list_offline_monitors` → `set[MonitorKey]`,
`list_online_customer_ids`), `sds_portal_gateway.py` (`delete_device`), `exclusive_lock.py` (§3).

Implementaciones: `sqlalchemy_known_device_repository.py` (+4 métodos, queda en ~228 líneas — si
crece más, mover los mappers a `_known_device_mapping.py`) y
`sqlalchemy_dca_monitor_repository.py` (nuevo). El reset de `cd_status` cuando cambia `last_contact`
**ya está implementado** en `_refresh_values()` — reusar, no reescribir.

---

## 3. Advisory lock de Postgres

Puerto `domain/repositories/exclusive_lock.py`:

```python
class ExclusiveLock(Protocol):
    def hold(self) -> AbstractAsyncContextManager[bool]:
        """True = lock tomado (se libera al salir); False = ya lo tiene otro. Nunca espera."""
```

`AbstractAsyncContextManager` es stdlib → no viola `insumos-domain-no-frameworks`.

Adapter `infrastructure/locks/postgres_advisory_lock.py`: `pg_try_advisory_lock` (no bloqueante,
calza 1:1 con el `acquire(blocking=False)` del legacy) sobre una **conexión dedicada tomada del
engine en `isolation_level="AUTOCOMMIT"`**, sostenida por el `async with`, con `pg_advisory_unlock`
en `finally`.

Por qué no la `AsyncSession` del request: `get_db` comitea al final, y el día que alguien meta un
commit intermedio la conexión vuelve al pool y el unlock corre sobre otra → lock colgado hasta que
muera el proceso. Acoplamiento invisible que ningún test atrapa. Por qué no
`pg_try_advisory_xact_lock`: ataría una transacción abierta durante los ~3 min del verify (snapshot
retenido, vacuum bloqueado).

Dos claves distintas (`OFFLINE_VERIFY_LOCK_KEY`, `OFFLINE_DELETE_LOCK_KEY`) para que verify y delete
no se bloqueen entre sí. Se cablean en `wiring.py` con `@lru_cache`.

**ADR-008** en `docs/adr/008-advisory-lock-de-postgres-para-exclusion-entre-workers.md`: es
infraestructura sin precedente, con 3 decisiones que no se infieren del código (advisory vs. tabla
vs. Redis; conexión dedicada vs. sesión del request vs. xact lock; registro central de claves).
Nota: si un segundo módulo lo necesita, el par Protocol+adapter se muda a `shared/`.

---

## 4. Casos de uso

`application/use_cases/_offline_snapshot.py` es el corazón compartido por los 5 endpoints:
4 queries locales + detección pura + armado de filas. **Cero red** — no llama ni a Insight ni al SOAP.

| Archivo | Qué hace |
|---|---|
| `list_offline_devices.py` | `ListOfflineDevices`, `ListOfflineOutages`, `CountOfflineCandidates`, `DismissOfflineDevice` (mismo patrón que `list_new_devices.py`) |
| `sync_monitor_status.py` | `asyncio.Semaphore(8)` + `gather` (equivalente async del ThreadPoolExecutor legacy); error por cliente se loguea y se saltea, nunca aborta |
| `verify_offline_devices.py` | Lock → rows → sync monitores → snapshot → `select_due` → slice(limit) → loop SOAP **secuencial** con `asyncio.sleep(2.0)` → **un solo** write con todo (incluidos los ERROR) → summary con `remaining` |
| `delete_offline_devices.py` | Lock → snapshot fresco → loop **estrictamente secuencial**, nunca paralelo, nunca reintento |

Secuencia exacta de la baja, por equipo: (a) re-validar `deletable` server-side contra el snapshot
fresco — el frontend **no** es autoridad; (b) si no es dry-run, `portal.delete_device()`; (c)
**siempre**, incluso en dry-run, auditar `EVENT_DEVICE_DELETED` con el flag `dry_run` y detail
`f"{cd_status} · {cd_detail} · {days_offline} días offline"`; (d) si no es dry-run, borrar la fila
local. Error en un equipo → `ok=false` y **sigue** con el resto.

`VerifySummary` usa un contador tipado, lo que corrige el **bug 1** por construcción (el legacy
inicializaba la clave `"errores"` pero incrementaba `"error"`, así que el contador quedaba siempre
en 0). El verify consulta colectores caídos con `offline_monitor_hours` (48) **siempre**, nunca con
`offline_device_hours` (72) — **bug 2**, el job nocturno legacy caía a un fallback equivocado.

---

## 5. Presentation

```
GET   /api/insumos/offline-devices          -> Page[OfflineDeviceOut]   (+ filtro customerId)
GET   /api/insumos/offline-devices/outages  -> Page[MassOutageOut]
GET   /api/insumos/offline-devices/summary  -> OfflineSummaryOut { candidateCount }
POST  /api/insumos/offline-devices/verify   -> VerifyResponse           (limit obligatorio, le=50)
PATCH /api/insumos/offline-devices/{id}     -> OfflineDismissResponse
POST  /api/insumos/offline-devices/delete   -> DeleteResponse           (requiere insumos.delete)
```

**Por qué tres endpoints y no uno con envelope propio**: el legacy devolvía devices + outages +
contador en una sola respuesta, pero `Page[T]` nunca se usa anidado en este monorepo (las 10
apariciones son `response_model=Page[X]` en la raíz), y dejar `outages` como `list[...]` suelta viola
§11. Ya hay precedente idéntico resuelto igual en este mismo módulo: `SyncNewDevicesResponse`
documenta que el listado se pide aparte porque *"el legacy devolvía las dos cosas en la misma
respuesta"*. Costo real ≈ 0: los tres comparten el snapshot, que son 4 queries locales.

**`candidateCount` no se puede resolver con un COUNT en SQL** y hay que decirlo: `deletable` depende
de la detección de caídas (agrupar por cliente+día, doble umbral, señal de colectores) — expresarlo
en SQL duplicaría lógica de negocio en infraestructura. Lo que sí se corrige del legacy es que
construía la respuesta HTTP **entera** para devolver un int; acá se corta antes de instanciar
schemas y de calcular `days_offline` por fila.

Archivos: `schemas/offline_device_schemas.py` y `schemas/offline_action_schemas.py` (split preventivo
por el tope de 300 líneas), `dependencies/offline_devices.py`, `offline_devices_router.py`,
más `wiring.py` (+`get_sds_portal_gateway`, +los 2 locks), `dependencies/__init__.py` y `app.py`.

Errores: los handlers de `shared/presentation/errors/handlers.py` ya mapean `http_status`, así que
no hace falta `HTTPException` en el router — 409 sale solo de `BusinessRuleViolationError`, 502 de
`ExternalServiceError`.

---

## 6. Gateway del PortalWeb

`infrastructure/portal/portal_parsing.py` (puro: regex CSRF, marcador de éxito literal, cap de 5 MiB)
+ `infrastructure/portal/httpx_sds_portal_gateway.py`.

Flujo de la baja: `_ensure_login()` → GET del CSRF con `X-Requested-With: XMLHttpRequest` → si no hay
token **y** hubo redirect a `/login`, **un solo** re-login forzado y reintento → POST de baja con
`deleteMode="Y"` → éxito **solo** si el body contiene literalmente
`"Los cambios se han guardado correctamente"`.

Nunca adivinar ante HTML inesperado: envolver en `ExternalServiceError`. Nunca retry automático en el
POST (duplicaría la baja). Timeouts connect 5s / read 30s. **`follow_redirects=True` explícito**
(trampa 1). Login: GET a `/PortalWeb/login` **antes** del POST — el portal exige una sesión
`JSESSIONID` ya creada.

Settings nuevos en `shared/infrastructure/config/settings.py`: `sds_portal_base_url`,
`sds_portal_username`, `sds_portal_password` (SecretStr), `sds_delete_dry_run: bool = True`. Las env
vars ya están en `.env` y `.env.example`.

---

## 7. Orden de implementación

Cada paso cierra con la tanda completa de verificación (§ Verificación).

1. **Lógica pura de dominio** + extensión de `CdMachine` — el grueso del riesgo funcional, validable sin DB
2. **Puertos + repos SQL** (`known_devices` ×4, `dca_monitors` nuevo)
3. **Lock**: puerto, adapter, errores de dominio, ADR-008
4. **Snapshot + lecturas** (DTOs, `_offline_snapshot`, los 4 casos de uso de lectura)
5. **Sync de monitores** contra Insight
6. **Verify** (lock + loop SOAP pausado + write único)
7. **Gateway del PortalWeb** + settings
8. **Delete** + `EVENT_DEVICE_DELETED` + permiso `insumos.delete`
9. **Presentation** (schemas, dependencies, wiring, router, registro en `app.py`)
10. **Cierre**: actualizar `SDSINSUMOS_MIGRACION_ESTADO.md` (punto 7 hecho, restan 1 y 8)

---

## Verificación

**Por paso**, dentro del contenedor del backend (regla dura de CLAUDE.md):

```
uv run lint-imports          # contratos de capas — la más importante, no es opinable
uv run ruff check src tests
uv run mypy src
uv run pytest tests/unit -q
```

**Tests unitarios** en `backend/tests/unit/domain/insumos/`, uno por servicio puro. Los casos que no
pueden faltar:

- `test_company_matching.py`: alias de una palabra solo por token exacto (`"ausol"` sí, `"causolar"`
  no); contención bidireccional (`"Cartocor /Arcor"` ↔ `"ARCOR SAIC"`); el caso `gco` (la clave va sin
  "grupo" porque la regex de sufijos lo saca antes)
- `test_outage_detection.py`: **bug 3** — dos clientes con colector homónimo no se contaminan; outage
  confirmado sin umbral de cantidad; división float en el umbral de % (5/48 = 10.41% pasa con min 10);
  `fleet == 0` saltea el chequeo; `detect_outages` concatena sin re-sort global
- `test_recheck_schedule.py`: excluye BODEGA y miembros de outage, **no** filtra `offline_dismissed`
- `test_offline_candidates.py`: `dismissed` no afecta `deletable` pero sí el contador
- `test_offline_clock.py`: días calendario en tz local (contacto ayer 23:30 ART → 1, no 0)
- `test_verify_offline_devices.py`: excepción del SOAP → ERROR y **sigue**; el write final incluye los
  ERROR; **bug 2** — aserción explícita de que se consulta con `offline_monitor_hours`, nunca con
  `offline_device_hours`; `remaining` correcto; lock tomado → 409
- Gateway del portal con `httpx.MockTransport` (patrón de `test_httpx_insight_gateway.py`): **un solo**
  re-login ante `session_expired` y **ninguno** sin esa señal (aserción sobre el conteo de POSTs a
  `/login` — es la regla del incidente 2026-07-30); el mock debe simular el **302 real**, no el estado
  final, o el test pasa con `follow_redirects` mal configurado
- `test_delete_offline_devices.py`: dry-run no llama al portal ni borra, **pero sí audita**; formato
  exacto del detail; error en uno no aborta el lote

**Tests de integración** en `backend/tests/integration/`: `list_offline` ignora `enabled` (caso
Santander); `set_device_locations` pisa `cd_checked_at` incluso con ERROR; `list_offline_monitors`
exige los 3 AND y devuelve el **par**; el advisory lock rechaza el segundo `hold()` concurrente, libera
ante excepción, y claves distintas no se bloquean entre sí.

**Fakes**: `tests/unit/domain/insumos/offline_fakes.py` para los 3 puertos nuevos (`fakes.py` ya tiene
844 líneas); los 4 métodos nuevos de `FakeKnownDeviceRepository` sí van en `fakes.py`.

**Prueba en vivo** contra la DB de dev sembrada con backup real de producción (210 equipos offline,
ninguno verificado):

1. `GET /offline-devices` y `/summary` — deben responder sin tocar Insight ni el SOAP
2. `POST /verify` con `limit=5` — verificar en la DB que `cd_status`/`cd_checked_at` se poblaron, que
   tardó ~10s + latencia SOAP, y que `remaining` bajó de 210 a 205
3. `POST /verify` concurrente durante el anterior — debe dar 409, no correr en paralelo
4. `POST /delete` con `SDS_DELETE_DRY_RUN=true` (valor actual del `.env`) sobre un equipo en BODEGA —
   verificar que **no** se llamó al portal, que la fila **sigue** en `known_devices`, y que hay una
   fila en `order_audit` con `event='DEVICE_DELETED'` y `dry_run=true`

**La baja real (`SDS_DELETE_DRY_RUN=false`) no se prueba en esta ronda**: es irreversible contra el
portal de producción de HP y no hay entorno de prueba. Queda para una decisión explícita tuya.

---

## Riesgos y decisiones abiertas

1. **`follow_redirects`** (trampa 1): sin el flag, el port "funciona" en dev y falla la primera vez que
   expira el JSESSIONID en producción. Cubierto por test, pero el mock tiene que simular el 302 real.
2. **Transacción larga en el verify**: el request dura 2-3 min con la `AsyncSession` abierta (el commit
   es al final). No es lock — eso ya lo resuelve la conexión dedicada — pero sí un snapshot retenido.
   Mitigado por el `limit` acotado. Si molesta, la salida es mover el verify a un job (punto 8).
3. **Atomicidad de la baja**: los `record_audit` y los deletes locales del lote se comitean recién al
   final del request. Si algo lanza **después** del loop, se pierde la auditoría de bajas que ya
   ocurrieron en el portal. Mitigación de diseño: que todo lo posterior al loop sea mapeo puro de DTOs,
   sin I/O. Se mantiene el commit único por consistencia con `load_order`, que ya tiene exactamente la
   misma exposición al crear pedidos irreversibles.
4. **Pool de conexiones**: el verify sostiene 1 conexión dedicada para el lock + 1 del request durante
   minutos, sobre un pool con los defaults (5 + 10 overflow). Aceptable hoy; conviene dimensionar
   `pool_size` explícitamente en algún momento.
5. **Race verify ↔ delete**: con claves distintas, un verify puede reescribir `cd_status` mientras el
   delete valida. Ventana de milisegundos y el peor caso es un `ok=false` espurio — nunca una baja
   indebida, porque la validación es server-side y previa. Aceptable.
6. El snapshot del delete se lee **una vez** al principio del lote (igual que el legacy): en un lote
   largo, el último equipo se valida contra datos de hace un rato. Se mantiene.
