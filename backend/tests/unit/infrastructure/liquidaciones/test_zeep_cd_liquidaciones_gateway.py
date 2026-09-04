"""Tests del parseo de `Extra`/`DetalleExtra`/`FacturaLocal`/`FacturaNro` de
`getLiquidationById` — el WS de AyC reporta "sin extra cargado" como `Extra="0"`
(no ausencia del campo), "sin facturar" como `FacturaLocal`/`FacturaNro` vacíos,
y algunos `DetalleExtra` vienen con acentos double-encoded (verificado contra la
liquidación real 3929-7, 2026-08-20)."""

import json
from datetime import date

from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import CdLiquidacionDetalle
from src.modules.liquidaciones.infrastructure.soap.zeep_cd_liquidaciones_gateway import (
    _armar_numero_factura,
    _fix_mojibake,
    _parse_detalle,
)


def _raw(
    extra: str = "0",
    detalle: str = " ",
    factura_local: str = "",
    factura_nro: str = "",
    fecha: str = "",
    rs_prestador: str = "",
) -> str:
    return json.dumps(
        {
            "Liquidation": {
                "id": "3929",
                "Extra": extra,
                "DetalleExtra": detalle,
                "FacturaLocal": factura_local,
                "FacturaNro": factura_nro,
                "Fecha": fecha,
                "RsPrestador": rs_prestador,
            }
        }
    )


def test_sin_extra_ni_factura_arma_value_object_todo_none() -> None:
    assert _parse_detalle(_raw()) == CdLiquidacionDetalle(
        concepto_extra=None, monto_extra=None, numero_factura=None
    )


def test_raw_vacio_es_fallo_soap() -> None:
    assert _parse_detalle("") is None


def test_extra_con_monto_arma_el_value_object() -> None:
    detalle = " Adicional Factura NRO 0002-00001573"
    resultado = _parse_detalle(_raw(extra="1499999", detalle=detalle))

    assert resultado == CdLiquidacionDetalle(
        concepto_extra="Adicional Factura NRO 0002-00001573",
        monto_extra=1499999.0,
        numero_factura=None,
    )


def test_extra_corrige_el_mojibake_del_detalle() -> None:
    """Bytes reales de AyC para "Servicios Ci\xadvico" (2026-08-20)."""
    detalle_mojibake = " Adicional Factura NRO 0002-00001573 Servicios CiÂ­vico Julio 2026"

    resultado = _parse_detalle(_raw(extra="1499999", detalle=detalle_mojibake))

    assert resultado is not None
    assert "Â­" not in resultado.concepto_extra
    esperado = "Adicional Factura NRO 0002-00001573 Servicios Ci\xadvico Julio 2026"
    assert resultado.concepto_extra == esperado


def test_numero_factura_se_arma_desde_local_y_nro() -> None:
    """Bytes reales de AyC (liquidación 3928): `FacturaLocal="2"`+`FacturaNro="144"`
    → `"2-144"`, idéntico al `NroFactura` que trae `getTopLiquidations` para la
    misma liquidación."""
    resultado = _parse_detalle(_raw(factura_local="2", factura_nro="144"))

    assert resultado is not None
    assert resultado.numero_factura == "2-144"


def test_numero_factura_vacio_es_sin_facturar() -> None:
    resultado = _parse_detalle(_raw(factura_local="", factura_nro=""))

    assert resultado is not None
    assert resultado.numero_factura is None


def test_fix_mojibake_no_rompe_texto_ya_valido() -> None:
    assert _fix_mojibake("Seguro de viaje ítem cerrado") == "Seguro de viaje ítem cerrado"


def test_armar_numero_factura_con_alguno_vacio_es_none() -> None:
    assert _armar_numero_factura("2", "") is None
    assert _armar_numero_factura("", "144") is None


def test_fecha_y_rs_prestador_se_parsean_para_armar_el_link_de_factura() -> None:
    """Datos reales de la liquidación 3943-7 (2026-09-04) — ver
    `domain/services/factura_pdf_url.py`."""
    resultado = _parse_detalle(
        _raw(
            factura_local="6",
            factura_nro="417",
            fecha="02/09/2026",
            rs_prestador="LOPEZ MARIO JAVIER",
        )
    )

    assert resultado is not None
    assert resultado.fecha == date(2026, 9, 2)
    assert resultado.rs_prestador == "LOPEZ MARIO JAVIER"
