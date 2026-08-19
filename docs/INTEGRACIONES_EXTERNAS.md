# Integraciones externas del backend

Mapa de todos los sistemas externos que consume el backend: qué módulos los usan, por qué
puerto/adapter, desde qué endpoints/jobs, con qué timeout, qué política de retry y cómo
degradan sin configuración. Relevado el 2026-08-14 y actualizado tras el refactor de
acceso compartido a MERCURIO/wsAyC (ADR-018). Los hallazgos pre-refactor y su corrección
están documentados en el ADR; acá queda el estado vigente.

Inventario verificado con grep sobre `backend/src`: **6 gateways pyodbc** (SIGES/MERCURIO),
**2 gateways zeep** (wsAyC), **9 archivos httpx** (Insight, SDS Portal, SDS web, Epson ERS,
Gestión web, feriados), **1 smtplib** (SMTP), **1 ftplib** (FTP db3).

---

## 1. SIGES / MERCURIO (SQL Server, pyodbc)

Base `Siges` del SQL Server MERCURIO, cuenta de solo lectura `SiGesReadOnly`. La
plomería vive en `shared/infrastructure/mercurio/` (ADR-018): `connection.py` arma el
connection string (settings bajo el nombre histórico `sla_mercurio_*` — no se renombran:
integración verificada en producción), `query_runner.py` (`MercurioQueryRunner`) ejecuta
toda consulta — pyodbc es síncrono, corre en `asyncio.to_thread`, conexión efímera por
consulta, timeout de login + consulta (`sla_mercurio_timeout_seconds`, default 30 s),
`pyodbc.Error` → `ExternalServiceError` (→ 502) con log contextualizado — y
`factories.py::require_mercurio_runner()` es el singleton de proceso con el chequeo de
host definido una vez.

**Concurrencia**: semáforo de proceso en el runner (`MERCURIO_MAX_CONCURRENT`, default 3).
La espera es previa al connect (no consume timeouts); si una consulta espera >10 s el
runner loguea warning con el gateway en `extra`.

Los gateways de módulo son adapters finos: conservan su puerto de domain, su SQL y su
mapeo de filas, y delegan la plomería en el runner.

| Módulo | Adapter (infrastructure) | Puerto (domain) | Factory | Consumidores | Timeout | Sin config |
|---|---|---|---|---|---|---|
| sla | `mercurio/pyodbc_sla_query_gateway.py` | `SlaQueryGateway` | `get_sla_query_gateway` (`lru_cache`) | `GET /api/sla/resumen`, `GET /api/sla/incidentes-vencidos`, `POST /api/sla/actualizar` (refresh on-demand del snapshot), job `sla/presentation/background_jobs.py` (refresco periódico) | 30 s | fail-fast 502 ("falta SLA_MERCURIO_HOST"); el job loguea y no arranca |
| prestadores | `siges/pyodbc_prestador_gateway.py` | `SigesPrestadorGateway` | `get_prestador_siges_gateway` (`lru_cache`) y `_or_none` | `GET /api/prestadores` (listado, `_or_none`: degrada al último parque persistido), sync de parque (estricta) | 30 s | listado degrada con warning; sync fail-fast 502 |
| contadores | `siges/pyodbc_operador_gateway.py` | `OperadorCatalogPort` | `get_operador_catalog_gateway` (`lru_cache`) | `GET /api/contadores/calendario/operadores` (catálogo, ADR-012) | 30 s | fail-fast 502 |
| contadores | `siges/pyodbc_parque_cliente_gateway.py` | `ParqueClientePort` | `get_parque_cliente_gateway` (`lru_cache`) y `_or_none` | card de Inicio `resumen-clientes` (`_or_none`: va sin impresoras), búsqueda de empresas del modal (estricta) | 30 s | card degrada con warning; búsqueda fail-fast 502 |
| contadores | `siges/pyodbc_equipos_sin_real_gateway.py` | `EquiposSinRealPort` | `get_equipos_sin_real_gateway` (`lru_cache`) | `GET /api/contadores/equipos-sin-real` (+`/resumen`) | **120 s** propio (vía `timeout_override`; la consulta recorre Contadores completo, ~10 s) + **caché TTL 600 s** en memoria con `asyncio.Lock` (un solo refresh en vuelo) | fail-fast 502 |
| liquidaciones | `siges/pyodbc_siges_catalogo_gateway.py` | `SigesCatalogoGateway` | `_gateway()` en `dependencies/siges.py` (`lru_cache`) | vínculos/sync de config (ADR-014): proponer/vincular PST y SPST, sync config, tarifarios (estado zonas, mapear, sync), búsqueda de sucursales | 30 s | fail-fast 502 |
| preventivos | `siges/pyodbc_preventivos_gateway.py` | `PreventivosQueryGateway` | `get_preventivos_gateway` (`lru_cache`) | `GET /api/preventivos/equipos` (parque por zona + último preventivo, consulta en vivo, ADR-019), `GET /api/preventivos/zonas` (catálogo) | 30 s + **caché TTL 300 s** por zona en memoria con `asyncio.Lock` (la consulta mide 0.2-0.4 s por zona) | fail-fast 502 |

