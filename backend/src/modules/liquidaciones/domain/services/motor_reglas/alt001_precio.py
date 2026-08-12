"""ALT001 — Precio Incorrecto: costo de servicio cobrado vs. tarifario vigente.

Tolerancia fija de $0.01 (no viene de `ReglaAlerta.configuracion` — así era en el
legacy, confirmado leyendo `alt001_precio.py`)."""

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import Hallazgo

TOLERANCIA_PRECIO = 0.01


def evaluar_alt001(incidente: Incidente, tarifario: Tarifario | None) -> list[Hallazgo]:
    if incidente.fecha_cierre is None or tarifario is None:
        return []
    diferencia = abs((incidente.costo_servicio_cobrado or 0) - tarifario.costo_servicio)
    if diferencia <= TOLERANCIA_PRECIO:
        return []
    return [_hallazgo(incidente, tarifario, diferencia)]


def _hallazgo(incidente: Incidente, tarifario: Tarifario, diferencia: float) -> Hallazgo:
    cobrado = incidente.costo_servicio_cobrado or 0
    descripcion = (
        f"Precio cobrado ${cobrado:,.2f} difiere del tarifario "
        f"${tarifario.costo_servicio:,.2f} (diferencia: ${diferencia:,.2f})"
    )
    contexto = {
        "cobrado": cobrado,
        "esperado": tarifario.costo_servicio,
        "diferencia": round(diferencia, 2),
        "tipo_servicio": incidente.tipo,
    }
    return Hallazgo(descripcion, contexto)
