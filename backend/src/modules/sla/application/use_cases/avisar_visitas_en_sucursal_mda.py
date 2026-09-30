from src.modules.sla.domain.entities.incidente_mesa_ayuda import IncidenteMesaAyuda
from src.modules.sla.domain.repositories.avisos_visita_sucursal import (
    NotificadorVisitaSucursal,
    ParAvisado,
    RegistroAvisosVisita,
)
from src.modules.sla.domain.repositories.mesa_ayuda_query_gateway import MesaAyudaQueryGateway


def _con_visita(
    incidentes: list[IncidenteMesaAyuda],
) -> list[tuple[IncidenteMesaAyuda, ParAvisado]]:
    return [
        (i, (i.id_incidente, i.visita_id_incidente))
        for i in incidentes
        if i.visita_id_incidente is not None
    ]


class AvisarVisitasEnSucursalMda:
    """Avisa por mail los casos de MDA cuya sucursal tiene una visita de
    técnico en marcha, para que la consulta de MDA no quede afuera del viaje.

    Un aviso por par (caso MDA, visita más reciente): si después se deriva
    otra visita a la misma sucursal, pasa a ser la más reciente y se avisa de
    nuevo. Todos los pares nuevos de un ciclo van en un solo mail."""

    def __init__(
        self,
        gateway: MesaAyudaQueryGateway,
        id_tecnico: int,
        registro: RegistroAvisosVisita,
        notificador: NotificadorVisitaSucursal,
    ) -> None:
        self._gateway = gateway
        self._id_tecnico = id_tecnico
        self._registro = registro
        self._notificador = notificador

    async def execute(self) -> int:
        incidentes = await self._gateway.find_incidentes_mesa_ayuda(self._id_tecnico)
        con_visita = _con_visita(incidentes)
        ya = await self._registro.ya_avisados([par for _, par in con_visita])
        nuevos = [(i, par) for i, par in con_visita if par not in ya]
        if not nuevos:
            return 0
        await self._notificador.avisar([i for i, _ in nuevos])
        await self._registro.registrar([par for _, par in nuevos])
        return len(nuevos)
