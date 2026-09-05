from datetime import date

from src.modules.turnos.application.dtos.grilla_variante_dtos import GrillaVarianteDTO
from src.modules.turnos.application.fecha_local import hoy_local
from src.modules.turnos.application.use_cases.grilla_variante_support import (
    GrillaVarianteDependencies,
    grilla_variante_dto,
    resolver_nombres,
)
from src.modules.turnos.domain.entities.grilla_variante import GrillaVariante
from src.modules.turnos.domain.services.grilla_variante_reglas import (
    advertencias_de_cobertura,
)


class ListGrillaVariantes:
    """Caso de uso: lista las grillas de vacaciones (activas y canceladas),
    más recientes primero por `desde`. Con `solo_vigentes` devuelve solo las
    ACTIVAS cuya vigencia incluye `hoy` o es futura. Las advertencias del
    listado son las estructurales (huecos/franjas sin operador); la de
    cubrientes ausentes se calcula solo al guardar (evita N consultas a
    vacaciones en un listado)."""

    def __init__(self, deps: GrillaVarianteDependencies) -> None:
        self._deps = deps

    async def execute(
        self, *, solo_vigentes: bool = False, hoy: date | None = None
    ) -> list[GrillaVarianteDTO]:
        variantes = await self._deps.variantes.list_all()
        if solo_vigentes:
            referencia = hoy or hoy_local()
            variantes = [v for v in variantes if _vigente_o_futura(v, referencia)]
        titulares = await self._deps.slots.list_all()
        ordenadas = sorted(variantes, key=lambda v: v.desde, reverse=True)
        advertencias = {v.id: advertencias_de_cobertura(v.slots, titulares) for v in ordenadas}
        nombres = await resolver_nombres(self._deps, ordenadas, [])
        return [grilla_variante_dto(v, advertencias[v.id], nombres) for v in ordenadas]


def _vigente_o_futura(variante: GrillaVariante, hoy: date) -> bool:
    return variante.estado == "ACTIVA" and variante.hasta >= hoy
