from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)


def resultado_real(entrada: EstimacionInput) -> EstimacionResultado:
    """Fila con lectura real ya cargada para el período: no se estima nada,
    las impresiones son las reales (`FC_ImpresionesReales`)."""
    return EstimacionResultado(
        estim_propuesto=None,
        impresiones=entrada.impresiones_reales,
        tipo_toma=None,
        fuente="Sin_Estimar",
        metodo_detalle="Lectura real cargada para el período",
        coloreo="NORMAL",
        detalle_calculo="Lectura real registrada para el período.",
    )


def resultado_pendiente() -> EstimacionResultado:
    """`Pendiente` del legacy (`RequierePendiente`): ninguna rama pudo
    estimar. No pide confirmación: lo que hace falta es marcarla pendiente.
    Sin marcadores (los aplica quien lo llama)."""
    return EstimacionResultado(
        estim_propuesto=None,
        impresiones=None,
        tipo_toma=None,
        fuente="Pendiente",
        metodo_detalle="Sin datos suficientes para estimar",
        detalle_calculo="Sin datos suficientes para estimar — marcar pendiente.",
    )
