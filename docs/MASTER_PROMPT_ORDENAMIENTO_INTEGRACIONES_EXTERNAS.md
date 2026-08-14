# Master Prompt — Ordenamiento de las integraciones externas (SigesReadOnly / wsAyC)

Consolidar el acceso a las herramientas de la empresa — hoy principalmente **Siges/MERCURIO
(pyodbc, cuenta SiGesReadOnly)** y **wsAyC (SOAP zeep)** — que está repetido módulo por módulo:
6 gateways pyodbc en 4 módulos y 2 gateways zeep en 2 módulos, cada uno duplicando la misma
plomería (to_thread, conexión efímera, wrap de errores, factory con chequeo de config), con
inconsistencias reales entre sí. El objetivo es una capa compartida de infraestructura + reglas de
concurrencia para que las consultas no se pisen, **sin cambiar ningún comportamiento de negocio**.

Generado el 2026-08-14 a partir del análisis del código real. El inventario de duplicación del
[CONTEXTO] está verificado archivo por archivo; los dos riesgos de concurrencia señalados en la
Fase 0 (thread-safety de zeep compartido, WSDL por request en liquidaciones) están fundados en el
código pero su impacto real hay que medirlo, no asumirlo.

---

```text
[ROL]
Actuá como arquitecto/desarrollador senior full-stack del monorepo HelpDeskManagerApp---Unificacion
(FastAPI + SQLAlchemy async + Alembic + Next.js App Router, arquitectura módulo→capa
domain/application/infrastructure/presentation). Conocés y aplicás ARCHITECTURE_GUIDE.md y CLAUDE.md
del repo como reglas obligatorias. Este es un refactor de infraestructura CONDUCTUAL-NEUTRO: si al
final algo de negocio se comporta distinto, está mal hecho. Respondés en español de Argentina,
directo y sin relleno.

[CONTEXTO]
Estado actual verificado contra el código (no supuesto):

SIGES/MERCURIO (SQL Server, pyodbc, cuenta de solo lectura SiGesReadOnly):
- Único código compartido: `shared/infrastructure/mercurio/connection.py`
  (`build_mercurio_connection_string`). Las settings se llaman `sla_mercurio_*` por razón
  histórica (sla fue el primero) pero las usan 4 módulos — el docstring ya lo aclara.
- 6 gateways pyodbc, uno por consulta, repartidos así:
  · sla: `infrastructure/mercurio/pyodbc_sla_query_gateway.py`
  · prestadores: `infrastructure/siges/pyodbc_prestador_gateway.py`
  · contadores: `infrastructure/siges/pyodbc_operador_gateway.py`,
    `pyodbc_equipos_sin_real_gateway.py` (timeout propio 120 s + cache TTL 600 s),
    `pyodbc_parque_cliente_gateway.py`
  · liquidaciones: `infrastructure/siges/pyodbc_siges_catalogo_gateway.py`
- Cada gateway duplica el mismo esqueleto (~30 líneas): `asyncio.to_thread` (pyodbc es síncrono),
  conexión efímera por consulta (`pyodbc.connect` + timeout de login y de consulta),
  `pyodbc.Error` → `ExternalServiceError` con log contextualizado.
- Las factories duplican otro patrón: `lru_cache` + chequeo "falta SLA_MERCURIO_HOST" en
  sla/prestadores/contadores (prestadores y contadores además con variante `_or_none` que degrada
  con warning). INCONSISTENCIA REAL: `liquidaciones/presentation/dependencies/siges.py::_gateway()`
  NO tiene `lru_cache` NI chequeo de host — sin MERCURIO configurado falla con error críptico de
  pyodbc en lugar del 502 claro de los demás, y arma un gateway nuevo por request.
- No existe ningún límite de concurrencia hacia MERCURIO: la consulta de sla tarda ~40 s, la de
  equipos-sin-real ~10 s (timeout 120 s), y jobs de fondo + requests de usuarios pueden apilarse
  sin tope.

wsAyC (SOAP de Canal Directo, zeep sobre requests, `wsg.cdsisa.com.ar/wsAyC_server.php`):
- 2 gateways: `insumos/infrastructure/soap/zeep_wsayc_gateway.py` (175 líneas) y
  `liquidaciones/infrastructure/soap/zeep_cd_liquidaciones_gateway.py` (220 líneas). Es el MISMO
  endpoint/WSDL; las constantes `WSDL_URL`/`REAL_ENDPOINT`/timeout 30 s están HARDCODEADAS y
  DUPLICADAS en los dos archivos (no salen de settings, a diferencia de todo el resto de la app).
- Ambos duplican el mismo esqueleto: cliente zeep lazy cacheado con `threading.Lock` (cargar el
  WSDL es caro), llamadas via `asyncio.to_thread`, transporte SIN reintentos (regla de negocio
  dura: reintentar `persistNewSupply` duplica pedidos reales).
- INCONSISTENCIA REAL: insumos instancia su gateway como singleton de proceso
  (`wiring.py::get_wsayc_gateway` con `lru_cache`); liquidaciones hace
  `ZeepCdLiquidacionesGateway()` NUEVO dentro de cada `build_*`
  (`dependencies/liquidaciones.py` líneas ~132/145/154/163/171) → cada request arranca con
  `_client=None` y la primera llamada SOAP re-descarga y re-parsea el WSDL. Costo por request +
  tráfico innecesario contra wsg.cdsisa.com.ar.
- El lock de ambos gateways protege solo la CONSTRUCCIÓN del cliente, no las llamadas: el
  singleton de insumos es usado a la vez por el poller de fondo y por requests de usuarios, todos
  compartiendo un mismo `requests.Session` interno del Transport de zeep.

OTRAS integraciones externas (fuera del alcance del refactor, pero entran al inventario):
insumos: Insight (`HttpxInsightGateway`, cachea token), SDS Portal (`HttpxSdsPortalGateway`);
contadores: Epson ERS (httpx + token file), Gestión web (scraping `gestion.cdsa.com.ar`), SDS web;
shared: SMTP. Locks entre workers ya resueltos con advisory locks de Postgres (ADR-008).

Arquitectura vigente: puertos (Protocols) en el domain de cada módulo, adapters en su
infrastructure; import-linter (`backend/.importlinter`) fija que domain no importa frameworks y
los cruces entre módulos permitidos; `shared/` es importable por todos. ADRs en `docs/adr/`.

[OBJETIVO]

FASE 0 — INVENTARIO Y MEDICIÓN (antes de mover una línea):
  1. Confirmar el inventario del [CONTEXTO] con grep (pyodbc/zeep/httpx por módulo y capa) y
     volcarlo a `docs/INTEGRACIONES_EXTERNAS.md`: por cada sistema externo → qué módulos lo usan,
     por qué puerto/adapter, desde qué endpoints/jobs, con qué timeout, qué política de retry y
     cómo degrada sin config (fail-fast 502 vs `_or_none`). Este doc es un entregable en sí: es el
     mapa que hoy no existe.
  2. Medir el problema del WSDL por request en liquidaciones: loguear/cronometrar cuánto tarda la
     primera llamada de un `ZeepCdLiquidacionesGateway` recién creado vs una repetida (en dev,
     contra el WSDL real, SOLO operaciones de lectura tipo `getTopLiquidations`).
  3. Investigar thread-safety del cliente zeep compartido: zeep usa un `requests.Session` en el
     Transport y `requests.Session` NO está documentado como thread-safe. Determinar si con el
     patrón actual (`asyncio.to_thread` concurrente sobre un singleton) pueden pisarse dos
     llamadas, leyendo doc/código de zeep y requests — no adivinando. Salida: decisión escrita
     entre (a) lock por llamada (serializa), (b) Session/Transport por llamada con el documento
     WSDL parseado cacheado y compartido, (c) pool acotado de clientes. Elegir la más simple que
     elimine el riesgo sin degradar el poller.
  4. Decidir y documentar el tope de concurrencia hacia MERCURIO (semáforo de proceso,
     configurable por env, default propuesto: 3 consultas simultáneas) — suficiente para que
     Inicio + jobs no se apilen, sin serializar todo.
  Validar las 4 salidas con el usuario antes de la Fase 1.

FASE 1 — CAPA COMPARTIDA SIGES (`shared/infrastructure/mercurio/`, junto a `connection.py`):
  - `query_runner.py`: una pieza única (ej. `MercurioQueryRunner`) que encapsula TODO el esqueleto
    duplicado: connection string, conexión efímera por consulta, timeout de login y de consulta,
    `asyncio.to_thread`, semáforo de concurrencia (Fase 0.4), `pyodbc.Error` →
    `ExternalServiceError` con log contextualizado (§6). API sugerida:
    `async def fetch_all(sql: str, params: Sequence, *, timeout_override: float | None) -> list[Row]`.
  - `factories.py`: helper único `require_mercurio_runner()` (fail-fast con el mensaje "falta
    SLA_MERCURIO_HOST" actual) + `mercurio_runner_or_none()` (degradación con warning) — las dos
    semánticas que hoy existen, definidas UNA vez.
  - Migrar los 6 gateways a adapters finos: cada uno conserva su SQL (`query.py`), su row mapping
    y su puerto de domain — solo delega la plomería en el runner. Los puertos de domain NO se
    tocan; los use cases NO se enteran del cambio.
  - Respetar los casos especiales tal cual: timeout 120 s + cache TTL de equipos-sin-real,
    variantes `_or_none` exactamente donde hoy existen (ni una más ni una menos).
  - Corregir la inconsistencia de liquidaciones: su factory pasa a usar el helper compartido
    (gana el chequeo de host y el singleton que hoy no tiene).
  - Settings: NO renombrar `sla_mercurio_*` en `.env` (integración verificada en producción —
    razón documentada en `connection.py`). Opcional recomendado: aceptar TAMBIÉN los nombres
    `MERCURIO_*` vía `AliasChoices` de pydantic-settings, documentando en `.env.example` que los
    dos funcionan y que `SLA_MERCURIO_*` es el nombre histórico. Si esto genera cualquier duda,
    dejarlo afuera y solo documentar.

FASE 2 — CAPA COMPARTIDA wsAyC (`shared/infrastructure/wsayc/`):
  - `client_provider.py`: UNA fuente del cliente zeep para toda la app — WSDL cargado y parseado
    una sola vez por proceso, endpoint fijado, transporte sin reintentos (dejar el comentario de
    negocio: reintentar duplica pedidos reales), timeout 30 s, y la estrategia de concurrencia
    elegida en Fase 0.3 implementada acá (no en cada módulo).
  - Constantes `WSDL_URL`/`REAL_ENDPOINT`/timeout salen de settings nuevas
    (`WSAYC_WSDL_URL`, `WSAYC_ENDPOINT`, `WSAYC_TIMEOUT_SECONDS`) con defaults = valores actuales
    hardcodeados, agregadas a `.env.example`. Comportamiento idéntico sin tocar ningún `.env`.
  - `ZeepWsAycGateway` (insumos) y `ZeepCdLiquidacionesGateway` (liquidaciones) conservan sus
    métodos, su parsing y sus puertos — solo reemplazan su `_service()` propio por el provider
    compartido. El manejo de errores por método NO cambia (hay métodos que degradan a lista vacía
    con warning y métodos que dejan propagar a propósito — conservar cada uno tal cual).
  - Liquidaciones pasa a singleton de proceso (`lru_cache` en sus dependencies), igual que
    insumos — se acaba el WSDL por request.

FASE 3 — CANDADOS PARA QUE NO VUELVA EL ESPAGUETI:
  - Contratos nuevos en `backend/.importlinter`:
    · `pyodbc` y `zeep` prohibidos en `src.modules.*.domain`, `src.modules.*.application` y
      `src.modules.*.presentation` — solo `infrastructure` (y `shared.infrastructure`) pueden
      importarlos. Verificar contra el estado real antes de fijarlo: si algo ya los importa fuera
      de infrastructure, ese es un hallazgo a corregir, no a excepcionar.
  - ADR nuevo en `docs/adr/` (numeración siguiente a la última existente): "Acceso compartido a
    integraciones externas (MERCURIO / wsAyC)" — qué se centraliza (plomería), qué NO se
    centraliza (puertos y parsing por módulo, que son negocio), la política de concurrencia
    elegida y por qué NO se renombraron las env vars.
  - `docs/INTEGRACIONES_EXTERNAS.md` (Fase 0) actualizado al estado post-refactor.
  - El patrón queda listo para el resto (Insight/SDS/ERS/Gestión web) pero NO se migran en esta
    pasada — alcance acotado a Siges + wsAyC.

VERIFICACIÓN (parte del entregable, no opcional):
  - Verde dentro del contenedor del backend: `uv run lint-imports` (incluidos los contratos
    nuevos), `uv run ruff check src tests`, `uv run mypy src`, `uv run pytest tests/unit -q`. Los
    tests existentes de gateways/parsing tienen que pasar SIN modificarse (si un test hay que
    tocarlo, explicar por qué — es señal de cambio de contrato).
  - Smoke de lectura real en dev, módulo por módulo, comparando ANTES vs DESPUÉS del refactor la
    misma operación: sla resumen del período actual, prestadores conteo de parque, contadores
    catálogo de operadores, liquidaciones propuesta de vínculos (Siges) y `getTopLiquidations`
    (wsAyC). Mismos números antes y después = refactor neutro. SOLO lecturas.
  - Concurrencia: reproducir N requests simultáneos que crucen MERCURIO y wsAyC (script simple o
    curl en paralelo) y verificar que el semáforo/estrategia elegida no genera deadlock ni
    timeouts nuevos, y que el poller de insumos sigue ciclando (con jobs deshabilitados, el ciclo
    se prueba con el endpoint manual equivalente, no reactivando los jobs).
  - Frontend intacto: `tsc` + `eslint` (no debería haber ni un archivo tocado del frontend; si lo
    hay, justificarlo).

[FORMATO]
- Todo texto al usuario en español de Argentina, directo, sin cortesías (regla de CLAUDE.md).
- Commits atómicos en inglés, convención del historial (`refactor(shared): ...`,
  `refactor(liquidaciones): ...`) — una fase por commit como mínimo; el fix del WSDL por request
  de liquidaciones puede ir como commit propio (es un fix medible, no solo orden).
- ADR con el formato de los existentes en `docs/adr/`.
- Al cierre: resumen con los comandos exactos corridos y su salida real (no "debería andar"),
  incluido el antes/después de la medición del WSDL y las paridades de smoke.

[RESTRICCIONES]
Operativas (innegociables, de CLAUDE.md):
- `DISABLE_BACKGROUND_JOBS=true` aplicado DE VERDAD antes de tocar nada que ejecuten los jobs
  (los gateways que se refactorizan acá son exactamente lo que los jobs usan):
  `docker compose up -d --force-recreate backend` + `docker exec helpdesk-manager-backend printenv
  DISABLE_BACKGROUND_JOBS` → "true", y el log de arranque sin `background_jobs: N job(s)
  iniciados`. `docker restart` NO relee `.env`. El incidente 2026-08-12 (mail real) salió de esto.
- PROHIBIDO disparar escrituras reales para probar: nada de `persistNewSupply`,
  `persistNewIncident`, cambios de estado de liquidaciones ni ninguna operación SOAP de
  escritura. Las pruebas wsAyC son SOLO de lectura (`getTopLiquidations`, `getMachineBySerial`).
  Siges/MERCURIO es solo lectura por cuenta (SiGesReadOnly) — únicamente SELECT igualmente.
- Sin hot reload: tras editar backend `docker restart helpdesk-manager-backend`. Verificar con
  curl antes de dar por servido un cambio. No dejar contenedores apagados al terminar.

De arquitectura (ARCHITECTURE_GUIDE.md):
- Los PUERTOS se quedan en el domain de cada módulo y el parsing/SQL en su infrastructure — lo
  compartido es SOLO plomería en `shared/infrastructure/`. NO crear un "módulo integraciones" ni
  mover lógica de negocio a shared.
- No tocar ni un carácter de los SQL de `query.py` ni del parsing SOAP: la paridad con las
  planillas/legacy depende de ellos (advertencia explícita en el docstring de sla).
- Ningún `except Exception` silencioso (§6); tamaños §4 (archivo ≤300, clase ≤200, función ≤20);
  dependencias hacia adentro y contratos de import-linter en verde.
- `lru_cache` y tests: si las factories cacheadas interfieren entre tests, limpiar con
  `cache_clear()` en fixtures — no quitar el cache de producción para que pasen los tests.

De alcance:
- Conductual-neutro: mismos timeouts por gateway, misma semántica de degradación (`_or_none` donde
  está hoy), misma política de no-retry, mismos mensajes de error visibles. Lo ÚNICO que puede
  cambiar observablemente: liquidaciones deja de recargar el WSDL por request, liquidaciones gana
  el 502 claro sin MERCURIO configurado, y las consultas concurrentes quedan acotadas.
- Insight/SDS/ERS/Gestión web/SMTP: inventariar sí, migrar no.

[EJEMPLO]
Nota de cierre esperada:

  Integraciones externas ordenadas — cerrado y verificado (refactor neutro):
  - Fase 0: inventario en docs/INTEGRACIONES_EXTERNAS.md (7 sistemas, 6 gateways pyodbc + 2 zeep);
    WSDL por request medido: primera llamada <X> s vs <Y> ms cacheado; decisión concurrencia zeep:
    <a/b/c> con evidencia; semáforo MERCURIO = 3 (env MERCURIO_MAX_CONCURRENT).
  - Fase 1: MercurioQueryRunner + factories compartidas; 6 gateways migrados a adapters finos;
    liquidaciones con chequeo de host y singleton (antes: gateway nuevo por request sin chequeo).
  - Fase 2: provider zeep compartido (1 carga de WSDL por proceso), constantes a settings con
    defaults idénticos; liquidaciones singleton.
  - Fase 3: contratos import-linter pyodbc/zeep solo-infrastructure; ADR-0NN.
  - lint-imports · ruff · mypy · pytest unit — en verde, tests existentes sin modificar.
  - Smoke antes/después: sla <n>/<n> · prestadores <n>/<n> · contadores <n>/<n> · liquidaciones
    <n>/<n> — idénticos. 10 requests concurrentes MERCURIO+wsAyC sin deadlock ni timeout nuevo.
  - Jobs de fondo deshabilitados durante todo el trabajo; cero escrituras SOAP.
```

