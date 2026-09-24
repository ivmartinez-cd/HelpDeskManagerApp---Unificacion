"""Puertos de lectura de la pantalla de Despachados y del calendario de feriados."""

from datetime import date
from typing import Protocol

from src.modules.insumos.domain.value_objects.despachados.vista_despachos import (
    FilaDespacho,
    FiltrosDespachos,
    Pagina,
    ResumenDespachos,
)


class ConsultaDespachosRepository(Protocol):
    async def listar(self, filtros: FiltrosDespachos, pagina: Pagina) -> list[FilaDespacho]:
        """Ordenadas por urgencia, como el mockup: rojo, naranja, amarillo, verde, gris,
        cerrado. Dentro del rojo, la fecha límite más próxima primero; en naranja y
        amarillo, la fecha de estado más vieja primero; en el resto, la más nueva primero
        (sin fecha de estado, al final). Desempata la guía."""
        ...

    async def contar(self, filtros: FiltrosDespachos) -> int: ...

    async def resumir(self, alcance_desde: date) -> ResumenDespachos: ...


class CalendarioFeriados(Protocol):
    async def feriados_entre(self, desde: date, hasta: date) -> frozenset[date]:
        """Feriados cargados en HDM entre las dos fechas, inclusive."""
        ...
