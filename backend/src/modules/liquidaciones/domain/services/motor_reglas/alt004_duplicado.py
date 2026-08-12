"""ALT004 — Servicio Duplicado: mismo `numero_incidente` ya liquidado antes para el
mismo prestador (cualquier liquidación, no solo la actual — el dígito verificador
módulo-10 de la numeración real de AyC es justamente lo que hace esta comparación
confiable entre orígenes CSV/WS, aunque WS quede fuera de esta migración)."""

from collections.abc import Sequence

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import Hallazgo


def evaluar_alt004(incidente: Incidente, duplicados: Sequence[Incidente]) -> list[Hallazgo]:
    if not duplicados:
        return []
    return [_hallazgo(incidente, duplicados)]


def _hallazgo(incidente: Incidente, duplicados: Sequence[Incidente]) -> Hallazgo:
    liq_ids = sorted({str(i.liquidacion_id) for i in duplicados})
    descripcion = (
        f"Incidente #{incidente.numero_incidente} ya fue liquidado en "
        f"{len(duplicados)} liquidación(es) anterior(es)"
    )
    contexto = {
        "numero_incidente": incidente.numero_incidente,
        "liquidaciones_previas": liq_ids,
    }
    return Hallazgo(descripcion, contexto)
