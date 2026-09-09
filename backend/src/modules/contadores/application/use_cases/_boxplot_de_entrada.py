"""Compartido por `get_candidatos_equipo.py` (ejemplo) y
`get_candidatos_equipo_siges.py` (real): ambos ya tienen un `EstimacionInput`
armado cuando llega el momento de mostrar el gráfico de parque del panel de
candidatos."""

from src.modules.contadores.application.dtos.boxplot_parque_dto import BoxplotParqueDto
from src.modules.contadores.domain.services.estimacion.cascada_parque import (
    resolver_cascada_parque,
)
from src.modules.contadores.domain.services.estimacion.motor import estimar
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput


def boxplot_de_entrada(entrada: EstimacionInput) -> BoxplotParqueDto | None:
    """Estadísticas reales del nivel de parque resuelto (paridad con
    `CalcularBoxplotData` de `PanelCandidatos.razor`): `q1`/`q3` son los del
    mismo nivel usado para `mediana` (no se mezclan niveles distintos como
    hacía el legacy), y `valor_equipo` es la propuesta automática del motor
    para este equipo — no el valor del parque, que dejaría el punto "este
    equipo" siempre pegado a la mediana."""
    nivel = resolver_cascada_parque(entrada)
    if nivel is None:
        return None
    return BoxplotParqueDto(
        n_equipos=nivel.promedio.n_equipos,
        q1=nivel.promedio.q1,
        mediana=nivel.promedio.valor,
        q3=nivel.promedio.q3,
        valor_equipo=estimar(entrada).impresiones,
    )
