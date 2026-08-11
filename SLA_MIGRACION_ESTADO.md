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

## Frontend — PENDIENTE (continuar acá)

Hecho hasta ahora:

- `KpiTile`/`KpiGrid` movidos de `features/insumos/components/estadisticas/kpi-tile.tsx` a
  **`shared/components/ui/kpi-tile.tsx`** (primitiva compartida; `EMPTY_VALUE` duplicado
  adentro para no depender de la feature). Imports de insumos actualizados
  (`cliente-kpis.tsx`, `estadisticas-globales.tsx`). `tsc --noEmit` limpio.

Por hacer (en orden):

1. **`features/sla/types/sla.ts`** — tipos espejo del backend, **snake_case** (los schemas de
   sla no usan `serialization_alias`): `SlaResumen { periodo, total, correctos, vencidos,
   pct_correctos, pct_vencidos, vencidos_por_tecnico: TecnicoVencidos[] }`,
   `TecnicoVencidos { tecnico, cantidad, ids_incidente: number[] }`,
   `IncidenteVencido { id_incidente, tecnico, region, cliente, sucursal, modelo, nro_serie,
   fecha_ingreso, fecha_operativo, tiempo, rango, sla_horas, horas_vencido }` (fechas
   `string | null` ISO).
2. **`features/sla/api/sla-api.ts`** — patrón `turnos-api.ts`: objeto plano sobre
   `httpClient`, `interface Page<T>` local, `getResumen(periodo)` y
   `listIncidentesVencidos(periodo)` (`.then(p => p.items)`). Sin React Query (no se usa en
   este repo): `useState`+`useEffect`+`.then/.catch/.finally`.
3. **`features/sla/components/sla-summary-card.tsx`** — card para Inicio, calcada de
   `features/home/components/today-clients-card.tsx`: mismo shape visual
   (`rounded-[12px] border border-border bg-card p-5`, ícono en círculo
   `bg-brand-orange/[0.12] text-brand-orange` — sugerido `Gauge` de lucide), gate
   `modules.some(m => m.key === "sla")`, estados loading/error/vacío. Contenido: % Correcto
   (naranja) vs % Vencido (tono danger ya existente en KpiTile) + totales del período actual
   (AAAAMM del mes corriente), link a `/sla`. Agregarla como tercera card en el
   `flex flex-wrap gap-4` de `app/(app)/page.tsx`.
4. **Pantalla `/sla`** — `app/(app)/sla/page.tsx` + componentes en `features/sla/components/`:
   - Header h1 estilo Inicio ("SLA" + descripción).
   - Selector de período (mes): `<input type="month">` estilizado con tokens de la app, o
     selects mes/año; default mes actual. Convertir a AAAAMM para la API.
   - `KpiGrid` con `KpiTile`s: Total (neutral), Correctos (tone naranja, hint % correcto),
     Vencidos (tone danger, hint % vencido).
   - Tabla de vencidos agrupada por técnico: seguir el patrón visual de
     `features/insumos/components/estadisticas/stats-table.tsx` (header de card, thead
     uppercase 11px, filas border-t). Para el agrupado: o secciones por técnico (subheader con
     nombre + cantidad, filas con ID/cliente/sucursal/modelo/fecha operativo/tiempo/rango/
     SLA/horas vencido) usando `vencidos_por_tecnico` del resumen + detalle, o una StatsTable
     propia con columna técnico — decidir al maquetar y **mostrar render al usuario**.
   - El sidebar toma el módulo del catálogo del backend: no tocar `sidebar.tsx`.
5. **Reglas de diseño** (skill `ui-design-handoff` ya consultado): solo línea Institucional,
   `rounded-[Npx]` literales (nunca `rounded-lg` etc. — remapeados a 24px), tokens dark-aware
   (`bg-card`, `text-muted-foreground`...), app dark-by-default.
6. **Activación**: recién con todo probado end-to-end, migración `activate_sla_module`
   (`is_enabled=True`, patrón `6d910a2b8e39_activate_contadores_module.py`) y asignar el
   permiso sla/view a los usuarios que corresponda desde Configuración.
7. Verificación final backend (4 comandos de arriba) + `npx tsc --noEmit` en el contenedor
   frontend; probar la card y la pantalla logueado (credenciales dev en memoria del proyecto).

## Referencias rápidas

- Router backend: `backend/src/modules/sla/presentation/sla_router.py:1`
- Gateway pyodbc: `backend/src/modules/sla/infrastructure/mercurio/pyodbc_sla_query_gateway.py:1`
- Card de Inicio de referencia: `frontend/src/features/home/components/today-clients-card.tsx:1`
- KpiTile compartido: `frontend/src/shared/components/ui/kpi-tile.tsx:1`
- Tabla de referencia: `frontend/src/features/insumos/components/estadisticas/stats-table.tsx:1`
