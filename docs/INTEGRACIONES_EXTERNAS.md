# Integraciones externas del backend

Mapa de todos los sistemas externos que consume el backend: qué módulos los usan, por qué
puerto/adapter, desde qué endpoints/jobs, con qué timeout, qué política de retry y cómo
degradan sin configuración. Relevado el 2026-08-14 (Fase 0 del refactor de integraciones —
ver ADR-018 cuando exista). Estado: **pre-refactor** — las inconsistencias marcadas 🔴 son
los hallazgos que el refactor corrige.

Inventario verificado con grep sobre `backend/src`: **6 gateways pyodbc** (SIGES/MERCURIO),
**2 gateways zeep** (wsAyC), **9 archivos httpx** (Insight, SDS Portal, SDS web, Epson ERS,
Gestión web, feriados), **1 smtplib** (SMTP), **1 ftplib** (FTP db3).

---

## 1. SIGES / MERCURIO (SQL Server, pyodbc)

Base `Siges` del SQL Server MERCURIO, cuenta de solo lectura `SiGesReadOnly`. Config
compartida en `shared/infrastructure/mercurio/connection.py`
(`build_mercurio_connection_string`); settings bajo el nombre histórico `sla_mercurio_*`
(sla fue el primero en usarlas — no se renombran: integración verificada en producción).
pyodbc es síncrono: toda consulta corre en `asyncio.to_thread`, con conexión efímera por
consulta (timeout de login + timeout de consulta, ambos `sla_mercurio_timeout_seconds`,
default 30 s). Todo `pyodbc.Error` se traduce a `ExternalServiceError` (→ 502) con log
contextualizado.

🔴 **Sin límite de concurrencia**: no existe tope de consultas simultáneas contra MERCURIO.
La consulta de sla tarda ~40 s y la de equipos-sin-real ~10 s; requests de usuarios + jobs
pueden apilarse sin cota.

| Módulo | Adapter (infrastructure) | Puerto (domain) | Factory | Consumidores | Timeout | Sin config |
|---|---|---|---|---|---|---|
| sla | `mercurio/pyodbc_sla_query_gateway.py` | `SlaQueryGateway` | `get_sla_query_gateway` (`lru_cache` + chequeo host) | `GET /api/sla/resumen`, `GET /api/sla/incidentes-vencidos`, `POST /api/sla/actualizar` (refresh on-demand del snapshot), job `sla/presentation/background_jobs.py` (refresco periódico) | 30 s | fail-fast 502 ("falta SLA_MERCURIO_HOST"); el job loguea y no arranca |
| prestadores | `siges/pyodbc_prestador_gateway.py` | `SigesPrestadorGateway` | `get_prestador_siges_gateway` (`lru_cache` + chequeo) y `_or_none` | `GET /api/prestadores` (listado, `_or_none`: degrada al último parque persistido), sync de parque (estricta) | 30 s | listado degrada con warning; sync fail-fast 502 |
| contadores | `siges/pyodbc_operador_gateway.py` | `OperadorCatalogPort` | `get_operador_catalog_gateway` (`lru_cache` + chequeo) | `GET /api/contadores/calendario/operadores` (catálogo, ADR-012) | 30 s | fail-fast 502 |
| contadores | `siges/pyodbc_parque_cliente_gateway.py` | `ParqueClientePort` | `get_parque_cliente_gateway` (`lru_cache` + chequeo) y `_or_none` | card de Inicio `resumen-clientes` (`_or_none`: va sin impresoras), búsqueda de empresas del modal (estricta) | 30 s | card degrada con warning; búsqueda fail-fast 502 |
| contadores | `siges/pyodbc_equipos_sin_real_gateway.py` | `EquiposSinRealPort` | `get_equipos_sin_real_gateway` (`lru_cache` + chequeo) | `GET /api/contadores/equipos-sin-real` (+`/resumen`) | **120 s** propio (la consulta recorre Contadores completo, ~10 s) + **caché TTL 600 s** en memoria con `asyncio.Lock` (un solo refresh en vuelo) | fail-fast 502 |
| liquidaciones | `siges/pyodbc_siges_catalogo_gateway.py` | `SigesCatalogoGateway` | 🔴 `_gateway()` en `dependencies/siges.py`: **sin `lru_cache` ni chequeo de host** — gateway nuevo por request; sin MERCURIO falla con error críptico de pyodbc en vez del 502 claro | vínculos/sync de config (ADR-014): proponer/vincular PST y SPST, sync config, tarifarios (estado zonas, mapear, sync), búsqueda de sucursales | 30 s | 🔴 error críptico de pyodbc (login timeout) |

