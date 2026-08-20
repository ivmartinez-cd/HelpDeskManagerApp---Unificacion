"""Detección de instrucciones de entrega alternativa en la observación de una zona.

Algunas zonas tienen equipos ubicados físicamente en un lugar pero cuya entrega de
insumos debe despacharse a otra sucursal (caso testigo: Arcadium Lithium, equipos en
la mina, entrega en la oficina de Salta). Esa instrucción vive como texto libre en
`customer_zone_contacts.observaciones`, típicamente "CARGAR PARA SUCURSAL: <nombre>" —
pero el operador que la carga no sigue un formato fijo (orden de palabras variable,
"PARA CARGAR EN SUCURSAL X", "DESPACHAR A SUCURSAL X", etc.), así que el disparador no
exige una frase exacta: alcanza con que la observación mencione "sucursal" junto a algún
verbo de despacho/entrega, en cualquier orden.

No confundir con `sds_contact_parser._SUCURSAL_RE`: esa aplica sobre OTRA fuente (el
comentario libre de un equipo en SDS Insight) y exige la frase exacta "CARGAR PARA
SUCURSAL:". Acá el disparador es deliberadamente laxo porque quien carga la observación
de zona no sigue ningún formato.

No hay forma de fijar la sucursal de entrega vía SOAP `persistNewSupply` — el campo de
sucursal del pedido se resuelve del lado del servicio a partir de la ubicación
registrada del equipo, nunca del payload que manda este cliente (ver
docs/adr/003-scraping-canal-directo.md del legacy). Por eso esto solo alimenta un aviso
en la UI — el cambio de sucursal lo sigue haciendo el operador a mano en Canal Directo
después de cargar el pedido.
"""

import logging
import re
import unicodedata
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Ninguna de estas palabras lleva acentos en su ortografía correcta, pero se normaliza
# igual (typos, variantes de teclado) antes de buscar. Substring simple (no \b): así
# "descargar"/"recargar"/"despachar"/"envío" matchean por su raíz sin listar cada forma.
_ACTION_WORDS = re.compile(r"cargar|despach|entreg|env(?:i|í)|dirigi|manda")
# La palabra "sucursal" sola no alcanza — tiene que aparecer junto con un verbo de
# despacho en la misma observación.
_SUCURSAL_WORD = re.compile(r"sucursal\s*:?\s*")
# Delimitadores donde cortar el nombre de sucursal extraído: paréntesis de aclaración,
# punto final, punto y coma, o salto de línea.
_STOP_CHARS = "(.;\n"


def _fold(text: str) -> str:
    """Minúscula + sin acentos, preservando la longitud char a char.

    Al mapear 1 a 1 se puede usar el índice de un match sobre el texto "folded" para
    cortar el texto ORIGINAL (con su casing y acentos reales) en el mismo punto.
    """
    out = []
    for ch in text:
        base = ch
        for part in unicodedata.normalize("NFKD", ch):
            if not unicodedata.combining(part):
                base = part
                break
        out.append(base.lower())
    return "".join(out)


@dataclass(frozen=True)
class SucursalOverride:
    """Resultado de la detección. `sucursal` puede ser None con requiere_cambio=True
    cuando se detectó el patrón pero no se pudo extraer un nombre de sucursal legible —
    en ese caso la UI muestra igual el aviso, con `observacion` completa."""

    requiere_cambio: bool
    sucursal: str | None
    observacion: str


_SIN_AVISO = SucursalOverride(requiere_cambio=False, sucursal=None, observacion="")


def detect_sucursal_override(observaciones: str | None) -> SucursalOverride:
    """Detecta si la observación de una zona pide despachar a una sucursal distinta.

    Dispara con cualquier orden de palabras — no exige la frase exacta "CARGAR PARA
    SUCURSAL", solo que "sucursal" y algún verbo de despacho/entrega aparezcan juntos
    en la observación. Nunca lanza: ante cualquier observación rara, devuelve el aviso
    igual mostrando el texto completo — un falso aviso sale mucho más barato que un
    despacho al lugar equivocado.
    """
    text = (observaciones or "").strip()
    if not text:
        return _SIN_AVISO

    try:
        folded = _fold(text)
        if not _ACTION_WORDS.search(folded):
            return SucursalOverride(requiere_cambio=False, sucursal=None, observacion=text)

        match = _SUCURSAL_WORD.search(folded)
        if not match:
            return SucursalOverride(requiere_cambio=False, sucursal=None, observacion=text)

        candidate = text[match.end() :]
        cut = len(candidate)
        for ch in _STOP_CHARS:
            idx = candidate.find(ch)
            if idx != -1:
                cut = min(cut, idx)
        sucursal = candidate[:cut].strip(" \t-:") or None
        return SucursalOverride(requiere_cambio=True, sucursal=sucursal, observacion=text)
    except Exception:
        logger.warning(
            "detect_sucursal_override: fallo parseando observación, se avisa igual "
            "(fail-open: un falso aviso sale más barato que un despacho al lugar "
            "equivocado)",
            extra={"observaciones": text},
            exc_info=True,
        )
        return SucursalOverride(requiere_cambio=True, sucursal=None, observacion=text)
