from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ManualEstimationResult:
    imp_dia: float
    imp_mes: float
    dias_est: int
    imp_est: int
    cont_est: int
