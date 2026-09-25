"""Color de las categorías que ya no están en la taxonomía (port de
`hashColor` de `lib/ai/categories.ts` del legacy).

Un incidente tipificado con una categoría que después se borró o renombró
conserva esa categoría en la caché. El legacy le daba un color estable derivado
del nombre, `hsl(h, 60%, 50%)`, para que se distinga en la dona y en la tabla;
acá se devuelve el mismo color pero en `#rrggbb`, porque el frontend atenúa los
colores del gráfico agregándoles alfa en hexadecimal."""

import colorsys
import struct


def _int32(valor: int) -> int:
    valor &= 0xFFFFFFFF
    return valor - 0x1_0000_0000 if valor & 0x8000_0000 else valor


def _matiz(nombre: str) -> int:
    # Réplica exacta del hash JS: `(hash << 5)` trunca a int32, la resta y la
    # suma no; `%` conserva el signo del dividendo y después va `Math.abs`.
    # `charCodeAt` recorre unidades UTF-16, no caracteres.
    utf16 = nombre.encode("utf-16-le")
    acumulado = 0
    for codigo in struct.unpack(f"<{len(utf16) // 2}H", utf16):
        acumulado = codigo + (_int32(_int32(acumulado) << 5) - acumulado)
    return abs(acumulado) % 360


def color_por_nombre(nombre: str) -> str:
    rojo, verde, azul = colorsys.hls_to_rgb(_matiz(nombre) / 360, 0.5, 0.6)
    return "#" + "".join(f"{round(c * 255):02x}" for c in (rojo, verde, azul))