**Retry**: ninguno en ningún gateway (conexión efímera + timeout; el caller decide).
**SQL**: cada módulo conserva su `query.py` — la paridad con planillas/legacy depende de
ese SQL textual (advertencia explícita en sla); no se toca en ningún refactor.
**Candado**: contrato de import-linter `pyodbc-zeep-solo-infrastructure` — `pyodbc` solo
importable desde infrastructure (hoy, solo el runner compartido lo importa).

## 2. wsAyC (SOAP Canal Directo, zeep sobre requests)

Mismo endpoint/WSDL para los dos módulos: `https://wsg.cdsisa.com.ar/wsAyC_server.php`.
La fuente única del cliente es `shared/infrastructure/wsayc/client_provider.py`
(`WsAycClientProvider`, ADR-018): el `wsdl.Document` se descarga y parsea una vez por
proceso (lazy, bajo lock, ~0,2 s) y cada llamada recibe un `Client` liviano con
`Transport`/`requests.Session` propios sobre ese Document — `requests.Session` no está
documentado como thread-safe y muta su cookie jar en cada respuesta, así que el poller y
los requests no comparten estado mutable (costo por llamada igual al singleton, medido).
Config en settings: `WSAYC_WSDL_URL`, `WSAYC_ENDPOINT`, `WSAYC_TIMEOUT_SECONDS` (defaults
= los valores antes hardcodeados). zeep es síncrono (requests): cada llamada corre en
`asyncio.to_thread`. **Transporte sin reintentos — regla de negocio dura**: toda
operación SOAP viaja como POST y reintentar `persistNewSupply` duplica pedidos reales.

| Módulo | Adapter | Instanciación | Operaciones (lectura / escritura) | Manejo de errores |
|---|---|---|---|---|
| insumos | `soap/zeep_wsayc_gateway.py` (`ZeepWsAycGateway`) | singleton de proceso (`wiring.py::get_wsayc_gateway`, `lru_cache`) sobre el provider compartido | L: `getMachineBySerial`, `getMachineIncidents`, `getArticleParts`, `getSupplyById`, `getIncidentById`, `getSupplyDetails`, `getTopSupplies` · E: `persistNewSupply`, `persistNewIncident`, `voidSupply`, `voidIncident` | por método, a propósito distinto: los persist y `getMachineBySerial` propagan crudo (el caller distingue); el resto degrada a vacío/None con warning; los void degradan a `False` con error |
| liquidaciones | `soap/zeep_cd_liquidaciones_gateway.py` (`ZeepCdLiquidacionesGateway`) | singleton de proceso (`dependencies/liquidaciones.py::_cd_gateway`, `lru_cache`) sobre el provider compartido | L: `getTopLiquidations`, `getLiquidationDetails` · E: `setLiquidationStatus`, `voidLiquidation` | gets degradan a `[]` con warning; escrituras propagan crudo (+ `_raise_if_soap_error`) |

Consumidores: endpoints de insumos (customers, requests, offline_devices) + poller de
fondo de insumos (`background_jobs.py`: sync inventario, auto-carga, verificación de
offline, alertas); endpoints de liquidaciones (sincronizar/aprobar/observar/anular/
backfill). Delta consciente del refactor (documentado en ADR-018): sin continuidad de
cookies entre llamadas — wsAyC no la necesita (liquidaciones ya operaba con cliente
fresco por request en producción).

## 3. Insight (HP SDS Portal API, httpx)

- Módulo: insumos. Adapter: `insight/httpx_insight_gateway.py` (`HttpxInsightGateway`),
  singleton (`lru_cache`), cachea el token con margen de refresco.
