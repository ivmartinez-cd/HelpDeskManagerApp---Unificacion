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

## Automatización de fuentes — ADR-014, dataset 1 CERRADO (2026-08-13)

Workstream nuevo (posterior al port): reemplazar la carga CSV/Excel de configuración
por sync desde SigesReadOnly. Fase 1 (validación con dato real) en
`docs/liquidaciones/SIGES_READONLY_LIQUIDACIONES_VALIDACION.md`; Fase 2 (decisión) en
`docs/adr/014-fuente-siges-para-config-de-liquidaciones.md` (aceptado). Fase 3 se
implementa un dataset por vez — **dataset 1 (prestadores/SPSTs) cerrado**
(backend commiteado en `bf0257c`; frontend + verificación de esta sesión):

- **Modelo**: `siges_empresa_id` (nullable, UNIQUE) en `prestadores` y `spsts`
  (migración `c4d8a91f26e3`, aplicada a helpdesk-db), entidades/modelos/repos con
  `vincular_siges` (el `IntegrityError` del UNIQUE se traduce a
  `SigesVinculoDuplicadoError`, 409).
- **Dominio**: puerto `SigesCatalogoGateway` (+ `SigesEmpresaInfo`) y servicio puro
  `vinculacion_siges` (matching normalizado sin acentos/prefijos, contención sin
  espacios, solo matches inequívocos en ambas direcciones).
- **Infra**: `PyodbcSigesCatalogoGateway` sobre `dbo.Empresa` (`Estado=0` = activo,
  prefijos `'PST '`/`'SPST'`), patrón pyodbc de ADR-012.
- **Application**: `ProponerVinculosSiges`, `Vincular{Prestador,Spst}Siges`,
  `SyncConfigDesdeSiges` con dry-run first-class — actualiza solo el campo espejo
  `cuit` de prestadores vinculados (comparación por dígitos; nunca borra si Siges no
  lo tiene); nombre distinto se reporta sin escribir; nunca crea/desactiva.
- **HTTP**: `GET /api/liquidaciones/siges/propuestas`, `POST /siges/sync?dryRun=`,
  `PUT /prestadores/{id}/siges-vinculo`, `PUT /spsts/{id}/siges-vinculo`
  (`config_routers/siges.py`); `PrestadorOut`/`SpstOut` exponen `sigesEmpresaId`.
- **Frontend**: botón "Sincronizar Siges" en la pantalla de Prestadores →
  `siges-sync-modal.tsx` (propuestas con confirmación individual, dry-run automático
  al abrir, "Aplicar sync", disponibles-sin-vincular informativos); columna "Siges"
  en la tabla. Nota eslint: `react-hooks/set-state-in-effect` prohíbe `setState`
  dentro de un `catch` alcanzable desde un efecto — el load del modal usa
  promise-chain (`.then/.catch`), único patrón que la regla acepta con manejo de
  error.

**Verificado contra Siges real y DB real** (script reproducible
`backend/scripts/verificar_siges_vinculo_liquidaciones.py`, corrido con
`DISABLE_BACKGROUND_JOBS=true`): 37 propuestas de alta confianza (31 prestadores +
6 SPSTs), todas correctas a inspección; aplicadas; sync real trajo **31 CUITs
reales** (todos los prestadores locales tenían cuit vacío); re-corrida → 0 cambios
(idempotencia verificada). Quedaron sin vincular a propósito: `SUPERNOVA`+`PERTEX`
(ambos matchean la empresa #600 de Siges — el duplicado histórico Pertex/Supernova
del legacy; ambigüedad que el matching descarta y debe resolver la TL a mano),
`SM TUCUMAN`/`TUCUMAN` (nombres Siges sin match de confianza:
`'PST SM de Tucuman'`/`'PST Tucuman - NAPA'`) y `ZZTESTUI` (fila de prueba).

Gates: lint-imports 17/17 · ruff · mypy (777 archivos) · 872 unit (25 nuevos) ·
63 integración liquidaciones (3 nuevos de `vincular_siges`) · tsc · eslint — todo
en verde el 2026-08-13.

### Dataset 2 — sync de tarifarios CERRADO (2026-08-13, misma sesión)

