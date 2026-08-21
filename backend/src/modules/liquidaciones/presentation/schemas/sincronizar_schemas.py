"""Schemas de entrada/salida para el endpoint de sync con Canal Directo."""

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.dtos.sincronizar_liquidaciones import (
    SincronizarLiquidacionesResultado,
)


class SincronizarOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    creadas: int
    ya_existentes: int = Field(serialization_alias="yaExistentes")
    sin_prestador: int = Field(serialization_alias="sinPrestador")
    fallidas: int
    anuladas: int
    reconciliadas: int
    estados_actualizados: int = Field(serialization_alias="estadosActualizados")
    extras_actualizados: int = Field(serialization_alias="extrasActualizados")
    facturas_actualizadas: int = Field(serialization_alias="facturasActualizadas")

    @classmethod
    def from_dto(cls, dto: SincronizarLiquidacionesResultado) -> "SincronizarOut":
        return cls(
            creadas=dto.creadas,
            ya_existentes=dto.ya_existentes,
            sin_prestador=dto.sin_prestador,
            fallidas=dto.fallidas,
            anuladas=dto.anuladas,
            reconciliadas=dto.reconciliadas,
            estados_actualizados=dto.estados_actualizados,
            extras_actualizados=dto.extras_actualizados,
            facturas_actualizadas=dto.facturas_actualizadas,
        )