**Retry**: ninguno en ningún gateway (conexión efímera + timeout; el caller decide).
**SQL**: cada módulo conserva su `query.py` — la paridad con planillas/legacy depende de
ese SQL textual (advertencia explícita en sla); no se toca en ningún refactor.

## 2. wsAyC (SOAP Canal Directo, zeep sobre requests)

Mismo endpoint/WSDL para los dos módulos: `https://wsg.cdsisa.com.ar/wsAyC_server.php`.
🔴 Constantes `WSDL_URL`/`REAL_ENDPOINT`/timeout 30 s **hardcodeadas y duplicadas** en los
dos gateways (única integración cuya config no sale de settings). zeep es síncrono
(requests): cada llamada corre en `asyncio.to_thread`. Cliente lazy cacheado con
`threading.Lock` (cargar el WSDL es caro). **Transporte sin reintentos — regla de negocio
dura**: toda operación SOAP viaja como POST y reintentar `persistNewSupply` duplica
pedidos reales.

| Módulo | Adapter | Instanciación | Operaciones (lectura / escritura) | Manejo de errores |
|---|---|---|---|---|
| insumos | `soap/zeep_wsayc_gateway.py` (`ZeepWsAycGateway`) | singleton de proceso (`wiring.py::get_wsayc_gateway`, `lru_cache`) | L: `getMachineBySerial`, `getMachineIncidents`, `getArticleParts`, `getSupplyById`, `getIncidentById`, `getSupplyDetails`, `getTopSupplies` · E: `persistNewSupply`, `persistNewIncident`, `voidSupply`, `voidIncident` | por método, a propósito distinto: los persist y `getMachineBySerial` propagan crudo (el caller distingue); el resto degrada a vacío/None con warning; los void degradan a `False` con error |
| liquidaciones | `soap/zeep_cd_liquidaciones_gateway.py` (`ZeepCdLiquidacionesGateway`) | 🔴 **instancia nueva dentro de cada `build_*`** (`dependencies/liquidaciones.py`: sincronizar, aprobar, observar, anular, backfill) → cada request re-descarga y re-parsea el WSDL | L: `getTopLiquidations`, `getLiquidationDetails` · E: `setLiquidationStatus`, `voidLiquidation` | gets degradan a `[]` con warning; escrituras propagan crudo (+ `_raise_if_soap_error`) |

Consumidores: endpoints de insumos (customers, requests, offline_devices) + **poller de
fondo de insumos** (`background_jobs.py`: sync inventario, auto-carga, verificación de
offline, alertas) sobre el MISMO singleton que los requests de usuarios; endpoints de
liquidaciones (sincronizar/aprobar/observar/anular/backfill).

🔴 **Costo del WSDL por request en liquidaciones (medido 2026-08-14, dev, solo lectura)**:
primera llamada de un gateway recién creado mediana **1,239 s** vs **0,930 s** repetida →
**~0,31 s de sobrecosto por request** + una descarga del WSDL contra wsg.cdsisa.com.ar por
request. La carga+parseo del `wsdl.Document` aislada mide **0,197 s**.

🔴 **Thread-safety del singleton compartido** (verificado contra código instalado, zeep
4.3.3 / requests 2.34.2): el `threading.Lock` de ambos gateways protege solo la
CONSTRUCCIÓN del cliente. Las llamadas concurrentes (poller + requests) comparten un único
`requests.Session` (`zeep/transports.py::Transport.post` → `self.session.post`).
`requests.Session` **no está documentado como thread-safe** (ni el FAQ ni Advanced Usage
dan ninguna garantía) y su `Session.send` **muta estado compartido en cada respuesta**
(`extract_cookies_to_jar(self.cookies, ...)`, `sessions.py:799`). El pooling de urllib3 sí
es thread-safe, y el cookie jar tiene lock interno, así que no se espera corrupción — pero
es estado mutable compartido sin contrato, con riesgo de cross-talk de cookies (el server
es PHP) y de romperse en upgrades.

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

---

## Locks entre workers

Resuelto con advisory locks de Postgres (ADR-008) — fuera del alcance de este mapa.

## Alcance del refactor (referencia)

Fases 1–3 del refactor centralizan SOLO la plomería de **MERCURIO** (runner compartido +
factories únicas + semáforo de concurrencia) y **wsAyC** (provider único del cliente zeep,
constantes a settings). Los puertos de domain, el SQL de `query.py` y el parsing SOAP por
módulo son negocio y quedan donde están. Insight/SDS/ERS/Gestión web/FTP/feriados/SMTP:
inventariados acá, no migrados en esta pasada.
