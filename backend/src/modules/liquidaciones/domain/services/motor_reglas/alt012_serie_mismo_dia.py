"""ALT012 — Serie Repetida Mismo Día: la misma serie (`nro_serie`) aparece en dos o
más incidentes distintos con la misma `fecha_cierre`, sin importar el tipo de
servicio. A diferencia de ALT010 (que solo compara preventivo vs correctivo dentro
del mismo mes), esta regla cubre el caso de dos cargas del mismo equipo el mismo
día — por ejemplo dos preventivos duplicados con números de incidente distintos
(caso real reportado por Iván 2026-09-08). Puede coincidir con ALT010 cuando además
el tipo es opuesto y el día coincide exacto; no se suprimen entre sí porque
describen coincidencias distintas (mismo mes vs mismo día exacto)."""

from collections.abc import Sequence

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import Hallazgo


def evaluar_alt012(incidente: Incidente, coincidencias: Sequence[Incidente]) -> list[Hallazgo]:
    if not coincidencias:
        return []
    return [_hallazgo(incidente, coincidencias)]


def _hallazgo(incidente: Incidente, coincidencias: Sequence[Incidente]) -> Hallazgo:
    numeros = sorted({i.numero_incidente for i in coincidencias})
    descripcion = (
        f"Serie {incidente.nro_serie} repetida el mismo día "
        f"({incidente.fecha_cierre}): incidente(s) #{', #'.join(numeros)}"
    )
    contexto = {
        "nro_serie": incidente.nro_serie,
        "fecha_cierre": incidente.fecha_cierre.isoformat() if incidente.fecha_cierre else None,
        "incidentes_relacionados": numeros,
        "serie_repetida_mismo_dia": True,
    }
    return Hallazgo(descripcion, contexto)
