from src.modules.reporte_incidentes.application.use_cases.vista_reporte import colores_categorias
from src.modules.reporte_incidentes.domain.services.colores import color_por_nombre
from src.modules.reporte_incidentes.domain.services.tipificacion import (
    COLOR_PENDIENTE,
    COLOR_SIN_CLASIFICAR,
    PENDIENTE,
    SIN_CLASIFICAR,
)
from tests.unit.application.reporte_incidentes.fakes import TAXONOMIA, FakeArmar
from tests.unit.domain.reporte_incidentes.fakes import incidente


async def test_categoria_borrada_de_la_taxonomia_toma_el_color_por_nombre() -> None:
    vigente = TAXONOMIA[0]
    reporte = await FakeArmar(
        [incidente(categoria=vigente.nombre), incidente(categoria="Categoría vieja"),
         incidente(categoria=PENDIENTE), incidente()],
    ).execute(None)  # type: ignore[arg-type]

    colores = colores_categorias(reporte)

    assert colores[vigente.nombre] == vigente.color
    assert colores["Categoría vieja"] == color_por_nombre("Categoría vieja")
    assert colores[PENDIENTE] == COLOR_PENDIENTE
    assert colores[SIN_CLASIFICAR] == COLOR_SIN_CLASIFICAR
