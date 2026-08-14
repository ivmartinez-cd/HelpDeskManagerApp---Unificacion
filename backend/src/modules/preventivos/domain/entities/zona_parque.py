from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ZonaParque:
    """Una zona de distribución local (valor de `Sucursal.Cuadricula` en Siges;
    texto libre sin catálogo propio — el catálogo real es el DISTINCT de las
    sucursales activas, ver SIGES_READONLY_CATALOGO_DATOS.md §3)."""

    zona: str
    maquinas_activas: int
