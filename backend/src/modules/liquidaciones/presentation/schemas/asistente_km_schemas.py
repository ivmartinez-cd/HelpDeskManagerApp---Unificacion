"""Schema del diagnóstico del Asistente de KM (wizard APB)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.use_cases.estado_asistente_km import (
    EstadoAsistenteKm,
)


class EstadoAsistenteKmOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    vinculado_siges: bool = Field(serialization_alias="vinculadoSiges")
    base_configurada: bool = Field(serialization_alias="baseConfigurada")
    base_con_coordenadas: bool = Field(serialization_alias="baseConCoordenadas")
    sucursales_activas: int = Field(serialization_alias="sucursalesActivas")
    ex_clientes: int = Field(serialization_alias="exClientes")
    sucursales_nuevas_por_importar: int = Field(
        serialization_alias="sucursalesNuevasPorImportar"
    )
    filas_tabla_km: int = Field(serialization_alias="filasTablaKm")
    sin_coordenadas: int = Field(serialization_alias="sinCoordenadas")
    ambiguas_pendientes: int = Field(serialization_alias="ambiguasPendientes")
    filas_sin_km: int = Field(serialization_alias="filasSinKm")
    no_encontradas_en_siges: int = Field(serialization_alias="noEncontradasEnSiges")
    pines_sospechosos_cacheados: int = Field(
        serialization_alias="pinesSospechososCacheados"
    )
    estimacion_geocodificar: int = Field(serialization_alias="estimacionGeocodificar")
    estimacion_distancias: int = Field(serialization_alias="estimacionDistancias")
    estimacion_auditar_pines: int = Field(serialization_alias="estimacionAuditarPines")
    tope_por_corrida: int = Field(serialization_alias="topePorCorrida")

    @classmethod
    def from_dto(cls, e: EstadoAsistenteKm) -> EstadoAsistenteKmOut:
        return cls(**{campo: getattr(e, campo) for campo in cls.model_fields})
