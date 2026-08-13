"""Parsing de valores numéricos/URL del Excel maestro.

NO reusar `importacion/_valores.py::parse_monto` acá: esa función asume texto en
formato argentino (trata "." como separador de miles), pensada para el HTML
exportado del sistema fuente de las liquidaciones. Los valores de este Excel llegan
como floats reales de `pandas.read_excel` (o texto ya limpio) — tratarlos igual los
corrompería (1234.56 -> 123456.0). También, a diferencia de `parse_monto`, acá un
valor ilegible devuelve `None` (no `0.0`): la fila se descarta en vez de crearse
con `kms=0`."""

from typing import Any

_VACIOS = ("", "-", "nan", "none")


def parse_numero_excel(valor: Any) -> float | None:
    if valor is None:
        return None
    if isinstance(valor, int | float):
        return float(valor)
    texto = str(valor).strip().replace("$", "").replace(" ", "")
    if texto.lower() in _VACIOS:
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def url_o_none(valor: Any) -> str | None:
    """Solo persiste si el valor arranca con "http" — filtra el texto de display
    que Excel deja en la celda cuando el link real está en otro lado."""
    texto = str(valor).strip() if valor is not None else ""
    return texto if texto.lower().startswith("http") else None


def texto_o_none(valor: Any) -> str | None:
    """`str(None).strip()` da el string literal `"None"` (truthy) — sin este guard,
    una celda vacía de una columna opcional (Prestador/Domicilio/Localidad...) se
    persiste como el texto "None" en vez de quedar en blanco. Confirmado con datos
    reales: una fila de PENTACOM sin SPST asignado generaba un SPST fantasma
    literalmente llamado "None"."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto if texto and texto.lower() != "nan" else None
