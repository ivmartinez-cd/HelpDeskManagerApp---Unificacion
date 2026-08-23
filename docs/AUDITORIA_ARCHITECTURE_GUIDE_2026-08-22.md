# Auditoría de cumplimiento de ARCHITECTURE_GUIDE.md — 2026-08-22

Segunda pasada app-wide, ocho días después de la del 2026-08-14
(`AUDITORIA_ARCHITECTURE_GUIDE_2026-08-14.md`). Mismo método — herramientas, no lectura
impresionista — y además dos cosas nuevas: (a) cada número se compara contra la línea base
del 14/08 y contra los inventarios que congelaron los ADR-017 (backend) y ADR-020
(frontend), porque desde esos ADR **todo caso nuevo es violación, no deuda**; y (b) se
revisan los propios docs (`docs/*.md`, `CLAUDE.md`, READMEs) buscando referencias a archivos
que ya no existen.

Alcance: backend `src/modules/*` (ahora 12 módulos: auth, contadores, insumos,
liquidaciones, prestadores, sla, turnos, vacaciones + los nuevos **analisis_log_hp,
preventivos, wati** + `stc` vacío) y `src/shared/`; frontend `src/`. Sin cambios de código
en esta pasada, salvo el addendum final.

Condiciones de la corrida: `docker exec helpdesk-manager-backend printenv
DISABLE_BACKGROUND_JOBS` → `true`; 0 líneas `background_jobs: N job(s) iniciados` en el log
del contenedor. `helpdesk-db-test` estaba apagado; se levantó para la corrida de integración
y queda corriendo. Los 32 ADR (`docs/adr/001`–`032`) se leyeron antes de clasificar.

---

## FASE 1 — Números duros (y delta contra el 14/08)

### §2/§3 Capas y módulos — `make check` → `uv run lint-imports` (contenedor)

```
Contracts: 26 kept, 0 broken.
```

(14/08: 19 kept.) Siete contratos más que hace una semana: Los módulos nuevos
(`analisis_log_hp`, `preventivos`, `wati`) quedaron bajo contrato.

### Gates de calidad

| Gate | Comando | 14/08 | 22/08 |
|---|---|---|---|
| Capas | `uv run lint-imports` | 19 kept / 0 broken | **26 kept / 0 broken** |
| Lint backend | `uv run ruff check src tests` | limpio | **limpio** |
| Tipos backend | `uv run mypy src` | limpio | **limpio** |
| Unit | `uv run pytest tests/unit -q` | 1098 passed | **1824 passed** |
| Tipos frontend | `tsc --noEmit` | 0 errores | **0 errores** |
| Lint frontend | `eslint src --max-warnings=0` | 0 | **1 warning** (`analisis-log-hp/components/hp-logs-panel.tsx:49` prop `sdsResult` sin usar) — el gate estricto falla; el `pre-push` corre eslint sin `--max-warnings=0`, por eso pasó |
| Deps backend | `pip-audit` (en el contenedor, con red) | no medido | **0 vulnerabilidades conocidas** |
| Deps frontend | `npm audit --omit=dev` | no medido | **1 high** (`nanoid` GHSA-2v37-7h3g-55p8, transitiva; `npm audit fix` disponible) |

### §4 Tamaños — script AST sobre `backend/src` (span físico), sin migraciones

| Métrica | 14/08 (base ADR-017) | 22/08 | Delta |
|---|---|---|---|
| Funciones >20 | 247 | **375** | +128 |
| Clases >200 | 2 | **4** | +2 (`shared/infrastructure/config/settings.py Settings` 219, `liquidaciones/.../sqlalchemy_tabla_km_repository.py SqlAlchemyTablaKmRepository` 212) |
| Archivos >300 (no migración) | 3 | **0** | −3 ✅ (los 3 se partieron) |
| Funciones >50 | 10 | **11** | +1 neto (entran `delete_offline_devices._run` 55 y `sincronizar_liquidaciones.execute` 54; sale `decidir_solicitud.execute`; `create_app` pasó de 64 a 83) |
| Firmas >3 params | 252 | 383 | +131 (mismo idiom FastAPI/keyword-only; informativo) |
| Anidamiento >3 | 4 | 5 | `db3_merge._import_file` y `sincronizar_liquidaciones._sincronizar_prestador` entran; `ftplib_db3_downloader` salió |

Por módulo (funciones >20, 21–30 / 31–50 / >50): insumos 80/24/5 = 109 · liquidaciones
71/17/1 = 89 · contadores 41/11/3 = 55 · vacaciones 21/12/1 = 34 · **analisis_log_hp 17/8/0 =
25 (módulo nuevo)** · turnos 15/6/0 = 21 · prestadores 10/6/0 = 16 · sla 7/3/0 = 10 · auth
6/0/0 · shared 2/1/1 · preventivos 3/1/0 · wati 2/0/0.

**Lo que importa de verdad — el diff contra el inventario congelado.** Se corrió el mismo
script sobre el snapshot `87264330` (último commit del 2026-08-14, el estado que ADR-017
aceptó como deuda) y se comparó función por función:

- 123 violaciones nuevas por `(archivo, nombre)`; **48** de ellas son funciones con el
  mismo nombre que ya existían en otro archivo (movidas por los refactors §4 de la semana:
  `turnos_router` partido por recurso, `geolocalizacion` routers, `get_dashboard.py`…) —
  no son deuda nueva, es la misma deuda reubicada.
- **75 funciones estrictamente nuevas >20 líneas** (nombre inexistente el 14/08):
  liquidaciones 28 · analisis_log_hp 19 · turnos 8 · insumos 7 · contadores 7 · wati 2 ·
  vacaciones 1 · auth 1. De ellas **13 superan las 30 líneas** (las que tienen complejidad
  real, no una firma larga): `capture_sds_snapshots._capture_one` (48),
  `httpx_hp_portal_gateway.search_device` (43) y `.refresh_hp_cache` (42),
  `sincronizar_liquidaciones._reconciliar` (41), `zone_delivery_notice.detect_sucursal_override`
  (39), `analysis_router.preview_analysis` (37), `compare_service.diff_two_snapshots` (37),
  `preview_calcular_distancias._armar_fila` (37), `sqlalchemy_ausencias_lookup._bajas` (36),
  `sqlalchemy_tabla_km_repository.update_distancias` (36),
  `sqlalchemy_error_code_repository.bulk_update_solution_urls` (32),
  `sincronizar_liquidaciones._sincronizar_prestador` (32), `tabla_km_lugares._guardar` (31).
