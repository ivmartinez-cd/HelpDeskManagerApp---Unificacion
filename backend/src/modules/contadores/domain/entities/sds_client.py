from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SdsClient:
    """Cliente devuelto por la API de HP SDS."""

    id: str
    name: str
    status: str = "ACTIVE"
