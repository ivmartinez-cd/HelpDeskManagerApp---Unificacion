from typing import Protocol

from src.modules.contadores.domain.entities.operador import Operador


class OperadorCatalogPort(Protocol):
    """Puerto de resolución de identidad (nombre/apellido/color) de operadores
    para un conjunto puntual de logins ya conocido — no enumera "todos los
    operadores de facturación" de la fuente subyacente, porque no hay forma
    verificada de filtrar solo por ese rol (ver ADR-012 y
    SIGES_READONLY_CATALOGO_DATOS.md). Los logins a resolver salen de los
    eventos ya sincronizados, no de este puerto."""

    async def find_by_logins(self, logins: list[str]) -> list[Operador]: ...
