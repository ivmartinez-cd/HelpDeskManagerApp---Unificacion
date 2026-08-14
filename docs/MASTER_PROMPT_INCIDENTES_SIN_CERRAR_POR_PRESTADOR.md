# Master Prompt — Card de "Incidentes finalizados sin cerrar" por prestador (Inicio + módulo STC)

Agregar a la pantalla de Inicio (`/`, `app/(app)/page.tsx`) una tarjeta que muestre, **por prestador
(PST)**, la cantidad de incidentes que están **finalizados pero todavía no cerrados** en Siges. El
superadmin ve todos los PST; cada usuario logueado ve solo los PST que tiene asignados (más los que
cubre por override temporal). El detalle listado va en el módulo **STC** (`stc`), hoy vacío y con
entrada de catálogo ya sembrada pero deshabilitada.

Generado el 2026-08-14 a partir del análisis del código real del repo. Las piezas de arquitectura están
verificadas contra el código; **la definición exacta de "finalizado sin cerrar" en el esquema de Siges
NO está documentada en el repo y es la primera tarea del prompt** (Fase 0) — no asumirla.

---

```text
[ROL]
Actuá como arquitecto/desarrollador senior full-stack del monorepo HelpDeskManagerApp---Unificacion
(FastAPI + SQLAlchemy async + Alembic + Next.js App Router, arquitectura módulo→capa
domain/application/infrastructure/presentation). Conocés y aplicás ARCHITECTURE_GUIDE.md y CLAUDE.md
del repo como reglas obligatorias. Respondés en español de Argentina, directo y sin relleno. Cero
alucinaciones: si un dato de Siges no está confirmado, lo confirmás contra la base antes de construir
encima, y si no se puede confirmar, lo decís explícitamente en vez de inventarlo.

[CONTEXTO]
Piezas reales verificadas contra el código (no supuestas):

- Fuente de datos: Siges/MERCURIO (SQL Server, solo lectura). Patrón de acceso ya productivo:
  `build_mercurio_connection_string` (`shared/infrastructure/mercurio/connection.py`) +
  `PyodbcSlaQueryGateway` (`modules/sla/infrastructure/mercurio/pyodbc_sla_query_gateway.py`):
  conexión efímera por consulta, `asyncio.to_thread` (pyodbc es síncrono), SQL 100% parametrizado con
  `?`, `pyodbc.Error` envuelto en `ExternalServiceError`. Catálogo de tablas conocidas en
  `docs/siges/SIGES_READONLY_CATALOGO_DATOS.md`.
- Incidentes: `dbo.Incidente` + `dbo.Estado_Incidente` (`EI.Descripcion` = estado),
  `dbo.Tipo_Incidente` (el módulo sla filtra a `IN (101, 108)`), `dbo.Empresa` (E=cliente,
  E1=técnico/PST vía `I.ID_Tecnico`), `dbo.Sucursal`, `dbo.Maquina`→`Articulo`→`ArtGen` (modelo).
  Existen además `dbo.Estado_Incidente_ST_Correlatividad`, `dbo.MotivoFinalizacion` y la vista
  `dbo.VW_InformeIncidenteST`, todavía sin explorar en este repo.
- Vínculo PST↔operador: tabla local `prestador` (`prestadores/infrastructure/models/prestador_models.py`)
  con `siges_empresa_id` (= `ID_Empresa`/`ID_Tecnico` de Siges) y `operador_id` (FK a `app_user.id`).
  La resolución de "mis PST" incluyendo coberturas temporales (ADR-013) ya existe:
  `sla/infrastructure/repositories/sqlalchemy_prestador_lookup.py` implementando el Protocol
  `sla/domain/repositories/prestador_lookup.py` — devuelve `list[int]` de `siges_empresa_id`.
  Es un adapter cruzado legal **solo desde infrastructure/presentation** (contrato de import-linter
  `sla-domain-app-independent-from-prestadores` en `backend/.importlinter`).
- Identidad y permisos: `Identity` (`auth/application/dtos/results.py`) trae `user.id`,
  `user.is_superadmin`; `require_permission(Permission(ModuleKey("stc"), ActionKey("view")))`
  (`auth/presentation/dependencies/permissions.py`). El superadmin pasa todos los gates sin grants
  explícitos (ver `ListVisibleModules`).
- Módulo `stc`: `backend/src/modules/stc/` existe VACÍO (solo README). El catálogo ya lo tiene sembrado
  en la migración `4c741806341e_seed_catalog.py`: `("stc", "STC", "/stc", "activity", 50, False)` con
  acciones `view` y `export` — o sea, falta activarlo (`is_enabled=True`) con una migración propia,
  patrón `ac5e139e28b4_activate_sla_module.py`.
- Home: `app/(app)/page.tsx` renderiza una grilla de cards (`ShiftDashboardCard`, `TodayClientsCard`,
  `SlaSummaryCard`). Cada card es `"use client"`, vive en `features/<x>/components/`, se gatea con
  `useSession().modules.some(m => m.key === "<módulo>")` (no con `can()`: el superadmin no tiene grants
  explícitos), y usa el lenguaje visual `rounded-[12px] border border-border bg-card p-5` + tokens de
  marca (`brand-orange`), dark-aware. HTTP: `services/http-client.ts`.
- Costo de la consulta a MERCURIO: la del módulo sla tarda ~40 s, por eso `sla` NO consulta en vivo:
  persiste un snapshot (`sla_periodo_snapshot`) refrescado por un job de fondo
  (`sla/presentation/background_jobs.py`, `SLA_REFRESH_INTERVAL_MINUTES`) y las lecturas van al cache.
- Backend sin hot reload, jobs de fondo con efectos reales (mails a gente real) — ver [RESTRICCIONES].

[OBJETIVO]

FASE 0 — INVESTIGACIÓN (obligatoria, antes de escribir una línea de feature):
El repo NO documenta qué valores toma `Estado_Incidente` ni cómo se distingue "finalizado" de
"cerrado". Averiguarlo con dato real, con un script de exploración nuevo en `backend/scripts/`
(patrón de `explore_siges_parque_pst.py`: pyodbc, cuenta `SiGesReadOnly`, `autocommit=True`,
`close()` en `finally`, solo SELECT):
  1. `SELECT Id, Descripcion FROM dbo.Estado_Incidente ORDER BY Id` — catálogo completo.
  2. Conteo de incidentes vivos por estado (últimos ~12 meses) para ver cuáles son terminales y cuál
     es el limbo "finalizado, falta cerrar".
  3. Columnas reales de `dbo.Incidente` vía `INFORMATION_SCHEMA.COLUMNS` — buscar fechas de
     finalización/cierre y cualquier flag de cierre.
  4. Revisar `dbo.Estado_Incidente_ST_Correlatividad`, `dbo.MotivoFinalizacion` y
     `dbo.VW_InformeIncidenteST` — pueden definir el flujo de estados y ahorrar la consulta a mano.
  5. Confirmar el criterio de "vigente": `Empresa.Estado`/`Sucursal.Estado` están INVERTIDOS
     (0=activo, 1=inactivo), ya documentado.
Salida de la fase: la **definición operativa escrita** de "incidente finalizado sin cerrar"
(qué `ID_Estado_Incidente`, qué filtro de tipo, con qué antigüedad si aplica), validada con el usuario
antes de seguir, y agregada a `docs/siges/SIGES_READONLY_CATALOGO_DATOS.md` §3 como [CONFIRMADA].
Decisiones a confirmar en esa misma ronda (proponer default, no decidir en silencio):
  - ¿Se filtra por `Tipo_Incidente IN (101, 108)` como en sla, o entran todos los tipos? Default
    propuesto: mismo filtro que sla, para que los números sean comparables con la pantalla de SLA.
  - ¿El backlog es histórico completo o con corte (ej. últimos 24 meses)? Default: corte configurable
    por env, arrancando en 24 meses, para acotar el costo de la consulta.
  - ¿Se cuentan también los PST inactivos (`prestador.is_active=false`)? Default: no.
NO construir la feature sobre un criterio supuesto: si la exploración no puede correr (sin acceso a
MERCURIO desde el entorno), decirlo y frenar ahí, no inventar el filtro.

FASE 1 — BACKEND (módulo `stc`, módulo→capa, espejando la estructura de `sla`):
  - domain: entidad `IncidenteSinCerrar` (id_incidente, fecha_ingreso, tipo, estado, cliente, sucursal,
    nro_serie, modelo, prestador/técnico, id_tecnico, fecha_finalizacion si existe, días en ese estado)
    + entidad de agregado `PrestadorSinCerrar` (id_tecnico, prestador, cantidad) + Protocols
    `StcQueryGateway` (find_incidentes_sin_cerrar) y `StcSnapshotRepository` (get/save).
    `well_known_permissions.py` con `VIEW = Permission(ModuleKey("stc"), ActionKey("view"))`.
  - application: use cases `GetIncidentesSinCerrarResumen` (conteo por prestador) y
    `ListIncidentesSinCerrar` (detalle), ambos con filtro opcional `siges_ids_filtro: list[int] | None`,
    + `RefreshStcSnapshot`. DTOs propios, sin pydantic en domain/application.
  - infrastructure: `mercurio/query.py` con el SQL parametrizado (comentado, sin interpolación),
    `mercurio/row_mapping.py` (acceso por nombre de columna, no posicional), `PyodbcStcQueryGateway`,
    modelo + repo del snapshot, migración Alembic reversible para la tabla del snapshot.
  - presentation: `stc_router.py` con
      GET  /api/stc/incidentes-sin-cerrar/resumen   → conteo por prestador (Page[...] o objeto de
           resumen con lista acotada; si devuelve colección va paginado, §11)
      GET  /api/stc/incidentes-sin-cerrar           → Page[IncidenteSinCerrarSchema], filtros
           `prestadorId`/`operadorId`/`todos`, `page`/`size` con tope explícito
      POST /api/stc/actualizar                      → refresh a demanda (permiso `stc.update` o
           `stc.export` ya existente; si hace falta una acción nueva, sembrarla por migración)
    Todos con `require_permission(VIEW)`.
  - Visibilidad (regla de negocio central): el filtro por PST se resuelve SIEMPRE en el backend a
    partir de la identidad de sesión, nunca de un parámetro que mande el cliente sin control.
    Reusar la semántica de `SqlAlchemyPrestadorLookup` de sla (propios no cubiertos + los que cubro por
    override vigente). Elegir UNA opción y justificarla en 1 línea:
      (a) adapter propio `stc/infrastructure/repositories/sqlalchemy_prestador_lookup.py` con su Protocol
          en `stc/domain/repositories/` — duplica ~40 líneas pero es el patrón ya establecido
          [RECOMENDADO], o
      (b) extraer el lookup a un lugar compartido — requiere ADR en `backend/docs/adr/` explicando por
          qué no viola la independencia entre módulos.
    Agregar a `backend/.importlinter` los contratos `stc-domain-no-frameworks`,
    `stc-domain-app-independent-from-auth` y `stc-domain-app-independent-from-prestadores`, con el
    mismo texto que los de sla.
  - Cache: la card de Inicio NO puede pegarle a MERCURIO en cada carga. Snapshot persistido +
    `stc/presentation/background_jobs.py` con `STC_REFRESH_INTERVAL_MINUTES` (env nueva, documentada en
    `.env.example`), registrado igual que el de sla y respetando `DISABLE_BACKGROUND_JOBS`. El endpoint
    lee el snapshot; cold start consulta en vivo una vez (mismo criterio que `GetSlaCompliance`).
    Exponer `updated_at` en la respuesta y mostrarlo en la card ("actualizado hace X").
  - Registrar el router en `shared/presentation/app.py`.

FASE 2 — FRONTEND:
  - `features/stc/api/stc-api.ts`, `features/stc/types/stc.ts`.
  - `features/stc/components/incidentes-sin-cerrar-card.tsx` (`"use client"`): card de Inicio con el
    conteo total y el desglose por prestador (lista scrolleable, badge con la cantidad), estado de
    carga/error, sello de frescura del snapshot, y botón "Ver detalle" que linkea a `/stc`. Gate:
    `modules.some(m => m.key === "stc")`. Mismo lenguaje visual que `TodayClientsCard`/`SlaSummaryCard`.
  - Montarla en la grilla de `app/(app)/page.tsx`.
  - `app/(app)/stc/page.tsx` + vista de detalle en `features/stc/components/`: tabla paginada de los
    incidentes finalizados sin cerrar, agrupada/filtrable por prestador, con la misma regla de
    visibilidad (el backend ya la impone; el frontend no debe "abrir" nada por su cuenta). Es la
    primera pantalla del módulo STC: mínima pero funcional, no un placeholder.

FASE 3 — ACTIVACIÓN Y VERIFICACIÓN:
  - Migración `activate_stc_module` (`is_enabled=True`, reversible), aplicada DESPUÉS de que `/stc`
    exista y responda — activar el módulo lo hace aparecer en el sidebar del superadmin.
  - Verde dentro del contenedor del backend: `uv run lint-imports`, `uv run ruff check src tests`,
    `uv run mypy src`, `uv run pytest tests/unit -q`. Frontend: `tsc` + `eslint` (+ e2e Playwright si el
    módulo mantiene esa cobertura).
  - E2E real en el navegador: con superadmin se ven todos los PST; con un usuario operador que tenga
    PST asignados se ven solo los suyos; con un usuario sin PST asignados, el comportamiento acordado
    (default propuesto: ve todo, mismo criterio que `list_incidentes_vencidos`, o card vacía — decidir y
    documentar). Verificar también que un `prestadorId` de un PST ajeno no devuelva datos si el usuario
    no tiene visibilidad sobre él.
  - Paridad contra la realidad: elegir al menos 1 PST y contrastar el conteo contra Gestión
    (`gestion.cdsa.com.ar`) o el reporte legacy equivalente. Si no coincide, el criterio de la Fase 0
    está mal — corregirlo antes de dar la feature por terminada, no maquillar el número.

[FORMATO]
- Todo texto al usuario en español de Argentina, directo, sin cortesías (regla de CLAUDE.md).
- Commits atómicos en inglés con la convención del historial (`feat(stc): ...`).
- Migraciones Alembic reversibles (up y down), §9 de la guía + ADR-002.
- Documentar en `docs/siges/SIGES_READONLY_CATALOGO_DATOS.md` lo confirmado en la Fase 0, y crear
  `docs/stc/STC_INCIDENTES_SIN_CERRAR.md` con la definición operativa, el SQL final y las decisiones
  tomadas (filtro de tipo, corte temporal, visibilidad).
- ADR corto en `backend/docs/adr/` solo si se desvía del texto de la guía (ej. opción (b) del lookup).
- Al cierre: resumen de lo verificado con los comandos exactos corridos y su resultado real (no
  "debería andar"), incluida la verificación de visibilidad por usuario y la paridad de conteo.

[RESTRICCIONES]
Operativas (innegociables, de CLAUDE.md):
- `DISABLE_BACKGROUND_JOBS=true` aplicado de verdad antes de tocar o dejar correr cualquier código de
  jobs de fondo (`docker compose up -d --force-recreate backend`, verificado con
  `docker exec helpdesk-manager-backend printenv DISABLE_BACKGROUND_JOBS` y con el log de arranque —
  `docker restart` NO relee `.env`). El incidente del 2026-08-12 (mail real a Canal Directo) salió
  justamente de editar jobs en vivo.
- Sin hot reload: tras editar backend `docker restart helpdesk-manager-backend`; tras editar frontend
  `docker restart helpdesk-manager-frontend` (re-corre `next build`, tarda). Verificar con
  `curl -s http://localhost:3000/<ruta> | grep <algo nuevo>` antes de dar por servido un cambio.
  No dejar los contenedores apagados al terminar.
