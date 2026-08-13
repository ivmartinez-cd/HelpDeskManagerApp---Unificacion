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
4. **Casos de uso** de lectura, importación y reanálisis; los de escritura de config
   se agregaron el 2026-08-13 (ver sección propia más abajo).
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

### Importador de Excel maestro de PST — CERRADO (2026-08-13)

El legacy tenía `POST /prestadores/importar-excel` (un único `.xlsx`/`.xls` por
PST/mes con Prestador+SPSTs+Tarifarios+TablaKM embebidos en varias hojas) cableado
en su backend, pero **no** en su UI — el `<input>` que dispararía el import nunca
llegó a renderizarse (código huérfano). Además tenía un bug real: buscaba la hoja
llamada literalmente "ENERO", así que un archivo de otro mes con su hoja
homónima (ej. "ABRIL") lo rompía.

Portado corrigiendo ambos problemas, no replicándolos: detección de la hoja
principal por contenido (primera hoja con una celda "AGENTE:", sin importar el
nombre), y UI nueva desde cero en la pantalla de configuración de Prestadores.
Sigue el patrón "pesado" ya establecido para el importador de liquidaciones
mensuales (puerto `PrestadorMaestroFileParser` + adapter pandas +
`domain/services/importacion_maestro/` puro + use case
`ImportarPrestadorMaestro`), no el patrón simple de los importadores CSV — acá hay
lógica de dominio genuina (dedup en dos capas, matching fuzzy de SPST, cálculo de
`aplica_viatico`).

**2 bugs reales encontrados corriendo el parser contra archivos reales del legacy**
(no por los 45+8 tests unitarios, que pasaban igual con ambos bugs presentes —
mismo patrón que ya pasó con ALT005 el mismo mes): `str(None).strip()` da el
string literal `"None"` (truthy), así que una celda vacía de la columna Prestador
generaba un SPST fantasma llamado "None"; y `normalizar_tipo_servicio("")` cae a
`TIPO_CORRECTIVO` por default (correcto para el importador de liquidaciones, donde
"sin tipo" es una regla de negocio real), lo que convertía filas con la columna
Tipo vacía en tarifarios "correctivo" fantasma en vez de descartarlas como hacía
el legacy. Ambos corregidos.

Verificado con los 2 `.xlsx` reales del legacy (`PENTACOM 202601.xlsx` completo, y
`CATAMARCA 202604.xlsx` que no tiene hoja de Tabla KM — confirma que la ausencia
ya no es fatal) y, end-to-end en el navegador, subiendo `PENTACOM 202601.xlsx`
contra el prestador PENTACOM real ya migrado: primera corrida create 6 SPSTs y 11
filas de Tabla KM nuevas (0 tarifarios nuevos — los 4 ya estaban, migrados del
snapshot legacy); **re-subir el mismo archivo una segunda vez no creó nada** (0
SPSTs, 0 tarifarios, 0 Tabla KM, todo correctamente omitido por dedup) — confirma
el fix del hallazgo más grave de la revisión de diseño: el borrador original solo
dedupeaba tarifarios contra el resto del archivo, nunca contra la base, así que
re-importar el mismo mes los hubiera duplicado en cada corrida.

Soporta `.xlsx` y `.xls` (se agregó `xlrd` como dependencia).

### DELETE de prestador/SPST — CERRADO (2026-08-13)

