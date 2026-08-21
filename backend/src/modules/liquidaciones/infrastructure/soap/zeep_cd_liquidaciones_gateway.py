"""Gateway zeep para el SOAP de liquidaciones de Canal Directo.

Mismo patrón que ZeepWsAycGateway (insumos): cada llamada en asyncio.to_thread
para no bloquear el event loop; el cliente sale del provider compartido
(ADR-018) — el WSDL es el mismo endpoint que el módulo insumos, wsAyC expone
también métodos de liquidaciones. Acá quedan las operaciones, el parsing y el
manejo de errores por método, que son negocio de liquidaciones.
"""

import asyncio
import contextlib
import json
import logging
from datetime import date, datetime
from typing import Any

from src.modules.liquidaciones.domain.services.estados_ayc import estado_id_para_escribir
from src.modules.liquidaciones.domain.services.numeracion_ayc import numero_liquidacion
from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import (
    CdIncidenteRow,
    CdLiquidacion,
    CdLiquidacionDetalle,
)
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.wsayc.client_provider import (
    WsAycClientProvider,
    get_wsayc_client_provider,
)

logger = logging.getLogger(__name__)

_DATE_FMT_CIERRE = "%Y%m%d"
_DATE_FMT_FECHA = "%d/%m/%Y"


class ZeepCdLiquidacionesGateway:
    def __init__(self, provider: WsAycClientProvider | None = None) -> None:
        self._provider = provider or get_wsayc_client_provider()

    def _service(self) -> Any:
        return self._provider.service()

    async def get_liquidaciones(
        self, empresa_cd_id: int, top: int = 200
    ) -> list[CdLiquidacion]:
        try:
            raw = await asyncio.to_thread(
                lambda: self._service().getTopLiquidations(
                    IdEmpresa=str(empresa_cd_id), IdEstado="", OrderBy="", Top=str(top)
                )
            )
            return _parse_liquidaciones(raw, empresa_cd_id)
        except Exception as exc:
            logger.warning(
                "SOAP getTopLiquidations(empresa=%d) falló", empresa_cd_id, exc_info=exc
            )
            return []

    async def get_incidentes(self, liquidacion_id: int) -> list[CdIncidenteRow]:
        """A diferencia de `get_liquidaciones`, acá un fallo SOAP se propaga en vez de
        devolver `[]`: `[]` legítimo (liquidación sin incidentes) y `[]` por fallo de
        red son indistinguibles para el caller, y el caller puede usar este resultado
        para reconciliar (potencialmente borrar) incidentes existentes — confundir
        "no hay" con "no se pudo consultar" ahí es peligroso, no solo impreciso."""
        try:
            raw = await asyncio.to_thread(
                lambda: self._service().getLiquidationDetails(nro=str(liquidacion_id))
            )
            return _parse_incidentes(raw)
        except Exception as exc:
            logger.warning(
                "SOAP getLiquidationDetails(id=%d) falló", liquidacion_id, exc_info=exc
            )
            raise ExternalServiceError(
                f"getLiquidationDetails(id={liquidacion_id}) falló"
            ) from exc

    async def get_detalle(self, liquidacion_ayc_id: int) -> CdLiquidacionDetalle | None:
        try:
            raw = await asyncio.to_thread(
                lambda: self._service().getLiquidationById(id=str(liquidacion_ayc_id))
            )
            return _parse_detalle(raw)
        except Exception as exc:
            logger.warning(
                "SOAP getLiquidationById(id=%d) falló al pedir el detalle",
                liquidacion_ayc_id,
                exc_info=exc,
            )
            return None

    async def set_estado(
        self, liquidacion_ayc_id: int, nuevo_estado: str, usuario: str
    ) -> None:
        """`nuevo_estado`: constante local (`ESTADO_APROBADA`, `ESTADO_OBSERVADA`,
        etc. de `domain/entities/liquidacion.py`) — se traduce acá al id numérico
        vía `estados_ayc.estado_id_para_escribir` (wsAyC espera el numérico, no
        el nombre: pasar "Aprobada" retorna '""' sin cambiar el estado, pasar "4"
        sí lo aplica, verificado 2026-08-14). Sin try/except: la excepción de
        zeep, o el `KeyError` de un `nuevo_estado` sin id (ej. "abierta"),
        propagan crudas al use case."""
        estado_id = estado_id_para_escribir(nuevo_estado)
        raw = await asyncio.to_thread(
            lambda: self._service().setLiquidationStatus(
                id=str(liquidacion_ayc_id),
                newStatus=str(estado_id),
                usuario=usuario,
            )
        )
        logger.debug(
            "setLiquidationStatus(%d, %r, %r): raw=%r",
            liquidacion_ayc_id, nuevo_estado, usuario, raw,
        )
        _raise_if_soap_error(
            raw, f"setLiquidationStatus id={liquidacion_ayc_id} estado={nuevo_estado!r}"
        )

    async def void_liquidacion(self, liquidacion_ayc_id: int) -> None:
        # Sin try/except, igual que set_estado.
        # voidLiquidation retorna '""' en éxito (verificado con 3929-7 en 2026-08-14).
        # Formato correcto: {"Liquidation": {"id": "<id>"}}.
        raw = await asyncio.to_thread(
            lambda: self._service().voidLiquidation(
                Datos=json.dumps({"Liquidation": {"id": str(liquidacion_ayc_id)}})
            )
        )
        logger.debug("voidLiquidation(%d): raw=%r", liquidacion_ayc_id, raw)
        _raise_if_soap_error(raw, f"voidLiquidation id={liquidacion_ayc_id}")