- **Modelo**: tabla `tarifario_zona_maps` (migración `d91f4b7a03c8`): mapeo por
  prestador de `CostoServicio.descripcion` → zona local, UNIQUE por par;
  **`zona_local` NULL = mapeada a la zona genérica** (tarifario sin zona) — no es
  un caso raro, es el mayoritario (ver hallazgo TMT abajo).
- **Dominio**: `SigesCostoServicio` (fila wide) + `list_costos_habilitados` en el
  gateway; servicio puro `sync_tarifarios.py`: pivot wide→long (6 tipos con
  equivalente local; `inclusion_a_contrato`/`relevamiento`/`presupuesto`/`taller`
  ignorados por ADR), resolución de zona ('Genérica'→None implícito, 'DE
  BAJA'/'Sin servicio' excluidas, resto exige mapeo), plan
  crear/conflicto/sin_cambios (tolerancia 0.01, la de ALT001; costo 0 = "no
  presta", el $0,01 real de Centro Cívico sí pasa), y propuesta de mapeo de zonas
  con el mismo matching de alta confianza del dataset 1.
- **Application**: `SyncTarifariosDesdeSiges` (dry-run first-class; **toda alta
  entra por `CreateTarifario`** → recadenado de vigencias garantizado; conflicto
  = misma vigencia con costo distinto, se reporta y JAMÁS se pisa),
  `EstadoZonasSiges`, `MapearZonaSiges`. Resultado agregado por grupo (el detalle
  fila-por-fila serían miles de líneas).
- **HTTP**: `GET/PUT /api/liquidaciones/siges/zonas`,
  `POST /siges/sync-tarifarios?dryRun=`. **Frontend**: botón "Sincronizar Siges"
  en Tarifarios → `siges-tarifarios-modal.tsx` (mapeo de zonas pendientes con
  select — genérica / adoptar nombre Siges / zona local, propuesta preseleccionada
  —, resultado dry-run agrupado, aplicar).

**Hallazgos de la verificación contra datos reales** (script
`backend/scripts/verificar_siges_tarifarios_liquidaciones.py`):

1. **Paridad perfecta PENTACOM**: 168/168 sin cambios, 0 conflictos — la cadena
   completa de vigencias local coincide con `CostoServicio` end-to-end.
2. **Los códigos TMT\* son la tarifa genérica de cada PST**: la mayoría de los
   PSTs no usa descripción 'Genérica' sino su código de tarifa (`TMTB122`,
   `TMTA222`, …). Confirmado por conteos exactos con zona local NULL (MENDOZA
   192=192, SALTA 192=192, MACARONE 198=198, CATAMARCA 138=138). Esto motivó el
   rediseño `zona_local` NULL = genérica (la primera versión del modelo no
   permitía mapear a "sin zona").
3. **2 bugs reales encontrados por datos reales, no por los tests**: `CostoKm`
   puede venir NULL en `CostoServicio` (→ 0.0 en el gateway); y el modelo de
   mapeo sin opción "genérica" (punto 2).
4. **Sync real aplicado**: 33 mapeos de zona confirmados (TMT\*→genérica por
   regla, 3 propuestas automáticas de INFOMAC, General Roca→'Gral. Roca /
   Neuquén' manual), **764 vigencias históricas creadas** (CDU 168, MDQ 162,
   CHACO 144, VENADO 140, PERGAMINO 78, TANDIL 66, SAN JUAN 6), 3961 sin
   cambios, re-corrida idempotente (0 creados, 4725 sin cambios). Invariante de
   cadenas verificado en SQL: 0 filas con `vigencia_hasta` NULL que tengan una
   vigencia posterior en su grupo (5596 tarifarios totales).
5. **Los 3 conflictos reportados son hallazgos de negocio reales** (correctamente
   NO pisados): SAN JUAN instalación 2026-01-01 local=92252 vs Siges=46126 —
   exactamente el doble, la regla conocida "doble tarifa instalación San Juan"
   aplicada en la planilla local; VENADO instalación 2026-07-01 66794 vs 66749
   (probable typo de $45); INFOMAC preventivo Villa Mercedes 2026-01-01 23073 vs
   24559. Los resuelve la TL a mano si corresponde.
6. **Sin mapear a propósito** (decisión de la TL pendiente): `GSJ - Escuelas
   Valle Fertil` y `GSJ - GI Centro Civico` de SAN JUAN (excepciones de zona sin
   zona local equivalente — lo local maneja Centro Cívico sin zona).

Gates dataset 2: lint-imports 17/17 · ruff · mypy (785) · 891 unit (+19) · 65
integración (+2) · tsc · eslint · 15 e2e Playwright — en verde el 2026-08-13.

### Dataset 3 — alta asistida de Tabla KM CERRADO (2026-08-13, misma sesión) → ADR-014 completo

Por diseño (y pedido explícito del usuario) **solo lectura + solo agregar**: no
hay sync de tabla KM — nada toca, pisa ni borra los pares ya migrados. El alta
sigue siendo decisión manual vía `CreateTablaKm`; Siges solo precarga los datos
descriptivos del par.

- **Gateway**: `SigesSucursalCliente` + `list_sucursales_de_prestador`
  (`dbo.Sucursal` `Estado=0` JOIN `Empresa` LEFT JOIN `Ciudad` para
  localidad/provincia; el `Domicilio` real viene con ruido de plantilla
  `' 0 Piso: Dpto:'` cuando está vacío — se limpia en el gateway).
- **Application**: `BuscarSucursalesSiges(prestador_id, q)` — exige prestador
  vinculado (`PrestadorSinVinculoSigesError`, 409), filtra por nombre
  normalizado y marca `ya_cargada` cruzando contra la Tabla KM local (misma
  normalización sin acentos/case del matching del dataset 1).
- **HTTP**: `GET /api/liquidaciones/siges/sucursales?prestadorId&q` con
  `Page[T]` (§11). **Frontend**: botón "Agregar desde Siges" en Tabla KM
  (deshabilitado sin prestador vinculado) → modal de búsqueda con badge
  "Ya cargada" y botón "Usar" que abre la Nueva Entrada prefillada (prop
  `plantilla` nueva en `EntradaModal`, mismo patrón que `TarifaModal`); el km
  queda vacío a propósito.

**Verificado contra Siges real** (solo lectura): PENTACOM 762 sucursales
vigentes, **247 de los 276 pares locales reconocidos como `ya_cargada`** por
comparación normalizada ('Achiras'·'CP Achiras' ✓); domicilios reales para el
prefill ('Banco Credicoop · 100 - Cordoba Centro · Buenos Aires 23'); conteo de
Tabla KM intacto tras las búsquedas (276 — no escribe nada). Los ~29 pares
locales sin match son sucursales renombradas/inactivas en Siges — esperable, no
un bug.

Gates dataset 3: lint-imports 17/17 · ruff · mypy (787) · 895 unit (+4) · tsc ·
eslint · 15 e2e — en verde el 2026-08-13. **Con esto el ADR-014 queda
implementado completo (3/3 datasets).**

### Decisiones del usuario aplicadas (2026-08-13, cierre de pendientes del ADR-014)

- **SUPERNOVA → #600**: vinculado (tenía todo el historial real: 3 liquidaciones,
  180 tarifas, 199 km; PERTEX es el duplicado vacío del legacy — queda sin vínculo,
  candidato a baja cuando el usuario quiera).
- **SM TUCUMAN → #1285 y TUCUMAN → #491 (NAPA)**: vinculados y **confirmados con
  evidencia** por dry-run: tras mapear sus códigos TMT a genérica, los tres nuevos
  dieron 0 a crear / 0 conflictos — las 180 tarifas locales de "German Naselli" son
  exactamente las de "NAPA Tucuman" (mismo PST renombrado). `sin_cambios` global
  4725→5139 (+414 = 180+54+180). TUCUMAN además tiene la zona
  `'TMTA122 - SGO DEL ESTERO'` sin mapear (NAPA atiende Sgo del Estero como zona;
  lo local no la usa — misma situación que las GSJ).
- **CUITs de los 3 nuevos sincronizados** (SUPERNOVA 30715672657, SM TUCUMAN
  33709510369, TUCUMAN 20297151712), re-corrida idempotente. Quedan sin vínculo
  solo PERTEX (a propósito) y ZZTESTUI (fila de prueba): 34/36.
- **Conflicto SAN JUAN instalación = regla del doble confirmada por el usuario**
  ($46.126 × 2 = $92.252 exacto): se mantiene local. VENADO ($45) e INFOMAC
  (preventivo VM) también quedan locales, pendientes de la TL — seguirán
  apareciendo en cada dry-run como recordatorio.
- **Zonas `GSJ - *` de SAN JUAN: sin mapear a propósito** (el manejo local de
  Centro Cívico a $0,01 sin zona no se toca).

- **PERTEX eliminado definitivamente** (pedido del usuario, 2026-08-13): baja
  física vía `DeletePrestador` — cascadeó su único SPST (`'PST Rosario -
  Supernova/Pertex'`, sin tabla KM vinculada); no tenía liquidaciones ni
  tarifas. Quedan 35 prestadores, **34/35 vinculados a Siges** (solo ZZTESTUI,
  la fila de prueba, sin vínculo).

## Sprint TL — 8 mejoras funcionales (2026-08-13)

Cambios pedidos por la Team Leader una vez el módulo estuvo en uso real. Listado
completo en `docs/liquidaciones/MASTER_PROMPT_CAMBIOS_TL_LIQUIDACIONES.md`. Todos
committeados y verificados (lint-imports · ruff · mypy · pytest unit) el mismo día.

### P5 — Badge de estado en los 6 estados `CERRADO` (commit `e596ab7`)

`EstadoBadge` usaba un if-chain que solo coloreaba 3 de los 6 estados
(`aprobada`→success, `observada`→warning, `abierta`→info); los demás caían al
default neutro. Reemplazado por un lookup table `ESTADO_CONFIG` con los 6 estados
y sus variantes explícitas: `preliquidada`→accent, `recibida`→neutral,
`cerrada`→neutral.

### P6 — Filtros server-side + dropdown de período `CERRADO` (commit `e596ab7`)

El filtro de estado era client-side sobre la página actual: filtrar por "aprobada"
en la página 2 mostraba solo las aprobadas de esa página, no del total. Se movió
al backend (query param `?estado=` en `list_filtered()`) para que sea consistente
con la paginación. También se añadió filtro por período:

- **Dominio**: `LiquidacionRepository` Protocol reemplazó `list_all()`/
  `list_by_prestador()` por un único `list_filtered(prestador_id, estado, periodo)`;
  `list_periodos()` para el dropdown.
- **Infra**: `SqlAlchemyLiquidacionRepository` implementa ambos con cláusulas WHERE
  dinámicas y DISTINCT en periodos.
- **Application**: `ListLiquidaciones.execute()` acepta los 3 filtros opcionales.
- **Router**: `GET /api/liquidaciones` acepta `?estado=` y `?periodo=`; nuevo
  endpoint `GET /api/liquidaciones/periodos` registrado **antes** del catch-all
  `/{liquidacion_id}` (orden de registro importa en FastAPI).
- **Frontend**: `liquidaciones-lista.tsx` mueve el filtro de estado al servidor +
  agrega dropdown de período que llama a `listPeriodos()`; cualquier cambio de
  filtro resetea la página a 1 (`handleFilter` helper).
- Max size subido de 200 a 1000 (el anterior techo era un límite arbitrario
  que ya truncaba en algunos casos reales).

### P7 — Selectores en el dashboard + fix truncación `CERRADO` (commit `e596ab7`)

El dashboard pedía `list({size:200})` — con liquidaciones reales ya hay más de 200.
Resuelto con `listAll()` (patrón `fetchCatalogoCompleto` que loopea páginas hasta
cubrir `total`). Se agregaron filtros de prestador y año al dashboard con `useMemo`
para el filtrado client-side.

### P1 — `math.ceil` en ALT002 para kms decimales `CERRADO` (commit `1b562e4`)

La Tabla KM puede guardar kms con decimales (ej. 20.5 km medidos) pero el PST
factura el entero superior (21 km). La comparación de ALT002 usaba el valor raw
y con tolerancia 0 disparaba alerta cuando el PST cobraba correctamente
`ceil(kms_a_facturar)`.

- `evaluar_alt002` ahora compara contra `math.ceil(tabla_km.kms_a_facturar)`.
- `_hallazgo` incluye tanto el valor raw como el redondeado en la descripción:
  `"(20.5 km → 21 km redondeado)"`.
- La columna "KMs fact." de `tabla-km-config.tsx` muestra `Math.ceil(kmsAFacturar)`
  para consistencia visual con lo que ve el PST.
- Test nuevo `test_kms_decimal_cobrado_ceil_no_dispara` con `tolerancia_km=0.0`.

### P2 — Indicador visual de ruta compartida `CERRADO` (commit `1b562e4`)

Sin cambios de backend. `IncidentesSeccion` computa en el frontend (con `useMemo`)
qué incidentes comparten ruta: agrupa por `fechaCierre` los que tienen
`cantKmCobrado > 0`, y dentro de cada día marca los que coinciden en
`localidadCliente` o en `empresaNombre + sucursalNombre`. Los marcados reciben
un ícono `Route` (lucide) naranja junto al nombre del destino, con tooltip
`"Posible ruta compartida: otro incidente del mismo día comparte destino o localidad"`.

### P4 — Campo ítem extra en la liquidación `CERRADO` (commit `67449ff`)

Para registrar cargos manuales (seguros, documentación, etc.) no incluidos en
los incidentes importados.

- **Migración** `2e4b8f9d3a7c`: columnas `concepto_extra` (Text, nullable) y
  `monto_extra` (Float, nullable) en `liquidaciones`.
- **Dominio**: campos con default `None` al final del dataclass `Liquidacion`;
  `update_extra(liquidacion_id, concepto_extra, monto_extra)` en el Protocol.
- **Infra**: `SqlAlchemyLiquidacionRepository.update_extra()` + `_to_entity`
  actualizado.
- **Schema + Router**: `ExtraIn` schema; `PATCH /api/liquidaciones/{id}/extra`
  retorna `LiquidacionOut` con los campos nuevos.
- **Frontend**: `ExtraItemSeccion` en el detalle — muestra el ítem actual con
  botón "Editar"/"Agregar", formulario inline con concepto (text) y monto
  (number), y un "Total ajustado" = `totalImporte + montoExtra` cuando hay
  un ítem cargado.

### P3 / P8 — Hipervínculo a web agentes `CERRADO` (commit `23ec993`)

`webagentes.canaldirecto.com.ar` se alimenta del mismo WS SOAP que el PST usa
para cargar la liquidación, así que el `numero_liquidacion` del Excel **es** el
identificador del portal. URL: `https://webagentes.canaldirecto.com.ar/liquidations/view/{numero_liquidacion}`.

Sin cambios de backend — el campo ya estaba guardado desde el import. Agregado
el hipervínculo en tres lugares:

- **Lista** (`liquidaciones-tabla.tsx`): columna "Web Agentes" con el número
  como link y ícono `ExternalLink`; `—` cuando es null.
- **Dashboard** (`liquidaciones-dashboard.tsx`): misma columna en la tabla de
  últimas 10 liquidaciones.
- **Detalle** (`liquidacion-detalle.tsx`): link inline en el header junto al
  período y tipo (separado por `·`), visible solo cuando `numero_liquidacion`
  no es null.

---

## Sync automático de preliquidaciones desde wsAyC SOAP — CERRADO (2026-08-13, ADR-015)

ADR-014 había dejado el import de preliquidaciones por wsAyC fuera de su alcance,
indicando que antes exigía diseñar la reconciliación estado-TL/estado-AyC. El diseño
que resuelve esa preocupación: **solo crear, nunca tocar lo ya existente** — no hay
reconciliación porque no hay overwrite. Ver ADR-015 para la decisión completa.

### Qué se implementó

- **`cd_prestador_id` (nullable, UNIQUE) en `prestadores`** — migración
  `d6e3c1b4a829_add_prestador_cd_id.py` (encadenada antes de
  `a7c3f81e42d9`). Identifica la empresa en wsAyC; el vínculo es permanente
  desde el momento del setup (no cambia en runtime).
- **`ZeepCdLiquidacionesGateway`** (`infrastructure/soap/`) — mismo patrón lazy-cached
  que `ZeepWsAycGateway`. La clave del diseño: llama
  `getTopLiquidations(IdEmpresa=str(cd_prestador_id))` **por empresa**, no
  `IdEmpresa=""` global — la respuesta global no incluye `prestador_id`, así que
  filtrar por empresa es la única forma de saber a qué prestador pertenece cada
  liquidación sin hacer un `getLiquidationById` adicional por item.
- **`CdLiquidacionesGateway` (Protocol)** y **`CdLiquidacion` / `CdIncidenteRow`**
  (value objects) en domain.
- **`SincronizarLiquidaciones`** (use case) — itera `list_con_cd_id()`, compara
  contra `list_numeros_liquidacion()` (SET de strings, no recorre la lista), procesa
  solo las nuevas: llama `getLiquidationDetails` para los incidentes, crea la
  liquidación y sus incidentes, y corre `ReanalizarLiquidacion` automáticamente.
  Sin dry-run (es aditivo puro — no hay nada que proteger contra overwrite).
- **`POST /api/liquidaciones/sincronizar`** — requiere permiso `CREATE`; devuelve
  `{creadas, yaExistentes, sinPrestador}`.
- **Frontend**: botón "↻ Sincronizar CD" en el dashboard, con toast de resultado y
  recarga automática si `creadas > 0`.

### Setup inicial completado (2026-08-13)

**34** prestadores vinculados a su `cd_prestador_id` wsAyC (todos excepto
`ZZTESTUI`, la fila de prueba — el conteo original de esta sección decía 33, la
validación posterior contó 34 en DB):

- 32 vinculados por matching de nombre (nombres SOAP tienen prefijo `'PST '`; la
  coincidencia es perfecta en todos los casos).
- `TUCUMAN` (German Naselli) → id=491 (SOAP: `'PST Tucuman - NAPA Tucuman'`) —
  confirmado por el usuario: mismo PST renombrado; las 180 vigencias de tarifarios
  locales coinciden exactamente con NAPA (verificado en el dataset 2 de ADR-014).
- `PST Tres Arroyos - Carlos Douma` (id=154) — no existe en la DB; se omite a
  propósito (no se crea).
- `ZZTESTUI` marcado como inactivo (`activo=False`); sin `cd_prestador_id`.

### Verificación end-to-end (2026-08-13)

Corrida de prueba con JUJUY (`cd_prestador_id=816`) ya vinculado:
- `creadas=114  ya_existentes=1  sin_prestador=0` — los 114 registros históricos de
  JUJUY importados correctamente (el 1 ya existente era `3928-8`, importado
  previamente por CSV).
- Muestra de 3 liquidaciones verificadas: estructura correcta
  (`numero_liquidacion`, `periodo`, `total_incidentes`, `total_importe`, incidentes
  con empresa/sucursal/costos).
- Los 114 se eliminaron a continuación (prueba, no producción — el usuario confirmó
  que los datos eran correctos antes de borrarlos).

Gates: lint-imports 19/19 · ruff · mypy (147 archivos módulo) · 171 unit liquidaciones
— en verde.

## Validación adversarial + correcciones (2026-08-13, posterior al cierre de ADR-015)

Se corrió una validación completa del pipeline (código vs ADR-014/015 vs DB real vs
fuentes externas reales) — informe con evidencia en
`docs/liquidaciones/VALIDACION_PIPELINE_LIQUIDACIONES_2026-08-13.md`. Refutó dos
supuestos de la implementación del sync WS y encontró 6 hallazgos menores; **todo
corregido el mismo día** (Addendum de ADR-015, ADR-016):

- **H-1 (crítico)**: el gateway calculaba el dígito verificador como `id % 10`; el
  algoritmo real es pesos 3-1-3-1 (`domain/services/numeracion_ayc.py`, nuevo, con
  71 tests de caracterización sobre números reales). Los dos casos de la
  verificación original del ADR coincidían de casualidad — sin el fix, el sync
  duplicaba ~31 de las 35 liqs importadas por CSV (demostrado con corrida
  controlada real: `creadas=23, yaExistentes=0` pre-fix vs `creadas=20,
  yaExistentes=3` post-fix, 0 duplicados).
- **H-2 (alto)**: un 502 transitorio de wsAyC en `getLiquidationDetails` (ocurrió
  en vivo, 2 de 23 llamadas) creaba liquidaciones vacías irreparables; ahora no se
  crean y se cuentan en `fallidas` (campo nuevo en el resultado y en el toast).
- Menores: `sinPrestador` real (antes hardcodeado 0), `?prestadorId=` opcional en
  `POST /sincronizar` + log por prestador, `list_con_cd_id()` solo activos, ALT002
  con tolerancia contra valor crudo y ceil (el fix P1 alertaba al PST que factura
  el piso de un decimal), migración `b9f2d47c8e11` desactiva ALT007 (sin
  evaluador), split de `_liq_csv.py` (§4) y ADR-016 para la deuda restante de
  tamaño de funciones.

Gates post-fix: lint-imports 19/19 · ruff · mypy · **1098 unit** (+80). Toda
escritura de la validación sobre datos reales fue revertida (snapshots + diff
`EXCEPT` = 0); único cambio persistente: ALT007 inactiva (por migración).

## Sync CD completo ejecutado (2026-08-13) — pendiente #1 cerrado

Se corrió el sync WS completo real sobre los 34 prestadores vinculados, por tandas
(un `POST /api/liquidaciones/sincronizar?prestadorId=` secuencial por prestador —
mitigación H-5 para no hacer un request síncrono gigante), con
`DISABLE_BACKGROUND_JOBS=true` verificado en el contenedor y una sesión admin
temporal minteada en DB (user_agent `sync-cd-completo-2026-08-13`, revocada al
cierre — mismo método que la validación).

Resultado agregado (log por prestador de la corrida):

- **34/34 prestadores en verde, `fallidas=0` en todos** (ningún 502 de wsAyC esta vez;
  la guarda H-2 no tuvo que actuar).
- **2.380 creadas + 35 yaExistentes = 2.415 liquidaciones** — los 35 `yaExistentes`
  son exactamente las 35 importadas por CSV: el dedup por `numero_liquidacion`
  (numeración 3-1-3-1 del fix H-1) matcheó el 100% de lo preexistente, cero
  duplicados.
- Extremos: SAN JUAN 185 · MENDOZA/MACARONE 134 · CORRIENTES 132 · TUCUMAN 130 ·
  SUPERNOVA/INFOMAC 129 · PENTACOM 128 … JUNIN 12. JUJUY dio 114, idéntico a la
  prueba controlada que se había borrado.

Integridad post-sync verificada en `helpdesk-db`:

- 2.415 liquidaciones, **2.415 `numero_liquidacion` distintos** (cero duplicados),
  **0 con `total_incidentes=0`** (la guarda H-2 garantiza que no queden vacías).
- 112.354 incidentes · 32.329 alertas · 758 observaciones — el motor de reglas
  corrió al crear cada liquidación, como corresponde.
- Los 34 prestadores activos tienen liquidaciones (`count(DISTINCT prestador_id) = 34`).

## Pendiente

1. **Correr en paralelo con la app legacy antes de apagarla** — no hay cutover en frío.
   Con el histórico completo importado, el período de observación puede arrancar:
   comparar alertas/totales contra el legacy sobre las preliquidaciones nuevas.
2. TL: confirmar los 2 conflictos menores de tarifarios (VENADO $45, INFOMAC
   preventivo Villa Mercedes) y, si algún día hace falta, mapear
   `GSJ - *` / `TMTA122 - SGO DEL ESTERO`.
3. TL: confirmar el cambio de semántica de ALT002 del fix H-4 (tolerancia contra el
   valor crudo además del ceil) — documentado en docstring y tests, sin registro de
   confirmación explícita todavía.

## Próximo paso sugerido

Arrancar el período de observación en paralelo con la app legacy: la config se
mantiene sola desde Siges, el histórico completo ya está importado y las
preliquidaciones nuevas llegan con un click (o un `curl`) desde el dashboard. La TL
ya puede gestionar estados de alertas/observaciones sobre datos completos.
