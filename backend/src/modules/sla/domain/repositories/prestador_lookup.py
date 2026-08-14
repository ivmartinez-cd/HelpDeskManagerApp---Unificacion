import uuid
from typing import Protocol


class PrestadorLookup(Protocol):
    """Puerto para resolver qué PST (por `id_tecnico`/`ID_Empresa` de Siges)
    tiene asignados un operador — permite filtrar los incidentes vencidos por
    "mis PST" sin que sla.domain/application dependan del módulo prestadores
    (el contrato de import-linter `sla-domain-app-independent-from-prestadores`
    solo permite esa dependencia desde infrastructure/presentation)."""

    async def get_siges_ids_por_operador(self, operador_id: uuid.UUID) -> list[int]: ...

    async def get_all_pst_siges_ids(self) -> list[int]: ...