- Siges/MERCURIO es SOLO LECTURA: únicamente SELECT, con la cuenta `SiGesReadOnly`. Ningún INSERT/
  UPDATE/DELETE, ninguna llamada a wsAyC/SOAP que escriba. La DB local de dev tiene datos reales de
  producción: no dispararle nada a destinatarios reales.

De arquitectura (ARCHITECTURE_GUIDE.md):
- Dependencias hacia adentro (Presentation→Application→Domain←Infrastructure). `stc.domain` y
  `stc.application` no importan `auth` ni `prestadores` ni frameworks; el cruce a prestadores solo desde
  infrastructure/presentation, con contrato de import-linter que lo fije.
- Toda lectura de negocio pasa por el use case; prohibido router→repo/gateway directo.
- SQL parametrizado con `?`, nunca interpolación de strings (§8), ni siquiera para la lista de
  `siges_empresa_id` (armar placeholders dinámicos o filtrar en memoria si la lista es chica).
- Paginación §11 con el envelope `Page[T]` de `shared/presentation/schemas/pagination.py` para toda
  respuesta de colección, con tope de `size` explícito.
- Ningún `except Exception` silencioso (§6): loguear con contexto (`extra={...}`, `exc_info=exc`) o
  dejar propagar / envolver en `ExternalServiceError`.
