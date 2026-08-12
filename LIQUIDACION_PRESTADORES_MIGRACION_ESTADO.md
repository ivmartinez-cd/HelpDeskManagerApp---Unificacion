# Estado de la migración — Liquidacion-Prestadores

Ver `LIQUIDACION_PRESTADORES_CARACTERIZACION.md` para el reconocimiento funcional previo
(motor de reglas, alcance, decisión de dejar WS AyC afuera). Este doc trackea el avance
del port en sí — qué está hecho, verificado y committeado, y qué falta.

Regla del proyecto para este módulo (pedido explícito del usuario): **no tocar el
contenedor Docker de la app legacy sin permiso**. El trabajo de port corre contra
`helpdesk-manager-backend` únicamente.

## Hecho (verificado con ruff + mypy + lint-imports + pytest, committeado)

1. **Modelo de datos** — 10 entidades de dominio + modelos SQLAlchemy + 2 migraciones
   Alembic (`b74bde547b01`, `0468811de473`), aplicadas a `helpdesk-db`.
2. **Motor de reglas** — port puro a dominio (`domain/services/motor_reglas/`) de los 7
   evaluadores ALT001-009 del legacy, con 23 tests de caracterización
   (`tests/unit/domain/liquidaciones/test_motor_reglas.py`).
3. **Repositorios** — 10 Protocols + implementaciones SQLAlchemy (Prestador, Spst,
   Tarifario, TablaKm, ReglaAlerta, Liquidacion, Incidente, Alerta, Resolucion,
   Observacion).
4. **Casos de uso de lectura + reanálisis** — `ListLiquidaciones`,
   `GetLiquidacionDetalle`, `ReanalizarLiquidacion`.
5. **Endpoints HTTP** (`GET /api/liquidaciones`, `GET /api/liquidaciones/{id}`,
   `POST /api/liquidaciones/{id}/reanalyze`).
6. **Importación CSV/HTML** (recién armada en esta sesión):
   - Parsing puro en dominio (`domain/services/importacion/`: `_valores.py`,
     `normalizacion.py`, `metadata.py`, `constructor.py`) — sin pandas, testeable sin
     I/O.
   - `PandasLiquidacionFileParser` en infraestructura (único punto que importa
     pandas/lxml, agregados como dependencias nuevas del backend).
   - Caso de uso `ImportarLiquidacion`, compone `ReanalizarLiquidacion` en vez de
     duplicar la corrida del motor.
   - Endpoint `POST /api/liquidaciones/importar` (registrado antes de
     `/{liquidacion_id}` a propósito — ver docstring del router).
   - Permiso `liquidaciones.create` agregado a `well_known_permissions.py`.
   - Fakes de test actualizados (`FakePrestadorRepository` nuevo,
     `FakeLiquidacionRepository.create()` con `total_incidentes`/`total_importe`,
     `FakeIncidenteRepository.bulk_create()` nuevo) — usados por
     `ReanalizarLiquidacion` sin romper sus 3 tests existentes.
7. **Tests de `ImportarLiquidacion`** — 5 tests en
   `tests/unit/application/liquidaciones/test_importar_liquidacion.py`:
   - `test_prestador_inexistente_lanza_error` — prestador inexistente → `PrestadorNoEncontradoError`.
   - `test_happy_path_crea_liquidacion_con_totales_del_parseo` — `total_incidentes` y `total_importe` derivados del parseo.
   - `test_happy_path_crea_incidentes_via_bulk_create` — incidentes persistidos con `bulk_create`.
   - `test_happy_path_dispara_reanalizar_y_retorna_sus_totales` — alertas del motor reflejadas en el DTO de salida.
   - `test_parser_recibe_contenido_y_nombre_de_archivo` — el parser recibe exactamente lo que llega del endpoint.
   - `FakeLiquidacionFileParser` agregado a `tests/unit/domain/liquidaciones/fakes.py`.

8. **Tests de dominio de funciones puras de parsing** — 66 tests en
   `tests/unit/domain/liquidaciones/test_importacion_parsing.py`:
   - `TestParseMonto` (12): enteros, decimales argentinos (`1.500,00`), prefijo `$`,
     vacíos, `nan`, valores ilegibles, y documentación del comportamiento con floats.
   - `TestParseFecha` (9): formatos `yyyymmdd`, `dd/mm/yyyy`, `yyyy-mm-dd`, `dd/mm/yy`,
     `dd-mm-yyyy`, `None`, vacío, `nan`, ilegible.
   - `TestMapearColumnas` (6): nombres exactos, variantes, columna desconocida,
     lista vacía, alias `cliente→empresa`, `precio km→costo_km`.
   - `TestExtraerNumeroLiquidacion` (4): patrón `N-N`, guion bajo normalizado, sin patrón,
     case-insensitive.
   - `TestExtraerTipoLiquidacion` (6): regular, preco, cc, centro_civico, deposito, bodega.
   - `TestExtraerPeriodo` (5): desde fechas de incidentes, más frecuente gana, fallback a
     nombre de archivo, enero sube año, sin datos.
   - `TestNormalizarTipoServicio` (12): todos los tipos + vacío + desconocido +
     precedencia instalación sobre correctivo.
   - `TestConstruirIncidenteImportado` (8): happy path, extracción de patrón del número,
     filas `nan`/encabezado repetido/vacías → `None`, pasa_it=NO, rubro vacío→Impresoras,
     separador de miles.
   - `TestArmarResultadoImportacion` (4): resultado completo, filtro de filas inválidas,
     lista vacía, período derivado de fechas.

Verificado en este corte: `ruff check` (limpio), `mypy` (sin issues), `pytest
tests/unit/domain/liquidaciones tests/unit/application/liquidaciones` (97/97).

## Pendiente

1. **Smoke test del endpoint de importación con un archivo real** — el resto de los
   endpoints ya se probaron con requests HTTP reales contra el contenedor; falta
   hacer lo mismo con `POST /api/liquidaciones/importar` con un `.xls`
   (HTML-con-extensión-.xls) real de ejemplo, no solo verificación estática.
3. **Frontend** — nada arrancado todavía. Handoff en `Handoff Liquidacion Prestadores.md`
   (raíz del repo). Pantallas: Dashboard, Liquidaciones, Prestadores, SPSTs, Tarifarios,
   Tabla KM (6 pantallas).
4. **Catálogo de permisos** — `liquidaciones.is_enabled` sigue en `False`. Activarlo
   solo cuando el usuario lo pida explícitamente, una vez que exista frontend.
5. **Casos de uso de escritura para el resto de las entidades de configuración**
   (crear/editar Prestador, Spst, Tarifario, TablaKm) — todavía no se portaron; solo
   están los repositorios con sus métodos `create`. Hacen falta cuando se construya el
   frontend de configuración.

## Próximo paso sugerido

Arrancar el frontend de liquidaciones usando el handoff `Handoff Liquidacion Prestadores.md`.
El smoke test del endpoint (pendiente 1) requiere Docker corriendo y un `.xls` real de ejemplo.