- Config: `insight_base_url` (+ key/secret). Timeout: 30 s (connect 5 s).
- Retry: **solo GET** (429/5xx, backoff corto) — PATCH nunca (mutación, efectos dobles;
  misma regla que el legacy).
- Consumidores: endpoints de insumos + poller de fondo.

## 4. SDS Portal (scraping autenticado, httpx)

- Módulo: insumos. Adapter: `portal/httpx_sds_portal_gateway.py`, singleton (`lru_cache`).
- Config: `sds_portal_base_url` + usuario/password. Timeout: 30 s (connect 5 s). Sin retry.

## 5. SDS web (contadores, httpx)

- Módulo: contadores. Adapter: `sds/httpx_sds_client_provider.py` (cliente por operación,
  `async with`). Timeout: `sds_timeout_seconds` (default 20 s). Sin retry.

## 6. Epson ERS (contadores, httpx + token file)

- Módulo: contadores. Adapters: `ers/httpx_ers_client_provider.py`,
  `httpx_ers_token_refresher.py` (refresh de token con reintento de la operación tras
  re-login), `ers_device_telemetry.py`. Timeout: `epson_ers_timeout_seconds` (default 15 s;
  el refresher usa 30 s).

## 7. Gestión web (scraping gestion.cdsa.com.ar, httpx)

- Módulo: contadores. Adapters: `gestion/gestion_session_refresher.py` (login),
  `gestion_planificacion_client.py`. Timeout: `gestion_web_timeout_seconds` (default 15 s).
  Fuente de planificación del calendario (ADR-012).

## 8. FTP (descarga de .db3 de contadores, ftplib)

- Módulo: contadores. Adapter: `ftp/ftplib_db3_downloader.py`. Timeout: 8 s. Síncrono, en
  thread.

## 9. Feriados (api.argentinadatos.com, httpx)

- Módulo: vacaciones. Adapter: `argentinadatos_feriados_client.py`. Timeout: 15 s.
  `httpx.HTTPError` → `ExternalServiceError` con log. Sin retry.

## 10. SMTP (Gmail de Canal Directo, smtplib)

- Compartido vía puerto `Mailer`; adapter en `auth/infrastructure/smtp_mailer.py`
  (STARTTLS, timeout 10 s, síncrono en thread). Lo usan auth y los jobs de mail de insumos
  (`mail_delivery.py`, ADR-010). **Credenciales reales** — regla de CLAUDE.md:
  `DISABLE_BACKGROUND_JOBS=true` antes de tocar cualquier código de jobs.

## 11. Google Maps (Distance Matrix + Geocoding, httpx)

- Módulo: liquidaciones (Tabla KM). Puertos: `GoogleMapsGateway` (distancias ida y
  vuelta) y `GeocodingGateway` (candidatos por dirección) en
  `liquidaciones/domain/repositories/`; adapters httpx en
  `liquidaciones/infrastructure/google_maps/` (timeout 30 s, errores →
  `ExternalServiceError`, **sin retry**). Se agregó al inventario en 2026-08-15 — se le
  había escapado a la pasada del ADR-018.
- **Key corporativa y paga** (`GOOGLE_MAPS_API_KEY`, cuenta de Canal Directo): $5/1000
  por request de Geocoding y por elemento de Distance Matrix, 10.000 gratis/mes por SKU
  (pricing marzo 2025). Controles obligatorios: cache de geocodes por dirección
  normalizada (`geocode_cache`, incluye ZERO_RESULTS), tope por corrida
  (`GOOGLE_MAPS_MAX_CALLS_PER_RUN`, default 200 unidades facturables) y contador de
  llamadas visible en cada resultado. El cálculo masivo es two-step: el preview llama a
  Google una vez y el apply materializa sin re-llamar.
- Estado de la key (verificado 2026-08-15): Geocoding ✓, Distance Matrix ✓ (Legacy, sin
  fecha de apagado); Routes API y Places (New) NO habilitadas (403). Si algún día se
  migra a Routes `computeRouteMatrix`, va un adapter nuevo detrás del mismo puerto y el
  viejo se retira en el mismo commit.

## 12. Georef (apis.datos.gob.ar, API del Estado argentino, httpx)

