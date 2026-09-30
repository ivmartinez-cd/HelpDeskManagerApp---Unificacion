"""Decorador del repositorio de modificaciones del prestador (ADR-038) que,
además de guardarlas, avisa en la campanita de la app (ADR-041): una
notificación por liquidación y por tanda registrada, para quienes tengan
`liquidaciones.view`. Todo en la misma sesión que la reconciliación: si algo
falla, no queda ni la modificación ni el aviso.

Se arma en `presentation/dependencies/liquidaciones.py`; el caso de uso sigue
viendo solo el puerto `ModificacionPrestadorRepository`."""

from collections.abc import Sequence
from uuid import UUID

from src.modules.liquidaciones.domain.entities.modificacion_prestador import (
    ModificacionPrestador,
)
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)
from src.modules.liquidaciones.domain.repositories.modificacion_prestador_repository import (
    ModificacionPrestadorRepository,
)
from src.modules.liquidaciones.domain.well_known_permissions import VIEW
from src.modules.notificaciones.domain.entities.notificacion import NuevaNotificacion
from src.modules.notificaciones.domain.repositories.notificacion_repository import (
    PublicadorNotificaciones,
)
from src.modules.notificaciones.domain.value_objects.audiencia import audiencia_permiso


def _cuerpo(filas: Sequence[ModificacionPrestador]) -> str:
    resumen = next((f for f in filas if f.campo == "resumen"), None)
    if resumen and resumen.valor_nuevo:
        return f"{resumen.valor_nuevo}. Revisalo en el detalle de la liquidación."
    incidentes = len({f.numero_incidente for f in filas})
    return (
        f"{incidentes} incidente{'s' if incidentes != 1 else ''} con cambios "
        "del prestador. Revisalos en el detalle de la liquidación."
    )


def _titulo(numero: str | None, filas: Sequence[ModificacionPrestador]) -> str:
    etiqueta = numero or "sin número"
    if any(f.campo == "resumen" for f in filas):
        return f"Liquidación {etiqueta}: el prestador reenvió la liquidación"
    n = len(filas)
    return f"Liquidación {etiqueta}: el prestador modificó {n} valor{'es' if n != 1 else ''}"


class ModificacionesConAviso:
    def __init__(
        self,
        inner: ModificacionPrestadorRepository,
        liquidaciones: LiquidacionRepository,
        publicador: PublicadorNotificaciones,
    ) -> None:
        self._inner = inner
        self._liquidaciones = liquidaciones
        self._publicador = publicador

    async def bulk_create(self, modificaciones: Sequence[ModificacionPrestador]) -> None:
        await self._inner.bulk_create(modificaciones)
        por_liquidacion: dict[UUID, list[ModificacionPrestador]] = {}
        for m in modificaciones:
            por_liquidacion.setdefault(m.liquidacion_id, []).append(m)
        avisos = [await self._aviso(lid, filas) for lid, filas in por_liquidacion.items()]
        await self._publicador.publicar(avisos)

    async def _aviso(
        self, liquidacion_id: UUID, filas: list[ModificacionPrestador]
    ) -> NuevaNotificacion:
        liquidacion = await self._liquidaciones.get_by_id(liquidacion_id)
        numero = liquidacion.numero_liquidacion if liquidacion else None
        return NuevaNotificacion(
            # Una por tanda: el id de la primera fila es único y estable.
            clave=f"liquidaciones.modificaciones:{liquidacion_id}:{filas[0].id}",
            audiencia=audiencia_permiso(VIEW),
            titulo=_titulo(numero, filas),
            cuerpo=_cuerpo(filas),
            url=f"/liquidaciones/{liquidacion_id}",
        )

    async def list_by_liquidacion(self, liquidacion_id: UUID) -> list[ModificacionPrestador]:
        return await self._inner.list_by_liquidacion(liquidacion_id)

    async def list_no_vistas(self) -> list[ModificacionPrestador]:
        return await self._inner.list_no_vistas()

    async def marcar_vistas(self, liquidacion_id: UUID) -> int:
        return await self._inner.marcar_vistas(liquidacion_id)
