"""ALT010 — Serie Duplicada: la misma serie (`nro_serie`) recibió un servicio
preventivo y uno correctivo dentro del mismo período (mes/año de `fecha_cierre`).
Mismo criterio de "duplicado" que ALT004, pero la clave de comparación es
serie+tipo de servicio en vez de `numero_incidente` — la búsqueda de coincidencias
(mismo prestador, serie, tipo opuesto y período) vive en `motor.py::_coincidencias_alt010`."""

from collections.abc import Sequence

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import Hallazgo


def evaluar_alt010(incidente: Incidente, coincidencias: Sequence[Incidente]) -> list[Hallazgo]:
    if not coincidencias:
        return []
    return [_hallazgo(incidente, coincidencias)]


def _hallazgo(incidente: Incidente, coincidencias: Sequence[Incidente]) -> Hallazgo:
    numeros = sorted({i.numero_incidente for i in coincidencias})
    descripcion = (
        f"Serie {incidente.nro_serie} duplicada: preventivo y correctivo en el mismo "
        f"período (incidente(s) #{', #'.join(numeros)})"
    )
    contexto = {
        "nro_serie": incidente.nro_serie,
        "tipo_servicio": incidente.tipo,
        "incidentes_relacionados": numeros,
        "serie_duplicada": True,
    }
    return Hallazgo(descripcion, contexto)
