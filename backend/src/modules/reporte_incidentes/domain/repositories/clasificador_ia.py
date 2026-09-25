from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RespuestaIA:
    texto: str
    modelo: str
    tokens_entrada: int
    tokens_salida: int


class ClasificadorIA(Protocol):
    @property
    def configurado(self) -> bool:
        """False si falta la clave de la API: no se puede tipificar con IA."""
        ...

    async def clasificar(self, prompt: str) -> RespuestaIA:
        """Respuesta JSON cruda del modelo. Si fallan todos los modelos, lanza
        `ExternalServiceError` (nunca inventa una tipificación)."""
        ...
