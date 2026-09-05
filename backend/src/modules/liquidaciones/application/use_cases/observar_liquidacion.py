"""Caso de uso ObservarLiquidacion — propaga estado "Observada" a wsAyC y actualiza local.

El motivo de la observación no se persiste ni se envía a AyC: `setLiquidationStatus`
no tiene parámetro de texto, y las alertas agrupadas del motor de reglas
(`Alerta.es_grupo=True`, hoy solo ALT005) son otra cosa — no notas manuales de la
TL. Lógica compartida con `RecibirLiquidacion` en `PropagarEstadoAyC`.
"""

from src.modules.liquidaciones.application.use_cases.propagar_estado_ayc import (
    PropagarEstadoAyC,
    PropagarEstadoAyCPorts,
)
from src.modules.liquidaciones.domain.entities.liquidacion import ESTADO_OBSERVADA

ObservarLiquidacionPorts = PropagarEstadoAyCPorts


class ObservarLiquidacion(PropagarEstadoAyC):
    estado = ESTADO_OBSERVADA
    verbo = "observar"
