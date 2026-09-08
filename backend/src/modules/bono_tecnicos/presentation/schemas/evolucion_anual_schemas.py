from pydantic import BaseModel, ConfigDict


class PuntoMensualSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    periodo: int
    puntaje: float | None
    incidentes: float
    dias: float
    tv_solicitadas: float
    tv_aprobadas: float


class EvolucionTecnicoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tecnico: str
    id_tecnico: int
    puntos: list[PuntoMensualSchema]
    puntaje_promedio: float | None
    incidentes_total: int
    tv_solicitadas_total: int
    tv_aprobadas_total: int


class EvolucionEquipoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    anio: int
    puntos: list[PuntoMensualSchema]