- 18 violaciones del inventario del 14/08 desaparecieron (refactor oportunista cumplido).
- Las 2 clases >200 son nuevas desde el 14/08 y no están en ningún ADR.

Frontend (`wc -l`, `.ts/.tsx`): **11 archivos >300** (14/08: 9; ADR-020 congeló 14 el 16/08).
Contra el inventario de ADR-020: 4 archivos del inventario ya no lo superan
(`casillas-manager`, `types/liquidaciones.ts`, `use-order-actions.ts`, `incidentes-seccion`
— partidos esta semana), 2 crecieron (`sidebar.tsx` 349→379, `solicitudes-view.tsx`
308→327) y **1 es nuevo y no está en el inventario: `features/home/hooks/use-inicio-data.ts`
(317 líneas, creció hoy con el rediseño de Inicio)** → violación, no deuda.

AST de funciones TS (`typescript` compiler API, span físico, `frontend/src`): **566 funciones
>20 líneas, 489 de ellas son componentes React (devuelven JSX); 265 superan las 50** (máx.
`Sidebar` 334, `ConsumableDetailModal` 299, `PreventivosView` 297). No se había medido
antes. Leer §4 literalmente ("función ≤20 líneas") contra componentes JSX da un número que
nadie va a cumplir ni conviene perseguir: el límite útil en React es el del archivo
(ADR-020) y la extracción de sub-componentes/hooks cuando un componente mezcla
responsabilidades. Queda como **hallazgo de guía, no de código**: la guía no dice cómo
se mide §4 en componentes, y ADR-020 solo habla de archivos.

### §5 Dependencias

```
grep -rnE "^(import|from) (zeep|pyodbc|pandas|httpx|sqlalchemy|fastapi|pydantic|aiosmtplib|openpyxl|ftplib|alembic|dbf|requests|bs4|lxml)" src/modules/*/domain src/modules/*/application src/shared/domain
→ 0 hits
```

### §6 Manejo de errores — AST sobre `except Exception` / `except:`

| Clase | 14/08 | 22/08 |
|---|---|---|
| Relanzan (envuelven) | 18 | 23 |
| Loguean en el punto de manejo | 66 | 87 |
| "Silenciosos" según el AST | 2 | 2 |

Los 2 "silenciosos" son los mismos de la pasada anterior (`insumos/.../load_order.py:92` y
`:220`): delegan a `_handle_creation_failed`, que hace `logger.exception` y registra el
fallo en el resultado. **0 silenciamientos reales** sobre 112 handlers amplios; los 26
handlers nuevos (wati, analisis_log_hp, preventivos, liquidaciones) todos loguean o
relanzan.

### §7 Testing — cobertura unit+integración (`pytest tests -q --cov=src --cov-branch`)

Cómo se corrió: contenedor efímero con la imagen y el volumen `.venv` del backend
(`docker run --rm --entrypoint uv --volumes-from helpdesk-manager-backend --network
container:helpdesk-db-test -e DATABASE_URL=<db de test> -e DB_TEST_PORT=5432 …`), porque el
`conftest` de integración hardcodea `localhost:<puerto>` y desde el contenedor del backend
no llega a `helpdesk-db-test`. Dos trampas de método que conviene dejar anotadas: el
entrypoint de la imagen corre `alembic upgrade head` antes de cualquier comando (contra una
DB vacía rompe en una migración con datos sembrados, `b241c9c3…:252`), y el `.env` del host
apunta la DB a `localhost:5439`.

**Resultado: 2078 tests, 2073 passed, 5 FAILED.** Cobertura total **82.3 %** (14/08 tras
la corrección: 84.7 %; 1427 tests).

| Capa | 14/08 | 22/08 | ¿Mínimo? |
|---|---|---|---|
| domain | 95.3 % | 93.2 % | ✅ (≥90) |
| application | 94.0 % | 90.0 % | ✅ (≥85) |
| infrastructure | 78.6 % | **68.3 %** | ❌ (<70) |
| presentation | 74.1 % | 74.2 % | ✅ (≥60) |

Celdas módulo/capa bajo mínimo (14/08 tras la corrección: 0):

| Módulo/capa | Cobertura | Mínimo |
|---|---|---|
| **analisis_log_hp/application** | 38.7 % | 85 |
| **analisis_log_hp/domain** | 68.0 % | 90 |
| **analisis_log_hp/infrastructure** | 29.0 % | 70 |
| preventivos/infrastructure | 48.3 % | 70 |
| wati/infrastructure | 62.0 % | 70 |
| sla/application | 66.5 % | 85 |
| vacaciones/infrastructure | 65.1 % | 70 |
| liquidaciones/infrastructure | 68.0 % | 70 |
| insumos/infrastructure | 70.0 % (69.95) | 70 |

Lectura: los módulos que estaban sobre el mínimo el 14/08 siguen ahí o rozan el límite
(liquidaciones/insumos/vacaciones infra crecieron en código nuevo más rápido que en tests);
el agujero es **`analisis_log_hp`**, portado después de la auditoría anterior con una
fracción de los tests que el resto del repo tiene, más `preventivos` y `wati` (nuevos,
chicos) y `sla/application` (66.5 %, ya estaba marginal).

**Los 5 tests que fallan** (en `main`, no es ruido de entorno):

- `tests/integration/infrastructure/liquidaciones/test_sqlalchemy_alerta_repository.py` ×3 y
  `test_sqlalchemy_resolucion_repository.py` ×1: `AttributeError: 'AlertaGenerada' object
  has no attribute 'generada'` — el repositorio (`sqlalchemy_alerta_repository.py:56`) pasó
  a recibir `AlertaConciliada` (que envuelve a la `generada`, cambio de la reconciliación
  ADR-024) y los tests de integración siguen construyendo `AlertaGenerada` a secas. Los
  tests quedaron desactualizados respecto del dominio.
