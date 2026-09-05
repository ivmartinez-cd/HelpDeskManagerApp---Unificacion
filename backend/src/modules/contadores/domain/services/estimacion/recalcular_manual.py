from dataclasses import replace

from src.modules.contadores.domain.services.estimacion.armado_resultado import con_marcadores
from src.modules.contadores.domain.services.estimacion.marcadores import (
    SenalesRama,
    evaluar_marcadores,
)
from src.modules.contadores.domain.services.estimacion.regla_de_tres import (
    ResultadoReglaDeTres,
    calcular_regla_de_tres,
)
from src.modules.contadores.domain.services.estimacion.validez_t4 import par_valido
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    FuenteEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef

_TIPO_TOMA_ST = 4

_BASE = EstimacionResultado(
    estim_propuesto=0,
    impresiones=0,
    tipo_toma=14,
    fuente="Historia_Propia",
    metodo_detalle="Partida/Llegada elegidas a mano",
    requiere_confirmacion=True,
    semaforo="VERDE",
    borde_salto_imposible=False,
    coloreo=None,
    nota_operador=None,
    meses_sin_real_en_alerta=False,
    dias_par_pl=None,
    ajustado_por_receso=False,
    dias_receso_descontados=0,
)


def recalcular_con_pl(
    ctx: ContextoEstimacion, partida: LecturaRef, llegada: LecturaRef
) -> EstimacionResultado | None:
    """Override manual (REGLAS_DE_NEGOCIO §8): misma validez que el cálculo
    automático, Llegada T4 igual graba T14 pero fuente T4_ST (CASOS_DE_PRUEBA §12)."""
    if not par_valido(partida, llegada):
        return None
    r3 = calcular_regla_de_tres(partida, llegada, ctx)
    resultado = _borrador(r3, llegada)
    senales = SenalesRama(requiere_confirmacion_otro_motivo=True)
    marcadores = evaluar_marcadores(ctx.entrada, r3.impresiones, senales)
    return con_marcadores(resultado, marcadores)


def _borrador(r3: ResultadoReglaDeTres, llegada: LecturaRef) -> EstimacionResultado:
    fuente: FuenteEstimacion = "T4_ST" if llegada.tipo_toma == _TIPO_TOMA_ST else "Historia_Propia"
    return replace(
        _BASE,
        estim_propuesto=r3.estimado,
        impresiones=r3.impresiones,
        fuente=fuente,
        dias_par_pl=r3.dias_par,
        ajustado_por_receso=r3.dias_receso_descontados > 0,
        dias_receso_descontados=r3.dias_receso_descontados,
        dias_proyectados=r3.dias_proyectados,
        tasa_diaria=r3.tasa_diaria,
    )
