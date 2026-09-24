from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    MarcaEstimacion,
)


def marcas(*pares: tuple[MarcaEstimacion, bool]) -> frozenset[MarcaEstimacion]:
    """Arma el `MarcasEstimacion` del legacy a partir de pares (marca, se
    cumple): `marcas(("AjustadoPorReceso", ajusto), ("UsaT4EnPar", t4))`."""
    return frozenset(marca for marca, presente in pares if presente)
