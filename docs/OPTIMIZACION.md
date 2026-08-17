# Optimización y cumplimiento de ARCHITECTURE_GUIDE.md

**Última pasada:** 2026-08-16 (7ª corrida: §10 READMEs + README raíz corregido)

**Hallazgos 7ª corrida**: (1) el README raíz afirmaba que había hot-reload por
volúmenes — contradiciendo la decisión post-incidente de CLAUDE.md y sugiriendo el
`--reload` que causó el mail real del 2026-08-12; corregido, más rutas de docs
actualizadas a `docs/`. (2) Creados `backend/README.md` y `frontend/README.md`
(template §10) — cierra el hallazgo BAJO §10 de la auditoría. (3) Los 8 endpoints
BAJO §11 de la auditoría (customers, catálogos auth, /periodos) ya estaban paginados
desde la corrección del 08-14 — verificado; el único stray restante era
`GET /analysis/models`, sin consumidor en el frontend. **Resuelto mismo día**: se
borraron los dos endpoints huérfanos (`GET /clients` y `GET /analysis/models`) con
sus cadenas completas (use cases, métodos de puerto, implementaciones y entradas del
API client del frontend). Con esto no queda ningún endpoint de colección fuera de
§11 sin ADR.

**Estado §4 al cierre de la 6ª corrida**: todas las métricas en o por debajo de los
inventarios congelados — funciones >50: 10/10 de ADR-017 · clases >200: 2/2 ·
archivos >300 backend: solo los 3 de ADR-017 · anidamiento >3: los 4 de la línea de
base (los 3 nuevos se refactorizaron: `html_to_tsv` y `extract_help_urls` con
helpers de extracción, `_calcular_filas` con `_procesar_batch`; de paso cayó otro
`except Exception` silencioso interno en `html_to_tsv`, §6). Suite completa:
1382 tests en verde.
**Método:** gates obligatorios dentro de los contenedores (`lint-imports`, `ruff`, `mypy`,
`pytest tests/unit`, `tsc`, `eslint`) + medición AST de §4 (funciones/clases/anidamiento,
excluyendo migraciones) + revisión manual de `except Exception` (§6), endpoints de
colección (§11) y SQL/secretos (§8), contrastado contra los ADRs vigentes (011, 016, 017)
y el inventario congelado de `AUDITORIA_ARCHITECTURE_GUIDE_2026-08-14.md`.

---

## 1. Estado de los gates (2026-08-16, tras los fixes de esta pasada)

| Gate | Resultado |
|---|---|
| `uv run lint-imports` | 22/22 contratos KEPT |
| `uv run ruff check src tests` | limpio |
| `uv run mypy src` | limpio (1144 archivos) |
| `uv run pytest tests/unit -q` | 1355 pasan |
| `npx tsc --noEmit` (frontend) | limpio |
| `npx eslint src --quiet` (frontend) | limpio |

## 2. Bugs encontrados y corregidos en esta pasada

1. **`CorregirPin` roto en runtime** —
   `liquidaciones/application/use_cases/pines_sospechosos.py:202` llamaba a
   `upsert_pendiente` sin el argumento keyword-only obligatorio `prestador_id`: el endpoint
   de corregir un pin sospechoso (flujo Tabla KM / Distancias) tiraba `TypeError` al primer
   uso real. Detectado por mypy; **ningún test lo atrapó** (ver §4.1).
2. **`analysis-collapsibles.tsx` (`ConsumablesPanel`)** — `setLoading(true)` sincrónico
   dentro del `useEffect` (error eslint `react-hooks/set-state-in-effect`) y además mostraba
   consumibles del equipo anterior mientras refetcheaba al cambiar `deviceId`. Reescrito:
   `loading` derivado del estado, resultado atado al `deviceId` que lo produjo, cleanup de
   requests en vuelo.
3. **`analisis_log_hp/infrastructure/hp_portal/html_parser.py:34`** — `except Exception:
   pass` silencioso (violación literal §6). Ahora loguea a nivel debug con `exc_info` antes
   del fallback a CDATA.
4. **E501** en `liquidaciones/presentation/liquidaciones_router.py:169` (docstring 101
   chars).
5. **BOM UTF-8** en `liquidaciones/presentation/dependencies/siges.py` — único archivo
   del repo con BOM; Python lo tolera pero rompe herramientas que parsean el fuente (el
   script AST de auditoría falló ahí). Removido.

## 2.b Hallazgos de la 4ª corrida (2026-08-16)

