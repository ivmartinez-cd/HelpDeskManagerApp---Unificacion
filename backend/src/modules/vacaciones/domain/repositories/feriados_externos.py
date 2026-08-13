from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True, slots=True)
class FeriadoImportado:
    fecha: date
    nombre: str


class FeriadosExternosProvider(Protocol):
    """Proveedor de feriados de Argentina (api.argentinadatos.com en la impl).
    Levanta ExternalServiceError si el servicio falla."""

    async def fetch(self, year: int) -> list[FeriadoImportado]: ...
