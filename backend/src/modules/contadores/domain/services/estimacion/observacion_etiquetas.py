from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    FuenteEstimacion,
)

ETIQUETAS_PARQUE: dict[FuenteEstimacion, str] = {
    "Parque_Cliente_Modelo": "Parque cli/mod",
    "Parque_Grupo_Modelo": "Parque grupo/mod",
    "Parque_Cliente_Tec": "Parque cli/tec",
    "Parque_Global_Modelo": "Parque global/mod",
}

_ETIQUETAS_POR_FUENTE: dict[FuenteEstimacion, str] = {
    **ETIQUETAS_PARQUE,
    "Backup_SinST": "Backup sin movimiento",
    "Backup_ConST": "T4 ST tal cual",
    "EnTransito": "En transito sin movimiento",
}

_ETIQUETAS_POR_METODO_DETALLE: dict[str, str] = {
    "T4ST proyectado": "T4 ST proyectado",
    "T4ST valor": "T4 ST tal cual",
    "Partida/Llegada elegidas a mano": "P/L manual",
    "Entre dos reales": "Entre reales",
}


def etiqueta_metodo(resultado: EstimacionResultado) -> str:
    """Traduce el resultado del motor al vocabulario de
    LEYENDA_OBSERVACION.md (qué ve el operador en SiGes)."""
    if resultado.fuente in _ETIQUETAS_POR_FUENTE:
        return _ETIQUETAS_POR_FUENTE[resultado.fuente]
    return _ETIQUETAS_POR_METODO_DETALLE.get(resultado.metodo_detalle, resultado.metodo_detalle)


def avisos(resultado: EstimacionResultado, forzado_por_operador: bool) -> list[str]:
    """Avisos en el orden en que aparecen en los ejemplos de
    LEYENDA_OBSERVACION.md (§ Avisos)."""
    lista = []
    if resultado.t4_sin_revisar:
        lista.append("(!)T4 sin revisar")
    if resultado.nota_operador is not None:
        lista.append("sin par P/L")
    if resultado.par_incluye_t4:
        lista.append("usa T4")
    if resultado.ajustado_por_receso:
        lista.append("receso")
    if resultado.dias_proyectados is not None and resultado.dias_proyectados < 0:
        lista.append("interp. atras")
    if forzado_por_operador:
        lista.append("forzado op.")
    return lista