- `tests/integration/infrastructure/contadores/test_run_db3_export_end_to_end.py::
  test_end_to_end_matches_live_verified_legacy_output`: `assert '' == '20'` en
  `CLASE_20` de `SER002` — el export DB3 (`db3_merge.py` / exporter) cambió de
  comportamiento y la salida ya no coincide con la "legacy verificada en vivo" que el test
  protege. Esto es un test de caracterización contra el legacy: o el export tiene una
  regresión real, o el test quedó viejo — **hay que mirarlo**, no es cosmético.

Causa de fondo: `make check` y el `pre-push` corren **solo `tests/unit`**; la suite de
integración no corre en ningún gate desde que el conftest exige `localhost:5440`, así que
puede romperse sin que nadie lo vea. §9 "cada commit pasa los tests" hoy vale solo para
unit.

Frontend: **15 specs Playwright / 91 tests** (`frontend/tests/*.spec.ts`) contra un backend
mock — tests de UI, no e2e navegador→API→DB; ADR-022 (pirámide sin e2e real) sigue vigente
y no se contradice.

### §8 Seguridad

- **AuthZ** (AST sobre todos los decoradores de ruta, `src` completo): **322 endpoints**
  (14/08 contaba 170 solo en routers de módulos); **7 sin `require_permission`/
  `require_feature`/identidad**: `health` ×3 (`GET /api/health`, `GET /api/health/db`,
  `POST /api/health/echo`) y `auth` ×4 (`login`, `logout`, `forgot_password`,
  `reset_password`) — pre-auth por diseño. `POST /api/health/echo` es un endpoint de
  prueba sin auth que devuelve lo que recibe: inofensivo, pero no tiene consumidor (YAGNI).
- **SQL**: f-strings en SQL → 9 hits: 3 en migraciones con constantes de módulo
  (`b8d1f4c7…:49`, `c3e5a7b9…:140-141`), `ftp_client_model.py:22,25` (constantes),
  `sqlalchemy_supply_cache_repository.py:152` (`int()` previo) — los mismos de antes, sin
  vector — y **3 nuevos en `contadores/infrastructure/ftp/db3_merge.py:144,176,184`**:
  `PRAGMA table_info("{table}")` / `SELECT {col_str} FROM "{table}"` sobre SQLite, con
  nombres de tabla/columna que salen del `sqlite_master` del propio archivo DB3 bajado por
  FTP (identificadores entre comillas dobles, sin escapar `"`). No hay input de usuario;
  el "input" es un archivo externo de un cliente. Riesgo bajo, pero es concatenación de
  identificadores en SQL, que §8 prohíbe literalmente.
- **Secretos**: grep de literales → 0. `dangerouslySetInnerHTML` en frontend → **0** (el
  hallazgo ALTO del 14/08 sigue cerrado). `console.log` en `frontend/src` → 0; `print(` en
  `backend/src` → 0.
- **Dependencias auditadas**: ver gates (pip-audit limpio; npm 1 high transitiva).

### §11 Paginación y N+1

- `Page[` aparece en **58 archivos** de `presentation` (14/08: 24 routers).
- Endpoints que devuelven `list[...]` sin `Page[T]`: **6**, todos en
  `analisis_log_hp/presentation/sds_router.py` (`get_consumables`, `get_alerts`,
  `get_meters`, `get_hp_operations`, `get_clients`, `get_client_devices`) — **cubiertos por
  ADR-021** (proxy passthrough de SDS/Insight). Los 8 catálogos del 14/08 siguen paginados.
  → no es hallazgo.
- N+1 (heurística AST: loops en `application/` con `await` a repo/gateway adentro): **5**
  hits (14/08: 39): `contadores/get_calendar_events.py:74` (un `list_events` por operador
  ausente que el usuario cubre — cardinalidad = cantidad de ausentes, chica),
  `liquidaciones/_recadenado.py:25` y `matching_sucursales_tabla_km.py:110` (escrituras por
  fila, patrón ADR-014/015), `wati/sync_conversaciones.py:64,75` (una llamada a WATI por
  chat: es el diseño del polling, ADR del módulo). Sin hot path confirmado.

### §9 Control de versiones

Últimos 30 commits: **30/30 Conventional Commits**. Commits >400 líneas en los últimos 20:
13 (portes de módulos, refactors §4 en bloque y el rediseño de Inicio) — **cubierto por
ADR-023** (flujo single-dev, commits directos a `main`, gates locales como CI).

### §10 Documentación

- **32 ADR** (001–032), todos con Estado/Contexto/Decisión/Consecuencias; desde el 14/08 se
  agregaron 16, entre ellos los que cierran hallazgos de esa auditoría: 017 (tamaños
  backend), 020 (tamaños frontend), 021 (proxy SDS sin Page), 022 (pirámide sin e2e), 023
  (single-dev).
- **`backend/README.md` y `frontend/README.md` existen** (hallazgo BAJO del 14/08 cerrado).
- **Docs con referencias a archivos inexistentes** (script: todo path con extensión entre
  backticks en `docs/*.md`, `CLAUDE.md` y los 3 README, buscado por path relativo y por
  nombre en todo el repo):

| Doc | Refs rotas | Lectura |
|---|---|---|
| `INTEGRACION_APPS_PLAN.md` | 28 | Apuntan a los repos legacy (`HelpDeskManager-Web/…`, `SDSInsumos/CLAUDE.md`, `.mcp.json`…): es el plan de migración original; **desactualizado como doc vivo**, válido como histórico |
| `MASTER_PROMPT_REDISENO_DASHBOARD_INICIO.md` | 10 | Archivos borrados hoy por el rediseño (`use-auto-grid.ts`, `operador-donut.tsx`…) citados en la sección "antes" — correcto como histórico |
| `MASTER_PROMPT_INCIDENTES_SIN_CERRAR_POR_PRESTADOR.md` | 9 | Describe un módulo `stc/` + card que **no se construyó así** (lo que existe es `sla/pendientes-a-cerrar`); el prompt quedó obsoleto sin nota |
| `MASTER_PROMPT_NOTA_PERSONAL_INICIO.md` | 3 | Feature no implementada (`personal-note-card.tsx`, `notas-api.ts`); además describe una Home (`ShiftDashboardCard`, `TodayClientsCard`) que ya no existe |
| `AUDITORIA_…_2026-08-14.md` | 3 | Archivos que se renombraron después; histórico, correcto |
| `ARCHITECTURE_GUIDE.md` | 1 | Cita `HelpDeskManager-Unificacion/docs/adr/003-…` — el path real es `docs/adr/003-estructura-modulo-capa.md` |
| `MASTER_PROMPT_GEOLOCALIZACION_TABLA_KM.md` | 1 | `calcular_distancias_siges.py` (se renombró) |
| `CLAUDE.md` | 1 | `.claude/settings.local.json` existe en disco pero está fuera de git (esperado) |