- Tamaños §4: archivo ≤300 líneas, clase ≤200, función ≤20 — partir en el momento, no después.
- Frontend: cuidado con `react-hooks/set-state-in-effect` (ya mordió en este repo) — nada de setState
  síncrono en efectos ni en catch alcanzable desde un efecto; usar promise-chain como en
  `TodayClientsCard`.

De negocio:
- "Sin cerrar" = finalizado y pendiente de cierre, según la definición confirmada en la Fase 0. NO
  incluir incidentes abiertos/en curso ni ya cerrados. Si el estado no permite distinguirlo con
  certeza, decirlo y frenar antes de mostrar un número inventado.
- El agrupador es el PRESTADOR (`I.ID_Tecnico` → `Empresa.ID_Empresa` → `prestador.siges_empresa_id`),
  no el cliente ni el técnico individual. Incidentes cuyo `ID_Tecnico` no matchee ningún `prestador`
  local no se pueden atribuir: contarlos aparte como "sin prestador vinculado" y mostrarlos solo al
  superadmin, nunca repartirlos entre PST.
- Visibilidad: superadmin ve todos; el resto ve solo sus PST asignados + los que cubre por override
  vigente. El filtro se aplica en el backend a partir de la sesión; ningún parámetro del cliente puede
  ampliarlo.

