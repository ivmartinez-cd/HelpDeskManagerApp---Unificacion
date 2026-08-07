from pydantic import BaseModel, Field

from src.modules.contadores.application.dtos.ers_dtos import (
    ErsClientResult,
    ExportErsMetersResult,
)


class ErsClientOut(BaseModel):
    """Representación de un cliente ERS (grupo de dispositivos) en la API."""

    id: str
    name: str
    suma_color: bool

    @classmethod
    def from_result(cls, result: ErsClientResult) -> "ErsClientOut":
        return cls(
            id=result.id,
            name=result.name,
            suma_color=result.suma_color,
        )


class UpdateErsConfigIn(BaseModel):
    """Payload para actualizar la preferencia suma_color de un grupo ERS."""

    customer_name: str = Field(..., min_length=1, description="Nombre del grupo/cliente ERS")
    suma_color: bool = Field(..., description="Preferencia de combinación de contadores mono+color")


class ProcessErsMetersRequest(BaseModel):
    """Payload para procesar los contadores ERS de un grupo."""

    customer_id: str = Field(..., description="ID del grupo ERS")
    customer_name: str = Field(..., description="Nombre del grupo ERS")
    fecha_maxima: str = Field(..., description="Fecha máxima de lectura (formato ISO o YYYY-MM-DD)")


class ProcessErsMetersResponse(BaseModel):
    """Respuesta al procesar los contadores ERS."""

    csv_filename: str
    customer_name: str

    @classmethod
    def from_result(cls, result: ExportErsMetersResult) -> "ProcessErsMetersResponse":
        return cls(
            csv_filename=result.filename,
            customer_name=result.group_name,
        )