Total 56 referencias rotas; las que importan son las 4 filas del medio (docs que un lector
tomaría como vigentes y no lo están) y el path de la guía.

---

## FASE 2 — Veredicto por sección

| Sección | 14/08 | 22/08 | Evidencia |
|---|---|---|---|
| §1 Principios | CUMPLE (indirecto) | CUMPLE (indirecto) | DIP por lint-imports; SRP aproximada por §4 |
| §2 Estructura | CUMPLE-CON-ADR | CUMPLE-CON-ADR | ADR-003/006; módulos nuevos siguen módulo→capa |
| §3 Capas | CUMPLE | **CUMPLE** | lint-imports 0 broken incl. 3 módulos nuevos |
| §4 Convenciones/tamaños | NO-CUMPLE (deuda parcial) | **CUMPLE-CON-ADR, PERO CON 75 VIOLACIONES NUEVAS** | El inventario del 14/08 está cubierto por ADR-017/020, pero desde entonces entraron 75 funciones >20 (13 de >30), 2 clases >200 y 1 archivo frontend >300 que los ADR no cubren; archivos backend >300 = 0 ✅ |
| §5 Dependencias | CUMPLE | **CUMPLE** | 0 imports de terceros en domain/application |
| §6 Errores | CUMPLE | **CUMPLE** | 112 handlers amplios, 0 silenciamientos reales |
| §7 Testing | NO-CUMPLE en mínimos (corregido el mismo día a 0 celdas) | **NO-CUMPLE** | 5 tests de integración rotos en `main`; infra global 68.3 % (<70); 9 celdas bajo mínimo, 3 de ellas `analisis_log_hp` (29–68 %); los gates solo corren unit |
| §8 Seguridad | CUMPLE-CON-1-HALLAZGO | **CUMPLE-CON-OBSERVACIONES** | 315/322 endpoints con authz (7 pre-auth/health); 0 XSS; 0 secretos; pip-audit limpio; 1 vuln npm transitiva; identificadores SQLite concatenados en `db3_merge.py` |
| §9 Versionado | CUMPLE-CON-DESVIACIÓN-NO-DOC | **CUMPLE-CON-ADR** | 30/30 convencionales; single-dev = ADR-023 |
| §10 Documentación | CUMPLE-CON-DESVIACIONES | **CUMPLE-CON-DESVIACIONES** | READMEs ✅, 32 ADR ✅; 4 docs vigentes con refs rotas/obsoletos + 1 path en la guía |
| §11 Rendimiento | CUMPLE-CON-DESVIACIONES | **CUMPLE-CON-ADR** | 0 listas sin Page fuera de ADR-021; N+1 5 hits, ninguno en hot path |
| §12 Checklist PR | N/A | N/A (ADR-023) | ítem "no warnings" del lint: 1 warning abierto |

---

## FASE 3 — Matriz sección × módulo

VERDE = cumple con evidencia · AMARILLO = desviación menor o cubierta por ADR · ROJO =
violación sin ADR con impacto real.

| Módulo | §2/3 | §4 tamaños | §5 | §6 | §7 cobertura | §8 | §11 |
|---|---|---|---|---|---|---|---|
| auth | VERDE | VERDE (6 funcs, 1 nueva) | VERDE | VERDE | VERDE (dom 99.7 / app 99.6 / infra 71.7 / pres 75.8) | VERDE (4 pre-auth por diseño) | VERDE |
| contadores | VERDE | AMARILLO (55 funcs; 7 nuevas; 3 de >50 en ADR-017) | VERDE | VERDE | AMARILLO (infra 74.2 ✅, pero 1 test de caracterización DB3 roto) | AMARILLO (`db3_merge.py` identificadores SQLite concatenados) | VERDE |
| insumos | VERDE | AMARILLO (109 funcs; 7 nuevas; clase 215 en ADR-017) | VERDE | VERDE | AMARILLO (infra 70.0 justo en el límite; app 87.0) | VERDE | VERDE |
| liquidaciones | VERDE | **ROJO** (89 funcs, **28 nuevas** desde ADR-016/017, 4 de >30; clase nueva `SqlAlchemyTablaKmRepository` 212 sin ADR; 1 anidamiento 4 nuevo) | VERDE | VERDE | **ROJO** (infra 68.0 <70 y 4 tests de integración rotos; dom 96.9 / app 91.5) | VERDE | VERDE (ADR-014/015) |
| prestadores | VERDE | VERDE (16, ninguna >50) | VERDE | VERDE | VERDE (infra 86.6 / pres 79.7) | VERDE | VERDE (ADR-011) |
| sla | VERDE | VERDE (10) | VERDE | VERDE | AMARILLO (app 66.5 <85; dom 100 / infra 86.2) | VERDE | VERDE |
| turnos | VERDE | AMARILLO (21 funcs; 8 nuevas, 1 de >30) | VERDE | VERDE | VERDE (infra 96.6 / pres 83.8) | VERDE | VERDE |
| vacaciones | VERDE | AMARILLO (34; 1 nueva) | VERDE | VERDE | AMARILLO (infra 65.1 <70; app 94.6) | VERDE | VERDE |
| **analisis_log_hp** (nuevo) | VERDE | **ROJO** (25 funcs, **19 nuevas**, 7 de >30 — módulo posterior a ADR-017, nada está cubierto) | VERDE | VERDE | **ROJO** (dom 68.0 / app 38.7 / infra 29.0 / pres 67.6) | VERDE | AMARILLO (6 `list[...]` = ADR-021) |
| **preventivos** (nuevo) | VERDE | VERDE (4 funcs 21–31) | VERDE | VERDE | AMARILLO (infra 48.3 <70; dom 96.8 / app 96.6) | VERDE | VERDE |
| **wati** (nuevo) | VERDE | VERDE (2) | VERDE | VERDE | AMARILLO (infra 62.0 <70; dom 98.3 / app 98.2) | VERDE | VERDE (polling por diseño) |
| shared | VERDE | AMARILLO (`create_app` 83 y `Settings` 219 — `create_app` en ADR-017, `Settings` no) | VERDE | VERDE | VERDE (dom 96.2 / infra 86.5 / pres 82.0) | AMARILLO (`/health/echo` sin auth, sin uso) | n/a |
| **frontend** | n/a | AMARILLO (11 archivos >300: 10 en ADR-020 o herederos, **1 nuevo** `use-inicio-data.ts`; componentes >50 líneas: 265, sin criterio en la guía) | VERDE (tsc 0) | n/a | 15 specs Playwright / 91 tests (UI con backend mock) — ADR-022 sigue vigente para e2e real | VERDE (0 XSS; 1 vuln npm transitiva) | n/a |