1. **Secretos hardcodeados en `settings.py` (§8, CRÍTICO) — corregido, falta rotar.**
   Tres pares de credenciales reales commiteadas como defaults: `sds_api_key/secret`
   (Insight de contadores), `insight_api_key/secret` (Insight de insumos) y
   `epson_ers_username/password`. Los dos pares de Insight **ni siquiera estaban en
   `.env`**: la app corría con el default del código. Fix aplicado: valores movidos a
   `.env` (git-ignored, verificado), defaults blanqueados en `settings.py`, backend
   recreado y verificado. **Pendiente para el usuario: rotar las tres credenciales en
   sus portales — los valores viejos quedan para siempre en el historial de git.**
2. **`.env.example` desincronizado (§12)**: 23 variables de `Settings` sin documentar,
   incluida `DISABLE_BACKGROUND_JOBS` (el freno de seguridad de CLAUDE.md) y
   `GOOGLE_MAPS_API_KEY`. Sincronizado completo (verificado por diff contra
   `Settings.model_fields`); secretos como placeholder vacío, defaults como comentario.
3. **Migraciones (§12/ADR-002) — sin violaciones**: de 61 migraciones, las únicas dos
   con `downgrade` vacío son el baseline (upgrade también vacío, revisión bandera) y
   `60ee5fdc4225_backfill_app_user_color` (irreversibilidad deliberada y documentada
   en el propio archivo).
4. **Higiene §12 — limpio**: sin `console.log`/`debugger` en `frontend/src`, sin
   `print()` en `backend/src`, sin catches vacíos en el frontend.

## 3. Incumplimientos de la guía pendientes (requieren decisión o trabajo)

### 3.1 Deuda §4 **nueva**, fuera del inventario congelado de ADR-017 — RESUELTO PARCIAL 2026-08-16

Los dos archivos >300 se partieron (verificado: rutas OpenAPI idénticas antes/después):

- `calendario_router.py` (352) → aggregator de 20 líneas + paquete `calendario_routers/`
  (`eventos`, `sync`, `clientes_siges`, `overrides`, `_deps`), espejando el patrón
  `config_routers/` de liquidaciones.
- `tabla_km_lugares.py` (302) → 202 líneas; `RefrescarDatosSiges` y sus DTOs se movieron
  a `tabla_km_refrescar_siges.py` (sync de datos maestros ≠ operaciones por fila).

**Cerrado 2026-08-16 (5ª corrida)**: las 6 funciones >50 y la clase >200 nuevas se
refactorizaron — `evaluate_device_health` partido en una regla por helper
(`_rule_post_repair`/`_rule_recurrence`/`_rule_stable`), `analyze_events` con
`_build_incident`/`_max_severity`, `calculate_trend` con `_empeoro`/`_mejoro`,
`backfill_estado.execute` con `_backfill_prestador`/`_estados_ayc`/`_aplicar_estado`,
`RefrescarDatosSiges.execute` con `_indice_siges`/`_actualizar_fila`, y el `create`
del repo de tabla_km como passthrough `**campos` (la firma tipada vive en el puerto,
mismo criterio que su fake). La medición AST volvió exactamente al inventario
congelado de ADR-017 (10 funciones >50, 2 clases >200). Los tres servicios de dominio
de analisis-log-hp no tenían **ningún** test — se agregaron 15 tests de
caracterización (`tests/unit/domain/analisis_log_hp/`) como red del refactor.

**Medición AST 2026-08-16** (mismo criterio que la auditoría, sin migraciones) vs. línea
de base del 2026-08-14 — la brecha es deuda nueva o no inventariada:

| Métrica | Baseline 08-14 | Hoy | Nuevos |
|---|---|---|---|
| Funciones >50 líneas | 10 | 16 | 6 |
| Clases >200 líneas | 2 | 3 | 1 (`SqlAlchemyTablaKmRepository`, 229) |
| Anidamiento >3 | 4 | 7 | 3 |

Las 6 funciones >50 nuevas: `evaluate_device_health` (77), `backfill_estado_liquidaciones
.execute` (73), `analyze_events` (62), `calculate_trend` (57), `SqlAlchemyTablaKmRepository
.create` (55), `tabla_km_lugares.execute` (52). Las tres de `analisis_log_hp` no figuran
en ningún conteo de ADR-017 (el módulo no aparece en su desglose por módulo): son
inventario faltante, conviene incorporarlas explícitamente a la ADR o refactorizarlas.
Nota: el conteo total de funciones >20 dio 326 vs. 247 del baseline, pero sin el script
original de la auditoría la comparación fina no es 1:1 (criterios de span pueden diferir);
el tier >50 sí coincide nombre por nombre con el inventario de ADR-017, así que la tabla
de arriba es comparable.

### 3.2 §11 + tipado en `analisis_log_hp/presentation/sds_router.py` — RESUELTO 2026-08-16

