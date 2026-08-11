"""Puerto de exclusión mutua entre workers para operaciones offline de larga duración."""

from contextlib import AbstractAsyncContextManager
from typing import Protocol


class ExclusiveLock(Protocol):
    def hold(self) -> AbstractAsyncContextManager[bool]:
        """Intenta tomar el lock; True = tomado (se libera al salir del contexto);
        False = ya lo tiene otro proceso o worker. Nunca bloquea esperando."""
        ...