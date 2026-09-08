from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConteoTv:
    """Solicitudes de TV de un técnico en un período: cuántas se crearon y
    cuántas terminaron APROBADA — la evolución anual necesita las dos series,
    no solo las aprobadas del mes actual (ver `count_aprobadas_por_tecnico`,
    que sigue siendo lo que usa el cálculo de Puntaje del mes en curso)."""

    solicitadas: int
    aprobadas: int


@dataclass(frozen=True, slots=True)
class ResumenTvTecnico:
    """Desglose por estado de las TV de un técnico en un período — para "Mi
    bono" (`GetMiResumenBono`), a diferencia de `ConteoTv` (que la evolución
    anual usa agregado por período, no por estado)."""

    aprobadas: int
    pendientes: int
    rechazadas: int
