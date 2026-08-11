from src.modules.sla.application.dtos.sla_dtos import IncidenteVencidoDTO
from src.modules.sla.domain.entities.incidente_sla import IncidenteSla
from src.modules.sla.domain.repositories.sla_query_gateway import SlaQueryGateway
from src.modules.sla.domain.value_objects.periodo import Periodo


def _to_dto(incidente: IncidenteSla) -> IncidenteVencidoDTO:
    return IncidenteVencidoDTO(
        id_incidente=incidente.id_incidente,
        tecnico=incidente.tecnico,
        region=incidente.region,
        cliente=incidente.cliente,
        sucursal=incidente.sucursal,
        modelo=incidente.modelo,
        nro_serie=incidente.nro_serie,
        fecha_ingreso=incidente.fecha_ingreso,
        fecha_operativo=incidente.fecha_operativo,
        tiempo=incidente.tiempo,
        rango=incidente.rango,
        sla_horas=incidente.sla_horas,
        horas_vencido=incidente.horas_vencido,
    )


class ListIncidentesVencidos:
    """Detalle de los incidentes vencidos del período, en el mismo orden en que
    los entrega la consulta (ID de incidente descendente)."""

    def __init__(self, gateway: SlaQueryGateway) -> None:
        self._gateway = gateway

    async def execute(self, periodo: int) -> list[IncidenteVencidoDTO]:
        incidentes = await self._gateway.find_incidentes(Periodo(periodo))
        return [_to_dto(i) for i in incidentes if i.es_vencido]
