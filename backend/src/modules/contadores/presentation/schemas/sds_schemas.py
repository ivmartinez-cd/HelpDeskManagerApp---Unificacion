from pydantic import BaseModel, Field

from src.modules.contadores.application.dtos.sds_dtos import (
    ExportSdsMetersResult,
    SdsClientResult,
)


class SdsClientOut(BaseModel):
    """Representación de un cliente SDS en la API."""

    id: str
    name: str
    suma_color: bool

    @classmethod
    def from_result(cls, result: SdsClientResult) -> "SdsClientOut":
        return cls(
            id=result.id,
            name=result.name,
            suma_color=result.suma_color,
        )


class UpdateSdsConfigIn(BaseModel):
    """Payload para actualizar la preferencia suma_color de un cliente SDS."""

    customer_name: str = Field(..., min_length=1, description="Nombre del cliente")
    suma_color: bool = Field(..., description="Preferencia de combinación de contadores mono+color")


class ProcessSdsMetersRequest(BaseModel):
    """Payload para procesar los contadores SDS de un cliente."""

    customer_id: str = Field(..., description="ID del cliente SDS")
    customer_name: str = Field(..., description="Nombre del cliente SDS")
    fecha_maxima: str = Field(..., description="Fecha máxima de lectura (formato ISO o YYYY-MM-DD)")


class ProcessSdsMetersResponse(BaseModel):
    """Respuesta al procesar los contadores SDS."""

    csv_filename: str
    customer_name: str

    @classmethod
    def from_result(cls, result: ExportSdsMetersResult) -> "ProcessSdsMetersResponse":
        return cls(
            csv_filename=result.filename,
            customer_name=result.customer_name,
        )