**Patrones sistémicos:**

1. **§4 se sigue violando en código nuevo** a pesar de ADR-017/020: 75 funciones nuevas >20
   en 8 módulos, con dos focos claros — `analisis_log_hp` (módulo entero portado después
   del ADR, 19 nuevas) y `liquidaciones` (28 nuevas: matching, geovalidación, sincronización).
   Es el mismo patrón de la semana pasada con otra fecha: el ADR congela, el código nuevo no
   lo respeta, y el gate que lo haría visible (un lint de tamaño) no existe.
2. **§7: la suite de integración está rota y no corre en ningún gate** — 5 fallos en `main`
   (4 por un cambio de dominio de liquidaciones no reflejado en los tests, 1 de
   caracterización del export DB3), invisibles porque `make check`/`pre-push` solo corren
   `tests/unit`. Y el módulo nuevo `analisis_log_hp` entró con un tercio de la cobertura
   que la guía exige — el patrón "módulo portado después de la auditoría = sin la red de
   tests del resto" se repite con `preventivos` y `wati`.
3. **Docs de planificación (`MASTER_PROMPT_*`) no se cierran**: cuando el plan se ejecuta de
   otra forma (INCIDENTES_SIN_CERRAR → `sla/pendientes-a-cerrar`) o no se ejecuta
   (NOTA_PERSONAL), el doc queda como si fuera vigente.

---

## FASE 4 — Hallazgos priorizados

| Sev | Sección | Módulo | Evidencia | Impacto | ¿ADR? | Acción |
|---|---|---|---|---|---|---|
| ALTO | §7/§9 | liquidaciones, contadores (+ proceso) | `pytest tests` (unit+integración): **5 FAILED** — `test_sqlalchemy_alerta_repository` ×3 y `test_sqlalchemy_resolucion_repository` ×1 (`AlertaGenerada` vs `AlertaConciliada`), `test_run_db3_export_end_to_end` (`'' == '20'`); `make check` y `pre-push` solo corren `tests/unit` | El gate que "garantiza" que cada commit pasa los tests no ve la integración; el fallo del DB3 puede ser una regresión real del export | No | (1) Arreglar los 4 tests de alertas (construir `AlertaConciliada`); (2) decidir si el export DB3 cambió a propósito (actualizar el test) o no (bug); (3) hacer correr integración en `make check` (conftest con host configurable + `helpdesk-db-test` levantado por el Makefile) |
| ALTO | §7 | analisis_log_hp (+ preventivos, wati, sla/app, vacaciones/infra, liquidaciones/infra) | `--cov`: analisis_log_hp app 38.7 / dom 68.0 / infra 29.0; preventivos infra 48.3; wati infra 62.0; sla app 66.5; vacaciones infra 65.1; liquidaciones infra 68.0; infra global 68.3 (<70) | Los 3 módulos posteriores a la auditoría anterior entraron sin la cobertura mínima; el módulo de análisis de logs HP (scraping de portal HP + snapshots) es exactamente el tipo de código frágil que §7 quiere proteger | No | Backlog dirigido: unit de use cases y dominio de analisis_log_hp primero (540+612 statements), integración de repos después; sla/application 200 statements = una tarde |
| ALTO | §4 | analisis_log_hp, liquidaciones (+ turnos, insumos, contadores) | AST vs snapshot 14/08: **75 funciones nuevas >20** (13 de >30), **2 clases >200 nuevas** (`Settings` 219, `SqlAlchemyTablaKmRepository` 212), 1 anidamiento 4 nuevo; `use-inicio-data.ts` 317 en frontend | ADR-017/020 valen solo si el código nuevo respeta el límite; hoy no pasa y nada lo detecta | No (los ADR cubren el inventario del 14–16/08, no esto) | (1) Agregar el límite como gate: ruff `PLR0915`/`C901` o un check AST en `make check` que compare contra el inventario congelado y falle con casos nuevos; (2) refactor de las 13 >30 líneas y las 2 clases al tocarlas |
| MEDIO | §10 | docs | 4 docs vigentes con refs rotas u obsoletas (INTEGRACION_APPS_PLAN 28, INCIDENTES_SIN_CERRAR 9, NOTA_PERSONAL 3, GEOLOCALIZACION 1) + path erróneo en ARCHITECTURE_GUIDE §2 | Quien lea el plan/prompt cree que describe el código actual; CLAUDE.md exige "cero alucinaciones" y los docs las inducen | No | Marcar cada MASTER_PROMPT ejecutado/descartado con un encabezado "Estado: ejecutado en X / reemplazado por Y / descartado"; corregir el path de la guía; INTEGRACION_APPS_PLAN → nota "histórico" |
| BAJO | §12/§9 | frontend (analisis-log-hp) | eslint: `hp-logs-panel.tsx:49` `sdsResult` sin usar (1 warning) | El gate `--max-warnings=0` de la auditoría falla; el `pre-push` no lo exige | No | Borrar la prop o usarla; considerar `--max-warnings=0` en `pre-push` |
| BAJO | §8 | frontend deps | `npm audit`: `nanoid` high (GHSA-2v37-7h3g-55p8, transitiva) | Vulnerabilidad en dependencia de build/dev-tooling; sin exposición directa conocida | No | `npm audit fix` y re-correr `tsc`/eslint |
| BAJO | §8 | contadores | `db3_merge.py:144,176,184` identificadores SQLite concatenados (`"{table}"`, `{col_str}`), origen: `sqlite_master` del DB3 bajado por FTP | Sin input de usuario; un DB3 malicioso podría romper la consulta; no es inyección explotable en la práctica pero contradice §8 literal | No | Escapar `"` en identificadores (o validar contra `^[A-Za-z0-9_]+$`) al tocar el archivo |
| BAJO | §8/§1 | shared | `POST /api/health/echo` sin auth y sin consumidor | Superficie inútil (YAGNI) | No | Borrar o dejar solo en `DEBUG` |
| BAJO (guía) | §4 | guía | 566 funciones TS >20 (489 componentes JSX), 265 >50; ni la guía ni ADR-020 dicen cómo se mide §4 en React | El número es inaplicable tal cual; sin criterio explícito cada auditoría lo reporta distinto | No | Una línea en la guía o un ADR: en componentes React §4 se mide por archivo (ADR-020) + "un componente no mezcla fetch, estado y layout" |

