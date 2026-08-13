# Estado de la migración — Liquidacion-Prestadores

Ver `LIQUIDACION_PRESTADORES_CARACTERIZACION.md` para el reconocimiento funcional previo
(motor de reglas, alcance, decisión de dejar WS AyC afuera). Este doc trackea el avance
del port en sí — qué está hecho, verificado y committeado, y qué falta.

**Este archivo estaba desactualizado hasta 2026-08-13** (decía "Frontend — nada
arrancado todavía" de un corte anterior a la sesión que portó el frontend completo).
Reescrito de punta a punta ese día junto con la carga de datos reales — ver
`INTEGRACION_APPS_PLAN.md` §Fase 3 como fuente de verdad complementaria del checklist
de alto nivel.

Regla del proyecto para este módulo (pedido explícito del usuario): **no tocar el
contenedor Docker de la app legacy sin permiso**. El trabajo de port corre contra
`helpdesk-manager-backend` únicamente; para extraer datos del legacy se usa la API de
backup de SQLite en modo lectura (`sqlite3.Connection.backup()`), nunca escritura.

## Hecho (verificado con ruff + mypy + lint-imports + pytest, committeado)

1. **Modelo de datos** — 10 entidades de dominio + modelos SQLAlchemy + 2 migraciones
   Alembic (`b74bde547b01`, `0468811de473`), aplicadas a `helpdesk-db`.
2. **Motor de reglas** — port a dominio (`domain/services/motor_reglas/`) de 7 de los 9
   evaluadores ALT001-009 del legacy, con 33 tests de caracterización
   (`tests/unit/domain/liquidaciones/test_motor_reglas.py`). ALT005 quedó
   inicialmente incompleto (solo el camino de grupo) — **ya cerrado el 2026-08-13**,
   ver más abajo.
3. **Repositorios** — 10 Protocols + implementaciones SQLAlchemy.
4. **Casos de uso** de lectura, importación y reanálisis (no de escritura de config —
   ver pendientes).
5. **Endpoints HTTP** — 8 de liquidaciones + 23 de configuración (prestadores, SPSTs,
   tarifarios, tabla KM), todos con paginación `Page[T]`.
6. **Importación CSV/HTML** — parsing puro en dominio + `PandasLiquidacionFileParser`
   en infraestructura, endpoint `POST /api/liquidaciones/importar`.
7. **Frontend completo** — dashboard, lista, detalle, 4 pantallas de configuración,
   submenú en el sidebar, 12 tests e2e Playwright.
8. **729 tests unit en todo el backend** (120 propios de liquidaciones) verdes.

## Datos reales de producción cargados (2026-08-13)

Script `backend/scripts/migrate_liquidaciones_data_from_sqlite.py` (table-driven, specs
en `_migrate_liquidaciones_specs.py`), corrido una sola vez contra un snapshot
read-only fresco del contenedor productivo `liquidacion-prestadores-backend-1`
(`sqlite3.Connection.backup()`, nunca `cp` en caliente). El snapshot no se commiteó al
repo — vivió en el scratchpad de la sesión y se descartó después de correr el script.

Filas migradas (coinciden exactamente con el origen, verificado por conteo y por suma
de control `SUM(total_importe)`/`SUM(costo_total_cobrado)`, ambas $88.122.832,65 con
diferencia de precisión de punto flotante despreciable):

`prestadores` 35 · `spsts` 49 · `tarifarios` 4832 · `tabla_kms` 1633 ·
`liquidaciones` 34 · `incidentes` 1750 · `alertas` 746 · `resoluciones` 0 ·
`observaciones` 20 · `observacion_incidentes` 47.

`reglas_alerta` (9 filas) **no** viene del script de datos — se siembra por Alembic
(`17663a83c3fd_seed_liquidaciones_reglas_alerta.py`), porque es catálogo, no dato
transaccional. **Sembrada con el estado real de producción, no con el default de
`seed.py` legacy**: `ALT005` y `ALT007` activas (`seed.py` las tiene en `False`),
`ALT006` inactiva. Ver la migración para el detalle — la caracterización original
(`LIQUIDACION_PRESTADORES_CARACTERIZACION.md` §3/§7) asumía ALT005 desactivada; eso
quedó desactualizado, corregido ahí también.

Detalles técnicos de la migración de datos, para si hay que repetirla:
- IDs `INTEGER` autoincrement del legacy → `UUID` nuevos generados en Python,
  remapeados en las 12 FKs vía diccionario `{tabla: {id_legacy: uuid_nuevo}}`
  construido en orden topológico.
- Timestamps naive de SQLite (`CURRENT_TIMESTAMP`, siempre UTC) se etiquetan `UTC`
  explícitamente al insertar en columnas `timestamptz` — dejarlos naive corre el
  histórico 3 h.
- `alertas.datos_contexto` trae dos claves con IDs legacy embebidos en el JSON
  (`spst_id` de ALT005, `liquidaciones_previas` de ALT004) — se remapean a los UUIDs
  nuevos; si el legacy ya no tiene ese id (liquidación borrada desde entonces), se
  omite del array en vez de fallar.
- El legacy usa `create_all()` (sin Alembic) — 12 columnas `ayc_*`/WS declaradas en los
  modelos del working tree **no existen físicamente** en la SQLite real; el script
  valida contra `PRAGMA table_info` antes de seleccionarlas.
- Insert en un único `flush()` por tabla (mismo transacción, sin commit intermedio) —
  necesario para forzar el orden de INSERT; confiar en que SQLAlchemy infiera el orden
  topológico solo produjo violaciones de FK en la primera corrida.
- No idempotente a propósito: aborta si el destino ya tiene filas.

## Módulo activado (2026-08-13)

`liquidaciones.is_enabled` pasó a `true` vía Alembic
(`a000363bd8cd_activate_liquidaciones_module.py`, mismo patrón de dos pasos que
insumos/contadores/prestadores), **después** de cargar y verificar los datos —
`require_permission` da 403 en todo el módulo mientras está deshabilitado, incluso
para superadmin, así que no había forma de probar los endpoints antes de este paso.

## Verificación end-to-end hecha tras activar (2026-08-13)

- Los 4 catálogos paginados (`/prestadores`, `/tarifarios`, `/spsts`, `/tabla-km`)
  responden `Page[T]` con `total` correcto.
- **Fidelidad del motor contra datos reales** — la liquidación `3876-6` (111 incidentes)
  tenía 111 alertas `ALT001` migradas del legacy; tras `POST .../reanalyze`, el motor
  nuevo generó exactamente 111 `ALT001` — coincidencia exacta.
- Smoke test de importación con un `.xls` real del legacy
  (`liquidacion_3739-6_20260206.xls`, PENTACOM, enero 2026): `201 Created`, 107
  incidentes, 8 alertas, 2 observaciones — número de liquidación, período y tipo
  correctamente parseados del nombre de archivo.
- Verificación visual (Playwright): dashboard con KPIs reales, lista de liquidaciones,
  detalle con incidentes/alertas, sidebar con el submenú "Liquidaciones" ya visible.

### Bug encontrado y corregido en el camino: orden de registro de routers

`liquidaciones_router` (con el catch-all `GET/DELETE/PATCH /{liquidacion_id}`) estaba
registrado en `app.py` **antes** que `liquidaciones_config_router` (rutas literales
`/tarifarios`, `/spsts`, `/tabla-km`). Con el módulo deshabilitado esto era invisible
(todo daba 403 antes de llegar a la validación de path); al activarlo, `GET
/api/liquidaciones/tarifarios` devolvía 422 ("tarifarios" no es un UUID válido) porque
Starlette matcheaba el catch-all primero. Corregido invirtiendo el orden de
`app.include_router(...)` en `backend/src/shared/presentation/app.py`.

### Gap de paridad de ALT005 — CERRADO (2026-08-13)

El legacy generaba ALT005 (Ruta Compartida) por **dos caminos**: alertas individuales
por-incidente (vía `evaluar()`) y observaciones agrupadas (vía `evaluar_grupo()`). El
port nuevo había portado solo el camino de grupo (`evaluar_grupo_alt005` →
`ObservacionGenerada`) — el camino por-incidente se había dejado sin portar porque en
su momento se asumió que ALT005 estaba desactivada por default en producción.

**Portado el camino por-incidente** (`domain/services/motor_reglas/alt005_ruta_individual.py`,
función `evaluar_alt005`), fiel al algoritmo legacy (guardas de fecha/km/tabla,
partición disjunta `exactos`/`corredor`, hasta 2 alertas por incidente, mismos `tipo`
y mismas claves de `datos_contexto` que producción real). Cableado en `motor.py`
(`_EVALUADORES_POR_INCIDENTE` + branch explícito en `_evaluar_regla`, no el
fallthrough de ALT009). Las dos ramas muertas del legacy (`agrupado_ok`,
`corredor_agrupado_ok`, inalcanzables por una guarda que fuerza km cobrado > 0) **no**
se portaron — 0 apariciones en los datos reales, no forman parte del comportamiento a
preservar. `misma_localidad`/`mismo_spst_dentro_del_umbral` se promovieron a públicas
en `_resolucion.py` (antes privadas, usadas solo vía el combinador `mismo_corredor`)
para no duplicar la lógica de "mismo corredor" que ya usaba ALT002.

10 tests de caracterización nuevos en `TestAlt005RutaCompartida` (duplicado por
localidad, corredor_duplicado, corredor_contenido, las 3 guardas, disjunción
exactos/corredor, máximo 2 alertas, coexistencia con la Observación agrupada).

**Bug real encontrado por la verificación end-to-end, no por los tests unitarios**:
el `datos_contexto` de las alertas `corredor_*` incluía `tabla_km.spst_id` como
objeto `UUID` de Python — `TypeError: Object of type UUID is not JSON serializable`
al intentar persistir en la columna `JSONB`. Los tests unitarios no lo detectaron
porque comparan el dict en memoria, nunca lo serializan de verdad. Corregido
stringificando `spst_id` (mismo patrón que ya usaba ALT004 con
`liquidaciones_previas`). Confirma por qué el plan exige la verificación contra el
contenedor real además de los tests — este bug hubiera llegado a producción con solo
"pytest en verde".

Verificado contra datos reales: liquidación `224979f9-...` tenía 4 alertas `ALT005`
originalmente migradas del legacy; un `reanalyze` de sesión anterior (antes de este
port) las había dejado en 0; con el evaluador nuevo, `reanalyze` las regenera —
**4 alertas `ALT005`, mismo conteo que el original**, con el `tipo`/`datos_contexto`
en el mismo formato que producción real (`corredor_contenido`, `cobrado_este`,
`km_actual`, `otros_incidentes`, `spst_id` ahora como string UUID en vez de int
legacy).

### Gap de UX encontrado y CERRADO (2026-08-13): Tarifarios y Tabla KM truncaban a 500 filas en el frontend

`liquidaciones-api.ts::listTarifarios`/`listTablaKm` llamaban al endpoint sin `size`
(cae al default del backend, `CATALOGO_SIZE=500`) y descartaban el campo `.total` del
envelope `Page[T]`, quedándose solo con `.items` — la UI mostraba `items.length`
rotulado como "N tarifas/entradas cargadas en total". Invisible hasta la carga de
datos reales porque ambas tablas estaban vacías; `tarifarios` (4832 filas) y
`tabla_kms` (1633 filas) superan largamente las 500 que traía el cliente. El orden de
qué 500 filas llegaban no estaba garantizado por ningún `ORDER BY` explícito del lado
del backend, así que qué prestador aparecía con datos "cargados" y cuál con "no tiene
tarifas cargadas" era esencialmente arbitrario (BAHIA aparecía vacío en Tarifarios
pero con solo 7 de sus 15 filas reales en Tabla KM). `SPSTs` no tenía este problema (49
filas, por debajo del límite).

