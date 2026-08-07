from dataclasses import dataclass
from datetime import date

from src.modules.contadores.domain.value_objects.projection_method import ProjectionMethod


@dataclass(frozen=True, slots=True)
class CounterProjectionResult:
    """Una fila de la hoja "Proyeccion" — ver CONTADORES_CARACTERIZACION.md
    para el significado exacto de cada campo (portado 1:1 desde la app vieja).
    Solo `metodo == "PROYECTADO"` alimenta el CSV de SiGes."""

    serie: str
    clase: str
    articulo: str
    sector: str
    fecha_lectura: date | None
    contador_base: int | None
    dias_proyectados: int | None
    consumo_diario_promedio: float | None
    paginas_sumadas: int | None
    fecha_toma: date
    contador_proyectado: int | None
    metodo: ProjectionMethod
    observaciones: str