**No-hallazgos verificados** (cubiertos por ADR, se listan para que no se re-reporten):
inventario §4 del 14/08 (ADR-017) y del 16/08 frontend (ADR-020), `list[...]` del proxy
SDS/Insight (ADR-021), sin e2e automatizado real (ADR-022; los 91 tests Playwright actuales
corren con backend mock — son tests de UI, no e2e navegador→API→DB), commits >400 líneas y
sin PRs (ADR-023), resumen de prestadores no paginado (ADR-011), excepciones documentadas
de capas (ADR-007/009/010).

---

## Veredicto

**¿La app cumple ARCHITECTURE_GUIDE.md hoy? SÍ EN LO ESTRUCTURAL, CON DOS REGRESIONES
RESPECTO DEL 14/08 QUE HAY QUE CORREGIR.** Lo no opinable sigue limpio y medido: capas y
módulos 0 contratos rotos (con 3 módulos nuevos adentro), ruff/mypy/tsc en cero, 0 imports de
terceros en domain/application, 0 errores silenciados reales sobre 112 handlers, 315/322
endpoints con autorización (7 pre-auth/health por diseño), 0 XSS, 0 secretos, pip-audit
limpio, 0 listas sin `Page[T]` fuera de ADR, 0 archivos backend >300, READMEs y 32 ADR.
Cinco de los siete hallazgos del 14/08 siguen cerrados.

Lo que empeoró:

1. **§7 — la suite de integración está rota (5 FAILED en `main`) y ningún gate la corre**;
   `analisis_log_hp` entró con 29–68 % de cobertura y la infraestructura global bajó de
   78.6 % a 68.3 % (por debajo del mínimo).
2. **§4 — 75 funciones nuevas >20 líneas (13 de >30), 2 clases >200 y 1 archivo frontend
   >300 desde que ADR-017/020 congelaron el inventario** — el ADR dice "límite vigente para
   código nuevo" y nada lo hace cumplir.

Y un hallazgo nuevo de método: **4 docs vigentes describen cosas que no existen** (plan de
integración apuntando a los repos legacy, dos Master Prompts obsoletos, un path en la guía).

**Focos de mayor retorno:**

1. Arreglar los 5 tests de integración (4 son un cambio de constructor; el del DB3 exige
   decidir si hay regresión) y **meter la integración en `make check`** (conftest con host
   configurable, db-test levantada por el Makefile). Sin esto, §7 es unit-only de hecho.
2. **Gate de §4**: un check AST en `make check` que falle con cualquier función >20 / clase
   >200 / archivo >300 que no esté en el inventario congelado (ADR-017/020) — convierte el
   ADR en algo que se cumple solo.
3. Cobertura de `analisis_log_hp` a mínimo (use cases + dominio primero); `sla/application`
   es una tarde.
4. Docs: encabezado "Estado" en cada MASTER_PROMPT (ejecutado / reemplazado / descartado),
   nota "histórico" en `INTEGRACION_APPS_PLAN.md`, path corregido en la guía, y una línea en
   la guía sobre cómo se mide §4 en componentes React.
5. Limpieza chica: warning de eslint en `hp-logs-panel.tsx`, `npm audit fix` (nanoid),
   `/api/health/echo`, identificadores SQLite en `db3_merge.py`, partir
   `use-inicio-data.ts`.

---

## Addendum 2026-08-22 (misma jornada): lo que se corrigió en el acto

Solo lo que era propio de esta sesión o puramente documental; el resto queda como
hallazgo abierto para decidir (tests de integración, gate de §4, cobertura de
`analisis_log_hp`, `nanoid`, `hp-logs-panel.tsx`, `db3_merge.py`, `/health/echo`).

| Hallazgo | Acción |
|---|---|
| §4 frontend: `features/home/hooks/use-inicio-data.ts` 317 líneas (regresión del rediseño de Inicio de hoy) | Partido: la lógica de rango "hoy"/semana de Contadores pasó a `use-calendario-home.ts` (124); `use-inicio-data.ts` queda en 201. `tsc` + eslint en verde; `use-dashboard-data.ts` importa del archivo nuevo |
| §10: path erróneo en `ARCHITECTURE_GUIDE.md` §2 | Corregido a `docs/adr/003-estructura-modulo-capa.md` |
| §10: `MASTER_PROMPT_NOTA_PERSONAL_INICIO.md` describe una Home que no existe y una feature no hecha | Encabezado "Estado: NO implementado" con el contexto actual |
| §10: `MASTER_PROMPT_INCIDENTES_SIN_CERRAR_POR_PRESTADOR.md` describe un módulo `stc/` que no se construyó | Encabezado "Estado: reemplazado por `sla/pendientes-a-cerrar`" |
| §10: `INTEGRACION_APPS_PLAN.md` apunta a los repos legacy | Encabezado "Estado: histórico" |

