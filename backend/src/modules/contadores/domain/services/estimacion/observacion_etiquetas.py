"""Nivel "método + marcas" de la observación del CSV — `ResumenObservacion.Metodo`
/ `EtiquetaFuente` / `MismoMetodo` del Estimador de Contadores v1.7. Se arma
desde `metodo` y `marcas` del resultado (la `EstimacionDecision` del legacy),
no re-parseando el texto del cálculo."""

from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    FuenteEstimacion,
    MarcaEstimacion,
    MetodoEstimacion,
)

FUENTES_PARQUE: frozenset[FuenteEstimacion] = frozenset(
    {"Parque_Cliente_Modelo", "Parque_Grupo_Modelo", "Parque_Cliente_Tec", "Parque_Global_Modelo"}
)

_ETIQUETA_POR_FUENTE: dict[FuenteEstimacion, str] = {
    "Historia_Propia": "Entre reales",
    "Parque_Cliente_Modelo": "Parque cli/mod",
    "Parque_Grupo_Modelo": "Parque grupo/mod",
    "Parque_Cliente_Tec": "Parque cli/tec",
    "Parque_Global_Modelo": "Parque global/mod",
    "Backup_SinST": "Backup sin movimiento",
    "EnTransito": "En transito sin movimiento",
}

# Orden por gravedad: primero lo que puede invalidar la factura.
_NOTA_POR_MARCA: tuple[tuple[MarcaEstimacion, str], ...] = (
    ("T4SinRevisar", "(!)T4 sin revisar"),
    ("SinParValido", "sin par P/L"),
    ("InterpoladoAtras", "interp. atras"),
    ("UsaT4EnPar", "usa T4"),
    ("AjustadoPorReceso", "receso"),
    ("ForzadoPorOperador", "forzado op."),
)


def etiqueta_fuente(fuente: FuenteEstimacion, metodo: MetodoEstimacion) -> str:
    """Nombre corto del nivel de la cascada, legible sin leyenda."""
    if fuente == "T4_ST":
        return "T4 ST proyectado" if metodo == "T4ST_Proyectado" else "T4 ST tal cual"
    return _ETIQUETA_POR_FUENTE.get(fuente, "Sin estimar")


def texto_metodo(resultado: EstimacionResultado) -> str:
    """Nivel 1: el método (o "P/L manual") seguido de las marcas críticas."""
    nivel = (
        "P/L manual"
        if "PLManual" in resultado.marcas
        else etiqueta_fuente(resultado.fuente, resultado.metodo)
    )
    notas = [nota for marca, nota in _NOTA_POR_MARCA if marca in resultado.marcas]
    return nivel if not notas else f"{nivel}, {', '.join(notas)}"


def mismo_metodo(a: EstimacionResultado, b: EstimacionResultado) -> bool:
    """Mono y Color comparten método si coinciden fuente, método y marcas
    (los estadísticos pueden diferir: se emite el del principal)."""
    return a.fuente == b.fuente and a.metodo == b.metodo and a.marcas == b.marcas
