"""Reconstruye la URL real del PDF de factura que el prestador carga en AyC
(botón "Visualizar" de la sección FACTURA en webagentes) — AyC no la expone
como campo directo en ningún método del SOAP, solo el número de factura
(`FacturaLocal`-`FacturaNro`).

Convención de nombre de archivo verificada contra dos casos reales:

- Liquidación 3943-7, La Rioja, 2026-09-04: `getLiquidationById` devolvió
  `Fecha="02/09/2026"`, `RsPrestador="LOPEZ MARIO JAVIER"`, `FacturaLocal="6"`,
  `FacturaNro="417"`, y la URL real cargada en AyC es
  `.../liquidations/20260902_lopez_mario_javier_fc-6-417_3943-7.pdf`.
- Liquidación 3959-8, 2026-09-07: `RsPrestador="PENTACOM S.A."`,
  `FacturaNro="14-2115"`, y la URL real es
  `.../liquidations/20260907_pentacom_s.a._fc-14-2115_3959-8.pdf` — el punto
  de la abreviatura ("S.A.") se conserva tal cual, solo los espacios se
  vuelven `_`. La primera versión de este slug convertía el punto en espacio
  igual que cualquier separador y generaba `..._pentacom_s_a_fc-..._...pdf`,
  que no coincide con el archivo real (404 al abrir el link desde la app).

Coincide exactamente con `{fecha:%Y%m%d}_{slug(rs_prestador)}_fc-
{numero_factura}_{numero_liquidacion}.pdf`. La normalización de
`rs_prestador` (acentos, Ñ, otros separadores fuera de espacio/punto) sigue
sin confirmarse contra más casos — si un link generado por acá da 404, ese es
el primer sospechoso."""

import unicodedata
from datetime import date

_BASE_URL = "https://webagentes.canaldirecto.com.ar/files/webagentes/liquidations"


def armar_factura_pdf_url(
    *, fecha: date, rs_prestador: str, numero_factura: str, numero_liquidacion: str
) -> str:
    slug = _slug(rs_prestador)
    return f"{_BASE_URL}/{fecha:%Y%m%d}_{slug}_fc-{numero_factura}_{numero_liquidacion}.pdf"


def _slug(texto: str) -> str:
    sin_acentos = "".join(
        ch for ch in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(ch)
    )
    limpio = "".join(
        ch if (ch.isalnum() or ch == ".") else " " for ch in sin_acentos.lower()
    )
    return "_".join(limpio.split())