---

## Addendum 2 (2026-08-22, misma jornada): corrección de los hallazgos

Todo lo ALTO/MEDIO de la Fase 4 y lo barato de lo BAJO, re-medido con los mismos comandos.

| Hallazgo | Acción | Antes → después |
|---|---|---|
| §7 suite de integración rota y sin gate | Los 4 tests de alertas construyen `AlertaConciliada` (ADR-024); el test de caracterización DB3 se actualizó al comportamiento deliberado de `3eb8a23` (el total de un modelo color no se duplica en la columna mono). `conftest` de integración lee `DB_TEST_HOST/DB_TEST_PORT`; `make test-integration` levanta `helpdesk-db-test`, lo une a la red del backend y corre `tests/integration` dentro del contenedor; **`make check` (y el `pre-push`) ahora corre unit + integración** | 5 FAILED → **0** (297 de integración en verde) |
| §7 cobertura bajo mínimo | Tests nuevos (solo `backend/tests/`, sin tocar `src`): `analisis_log_hp` unit de dominio/aplicación/infraestructura (fakes, `MockTransport`, stub de Anthropic) + integración de sus 3 repos; `sla/application` (3 use cases); `wati` y `preventivos` infra (gateways, mappers, query); `vacaciones` y `liquidaciones` infra (repos de ausencias/cargos/aprobaciones/auditoría/usuarios, descartes, caches reverse, coordenadas, preview KM; clientes Google Maps y Siges con fakes); `insumos/portal_parsing` | Total **82.3 → 86.8 %**; infra **68.3 → 81.2 %**; celdas bajo mínimo **9 → 0**; tests **2078 → 2403** (`analisis_log_hp` dom 68.0→97.9, app 38.7→99.3, infra 29.0→98.5; sla/app 66.5→100; wati/infra 62.0→90+; preventivos/infra 48.3→82+; vacaciones/infra 65.1→84.6; liquidaciones/infra 68.0→81.8) |
| §4 sin gate para código nuevo | `scripts/check_sizes.py` + `scripts/sizes-baseline.json` en `make check`; addendums en ADR-017/020; guía §4 "Cómo se mide en este repo" (React por archivo) | Sin gate → **gate en pre-push**; inventario 389 entradas congeladas (incluye lo que entró 14–22/08, documentado) |
| §12 warning eslint | Prop `sdsResult` sin usar quitada de `HpLogsPanel`/`HpLogsView` | `eslint src --max-warnings=0`: 1 warning → **0** |
| §8 `npm audit` nanoid high | `npm audit fix` (3.3.17 → 3.3.18) | 1 high → **0** |
| §8 identificadores SQLite en `db3_merge.py` | `_ident()` valida `^[A-Za-z0-9_]+$` antes de interpolar | — |
| §8/§1 `POST /api/health/echo` | Se conserva: es la sonda del envelope de validación que usa `test_error_handling.py`; documentado en el router | — |

Gates finales: `make check` → lint-imports 26/26 · ruff · mypy · **2106 unit** · **297 integración** · sizes ✔;
`tsc` + `eslint --max-warnings=0` en verde. Sigue abierto, a propósito: refactor oportunista de
las 13 funciones nuevas >30 líneas y las 2 clases >200 (cubierto por el addendum de ADR-017);
`analisis_log_hp/presentation` 67.6 % está sobre el mínimo pero sin tests propios de router.

---

## Addendum 3 (2026-08-22): refactor §4 de lo que entró sin gate + tests de router

- Las **13 funciones nuevas >30 líneas** y las **2 clases >200** de la Fase 1 quedaron bajo
  el límite, sin cambiar firmas públicas ni contratos: `_capture_one` 48→15, `search_device`
  43→14, `refresh_hp_cache` 42→16, `preview_analysis` 37→15, `diff_two_snapshots` 37→19,
  `bulk_update_solution_urls` 32→17 (analisis_log_hp); `_reconciliar` 41→18,
  `_sincronizar_prestador` 32→19 (anidamiento 4→3), `execute` 54→18, `_armar_fila` 37→18,
  `_guardar` 31→19 (5→2 params), `update_distancias` 36→24 (resto es la firma del Protocol),
  clase `SqlAlchemyTablaKmRepository` 212→177 (liquidaciones); `detect_sucursal_override`
  39→17 (insumos); `_bajas` 36→6 con SQL compilado idéntico (turnos); clase `Settings` 219→16
  vía mixins por tema en `settings_groups.py`, con `model_fields`/`model_config` verificados
  idénticos antes/después (113 campos, mismos nombres de entorno).
- `analisis_log_hp/presentation` tiene tests de router propios
  (`tests/integration/test_analisis_log_hp_routers.py`, 14 casos: 401/403 por router, 400
  `VALIDATION_ERROR`, caminos felices con fakes) → 75.0 %.
- Gates: `make check` → 26/26 contratos · ruff · mypy · **2121 unit** · **316 integración** ·
  sizes ✔ (inventario podado a 372, ver ADR-017). Cobertura por módulo igual o mayor
  (liquidaciones infra 81.8→84.9, analisis_log_hp infra 98.5→98.9).

---

## Addendum 4 (2026-08-22): deuda §4 de complejidad real saldada; gate sobre HEAD/staged

- **Backend**: las 11 funciones >50 líneas → todas ≤30 (`export_meters_to_csv` SDS 106→27 y
  ERS 85→30 con `sds_export.py` + `auto_csv_writer.py` compartido; `refresh_ers_token` 65→16;
  `sync_pending` 67→4; `preview_zone_contacts` 65→17; `_row_from` 58→25; `delete/verify
  _offline_devices._run` 55→12 / 52→15; `create_app` 83→10 con 326 rutas y middlewares
  verificados idénticos; `EditarSolicitud.execute` 52→11); las 2 clases >200 → 122 y 94; los 3
  anidamientos >3 → ≤3; SQL compilado verificado idéntico donde aplicaba. Tests agregados
  antes de refactorizar donde faltaban (+~50). Cobertura por módulo igual o mayor
  (contadores infra 77→83, insumos 83→85 total).
