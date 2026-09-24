"""Casos de uso de las acciones de operador sobre un envío de Despachados: registrar una
acción (y, si se pide, dar la alerta por atendida) y cerrar la alerta.

Lo escrito queda en la transacción del request: estos casos de uso no confirman por su
cuenta (ADR-010). Una alerta cerrada se reabre sola si OCA informa otro problema.
"""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from src.modules.insumos.domain.entities.despachados.accion_registrada import (
    AccionNueva,
    AccionRegistrada,
    ResultadoAccion,
    TipoAccion,
)
from src.modules.insumos.domain.entities.despachados.envio_seguido import (
    CierreAlerta,
    EnvioSeguido,
)
from src.modules.insumos.domain.errores_despachados import (
    AccionDespachoInvalidaError,
    AlertaDespachoNoAbiertaError,
    CierreAlertaSinAccionError,
    EnvioDespachoNoEncontradoError,
)
from src.modules.insumos.domain.repositories.acciones_despacho_repository import (
    AccionesDespachoRepository,
)
from src.modules.insumos.domain.repositories.envios_despacho_repository import (
    EnviosDespachoRepository,
)

LARGO_MAXIMO_DETALLE = 2000


@dataclass(frozen=True, slots=True)
class UsuarioActuante:
    id: UUID | None
    nombre: str


@dataclass(frozen=True, slots=True)
class DatosAccion:
    tipo: TipoAccion
    detalle: str
    resultado: ResultadoAccion
    cerrar_alerta: bool
    """Además de registrar la acción, dar la alerta por atendida."""


@dataclass(frozen=True)
class AccionDespachoPorts:
    envios: EnviosDespachoRepository
    acciones: AccionesDespachoRepository
    reloj: Callable[[], datetime]
    """Hora actual, aware en UTC."""


class RegistrarAccionDespacho:
    def __init__(self, ports: AccionDespachoPorts) -> None:
        self._ports = ports

    async def execute(
        self, guia: str, datos: DatosAccion, usuario: UsuarioActuante
    ) -> AccionRegistrada:
        """Guarda la acción con el detalle recortado; con `cerrar_alerta`, la alerta del
        envío tiene que estar abierta y queda cerrada a nombre de `usuario`."""
        detalle = _detalle_valido(datos.detalle)
        envio = await _envio_seguido(self._ports.envios, guia)
        if datos.cerrar_alerta and not envio.alerta_abierta:
            raise AlertaDespachoNoAbiertaError(guia)
        accion = await self._ports.acciones.agregar(
            _accion_nueva(guia, replace(datos, detalle=detalle), usuario)
        )
        if datos.cerrar_alerta:
            cerrado = _con_alerta_cerrada(envio, self._ports.reloj(), usuario)
            await self._ports.envios.actualizar(cerrado)
        return accion


class CerrarAlertaDespacho:
    def __init__(self, ports: AccionDespachoPorts) -> None:
        self._ports = ports

    async def execute(self, guia: str, usuario: UsuarioActuante) -> EnvioSeguido:
        """Da la alerta por atendida. Solo si está abierta y ya hay al menos una acción
        registrada sobre la guía."""
        envio = await _envio_seguido(self._ports.envios, guia)
        if not envio.alerta_abierta:
            raise AlertaDespachoNoAbiertaError(guia)
        if not await self._ports.acciones.listar_por_guia(guia):
            raise CierreAlertaSinAccionError(guia)
        cerrado = _con_alerta_cerrada(envio, self._ports.reloj(), usuario)
        await self._ports.envios.actualizar(cerrado)
        return cerrado


def _detalle_valido(detalle: str) -> str:
    recortado = detalle.strip()
    if not recortado:
        raise AccionDespachoInvalidaError("El detalle es obligatorio")
    if len(recortado) > LARGO_MAXIMO_DETALLE:
        raise AccionDespachoInvalidaError(
            f"El detalle admite hasta {LARGO_MAXIMO_DETALLE} caracteres (tiene {len(recortado)})"
        )
    return recortado


async def _envio_seguido(envios: EnviosDespachoRepository, guia: str) -> EnvioSeguido:
    envio = await envios.obtener(guia)
    if envio is None:
        raise EnvioDespachoNoEncontradoError(guia)
    return envio


def _accion_nueva(guia: str, datos: DatosAccion, usuario: UsuarioActuante) -> AccionNueva:
    return AccionNueva(
        guia=guia,
        tipo=datos.tipo,
        detalle=datos.detalle,
        resultado=datos.resultado,
        cerro_alerta=datos.cerrar_alerta,
        usuario_id=usuario.id,
        usuario_nombre=usuario.nombre,
    )


def _con_alerta_cerrada(
    envio: EnvioSeguido, ahora: datetime, usuario: UsuarioActuante
) -> EnvioSeguido:
    cierre = CierreAlerta(cerrada_en=ahora, usuario_id=usuario.id, usuario_nombre=usuario.nombre)
    return replace(envio, cierre_alerta=cierre)
