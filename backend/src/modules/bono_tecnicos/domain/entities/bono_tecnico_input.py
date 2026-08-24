from dataclasses import dataclass

from src.modules.bono_tecnicos.domain.errors import ValorInvalidoError


@dataclass(frozen=True, slots=True)
class BonoTecnicoInput:
    """Días trabajados y Tareas Varias (TV) de un técnico en un período —
    celdas `Lista!$J$6`/`$J$7` del Excel "Tecnicos.xlsx", carga manual sin
    fuente de datos propia todavía (ver memoria de proyecto). `tecnico` queda
    desnormalizado acá porque el input se puede cargar antes de que ese
    técnico tenga algún incidente en el período (y por lo tanto antes de que
    aparezca en `ConteoTecnico`)."""

    id_tecnico: int
    periodo: int
    tecnico: str
    dias: int
    tareas_varias: int

    def __post_init__(self) -> None:
        if self.dias < 0:
            raise ValorInvalidoError("dias", self.dias)
        if self.tareas_varias < 0:
            raise ValorInvalidoError("tareas_varias", self.tareas_varias)
