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

Verificado en este corte: `ruff check` (limpio), `mypy` (sin issues), `pytest
tests/unit/domain/liquidaciones tests/unit/application/liquidaciones` (31/31).

## Pendiente

1. **Tests de dominio de las funciones puras de parsing** — sin pandas:
   `construir_incidente_importado`, `armar_resultado_importacion`, `mapear_columnas`,
   `extraer_numero_liquidacion`/`extraer_tipo_liquidacion`/`extraer_periodo`,
   `parse_monto`/`parse_fecha`. Van en `tests/unit/domain/liquidaciones/`, idealmente
   como caracterización contra los mismos casos que ya se usaron para verificar el
   parser contra el legacy (nombres de archivo reales, filas con montos con
   separador de miles, fechas en los formatos que exporta el sistema fuente).
2. **Smoke test del endpoint de importación con un archivo real** — el resto de los
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

Tests de dominio de las funciones puras de parsing (punto 1 de pendientes), o arrancar
el frontend de liquidaciones usando el handoff `Handoff Liquidacion Prestadores.md`.
El smoke test del endpoint (punto 2) requiere Docker corriendo y un `.xls` real de ejemplo.
