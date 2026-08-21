"""Puerto de lectura contra Siges para las fichas de clientes nuevos — el
adaptador pyodbc vive en infrastructure/siges (ADR-012: Siges es fuente de
solo lectura, la ficha local es la que se edita)."""

from datetime import date
from typing import Protocol

from src.modules.contadores.domain.entities.cliente_nuevo import (
    CandidatoClienteNuevo,
    ResumenSigesClienteNuevo,
)


class ClientesNuevosSigesPort(Protocol):
    async def resumen_por_empresa(
        self, empresa_ids: frozenset[int], *, force_refresh: bool = False
    ) -> dict[int, ResumenSigesClienteNuevo]: ...

    async def candidatos_desde(
        self, firmado_desde: date, *, force_refresh: bool = False
    ) -> list[CandidatoClienteNuevo]: ...
