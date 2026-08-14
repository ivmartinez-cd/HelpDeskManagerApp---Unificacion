# Estado actual del módulo Liquidaciones — 2026-08-13

Reporte de estado con verificación liviana (confirmar, no re-auditar). Todo lo marcado
"verificado ahora" se corrió en esta pasada contra el código committeado, los contenedores
y `helpdesk-db`; lo que viene del informe del 2026-08-13
(`VALIDACION_PIPELINE_LIQUIDACIONES_2026-08-13.md`) se cita como tal.

Precondición de seguridad cumplida antes de tocar los contenedores:
`docker exec helpdesk-manager-backend printenv DISABLE_BACKGROUND_JOBS` → `true`, y el log
de arranque no contiene `background_jobs: N job(s) iniciados` (verificado ahora). No se
ejecutó ningún sync ni escritura — solo lectura.

## 1. ESTADO GLOBAL

**VERDE** — los 8 hallazgos de la validación adversarial están cerrados y verificados contra
el código committeado; gates en verde (lint-imports 19/19, ruff, mypy 928 archivos, 1098
unit, tsc y eslint limpios); DB consistente (35 liqs / 1857 incidentes / 763 alertas / 22
observaciones, 34+34 vínculos, ALT007 inactiva).

**¿Listo para operar?** Sí, técnicamente: no queda ningún bloqueo. El único paso grande
pendiente — el sync WS completo (~2.000+ liquidaciones históricas) — es una decisión de
la TL por volumen y momento, no un impedimento técnico.

## 2. HALLAZGOS H-1..H-8

Todos verificados ahora contra el código en `main` (no contra la doc).

| H | Estado | Evidencia (verificada ahora) |
|---|--------|------------------------------|
| H-1 numeración 3-1-3-1 | CERRADO | `domain/services/numeracion_ayc.py` existe; `infrastructure/soap/zeep_cd_liquidaciones_gateway.py:19` importa el servicio y `:106` lo usa (`numero_liquidacion(liq_id)`); grep de `% 10` en `infrastructure/` solo devuelve ese import — el `id % 10` no existe más; `pytest -k numeracion_ayc` → **71 passed** |
| H-2 liqs vacías | CERRADO | `application/use_cases/sincronizar_liquidaciones.py`: campo `fallidas` en el resultado (`:63`), guarda de detalle vacío con incidentes declarados que no crea y cuenta (`:116`, `:120-125`), log por prestador con `fallidas` (`:86-90`) |
| H-3 sinPrestador | CERRADO | `sincronizar_liquidaciones.py:79` — `sin_prestador = sum(1 for p in activos if p.cd_prestador_id is None)`; expuesto como `sinPrestador` en `presentation/schemas/sincronizar_schemas.py:14` |
| H-4 ALT002 tolerancia dual | CERRADO | `domain/services/motor_reglas/alt002_km.py:32-35` — tolerancia contra `esperado_raw` **y** `math.ceil(esperado_raw)`, alcanza con que una pase; docstring documenta ambas formas válidas de facturar |
| H-5 ?prestadorId= | CERRADO | `presentation/liquidaciones_router.py:118` — `prestador_id: UUID \| None = Query(default=None, alias="prestadorId")` en `POST /sincronizar`; sin él sincroniza todos los vinculados (`:122-124`) |
| H-6 list_con_cd_id activos | CERRADO | `infrastructure/repositories/sqlalchemy_prestador_repository.py:90-95` — `where(cd_prestador_id.is_not(None), activo.is_(True))` |
| H-7 split §4 | CERRADO | `wc -l`: `_liq_csv.py` **282** líneas, `_liq_csv_export.py` **95** — ninguno >300; deuda restante de funciones 21–37 líneas documentada en `docs/adr/016-deuda-tamano-funciones-liquidaciones.md` (existe, estado Aceptado) |
| H-8 ALT007 inactiva | CERRADO | Migración `b9f2d47c8e11_liquidaciones_alt007_inactiva.py` existe; DB: `SELECT codigo, activa FROM reglas_alerta` → `ALT007 → f`; la DB está en head `c7d1f92e4a68` cuya `down_revision` es `b9f2d47c8e11` (aplicada) |

Nota: `ALT006` también figura inactiva — es preexistente y fiel al legacy (sin evaluador,
según el informe del 2026-08-13), no un cambio de esta ronda.

## 3. GATES

Todos re-corridos ahora, dentro de los contenedores. Resultados reales de esta pasada:

| Gate | Comando | Resultado |
|------|---------|-----------|
| lint-imports | `docker exec helpdesk-manager-backend uv run lint-imports` | **Contracts: 19 kept, 0 broken** |
| ruff | `… uv run ruff check src tests` | **All checks passed!** |
| mypy | `… uv run mypy src` | **Success: no issues found in 928 source files** (el informe decía 927; el +1 es la migración de vacaciones `c7d1f92e4a68`, posterior) |
| pytest unit | `… uv run pytest tests/unit -q` | **1098 passed** in 19.13s |
| tsc | `docker exec helpdesk-manager-frontend npx tsc --noEmit` | Sin errores (salida vacía, exit 0) |
| eslint | `docker exec helpdesk-manager-frontend npx eslint src` | Sin errores (salida vacía, exit 0) |

## 4. ESTADO DE DATOS

Consultado ahora contra `helpdesk-db` (`psql -U helpdesk -d helpdesk`, solo SELECT):

| Métrica | Valor hoy | vs. informe 2026-08-13 |
|---------|-----------|------------------------|
| Liquidaciones | **35** | igual |
| Incidentes | **1857** | igual |
| Alertas | **763** | igual |
| Observaciones | **22** | igual |
| Prestadores (total / activos) | **35 / 34** | igual (el inactivo es ZZTESTUI) |
| Vínculos `siges_empresa_id` | **34** | igual |
| Vínculos `cd_prestador_id` | **34** | igual |
| ALT007 | **inactiva** (`activa=f`) | único cambio persistente, por migración — confirmado |

