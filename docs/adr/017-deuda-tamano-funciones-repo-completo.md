# ADR-017: Deuda aceptada de tamaños (§4) extendida a todo el backend

## Estado: Aceptado (2026-08-14)

## Contexto

La auditoría app-wide (`docs/AUDITORIA_ARCHITECTURE_GUIDE_2026-08-14.md`) midió con AST
el cumplimiento de los límites de `ARCHITECTURE_GUIDE.md` §4 en todo `backend/src`,
excluyendo migraciones Alembic:

- Funciones ≤20: **247 violaciones** (179 de 21–30 líneas, 58 de 31–50, 10 de >50).
  Las 41 de `liquidaciones` ya estaban cubiertas por ADR-016; quedaban **206 sin ADR**
  (insumos 102, contadores 37, vacaciones 32, prestadores 17, turnos 6, auth 5, sla 5,
  shared 2).
- Clases ≤200: 2 (`HttpxSdsClientProvider` 222, `SqlAlchemyAuditStatisticsRepository` 215).
- Archivos ≤300: 3 no-migración (`get_dashboard.py` 327, `list_pending_orders.py` 305,
  `ftplib_db3_downloader.py` 313).
- Firmas ≤3 parámetros: 252, concentradas en endpoints FastAPI (parámetros
  `Depends`/`Query` inyectados por el framework) y firmas keyword-only de repos/schemas
  de muchas columnas.
- Anidamiento ≤3: 4 casos de profundidad 4.

Es el mismo fenómeno que ADR-016 diagnosticó para `liquidaciones`: el span físico
(firma multilínea + docstring) sobreestima la complejidad; los módulos afectados están
portados, verificados contra datos/servicios reales y en uso. El diagnóstico de esa ADR
— "los bugs aparecieron en la integración real, no en unidades largas" — aplica igual a
insumos, contadores y vacaciones.

## Decisión

Se extiende el criterio de ADR-016 del módulo `liquidaciones` a **todo `backend/src`**:

1. **El inventario existente al 2026-08-14 se acepta como deuda documentada** — el
   listado completo (archivo:línea y span de cada caso) está en la sección §4 del
   informe de auditoría citado. No se abre un workstream de refactor en bloque: tocar
   ~250 unidades verificadas contra contenedores y servicios reales solo para
   satisfacer un conteo de líneas agrega riesgo de regresión sin reducir complejidad
   real.
2. **Las 10 funciones >50 líneas son la parte con complejidad real** (no firmas largas):
   `export_meters_to_csv` (SDS 106, ERS 85), `sync_pending` (67), `refresh_ers_token`
   (65), `preview_zone_contacts` (65), `create_app` (64), `_row_from` (58),
   `decidir_solicitud.execute` (58), `verify_offline_devices._run` (52),
   `gestionar_solicitudes.execute` (52). **Se refactorizan de forma oportunista**: la
   próxima vez que cualquiera se toque por otro motivo, ese cambio la baja del límite.
   Ídem las 2 clases >200 y los 3 archivos >300.
3. **Las firmas >3 parámetros por inyección de FastAPI (`Depends`/`Query`/`Path` en
   endpoints) no se cuentan como violación de §4**: agruparlas en un objeto rompería el
   mecanismo de inyección del framework — es idiom, no diseño. Las firmas keyword-only
   de repos/schemas de muchas columnas entran en el punto 1 (deuda aceptada, se reducen
   al tocar).
4. **Los `upgrade()`/`downgrade()`/seeds de migraciones Alembic quedan fuera del alcance
   de §4**: una migración es un script lineal e inmutable una vez aplicado; partirlo en
   helpers no mejora nada y editarlo a posteriori está prohibido por diseño.
5. **El límite §4 sigue plenamente vigente para todo código nuevo o reescrito** en
   cualquier módulo — esta excepción cubre solo el inventario congelado. La auditoría
   periódica (script AST del informe) compara contra ese inventario: todo caso nuevo es
   violación, no deuda.

ADR-016 queda subsumido por esta ADR para lo general; su inventario específico de
`liquidaciones` sigue siendo el registro de detalle de ese módulo.

## Consecuencias

- La desviación §4 de toda la app queda con registro explícito (una excepción sin ADR
  es una violación, per CLAUDE.md) y con línea de base medible para detectar deuda
  nueva.
- El costo real se paga de a poco (refactor al tocar), donde hay contexto y tests
  frescos, no en un big-bang de refactor sin necesidad de negocio.
- Riesgo asumido: "oportunista" puede volverse "nunca" si esas funciones no se tocan.
  Mitigación: las 10 >50 son las únicas con complejidad real y están listadas acá — si
  en una futura auditoría siguen igual y además acumularon bugs, ese dato revierte esta
  decisión para ellas.

## Addendum 2026-08-22: gate automático e inventario ampliado

La auditoría del 2026-08-22 (`docs/AUDITORIA_ARCHITECTURE_GUIDE_2026-08-22.md`) midió que
entre el 14/08 y el 22/08 entraron **75 funciones nuevas >20 líneas** (13 de >30), **2
clases >200** (`Settings`, `SqlAlchemyTablaKmRepository`) y 1 archivo frontend >300 sin que
nada lo detectara: el punto 3 de esta ADR ("límite vigente para código nuevo") no tenía
herramienta que lo hiciera cumplir. Decisión:

1. **Gate en `make check`**: `scripts/check_sizes.py` mide con AST (backend, sin
   migraciones) y por archivo (frontend) y **falla** con cualquier función >20 / clase
   >200 / archivo >300 que no esté en `scripts/sizes-baseline.json`. Corre en el `pre-push`
   vía `make check`.
2. **El inventario congelado pasa a ser ese JSON** (antes: el listado del informe del
   14/08). Se generó con el estado del 2026-08-22, o sea **incluye** las 75+2 que entraron
   sin gate — refactorizarlas en bloque tiene el mismo costo/riesgo que motivó esta ADR y
   no reduce complejidad real; quedan bajo la misma regla de refactor oportunista (el
   archivo que se toque baja del límite) y el gate impide que el inventario vuelva a
   crecer. Regenerarlo (`--update`) es una decisión consciente que se acompaña con una
   nota en esta ADR.
3. Lo que sale del inventario por refactor se informa (`ℹ N entradas ya no exceden`) y se
   poda con `--update` en el siguiente commit que lo toque.

**Poda del 2026-08-22 (misma jornada, después del gate)**: se refactorizaron las 13 funciones
>30 líneas y las 2 clases >200 que habían entrado entre el 14/08 y el 22/08 (`analisis_log_hp`,
`liquidaciones`, `insumos`, `turnos`, `Settings` en shared), con `make check` completo en
verde antes y después y cobertura igual o mayor por módulo; el inventario pasó de 389 a 372
entradas (360 funciones, 2 clases, 10 archivos frontend) regenerado con `--update`.

**Poda del 2026-08-22 (segundo lote)**: refactorizadas las 11 funciones >50 líneas, las 2
clases >200 restantes (`HttpxSdsClientProvider` 222→122, `SqlAlchemyAuditStatisticsRepository`
215→94) y los 3 anidamientos >3 (`list_active_customers`, `_import_file`,
`build_availability_windows`), más `create_app` 83→10 y `EditarSolicitud.execute` 52→11; el
inventario queda en **340 funciones de 21–47 líneas, 0 clases, 0 archivos backend**. El gate
pasó a medir HEAD en `make check` (`--committed`) y lo staged en el pre-commit (`--staged`):
con varias sesiones sobre el mismo checkout, medir el árbol de trabajo frenaba el push de una
sesión por el WIP de otra.
