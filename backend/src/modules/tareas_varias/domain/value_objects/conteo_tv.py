from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConteoTv:
    """Solicitudes de TV de un técnico en un período: cuántas se crearon y
    cuántas terminaron APROBADA. Duplicado del homónimo en
    `bono_tecnicos.domain.value_objects.conteo_tv` — bono_tecnicos consume
    este dato por su propio puerto (`TareasVariasGateway`), nunca importando
    este tipo directamente (ver ADR de separación de Tareas Varias)."""

    solicitadas: int
    aprobadas: int
