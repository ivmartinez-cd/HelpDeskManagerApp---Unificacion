from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from src.modules.preventivos.domain.entities.habilitacion_preventivo import (
    HabilitacionPreventivo,
)


class HabilitacionRepository(Protocol):
    async def get_activa(self, siges_maquina_id: int) -> HabilitacionPreventivo | None: ...

    async def list_activas_por_maquinas(
        self, siges_maquina_ids: Sequence[int]
    ) -> list[HabilitacionPreventivo]: ...

    async def create(self, habilitacion: HabilitacionPreventivo) -> None: ...

    async def desactivar(
        self,
        siges_maquina_id: int,
        *,
        deshabilitado_por: str,
        deshabilitado_en: datetime,
    ) -> bool:
        """Desactiva la habilitación activa de la máquina (si la hay) dejando
        la auditoría de quién/cuándo. Devuelve False si no había ninguna."""
        ...