Documentado en **ADR-021**: los seis endpoints son proxies de lectura de HP Insight
(shape del sistema externo, sin transformación ni persistencia propia), acotados por
equipo o por el tamaño del negocio — se exceptúan de `Page[T]` y schemas con condiciones
de reversión explícitas. Hallazgo adicional: `GET /clients` no tiene ningún consumidor
en `frontend/src` — el ADR fija que si sigue huérfano en la próxima auditoría, se borra
(YAGNI) en vez de mantenerlo exceptuado.

### 3.3 Tamaños §4 del frontend sin inventario equivalente a ADR-017 — RESUELTO 2026-08-16

Dos partes:

- **ADR-020** extiende el criterio de ADR-017 al frontend con el inventario congelado de
  14 archivos >300 líneas (refactor oportunista; todo caso nuevo es violación).
- `liquidaciones-api.ts` (412, el más mecánico) se partió en sub-clientes por
  responsabilidad espejando los routers del backend: `liquidaciones-core-api.ts`,
  `config-api.ts`, `siges-api.ts`, `geolocalizacion-api.ts` + `_shared.ts`
  (`fetchCatalogoCompleto`/`Page`). `liquidaciones-api.ts` queda como aggregator que
  conserva el contrato para los consumidores existentes.

### 3.4 Seguridad §8 — revisado, sin hallazgos

Barrido de SQL construido por string: los únicos f-strings en queries son constantes de
módulo (`ftp_client_model.py`), un `int()` casteado (`sqlalchemy_supply_cache_repository
.py:152`) y lecturas de un SQLite local bajado por FTP con identificadores citados
(`ftplib_db3_downloader.py`) — nada recibe input de usuario. Sin secretos hardcodeados en
`backend/src`.

### 3.5 Observaciones sobre el card registry del dashboard (`c51dea2`) — RESUELTO 2026-08-16

Las tres puntas del refactor se corrigieron: el grid ahora se arma con
`grid-template-columns` desde las fractions de las columnas **visibles** del registry
(vía variable CSS + variante `xl:`), lo que elimina tanto la duplicación
registry/Tailwind como los tracks fantasma con permisos parciales; y se limpiaron el
import de `CARDS` sin uso y el cast innecesario `key as ColKey`.

## 4. Optimizaciones recomendadas (accionables, con evidencia)

### 4.1 Cobertura: `pines_sospechosos.py` tenía **cero tests** — RESUELTO 2026-08-16

`test_pines_sospechosos.py`: 12 tests con los fakes in-memory existentes de
`fakes_geolocalizacion.py`. Cubren la lógica que toca la Google key paga (`AuditarPines`
cache-first, respeta `tope_llamadas`, no audita sucursales sin pin), el umbral y orden de
`ListarPinesSospechosos` (que nunca llama a Google), y `CorregirPin` (guarda el override
con `prestador_id` y `PROCEDENCIA_GEOCODE` — el caso que hubiera atrapado el bug del
§2.1 — y falla sin geocode cacheado o con sucursal inexistente).

### 4.2 Refactor oportunista pendiente (ADR-017 punto 2)

Las 10 funciones >50 líneas del inventario siguen sin tocarse (verificado: ninguna bajó).
Regla vigente: la próxima edición de cualquiera de ellas debe bajarla del límite. Vale
recordarlo especialmente para `export_meters_to_csv` (SDS 106 líneas) si el cutover del
Printer-Logs-Analyzer la toca.

### 4.3 `sla/presentation/background_jobs.py` sigue en 0% de cobertura

Arrastrado de la auditoría 2026-08-14. Probar jobs de fondo requiere el cuidado especial
de CLAUDE.md (modo test, sin mails reales); cuando se planifique, hacerlo con los puertos
mockeados y `DISABLE_BACKGROUND_JOBS=true` verificado.

### 4.4 Suite e2e inexistente (§7)

Sigue abierta la decisión producto/ADR (hallazgo MEDIO de la auditoría). La pirámide §7
pide 5–10% e2e; hoy es 0. Mínimo viable: un smoke e2e de login + una pantalla por módulo
contra los contenedores, corrido a demanda (no en cada CI) mientras no haya pipeline.

## 5. Qué NO se recomienda tocar

- **Refactor en bloque del inventario ADR-016/017**: decidido y justificado — riesgo de
  regresión sin ganancia real.
- **Performance de queries/endpoints**: sin profiling previo no hay evidencia de ningún
  hotspot (§11: "medir antes de optimizar"). No se detectó ningún N+1 en los repos
  revisados en esta pasada; si aparece un síntoma real (p. ej. dashboard lento), medir
  primero con logs de SQLAlchemy echo o `EXPLAIN ANALYZE`.
- **Los `list[...]` de `background_jobs.py` y helpers internos** listados por grep de
  §11: la regla aplica a endpoints HTTP, no a funciones internas que devuelven listas.
