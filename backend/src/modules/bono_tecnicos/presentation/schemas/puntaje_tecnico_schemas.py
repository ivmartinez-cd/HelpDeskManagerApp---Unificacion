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
    dias: int
    tareas_varias: int
    puntaje: float | None
    dias_sugeridos: int | None


class GuardarBonoInputBody(BaseModel):
    tecnico: str = Field(min_length=1, max_length=120)
    dias: int = Field(ge=0)
