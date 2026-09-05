from dataclasses import dataclass

from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    FuenteEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.promedio_parque import PromedioParque

_MUESTRA_MINIMA = 2  # REGLAS_DE_NEGOCIO §5.5: "N <= 1: no hay dato suficiente"


@dataclass(frozen=True, slots=True)
class NivelParque:
    fuente: FuenteEstimacion
    promedio: PromedioParque


def resolver_cascada_parque(entrada: EstimacionInput) -> NivelParque | None:
    """Primer nivel con datos suficientes, de mayor a menor especificidad
    (REGLAS_DE_NEGOCIO §5.5). El valor representativo de cada nivel ya viene
    resuelto por la capa de datos (mediana truncada / IQR — ver
    `valor_representativo_parque.py`); acá solo se recorre la cascada."""
    niveles: list[tuple[FuenteEstimacion, PromedioParque | None]] = [
        ("Parque_Cliente_Modelo", entrada.parque_cliente_modelo),
        ("Parque_Grupo_Modelo", entrada.parque_grupo_modelo),
        ("Parque_Cliente_Tec", entrada.parque_cliente_tecnologia),
        ("Parque_Global_Modelo", entrada.parque_global_modelo),
    ]
    for fuente, promedio in niveles:
        if promedio is not None and promedio.n_equipos >= _MUESTRA_MINIMA:
            return NivelParque(fuente, promedio)
    return None
