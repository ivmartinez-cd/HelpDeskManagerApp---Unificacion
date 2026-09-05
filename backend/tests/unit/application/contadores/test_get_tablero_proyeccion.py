from datetime import date

from src.modules.contadores.application.dtos.contexto_proceso_dto import ContextoProcesoDto
from src.modules.contadores.application.use_cases.get_tablero_proyeccion import (
    GetTableroProyeccionUseCase,
)
from src.modules.contadores.infrastructure.ejemplo.decisiones_operador_store import (
    DecisionesOperadorStore,
)


def _use_case() -> GetTableroProyeccionUseCase:
    return GetTableroProyeccionUseCase(DecisionesOperadorStore())

_CTX = ContextoProcesoDto(
    fecha_objetivo=date(2026, 4, 30),
    periodo_desde=date(2026, 4, 1),
    periodo_hasta=date(2026, 5, 1),
    id_grupo_economico=1,
    id_anexo=1,
    recesos=[],
)


async def test_arma_una_fila_por_equipo_y_clase() -> None:
    resultado = await _use_case().execute(_CTX)

    assert len(resultado.filas) == 11  # 10 equipos, uno con 2 clases (Mono+Color)
    assert resultado.resumen.total == 11


async def test_equipo_real_cargado_es_verde_y_no_se_estima() -> None:
    resultado = await _use_case().execute(_CTX)

    fila = next(f for f in resultado.filas if f.nro_serie == "CD0001MONO")
    assert fila.es_real is True
    assert fila.semaforo == "VERDE"
    assert fila.estim_propuesto == 122_300


async def test_equipo_salto_imposible_es_rojo_con_borde() -> None:
    resultado = await _use_case().execute(_CTX)

    fila = next(f for f in resultado.filas if f.nro_serie == "CD0005MONO")
    assert fila.semaforo == "ROJO"
    assert fila.borde_salto_imposible is True


async def test_equipo_mono_color_genera_dos_filas() -> None:
    resultado = await _use_case().execute(_CTX)

    filas = [f for f in resultado.filas if f.nro_serie == "CD0011COLOR"]
    assert {f.clase for f in filas} == {"10", "20"}


async def test_resumen_cuenta_sospechosos_por_salto_imposible() -> None:
    resultado = await _use_case().execute(_CTX)

    assert resultado.resumen.sospechosos == 1
    assert resultado.resumen.reales == 1
