from dataclasses import dataclass

from src.modules.bono_tecnicos.domain.services.evolucion_anual import PuntoMensual


@dataclass(frozen=True, slots=True)
class GetEvolucionAnualRequest:
    anio: int


@dataclass(frozen=True, slots=True)
class EvolucionTecnicoDTO:
    tecnico: str
    id_tecnico: int
    puntos: list[PuntoMensual]
    puntaje_promedio: float | None
    incidentes_total: int
    tv_solicitadas_total: int
    tv_aprobadas_total: int


@dataclass(frozen=True, slots=True)
class EvolucionAnualDTO:
    anio: int
    tecnicos: list[EvolucionTecnicoDTO]
    # Promedio mes a mes del equipo completo — la serie de referencia del
    # gráfico de cada técnico (`GET /evolucion-anual/equipo` la expone sola).
    equipo: list[PuntoMensual]
