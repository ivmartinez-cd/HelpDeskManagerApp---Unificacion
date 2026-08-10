# Insumos (SDSInsumos) — estado del paso 2, para retomar en otra sesión

Este documento existe porque la sesión que arrancó el paso 2 (cliente SOAP real +
`POST /requests/{id}/load`) se cortó a mitad de la investigación y sigue en otra máquina.
Tiene que poder leerse solo, sin el historial de chat: reconstruye el estado completo y deja
explícitas las decisiones que faltan antes de escribir código.

## 1. Estado de commits (árbol limpio, nada pendiente)

| Commit | Qué |
|---|---|
| `bbf7a52` | fixes de cumplimiento ARCHITECTURE_GUIDE (logging, paginación, tamaño de archivo) |
| `3e36db2` | **Insumos paso 1**: scaffold del módulo, 15 modelos ORM, migración `ebe03bf01e96`, idempotencia, tests, 4 contratos import-linter |
| `f8aed00` | Calendario de Planificación (backend + frontend) |
| `6edeeab` | Calendario vista mes + filtro Facturación; se commiteó `Portal mesa de ayuda corporativo_2/` |

Verificación que pasó antes de commitear el paso 1: `lint-imports` 8/8, `ruff check` limpio,
`mypy src` 258 archivos limpio, `pytest tests/unit -q` 95 passed, `tsc --noEmit` limpio, y
ciclo real `alembic upgrade head → downgrade -1 → upgrade head`.

**Aviso pendiente de decidir**: `backend/src/shared/infrastructure/config/settings.py` tiene
hardcodeada `gestion_web_cookie = "theme=dark; PHPSESSID=..."` (cookie de sesión real como
default de código, del feature Calendario). Sigue el mismo patrón preexistente de
credenciales SDS/ERS en ese archivo, pero conviene moverla a `.env` cuando se toque ese
módulo.

## 2. Qué quedó hecho del paso 1 (base sobre la que construye el paso 2)

- 14 tablas legacy portadas a Postgres + `order_claim` (tabla nueva), todas en
  `backend/src/modules/insumos/infrastructure/models/`.
- `ClaimedOrderCreation` (`domain/services/claimed_order_creation.py`) — reemplazo real de
  `KeyedLock`: reclama `(device_serial, sku)` con un índice único parcial de Postgres, sin
  mantener transacción abierta durante la I/O externa larga.
- `verify_with_retries` (`domain/services/verify_with_retries.py`) — backoff `(0,1,2,4)s`,
  replica el incidente real 443017/SDS-974325.
- `SqlAlchemyOrderClaimRepository` — probado con concurrencia real (dos sesiones
  independientes + `asyncio.gather`), no solo con fakes.
- **Trampa ya resuelta, no repetirla**: el `index_where` del `ON CONFLICT` tiene que ser
  `text("status = 'IN_PROGRESS'")` (literal SQL). Con la expresión Python
  (`OrderClaimModel.status == "IN_PROGRESS"`) compila como parámetro bindeado y Postgres
  rechaza el `ON CONFLICT` porque el predicado no coincide textualmente con el del índice
  parcial.
- **Correr los tests de integración desde el host Windows** (`cd backend && uv run pytest
  tests/integration ...`), no con `docker exec`: el conftest apunta a `localhost:5440`, que
  solo resuelve desde el host.

## 3. Hallazgo principal del paso 2: el alcance es más grande de lo planificado

