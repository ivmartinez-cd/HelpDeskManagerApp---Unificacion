"""Color por nombre para categorías que ya no están en la taxonomía. Los
matices esperados salen de correr el `hashColor` del legacy en Node."""

import pytest

from src.modules.reporte_incidentes.domain.services.colores import color_por_nombre


@pytest.mark.parametrize(
    ("nombre", "esperado"),
    [
        ("Hardware", "#cc335c"),  # hsl(344, 60%, 50%)
        ("Categoría vieja", "#c233cc"),  # hsl(296, ...)
        ("Soporte Remoto y Configuración", "#6633cc"),  # hsl(260, ...): el hash desborda int32
        ("ñandú €", "#33cc70"),  # hsl(144, ...)
        ("Z", "#80cc33"),  # hsl(90, ...)
    ],
)
def test_color_por_nombre_replica_el_hash_del_legacy(nombre: str, esperado: str) -> None:
    assert color_por_nombre(nombre) == esperado


def test_mismo_nombre_mismo_color() -> None:
    assert color_por_nombre("Vieja") == color_por_nombre("Vieja")
