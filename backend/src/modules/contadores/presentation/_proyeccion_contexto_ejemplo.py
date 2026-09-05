"""Compartido por `proyeccion_router.py` y `proyeccion_candidatos_router.py`:
el `ContextoProcesoDto` de ejemplo que sigue siendo el fallback cuando no hay
selección real de grupo/proceso (ver docstring del módulo `proyeccion_router`)."""

from datetime import date

from src.modules.contadores.application.dtos.contexto_proceso_dto import ContextoProcesoDto
from src.modules.contadores.application.dtos.receso_dto import RecesoDto
from src.modules.contadores.domain.value_objects.estimacion.receso_cliente import RecesoCliente
from src.modules.contadores.infrastructure.ejemplo.datos_ejemplo_proyeccion import (
    FECHA_OBJETIVO_EJEMPLO,
    ID_ANEXO_EJEMPLO,
    ID_GRUPO_ECONOMICO_EJEMPLO,
    PERIODO_DESDE_EJEMPLO,
    PERIODO_HASTA_EJEMPLO,
)
from src.modules.contadores.infrastructure.ejemplo.recesos_store import get_recesos_ejemplo_store


async def contexto_ejemplo(fecha_objetivo: date | None) -> ContextoProcesoDto:
    recesos = await get_recesos_ejemplo_store().listar(ID_GRUPO_ECONOMICO_EJEMPLO)
    return ContextoProcesoDto(
        fecha_objetivo=fecha_objetivo or FECHA_OBJETIVO_EJEMPLO,
        periodo_desde=PERIODO_DESDE_EJEMPLO,
        periodo_hasta=PERIODO_HASTA_EJEMPLO,
        id_grupo_economico=ID_GRUPO_ECONOMICO_EJEMPLO,
        id_anexo=ID_ANEXO_EJEMPLO,
        recesos=[_a_receso_cliente(r) for r in recesos],
    )


def _a_receso_cliente(r: RecesoDto) -> RecesoCliente:
    return RecesoCliente(r.fecha_desde, r.fecha_hasta, r.id_grupo_economico, r.id_anexo)
