"""Los valores que aceptan los CHECK de las tablas de Despachados son exactamente los de
los enums del dominio: si se agrega un color, un tipo de acción o un resultado de un solo
lado, la base rechazaría lo que el dominio produce (o al revés)."""

import re
from enum import StrEnum

import pytest
from sqlalchemy import CheckConstraint, Table

from src.modules.insumos.domain.entities.despachados.accion_registrada import (
    ResultadoAccion,
    TipoAccion,
)
from src.modules.insumos.domain.entities.despachados.corrida import OrigenCorrida
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.infrastructure.models.despacho_accion_model import DespachoAccionModel
from src.modules.insumos.infrastructure.models.despacho_corrida_model import (
    DespachoCorridaModel,
)
from src.modules.insumos.infrastructure.models.despacho_envio_model import DespachoEnvioModel
from src.modules.insumos.infrastructure.models.despacho_estado_historial_model import (
    DespachoEstadoHistorialModel,
)


def _valores_del_check(tabla: Table, nombre: str) -> set[str]:
    [check] = [c for c in tabla.constraints if isinstance(c, CheckConstraint) and c.name == nombre]
    return set(re.findall(r"'([a-z_]+)'", str(check.sqltext)))


@pytest.mark.parametrize(
    ("tabla", "nombre", "enum"),
    [
        (DespachoEnvioModel.__table__, "ck_insumos_despacho_envio_color", ColorSemaforo),
        (
            DespachoEstadoHistorialModel.__table__,
            "ck_insumos_despacho_estado_historial_color",
            ColorSemaforo,
        ),
        (DespachoAccionModel.__table__, "ck_insumos_despacho_accion_tipo", TipoAccion),
        (DespachoAccionModel.__table__, "ck_insumos_despacho_accion_resultado", ResultadoAccion),
        (DespachoCorridaModel.__table__, "ck_insumos_despacho_corrida_origen", OrigenCorrida),
    ],
    ids=["color-envio", "color-historial", "tipo-accion", "resultado-accion", "origen-corrida"],
)
def test_check_acepta_exactamente_los_valores_del_enum(
    tabla: Table, nombre: str, enum: type[StrEnum]
) -> None:
    assert _valores_del_check(tabla, nombre) == {valor.value for valor in enum}
