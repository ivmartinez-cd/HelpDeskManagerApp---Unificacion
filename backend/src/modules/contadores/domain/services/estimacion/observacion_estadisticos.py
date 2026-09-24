"""Niveles "impresiones", "estadísticos" y "contexto" de la observación del CSV —
`ResumenObservacion.Impresiones` / `Estadisticos` / `Parque` / `Par` /
`Contexto` del Estimador de Contadores v1.7. Números en cultura invariante
(punto decimal), a diferencia del `DetalleCalculo` de la grilla."""

from decimal import ROUND_HALF_UP, Decimal

from src.modules.contadores.domain.services.estimacion.observacion_etiquetas import (
    FUENTES_PARQUE,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    FuenteEstimacion,
)

_CENTESIMO = Decimal("0.01")
_METODOS_PAR = frozenset({"EntreReales", "T4ST_Proyectado", "T4ST_Valor"})


def signo(valor: float) -> str:
    """`{x:+0;-0}` sobre decimal: el signo lo decide el valor, la magnitud se
    redondea lejos del cero; el cero sale con "+"."""
    numero = Decimal(repr(valor))
    magnitud = int(abs(numero).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return f"-{magnitud}" if numero < 0 else f"+{magnitud}"


def impresiones(
    mono: EstimacionResultado | None, color: EstimacionResultado | None, ambas: bool
) -> str:
    """Nivel 2: "+146 imp" con una sola clase estimada, "Mono +146 Color +38"
    con las dos."""
    if not ambas:
        una = mono if mono is not None else color
        if una is None or una.impresiones is None:
            return ""
        return f"{signo(una.impresiones)} imp"
    partes = []
    if mono is not None and mono.impresiones is not None:
        partes.append(f"Mono {signo(mono.impresiones)}")
    if color is not None and color.impresiones is not None:
        partes.append(f"Color {signo(color.impresiones)}")
    return " ".join(partes)


def estadisticos(resultado: EstimacionResultado) -> str:
    """Nivel 3: respaldo de la mediana del parque o el par de la regla de
    tres. `T4ST_Valor` entra por la P/L manual con Llegada T4 (tiene par); en
    el "T4 tal cual" esos campos no existen y el nivel queda vacío solo."""
    if resultado.metodo == "MedianaTruncadaP80":
        return _parque("P80", resultado)
    if resultado.metodo == "MedianaCruda":
        return _parque("mediana", resultado)
    if resultado.metodo in _METODOS_PAR:
        return _par(resultado)
    return ""


def _parque(nombre: str, resultado: EstimacionResultado) -> str:
    detalle = resultado.detalle_parque
    if detalle is None or detalle.n_equipos <= 0:
        return ""
    desc = f"(-{detalle.n_descartados} desc)" if detalle.n_descartados > 0 else ""
    return f"{nombre} {detalle.n_equipos}eq{desc}"


def _par(r: EstimacionResultado) -> str:
    partes = []
    if r.dias_par_pl is not None and r.dias_par_pl > 0:
        partes.append(f"{r.dias_par_pl}d")
    if r.tasa_diaria is not None and r.tasa_diaria != 0:
        partes.append(f"{_hasta_dos_decimales(r.tasa_diaria)}/dia")
    if r.dias_proyectados is not None and r.dias_proyectados != 0:
        extrap = f"+{r.dias_proyectados}" if r.dias_proyectados > 0 else str(r.dias_proyectados)
        partes.append(f"extrap {extrap}d")
    return " ".join(partes)


def _hasta_dos_decimales(valor: float) -> str:
    """`{x:0.##}` en cultura invariante: 3.4 / 12 / 98765.43."""
    redondeado = Decimal(repr(valor)).quantize(_CENTESIMO, rounding=ROUND_HALF_UP)
    texto = f"{redondeado:f}".rstrip("0").rstrip(".")
    return "0" if texto in ("", "-0") else texto


def contexto(fuente: FuenteEstimacion, meses_sin_real: int | None) -> str:
    """Nivel 4: por qué se cayó al parque. Solo con fuente de parque; con 0
    meses (o sin real) el legacy dice "sin historia propia"."""
    if fuente not in FUENTES_PARQUE:
        return ""
    if meses_sin_real is not None and meses_sin_real > 0:
        return f"sin real {meses_sin_real}m"
    return "sin historia propia"
