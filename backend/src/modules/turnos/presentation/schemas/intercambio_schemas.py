"""Schemas del intercambio de turnos (ADR-026): un par de coberturas
cruzadas que se crea, edita y cancela junto."""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from src.modules.turnos.application.dtos.turno_dtos import IntercambioDTO
from src.modules.turnos.presentation.schemas.turno_schemas import AsignacionOverrideResponse


class IntercambioRequest(BaseModel):
    """Mismo body para alta (`POST`) y edición (`PUT /{intercambio_id}`).
    `slotIdsA` = franjas de A que pasa a cubrir B (`null` = todas);
    `slotIdsB`, simétrico. `motivo` vacío = "Intercambio"."""

    model_config = ConfigDict(populate_by_name=True)

    operador_a_id: uuid.UUID = Field(validation_alias="operadorAId")
    operador_b_id: uuid.UUID = Field(validation_alias="operadorBId")
    desde: date
    hasta: date
    slot_ids_a: list[uuid.UUID] | None = Field(default=None, validation_alias="slotIdsA")
    slot_ids_b: list[uuid.UUID] | None = Field(default=None, validation_alias="slotIdsB")
    motivo: str | None = None


class IntercambioResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    intercambio_id: uuid.UUID = Field(serialization_alias="intercambioId")
    coberturas: list[AsignacionOverrideResponse]
    """Siempre dos: [A ausente → B cubre, B ausente → A cubre]."""

    @classmethod
    def from_dto(cls, dto: IntercambioDTO) -> "IntercambioResponse":
        return cls(
            intercambio_id=dto.intercambio_id,
            coberturas=[AsignacionOverrideResponse.from_dto(c) for c in dto.coberturas],
        )
