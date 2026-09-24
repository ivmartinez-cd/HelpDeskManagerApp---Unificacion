"""Aritmética de `System.Decimal` (C#), que es la que usa el motor legacy.

Un `decimal` de .NET es una mantisa entera de 96 bits con escala 0..28: el
cociente 2/24 da 0,0833333333333333333333333333 (27 dígitos significativos)
donde `decimal.Decimal` de Python con precisión 28 da un dígito más. Esa
diferencia en el dígito 28 alcanza para que un `Math.Round` posterior caiga
del otro lado de un ,5 (29634 × 2/24 da 2469 en el legacy y 2470 con la
aritmética de Python). Por eso cada operación con resultado no exacto se
calcula con precisión holgada y se reduce a lo que cabe en un `System.Decimal`
(redondeo al par, como `DecCalc`)."""

from decimal import ROUND_HALF_EVEN, Context, Decimal

_CONTEXTO_HOLGADO = Context(prec=60)
_ESCALA_MAXIMA = 28
_MANTISA_MAXIMA = Decimal(2**96 - 1)


def a_rango_cs(valor: Decimal) -> Decimal:
    """Mayor escala (<= 28) cuya mantisa entra en 96 bits."""
    for escala in range(_ESCALA_MAXIMA, -1, -1):
        cuanto = Decimal(1).scaleb(-escala)
        ajustado = valor.quantize(cuanto, rounding=ROUND_HALF_EVEN, context=_CONTEXTO_HOLGADO)
        if abs(ajustado.scaleb(escala, context=_CONTEXTO_HOLGADO)) <= _MANTISA_MAXIMA:
            return ajustado
    return valor


def dividir(dividendo: Decimal, divisor: Decimal | int) -> Decimal:
    return a_rango_cs(_CONTEXTO_HOLGADO.divide(dividendo, Decimal(divisor)))


def multiplicar(a: Decimal, b: Decimal | int) -> Decimal:
    return a_rango_cs(_CONTEXTO_HOLGADO.multiply(a, Decimal(b)))


def sumar(a: Decimal, b: Decimal) -> Decimal:
    return a_rango_cs(_CONTEXTO_HOLGADO.add(a, b))
