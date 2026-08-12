"""ALT003 — Posible Viático Duplicado: mismo prestador/empresa/sucursal/fecha con KMs
cobrados en más de un incidente. El parámetro `ventana_dias` de `ReglaAlerta.configuracion`
NUNCA se lee acá — confirmado empíricamente en la caracterización (22 tests, ver
`LIQUIDACION_PRESTADORES_CARACTERIZACION.md` §7): el legacy compara `fecha_cierre` exacto,
no una ventana. No implementarlo sería inventar comportamiento nuevo, así que se porta
la config muerta tal cual — no agregarle uso sin que el usuario lo pida."""

from collections.abc import Sequence

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import Hallazgo


def evaluar_alt003(incidente: Incidente, similares: Sequence[Incidente]) -> list[Hallazgo]:
    if not incidente.cant_km_cobrado or not incidente.fecha_cierre or not similares:
        return []
    return [_hallazgo(incidente, similares)]


def _hallazgo(incidente: Incidente, similares: Sequence[Incidente]) -> Hallazgo:
    refs = [f"#{i.numero_incidente}" for i in similares[:3]]
    descripcion = (
        f"Posible viático duplicado: {len(similares)} incidente(s) con KMs en la misma "
        f"sucursal el mismo día: {', '.join(refs)}"
    )
    contexto = {
        "incidentes_similares": [i.numero_incidente for i in similares],
        "empresa": incidente.empresa_nombre,
        "sucursal": incidente.sucursal_nombre,
        "fecha": str(incidente.fecha_cierre),
    }
    return Hallazgo(descripcion, contexto)
