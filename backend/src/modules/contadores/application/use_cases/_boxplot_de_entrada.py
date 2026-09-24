"""Compartido por `get_candidatos_equipo.py` (ejemplo) y
`get_candidatos_equipo_siges.py` (real): ambos ya tienen un `EstimacionInput`
armado cuando llega el momento de mostrar el gráfico de parque del panel de
candidatos."""

from src.modules.contadores.application.dtos.boxplot_parque_dto import BoxplotParqueDto
from src.modules.contadores.domain.services.estimacion.motor import estimar
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput


def boxplot_de_entrada(
    entrada: EstimacionInput, impresiones_fila: float | None = None
) -> BoxplotParqueDto | None:
    """`CalcularBoxplotData` de `PanelCandidatos` (legacy): la referencia es
    el parque del cliente por tecnología y, si ese nivel no trae promedio, el
    del cliente por modelo; Q1/Q3 y N salen siempre del parque por
    tecnología (el gráfico se titula "Parque del cliente (Mono/Color)").
    `valor_equipo` es `Equipo.Impresiones`: las de la fila con la decisión
    del operador si se pasan; si no, la propuesta del motor."""
    tecnologia = entrada.parque_cliente_tecnologia
    referencia = tecnologia if tecnologia is not None else entrada.parque_cliente_modelo
    if referencia is None or referencia.valor <= 0:
        return None
    return BoxplotParqueDto(
        n_equipos=tecnologia.n_equipos if tecnologia is not None else 0,
        q1=tecnologia.q1 if tecnologia is not None else None,
        mediana=referencia.valor,
        q3=tecnologia.q3 if tecnologia is not None else None,
        valor_equipo=impresiones_fila if impresiones_fila is not None else _automatico(entrada),
    )


def _automatico(entrada: EstimacionInput) -> float | None:
    return estimar(entrada).impresiones
