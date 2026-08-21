from datetime import datetime
from typing import Protocol

from src.modules.wati.domain.entities.conversacion import ConversacionWati


class ConversacionRepository(Protocol):
    async def upsert(self, conversacion: ConversacionWati) -> None: ...

    async def list_activas(self, desde: datetime) -> list[ConversacionWati]:
        """Conversaciones con actividad del cliente desde `desde` o que siguen
        esperando respuesta — la lista de vigilancia del próximo ciclo."""
        ...

    async def list_esperando(self, ahora: datetime) -> list[ConversacionWati]:
        """Las que esperan respuesta humana (ver ConversacionWati.espera_respuesta),
        ordenadas de la más antigua a la más nueva."""
        ...

    async def get_ultima_sincronizacion(self) -> datetime | None: ...
