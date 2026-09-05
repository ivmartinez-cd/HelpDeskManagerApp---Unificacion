"""ALT008 — Tarifario Inexistente: no hay ninguna fila de `Tarifario` aplicable al tipo
de servicio/fecha del incidente (comparte la resolución de tarifario con ALT001, pero
dispara cuando NO se encuentra ninguno, en vez de comparar montos)."""

import uuid

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import Hallazgo


def evaluar_alt008(
    incidente: Incidente, tarifario: Tarifario | None, spst_id: uuid.UUID | None
) -> list[Hallazgo]:
    if incidente.fecha_cierre is None or tarifario is not None:
        return []
    descripcion = (
        f"Sin tarifario para tipo '{incidente.tipo}' en el período {incidente.fecha_cierre}"
    )
    contexto = {
        "tipo_servicio": incidente.tipo,
        "fecha_cierre": str(incidente.fecha_cierre),
        # None = todavía no se pudo resolver el SPST de este incidente (falta
        # vincularlo en Tabla KM) — la UI usa esto para linkear a "Vincular
        # SPST" en vez de "Cargar tarifa" cuando corresponde.
        "spst_id": str(spst_id) if spst_id else None,
    }
    return [Hallazgo(descripcion, contexto)]
