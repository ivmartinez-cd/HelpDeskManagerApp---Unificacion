from pydantic import BaseModel, ConfigDict, Field


class PuntajeTecnicoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tecnico: str
    id_tecnico: int
    periodo: int
    correctivo: int
    preventivo: int
    inst_des: int
    pre_correctivo: int
    entrega_insumos: int
    dias: float
    tareas_varias: int
    puntaje: float | None
    dias_sugeridos: float | None


class GuardarBonoInputBody(BaseModel):
    tecnico: str = Field(min_length=1, max_length=120)
    dias: float = Field(ge=0, multiple_of=0.5)
