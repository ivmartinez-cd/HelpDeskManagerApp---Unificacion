"""Actualiza el ítem extra y el número de factura de una liquidación contra el
detalle de AyC — extraído de `_reconciliar_liquidacion.py` (§4) porque es un
colaborador autocontenido, sin estado compartido con el resto del flujo de
reconciliación de incidentes."""

from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion
from src.modules.liquidaciones.domain.repositories.cd_liquidaciones_gateway import (
    CdLiquidacionesGateway,
)
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)
from src.modules.liquidaciones.domain.services.factura_pdf_url import armar_factura_pdf_url
from src.modules.liquidaciones.domain.services.recalcular_total_extra import (
    total_importe_tras_cambiar_extra,
)
from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import (
    CdLiquidacion,
    CdLiquidacionDetalle,
)


async def actualizar_extra_y_factura(
    liquidaciones: LiquidacionRepository,
    cd_gateway: CdLiquidacionesGateway,
    liquidacion: Liquidacion,
    cd_liq: CdLiquidacion,
) -> tuple[bool, bool]:
    """Una sola llamada a `get_detalle` cubre ambos campos. Nunca borra un
    ítem extra cargado a mano cuando AyC no tiene ninguno (`concepto_extra`/
    `monto_extra` en `None`): la carga manual sigue siendo el fallback
    acordado con la TL (P4). El número de factura no tiene contraparte
    manual — si AyC no la reporta (`numero_factura=None`), no hay nada que
    pisar."""
    detalle = await cd_gateway.get_detalle(cd_liq.id)
    if detalle is None:
        return False, False
    extra_actualizado = await _actualizar_extra(liquidaciones, liquidacion, detalle)
    factura_actualizada = await _actualizar_factura(liquidaciones, liquidacion, detalle)
    return extra_actualizado, factura_actualizada


async def _actualizar_extra(
    liquidaciones: LiquidacionRepository, liquidacion: Liquidacion, detalle: CdLiquidacionDetalle
) -> bool:
    if detalle.monto_extra is None:
        return False
    if (
        detalle.concepto_extra == liquidacion.concepto_extra
        and detalle.monto_extra == liquidacion.monto_extra
    ):
        return False
    nuevo_total = total_importe_tras_cambiar_extra(liquidacion, detalle.monto_extra)
    await liquidaciones.update_totales(liquidacion.id, liquidacion.total_incidentes, nuevo_total)
    await liquidaciones.update_extra(liquidacion.id, detalle.concepto_extra, detalle.monto_extra)
    return True


async def _actualizar_factura(
    liquidaciones: LiquidacionRepository, liquidacion: Liquidacion, detalle: CdLiquidacionDetalle
) -> bool:
    """El link al PDF (`factura_pdf_url`) se calcula una sola vez — la primera
    vez que aparece `numero_factura`, o cuando ese número cambia — y no se
    recalcula en reconciliaciones posteriores mientras el número siga igual.
    Así una liquidación que ya tenía el número guardado antes de que este
    campo existiera lo completa solo en el próximo ciclo del job (backfill),
    pero una vez calculada la URL queda fija. Verificado contra AyC real
    (liquidación 3951-6, 2026-09-04): `Fecha` en `getLiquidationById` no es
    estable en el tiempo (no es la fecha fija de subida del archivo, cambia
    entre corridas) — recalcular con ese campo en cada reconciliación pisaba
    una URL válida con una fecha equivocada."""
    if detalle.numero_factura is None:
        return False
    numero_sin_cambios = detalle.numero_factura == liquidacion.numero_factura
    if numero_sin_cambios and liquidacion.factura_pdf_url is not None:
        return False
    pdf_url = _calcular_pdf_url(liquidacion, detalle)
    if numero_sin_cambios and pdf_url == liquidacion.factura_pdf_url:
        return False
    await liquidaciones.update_numero_factura(liquidacion.id, detalle.numero_factura, pdf_url)
    return True


def _calcular_pdf_url(liquidacion: Liquidacion, detalle: CdLiquidacionDetalle) -> str | None:
    if (
        detalle.fecha is None
        or not detalle.rs_prestador
        or not detalle.numero_factura
        or not liquidacion.numero_liquidacion
    ):
        return None
    return armar_factura_pdf_url(
        fecha=detalle.fecha,
        rs_prestador=detalle.rs_prestador,
        numero_factura=detalle.numero_factura,
        numero_liquidacion=liquidacion.numero_liquidacion,
    )
