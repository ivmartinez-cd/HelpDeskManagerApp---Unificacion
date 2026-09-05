from src.modules.contadores.domain.services.estimacion.antiguedad import historia_en_alerta
from src.modules.contadores.domain.services.estimacion.entre_dos_reales import (
    hay_par_utilizable,
    intentar_entre_dos_reales,
)
from src.modules.contadores.domain.services.estimacion.estado_especial import (
    resolver_backup,
    resolver_en_transito,
)
from src.modules.contadores.domain.services.estimacion.parque import intentar_parque
from src.modules.contadores.domain.services.estimacion.recesos import recesos_aplicables
from src.modules.contadores.domain.services.estimacion.t4_como_llegada import (
    intentar_t4_como_llegada,
)
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)

_RESULTADO_SIN_ESTIMAR = EstimacionResultado(
    estim_propuesto=None,
    impresiones=None,
    tipo_toma=None,
    fuente="Sin_Estimar",
    metodo_detalle="Lectura real cargada para el período",
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


def estimar(entrada: EstimacionInput) -> EstimacionResultado:
    """Cascada de decisión completa para un (equipo, clase de contador)
    pendiente de estimar (REGLAS_DE_NEGOCIO §5). El primer caso que aplica
    gana; cada `intentar_*` devuelve `None` cuando no aplica y se sigue
    probando el siguiente nivel."""
    if not entrada.pendiente_estimar:
        return _RESULTADO_SIN_ESTIMAR
    if entrada.estado_maquina == "BACKUP":
        return resolver_backup(entrada)
    if entrada.estado_maquina == "EN_TRANSITO":
        return resolver_en_transito(entrada)
    return _estimar_normal(entrada)


def _estimar_normal(entrada: EstimacionInput) -> EstimacionResultado:
    recesos = recesos_aplicables(entrada.recesos, entrada.id_anexo, entrada.id_grupo_economico)
    ctx = ContextoEstimacion(entrada, recesos)
    en_alerta = historia_en_alerta(entrada.ultimo_real, entrada.tecnologia, entrada.fecha_objetivo)

    if hay_par_utilizable(entrada, en_alerta):
        resultado = intentar_entre_dos_reales(ctx)
        if resultado is not None:
            return resultado

    resultado_t4 = intentar_t4_como_llegada(ctx, en_alerta)
    if resultado_t4 is not None:
        return resultado_t4

    resultado_parque = intentar_parque(ctx, en_alerta)
    if resultado_parque is not None:
        return resultado_parque

    return _resultado_pendiente(en_alerta)


def _resultado_pendiente(en_alerta: bool) -> EstimacionResultado:
    return EstimacionResultado(
        estim_propuesto=None,
        impresiones=None,
        tipo_toma=None,
        fuente="Pendiente",
        metodo_detalle="Sin datos suficientes para estimar",
        requiere_confirmacion=True,
        semaforo="ROJO",
        borde_salto_imposible=False,
        coloreo=None,
        nota_operador=None,
        meses_sin_real_en_alerta=en_alerta,
        dias_par_pl=None,
        ajustado_por_receso=False,
        dias_receso_descontados=0,
    )
