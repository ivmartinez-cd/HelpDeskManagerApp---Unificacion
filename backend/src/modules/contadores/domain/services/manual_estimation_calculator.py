import math

from src.modules.contadores.domain.errors import InvalidDateRangeError
from src.modules.contadores.domain.services.days_360 import days_360
from src.modules.contadores.domain.value_objects.manual_estimation_input import (
    ManualEstimationInput,
)
from src.modules.contadores.domain.value_objects.manual_estimation_result import (
    ManualEstimationResult,
)


def calculate_manual_estimation(data: ManualEstimationInput) -> ManualEstimationResult:
    ndias = days_360(data.fecha_inicial, data.fecha_final)
    if ndias <= 0:
        raise InvalidDateRangeError

    ndias_est = days_360(data.fecha_final, data.fecha_estimacion)
    imp_dia = round((data.contador_final - data.contador_inicial) / ndias, 2)
    imp_mes = round(imp_dia * 30, 2)
    imp_est = math.ceil(imp_dia * ndias_est)

    return ManualEstimationResult(
        imp_dia=imp_dia,
        imp_mes=imp_mes,
        dias_est=ndias_est,
        imp_est=imp_est,
        cont_est=data.contador_final + imp_est,
    )
