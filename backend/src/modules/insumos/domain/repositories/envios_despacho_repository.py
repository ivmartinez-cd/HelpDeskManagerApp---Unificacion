"""Puertos de persistencia de Insumos > Despachados en la base de HDM (nunca en Siges)."""

from collections.abc import Collection, Sequence
from typing import Protocol

from src.modules.insumos.domain.entities.despachados.envio_seguido import EnvioSeguido
from src.modules.insumos.domain.value_objects.despachados.cambio_estado import CambioEstado
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.despacho_siges import DespachoSiges
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca


class EnviosDespachoRepository(Protocol):
    async def guias_seguidas(self, guias: Collection[str]) -> set[str]:
        """De `guias`, las que ya tienen envío (para dar de alta solo las nuevas)."""
        ...

    async def crear(self, envios: Sequence[EnvioSeguido]) -> None:
        """Alta de envíos nuevos; una guía que ya existe se ignora (no se pisa)."""
        ...

    async def listar_abiertos(self) -> list[EnvioSeguido]:
        """Envíos con `abierto = True`, los que el job vuelve a consultar en OCA."""
        ...

    async def obtener(self, guia: str) -> EnvioSeguido | None: ...

    async def actualizar(self, envio: EnvioSeguido) -> None:
        """Persiste estado OCA, clasificación, última consulta/error y cierre de alerta.
        No toca los datos de Siges (cliente, sucursal, fecha de remito)."""
        ...


class RemitosDespachoRepository(Protocol):
    async def guardar(self, despachos: Sequence[DespachoSiges]) -> None:
        """Alta o actualización por `id_remito`, con sus incidentes. El envío de cada guía
        tiene que existir antes (FK)."""
        ...

    async def listar_por_guia(self, guia: str) -> list[DespachoSiges]:
        """Remitos de la guía, del más viejo al más nuevo, con sus incidentes."""
        ...


class HistorialEstadosRepository(Protocol):
    async def registrar(self, guia: str, estado: EstadoOca, color: ColorSemaforo) -> None:
        """Agrega un cambio observado (`observado_en` lo pone la base)."""
        ...

    async def listar_por_guia(self, guia: str) -> list[CambioEstado]:
        """Del más reciente al más viejo."""
        ...
