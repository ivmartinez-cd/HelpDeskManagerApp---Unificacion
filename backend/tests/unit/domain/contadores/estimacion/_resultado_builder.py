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
    requiere_confirmacion=False,
    semaforo="VERDE",
    borde_salto_imposible=False,
    coloreo=None,
    nota_operador=None,
    meses_sin_real_en_alerta=False,
    dias_par_pl=None,
    ajustado_por_receso=False,
    dias_receso_descontados=0,
)


def make_resultado(**overrides: object) -> EstimacionResultado:
    return replace(_BASE, **overrides)  # type: ignore[arg-type]
