"""Filas de `consulta_despachos` a `DespachoSiges`.

La consulta devuelve una fila por (remito, incidente), así que un remito que lleva varios
pedidos de insumos llega repartido en varias filas: acá se agrupa por `id_remito`,
conservando el orden en que llegan (fecha de remito descendente). Los textos de SiGes
suelen traer espacios de relleno y los LEFT JOIN traen None cuando no hay dato: todo texto
se normaliza a `str` recortado, "" si falta. Las filas de pyodbc se leen por atributo
(`fila.guia`), con los alias de la consulta.
"""

from collections.abc import Iterable
from datetime import date, datetime
from typing import Any

from src.modules.insumos.domain.value_objects.despachados.despacho_siges import (
    DespachoSiges,
    IncidenteInsumo,
)


def mapear_despachos(filas: Iterable[Any]) -> list[DespachoSiges]:
    """Un `DespachoSiges` por remito, en el orden en que aparece cada uno por primera vez."""
    por_remito: dict[int, list[Any]] = {}
    for fila in filas:
        por_remito.setdefault(int(fila.id_remito), []).append(fila)
    return [_despacho(grupo) for grupo in por_remito.values()]


def _despacho(filas: list[Any]) -> DespachoSiges:
    primera = filas[0]
    return DespachoSiges(
        id_remito=int(primera.id_remito),
        numero_remito=int(primera.numero_remito),
        guia=_texto(primera.guia),
        id_distribucion=int(primera.id_distribucion),
        fecha_remito=_fecha(primera.fecha_remito),
        bultos=_entero(primera.bultos),
        cliente=_texto(primera.cliente),
        sucursal_cliente=_texto(primera.sucursal_cliente),
        entrega_a=_texto(primera.entrega_a),
        incidentes=_incidentes(filas),
    )


def _incidentes(filas: list[Any]) -> tuple[IncidenteInsumo, ...]:
    """Sin repetidos y en orden de aparición. La fila de un remito sin incidente (el LEFT
    JOIN la trae con None) no aporta ninguno: ese remito queda con la tupla vacía."""
    incidentes = (
        IncidenteInsumo(
            numero=_texto(fila.numero_incidente),
            numero_cliente=_texto(fila.numero_incidente_cliente),
        )
        for fila in filas
        if _texto(fila.numero_incidente)
    )
    return tuple(dict.fromkeys(incidentes))


def _texto(valor: object) -> str:
    return "" if valor is None else str(valor).strip()


def _entero(valor: Any) -> int:
    """`Bultos` sin cargar se toma como 0 para no perder el remito por un dato informativo."""
    return 0 if valor is None else int(valor)


def _fecha(valor: date) -> date:
    """pyodbc devuelve `smalldatetime` como `datetime`; el dominio usa solo la fecha."""
    return valor.date() if isinstance(valor, datetime) else valor
