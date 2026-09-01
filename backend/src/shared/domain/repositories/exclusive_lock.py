"""Puerto de exclusión mutua entre workers para operaciones de larga duración o con
efectos externos que no deben solaparse (ver `shared/infrastructure/locks/`)."""

from contextlib import AbstractAsyncContextManager
from typing import Protocol


class ExclusiveLock(Protocol):
    def hold(self) -> AbstractAsyncContextManager[bool]:
        """Intenta tomar el lock; True = tomado (se libera al salir del contexto);
        False = ya lo tiene otro proceso o worker. Nunca bloquea esperando."""
        ...
