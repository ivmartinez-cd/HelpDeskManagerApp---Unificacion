# ADR-018: Acceso compartido a integraciones externas (MERCURIO / wsAyC)

## Estado: Aceptado e implementado (2026-08-14)

## Contexto

Cuatro módulos consultan la base Siges del SQL Server MERCURIO (sla,
prestadores, contadores, liquidaciones) y dos consumen el SOAP wsAyC de Canal
Directo (insumos, liquidaciones). El acceso creció módulo a módulo copiando el
patrón del anterior, y el relevamiento (`docs/INTEGRACIONES_EXTERNAS.md`,
Fase 0 de este refactor) encontró:

- **6 gateways pyodbc** duplicando el mismo esqueleto (~30 líneas c/u):
  `asyncio.to_thread`, conexión efímera, timeouts de login y consulta,
  `pyodbc.Error` → `ExternalServiceError` con log. Las factories duplicaban
  además el chequeo "falta SLA_MERCURIO_HOST" — salvo liquidaciones, que no lo
  tenía: sin MERCURIO fallaba con el error críptico de pyodbc en vez del 502
  claro, y armaba un gateway nuevo por request.
- **Ningún tope de concurrencia** hacia MERCURIO: la consulta de sla puede
  tardar ~40 s y la de equipos-sin-real ~10 s; requests de usuarios + jobs de
  fondo podían apilarse sin cota, y el apilamiento era invisible.
- **2 gateways zeep** contra el MISMO endpoint/WSDL, con
  `WSDL_URL`/`REAL_ENDPOINT`/timeout 30 s hardcodeados y duplicados (única
  integración cuya config no salía de settings). Insumos usaba un singleton de
  proceso; liquidaciones instanciaba `ZeepCdLiquidacionesGateway()` nuevo
  dentro de cada `build_*` → **cada request re-descargaba y re-parseaba el
  WSDL**. Medido en dev contra el WSDL real (solo lecturas,
  `scripts/medir_wsdl_por_request.py`): primera llamada de un gateway recién
  creado mediana 1,239 s vs 0,930 s repetida → ~0,31 s de sobrecosto y una
  descarga extra contra wsg.cdsisa.com.ar por request. Un despilfarro de
  corrección (objeto descartado por request + tráfico innecesario) más que un
  problema dramático de performance — los números son estos y no más.
- **Thread-safety del singleton zeep** (verificado contra el código instalado,
  zeep 4.3.3 / requests 2.34.2, no supuesto): el `threading.Lock` de los
  gateways protegía solo la construcción del cliente; las llamadas
  concurrentes (poller de insumos + requests de usuarios) compartían un único
  `requests.Session` (`zeep/transports.py::Transport.post`).
  `requests.Session` no está documentado como thread-safe (ni FAQ ni Advanced
  Usage dan garantía alguna) y `Session.send` muta el cookie jar compartido en
  cada respuesta (`sessions.py:799`). El pooling de urllib3 sí es thread-safe
  y el jar tiene lock interno — no se esperaba corrupción, pero era estado
  mutable compartido sin contrato, contra un server PHP que puede setear
  cookies, con riesgo de romperse en upgrades.

## Decisión

### Qué se centraliza: SOLO plomería, en `shared/infrastructure/`

- **`shared/infrastructure/mercurio/query_runner.py`** (`MercurioQueryRunner`):
  thread, conexión efímera, timeouts, traducción de errores con log
  contextualizado (§6) y el semáforo de concurrencia. Factory única
  `require_mercurio_runner()` (`factories.py`): singleton de proceso con el
  chequeo de host definido una vez (`lru_cache` no cachea excepciones: sin
  config, cada request reintenta y da el 502 claro).
- **`shared/infrastructure/wsayc/client_provider.py`** (`WsAycClientProvider`):
  única fuente del cliente zeep — WSDL descargado y parseado una vez por
  proceso, endpoint fijado, transporte sin reintentos, timeout de settings.

### Qué NO se centraliza: los puertos y el negocio por módulo

Los puertos (Protocols) siguen en el domain de cada módulo; el SQL
(`query.py`), el mapeo de filas, el parsing SOAP y el manejo de errores por
método siguen en la infrastructure de cada módulo, sin tocar un carácter: la
paridad con planillas/legacy depende de ellos. Los gateways quedaron como
adapters finos que delegan la plomería. No existe un "módulo integraciones":
lo compartido es infraestructura pura, sin lógica de negocio.