**Resuelto rediseñando ambas pantallas para pedir por prestador seleccionado**
(decisión del usuario, no subir `CATALOGO_SIZE`): `tarifarios-config.tsx` y
`tabla-km-config.tsx` ya no traen el catálogo completo al montar — cargan solo la
lista de prestadores (liviana, 35 filas) y no piden tarifarios/tabla-km hasta que el
usuario elige un prestador del selector, momento en el que llaman
`listTarifarios(prestadorId)`/`listTablaKm({ prestadorId })` (el backend ya soportaba
el filtro `?prestadorId=` en SQL, no hizo falta tocarlo). Al estar acotado a un solo
prestador, el volumen nunca se acerca al límite de 500/1000 filas del backend. Se
sacó el agrupado-por-todos-los-prestadores (ya no aplica con un solo prestador
visible a la vez) y el estado de carga se deriva comparando el prestador seleccionado
contra el prestador de los datos ya cargados (`tarifariosPstId`/`entradasPstId`) en
vez de un flag `setLoading(true)` síncrono en el efecto — lo segundo viola
`react-hooks/set-state-in-effect`. Verificado en el navegador contra datos reales:
BAHIA muestra sus 48 tarifas y sus 15 entradas de Tabla KM completas (antes 0 y 7
respectivamente).

## Pendiente

1. **Importadores Excel + plantillas** (hoy solo CSV/HTML) — el legacy tenía
   `POST /prestadores/importar-excel` (Excel maestro del PST) cableado en su UI; el
   nuevo módulo no lo portó.
2. **DELETE físico vs soft-delete** de prestador/SPST — sin decidir.
3. **0 tests de integración de infrastructure** (10 repos SQLAlchemy + parser pandas) —
   deuda transversal compartida con turnos/sla.
4. **Use cases de escritura para el resto de las entidades de configuración** — hoy
   router→repositorio directo en los 4 config_routers, sin casos de uso propios.
5. Correr en paralelo con la app legacy antes de apagarla — no hay cutover en frío.

## Próximo paso sugerido

Decidir con el usuario cuál de los pendientes de arriba se ataca primero, o arrancar
el período de observación en paralelo con la app legacy.
