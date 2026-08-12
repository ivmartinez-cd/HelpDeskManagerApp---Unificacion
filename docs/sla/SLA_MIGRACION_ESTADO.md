# Módulo SLA — estado de la implementación

Última actualización: 2026-08-11. Origen funcional: `SLA.md` (query legacy de cumplimiento
contra la base `Siges` del SQL Server `MERCURIO`, reemplazo de la tabla dinámica de Excel).

Decisiones ya acordadas con el usuario (no re-preguntar):

- **Alcance**: card resumen en Inicio + pantalla de detalle propia en `/sla`.
- **Datos**: consulta **en vivo** a Siges vía pyodbc (sin caché/sync local en Postgres).
- **UI**: sin handoff — diseñar de cero respetando marca Institucional (#F7941D/#58595B) y
  los patrones ya existentes en la app (`KpiTile`, cards de Inicio, `StatsTable` de insumos).
  Mostrar un primer render al usuario para OK antes de pulir.
- El front solo expone **un selector de Período (AAAAMM)**; el backend deriva Desde/Hasta como
  primer/último día del mes (si algún día hace falta rango independiente, se agrega después).

## Backend — TERMINADO y verificado

`backend/src/modules/sla/` con la estructura módulo→capa estándar (ADR-003):

- **domain**: `entities/incidente_sla.py` (entidad de lectura, `es_vencido`, constantes
  `RESULTADO_*`), `value_objects/periodo.py` (VO AAAAMM, valida y deriva primer/último día),
  `repositories/sla_query_gateway.py` (puerto `Protocol`), `errors.py`
  (`PeriodoInvalidoError`), `well_known_permissions.py` (`VIEW` = sla/view).
- **application**: `use_cases/get_sla_compliance.py` (totales, % redondeado a 2 decimales,
  agrupación de vencidos por técnico ordenada por cantidad desc + nombre),
  `use_cases/list_incidentes_vencidos.py` (detalle filtrado, orden de la consulta),
  `dtos/sla_dtos.py`.
- **infrastructure/mercurio**: `query.py` (SQL exacto de SLA.md, reindentado solo por largo de
  línea, placeholders `?`), `row_mapping.py` (acceso por nombre de columna, trim de CHAR,
  NULL-safe), `pyodbc_sla_query_gateway.py` (síncrono en `asyncio.to_thread`, conexión nueva
  por consulta, `pyodbc.Error` → `ExternalServiceError` con log contextual).
  - Detalle importante: el BETWEEN de `FechaOperativo` va de `primer_dia` a `ultimo_dia + 1`
    (datetime: si no, el último día del mes queda afuera); el filtro por período de la propia
    query descarta el excedente.
- **presentation**: `sla_router.py` con dos endpoints, ambos con `require_permission(VIEW)`:
  - `GET /api/sla/resumen?periodo=AAAAMM` → resumen (no colección → sin `Page[T]`, mismo
    criterio que statistics de insumos).
  - `GET /api/sla/incidentes-vencidos?periodo=AAAAMM&page&size` → `Page[IncidenteVencidoSchema]`.
  - `dependencies.py`: `get_sla_query_gateway()` con `lru_cache`; sin `SLA_MERCURIO_HOST`
    responde 502 con mensaje claro (no rompe el arranque).
  - Router registrado en `src/shared/presentation/app.py`.
- **Config** (`settings.py`): bloque `sla_mercurio_*` (host, database=Siges, user, password,
  driver=ODBC 18, `encrypt=False` porque el server legacy no tiene certificado confiable,
  timeout 30s). Sin defaults con credenciales reales a propósito. Documentado en un bloque
  nuevo al final del `.env.example` (ojo: ese archivo estaba trackeado en git pero borrado del
  working tree — se restauró desde HEAD y se le agregó el bloque de sla).
- **Infra de deps**: `pyodbc==5.2.0` en pyproject/uv.lock; override de mypy para pyodbc (sin
  py.typed, `types-pyodbc` no existe en PyPI); Dockerfile instala `msodbcsql18` + `unixodbc`
  (repo MS de Debian 13/trixie, clave `microsoft-2025.asc` — la clásica ya no firma ese repo).
  **El contenedor vivo ya lo tiene instalado a mano**; si se recrea la imagen, rebuild normal.
- **Catálogo**: migración `53826efbc9ed_seed_sla_catalog.py` aplicada — módulo `sla`
  ("SLA", `/sla`, icon gauge, sort 15) con **`is_enabled=False`** + acción `(sla, view)`.
  Reversibilidad probada (up/down/up).
- **import-linter**: 2 contratos nuevos (dominio sin frameworks; domain/application sin auth).
- **Tests** (15 nuevos): VO Periodo, entidad, ambos use cases (con `FakeSlaQueryGateway` +
  `build_incidente` en `tests/unit/domain/sla/fakes.py`), row mapping y wrapping de errores.

Verificación (todo verde al cierre): `uv run lint-imports` (12 kept), `ruff check src tests`,
`mypy src`, `pytest tests/unit -q` (471 passed) — dentro del contenedor
`helpdesk-manager-backend`.

## Bloqueante externo

Faltan las credenciales reales de MERCURIO para probar end-to-end: completar en `.env`
`SLA_MERCURIO_HOST` (admite `SERVIDOR,puerto`), `SLA_MERCURIO_USER`, `SLA_MERCURIO_PASSWORD`
(y `SLA_MERCURIO_DATABASE` si no es `Siges`). Con eso: login como admin y probar
`GET /api/sla/resumen?periodo=202608` (el permiso sla/view lo tiene que tener el usuario, o
ser superadmin). Si el handshake TLS falla igual, revisar `sla_mercurio_encrypt`/driver.

## Frontend — IMPLEMENTADO (pendiente de prueba end-to-end y activación)

Archivos creados:

- **`shared/components/ui/stats-table.tsx`** — `StatsTable`/`StatsColumn` movidos desde
  `features/insumos/...` (igual que `KpiTile`). El original de insumos ahora es re-export.
- **`features/sla/types/sla.ts`** — `SlaResumen`, `TecnicoVencidos`, `IncidenteVencido`
  (snake_case, fechas `string | null`).
- **`features/sla/api/sla-api.ts`** — `slaApi.getResumen(periodo)` y
  `slaApi.listIncidentesVencidos(periodo)`.
- **`features/sla/components/sla-summary-card.tsx`** — card de Inicio: % Correcto (naranja)
  vs % Vencido (danger) + totales del mes corriente, link a `/sla`, gate `modules.some("sla")`.
- **`features/sla/components/sla-detail.tsx`** — pantalla completa: header + selector
  `<input type="month">` + `KpiGrid` (Total/Correctos/Vencidos) + `StatsTable` de incidentes
  vencidos con columnas: ID, Técnico, Región, Cliente, Sucursal, Modelo, Operativo, Rango,
  SLA (h), Vencido (h). El subtitle de la tabla lista técnicos con sus cantidades.
- **`app/(app)/sla/page.tsx`** — wrapper delgado sobre `SlaDetail`.
- **`app/(app)/page.tsx`** — `<SlaSummaryCard />` agregada como tercera card.

- `tsc --noEmit` corrido en el contenedor: solo errores preexistentes de `trend-chart.tsx`
  (chart.js no instalado), cero errores en código SLA.
- Migración `ac5e139e28b4_activate_sla_module.py` aplicada — módulo SLA `is_enabled=True`.
- Usuario `admin@example.com` (superadmin) creado/restaurado en la DB de la PC personal.
- Card en Inicio visible y renderizando correctamente (ícono, título, estados loading/error).

Pendiente (mañana, en red corpo):

1. Completar en `.env`: `SLA_MERCURIO_HOST`, `SLA_MERCURIO_USER`, `SLA_MERCURIO_PASSWORD`
   y `docker compose restart backend`.
2. Verificar end-to-end: card de Inicio muestra % del mes actual, pantalla `/sla` carga
   KpiGrid + tabla de incidentes vencidos.
3. Confirmar layout de la tabla con datos reales; ajustar columnas si hace falta.

## Referencias rápidas

- Router backend: `backend/src/modules/sla/presentation/sla_router.py:1`
- Gateway pyodbc: `backend/src/modules/sla/infrastructure/mercurio/pyodbc_sla_query_gateway.py:1`
- Card de Inicio de referencia: `frontend/src/features/home/components/today-clients-card.tsx:1`
- KpiTile compartido: `frontend/src/shared/components/ui/kpi-tile.tsx:1`
- Tabla de referencia: `frontend/src/features/insumos/components/estadisticas/stats-table.tsx:1`
