# Optimización y cumplimiento de ARCHITECTURE_GUIDE.md

**Última pasada:** 2026-08-16 (2ª corrida; incluye el commit `c51dea2` del card registry)
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

## 3. Incumplimientos de la guía pendientes (requieren decisión o trabajo)

### 3.1 Deuda §4 **nueva**, fuera del inventario congelado de ADR-017 — PRIORIDAD ALTA

ADR-017 §5: todo caso posterior al inventario del 2026-08-14 "es violación, no deuda".
Ambos archivos crecieron/nacieron después de esa fecha:

- `backend/src/modules/contadores/presentation/calendario_router.py` — **352 líneas**
  (creció con `get_pending_clients`, portfolio por operador y overrides de coberturas).
  Acción: separar por responsabilidad (p. ej. router de calendario vs. router de
  coberturas/portfolio) como ya hace liquidaciones con `config_routers/`.
- `backend/src/modules/liquidaciones/application/use_cases/tabla_km_lugares.py` — **302
  líneas** (módulo geo nuevo, posterior a la auditoría). Está apenas sobre el límite:
  extraer helpers compartidos con `_distancias_comunes.py` o partir preview/apply.

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

### 3.2 §11 + tipado en `analisis_log_hp/presentation/sds_router.py` — PRIORIDAD MEDIA

Seis endpoints devuelven `list[dict[str, Any]]` sin `Page[T]` ni schemas Pydantic:
`/devices/{id}/consumables`, `/alerts`, `/meters`, `/hp-operations`, `/clients`,
`/clients/{id}/devices`. No hay ADR que lo cubra — per CLAUDE.md, excepción sin ADR es
violación. Los cinco por-device son sub-recursos acotados por el equipo (candidatos a un
ADR estilo 011), pero `/clients` es el catálogo de clientes de la flota completa y
`dict[str, Any]` en presentation esquiva la validación de salida. Acción: escribir el ADR
que delimite la excepción para los sub-recursos por device **y** tipar/paginar `/clients`.

### 3.3 Tamaños §4 del frontend sin inventario equivalente a ADR-017 — PRIORIDAD MEDIA

ADR-017 cubre solo `backend/src`. En `frontend/src` hay **15 archivos >300 líneas** sin
registro de deuda; los peores:

| Archivo | Líneas |
|---|---|
| `features/insumos/components/dashboard/consumable-detail-modal.tsx` | 459 |
| `features/insumos/components/shared/date-range-picker.tsx` | 450 |
| `features/turnos/components/admin/casillas-manager.tsx` | 428 |
| `features/liquidaciones/api/liquidaciones-api.ts` | 412 |
| `features/contadores/components/client-picker-process-modal.tsx` | 395 |

Acción: o se extiende ADR-017 al frontend con este inventario congelado (misma lógica:
código portado y verificado, refactor oportunista), o se abre workstream de split. Lo
primero es coherente con lo ya decidido para backend. `liquidaciones-api.ts` (412) es el
más mecánico de partir: un archivo por sub-recurso (liquidaciones / config / distancias /
pines), espejando `config_routers/` del backend.

### 3.4 Seguridad §8 — revisado, sin hallazgos

Barrido de SQL construido por string: los únicos f-strings en queries son constantes de
módulo (`ftp_client_model.py`), un `int()` casteado (`sqlalchemy_supply_cache_repository
.py:152`) y lecturas de un SQLite local bajado por FTP con identificadores citados
(`ftplib_db3_downloader.py`) — nada recibe input de usuario. Sin secretos hardcodeados en
`backend/src`.

### 3.5 Observaciones sobre el card registry del dashboard (`c51dea2`) — PRIORIDAD BAJA

El refactor es correcto (gates verdes, sin bugs funcionales), pero quedaron tres puntas:

1. **`COLUMNS[].fraction` es dato muerto**: el grid sigue hardcodeado en la clase Tailwind
   `xl:grid-cols-[1.4fr_1fr_0.9fr_0.9fr]` y el registry solo lo "documenta" con un
   comentario de "deben coincidir" — exactamente la duplicación que el registry venía a
   eliminar. Generar `gridTemplateColumns` inline desde las columnas **visibles** resuelve
   la duplicación y de paso el punto 2.
2. **Tracks fantasma con permisos parciales** (preexistente al refactor): el template
   declara 4 tracks fijos; si un usuario no ve `contadores`/`sla`, las columnas visibles
   se corren a tracks con fracciones que no les corresponden y queda un track vacío al
   final.
3. `CARDS` se importa en `inicio-dashboard.tsx` pero no se usa (solo lo usa `cardsForCol`
   internamente), y el cast `key as ColKey` es innecesario (`key` ya tipa `ColKey`).

## 4. Optimizaciones recomendadas (accionables, con evidencia)

### 4.1 Cobertura: `pines_sospechosos.py` tiene **cero tests** — PRIORIDAD ALTA

`grep CorregirPin|AuditarPines|ListarPinesSospechosos backend/tests` → sin resultados. El
bug del §2.1 (endpoint que revienta al primer uso) atravesó 1355 tests unitarios en verde.
Es exactamente el caso que la cobertura mínima de application (≥85%, §7 de la guía) debía
prevenir, y el flujo toca la Google key paga (tope de llamadas, cache-first): merece tests
de la lógica de tope/cache (`AuditarPines` no llama a Google si está en cache, respeta
`tope_llamadas`, `CorregirPin` exige geocode cacheado). Todos los puertos son Protocols —
fakes in-memory triviales.

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
