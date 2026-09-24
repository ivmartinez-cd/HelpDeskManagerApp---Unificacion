"""Formatos numéricos que usa el `DetalleCalculo` del legacy, en cultura
es-AR (coma decimal, sin separador de miles porque los formatos custom
`"0"`/`"0.##"` no lo llevan). A diferencia de `Math.Round`, el formateo de un
`decimal` en .NET redondea el medio "lejos del cero" (`ROUND_HALF_UP` de
Python) y nunca imprime "-0"."""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

_CENTESIMO = Decimal("0.01")


def entero(valor: Decimal) -> str:
    """`{x:0}`."""
    return str(int(valor.quantize(Decimal(1), rounding=ROUND_HALF_UP)))


def hasta_dos_decimales(valor: Decimal) -> str:
    """`{x:0.##}` — 12,5 / 12 / 12,35."""
    redondeado = valor.quantize(_CENTESIMO, rounding=ROUND_HALF_UP)
    if redondeado == 0:
        return "0"
    texto = f"{redondeado:f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def dos_decimales(valor: Decimal) -> str:
    """`{x:0.00}` — 0,50."""
    redondeado = valor.quantize(_CENTESIMO, rounding=ROUND_HALF_UP)
    if redondeado == 0:
        redondeado = abs(redondeado)
    return f"{redondeado:f}".replace(".", ",")


def con_signo(numero: int) -> str:
    """`{x:+0;-0}` — el cero sale con "+"."""
    return f"+{numero}" if numero >= 0 else str(numero)


def fecha_corta(fecha: date) -> str:
    """`{x:dd/MM/yy}`."""
    return fecha.strftime("%d/%m/%y")