[EJEMPLO]
Nota de cierre esperada:

  Incidentes finalizados sin cerrar por prestador — cerrado y verificado:
  - Fase 0: `Estado_Incidente` tiene N estados; "finalizado sin cerrar" = `ID_Estado_Incidente=<X>`
    (<Descripcion>), tipos (101,108), corte 24 meses — confirmado con <N> filas reales y documentado en
    SIGES_READONLY_CATALOGO_DATOS.md §3 y docs/stc/STC_INCIDENTES_SIN_CERRAR.md.
  - Backend módulo `stc`: entidad + 3 use cases, `PyodbcStcQueryGateway`, snapshot `stc_snapshot`
    (migración `xxxx` up/down aplicada), job de fondo cada `STC_REFRESH_INTERVAL_MINUTES`, router con
    `require_permission(stc.view)`; contratos de import-linter agregados.
  - Frontend: `incidentes-sin-cerrar-card.tsx` montada en Inicio + pantalla `/stc` con tabla paginada.
  - Migración `activate_stc_module` aplicada; módulo visible en el sidebar.
  - lint-imports · ruff · mypy · pytest unit (+N nuevos) · tsc · eslint — en verde (salidas pegadas).
  - E2E: superadmin ve <N> PST / <M> incidentes; el operador <mail> ve solo sus <K> PST; usuario sin PST
    → <comportamiento acordado>. Paridad: PST <nombre> = <n> incidentes en la app vs <n> en Gestión.
