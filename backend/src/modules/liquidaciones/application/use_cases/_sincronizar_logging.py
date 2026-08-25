"""Logging de resumen del sync de liquidaciones — separado de
`sincronizar_liquidaciones.py` (§4) porque no es lógica de negocio, solo deja
rastro de lo que hizo `Contadores`/`ReconciliarLiquidacionResultado`."""

import logging

from src.modules.liquidaciones.application.use_cases._reconciliar_liquidacion import (
    ReconciliarLiquidacionResultado,
)
from src.modules.liquidaciones.application.use_cases._sincronizar_contadores import Contadores
from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import CdLiquidacion

logger = logging.getLogger(__name__)


def log_parciales(prestador: Prestador, parciales: Contadores) -> None:
    logger.info(
        "sync CD %s: %d creadas, %d ya existentes, %d fallidas, %d anuladas, "
        "%d reconciliadas, %d estados actualizados, %d períodos actualizados, "
        "%d extras actualizados, %d facturas actualizadas",
        prestador.nombre_corto,
        parciales.creadas,
        parciales.ya_existentes,
        parciales.fallidas,
        parciales.anuladas,
        parciales.reconciliadas,
        parciales.estados_actualizados,
        parciales.periodos_actualizados,
        parciales.extras_actualizados,
        parciales.facturas_actualizadas,
    )


def log_reconciliada(cd_liq: CdLiquidacion, resultado: ReconciliarLiquidacionResultado) -> None:
    """Solo deja rastro cuando la reconciliación aplicó algo (diff de incidentes,
    estado, período, extra o factura); las revisiones sin novedad no ensucian el log."""
    campos = (
        resultado.altas, resultado.cambios, resultado.bajas,
        resultado.estado_actualizado, resultado.periodo_actualizado,
        resultado.extra_actualizado, resultado.factura_actualizada,
    )
    if not (resultado.reconciliada and any(campos)):
        return
    logger.info(
        "sync CD: %s reconciliada — %d altas, %d cambios, %d bajas, "
        "estado actualizado=%s, período actualizado=%s, extra actualizado=%s, "
        "factura actualizada=%s",
        cd_liq.numero_liquidacion,
        *campos,
    )