---

## Notas de contexto para quien use este prompt (fuera del prompt en sí)

- **El espagueti es real pero acotado**: la duplicación no es caos — los 6 gateways pyodbc copian
  conscientemente el mismo patrón bueno (conexión efímera, to_thread, error envuelto). El problema
  es que está copiado 6 veces con 2 desviaciones reales (liquidaciones sin chequeo de host ni
  singleton en Siges, y gateway wsAyC nuevo por request). Consolidar baja el costo de cada módulo
  futuro (el de STC, por ejemplo) a "SQL + mapping" y elimina las desviaciones por construcción.
- **Los dos hallazgos con impacto medible** están en liquidaciones: (1) re-descarga del WSDL de
  wsAyC en cada request que use SOAP, y (2) sin MERCURIO configurado falla críptico en vez del 502
  claro. Se arreglan solos al pasar por la capa compartida.
- **"Que no se pisen consultas" tiene dos caras**: hacia MERCURIO hoy nada se pisa (cada consulta
  abre su conexión) pero tampoco hay tope — pueden apilarse consultas de 40 s; el semáforo lo
  resuelve. Hacia wsAyC el riesgo es distinto: un `requests.Session` compartido entre threads
  concurrentes no está garantizado como seguro — por eso la Fase 0.3 lo investiga con doc/código
  en mano en vez de asumir para cualquiera de los dos lados.
