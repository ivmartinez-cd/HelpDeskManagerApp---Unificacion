"""Aviso en la campanita de la app: casos de Mesa de Ayuda con una visita de
técnico en marcha en la misma sucursal. Una notificación por par (caso MDA,
visita), para quienes tengan la función `sla-avisos-mesa-ayuda`.

`NotificadoresEnSerie` combina este canal con el mail: si cualquiera lanza, el
caso de uso no registra los pares y, como todo va en la misma sesión, tampoco
queda la notificación — el próximo ciclo reintenta los dos canales juntos."""

from src.modules.notificaciones.domain.entities.notificacion import NuevaNotificacion
from src.modules.notificaciones.domain.repositories.notificacion_repository import (
    PublicadorNotificaciones,
)
from src.modules.notificaciones.domain.value_objects.audiencia import audiencia_funcion
from src.modules.sla.domain.entities.incidente_mesa_ayuda import IncidenteMesaAyuda
from src.modules.sla.domain.repositories.avisos_visita_sucursal import (
    NotificadorVisitaSucursal,
)
from src.modules.sla.domain.well_known_features import AVISOS_MESA_AYUDA

_URL = "/sla/mesa-de-ayuda"


def _notificacion(inc: IncidenteMesaAyuda) -> NuevaNotificacion:
    extra = inc.visitas_en_sucursal - 1
    mas = f" (+{extra} más)" if extra > 0 else ""
    tecnico = f" a {inc.visita_tecnico}" if inc.visita_tecnico else ""
    estado = f", {inc.visita_estado}" if inc.visita_estado else ""
    return NuevaNotificacion(
        clave=f"sla.visita-sucursal:{inc.id_incidente}:{inc.visita_id_incidente}",
        audiencia=audiencia_funcion(AVISOS_MESA_AYUDA),
        titulo=f"Caso {inc.id_incidente}: hay una visita en la misma sucursal",
        cuerpo=(
            f"{inc.cliente} — {inc.sucursal}. Caso {inc.visita_id_incidente}{mas} "
            f"derivado{tecnico}{estado}. Coordinar para que la visita cubra los dos."
        ),
        url=_URL,
    )


class InAppNotificadorVisitaSucursal:
    def __init__(self, publicador: PublicadorNotificaciones) -> None:
        self._publicador = publicador

    async def avisar(self, incidentes: list[IncidenteMesaAyuda]) -> None:
        await self._publicador.publicar([_notificacion(i) for i in incidentes])


class NotificadoresEnSerie:
    def __init__(self, notificadores: list[NotificadorVisitaSucursal]) -> None:
        self._notificadores = notificadores

    async def avisar(self, incidentes: list[IncidenteMesaAyuda]) -> None:
        for notificador in self._notificadores:
            await notificador.avisar(incidentes)
