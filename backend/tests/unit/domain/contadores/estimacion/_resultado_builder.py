from dataclasses import replace

from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)

_BASE = EstimacionResultado(
    estim_propuesto=0,
    impresiones=0,
    tipo_toma=14,
    fuente="Historia_Propia",
    metodo_detalle="Entre dos reales",
)


def make_resultado(**overrides: object) -> EstimacionResultado:
    return replace(_BASE, **overrides)  # type: ignore[arg-type]
