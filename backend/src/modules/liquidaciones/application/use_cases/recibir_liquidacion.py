"""Caso de uso RecibirLiquidacion — propaga estado "Recibida" (id 2 en AyC) a wsAyC
y actualiza local. Es el paso previo a aprobar/observar en el circuito de la TL:
la liquidación llega preliquidada del prestador y se marca recibida al tomarla.
Lógica compartida con `ObservarLiquidacion` en `PropagarEstadoAyC`."""

from src.modules.liquidaciones.application.use_cases.propagar_estado_ayc import (
    PropagarEstadoAyC,
    PropagarEstadoAyCPorts,
)
from src.modules.liquidaciones.domain.entities.liquidacion import ESTADO_RECIBIDA

RecibirLiquidacionPorts = PropagarEstadoAyCPorts


class RecibirLiquidacion(PropagarEstadoAyC):
    estado = ESTADO_RECIBIDA
    verbo = "recibir"
