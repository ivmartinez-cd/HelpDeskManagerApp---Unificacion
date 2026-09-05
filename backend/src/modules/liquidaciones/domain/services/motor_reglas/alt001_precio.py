"""ALT001 — Precio Incorrecto: costo de servicio cobrado vs. tarifario vigente.

Tolerancia fija de $0.01 (no viene de `ReglaAlerta.configuracion` — así era en el
legacy, confirmado leyendo `alt001_precio.py`)."""

from src.modules.liquidaciones.domain.entities.acuerdo_precio_cliente import (
    AcuerdoPrecioCliente,
)
from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import Hallazgo

TOLERANCIA_PRECIO = 0.01


def evaluar_alt001(
    incidente: Incidente,
    tarifario: Tarifario | None,
    acuerdo: AcuerdoPrecioCliente | None = None,
) -> list[Hallazgo]:
    """Con un acuerdo de precio por cliente, el esperado es el del acuerdo
    (`precio_esperado`), no el tarifario — ver la entidad."""
    if incidente.fecha_cierre is None:
        return []
    precio_tarifario = tarifario.costo_servicio if tarifario else None
    esperado = acuerdo.precio_esperado(precio_tarifario) if acuerdo else precio_tarifario
    if esperado is None:
        return []
    diferencia = abs((incidente.costo_servicio_cobrado or 0) - esperado)
    if diferencia <= TOLERANCIA_PRECIO:
        return []
    return _hallazgo(incidente, esperado, diferencia, acuerdo)


def _hallazgo(
    incidente: Incidente,
    esperado: float,
    diferencia: float,
    acuerdo: AcuerdoPrecioCliente | None,
) -> list[Hallazgo]:
    cobrado = incidente.costo_servicio_cobrado or 0
    contexto = {
        "cobrado": cobrado,
        "esperado": esperado,
        "diferencia": round(diferencia, 2),
        "tipo_servicio": incidente.tipo,
    }
    if acuerdo:
        contexto["acuerdo_id"] = str(acuerdo.id)
    return [Hallazgo(_descripcion(cobrado, esperado, diferencia, acuerdo), contexto)]


def _descripcion(
    cobrado: float, esperado: float, diferencia: float, acuerdo: AcuerdoPrecioCliente | None
) -> str:
    referencia = (
        f"del acuerdo con {acuerdo.empresa_nombre} ({acuerdo.motivo})"
        if acuerdo
        else "del tarifario"
    )
    return (
        f"Precio cobrado ${cobrado:,.2f} difiere {referencia} "
        f"${esperado:,.2f} (diferencia: ${diferencia:,.2f})"
    )
