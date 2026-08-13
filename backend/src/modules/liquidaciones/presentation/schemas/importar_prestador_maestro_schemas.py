"""Schema de POST /api/liquidaciones/prestadores/importar-excel."""

import uuid

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.dtos.importar_prestador_maestro import (
    ImportarPrestadorMaestroResultado,
)


class ImportarPrestadorMaestroOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    prestador_id: uuid.UUID = Field(serialization_alias="prestadorId")
    prestador_creado: bool = Field(serialization_alias="prestadorCreado")
    spsts_creados: int = Field(serialization_alias="spstsCreados")
    tarifarios_creados: int = Field(serialization_alias="tarifariosCreados")
    tarifarios_omitidos: int = Field(serialization_alias="tarifariosOmitidos")
    tabla_km_creadas: int = Field(serialization_alias="tablaKmCreadas")
    tabla_km_omitidas: int = Field(serialization_alias="tablaKmOmitidas")
    hoja_tabla_km: str | None = Field(default=None, serialization_alias="hojaTablaKm")

    @classmethod
    def from_dto(
        cls, dto: ImportarPrestadorMaestroResultado
    ) -> "ImportarPrestadorMaestroOut":
        return cls(
            prestador_id=dto.prestador_id,
            prestador_creado=dto.prestador_creado,
            spsts_creados=dto.spsts_creados,
            tarifarios_creados=dto.tarifarios_creados,
            tarifarios_omitidos=dto.tarifarios_omitidos,
            tabla_km_creadas=dto.tabla_km_creadas,
            tabla_km_omitidas=dto.tabla_km_omitidas,
            hoja_tabla_km=dto.hoja_tabla_km,
        )
