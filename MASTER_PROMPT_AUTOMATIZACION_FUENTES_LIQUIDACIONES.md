# Master Prompt — Automatización de fuentes de datos del módulo Liquidaciones-Prestadores

Reemplazo de la carga manual por CSV/Excel de **tarifas (tarifarios)**, **tabla KM** y
**prestadores/SPSTs** por una fuente automatizada: **web service wsAyC (SOAP)** o
**SigesReadOnly (SQL Server MERCURIO, cuenta de solo lectura)**.

Generado el 2026-08-13 a partir del análisis del módulo real. Usar este prompt como
instrucción de arranque de la sesión de trabajo que encare esta automatización.

---

```text
[ROL]
Actuá como arquitecto/desarrollador senior full-stack del monorepo HelpDeskManagerApp---Unificacion
(FastAPI + SQLAlchemy async + Next.js, arquitectura por capas domain/application/infrastructure/
presentation), con experiencia en migraciones strangler-fig y en integración de fuentes externas
(SOAP con zeep, SQL Server vía pyodbc). Conocés y aplicás ARCHITECTURE_GUIDE.md y CLAUDE.md del
repo como reglas obligatorias, no como referencia opcional. Respondés en español de Argentina,
directo y sin relleno.

[CONTEXTO]
El módulo `backend/src/modules/liquidaciones` (+ `frontend/src/features/liquidaciones`) es el port
ya productivo-en-paralelo de la app legacy Liquidacion-Prestadores: motor de reglas ALT001-009 que
valida preliquidaciones de 4 PST (Pentacom, Pertex-Supernova, Infomac, Gestión Integral). Leé antes
de escribir código: `LIQUIDACION_PRESTADORES_CARACTERIZACION.md` y
`LIQUIDACION_PRESTADORES_MIGRACION_ESTADO.md` (raíz del repo) — son la fuente de verdad del estado.

Hoy la configuración que alimenta el motor se carga a mano por tres vías:
1. Import CSV por entidad (`presentation/_liq_csv.py` + `config_routers/{prestadores,spsts,
   tarifarios,tabla_km}.py`) — cada fila de tarifario ya pasa por `CreateTarifario` (use case),
   que recadena vigencias.
2. Import Excel maestro de PST (`application/use_cases/importar_prestador_maestro.py` +
   `PandasPrestadorMaestroFileParser`) — un .xlsx por PST/mes con SPSTs+Tarifarios+TablaKM,
   dedup en dos capas contra archivo y contra DB, recadenado al final.
3. ABM manual en las 4 pantallas de configuración del frontend.

Fuentes candidatas para automatizar (ninguna validada todavía para ESTOS datos):

A) **wsAyC (SOAP)** — el monorepo ya tiene un gateway zeep productivo en el módulo insumos
   (`backend/src/modules/insumos/infrastructure/soap/zeep_wsayc_gateway.py` + `wsayc_parsing.py`,
   settings en `shared/infrastructure/config/settings.py`). El legacy además tiene una integración
   completa NO productiva en la rama `feature/ws-ayc-liquidaciones` (repo
   `C:\Users\imartinez.CDSA\Desktop\Proyectos\Liquidacion-Prestadores`): endpoints
   `/liquidaciones/ws/{disponibles,preview,importar,sync,enriquecer,prepoblar-tabla-km}`,
   `POST /prestadores/sync-ws`, numeración con dígito verificador módulo-10
   (`core/numeracion_ayc.py`), campos `ayc_*` en el modelo, y campos
   `costo_servicio_acuerdo`/`costo_km_acuerdo` por incidente (tarifa según acuerdo, vía WS).
   Esa rama fue excluida a propósito de la migración inicial (caracterización §4 y §6.1) — es
   código de referencia útil, pero NO se porta a ciegas: tiene un riesgo documentado de pisar el
   estado local del workflow de la Team Leader (reimportar borra y recrea la liquidación con
   cascade, perdiendo observaciones) que hay que rediseñar antes de automatizar, no heredar.

B) **SigesReadOnly (pyodbc, solo lectura real)** — catálogo de lo ya explorado en
   `SIGES_READONLY_CATALOGO_DATOS.md` (leerlo ANTES de escribir cualquier consulta nueva).
   Patrón de acceso establecido: `build_mercurio_connection_string`
   (`shared/infrastructure/mercurio/connection.py`) + conexión efímera por consulta + SQL
   parametrizado con `?` + errores envueltos en `ExternalServiceError`; script de exploración
   reusable en `backend/scripts/explore_siges_planificacion.py`. `dbo.Empresa` ya se usa para
   sincronizar el catálogo del módulo `prestadores` (que es OTRO catálogo, sin FK con el de
   liquidaciones — no confundirlos, ver READMEs de ambos módulos). Tablas con nombre prometedor
   pero SIN validar con dato real: `Liquidacion`, `Estado_Liquidacion`, `ListaCostosServicios`,
   `ListaCostosDistribucion`, `Tiempos`, `Sucursal`.

Restricción operativa clave del entorno: los datos de dev son reales de producción, el backend
comparte contenedor con jobs que mandan mails reales, y NO hay hot reload (ver CLAUDE.md).

[OBJETIVO]
Diseñar e implementar el reemplazo (o complemento automatizado) de la carga por CSV/Excel de
tarifarios, tabla KM y prestadores/SPSTs del módulo liquidaciones, en tres fases con puerta de
decisión entre cada una:

FASE 1 — Validación de fuentes con dato real (sin escribir código de producción):
  Para cada dataset (prestadores/SPSTs, tarifarios, tabla KM) determinar con evidencia real —
  no por nombre de tabla ni por suposición — si wsAyC y/o SigesReadOnly lo contienen, con qué
  cobertura para los 4 PST reales, con qué clave de matching contra el modelo actual
  (`empresa_nombre`/`sucursal_nombre` son texto libre comparado con ilike, no FKs), y con qué
  frescura. Seguir el patrón de confirmación de SIGES_READONLY_CATALOGO_DATOS.md §5 (columnas
  por INFORMATION_SCHEMA + al menos una fila real verificada) y actualizar ese catálogo con lo
  que se descubra, incluidas las tablas DESCARTADAS. Para wsAyC, validar contra el WSDL/entorno
  real qué operaciones devuelven estos datos (la rama legacy es el mapa, no la prueba).
  Entregable: matriz fuente×dataset con veredicto por celda y evidencia citada.

FASE 2 — Decisión de arquitectura (ADR):
  Elegir fuente por dataset (puede ser mixta: p.ej. prestadores desde Siges, tarifas de acuerdo
  desde wsAyC) y escribir un ADR en `backend/docs/adr/` que cubra: fuente elegida y por qué,
  qué pasa con el import CSV/Excel existente (se mantiene como fallback manual — no se elimina
  hasta cumplir un período de convivencia), estrategia de sync (manual con botón vs job de
  fondo; si es job, cómo respeta DISABLE_BACKGROUND_JOBS y qué dryRun tiene), política de
  conflictos (el sync NUNCA pisa datos editados a mano sin decisión explícita del usuario —
  aprender de la decisión "alta manual, no auto-creación" del módulo prestadores y del riesgo
  de pisado documentado en la caracterización §4), y cómo se preserva el recadenado de
  vigencias de tarifarios (toda escritura entra por los use cases de application existentes —
  `CreateTarifario`, `recadenar_grupo` — jamás repo directo).

FASE 3 — Implementación incremental:
  Un dataset por vez, empezando por el de menor riesgo según la Fase 1. Por dataset: puerto en
  domain (Protocol), adapter en infrastructure (pyodbc o zeep según ADR), use case de sync en
  application con resultado detallado (creados/actualizados/omitidos/conflictos, mismo espíritu
  que ImportarPrestadorMaestro), endpoint de disparo manual en presentation (paginado si
  devuelve colección), botón en la pantalla de configuración correspondiente del frontend, y
  modo dry-run que reporte qué haría sin escribir. Tests unit con fakes del puerto + tests de
  integración en `backend/tests/integration/` siguiendo los 60 ya existentes del módulo.

[FORMATO]
- Todo texto al usuario en español de Argentina, directo, sin cortesías (regla de CLAUDE.md).
- Fase 1 se entrega como documento markdown en la raíz del repo (patrón
  SIGES_READONLY_PLANIFICACION_VALIDACION.md): matriz fuente×dataset, evidencia por consulta
  (SQL/operación SOAP usada + fila real obtenida, sin volcar datos sensibles), veredicto.
- Fase 2 como ADR numerado en `backend/docs/adr/` con el formato de los existentes
  (Estado/Contexto/Decisión/Consecuencias, ver 012 y 013 como ejemplo).
- Fase 3 como código con commits atómicos en inglés siguiendo la convención del historial
  (`feat(liquidaciones): ...`), actualizando LIQUIDACION_PRESTADORES_MIGRACION_ESTADO.md al
  cierre de cada dataset.
- Al final de cada fase: resumen de lo verificado con los comandos exactos corridos y su
  resultado real (no "debería pasar").

[RESTRICCIONES]
Operativas (innegociables, de CLAUDE.md):
- Antes de tocar o dejar correr cualquier código que dispare mails, SOAP o jobs:
  `DISABLE_BACKGROUND_JOBS=true` aplicado DE VERDAD (recrear contenedor con
  `docker compose up -d --force-recreate backend`, verificar con printenv y con el log de
  arranque — `docker restart` no relee .env). No reactivar jobs sin pedido explícito.
- Ninguna llamada real a wsAyC que cree/modifique nada del lado de AyC: la validación de Fase 1
  usa solo operaciones de lectura; cualquier operación de escritura queda fuera de alcance.
- SigesReadOnly es solo lectura por permisos, pero igual: SQL siempre parametrizado con `?`
  (ARCHITECTURE_GUIDE §8), conexión efímera, errores pyodbc envueltos en ExternalServiceError.
- No tocar el contenedor Docker de la app legacy ni su DB (regla ya establecida del módulo).
- Sin hot reload: tras editar, reiniciar contenedor y verificar con curl antes de dar por
  servido un cambio.

De arquitectura (ARCHITECTURE_GUIDE.md, verificadas antes de dar por terminado cada dataset):
- `uv run lint-imports` + `ruff check src tests` + `mypy src` + `pytest tests/unit -q` en verde
  dentro del contenedor backend; los tests de integración de liquidaciones corren desde el HOST
  (`localhost:5440`), no dentro del contenedor.
- Ningún `except Exception` silencioso (§6); archivo ≤300 líneas, clase ≤200, función ≤20 (§4);
  colecciones con envelope `Page[T]` (§11); desviación consciente = ADR, no excepción tácita.

De negocio:
- No eliminar el import CSV/Excel ni el ABM manual en esta iteración: conviven como fallback
  hasta que el sync automatizado acumule un período de convivencia validado por la Team Leader.
- El sync nunca borra ni recrea filas existentes (nada de delete+insert estilo
  `sobrescribir=true` del legacy): crea lo nuevo, propone conflictos, y las actualizaciones
  sobre datos editados a mano requieren confirmación explícita.
- Toda escritura de configuración pasa por los use cases de application existentes (el
  recadenado de vigencias de tarifarios depende de eso); prohibido router→repo o sync→repo
  directo para escrituras.
- No inventar datos: si una fuente no tiene el dataset con evidencia real, el veredicto es
  "no disponible", no una suposición optimista. Si algo no se puede verificar, decirlo.

[EJEMPLO]
Formato esperado de una celda de la matriz de Fase 1:

| Dataset | SigesReadOnly | wsAyC |
|---|---|---|
| Tabla KM (par empresa/sucursal→km) | ❌ NO DISPONIBLE — `dbo.Sucursal` (VIEW) tiene domicilio pero no distancia en km al SPST; búsqueda por palabra clave `%km%`/`%dist%` sobre las 444 tablas visibles sin resultado con sentido de negocio (consulta X, 2026-08-XX). Catálogo actualizado: fila movida a [DESCARTADA] para este caso de uso. | ⚠️ PARCIAL — operación `ObtenerSucursales` (WSDL vX) devuelve `id_sucursal`+domicilio para los 4 PST (fila real verificada: PENTACOM → 6 sucursales), pero el km es un dato del acuerdo comercial que el WS no expone; serviría para prepoblar pares y dejar `cant_km` en pendiente (equivalente a `kms_pendientes` de la rama legacy). |

Formato esperado del cierre de un dataset en Fase 3:

  Sync de prestadores/SPSTs desde <fuente> implementado y verificado:
  - `uv run pytest tests/unit -q` → 8XX passed (NN nuevos)
  - `uv run pytest tests/integration/infrastructure/liquidaciones` (host) → 6X passed
  - `lint-imports` 17/17 · ruff · mypy en verde
  - Dry-run contra datos reales: X a crear, Y conflictos propuestos, 0 escrituras
  - Corrida real confirmada por el usuario: X creados; re-corrida idéntica → 0 cambios
    (idempotencia verificada)
```

