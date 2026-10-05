"""Hilo de comentarios de Web Agentes de una liquidación, para verlo en el
detalle sin entrar a Web Agentes. Solo lectura contra Siges.

La bitácora se referencia por el número de CD sin dígito verificador (la local
'3984-4' → 3984). Una liquidación sin número (import CSV manual sin vínculo a
AyC) no tiene hilo: lista vacía."""

from uuid import UUID

from src.modules.liquidaciones.domain.errors import LiquidacionNoEncontradaError
from src.modules.liquidaciones.domain.repositories.bitacora_gateway import (
    BitacoraGateway,
    EntradaBitacora,
)
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)


class ListarBitacoraLiquidacion:
    def __init__(self, liquidaciones: LiquidacionRepository, bitacora: BitacoraGateway) -> None:
        self._liquidaciones = liquidaciones
        self._bitacora = bitacora

    async def execute(self, liquidacion_id: UUID) -> list[EntradaBitacora]:
        liquidacion = await self._liquidaciones.get_by_id(liquidacion_id)
        if liquidacion is None:
            raise LiquidacionNoEncontradaError(liquidacion_id)
        numero_cd = numero_cd_sin_verificador(liquidacion.numero_liquidacion)
        if numero_cd is None:
            return []
        return await self._bitacora.hilo_de_liquidacion(numero_cd)


def numero_cd_sin_verificador(numero_liquidacion: str | None) -> int | None:
    base = (numero_liquidacion or "").split("-")[0].strip()
    return int(base) if base.isdigit() else None