- **Frontend**: los 10 archivos >300 partidos por extracción pura (máx. ahora 242); tsc,
  eslint estricto y Playwright (suite completa) en verde.
- **Gate**: `check_sizes.py --committed` en `make check` (HEAD, lo que se pushea) y `--staged`
  en el pre-commit; el árbol de trabajo queda para `make sizes-wip`. Inventario: 389 → **340
  funciones de 21–47 líneas; 0 clases, 0 archivos** (ADR-017/020 actualizados).
- Gates finales: lint-imports 26/26 · ruff · mypy · 2166 unit · 332 integración · sizes ✔.

---

## Addendum 5 (2026-08-22): gate §6/§8/§11 y specs Playwright stale

- **`scripts/check_guards.py`** en `make check` (HEAD) y en el pre-commit (staged): `except`
  silencioso (sin relanzar, loguear ni delegar en un handler con nombre), SQL por f-string o
  concatenación, literales tipo secreto, `print(`/`console.log(`, `dangerouslySetInnerHTML`,
  endpoints `list[...]` sin `Page[T]` y endpoints sin authz. Inventario aceptado
  (`scripts/guards-baseline.json`, 23 entradas): los 6 passthrough de ADR-021, los 7 pre-auth/
  health, los 9 f-strings con constantes/`int()`/identificadores validados. Cero casos nuevos
  en HEAD. La guía §6 tiene la nota "cómo se verifica en este repo".
- **Playwright**: los 3 specs que fallaban en `main` eran stale, no regresión: el commit
  `04f9cc8` (21/08, paginación `Page[T]` de sucursales-propia/matching-propuestas, §11) cambió
  el contrato y los mocks seguían devolviendo arrays pelados. Corregidos los mocks
  (`tabla-km-wizard.spec.ts`, `prestadores-distancias.spec.ts`); 4/4 en verde. Queda como
  lección: los specs con backend mock no ven los cambios de contrato hasta que alguien corre la
  suite — correrla forma parte del cierre de cualquier cambio de API que consuma el frontend.

---

## Addendum 6 (2026-08-22): tests de router para wati, preventivos, sla y turnos

~120 tests de integración nuevos (`tests/integration/{test_wati_router,test_preventivos_router}.py`,
`tests/integration/sla/`, `tests/integration/turnos/`, helper `router_testing.py`), mismo patrón
que los de analisis_log_hp: 401 sin sesión, 403 por permiso/feature exacto, caminos felices
con contrato (`Page[T]`, aliases), 400/404/409. Cobertura de `presentation` en los 4 módulos:
92 → 96 % de líneas; routers de wati/preventivos/sla y los 6 de turnos al 100 %. Quedan fuera
a propósito: factories reales contra WATI/MERCURIO y `background_jobs.py`. Dos observaciones
de contrato anotadas en los tests (no cambiadas): `GET /api/sla/resumen?periodo=202613` devuelve
400 `PERIODO_INVALIDO` (VO) y no `VALIDATION_ERROR`; `PUT /api/turnos/casillas/{id}` inexistente
lanza `ValueError` sin mapear (sería 500) — candidato a 404 en el próximo toque del router.

---

## Addendum 7 (2026-08-22): contratos anotados y smoke de Playwright en el pre-push

- `PUT /api/turnos/casillas/{id}` inexistente: el use case lanzaba `ValueError` (500); ahora
  `CasillaNotFoundError` (dominio, `NotFoundError` → 404 `CASILLA_NOT_FOUND`), con test de
  router.
- `GET /api/sla/resumen?periodo=202613`: decisión — queda como está. El borde valida el rango
  numérico (`Query(ge/le)`); que el mes sea 1–12 es regla del VO `Periodo` y se devuelve como
  400 `PERIODO_INVALIDO`, un código de dominio que el frontend puede mostrar; convertirlo en
  `VALIDATION_ERROR` duplicaría la regla en el borde sin ganancia. Documentado en el test.
- **Smoke de Playwright en el pre-push** (solo con cambios en `frontend/`): un test por spec
  etiquetado `@smoke` (15), el hook levanta un `next dev` de test en 3011 (o reusa uno), corre
  `playwright test --grep @smoke` y lo apaga. Cierra el único gate que faltaba: un cambio de
  contrato de API que rompa la UI ya no pasa en silencio. La suite completa sigue siendo
  a mano al cerrar cambios de API que consume el front (CLAUDE.md actualizado).

---

## Addendum 8 (2026-08-23): decisiones cerradas sobre lo que quedaba "abierto"

Pedido del usuario: que nada quede como pendiente difuso. Cada punto tiene ahora una decisión
escrita en su lugar:

| Tema | Decisión | Dónde |
|---|---|---|
| "Defaults de Inicio por rol" | **No hace falta**: qué ve cada perfil ya lo decide la administración de usuarios (módulos + funciones por usuario, ADR-032); Personalizar es solo la capa personal encima | ADR-033, Consecuencias |
| Deuda §4 restante (340 funciones 21–47 líneas) | **Cerrada como deuda aceptada**: sin barrido en bloque; gate impide casos nuevos; refactor oportunista al tocar el archivo | ADR-017, "Decisión final" |
| 23 excepciones del gate §6/§8/§11 | **Aceptadas con justificación por tipo** junto al inventario; regla: agregar una entrada es una decisión escrita, no un atajo | `scripts/guards-baseline.json` → `notes` |
| Suite e2e real | **No se construye ahora**: red = integración + routers por HTTP + smoke UI en pre-push + suite completa manual + verificación en navegador al cerrar cada bloque; única vía de cambio: cláusula de reversión de ADR-022 | ADR-022, addendum 2026-08-23 |
| `GET /api/sla/resumen?periodo=` inválido | **Queda `PERIODO_INVALIDO`** (código de dominio); el frontend muestra el `message` del envelope igual que cualquier 400 | Addendum 7 + test |
| Cobertura: `sla/pendientes_router` 89 % y `background_jobs.py` 0 % | Ramas de superadmin cubiertas con 2 tests (89 → 96 %); los jobs de fondo **quedan sin cobertura por regla** (no se ejecutan en dev; su lógica vive en use cases testeados) | tests + ADR-022 addendum |
