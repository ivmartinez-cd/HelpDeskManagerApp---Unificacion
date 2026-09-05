"""Compartido por `recalcular_candidato` y `forzar_metodo_candidato`: ambos
endpoints reciben un request que puede o no traer la selección de un equipo
real de Siges (nro_proceso/id_grupo_economico/id_anexo/fecha_objetivo,
además de que `clase` sea numérica — ver docstring de `get_candidatos` en
`proyeccion_router.py`). Evita duplicar el mismo chequeo en los dos routers."""

from datetime import date
from typing import Protocol

from src.modules.contadores.application.dtos.solicitud_recalculo_siges_dto import (
    SolicitudRecalculoSigesDto,
)


class SolicitudConSeleccionReal(Protocol):
    """Atributos como `@property` read-only (no anotaciones de instancia
    simples): los dataclasses `frozen=True` que implementan este Protocol
    (`RecalcularCandidatoRequest`, `ForzarMetodoRequest`) tienen atributos de
    solo lectura, y mypy exige que el Protocol calce esa mutabilidad."""

    @property
    def clase(self) -> str: ...
    @property
    def nro_proceso(self) -> int | None: ...
    @property
    def id_grupo_economico(self) -> int | None: ...
    @property
    def id_anexo(self) -> int | None: ...
    @property
    def fecha_objetivo(self) -> date | None: ...


def es_solicitud_real(request: SolicitudConSeleccionReal) -> bool:
    return (
        request.clase.isdigit()
        and request.nro_proceso is not None
        and request.id_grupo_economico is not None
        and request.id_anexo is not None
        and request.fecha_objetivo is not None
    )


def solicitud_de(request: SolicitudConSeleccionReal) -> SolicitudRecalculoSigesDto:
    assert request.nro_proceso is not None
    assert request.id_grupo_economico is not None
    assert request.id_anexo is not None
    assert request.fecha_objetivo is not None
    return SolicitudRecalculoSigesDto(
        nro_proceso=request.nro_proceso,
        id_grupo_economico=request.id_grupo_economico,
        id_anexo=request.id_anexo,
        fecha_objetivo=request.fecha_objetivo,
    )
