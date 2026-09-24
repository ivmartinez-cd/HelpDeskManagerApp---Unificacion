"""`CalculadorContadores.Calcular` del Estimador de Contadores legacy."""

from src.modules.contadores.domain.services.estimacion.antiguedad import historia_en_alerta
from src.modules.contadores.domain.services.estimacion.entre_dos_reales import (
    conserva_negativo,
    estimar_entre_reales,
    hay_par_entre_reales,
)
from src.modules.contadores.domain.services.estimacion.estado_especial import (
    resolver_backup,
    resolver_en_transito,
)
from src.modules.contadores.domain.services.estimacion.marcadores import finalizar
from src.modules.contadores.domain.services.estimacion.parque import estimar_cascada_t19
from src.modules.contadores.domain.services.estimacion.recesos import recesos_aplicables
from src.modules.contadores.domain.services.estimacion.resultados_sin_estimacion import (
    resultado_pendiente,
    resultado_real,
)
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


def estimar(entrada: EstimacionInput) -> EstimacionResultado:
    """Cascada de decisión completa para un (equipo, clase de contador). Fila
    ya real: no se estima. Backup / En tránsito tienen su propia regla. El
    resto: entre dos reales → T4 ST como Llegada → cascada de parque T19 →
    pendiente; el primer caso que aplica gana."""
    if not entrada.pendiente_estimar:
        return resultado_real(entrada)
    if entrada.estado_maquina == "BACKUP":
        return finalizar(resolver_backup(entrada), entrada)
    if entrada.estado_maquina == "EN_TRANSITO":
        return finalizar(resolver_en_transito(entrada), entrada)
    return finalizar(_estimar_normal(entrada), entrada)


def contexto_de(entrada: EstimacionInput) -> ContextoEstimacion:
    recesos = recesos_aplicables(entrada.recesos, entrada.id_anexo, entrada.id_grupo_economico)
    return ContextoEstimacion(entrada, recesos)


def _estimar_normal(entrada: EstimacionInput) -> EstimacionResultado:
    ctx = contexto_de(entrada)
    resultado = _entre_reales(ctx)
    if resultado is None and t4_aplicable(entrada):
        resultado = estimar_con_t4(ctx)
    if resultado is None:
        resultado = estimar_cascada_t19(ctx)
    return resultado if resultado is not None else resultado_pendiente()


def _entre_reales(ctx: ContextoEstimacion) -> EstimacionResultado | None:
    """Solo con historia propia no vieja (`MesesEnAlerta`) y par válido. Un
    resultado negativo se descarta (cae al T4 / parque), salvo que el último
    real sea un T4 corrector todavía válido (`conserva_negativo`)."""
    entrada = ctx.entrada
    en_alerta = historia_en_alerta(entrada.ultimo_real, entrada.tecnologia, entrada.fecha_objetivo)
    if en_alerta or not hay_par_entre_reales(entrada):
        return None
    resultado = estimar_entre_reales(ctx)
    negativo = resultado.impresiones is not None and resultado.impresiones < 0
    if negativo and not conserva_negativo(entrada):
        return None
    return resultado
