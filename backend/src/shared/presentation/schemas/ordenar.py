"""Orden por columna para endpoints que arman la colección completa en
memoria y recién después cortan la página con `Page.of`: el orden tiene que
aplicarse ANTES del corte, o cada página quedaría ordenada por separado.

`campo` es el nombre de un atributo del ítem; cada endpoint lo restringe con
un `Literal` de las columnas que muestra. Sin campo se respeta el orden de
negocio con que llegan los ítems, que además desempata (el sort es estable).
Los vacíos (None) van al final en ambos sentidos; los textos se comparan sin
distinguir mayúsculas."""

from typing import Any, Literal

DireccionOrden = Literal["asc", "desc"]


def _clave(valor: Any) -> Any:
    return valor.casefold() if isinstance(valor, str) else valor


def ordenar_por_campo[T](items: list[T], campo: str | None, direccion: DireccionOrden) -> list[T]:
    if campo is None:
        return items
    con_valor = [i for i in items if getattr(i, campo) is not None]
    sin_valor = [i for i in items if getattr(i, campo) is None]
    con_valor.sort(key=lambda i: _clave(getattr(i, campo)), reverse=direccion == "desc")
    return con_valor + sin_valor
