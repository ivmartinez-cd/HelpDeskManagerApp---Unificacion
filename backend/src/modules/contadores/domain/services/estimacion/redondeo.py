"""Aritmética `decimal` del legacy (`CalculadorContadores` opera en `decimal`
de C#). `Math.Round(x, n)` de C# sobre decimal es redondeo bancario
(`MidpointRounding.ToEven`): se replica con `decimal.Decimal` y
`ROUND_HALF_EVEN`, no con `round()` sobre float, para que un .5 exacto dé lo
mismo que en el Estimador de Contadores."""

from decimal import ROUND_HALF_EVEN, Decimal

from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput

CERO = Decimal(0)


def a_decimal(valor: float) -> Decimal:
    """`repr` da la representación decimal más corta del float (130000.0,
    12345.5), que es el valor que SiGes guardó como `decimal(18,2)`."""
    return Decimal(repr(valor))


def redondear(valor: Decimal, decimales: int = 0) -> Decimal:
    return valor.quantize(Decimal(1).scaleb(-decimales), rounding=ROUND_HALF_EVEN)


def a_float(valor: Decimal) -> float:
    # `+ 0.0` normaliza un -0 (redondeo de -0,4) a 0, como el decimal de C#.
    return float(valor) + 0.0


def contador_anterior_o_cero(entrada: EstimacionInput) -> Decimal:
    """`ContadorAnterior_Valor.GetValueOrDefault()` del legacy."""
    anterior = entrada.ultimo_contador_facturado
    return a_decimal(anterior.valor) if anterior is not None else CERO


def base_cascada(entrada: EstimacionInput) -> Decimal:
    """`ContadorAnterior ?? UltimoReal ?? 0` — base a la que la cascada T19
    le suma las impresiones del parque."""
    for lectura in (entrada.ultimo_contador_facturado, entrada.ultimo_real):
        if lectura is not None:
            return a_decimal(lectura.valor)
    return CERO