```

---

## Notas de contexto para quien use este prompt (fuera del prompt en sí)

- **Lo único no verificado es lo más importante**: el repo usa `Estado_Incidente` en la consulta de SLA
  (`EI.Descripcion AS Estado`) pero en ningún lado documenta qué valores toma. Sin ese catálogo, la
  feature entera es un número inventado. Por eso la Fase 0 es bloqueante y termina con validación del
  usuario, no con una suposición del agente.
- **Por qué no alcanza con reusar el snapshot de SLA**: `INCIDENTES_SLA_SQL` hace `INNER JOIN
  IncidenteTiempo` y filtra por período mensual (`YEAR*100+MONTH = ?`). Un backlog de "finalizados sin
  cerrar" es transversal a los períodos y puede incluir incidentes sin fila de tiempo. Hace falta
  consulta propia.
- **Por qué snapshot y no consulta en vivo**: la consulta de SLA contra MERCURIO tarda ~40 s (documentado
  en el job de fondo de sla). Una card de Inicio que consulte en vivo haría que Inicio tarde eso en
  cargar para todos los usuarios. El patrón snapshot + job ya está resuelto en el repo; copiarlo.
- **El módulo STC ya existe en el catálogo** (`4c741806341e_seed_catalog.py`: key `stc`, label `STC`,
  ruta `/stc`, ícono `activity`, orden 50, `is_enabled=False`, acciones `view`/`export`). No hace falta
  crear la entrada, solo activarla — y activarla recién cuando `/stc` responda, porque enciende el ítem
  del sidebar para el superadmin. Si se quiere que el sidebar diga "Servicio Técnico" en vez de "STC",
  hay que cambiar el `label` por migración (patrón `c7d1f92e4a68_rename_vacaciones_module_label.py`).
- **La regla de visibilidad ya está resuelta y probada en sla**: `SqlAlchemyPrestadorLookup` devuelve los
  `siges_empresa_id` propios (descontando los cubiertos por otro operador) más los que el usuario cubre
  por override vigente (ADR-013). Reusar esa semántica evita que la card de Inicio y la pantalla de SLA
  contradigan entre sí quién es "mi PST".
- **Decisión abierta que conviene cerrar antes de codear**: qué ve un usuario logueado sin ningún PST
  asignado. `list_incidentes_vencidos` en sla optó por "ve todo" (forzar una vista vacía no sirve de
  nada). Si acá se quiere lo contrario, hay que decirlo explícito, porque son dos criterios distintos en
  la misma app.