El schema nuevo ya tenía la decisión tomada a nivel de FK (alguien la dejó lista al
migrar el modelo de datos, con docstrings explicando el porqué), solo faltaba el
endpoint que la usara: `spsts.prestador_id`/`tarifarios.prestador_id`/
`tabla_kms.prestador_id` → `ON DELETE CASCADE`; `tabla_kms.spst_id` → `ON DELETE
SET NULL` (borrar un SPST desvincula su Tabla KM, no la borra); `liquidaciones.
prestador_id` → sin `ondelete` (bloquea a propósito: "es historial de facturación
real, no se pierde por una baja administrativa").

El legacy sí tenía DELETE físico, pero frágil: cascada solo a nivel ORM (no en la
DB) y sin capturar el `IntegrityError` de Postgres cuando había liquidaciones o
tabla_km relacionadas → 500 crudo sin manejar. Para SPST ni siquiera tenía
confirmación en la UI (para Prestador sí, `confirm()` nativo del navegador).

**Decisión, confirmada con el usuario**: DELETE físico apoyado en esas FK, con el
`IntegrityError` traducido a un error de dominio prolijo
(`PrestadorConLiquidacionesError`, 409) en vez de un 500. `SqlAlchemyPrestadorRepository
.delete()`/`SqlAlchemySpstRepository.delete()` (siguen el mismo patrón que
`update()`/`toggle_activo()`: métodos directos en el repo concreto, no en el
Protocol — igual que el resto de este router). Nuevos `DELETE /prestadores/{id}` y
`DELETE /spsts/{id}`, botón "Eliminar" + modal de confirmación en ambas pantallas
(clon del patrón ya usado para tarifario/tabla-km, no el `confirm()` nativo del
legacy).

Verificado end-to-end contra el backend real (llamadas HTTP directas, no solo
tests): prestador descartable sin relacionados → 201 crear, 204 eliminar; SPST con
una fila de Tabla KM vinculada → eliminar el SPST da 204 y la fila de Tabla KM
sigue existiendo con `spstId=null` (`SET NULL` confirmado); intento de eliminar el
prestador real PENTACOM (tiene liquidaciones reales) → 409 con mensaje claro,
PENTACOM sigue intacto después. El smoke test de click-through en el navegador
quedó bloqueado por el contenedor de backend reiniciándose constantemente (otra
sesión editando `contadores` en simultáneo, mismo contenedor compartido) — no se
reintentó más allá de lo razonable porque no es un problema del código; el patrón
de botón/modal es una copia mecánica de uno ya probado en este mismo módulo.

Sin tests unitarios nuevos para `delete()`: este módulo no tiene tests de
infraestructura para ningún repo SQLAlchemy (ver pendiente de tests de
integración, abajo) — `delete_liquidacion` (ya existente) tampoco los tiene,
consistente con la convención actual.

### Tests de integración de infrastructure — CERRADO (2026-08-13)

`backend/tests/integration/infrastructure/liquidaciones/` — 60 tests nuevos contra
Postgres real (`docker-compose.test.yml`, `db_session` con rollback por test), no
contra `helpdesk-db`: los 10 repos SQLAlchemy (prestador, spst, tarifario, tabla_km,
regla_alerta, liquidacion, incidente, alerta, observacion, resolucion) y los 2
parsers pandas (`PandasLiquidacionFileParser` contra bytes HTML reales vía lxml,
`PandasPrestadorMaestroFileParser` contra un `.xlsx` real construido con openpyxl —
ambos ejercitan la capa de infraestructura que los tests de dominio puro no cubren:
lectura real del archivo, selección de tabla/hoja entre varias, fallback de
`flavor`). `conftest.py` local con fixtures encadenadas `prestador_id` →
`liquidacion_id` → `incidente_id` (via los repos reales, no factories separadas) —
la mayoría de los repos transaccionales depende de esa cadena de FKs.

Corren en el **host**, no dentro del contenedor backend (`uv run pytest
tests/integration/infrastructure/liquidaciones`) — el fixture de conexión usa
`localhost:5440`, que es el mapeo de puerto de `db-test` hacia el host; desde dentro
del contenedor `helpdesk-manager-backend` ese `localhost` no resuelve a nada
(contenedores distintos, sin red compartida) y todos los tests fallan con
`Connect call failed`.

**Bug real encontrado por el test, no por code review**:
`SqlAlchemyLiquidacionRepository.delete()` no hacía `await self._session.flush()`
tras `session.delete()` — a diferencia de los 4 repos hermanos (prestador, spst,
tarifario, tabla_km), que sí flushean explícito en su `delete()`. `session.get()`
inmediatamente después devolvía la fila desde el identity map en vez de `None`,
porque sin flush la baja no se materializa. Corregido agregando el `flush()`
faltante, mismo patrón que el resto. En producción probablemente no se notaba (el
commit final de `get_db()` igual persiste la baja), pero cualquier lectura dentro
del mismo request/sesión después del DELETE hubiera visto la fila "zombie".

Verificado: `lint-imports` (17/17 contratos), `ruff check src tests`, `mypy src`
(758 archivos), `pytest tests/unit` (816 tests) y `pytest tests/integration` (166
tests, todos los módulos) — los 4 en verde.

## Use cases de escritura de configuración (2026-08-13)

Cerrado el pendiente 1: los 4 config_routers ya no van router→repositorio directo
en las escrituras. Nuevos casos de uso en `application/use_cases/` —
`config_prestadores.py` (Create/Update/TogglePrestadorActivo/DeletePrestador),
`config_spsts.py` (ídem SPST), `config_tarifarios.py`
(Create/Update/DeleteTarifario) y `config_tabla_km.py`
(Create/Update/DeleteTablaKm, con DTO `TablaKmDatos` para no repetir los 13 campos
en alta y edición) — con factories en `presentation/dependencies/config.py`.
Detalles con intención:

- Los Protocols de dominio (`prestador/spst/tarifario/tabla_km_repository.py`) se
  ampliaron con `update`/`toggle_activo`/`delete` (y en tarifarios además
  `get_by_id`/`list_grupo`/`set_vigencia_hasta`) — los métodos ya existían en los
  impl SQLAlchemy, solo faltaban en el puerto.
- El **recadenado de vigencias** de tarifarios se movió del router
  (`_recadenar_grupo` en presentation) a los use cases de tarifarios: la regla de
  negocio ya no vive en la capa HTTP. El comportamiento es el mismo (recadena el
  grupo afectado en alta/edición/baja; si la edición cambia de grupo, recadena
  origen y destino).
- Los 404 ya no son `HTTPException` en el router: los use cases lanzan
  `SpstNoEncontradoError`/`TarifarioNoEncontradoError`/`TablaKmNoEncontradaError`
  (nuevos en `domain/errors.py`, junto al ya existente `PrestadorNoEncontradoError`)
  y el handler global de `AppError` los traduce. Cambia el shape del error: antes
  `code: "HTTP_ERROR"`, ahora el `default_code` de cada error — el frontend no
  matchea ni mensajes ni códigos, verificado por grep.
- La normalización `strip().upper()` de `nombre_corto` de Prestador bajó del router
  a Create/UpdatePrestador (es regla de negocio, no de transporte).
- Export/import CSV siguen llamando repos concretos vía `_liq_csv` (lecturas +
  helpers de presentación, mismo estado que antes); el import Excel maestro ya
  tenía su use case.
- Tests: 26 unit nuevos (`test_config_{prestadores,spsts,tarifarios,tabla_km}.py`)
  sobre fakes de escritura nuevos en `fakes_config.py` (extienden los de
  `fakes.py`, que ya estaba al límite de tamaño). Los de tarifarios cubren el
  recadenado en create/update (con cambio de grupo) y delete.

Verificado: `lint-imports` (17/17), `ruff check src tests`, `mypy src` (763
archivos), `pytest tests/unit` (842 tests) y
`pytest tests/integration/infrastructure/liquidaciones` (60 tests, desde el host
con `helpdesk-db-test` arriba) — todo en verde. Backend reiniciado
(`DISABLE_BACKGROUND_JOBS=true` confirmado antes y después, sin jobs iniciados).

## Recadenado de vigencias en los importadores (2026-08-13)

Cerrado el pendiente de importación (el usuario confirmó el cambio de
comportamiento vs. el legacy): `ImportarPrestadorMaestro` y el import CSV de
tarifarios ahora recadenan vigencias igual que el alta/edición/baja manual — el
legacy al importar dejaba vigencias solapadas, que es justo lo que ALT001/ALT008
usan para resolver el precio esperado. La divergencia quedó documentada en el
docstring de `importar_prestador_maestro.py`.

- Helper compartido `application/use_cases/_recadenado.py` (`recadenar_grupo`):
  lo usan `config_tarifarios.py` (antes tenía la misma lógica inline en
  `_recadenar_grupo_de`) y `ImportarPrestadorMaestro`.
- `ImportarPrestadorMaestro` recadena una sola vez al final, por cada grupo
  (tipo_servicio, zona=None) que recibió filas nuevas; si el archivo entero se
  omite por duplicado no toca ninguna vigencia ya persistida.
- El import CSV (`_liq_csv.import_tarifarios`) ya no llama al repo directo: cada
  fila va por `CreateTarifario`, que recadena el grupo en cada alta — mismo camino
  que el alta manual. Con esto no queda ninguna escritura de configuración que
  saltee la capa de application (`prestador_repo` quedó tipado con el Protocol de
  dominio, ya no con el repo SQLAlchemy concreto).
- Tests: 3 unit nuevos en `test_importar_prestador_maestro.py` (recadenado dentro
  del archivo, contra un tarifario preexistente del grupo, y no-recadenado cuando
  todo se omite por duplicado; el `World` pasó a `FakeConfigTarifarioRepository`,
  que implementa `list_grupo`/`set_vigencia_hasta`) y 2 en
  `tests/unit/presentation/liquidaciones/test_liq_csv_tarifarios.py` (directorio
  nuevo de tests unit de presentación).

Verificado: `lint-imports` (17/17), `ruff check src tests`, `mypy src` (764
archivos), `pytest tests/unit` (847 tests) y
`pytest tests/integration/infrastructure/liquidaciones` (60 tests, desde el host
con `helpdesk-db-test` arriba) — todo en verde.

## TarifarioHistoryTimeline + cierre real del truncamiento por prestador (2026-08-13)

Cerrado el pendiente menor de UX que quedaba (timeline de vigencias + evaluación de
paginación server-side de tabla-km):

**TarifarioHistoryTimeline portado.** La pantalla de Tarifarios ya no muestra una tabla
plana de filas sueltas: agrupa por servicio (tipo + zona) con el resumen de la tarifa
vigente (costo servicio / costo KM / desde) y un botón "Historial (N)" que expande la
línea de tiempo de vigencias — variación % entre vigencias consecutivas, badges
"Vigente hoy"/"Inicial", editar/eliminar por vigencia, y botón "Actualizar" que abre el
modal prefijado (tipo/zona/costos de la vigente, vigencia desde hoy) para cargar la
vigencia nueva (el recadenado del use case cierra la anterior). Port de
`components/tarifarios/{ServiceTarifaRow,TarifarioHistoryTimeline}.tsx` del legacy,
reestilado a los tokens del monorepo (indigo→brand-orange, emerald→success, dark-aware,
radios arbitrarios) en `frontend/src/features/liquidaciones/components/
tarifario-history-timeline.tsx`. La card-acordeón por prestador del legacy
(`PrestadorTarifasCard`) no se portó a propósito: el selector de prestador del rediseño
por-prestador ya cumple ese rol. `formatFechaDia` nuevo en `lib/format.ts` para fechas
date-only (`formatFecha` con `new Date("YYYY-MM-DD")` mostraría el día anterior en
timezone AR por el parseo UTC).

**Corrección a la sección del truncamiento de más arriba**: el claim "al estar acotado
a un solo prestador, el volumen nunca se acerca al límite de 500/1000" era falso con
los datos reales — INFOMAC tiene 960 tarifas (la pantalla seguía truncando a las 500
del default, historial incompleto justo para lo que el timeline necesita) y SAN JUAN
tiene 487 entradas de tabla KM (97% del default; una importación más y truncaba en
silencio). Cerrado de verdad con `fetchCatalogoCompleto` en `liquidaciones-api.ts`:
pide `size=1000` (el tope `le=1000` del backend) y sigue pidiendo páginas hasta cubrir
`total`, así ningún prestador puede truncar aunque siga creciendo. Para que ese paginado
multi-request sea consistente se agregó orden total en SQL (los repos no tenían ningún
`ORDER BY` en tarifarios, y tabla_km no tenía desempate — sin orden estable, `Page[T]`
puede repetir o saltear filas entre páginas): tarifarios por (tipo_servicio, zona,
vigencia_desde desc, id), tabla_km con id como desempate.

**Paginación server-side de Tabla KM: DESCARTADA como UI, decisión documentada.** Tras
el rediseño por-prestador el volumen máximo por vista es 487 filas (SAN JUAN) — render
client-side sin problema, y la búsqueda por cliente/sucursal ya cubre la navegación.
Una tabla paginada agregaría fricción (la búsqueda es client-side sobre lo cargado) sin
resolver nada: el único problema real era el truncamiento silencioso del punto anterior,
que se cerró con el fetch paginado. El contrato HTTP sigue siendo `Page[T]` (§11), así
que si algún día una vista lo necesita, el backend ya lo soporta.

## Pendiente

1. Correr en paralelo con la app legacy antes de apagarla — no hay cutover en frío.

## Próximo paso sugerido

Arrancar el período de observación en paralelo con la app legacy.