La DB está exactamente en el estado final que reportó el informe: ninguna escritura de la
validación persistió salvo la desactivación de ALT007 (intencional, por migración).

## 5. GIT

Verificado ahora:

- `e75685a` y `fbec610` están en `main` (`git branch --contains` → `main`, y son los dos
  commits más recientes).
  - `e75685a fix(liquidaciones)`: los 8 fixes — `numeracion_ayc.py` nuevo,
    `sincronizar_liquidaciones.py` (use case + DTO), `alt002_km.py`, contrato del
    `prestador_repository`, `cd_liquidacion.py`, más tests.
  - `fbec610 docs(liquidaciones)`: informe de validación, master prompt de la auditoría,
    capturas Chromium (dashboard pre-sync, resultado, idempotencia), actualización de
    `LIQUIDACION_PRESTADORES_MIGRACION_ESTADO.md`.
- Working tree: 2 archivos modificados **ajenos a este trabajo** (sesión de vacaciones/menú):
  `frontend/src/shared/components/insumos-nav-submenu.tsx` (±14 líneas) y
  `vacaciones-nav-submenu.tsx` (±160). Sin tocar. Además queda untracked
  `docs/liquidaciones/MASTER_PROMPT_ESTADO_ACTUAL_LIQUIDACIONES.md` (el prompt de este
  reporte) y este archivo.

## 6. DEUDA ACEPTADA Y DECISIONES

- **ADR-016** (`docs/adr/016-deuda-tamano-funciones-liquidaciones.md`, Aceptado
  2026-08-13): las ~40 funciones de 21–37 líneas del módulo quedan como deuda documentada
  — el span físico sobreestima la complejidad (firmas keyword-only + docstrings) y
  refactorizarlas en bloque agrega riesgo sin reducir complejidad real. El límite §4 sigue
  vigente para todo código nuevo; si una de esas funciones se toca por otro motivo, se baja
  del límite en ese cambio.
- **ALT007 desactivada** (migración `b9f2d47c8e11`): regla activa sin evaluador confundía
  operativamente; se cede fidelidad al snapshot de prod por claridad. Documentado en el
  informe (tabla de fixes) y en `regla_alerta.py`.
- **H-4 / semántica de ALT002**: el fix cambia el comportamiento del commit `1b562e4`
  (solo-ceil) a tolerancia dual (crudo o ceil). Está documentado en docstring y cubierto
  por 36 tests del motor, pero **no encontré registro de confirmación explícita de la TL**
  ni en el informe ni en `MIGRACION_ESTADO` — queda como pendiente de confirmación con
  ella (a diferencia de, p. ej., el recadenado de vigencias en importadores, que sí tiene
  confirmación registrada).

## 7. PENDIENTES Y PRÓXIMO PASO

1. **Sync WS completo (pendiente #1, DESBLOQUEADO, no ejecutado)** — verificado ahora: la
   DB sigue en 35 liquidaciones (las del CSV), o sea el histórico completo **no** se
   importó; solo existen las corridas controladas ya documentadas y revertidas (SM TUCUMAN:
   `creadas=20, yaExistentes=3, 0 duplicados` post-fix; JUJUY: 114 creadas y borradas).
   Riesgo/volumen conocido: ~2.000+ liquidaciones históricas proyectadas según el sondeo de
   la validación, con request síncrono largo — mitigable corriendo por prestador con
   `POST /api/liquidaciones/sincronizar?prestadorId=` (H-5). Es decisión de la TL cuándo
   correrlo; no se ejecutó como parte de este reporte (restricción explícita).
2. **Período en paralelo con la app legacy** antes de cualquier cutover — sin cambios.
3. **TL**: confirmar los 2 conflictos menores de tarifarios (VENADO $45, INFOMAC preventivo
   Villa Mercedes — seguirán apareciendo en cada dry-run como recordatorio) y, si algún día
   hace falta, mapear las zonas `GSJ - *` de SAN JUAN / `TMTA122 - SGO DEL ESTERO` (hoy sin
   mapear a propósito).
4. **TL**: confirmar el cambio de semántica de ALT002 (punto 6).

**Próximo paso sugerido** (igual que en `MIGRACION_ESTADO`): correr el sync completo —
idealmente por tandas con `?prestadorId=` — y arrancar la observación en paralelo con el
legacy. La config se mantiene sola desde Siges; las preliquidaciones nuevas llegan con un
click desde el dashboard.

---

## Addendum (2026-08-13, mismo día, posterior al reporte): pendiente #1 EJECUTADO

A pedido del usuario se corrió el sync WS completo — por tandas por prestador
(`?prestadorId=`, 34 requests secuenciales), con `DISABLE_BACKGROUND_JOBS=true`
verificado y sesión admin temporal minteada y revocada al cierre. Resultado:

- **34/34 en verde, `fallidas=0` en todos**: 2.380 creadas + 35 yaExistentes (las 35
  del CSV — dedup H-1 al 100%, cero duplicados).
- DB post-sync: **2.415 liquidaciones** (2.415 `numero_liquidacion` distintos, 0
  vacías) · 112.354 incidentes · 32.329 alertas · 758 observaciones · 34/34
  prestadores con liquidaciones.

Detalle por prestador y verificación de integridad en
`LIQUIDACION_PRESTADORES_MIGRACION_ESTADO.md` §"Sync CD completo ejecutado". Los
pendientes vigentes pasan a ser: observación en paralelo con el legacy, y las dos
confirmaciones de la TL (conflictos de tarifarios; semántica ALT002 del fix H-4).
