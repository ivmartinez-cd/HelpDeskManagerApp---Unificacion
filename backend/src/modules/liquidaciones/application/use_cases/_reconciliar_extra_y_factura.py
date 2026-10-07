"""Actualiza el ítem extra y el número de factura de una liquidación contra el
detalle de AyC — extraído de `_reconciliar_liquidacion.py` (§4) porque es un
colaborador autocontenido, sin estado compartido con el resto del flujo de
reconciliación de incidentes."""

from datetime import timedelta

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
    factura_actualizada = await _actualizar_factura(
        liquidaciones, cd_gateway, liquidacion, detalle
    )
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


# Cuántos días antes de `Fecha` se busca el PDF: `Fecha` es la última
# modificación de la liquidación en AyC, no el día en que se subió la factura
# (3978-3: subida el 01/10, AyC informaba una fecha posterior).
# ponytail: hasta 15 HEAD por liquidación con número y sin PDF en cada corrida;
# si crece, guardar el último intento y espaciar los reintentos.
_DIAS_HACIA_ATRAS = 14


async def _actualizar_factura(
    liquidaciones: LiquidacionRepository,
    cd_gateway: CdLiquidacionesGateway,
    liquidacion: Liquidacion,
    detalle: CdLiquidacionDetalle,
) -> bool:
    """El número de factura se guarda recién cuando su PDF existe en webagentes:
    AyC informa el número aunque el archivo no esté (3988-0, 2026-10-07), y
    guardarlo dispara el aviso "el prestador cargó la factura". Mientras no
    aparezca, no se guarda nada y la próxima reconciliación vuelve a buscar.

    Una vez encontrado, el link no se recalcula: `Fecha` en `getLiquidationById`
    no es estable entre llamadas (verificado contra AyC real, liquidación
    3951-6, 2026-09-04)."""
    if detalle.numero_factura is None:
        return False
    numero_sin_cambios = detalle.numero_factura == liquidacion.numero_factura
    if numero_sin_cambios and liquidacion.factura_pdf_url is not None:
        return False
    pdf_url = await _buscar_pdf_url(cd_gateway, liquidacion, detalle)
    if pdf_url is None:
        return False
    await liquidaciones.update_numero_factura(liquidacion.id, detalle.numero_factura, pdf_url)
    return True


async def _buscar_pdf_url(
    cd_gateway: CdLiquidacionesGateway, liquidacion: Liquidacion, detalle: CdLiquidacionDetalle
) -> str | None:
    if (
        detalle.fecha is None
        or not detalle.rs_prestador
        or not detalle.numero_factura
        or not liquidacion.numero_liquidacion
    ):
        return None
    for dias in range(_DIAS_HACIA_ATRAS + 1):
        url = armar_factura_pdf_url(
            fecha=detalle.fecha - timedelta(days=dias),
            rs_prestador=detalle.rs_prestador,
            numero_factura=detalle.numero_factura,
            numero_liquidacion=liquidacion.numero_liquidacion,
        )
        if await cd_gateway.factura_pdf_existe(url):
            return url
    return None
