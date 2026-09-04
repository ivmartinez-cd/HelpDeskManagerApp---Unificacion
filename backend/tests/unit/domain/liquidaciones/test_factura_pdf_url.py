"""`armar_factura_pdf_url` — verificado contra un caso real: liquidación 3943-7
(La Rioja, Mario Javier Lopez), `getLiquidationById` devolvió
`Fecha="02/09/2026"` + `RsPrestador="LOPEZ MARIO JAVIER"` + `FacturaLocal="6"`
+ `FacturaNro="417"`, y la URL real cargada en AyC (botón "Visualizar" de la
sección FACTURA en webagentes) es
`.../liquidations/20260902_lopez_mario_javier_fc-6-417_3943-7.pdf`."""

from datetime import date

from src.modules.liquidaciones.domain.services.factura_pdf_url import armar_factura_pdf_url


def test_arma_la_url_real_verificada_contra_liquidacion_3943_7() -> None:
    url = armar_factura_pdf_url(
        fecha=date(2026, 9, 2),
        rs_prestador="LOPEZ MARIO JAVIER",
        numero_factura="6-417",
        numero_liquidacion="3943-7",
    )

    assert url == (
        "https://webagentes.canaldirecto.com.ar/files/webagentes/liquidations/"
        "20260902_lopez_mario_javier_fc-6-417_3943-7.pdf"
    )


def test_normaliza_acentos_y_espacios_multiples() -> None:
    url = armar_factura_pdf_url(
        fecha=date(2026, 1, 5),
        rs_prestador="PÉREZ  ÑOÑO   José",
        numero_factura="1-1",
        numero_liquidacion="1-1",
    )

    assert "perez_nono_jose" in url