- Módulo: liquidaciones (geovalidación de coordenadas Tabla KM, Tier 1). Puerto:
  `GeoreferenciacionGateway` en `liquidaciones/domain/repositories/`; adapter httpx en
  `liquidaciones/infrastructure/georef/httpx_georef_gateway.py` (timeout 30 s, errores →
  `ExternalServiceError`). Agregado al inventario en 2026-08-19 al implementarse — no se
  le escapa al ADR-018 como le pasó a Google Maps.
- **Gratuita, sin autenticación** (doc oficial: "completamente gratuita y no requiere
  autenticación"). Sin rate limit publicado, pero sin abuso: llamadas secuenciales con
  pausa configurable (`GEOREF_PAUSA_SEGUNDOS`, default 0.2 s) y backoff acotado (2
  reintentos, 1 s/2 s) SOLO ante 429/5xx — un error persistente o un 4xx no reintentable
  se propaga, no se reintenta en loop. Tope por corrida (`GEOREF_MAX_CALLS_PER_RUN`,
  default 200) — no por costo, por duración del request HTTP.
- Endpoint usado: `/ubicacion` (reverse geocoding por lat/lon). Shape verificado en vivo
  contra la API real antes de escribir el parser: `provincia.nombre == null` es "sin
  cobertura para ese punto" (HTTP 200, no error). El endpoint `/direcciones` (geocode de
  domicilio) no se implementó — cobertura de calles pobre para San Juan confirmada en la
  medición de Fase 0 (0 resultados en 4 pruebas reales).
- Cache propio (`georef_reverse_cache`, no comparte tabla con `geocode_cache` de Google
  — shape de dato distinto) por pin redondeado a 4 decimales (~11 m), evita re-consultar
  el mismo punto.

## 13. Nominatim / OpenStreetMap (nominatim.openstreetmap.org, httpx)

- Módulo: liquidaciones (geovalidación de coordenadas Tabla KM, Tier 1b — segunda
  opinión). Puerto: `NominatimGateway`; adapter httpx en
  `liquidaciones/infrastructure/nominatim/httpx_nominatim_gateway.py` (timeout 30 s,
  errores → `ExternalServiceError`, **sin backoff ante error** — a diferencia de
  Georef: un 5xx de Nominatim probablemente signifique que se violó el rate limit,
  mejor fallar ese caso que insistir). Agregado al inventario en 2026-08-19 al
  implementarse.
- **Gratuito**, pero con política de uso DURA
  (https://operations.osmfoundation.org/policies/nominatim/), cumplida al pie de la
  letra: máximo **1 req/s** (lock + timestamp en la instancia singleton del gateway —
  serializa TODAS las llamadas del proceso), User-Agent identificable propio
  (`HelpDeskManager-CanalDirecto-Geovalidacion/1.0`), secuencial (un solo
  thread/proceso), cache **obligatoria** (no solo cortesía), atribución ODbL visible
  donde se muestra el dato (`"Data © OpenStreetMap contributors, ODbL 1.0"`, viaja en
  cada hallazgo de la API y se renderiza en la UI).
- Uso acotado a propósito: **solo consulta lo que Tier 1 (Georef) ya marcó
  incompatible** — nunca el universo completo del PST. Si Nominatim coincide con
  Georef, son dos fuentes independientes de acuerdo (confirmación fuerte sin gastar
  Google).
- Endpoint usado: `/reverse` (reverse geocoding por lat/lon, `format=jsonv2`). Shape
  verificado en vivo antes de escribir el parser: `{"error": "..."}` con HTTP 200 es
  "sin resultado", la provincia vive en `address.state`.
- Cache propio (`nominatim_reverse_cache`) por pin redondeado a 4 decimales.

---

## Locks entre workers

Resuelto con advisory locks de Postgres (ADR-008) — fuera del alcance de este mapa.

## Alcance del refactor (ADR-018)

El refactor centralizó SOLO la plomería de **MERCURIO** (runner compartido + factory
única + semáforo de concurrencia) y **wsAyC** (provider único del cliente zeep,
constantes a settings). Los puertos de domain, el SQL de `query.py` y el parsing SOAP por
módulo son negocio y quedaron donde estaban. El patrón queda disponible para el resto
(Insight/SDS/ERS/Gestión web/FTP/feriados/SMTP), inventariado acá y no migrado en esa
pasada. Hallazgos pre-refactor, mediciones y decisiones: ADR-018 y los scripts
`backend/scripts/medir_*.py` / `smoke_*.py`.
