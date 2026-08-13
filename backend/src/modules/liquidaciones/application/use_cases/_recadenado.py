"""Recadenado del grupo (prestador, tipo_servicio, zona) — glue compartido entre
todos los caminos de escritura de tarifarios (alta/edición/baja manual de
`config_tarifarios.py` y los importadores). La regla en sí vive en
`domain/services/cadena_tarifaria.py`."""

from uuid import UUID

from src.modules.liquidaciones.domain.repositories.tarifario_repository import (
    TarifarioRepository,
)
from src.modules.liquidaciones.domain.services.cadena_tarifaria import recalcular_cadena


async def recadenar_grupo(
    repo: TarifarioRepository,
    *,
    prestador_id: UUID,
    tipo_servicio: str,
    zona: str | None,
) -> None:
    grupo = await repo.list_grupo(
        prestador_id=prestador_id, tipo_servicio=tipo_servicio, zona=zona
    )
    for ajuste in recalcular_cadena(grupo):
        await repo.set_vigencia_hasta(ajuste.tarifario_id, ajuste.vigencia_hasta)
