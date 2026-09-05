from src.modules.contadores.domain.services.estimacion.antiguedad import meses_entre
from src.modules.contadores.domain.services.estimacion.observacion_etiquetas import ETIQUETAS_PARQUE
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.promedio_parque import PromedioParque


def estadisticos_base(
    resultados: dict[str, EstimacionResultado], entrada: EstimacionInput
) -> str:
    """Estadísticos de respaldo del primer resultado que tenga (LEYENDA_OBSERVACION
    § Estadísticos) — parque o regla de tres, según cuál método se usó."""
    for r in resultados.values():
        texto = _estadistico_de(r, entrada)
        if texto:
            return texto
    return ""


def _estadistico_de(r: EstimacionResultado, entrada: EstimacionInput) -> str:
    if r.fuente in ETIQUETAS_PARQUE:
        return _estadistico_parque(r, entrada)
    if r.dias_par_pl is not None and r.tasa_diaria is not None and r.dias_proyectados is not None:
        tasa = f"{r.tasa_diaria:.1f}".replace(".", ",")
        return f"{r.dias_par_pl}d {tasa}/dia extrap +{r.dias_proyectados}d"
    return ""


def _estadistico_parque(r: EstimacionResultado, entrada: EstimacionInput) -> str:
    promedio = _promedio_de(entrada, r.fuente)
    if promedio is None:
        return ""
    if promedio.n_descartados > 0:
        return f"P80 {promedio.n_equipos}eq(-{promedio.n_descartados} desc)"
    return f"mediana {promedio.n_equipos}eq"


def _promedio_de(entrada: EstimacionInput, fuente: str) -> PromedioParque | None:
    return {
        "Parque_Cliente_Modelo": entrada.parque_cliente_modelo,
        "Parque_Grupo_Modelo": entrada.parque_grupo_modelo,
        "Parque_Cliente_Tec": entrada.parque_cliente_tecnologia,
        "Parque_Global_Modelo": entrada.parque_global_modelo,
    }.get(fuente)


def contexto_antiguedad(
    resultados: dict[str, EstimacionResultado], entrada: EstimacionInput
) -> str:
    """"sin real Nm" — pieza de menor prioridad de conservación, sacrificada
    primero al recortar (REGLAS_DE_NEGOCIO §12). Es informativo de por qué
    se fue al parque, no depende de si esa antigüedad superó el umbral de
    alerta de §5.4 (LEYENDA_OBSERVACION.md: ejemplo con 3 meses, por debajo
    de ambos umbrales, igual se muestra)."""
    hay_parque = any(r.fuente in ETIQUETAS_PARQUE for r in resultados.values())
    if entrada.ultimo_real is None or not hay_parque:
        return ""
    meses = meses_entre(entrada.ultimo_real.fecha, entrada.fecha_objetivo)
    return f"sin real {meses}m"
