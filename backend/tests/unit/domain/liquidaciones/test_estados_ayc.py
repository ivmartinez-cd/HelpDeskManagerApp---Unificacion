"""estados_ayc: mapeo ida y vuelta entre el id numérico de AyC y la constante
local, fallback por nombre cuando no hay id, y `abierta` como local-only."""

import pytest

from src.modules.liquidaciones.domain.entities.liquidacion import (
    ESTADO_ABIERTA,
    ESTADO_APROBADA,
    ESTADO_CERRADA,
    ESTADO_OBSERVADA,
    ESTADO_PRELIQUIDADA,
    ESTADO_RECIBIDA,
)
from src.modules.liquidaciones.domain.services.estados_ayc import (
    estado_id_para_escribir,
    estado_local_desde_ayc,
)

_TODOS = [
    (1, ESTADO_PRELIQUIDADA, "Preliquidada"),
    (2, ESTADO_RECIBIDA, "Recibida"),
    (3, ESTADO_OBSERVADA, "Observada"),
    (4, ESTADO_APROBADA, "Aprobada"),
    (5, ESTADO_CERRADA, "Cerrada"),
]


@pytest.mark.parametrize("estado_id,local,nombre_ayc", _TODOS)
def test_estado_id_y_local_mapean_ida_y_vuelta(
    estado_id: int, local: str, nombre_ayc: str
) -> None:
    assert estado_id_para_escribir(local) == estado_id
    assert estado_local_desde_ayc(estado_id=estado_id, nombre=nombre_ayc) == local


@pytest.mark.parametrize("estado_id,local,nombre_ayc", _TODOS)
def test_fallback_por_nombre_cuando_no_hay_estado_id(
    estado_id: int, local: str, nombre_ayc: str
) -> None:
    assert estado_local_desde_ayc(estado_id=None, nombre=nombre_ayc) == local
    # case-insensitive, con espacios — tal como puede venir de un campo AyC
    assert estado_local_desde_ayc(estado_id=None, nombre=f"  {nombre_ayc.upper()}  ") == local


def test_estado_id_tiene_prioridad_sobre_un_nombre_inconsistente() -> None:
    """Si vienen ambos y no coinciden, el id numérico manda (es el que usa el
    propio SOAP para escribir — más confiable que el nombre de display)."""
    assert estado_local_desde_ayc(estado_id=4, nombre="Observada") == ESTADO_APROBADA


def test_estado_desconocido_devuelve_none() -> None:
    assert estado_local_desde_ayc(estado_id=99, nombre="Anulada") is None
    assert estado_local_desde_ayc(estado_id=None, nombre="Anulada") is None
    assert estado_local_desde_ayc(estado_id=None, nombre="") is None


def test_abierta_es_local_only() -> None:
    with pytest.raises(KeyError):
        estado_id_para_escribir(ESTADO_ABIERTA)
    assert all(
        estado_local_desde_ayc(estado_id=eid, nombre=n) != ESTADO_ABIERTA for eid, _, n in _TODOS
    )
