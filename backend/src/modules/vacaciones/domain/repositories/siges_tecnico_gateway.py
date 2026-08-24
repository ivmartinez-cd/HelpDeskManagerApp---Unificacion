"""Puerto de lectura del catálogo de técnicos de planta en Siges — insumo del
vínculo Empleado↔técnico (ver `domain/services/vinculacion_siges.py`). Solo
lectura: la cuenta `SiGesReadOnly` no tiene permisos de escritura."""

from typing import Protocol

from src.modules.vacaciones.domain.services.vinculacion_siges import SigesTecnicoInfo


class SigesTecnicoGateway(Protocol):
    async def list_tecnicos_activos(self) -> list[SigesTecnicoInfo]:
        """Técnicos de planta activos (`Estado=0`) cuyo `Den_Comercial`
        empieza con `'CD - '` — mismo filtro que usa `bono_tecnicos` para
        identificar técnicos de Canal Directo."""
        ...