def _raise_if_soap_error(raw: Any, context: str) -> None:
    """Levanta RuntimeError si el raw de wsAyC indica un error explícito.

    AyC usa patrones distintos según la operación:
    - '"false"' / 'false' → falla genérica
    - '"Error: <mensaje>"' → error descriptivo del servidor
    - '""' → éxito (verificado para voidLiquidation en 2026-08-14)
    """
    normalized = str(raw or "").strip().strip('"').lower()
    if normalized == "false" or normalized.startswith("error:"):
        raise RuntimeError(f"{context}: {raw!r}")


def _parse_liquidaciones(raw: str, empresa_cd_id: int) -> list[CdLiquidacion]:
    items = json.loads(raw) if raw else []
    result = []
    for item in items:
        liq = item.get("Liquidation", item)
        liq_id_raw = liq.get("id")
        if not liq_id_raw:
            logger.warning(
                "getTopLiquidations(empresa=%d): item sin 'id', descartado: %s",
                empresa_cd_id,
                item,
            )
            continue
        liq_id = int(liq_id_raw)
        fecha = _parse_fecha_liquidacion(liq.get("Fecha", ""))
        if fecha is None:
            logger.warning(
                "getTopLiquidations(empresa=%d): item %s con Fecha ilegible %r, descartado",
                empresa_cd_id,
                liq_id_raw,
                liq.get("Fecha"),
            )
            continue
        result.append(
            CdLiquidacion(
                id=liq_id,
                prestador_cd_id=empresa_cd_id,
                numero_liquidacion=numero_liquidacion(liq_id),
                fecha_liquidacion=fecha,
                estado=liq.get("Estado", ""),
                cant_incidentes=int(liq.get("CantIncidentes", 0) or 0),
                estado_id=_safe_int(liq.get("estado_id")),
            )
        )
    return result


def _parse_incidentes(raw: str) -> list[CdIncidenteRow]:
    items = json.loads(raw) if raw else []
    result = []
    for item in items:
        try:
            result.append(_parse_incidente_row(item))
        except Exception as exc:
            logger.warning("Error parseando incidente SOAP %s", item, exc_info=exc)
    return result


def _parse_incidente_row(row: dict[str, Any]) -> CdIncidenteRow:
    cant_km = _safe_float(row.get("CantidadKm", "0"))
    costo_km = _safe_float(row.get("CostoKm", "0"))
    fecha_raw = row.get("FechaCierre", "")
    fecha = None
    if fecha_raw:
        with contextlib.suppress(ValueError):
            fecha = datetime.strptime(fecha_raw, _DATE_FMT_CIERRE).date()
    return CdIncidenteRow(
        id=int(row["id"]),
        tipo=row.get("Tipo", "Correctivo"),
        empresa_nombre=row.get("Empresa", ""),
        sucursal_nombre=row.get("Sucursal", ""),
        nro_serie=row.get("NroSerie", ""),
        fecha_cierre=fecha,
        costo_servicio=_safe_float(row.get("CostoServicio", "0")),
        cant_km=cant_km,
        costo_km=costo_km,
        rubro=row.get("Rubro", "Impresoras"),
        pasa_it=str(row.get("PlanillaIT", "1")) == "1",
    )


def _parse_detalle(raw: str) -> CdLiquidacionDetalle | None:
    if not raw:
        return None
    datos = json.loads(raw)
    liq = datos.get("Liquidation", datos)
    monto = _safe_float(liq.get("Extra", "0")) or None
    concepto = _fix_mojibake(str(liq.get("DetalleExtra", "")).strip()) or None if monto else None
    numero_factura = _armar_numero_factura(liq.get("FacturaLocal", ""), liq.get("FacturaNro", ""))
    return CdLiquidacionDetalle(
        concepto_extra=concepto, monto_extra=monto, numero_factura=numero_factura
    )


def _armar_numero_factura(punto_venta: str, numero: str) -> str | None:
    """`f"{FacturaLocal}-{FacturaNro}"`, mismo formato sin padding que ya usa
    `getTopLiquidations` en su campo `NroFactura` (verificado: liquidación real
    3928, `FacturaLocal="2"`+`FacturaNro="144"` → `"2-144"`, idéntico al
    `NroFactura` que trae `getTopLiquidations` para la misma liquidación).
    `""` en cualquiera de los dos es "todavía no facturada"."""
    punto_venta = str(punto_venta).strip()
    numero = str(numero).strip()
    if not punto_venta or not numero:
        return None
    return f"{punto_venta}-{numero}"


def _fix_mojibake(texto: str) -> str:
    """AyC devuelve algunos `DetalleExtra` con acentos double-encoded (UTF-8
    reinterpretado como Latin-1 y re-codificado — ej. "CiÂ­vico" en vez de
    "Ci\xadvico") — verificado contra la liquidación real 3929-7 (2026-08-20).
    Revierte esa vuelta de más; si el texto ya es UTF-8 válido de una sola
    pasada, el roundtrip falla y se devuelve el original sin tocar."""
    try:
        return texto.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return texto


def _parse_fecha_liquidacion(valor: str) -> date | None:
    if not valor:
        return None
    try:
        return datetime.strptime(valor, _DATE_FMT_FECHA).date()
    except ValueError:
        return None


def _safe_float(valor: Any) -> float:
    try:
        return float(str(valor).strip() or "0")
    except ValueError:
        return 0.0


def _safe_int(valor: Any) -> int | None:
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        return None