Casos especiales preservados tal cual: timeout propio de 120 s y caché TTL de
600 s de equipos-sin-real (en su gateway, vía `timeout_override`); variantes
`_or_none` exactamente donde existían, con sus mensajes por consumidor (por
eso la semántica `_or_none` no se movió a la factory compartida: el warning
describe qué funcionalidad concreta degrada, y eso es del módulo).

### Concurrencia hacia MERCURIO: semáforo de proceso, default 3

`asyncio.Semaphore` dentro del runner compartido, configurable por
`MERCURIO_MAX_CONCURRENT` (default 3): suficiente para que Inicio + jobs no se
apilen sin serializar todo. La espera en el semáforo ocurre antes de abrir
conexión, así que no consume el timeout de login/consulta — encolar no genera
timeouts nuevos. Como encolar en silencio volvería invisibles los
apilamientos, el runner loguea un warning cuando una consulta espera más de
10 s, con el gateway en `extra`.

### Concurrencia hacia wsAyC: Document compartido + Session por llamada

De las tres alternativas evaluadas — (a) lock por llamada, (b) Document
parseado compartido + Transport/Session por llamada, (c) pool de clientes —
se eligió **(b)**:

- Es un camino de primera clase de zeep: `Client.__init__` acepta "Url/local
  WSDL location **or preparsed WSDL Document**".
- Costo medido igual al singleton (`scripts/medir_zeep_document_compartido.py`:
  mediana 0,998 s vs 1,024 s — domina la latencia del servidor; el handshake
  TLS por llamada es ruido), con el parseo del Document pagado una vez
  (0,197 s). (a) serializaba poller + usuarios detrás de llamadas de ~1 s;
  (c) era más complejidad para el mismo resultado.
- El Document se construye lazy bajo lock — el parseo tampoco tiene contrato
  de thread-safety — y los bindings se resuelven dentro del lock (warm-up) para
  que dos primeras llamadas concurrentes no los materialicen a la vez.

**Delta observable consciente** (el único, además de los fixes buscados): se
pierde la continuidad de cookies entre llamadas que el singleton de insumos
tenía de rebote. wsAyC no la necesita — liquidaciones ya operaba en producción
con cliente fresco por request — pero queda escrito acá como cambio decidido,
no silencioso.

La política de **no-retry es regla de negocio**, no configuración: toda
operación SOAP viaja como POST y reintentar `persistNewSupply` /
`persistNewIncident` duplica pedidos reales. El provider no monta reintentos y
el comentario vive en el código.

### Env vars: no se renombran

Las settings de MERCURIO siguen bajo `sla_mercurio_*` (`SLA_MERCURIO_*` en
`.env`): es una integración verificada en producción y el nombre histórico
está documentado en `connection.py` y `.env.example`. Se evaluó aceptar
también `MERCURIO_*` vía `AliasChoices` y se dejó afuera a propósito: el
beneficio es cosmético y el riesgo (dos nombres válidos para la misma
credencial, confusión en diagnóstico de entornos) no lo paga. Las settings
nuevas sí nacen sin prefijo de módulo: `MERCURIO_MAX_CONCURRENT`,
`WSAYC_WSDL_URL`, `WSAYC_ENDPOINT`, `WSAYC_TIMEOUT_SECONDS` (defaults = los
valores antes hardcodeados; ningún `.env` necesita cambios).

### Candado

Contrato nuevo de import-linter (`pyodbc-zeep-solo-infrastructure`): `pyodbc`
y `zeep` prohibidos como import directo en `domain`, `application` y
`presentation` de todo módulo (`allow_indirect_imports = True`: la cadena
transitiva presentation → infrastructure → shared → pyodbc es exactamente la
arquitectura). Verificado con prueba negativa: un `import pyodbc` en
presentation rompe el contrato.

## Consecuencias

- Liquidaciones gana el 502 claro sin MERCURIO configurado y deja de pagar
  WSDL por request; las consultas concurrentes a MERCURIO quedan acotadas y
  los apilamientos son visibles en el log. Todo lo demás es conductual-neutro
  (verificado con smoke de lectura antes/después por gateway, mismos números;
  el único delta fue equipos-sin-real 12085→12081 entre corridas porque en
  SIGES productivo estaban cargando contadores reales en ese momento — el SQL
  no tiene diff).
- El patrón queda listo para el resto de las integraciones (Insight, SDS, ERS,
  Gestión web, FTP, feriados) pero NO se migraron en esta pasada — alcance
  acotado a Siges + wsAyC.
- Los constructores de los gateways ahora reciben el runner/provider: los dos
  tests de errores de pyodbc y el test de wiring de sla se actualizaron a la
  firma nueva (mismas aserciones de comportamiento; el seam del chequeo de
  host se movió a `shared.infrastructure.mercurio.factories`).
