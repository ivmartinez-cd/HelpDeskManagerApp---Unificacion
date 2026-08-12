"""ALT008 — Tarifario Inexistente: no hay ninguna fila de `Tarifario` aplicable al tipo
de servicio/fecha del incidente (comparte la resolución de tarifario con ALT001, pero
dispara cuando NO se encuentra ninguno, en vez de comparar montos)."""

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import Hallazgo


def evaluar_alt008(incidente: Incidente, tarifario: Tarifario | None) -> list[Hallazgo]:
    if incidente.fecha_cierre is None or tarifario is not None:
        return []
    descripcion = (
        f"Sin tarifario para tipo '{incidente.tipo}' en el período {incidente.fecha_cierre}"
    )
    contexto = {
        "tipo_servicio": incidente.tipo,
        "fecha_cierre": str(incidente.fecha_cierre),
    }
    return [Hallazgo(descripcion, contexto)]
