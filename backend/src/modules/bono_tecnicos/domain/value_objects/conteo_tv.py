from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConteoTv:
    """Solicitudes de TV de un técnico en un período: cuántas se crearon y
    cuántas terminaron APROBADA — la evolución anual necesita las dos series,
    no solo las aprobadas del mes actual (ver `count_aprobadas_por_tecnico`,
    que sigue siendo lo que usa el cálculo de Puntaje del mes en curso)."""

    solicitadas: int
    aprobadas: int
