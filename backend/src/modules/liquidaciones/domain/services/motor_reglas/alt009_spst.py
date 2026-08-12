"""ALT009 — Par Empresa+Sucursal no encontrado en Tabla KM. Solo dispara si el
incidente cobró KMs (`cant_km_cobrado>0`) — si no cobró KMs, el legacy corta antes de
buscar en Tabla KM, así que nunca dispara aunque el par no exista (confirmado en la
caracterización, no es un bug a corregir en esta migración)."""

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import Hallazgo


def evaluar_alt009(incidente: Incidente, tabla_km: TablaKm | None) -> list[Hallazgo]:
    if not incidente.empresa_nombre or not incidente.sucursal_nombre:
        return []
    if not incidente.cant_km_cobrado:
        return []
    if tabla_km is not None:
        return []
    descripcion = (
        f"Par Empresa+Sucursal no encontrado en Tabla KM: "
        f"'{incidente.empresa_nombre}' — '{incidente.sucursal_nombre}'"
    )
    contexto = {"empresa": incidente.empresa_nombre, "sucursal": incidente.sucursal_nombre}
    return [Hallazgo(descripcion, contexto)]
