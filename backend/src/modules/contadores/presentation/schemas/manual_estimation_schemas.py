from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from src.modules.contadores.domain.value_objects.manual_estimation_result import (
    ManualEstimationResult,
)


class ManualEstimationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    contador_inicial: int = Field(alias="ci")
    contador_final: int = Field(alias="cf")
    fecha_inicial: date = Field(alias="fi")
    fecha_final: date = Field(alias="ff")
    fecha_estimacion: date = Field(alias="fe")


class ManualEstimationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    imp_dia: float = Field(serialization_alias="impDia")
    imp_mes: float = Field(serialization_alias="impMes")
    dias_est: int = Field(serialization_alias="diasEst")
    imp_est: int = Field(serialization_alias="impEst")
    cont_est: int = Field(serialization_alias="contEst")

    @classmethod
    def from_domain(cls, result: ManualEstimationResult) -> "ManualEstimationResponse":
        return cls(
            imp_dia=result.imp_dia,
            imp_mes=result.imp_mes,
            dias_est=result.dias_est,
            imp_est=result.imp_est,
            cont_est=result.cont_est,
        )
