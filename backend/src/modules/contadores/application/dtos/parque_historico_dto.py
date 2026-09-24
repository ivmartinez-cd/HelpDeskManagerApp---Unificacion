"""Valores de parque por nivel de la cascada tal como los trae la consulta de
la grilla, para el panel "Detalle por Modelo histórico" del legacy
(`GrillaEstimacion.razor` `DetalleModeloHist`): a diferencia de
`PromedioParque`, conserva N y la mediana cruda aunque el valor P80 sea NULL
(N<=1)."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.modules.contadores.domain.value_objects.estimacion.promedio_parque import PromedioParque

if TYPE_CHECKING:
    from src.modules.contadores.application.dtos.equipo_proceso_dto import ClaseProceso


@dataclass(frozen=True, slots=True)
class NivelParqueHistorico:
    n: int
    p80: float | None
    cruda: float | None


@dataclass(frozen=True, slots=True)
class ParqueHistorico:
    cliente_modelo: NivelParqueHistorico
    grupo_modelo: NivelParqueHistorico
    cliente_tec: NivelParqueHistorico
    global_modelo: NivelParqueHistorico


def _nivel(p: PromedioParque | None) -> NivelParqueHistorico:
    if p is None:
        return NivelParqueHistorico(0, None, None)
    return NivelParqueHistorico(p.n_equipos, p.valor, p.mediana_cruda)


def parque_historico_de_ejemplo(clase: "ClaseProceso") -> ParqueHistorico:
    """Datos de ejemplo: no traen los N crudos, se derivan de los parques."""
    return ParqueHistorico(
        cliente_modelo=_nivel(clase.parque_cliente_modelo),
        grupo_modelo=_nivel(clase.parque_grupo_modelo),
        cliente_tec=_nivel(clase.parque_cliente_tecnologia),
        global_modelo=_nivel(clase.parque_global_modelo),
    )