- **Por qué NO renombrar `SLA_MERCURIO_*`**: el docstring de `connection.py` documenta que se dejó
  así a propósito para no tocar una integración verificada en producción. El prompt ofrece el
  camino intermedio (aliases que aceptan ambos nombres) como opcional, y explícitamente permite
  descartarlo si genera dudas.
- **Por qué los puertos NO se centralizan**: `WsAycGateway` (insumos) y `CdLiquidacionesGateway`
  (liquidaciones) son contratos de negocio distintos sobre el mismo endpoint físico — cada módulo
  necesita métodos, parsing y semántica de error propios. Centralizar eso crearía acoplamiento
  entre módulos (lo que import-linter prohíbe); centralizar solo el cliente/transporte no.
- **Riesgo principal del refactor**: tocar sin querer la semántica de error de algún método SOAP
  (hay métodos que degradan a `[]` con warning y otros que propagan a propósito — ver
  `get_machine_by_serial`, que NO tiene try/except deliberadamente). Por eso la restricción de
  "tests existentes sin modificar" y el smoke antes/después: son la red de seguridad de la
  neutralidad.
- **Extensión futura natural** (fuera de este alcance): migrar Insight/SDS/ERS/Gestión web al
  mismo patrón de provider compartido, y un healthcheck `/api/health/integraciones` que reporte
  el estado de cada sistema externo desde el inventario. Dejarlo anotado en el ADR como "siguiente
  paso posible", no hacerlo ahora.