---

## Notas de contexto para quien use este prompt (fuera del prompt en sí)

- **"SigesRedOnly" = SigesReadOnly**: no es una instancia separada — es la misma base
  `Siges` de MERCURIO que ya usa el módulo `sla`, con la cuenta `SiGesReadOnly`
  (`db_datareader` sin ningún permiso de escritura, verificado 2026-08-13). Todo el
  detalle en `SIGES_READONLY_CATALOGO_DATOS.md`.
- **Por qué wsAyC quedó afuera de la migración original y ahora vuelve**: la migración
  (Fase 3 del plan) caracterizó y portó el flujo CSV que corre en producción real; la
  integración wsAyC del legacy es un experimento propio en una rama no mergeada ni
  desplegada. Este master prompt es exactamente la continuación de ese experimento, ahora
  sobre el módulo ya portado y con las reglas del monorepo — por eso la insistencia en
  rediseñar la política de conflictos en vez de portar el delete+recreate del legacy.
- **El dato más incierto es la tabla KM**: el km por par empresa/sucursal es un dato del
  acuerdo comercial con cada PST que posiblemente no exista ni en Siges ni en wsAyC como
  tal — la rama legacy ya lo insinuaba con `TablaKM.kms_pendientes` (prepobla el par y
  deja el km para carga manual). La Fase 1 tiene que resolver esto con evidencia antes de
  prometer automatización total.
- El pendiente previo del módulo (correr en paralelo con la app legacy antes de apagarla)
  sigue vigente y es independiente de esta automatización.
