from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ErsClient:
    """Cliente (grupo de dispositivos) devuelto por Epson Remote Services (ERS)."""

    id: str
    name: str
    status: str = "ACTIVE"
