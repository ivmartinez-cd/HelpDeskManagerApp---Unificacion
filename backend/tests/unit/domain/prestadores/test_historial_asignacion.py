import uuid
from datetime import date

from src.modules.prestadores.domain.entities.asignacion_historial import AsignacionHistorial
from src.modules.prestadores.domain.services.historial_asignacion import (
    operador_vigente,
    planificar_reasignacion,
)

_PST = uuid.uuid4()


def _tramo(desde: date, hasta: date | None) -> AsignacionHistorial:
    return AsignacionHistorial(
        id=uuid.uuid4(), prestador_id=_PST, operador_id=uuid.uuid4(), desde=desde, hasta=hasta
    )


def test_cierra_el_tramo_vigente_un_dia_antes() -> None:
    abierto = _tramo(date(2026, 1, 1), None)

    plan = planificar_reasignacion([abierto], date(2026, 9, 6))

    assert plan.cerrar == [abierto]
    assert plan.borrar == []
    assert plan.cierre == date(2026, 9, 5)


def test_borra_los_tramos_que_empiezan_en_desde_o_despues_y_recorta_el_que_alcanza() -> None:
    viejo = _tramo(date(2026, 1, 1), date(2026, 9, 30))
    futuro_cerrado = _tramo(date(2026, 10, 1), date(2026, 10, 31))
    futuro_abierto = _tramo(date(2026, 11, 1), None)

    plan = planificar_reasignacion([viejo, futuro_cerrado, futuro_abierto], date(2026, 9, 6))

    assert plan.borrar == [futuro_cerrado, futuro_abierto]
    assert plan.cerrar == [viejo]
    assert plan.cierre == date(2026, 9, 5)


def test_no_toca_tramos_que_terminan_antes_de_desde() -> None:
    historico = _tramo(date(2025, 1, 1), date(2025, 12, 31))

    plan = planificar_reasignacion([historico], date(2026, 9, 6))

    assert plan.borrar == []
    assert plan.cerrar == []


def test_operador_vigente_devuelve_el_tramo_que_cubre_la_fecha() -> None:
    viejo = _tramo(date(2026, 1, 1), date(2026, 9, 30))
    futuro = _tramo(date(2026, 10, 1), None)

    assert operador_vigente([viejo, futuro], date(2026, 9, 5)) is viejo
    assert operador_vigente([viejo, futuro], date(2026, 10, 1)) is futuro
    assert operador_vigente([viejo, futuro], date(2025, 12, 31)) is None
