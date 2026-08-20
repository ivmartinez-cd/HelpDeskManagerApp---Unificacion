import uuid
from datetime import date
from typing import Protocol


class ImpactoTurnosLookup(Protocol):
    """Puerto vacaciones → turnos (ADR-025): ¿el usuario de la plataforma tiene
    franjas de turno asignadas que intersectan el rango? Solo lectura; la
    grilla de cobertura NO se crea automáticamente (exige criterio humano), el
    resultado alimenta el aviso `afecta_turnos` de la decisión. Implementado en
    infrastructure leyendo las tablas de turnos -- el contrato
    `vacaciones-domain-app-independent-from-turnos` prohíbe importarlas acá."""

    async def tiene_turnos_en(self, user_id: uuid.UUID, desde: date, hasta: date) -> bool: ...


class ImpactoTurnosLookupNulo:
    """Default para wiring sin turnos (tests, scripts): nunca avisa."""

    async def tiene_turnos_en(self, user_id: uuid.UUID, desde: date, hasta: date) -> bool:
        return False
