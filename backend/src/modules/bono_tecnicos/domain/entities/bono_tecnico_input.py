from dataclasses import dataclass

from src.modules.bono_tecnicos.domain.errors import ValorInvalidoError


@dataclass(frozen=True, slots=True)
class BonoTecnicoInput:
    """Días trabajados de un técnico en un período — celda `Lista!$J$6` del
    Excel "Tecnicos.xlsx", carga manual sin fuente de datos propia todavía
    (ver memoria de proyecto). `tecnico` queda desnormalizado acá porque el
    input se puede cargar antes de que ese técnico tenga algún incidente en
    el período (y por lo tanto antes de que aparezca en `ConteoTecnico`).

    Tareas Varias (`$J$7`) dejó de vivir acá: ahora es la cuenta de
    `SolicitudTv` en estado APROBADA del período, ver `GetPuntajesPeriodo`.

    `dias` admite medios días (ej. 20.5) — granularidad real del Excel legacy
    (caso Matías Milán, bono julio/2026), no un entero puro."""

    id_tecnico: int
    periodo: int
    tecnico: str
    dias: float

    def __post_init__(self) -> None:
        if self.dias < 0:
            raise ValorInvalidoError("dias", self.dias)
        if (self.dias * 2) % 1 != 0:
            raise ValorInvalidoError("dias", self.dias)
