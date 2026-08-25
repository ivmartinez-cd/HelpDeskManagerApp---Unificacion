from src.modules.sla.application.dtos.mesa_ayuda_dtos import IncidenteMesaAyudaDTO
from src.modules.sla.domain.entities.incidente_mesa_ayuda import IncidenteMesaAyuda
from src.modules.sla.domain.repositories.mesa_ayuda_query_gateway import MesaAyudaQueryGateway


def _to_dto(inc: IncidenteMesaAyuda) -> IncidenteMesaAyudaDTO:
    return IncidenteMesaAyudaDTO(
        id_incidente=inc.id_incidente,
        fecha_ingreso=inc.fecha_ingreso,
        tipo=inc.tipo,
        estado=inc.estado,
        cliente=inc.cliente,
        sucursal=inc.sucursal,
        nro_serie=inc.nro_serie,
        modelo=inc.modelo,
        operador_login=inc.operador_login,
        operador=inc.operador,
        dias_transcurridos=inc.dias_transcurridos,
        demorado=inc.demorado,
    )


class ListIncidentesMesaAyuda:
    """Incidentes sin cerrar asignados a 'CD - Mesa de Ayuda', ordenados por
    días transcurridos descendente (los más viejos primero). Consulta en vivo
    a Siges — sin snapshot, es un único técnico fijo y un volumen chico."""

    def __init__(self, gateway: MesaAyudaQueryGateway, id_tecnico: int) -> None:
        self._gateway = gateway
        self._id_tecnico = id_tecnico

    async def execute(self, *, operador_login: str | None = None) -> list[IncidenteMesaAyudaDTO]:
        incidentes = await self._gateway.find_incidentes_mesa_ayuda(self._id_tecnico)
        if operador_login is not None:
            incidentes = [i for i in incidentes if i.operador_login == operador_login]
        ordenados = sorted(incidentes, key=lambda i: i.dias_transcurridos, reverse=True)
        return [_to_dto(i) for i in ordenados]
