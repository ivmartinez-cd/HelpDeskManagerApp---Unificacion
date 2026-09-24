from src.modules.contadores.domain.services.estimacion.t4_como_llegada import (
    estimar_con_t4,
    t4_aplicable,
)
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    FuenteEstimacion,
)

_TIPO_TOMA_ESTIMADO = 14
_TEXTO_EN_TRANSITO = "En tránsito a taller — sin movimiento, se repite contador anterior."
_TEXTO_BACKUP = "Backup sin T4 ST — sin movimiento, se repite contador anterior."


def resolver_backup(entrada: EstimacionInput) -> EstimacionResultado:
    """Backup (estados 3/8) del legacy: con T4 ST válido se toma su valor tal
    cual, sin proyectar — un Backup no tiene tasa de impresión representativa
    (`EstimarConT4ST(proyectar: false)`: fuente T4_ST, tipo 14); sin T4
    válido se repite el contador anterior. No mira recesos."""
    if t4_aplicable(entrada):
        resultado = estimar_con_t4(ContextoEstimacion(entrada, []), proyectar=False)
        if resultado is not None:
            return resultado
    return _sin_movimiento(entrada, "Backup_SinST")


def resolver_en_transito(entrada: EstimacionInput) -> EstimacionResultado:
    return _sin_movimiento(entrada, "EnTransito")


def _sin_movimiento(entrada: EstimacionInput, fuente: FuenteEstimacion) -> EstimacionResultado:
    """`CrearSinMovimiento` del legacy: propone el contador anterior tal cual
    (`None` si el equipo no tiene), 0 impresiones, tipo 14, siempre a
    confirmar."""
    anterior = entrada.ultimo_contador_facturado
    texto = _TEXTO_EN_TRANSITO if fuente == "EnTransito" else _TEXTO_BACKUP
    return EstimacionResultado(
        estim_propuesto=anterior.valor if anterior is not None else None,
        impresiones=0,
        tipo_toma=_TIPO_TOMA_ESTIMADO,
        fuente=fuente,
        metodo_detalle="Sin movimiento",
        metodo="ContadorAnterior",
        requiere_confirmacion=True,
        detalle_calculo=texto,
        etiqueta_nivel=texto,
    )