El plan original definía el paso 2 como "cliente SOAP real + `POST /requests/{id}/load`".
Al leer el código legacy real (`routers/requests/load.py`, 434 líneas, repo
`C:\Users\imartinez.CDSA\Desktop\proyectos\SDSInsumos\backend\src\sds_autoloader\`),
`/load` **no depende solo del SOAP**: depende de dos servicios externos y de cinco tablas.

Lo que el `/load` legacy necesita, en orden de ejecución:

1. **Insight API** (`get_consumable_requests` + `get_device_by_id`) — resuelve
   `deviceId`/`serial`/`sku`/`zone` **del lado del servidor**, nunca del body. Es una decisión
   de seguridad explícita (`load.py:52-56`), no un detalle: el body solo trae
   `customerId, customerName, dryRun, forceOverride, overrideInsumoId, revision`.
2. **5 bloqueos anti-duplicados en orden exacto**, dentro del lock:
   - Bloqueo 0 — ventana de validación pendiente (saltable con `forceOverride`).
   - Bloqueo 1 — pedido ya procesado y no cancelado → responde **idempotente** sin crear nada.
   - Bloqueo 2 — pedido ya cargado hoy para serie+sku (saltable).
   - Bloqueo 3 — pedido activo en CD para la serie (saltable, no aplica en dryRun) — usa
     `resolve_supply_match`, que depende de `supply_serial_cache`.
   - Bloqueo 4 — `CANCEL_RELOAD_DAILY_LIMIT = 3` — **el único sin bypass**, techo anti-abuso.
3. **SOAP a Canal Directo** para crear el pedido.
4. **Insight otra vez** (`update_consumable_request`) para marcar la solicitud como atendida.
5. Escrituras locales: `processed_requests`, `order_audit`, `request_alerts` (resolve),
   `supply_serial_cache` (siembra inmediata).

Además, si el consumible es kit de mantenimiento (`reorderPart.type == 'MAINTENANCE_KIT'`),
`/load` **no crea un pedido de insumo sino un incidente Pre-Correctivo** por otro cliente
(`CanalDirectoIncidentClient`, que sigue scrapeando el portal, no SOAP).

**Conclusión a decidir**: el paso 2 real se parte en al menos 3 sub-pasos (2a cliente
Insight, 2b cliente SOAP, 2c endpoint `/load` que los orquesta), o se recorta el alcance del
`/load` inicial (ej. sin kit de mantenimiento, sin `update_consumable_request`).

## 4. Lo que ya existe en el monolito y se reusa (no rehacer)

- **La API de Insight ya está integrada** en el monolito: `sds_base_url =
  "https://hp-sds-latam.insightportal.net/PortalAPI"` con `sds_api_key`/`sds_api_secret` en
  `settings.py`, y el flujo de auth completo (Basic base64(key:secret) → `POST /login` →
  `access_token`) ya implementado en
  `backend/src/modules/contadores/infrastructure/sds/httpx_sds_client_provider.py:161`. Es
  exactamente la misma API que el legacy llama "Insight".
  **Ojo**: insumos NO puede importar de contadores (contrato import-linter
  `contadores-independent-from-insumos`, en `backend/.importlinter`). Hay que replicar el
  patrón en `modules/insumos/infrastructure/`, o evaluar mover el cliente a `shared/` con un
  ADR (ver `backend/docs/adr/` para el formato).
- Jerarquía de errores (`backend/src/shared/domain/errors.py`): `ExternalServiceError` (502)
  para fallas de servicios externos, `BusinessRuleViolationError` (409) para bloqueos de
  negocio.
- Envelope de paginación `Page[T]` (`backend/src/shared/presentation/schemas/pagination.py`).
- Patrón de router: `require_permission(...)` + `Depends(get_db)` + casos de uso instanciados
  en el handler (ver `backend/src/modules/contadores/presentation/ftp_clients_router.py`).

## 5. Caracterización del SOAP (leída del código legacy real, con citas)

Repo legacy: `C:\Users\imartinez.CDSA\Desktop\proyectos\SDSInsumos\backend\src\sds_autoloader\`.

Servicio: `https://wsg.cdsisa.com.ar/wsAyC_server.php` (WSDL en `?wsdl`).
**Sin autenticación de ningún tipo** — ni headers, ni WS-Security (`soap_query.py:20-21`).

Transporte legacy: `zeep` con `Transport(session=..., operation_timeout=30)`, cliente
cacheado en un global con `threading.Lock`, y **override manual del endpoint** después de
cargar el WSDL (`client.service._binding_options["address"] = REAL_ENDPOINT`) —
`soap_query.py:59-70`. Ese override importa: el WSDL declara una address distinta de la real.

Operaciones usadas (todas devuelven **JSON dentro de un string SOAP**, se parsean con
`json.loads`):

| Operación | Parámetros | Devuelve |
|---|---|---|
| `getMachineBySerial` | `SerialNumber` | `{"Machine": {...}}` o `[]` — de acá salen `familia_id`, `empresa_id`, `sucursal_id` |
| `getArticleParts` | `IdFamilia` | `[{"id","name"}]` — insumos de la familia. **Nunca trae `sku` en producción** |
| `persistNewSupply` | `Datos` (JSON serializado) | escalar JSON con el ID nuevo, ej. `"441770"` (o `"0"` si falló) |
| `getSupplyById` | `id` (no `IdSupply` — pasarlo mal lanza TypeError en zeep y el scan queda ciego en silencio) | `{"Supply": {...}}` o `[]` |
| `getSupplyDetails` | `id`, `top` | `[{"Detail": {...}}]` — única vía que trae la descripción real del consumible |
| `getTopSupplies` | `IdEmpresa, IdSucursal, IdSector, OrderBy, Top, IdEstado` | `[{"Supply": {...}}]` — **excluye origen Interno** (`WHERE i.ID_Origen <> 3`) |
| `voidSupply` / `voidIncident` | `Datos` (JSON) | siempre `"true"`, aunque el ID no exista — hay que reconsultar para confirmar |

Payload de `persistNewSupply` (`canal_directo_soap_client.py:150-183`) — la forma exacta
importa: `{"Supply": {...20 campos...}, "Detail": [{familia_id, insumo_id, cantidad,
motivo_id}], "origen_id": ..., "Revision": ..., "revision": ...}`.
**`origen_id` va también en la RAÍZ, no solo anidado dentro de `Supply`** — bug real ya
corregido en el legacy: anidado solo, todo pedido quedaba con origen Web en vez de Interno.
`NroIncidenteCliente` es donde viaja la clave de idempotencia `SDS-{hp_request_id}`.

Verificación post-creación obligatoria (`_verify_created`, `canal_directo_soap_client.py:233`):
`persistNewSupply` **no valida que la serie exista** — si no la encuentra, el
`INSERT...SELECT FROM Maquina` no inserta filas pero devuelve igual un ID "exitoso" (MAX+1).
Por eso siempre se relee con `getSupplyById` y se compara `NroIncidenteCliente` con la
referencia, con reintentos cortos `(1, 2, 4)s` ante lag de lectura del lado de CD (caso real
documentado: pedido `443017`/`SDS-974325`, 2026-08-03). Nunca se reintenta `persistNewSupply`
en sí (duplicaría un pedido real).

Otras piezas a portar del mismo camino, ya extraídas del código real:

- `clean_serial` (`soap_query.py:42`) — saca espacios/puntos/tabs/saltos de línea; el match
  contra CD es exacto y un punto de más da un falso "equipo en bodega" (caso real
  `Z83DBJEJ90000GT.` vs `Z83DBJEJ90000GT`).
- `ean_check_digit` (`soap_query.py:73`) — modulo-10 propio de Canal Directo, pesos
  `3,1,3,1,...` **aplicados de izquierda a derecha** (no como el EAN/GTIN estándar, que arranca
  desde el dígito más a la derecha). El `orderId` que devuelve `/load` es `f"{id}-{dv}"`.
- `_INTERNAL_SERIAL_RE` (`soap_query.py:32`) — extrae el serial del campo `NroSerie` en
  pedidos de origen interno; regex ya corregido para no exigir letra inicial (bug real:
  supply `441396`, seriales de impresoras Samsung que arrancan con dígito).
- `select_insumo_id` (`insumo_matching.py`, 231 líneas) — heurística: override manual → match
  exacto por SKU (hoy nunca dispara en producción, pero no es dead code) → filtro por tipo de
  consumible (drum/developer/waste/staples/toner, por palabras clave en la descripción) →
  filtro por color dentro del tipo (mapa ES/EN) → fallback CMY → única opción disponible →
  `InsumoAmbiguoError` con las opciones candidatas para que el operador elija a mano
  (`override_insumo_id` en el reintento). Es lógica de dominio pura, portable casi 1:1 a
  `domain/services/`.
- `_resolve_contact` (`canal_directo_soap_client.py:33`) — fallback de 3 niveles: zona
  (tabla `customer_zone_contacts`, ya migrada en el paso 1) → contacto del último pedido de
  la sucursal vía SOAP (`get_supplies_for_empresa` + `fetch_supply_by_id`) → config global.
  Si falta nombre/apellido, teléfono o email de solicitante o destinatario tras los 3
  niveles, `RuntimeError` explícito — no crea el pedido con datos incompletos.

## 6. Decisiones abiertas — resolver con el usuario ANTES de escribir código

1. **Transporte SOAP**: agregar `zeep` (bloqueante — el módulo entero de operaciones SOAP en
   el legacy corre en threadpool por eso; en el monolito async hay que envolver cada llamada
   en `asyncio.to_thread`, y sería la primera dependencia bloqueante del proyecto) **vs.**
   armar los sobres SOAP a mano con `httpx` (async nativo, sin dependencia nueva; el servicio
   en sí es simple — parámetros string planos y un JSON adentro — pero hay que replicar
   namespaces/envelope exactos contra el WSDL real, sin la ayuda de zeep para generarlos).
   **No se pudo inspeccionar el WSDL real en la sesión anterior** — los dumps
   `wsdl_content.xml` / `methods_summary.txt` que habían aparecido sueltos en la raíz del
   repo ya no están (se borraron sin commitear) y el intento de bajar el WSDL en vivo
   (`curl https://wsg.cdsisa.com.ar/wsAyC_server.php?wsdl`) quedó sin ejecutar. **Bajar el
   WSDL real de nuevo es el primer paso concreto de la próxima sesión** — la decisión de
   transporte depende de ver qué tan simple/complejo es el envelope real.
2. **Alcance del `/load` inicial**: ¿incluye el camino de kit de mantenimiento (crea un
   incidente Pre-Correctivo vía `CanalDirectoIncidentClient`, que sigue siendo scraping del
   portal, no SOAP — otro cliente entero a portar)? ¿incluye
   `update_consumable_request` contra Insight al final del flujo?
3. **`supply_serial_cache` / scan incremental**: el Bloqueo 3 depende de esa tabla, que en el
   legacy se llena con un scan incremental por ID (`supply_scanner.py`, ~300 IDs por ciclo,
   20 workers en paralelo, con checkpoint). Sin ese scan portado, el Bloqueo 3 queda ciego
   para pedidos de origen Interno (los que crea esta misma app) — no se podría detectar "ya
   hay un pedido activo para esta serie" de forma confiable. ¿El `/load` del paso 2 sale sin
   ese bloqueo (aceptando el hueco temporalmente, documentado), o el scan entra antes como un
   sub-paso propio?
4. **Autenticación del endpoint**: el legacy no tiene auth en ningún endpoint **por diseño**
   (red interna/VPN, decisión documentada en `SDSInsumos/docs/SEGURIDAD_PENDIENTE.md`, 8/8
   hallazgos cerrados). El monolito unificado sí tiene auth con permisos por módulo
   (`require_permission`, ver `well_known_permissions.py` de contadores como referencia). Hay
   que definir qué permiso exige `/load` (¿uno nuevo, ej. `insumos:create_order`?) — es un
   cambio de producto explícito a decidir, no algo que se pueda heredar del legacy sin más.
5. **Modo `dryRun`**: el legacy lo implementa con un cliente intercambiable por duck typing
   (`DryRunOrderClient`, mismo `Protocol` que `SoapOrderClient`). ¿Se preserva esa forma en el
   monolito (dos implementaciones del mismo puerto de dominio)?

## 7. Recordatorios de proceso que aplican al paso 2

- Cumplir `ARCHITECTURE_GUIDE.md` **mientras se escribe**, no en auditoría aparte (ver
  `CLAUDE.md` del repo): archivo ≤300 líneas, clase ≤200, función ≤20; ningún
  `except Exception` silencioso (loguear con contexto en el punto donde se atrapa); toda
  colección devuelta por un endpoint paginada con `Page[T]`.
- Antes de dar por terminado cualquier módulo nuevo, correr dentro del contenedor del
  backend: `uv run lint-imports`, `uv run ruff check src tests`, `uv run mypy src`,
  `uv run pytest tests/unit -q`; los tests de integración correrlos desde el host Windows
  (ver punto 2 arriba).
- Para UI: no inventar patrones sin mockup existente (regla dura de esta sesión). El handoff
  del diseñador para Insumos ya está commiteado en
  `Portal mesa de ayuda corporativo_2/design_handoff_sds_insumos/`. **Pendiente sin resolver**:
  el Patrón 2 (gráfico de tendencia) del handoff reintroduce magenta `#E32D91`, que viola la
  regla de pureza de marca de esta app (solo línea Institucional: naranja `#F7941D` / gris
  `#58595B`, ni siquiera como acento puntual, con la única excepción de semaforización de
  estado rojo/amarillo/verde). Hay que reemplazar ese magenta por naranja/gris/semáforo antes
  de construir esa pantalla — no es algo que se deba editar en el handoff del diseñador sin
  avisar primero.

## Verificación de que este documento cumplió su propósito

Debería poder leerse de punta a punta sin acceso al historial de chat de la sesión que lo
escribió, y dejar a quien lo lea en condiciones de: (1) bajar el WSDL real y decidir
transporte, (2) contestar las 5 decisiones abiertas de la sección 6, (3) empezar a escribir
`modules/insumos/infrastructure/` con las citas de código de la sección 5 a mano.
